"""Meaningful once/lost-ACK/independent-after tests. Never attach or start CK3."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256
from xar_autoplayer.bridge import white_control_action_driver as action
from xar_autoplayer.bridge.white_control_action_contract import (
    CAPABILITY, STEP, SCHEMA, PROOFS, business_binding, normalize_action_ack,
)
from xar_autoplayer.bridge.white_player_business_variables_contract import VARIABLE_KEYS
from xar_autoplayer.bridge.white_rendered_text_contract import TEXT_NAMES, PROOFS as TEXT_PROOFS

class FakeDriver:
    def __init__(self, directory):
        self.directory = Path(directory); self.age = 30; self.generation = 1
        self.dispatches = 0; self.reads = 0; self.mode = "success"; self.text_before = "30"
        self.snapshot = {"revision": 3, "native_revision": 2, "snapshot_id": "actual-2",
                         "episode_run_id": "actual-episode", "date_raw": 53144328,
                         "paused": True, "map_ready": True, "active_event": None,
                         "played_character": {"alive": True, "character_id": 31254},
                         "diagnostics": {"connection_generation": 1, "hello": {
                             "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.3-msvc-x64",
                             "expected_ck3_version": "1.20.0.3", "expected_ck3_sha256": EXE_SHA256, "pid": 1234}}}
    def capabilities(self): return {"bridge_capabilities": [CAPABILITY]}
    def take_snapshot(self):
        value = deepcopy(self.snapshot); value["diagnostics"]["connection_generation"] = self.generation
        return value
    def _native_driver_state_path(self): return self.directory / "state.json"
    def _record_command(self, *args, **kwargs): pass
    def query_white_player_business_variables_v1(self, **kwargs):
        self.reads += 1
        values = [0, self.age, 6, 6, 6, 6, 6, 6]
        if self.dispatches and self.mode == "wrong_other": values[2] = 7
        fields = {key: {"present": True, "actual_kind": 1, "actual_payload": value * 100000,
                         "fixed_raw": value * 100000, "integer_value": value}
                  for key, value in zip(VARIABLE_KEYS, values)}
        return {"schema": "ck3-native-white-player-business-variables-v1", "available": True,
                "read_only": True, "all_eight_numeric_integers": True, "fields": fields,
                **business_binding(self.take_snapshot()),
                **{key: True for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified",
                                        "player_scope_verified", "stable_two_pass_values")}}
    def query_white_rendered_text_v1(self, **kwargs):
        self.reads += 1
        text = self.text_before if not self.dispatches or self.mode == "stale_text" else str(self.age)
        fields = {key: {"child_path": "0/" + str(i + 1), "text_utf8": text if i == 0 else "6",
                         "effective_visible": True, "enabled": True} for i, key in enumerate(TEXT_NAMES)}
        return {"schema": "ck3-native-white-rendered-text-v1", "available": True, "read_only": True,
                "rendered_text_available": True, "selected_down_available": False,
                "text_source": "actual_CPdxGuiTextbox_GetText_390", "fields": fields,
                **{key: True for key in TEXT_PROOFS}, **business_binding(self.take_snapshot())}
    def _execute_primitive_step(self, step, **kwargs):
        self.dispatches += 1
        if self.mode == "lost_ack": raise BridgeUnavailableError("synthetic missing ACK")
        expected_age = kwargs["request_fields"]["expected_before_age"]
        if self.mode != "no_effect": self.age += 1
        result = {"schema": SCHEMA, "step": STEP, "control": "age_plus_1", "available": True,
                  "read_only": False, "selected_down_available": False, "postcondition_verified": False,
                  "expected_before_age": expected_age, "native_handled": False, "unavailable_reason": "",
                  "target_child_path": "0/1/3/3/1/5", **{key: True for key in PROOFS},
                  **{key: value for key, value in business_binding(self.take_snapshot()).items() if key != "episode_run_id"}}
        if self.mode == "bad_receiver": result["receiver_qualified"] = False
        if self.mode == "native_fake_credit": result["postcondition_verified"] = True
        return result

class WhiteControlActionTests(unittest.TestCase):
    def test_success_proves_separate_business_and_rendered_after(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            result = action.click_white_control(driver, "age_plus_1", 30, "age-first")
            self.assertEqual(driver.dispatches, 1)
            self.assertTrue(result["postcondition_verified"])
            self.assertEqual(result["later_actual_business"]["fields"]["ervc_cc_age"]["integer_value"], 31)
            self.assertEqual(result["later_actual_rendered_text"]["fields"][TEXT_NAMES[0]]["text_utf8"], "31")
            self.assertFalse(result["selected_down_available"])
            self.assertFalse(result["full_gui_acceptance_credit"])
            with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 31, "age-first")
            self.assertEqual(driver.dispatches, 1)
            driver.text_before = "31"
            action.click_white_control(driver, "age_plus_1", 31, "age-second")
            self.assertEqual(driver.dispatches, 2)
    def test_lost_ack_consumes_same_intent_across_generation_and_argument_change(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory); driver.mode = "lost_ack"
            with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 30, "lost")
            reads = driver.reads; driver.generation = 2
            with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 31, "lost")
            self.assertEqual(driver.dispatches, 1); self.assertEqual(driver.reads, reads)
            self.assertEqual(len(list(Path(directory).glob("white-control-actions/*.claim.json"))), 1)
    def test_invalid_or_changed_before_never_dispatches(self):
        cases = [("age_plus_10", 30, "a"), ("age_plus_1", True, "a"), ("age_plus_1", 120, "a"),
                 ("age_plus_1", 30, "../a"), ("age_plus_1", 29, "a")]
        for control, age, intent in cases:
            with self.subTest(control=control, age=age, intent=intent), TemporaryDirectory() as directory:
                driver = FakeDriver(directory)
                with self.assertRaises((ValueError, BridgeUnavailableError)): action.click_white_control(driver, control, age, intent)
                self.assertEqual(driver.dispatches, 0)
                self.assertFalse(list(Path(directory).glob("white-control-actions/*.claim.json")))
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory); driver.text_before = "999"
            with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 30, "before")
            self.assertEqual(driver.dispatches, 0)
    def test_ack_receiver_or_claimed_native_post_credit_does_not_pass(self):
        for mode in ("bad_receiver", "native_fake_credit"):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                driver = FakeDriver(directory); driver.mode = mode
                with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 30, "ack")
                self.assertEqual(driver.dispatches, 1); self.assertEqual(driver.reads, 2)
                with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 30, "ack")
                self.assertEqual(driver.dispatches, 1)
    def test_ack_without_actual_effect_or_rendered_effect_fails_with_one_dispatch(self):
        for mode in ("no_effect", "stale_text", "wrong_other"):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                driver = FakeDriver(directory); driver.mode = mode
                clock = iter(range(100))
                fake_time = SimpleNamespace(monotonic=lambda: next(clock), sleep=lambda _: None)
                with patch.object(action, "time", fake_time), self.assertRaises(BridgeUnavailableError):
                    action.click_white_control(driver, "age_plus_1", 30, "after")
                self.assertEqual(driver.dispatches, 1)
                receipt = json_read(next(Path(directory).glob("white-control-actions/*.result.json")))
                self.assertFalse(receipt["ok"])
    def test_after_frame_change_consumes_intent_without_second_dispatch(self):
        with TemporaryDirectory() as directory:
            driver = FakeDriver(directory)
            original = driver._execute_primitive_step
            def dispatch(*args, **kwargs):
                result = original(*args, **kwargs)
                driver.snapshot["date_raw"] += 1
                return result
            driver._execute_primitive_step = dispatch
            with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 30, "frame")
            self.assertEqual(driver.dispatches, 1)
            with self.assertRaises(BridgeUnavailableError): action.click_white_control(driver, "age_plus_1", 31, "frame")
            self.assertEqual(driver.dispatches, 1)

def json_read(path):
    import json
    return json.loads(path.read_text())

if __name__ == "__main__": unittest.main()
