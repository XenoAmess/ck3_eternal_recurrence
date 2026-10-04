"""New mapping/price/cross-control tests only; the age04 suite is not rerun."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from test_white_control_action_v1 import FakeDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.white_numeric_control_action_contract import (
    CAPABILITY, STEP, CONTROLS, PRICE_TEXT, GOLD_TEXT, validate_numeric_action,
)
from xar_autoplayer.bridge import white_numeric_control_action_driver as numeric
from xar_autoplayer.bridge.white_control_action_contract import PROOFS, SCHEMA, business_binding
from xar_autoplayer.bridge.white_control_action_driver import click_white_control

class NumericDriver(FakeDriver):
    def __init__(self, directory):
        super().__init__(directory)
        self.values = {"ervc_cc_" + name: 6 for name in ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess")}
        self.price = "actual-localized-price-A"; self.before_price = self.price
        self.mode = "success"
    def capabilities(self):
        if self.mode == "old_dll": return super().capabilities()
        return {"bridge_capabilities": [CAPABILITY, *super().capabilities()["bridge_capabilities"]]}
    def query_white_player_business_variables_v1(self, **kwargs):
        result = super().query_white_player_business_variables_v1(**kwargs)
        for key, value in self.values.items():
            result["fields"][key].update(integer_value=value, fixed_raw=value * 100000, actual_payload=value * 100000)
        return result
    def query_white_rendered_text_v1(self, **kwargs):
        result = super().query_white_rendered_text_v1(**kwargs)
        for key, value in self.values.items(): result["fields"][key + "_value_text"]["text_utf8"] = str(value)
        result["fields"][PRICE_TEXT]["text_utf8"] = self.price
        result["fields"][GOLD_TEXT]["text_utf8"] = "actual-gold-unchanged"
        if self.dispatches and self.mode == "wrong_text":
            result["fields"][self.target_text]["text_utf8"] = "999"
        return result
    def _execute_primitive_step(self, step, **kwargs):
        self.dispatches += 1
        fields = kwargs["request_fields"]; control = fields["control"]
        self.target_variable, self.target_text = CONTROLS[control]
        self.values[self.target_variable] += 1
        self.price = "actual-localized-price-Z"  # No numerical formula is supplied or inferred.
        if self.mode == "wrong_variable":
            self.values[self.target_variable] -= 1
            wrong = next(key for key in self.values if key != self.target_variable)
            self.values[wrong] += 1
        result = {"schema": SCHEMA, "step": STEP, "control": control, "available": True,
                  "read_only": False, "selected_down_available": False, "postcondition_verified": False,
                  "expected_before_value": fields["expected_before_value"], "before_price_bound": True,
                  "native_handled": False, "unavailable_reason": "", "target_child_path": "0/1/3/4/1/5",
                  **{key: True for key in PROOFS},
                  **{key: value for key, value in business_binding(self.take_snapshot()).items() if key != "episode_run_id"}}
        if self.mode == "price_unbound": result["before_price_bound"] = False
        if self.mode == "wrong_ack_control": result["control"] = next(key for key in CONTROLS if key != control)
        return result

class WhiteNumericActionTests(unittest.TestCase):
    def test_six_exact_variable_text_mappings_and_actual_arbitrary_price_strings(self):
        for control, (variable, widget_text) in CONTROLS.items():
            with self.subTest(control=control), TemporaryDirectory() as directory:
                driver = NumericDriver(directory)
                result = numeric.click_white_numeric_control(driver, control, 6, driver.price, "mapping")
                self.assertEqual(driver.dispatches, 1)
                self.assertEqual(result["later_actual_business"]["fields"][variable]["integer_value"], 7)
                self.assertEqual(result["later_actual_rendered_text"]["fields"][widget_text]["text_utf8"], "7")
                self.assertEqual(result["actual_price_before"], "actual-localized-price-A")
                self.assertEqual(result["actual_price_after"], "actual-localized-price-Z")
                self.assertTrue(result["actual_price_before_after_bound"])
                self.assertFalse(result["price_formula_verified"])
    def test_moved_actual_before_price_refuses_without_claim_or_dispatch(self):
        with TemporaryDirectory() as directory:
            driver = NumericDriver(directory)
            with self.assertRaises(BridgeUnavailableError):
                numeric.click_white_numeric_control(driver, "diplomacy_plus_1", 6, "old-stale-price", "price")
            self.assertEqual(driver.dispatches, 0)
            self.assertFalse(list(Path(directory).glob("white-control-actions/*.claim.json")))
    def test_native_price_binding_and_control_identity_are_mandatory(self):
        for mode in ("price_unbound", "wrong_ack_control"):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                driver = NumericDriver(directory); driver.mode = mode
                with self.assertRaises(BridgeUnavailableError):
                    numeric.click_white_numeric_control(driver, "diplomacy_plus_1", 6, driver.price, "native")
                self.assertEqual(driver.dispatches, 1); self.assertEqual(driver.reads, 2)
    def test_wrong_variable_or_wrong_actual_rendered_value_does_not_pass(self):
        for mode in ("wrong_variable", "wrong_text"):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                driver = NumericDriver(directory); driver.mode = mode
                clock = iter(range(100))
                fake_time = SimpleNamespace(monotonic=lambda: next(clock), sleep=lambda _: None)
                with patch.object(numeric, "time", fake_time), self.assertRaises(BridgeUnavailableError):
                    numeric.click_white_numeric_control(driver, "stewardship_plus_1", 6, driver.price, "wrong")
                self.assertEqual(driver.dispatches, 1)
    def test_same_intent_is_shared_between_skill_controls_and_legacy_age_api(self):
        with TemporaryDirectory() as directory:
            driver = NumericDriver(directory)
            numeric.click_white_numeric_control(driver, "learning_plus_1", 6, driver.price, "shared")
            reads = driver.reads
            with self.assertRaises(BridgeUnavailableError):
                numeric.click_white_numeric_control(driver, "prowess_plus_1", 6, driver.price, "shared")
            with self.assertRaises(BridgeUnavailableError):
                click_white_control(driver, "age_plus_1", 30, "shared")
            self.assertEqual(driver.dispatches, 1); self.assertEqual(driver.reads, reads)
    def test_boundary_and_fixed_allowlist_reject_and_old_dll_has_no_new_capability(self):
        for control, value, price in [("age_plus_1", 6, "1"), ("learning_plus_10", 6, "1"),
                                      ("learning_plus_1", 100, "1"), ("learning_plus_1", 6, "")]:
            with self.subTest(control=control, value=value, price=price), self.assertRaises(ValueError):
                validate_numeric_action(control, value, price, "fixed")
        with TemporaryDirectory() as directory:
            driver = NumericDriver(directory); driver.mode = "old_dll"
            with self.assertRaises(UnsupportedStepError):
                numeric.click_white_numeric_control(driver, "martial_plus_1", 6, driver.price, "old")
            self.assertEqual(driver.dispatches, 0); self.assertEqual(driver.reads, 0)

if __name__ == "__main__": unittest.main()
