"""Focused source tests: actual f198/candidate AST with explicit I/O mocks.

No SDK process, Native call, state directory, timing sink or file scratch.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

import prepare_candidate as producer

ROOT = Path(__file__).resolve().parent
BRIDGE = ROOT / "xar_autoplayer" / "bridge"
PACKAGE = "a0_source_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(BRIDGE)]
sys.modules[PACKAGE] = package
helper = __import__(PACKAGE + ".exact_clock_failure_diagnostic_v1", fromlist=["*"])
driver_api = subprocess.check_output(["git", "show", producer.BASE + ":" + producer.PREFIX + "driver.py"], cwd=producer.REPO)
api_nodes = [n for n in ast.parse(driver_api).body if isinstance(n, ast.ClassDef)
             and n.name in {"BridgeUnavailableError", "StepPostconditionError"}]
api = {}
exec(compile(ast.Module(body=api_nodes, type_ignores=[]), "actual-f198-driver-api", "exec"), api)
BridgeUnavailableError = api["BridgeUnavailableError"]
StepPostconditionError = api["StepPostconditionError"]
driver_module = types.ModuleType(PACKAGE + ".driver")
driver_module.BridgeUnavailableError = BridgeUnavailableError
driver_module.StepPostconditionError = StepPostconditionError
sys.modules[driver_module.__name__] = driver_module


def load_function(data, name, namespace):
    node = copy.deepcopy(producer.function_node(data, name))
    node.decorator_list = []
    namespace.update(__package__=PACKAGE, BridgeUnavailableError=BridgeUnavailableError,
                     StepPostconditionError=StepPostconditionError)
    exec(compile(ast.Module(body=[node], type_ignores=[]), "actual-source:" + name, "exec"), namespace)
    return namespace[name]


def frame(raw=100, paused=True):
    return {"date_raw": raw, "paused": paused, "speed": 3, "revision": 9,
            "native_revision": 44, "player_character_id": 40526,
            "episode_id": "episode-actual", "snapshot_id": "bound-frame",
            "diagnostics": {"bridge_pid": 123, "connection_generation": 4},
            "history": ["MUST_NOT_EXPORT"], "unbounded_body": "SECRET"}


class Fake:
    life_advance_timeout_seconds = 30

    def __init__(self, mode="failure", cleanup_error=False, original_error=None):
        self.mode, self.cleanup_error, self.original_error = mode, cleanup_error, original_error
        self.events = []

    def _execute_primitive_step(self, step, **kwargs):
        self.events.append(("primitive", step, kwargs))
        if step.startswith("arm-"):
            if self.original_error is not None:
                raise self.original_error
            return {"step": step, "accepted": True, "status": "armed",
                    "request_id": "arm-request", "tactical_daily_sentinel": {
                        "generation": 147, "state": "armed", "starting_date_raw": 100,
                        "target_date_raw": 124, "speed": 3, "pause_observed": False}}
        if step == "status":
            return {"tactical_daily_sentinel": {"state": "triggered", "generation": 147}}
        return {"step": step, "accepted": True, "status": "canceled", "request_id": "cancel-request"}

    def _resume_life_advance(self, current, actions, **kwargs):
        self.events.append(("resume", kwargs))
        actions.append({"step": "resume-map", "result": {"accepted": True}})
        return frame(paused=False)

    def _wait_for_life_advance_snapshot(self, current, predicate, **kwargs):
        self.events.append(("wait", kwargs))
        return frame(124, True) if self.mode == "normal" else frame(100, False)

    def take_internal_semantic_snapshot(self):
        self.events.append(("cleanup-snapshot",))
        if self.cleanup_error:
            raise BridgeUnavailableError("cleanup unavailable")
        return frame(124, True)

    def _pause_life_advance(self, current, actions):
        self.events.append(("pause", current["date_raw"], current["paused"]))
        if current.get("paused") is not True:
            actions.append({"step": "pause-map", "result": {"accepted": True}})
        return current


def method(candidate, fake):
    data = (BRIDGE / "native_driver.py").read_bytes() if candidate else producer.original("native_driver.py")
    ns = {
        "_date_raw": lambda value, _: value["date_raw"],
        "_TACTICAL_DAILY_SENTINEL_ARM_PREFIX": "arm-",
        "_TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX": "cancel-",
        "_TACTICAL_DAILY_SENTINEL_STATUS_STEP": "status",
        "_TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY": "arm-cap",
        "_TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY": "cancel-cap",
        "_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY": "status-cap",
        "_normalize_tactical_daily_sentinel_status": lambda value: copy.deepcopy(value),
        "_validate_tactical_daily_sentinel_arm": lambda *args, **kwargs: fake.events.append(("validate-arm", kwargs)),
        "_validate_tactical_daily_sentinel_stop": lambda *args, **kwargs: fake.events.append(("validate-stop", kwargs)),
        "_life_advance_new_modal_hint": lambda *args: None,
        "start_army_timing": lambda stage: fake.events.append(("timing-start", stage)),
        "finish_army_timing": lambda *args, **kwargs: fake.events.append(("timing-end", kwargs)),
    }
    return load_function(data, "_advance_exact_day_with_sentinel", ns)


def boundary_modules(fake):
    speed = types.ModuleType(PACKAGE + ".exact_day_speed_configuration_v1")
    def prepare(driver, current, *, speed, actions):
        fake.events.append(("prepare-speed", speed))
        return current
    speed.prepare_exact_day_speed_v1 = prepare
    clock = types.ModuleType(PACKAGE + ".clock_observation_timing_v1")
    clock.start_clock_observation_v1 = lambda *args: fake.events.append(("clock-start",))
    clock.finish_clock_observation_v1 = lambda *args: fake.events.append(("clock-finish",))
    war = types.ModuleType(PACKAGE + ".war_daily_watch_v1")
    war.resume_once_v1 = lambda driver, start, watch, actions: frame(paused=False)
    return {speed.__name__: speed, clock.__name__: clock, war.__name__: war}


def execute(candidate=True, fake=None, watch=None):
    fake = fake or Fake()
    actions = [{"step": "previous-horizon-day", "result": {"request_id": "DO_NOT_EXPORT"}}]
    with patch.dict(sys.modules, boundary_modules(fake)):
        result = method(candidate, fake)(fake, frame(), speed=3, actions=actions, war_daily_watch=watch)
    return result, actions, fake.events


class CandidateTests(unittest.TestCase):
    def test_exact_inverse_and_only_named_functions_changed(self):
        for name, edits, owner in (("native_driver.py", producer.DRIVER_EDITS, "_advance_exact_day_with_sentinel"),
                                  ("mcp_server.py", producer.MCP_EDITS, "ck3_auto_turn")):
            before, after = producer.original(name), (BRIDGE / name).read_bytes()
            self.assertEqual(producer.transform(after, edits, reverse=True), before)
            # Replace the one owned node in the candidate AST with the baseline:
            # every other AST node (incl. shared budget and typed ROOT) must match.
            oldtree, newtree = ast.parse(before), ast.parse(after)
            oldnode = producer.function_node(before, owner)
            for parent in ast.walk(newtree):
                for field, value in ast.iter_fields(parent):
                    if isinstance(value, list):
                        for index, node in enumerate(value):
                            if isinstance(node, ast.FunctionDef) and node.name == owner:
                                value[index] = copy.deepcopy(oldnode)
            self.assertEqual(ast.dump(newtree), ast.dump(oldtree))

    def test_normal_calls_actions_and_result_equal_original(self):
        self.assertEqual(execute(False, Fake("normal")), execute(True, Fake("normal")))

    def test_target_error_retains_original_and_no_stop_query(self):
        fake = Fake()
        with self.assertRaises(StepPostconditionError) as caught:
            execute(fake=fake)
        error = caught.exception
        self.assertEqual(str(error), helper.MESSAGE)
        self.assertIs(type(error.__cause__), BridgeUnavailableError)
        value = error.step_result
        self.assertEqual(value["armed_reply"]["generation"], 147)
        self.assertFalse(value["normal_status_query_attempted"])
        self.assertFalse(value["stop_validation_attempted"])
        self.assertIsNone(value["stopped_status"])
        self.assertEqual(value["last_wait_frame"]["date_raw"], 100)
        self.assertEqual(value["cleanup_before_pause_frame"]["date_raw"], 124)
        self.assertIs(value["cleanup_before_pause_frame"]["paused"], True)
        self.assertEqual([e[1] for e in fake.events if e[0] == "primitive"],
                         ["arm-100-to-124-speed-3-mode-terminal-a-0", "cancel-147"])
        row = value["cleanup_actions"]["rows"][0]
        self.assertEqual(row["ack"]["request_id"], "cancel-request")
        encoded = json.dumps(value)
        for forbidden in ("DO_NOT_EXPORT", "previous-horizon-day", "MUST_NOT_EXPORT", "SECRET"):
            self.assertNotIn(forbidden, encoded)
        self.assertLessEqual(len(helper._encode(value)), 8192)

    def test_missing_cleanup_ack_is_unknown(self):
        with self.assertRaises(StepPostconditionError) as caught:
            execute(fake=Fake(cleanup_error=True))
        value = caught.exception.step_result
        self.assertIsNone(value["cleanup_before_pause_frame"])
        row = value["cleanup_actions"]["rows"][0]
        self.assertFalse(row["result_observed"])
        self.assertIsNone(row["ack"]["accepted"])
        self.assertIsNone(row["ack"]["request_id"])
        self.assertEqual(row["error"], "cleanup unavailable")

    def test_other_error_object_is_preserved(self):
        for message in ("arm transport unavailable", helper.MESSAGE):
            for candidate in (False, True):
                original = BridgeUnavailableError(message)
                with self.assertRaises(BridgeUnavailableError) as caught:
                    execute(candidate, Fake(original_error=original))
                self.assertIs(caught.exception, original)

    def test_diagnostic_failure_does_not_mask_original_error(self):
        with patch.object(helper, "build_exact_clock_failure_v1", side_effect=ValueError("bad projector")):
            with self.assertRaises(BridgeUnavailableError) as caught:
                execute()
        self.assertIs(type(caught.exception), BridgeUnavailableError)
        self.assertEqual(str(caught.exception), helper.MESSAGE)

    def test_war_watch_legacy_branch_unchanged(self):
        watch = types.SimpleNamespace(watch_army_ids=(7,), owner=(40526, "episode", 4),
            ready_to_arm=lambda f: True, same_owner=lambda f: True,
            same_connection=lambda f: True, boundary=lambda f: None)
        errors = []
        for candidate in (False, True):
            with self.assertRaises(StepPostconditionError) as caught:
                execute(candidate, Fake(), watch)
            errors.append(caught.exception)
        self.assertEqual(str(errors[0]), str(errors[1]))
        self.assertEqual(errors[0].step_result, errors[1].step_result)

    def test_utf8_bound_and_nullable_unknown_fields(self):
        actions = [{"step": "x" * 10000, "result": {"accepted": "unknown", "snapshot": "SECRET"}}] * 1000
        value = helper.build_exact_clock_failure_v1(original_error=BridgeUnavailableError(helper.MESSAGE),
            starting_date_raw=100, target_date_raw=124, speed=3, arm_status={"generation": 147},
            starting=frame(), last_frame=frame(paused=False), cleanup_before_frame=None,
            actions=actions, action_start=0, cleanup_start=500)
        self.assertLessEqual(len(helper._encode(value)), 8192)
        self.assertIsNone(value["armed_reply"]["pause_observed"])
        self.assertIsNone(value["stopped_status"])
        if value["before_cleanup_actions"] is not None:
            self.assertIsNone(value["before_cleanup_actions"]["rows"][0]["ack"]["accepted"])
        self.assertNotIn("SECRET", json.dumps(value))

    def test_projection_is_isolated_rejects_wrong_or_oversized(self):
        with self.assertRaises(StepPostconditionError) as caught:
            execute()
        error = caught.exception
        isolated = helper.exact_clock_failure_diagnostic_v1(error)
        isolated["armed_reply"]["generation"] = 9
        self.assertEqual(error.step_result["armed_reply"]["generation"], 147)
        for patch_value in ({"schema": "other"}, {"credit": True}, {"stop_credit": True},
                            {"normal_status_query_attempted": True}, {"extra": "z" * 9000}):
            bad = StepPostconditionError(helper.MESSAGE, selected_step="life-advance-one-day",
                                        step_result={**error.step_result, **patch_value})
            self.assertIsNone(helper.exact_clock_failure_diagnostic_v1(bad))

    def test_actual_mcp_error_branch_and_legacy_fallback(self):
        from mcp.types import CallToolResult
        construction = types.ModuleType(PACKAGE + ".domain_construction_private_transport_v1")
        construction.construction_transport_diagnostic = lambda error: None
        retry = types.ModuleType(PACKAGE + ".campaign_root_retry_diagnostic_v1")
        retry.project_campaign_root_retry_diagnostic_v1 = lambda error, value: None
        with self.assertRaises(StepPostconditionError) as caught:
            execute()
        typed = caught.exception
        plain = BridgeUnavailableError("other failure")
        native = BridgeUnavailableError("native rejected")
        for error in (typed, plain, native):
            def auto_turn():
                raise error
            ns = {"start_army_timing": lambda *args: None, "successor_owner": None,
                  "before_auto_turn_submit": None, "service": types.SimpleNamespace(auto_turn=auto_turn),
                  "_native_command_rejection_diagnostic": lambda e: {"legacy": True} if e is native else None}
            fn = load_function((BRIDGE / "mcp_server.py").read_bytes(), "ck3_auto_turn", ns)
            with patch.dict(sys.modules, {construction.__name__: construction, retry.__name__: retry}):
                if error is plain:
                    with self.assertRaises(BridgeUnavailableError) as reraised:
                        fn()
                    self.assertIs(reraised.exception, plain)
                else:
                    result = fn()
                    self.assertIsInstance(result, CallToolResult)
                    dumped = result.model_dump()
                    self.assertIs(dumped["is_error"], True)
                    self.assertIn(str(error), dumped["content"][0]["text"])
                    key = "exact_day_clock_failure_v1" if error is typed else "native_command_rejection"
                    self.assertIn(key, dumped["structured_content"]["diagnostics"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
