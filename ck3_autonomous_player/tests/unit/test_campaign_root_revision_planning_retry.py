"""P14 native-before-read and P17 Service-before-send revision races."""
from pathlib import Path
import copy
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.native_driver import _NativeCommandRejectedError
from xar_autoplayer.bridge.readonly_planning_retry_v1 import (
    classify_readonly_planning_error_v1, retry_readonly_planning_once_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


def before_read_rejection():
    # Synthetic native envelopes preserve the exact actual P14 diagnostic shape.
    rid = "fixture-p14-before-read"
    request = dict(type="execute_step", protocol_version=1, request_id=rid,
                   step="query-campaign-root-context-v1", expected_revision=370)
    failure = dict(query_type="campaign", stage="preflight_revision_changed",
                   request_native_revision=370, worker_native_revision=371,
                   predicates=dict(revision_matches=False, worker_ready=True,
                                   previous_present=True, observed_read=False,
                                   observed_equal=False), read_attempted=False,
                   cached_scalars="date_raw:53330664,paused:1", observed_scalars=None,
                   differing_fields=None, truncated=False)
    result = dict(type="command_result", protocol_version=1, request_id=rid,
                  ok=False, error="state_changed", campaign_root_preflight_failure_v1=failure)
    return _NativeCommandRejectedError("state_changed", native_request_id=rid,
                                      native_request_frame=request, native_command_result_frame=result)


class CampaignRootRevisionPlanningRetry(unittest.TestCase):
    def test_actual_service_local_guard_proves_no_root_query_sent(self):
        calls = []
        service = SimpleNamespace(snapshot=lambda **kwargs: {"paused": True, "revision": 65},
                                  execute_step=lambda *args, **kwargs: calls.append(args))
        with self.assertRaises(PreSubmissionRevisionMismatchError) as caught:
            GameplayBridgeService.query_campaign_root_context_v1(service, expected_revision=64)
        self.assertEqual(calls, [])
        result = classify_readonly_planning_error_v1(caught.exception)
        self.assertEqual(result["class"], "campaign_root_local_revision_changed_before_send")
        self.assertFalse(result["failed_root_query_native_request_sent"])
        self.assertNotIn("native_request_id", result)
        # An arbitrary plain BridgeUnavailableError is not source-qualified.
        self.assertIsNone(classify_readonly_planning_error_v1(BridgeUnavailableError(str(caught.exception))))

    def test_actual_service_planning_wrapper_retries_each_known_race_once(self):
        for error in (before_read_rejection(), PreSubmissionRevisionMismatchError(
                "campaign-root revision mismatch: expected 64, current 65")):
            with self.subTest(error=str(error)):
                calls = []
                def fresh_plan(**kwargs):
                    calls.append(kwargs)
                    if len(calls) == 1:
                        raise error
                    return {"snapshot_id": "native:371", "revision": 65, "plan": {"selected_step": "query"}}
                service = SimpleNamespace(_plan_turn_internal_without_readonly_retry_v1=fresh_plan)
                result = GameplayBridgeService._plan_turn_internal(service)
                self.assertEqual(len(calls), 2)
                self.assertEqual(result["readonly_planning_replan_v1"]["business_actions_replayed"], 0)

    def test_native_before_read_requires_exact_readonly_stage(self):
        for change in ("business_step", "read_attempted", "worker_not_ahead"):
            error = before_read_rejection()
            failure = error.native_command_result_frame["campaign_root_preflight_failure_v1"]
            if change == "business_step":
                error.native_request_frame["step"] = "raise-troops"
            elif change == "read_attempted":
                failure["read_attempted"] = True
            else:
                failure["worker_native_revision"] = 370
            with self.subTest(change=change):
                self.assertIsNone(classify_readonly_planning_error_v1(error))

    def test_new_races_share_existing_single_retry_budget(self):
        calls = []
        def fail():
            calls.append(1)
            raise before_read_rejection()
        with self.assertRaises(_NativeCommandRejectedError):
            retry_readonly_planning_once_v1(lambda: retry_readonly_planning_once_v1(fail))
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
