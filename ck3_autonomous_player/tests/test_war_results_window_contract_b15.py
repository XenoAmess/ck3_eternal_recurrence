"""Synthetic B14/B15 war-results wire tests; no game, recording or D: fixtures."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src/xar_autoplayer"
PACKAGE = "_war_results_b15_fixture"
for name, path in ((PACKAGE, SOURCE), (PACKAGE + ".bridge", SOURCE / "bridge")):
    package = ModuleType(name)
    package.__path__ = [str(path)]
    sys.modules[name] = package
spec = importlib.util.spec_from_file_location(
    PACKAGE + ".bridge.war_results_window_contract", SOURCE / "bridge/war_results_window_contract.py",
)
assert spec and spec.loader
CONTRACT = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = CONTRACT
spec.loader.exec_module(CONTRACT)


def old_leaf():
    return {
        "schema": "ck3-war-results-window-v1", "operation": "close", "window_name": "war_results",
        "available": False, "accepted": False, "status": "verification_pending",
        "unavailable_reason": "war_declared_close_not_post_verified",
        "root_observed": True, "window_present": True, "effective_visible": True,
        "button_name": "close_button", "dispatch_attempted": True,
        "dispatch_invoked": False, "native_handled": False,
        "post_observed": True, "post_window_present": True, "post_effective_visible": True,
        "scope_unchanged": True, "closure_verified": False,
        "application_owner_thread_verified": True,
        "played_character_id": 31254, "date_raw": 53169792, "paused": True,
        "native_revision": 617, "connection_generation": 13,
        "pump_epoch": 101, "thread_id": 202, "ticket_sequence": 303,
        "request_id": "synthetic-close-one",
        "root_observation_source": "guarded_top_level_and_complete_owner_tree",
        "post_observation_source": "guarded_top_level_and_complete_owner_tree",
        "game_version": "1.20.0.4", "executable_sha256":
            "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
    }


def normalize(leaf):
    receipt = {
        "request_id": leaf["request_id"], "ticket_sequence": 303,
        "executor_started_sequence": 303, "completed_sequence": 303,
        "pump_epoch": 101, "thread_id": 202, "date_raw": 53169792,
        "connection_generation": 13,
    }
    binding = {"native_revision": 617, "actor_character_id": 31254, "date_raw": 53169792}
    return CONTRACT.normalize_war_results_window_v1(
        leaf, operation="close", binding=binding, native_generation=13,
        owner_receipt=receipt,
    )


class WarResultsB15ContractTests(unittest.TestCase):
    def test_old_b14_shape_is_still_accepted_without_business_credit(self):
        row = normalize(old_leaf())
        self.assertEqual(row["status"], "verification_pending")
        self.assertFalse(row["closure_verified"])

    def test_preflight_rejection_and_seh_are_uncredited(self):
        for stage, code in (("preflight_rejected", 0), ("callback_exception", 0xC0000005)):
            with self.subTest(stage=stage):
                leaf = old_leaf()
                leaf.update(dismiss_stage=stage, dismiss_exception_code=code)
                self.assertFalse(normalize(leaf)["accepted"])

    def test_callback_return_does_not_credit_visible_window(self):
        leaf = old_leaf()
        leaf.update(dismiss_stage="callback_returned", dismiss_exception_code=0,
                    dispatch_invoked=True, native_handled=True)
        row = normalize(leaf)
        self.assertFalse(row["closure_verified"])
        self.assertEqual(row["status"], "verification_pending")

    def test_only_post_hidden_window_can_be_closed_verified(self):
        leaf = old_leaf()
        leaf.update(dismiss_stage="callback_returned", dismiss_exception_code=0,
                    dispatch_invoked=True, native_handled=True,
                    available=True, accepted=True, closure_verified=True,
                    post_effective_visible=False, status="closed_verified",
                    unavailable_reason="")
        self.assertTrue(normalize(leaf)["closure_verified"])
        forged = deepcopy(leaf)
        forged["post_effective_visible"] = True
        with self.assertRaises(ValueError):
            normalize(forged)

    def test_stage_shape_and_exception_code_are_strict(self):
        leaf = old_leaf()
        leaf.update(dismiss_stage="callback_returned", dismiss_exception_code=0)
        with self.assertRaises(ValueError):
            normalize(leaf)
        leaf["dismiss_stage"] = "callback_exception"
        with self.assertRaises(ValueError):
            normalize(leaf)
        leaf["dismiss_exception_code"] = 0xC0000005
        leaf["unexpected"] = True
        with self.assertRaises(ValueError):
            normalize(leaf)


if __name__ == "__main__":
    unittest.main()
