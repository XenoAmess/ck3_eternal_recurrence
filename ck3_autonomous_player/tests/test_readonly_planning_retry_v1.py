"""A stale read may restart planning once; business submissions never replay."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.readonly_planning_retry_v1 import (
    classify_readonly_planning_error_v1, retry_readonly_planning_once_v1,
)


def rejection(step="query-campaign-root-context-v1", *, complete=True):
    request_id = "fixture-readonly-race"
    request = dict(type="execute_step", protocol_version=1, request_id=request_id,
                   step=step, expected_revision=42)
    result = dict(type="command_result", protocol_version=1, request_id=request_id,
                  ok=False, error="state_changed")
    if complete:
        result["campaign_root_preflight_failure_v1"] = dict(
            query_type="campaign", stage="preflight_native_snapshot_changed",
            read_attempted=True, truncated=False, request_native_revision=42,
            worker_native_revision=42, differing_fields=["wars"],
            predicates=dict(observed_equal=False, revision_matches=True, worker_ready=True,
                            previous_present=True, observed_read=True))
    return _NativeCommandRejectedError("state_changed", native_request_id=request_id,
                                      native_request_frame=request, native_command_result_frame=result)


def executor_not_entered_rejection(*, mutate=None):
    """P05 AUTO68 completed native result; no application-main executor entry."""
    request_id = "step-64-ce69004646e1"
    request = dict(type="execute_step", protocol_version=1, request_id=request_id,
                   step="query-campaign-root-context-v1", expected_revision=29)
    failure = dict(executor_enter=False,
        executor_exception={"code": 0, "image": "none", "rva": None},
        executor_finish=None, executor_typed_result=None, final_equal=None,
        final_read=None, frame_stable=None, query_type="campaign", stage="wait",
        typed_result=None, wait_completed=False, wait_result="executor_failed")
    result = dict(type="command_result", protocol_version=1, request_id=request_id,
                  ok=False, error="application-main typed query failed or its snapshot changed",
                  typed_query_failure_v1=failure)
    if mutate is not None:
        mutate(request, result)
    native_error = result["error"] + "; typed_query_failure_v1=" + json.dumps(
        result["typed_query_failure_v1"], sort_keys=True, separators=(",", ":"))
    return _NativeCommandRejectedError(native_error, native_request_id=request_id,
        native_request_frame=request, native_command_result_frame=result)


class ReadonlyPlanningRetryTest(unittest.TestCase):
    def test_actual_service_wrapper_replans_with_a_fresh_frame(self):
        source = Path(__file__).parents[1] / "src/xar_autoplayer/bridge/service.py"
        tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        service = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                       and n.name == "GameplayBridgeService")
        wrapper = next(n for n in service.body if isinstance(n, ast.FunctionDef)
                       and n.name == "_plan_turn_internal")
        namespace = {"__package__": "xar_autoplayer.bridge"}
        exec(compile(ast.Module(body=[wrapper], type_ignores=[]), str(source), "exec"), namespace)
        for error in (rejection(), executor_not_entered_rejection(),
                      ValueError("current heir relationship needs a paused living-player map frame")):
            with self.subTest(error=str(error)):
                calls = []
                def fresh_plan(**arguments):
                    calls.append(arguments)
                    if len(calls) == 1:
                        raise error
                    return {"snapshot_id": "native:43", "revision": 7, "plan": {"war_count": 2}}
                stub = SimpleNamespace(_plan_turn_internal_without_readonly_retry_v1=fresh_plan)
                planned = namespace["_plan_turn_internal"](stub)
                self.assertEqual(len(calls), 2)
                evidence = planned["readonly_planning_replan_v1"]
                self.assertEqual(evidence["fresh_snapshot_id"], "native:43")
                self.assertEqual(evidence["business_actions_replayed"], 0)

    def test_actual_p05_executor_not_entered_is_one_readonly_replan(self):
        error = executor_not_entered_rejection()
        qualified = classify_readonly_planning_error_v1(error)
        self.assertEqual(qualified["class"], "campaign_root_executor_not_entered")
        self.assertEqual(qualified["native_request_id"], "step-64-ce69004646e1")
        self.assertEqual(qualified["source_native_revision"], 29)
        self.assertIs(qualified["business_submission"], False)
        calls = []
        def fresh():
            calls.append(1)
            if len(calls) == 1:
                raise error
            return {"snapshot_id": "native:30", "revision": 5}
        planned = retry_readonly_planning_once_v1(fresh)
        self.assertEqual(len(calls), 2)
        self.assertEqual(planned["readonly_planning_replan_v1"]["fresh_replans"], 1)

    def test_unentered_claim_requires_exact_read_request_and_native_failure(self):
        mutations = (
            lambda request, result: request.update(step="query-declarable-wars"),
            lambda request, result: request.update(expected_revision=0),
            lambda request, result: result.update(request_id="other"),
            lambda request, result: result.update(result={"accepted": True}),
            lambda request, result: result.update(error="unknown native error"),
            lambda request, result: result["typed_query_failure_v1"].update(executor_enter=True),
            lambda request, result: result["typed_query_failure_v1"].update(wait_completed=True),
            lambda request, result: result["typed_query_failure_v1"].update(query_type="other"),
            lambda request, result: result["typed_query_failure_v1"].update(stage="done"),
            lambda request, result: result["typed_query_failure_v1"].update(
                executor_exception={"code": 5, "image": "none", "rva": None}),
            lambda request, result: result["typed_query_failure_v1"].update(final_read=True),
            lambda request, result: result["typed_query_failure_v1"].update(unexpected="unknown"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.assertIsNone(classify_readonly_planning_error_v1(
                    executor_not_entered_rejection(mutate=mutate)))
        error = executor_not_entered_rejection()
        error.native_error += "; modified"
        self.assertIsNone(classify_readonly_planning_error_v1(error))

    def test_actions_unknown_reads_and_timeouts_are_not_retried(self):
        for error in (rejection("enforce-demands-1"), rejection("query-declarable-wars"),
                      rejection(complete=False), BridgeUnavailableError("native command_result timed out"),
                      ValueError("different precondition")):
            with self.subTest(error=repr(error)):
                calls = []
                def fail():
                    calls.append(1)
                    raise error
                with self.assertRaises(type(error)) as caught:
                    retry_readonly_planning_once_v1(fail)
                self.assertIs(caught.exception, error)
                self.assertEqual(len(calls), 1)

    def test_nested_repeated_races_share_one_retry_budget(self):
        calls = []
        def fail():
            calls.append(1)
            raise rejection()
        with self.assertRaises(_NativeCommandRejectedError):
            retry_readonly_planning_once_v1(lambda: retry_readonly_planning_once_v1(fail))
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
