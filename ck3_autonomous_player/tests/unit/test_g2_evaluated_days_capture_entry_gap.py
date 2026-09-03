from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
ARTIFACT = (
    REPO_ROOT
    / "artifacts"
    / "g2-open-kaishek-compatibility"
    / "2026-09-03"
    / "evaluated-days-capture-entry-gap-20260903T1325.json"
)
COMPATIBILITY = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_open_kaishek_compatibility_v1.json"
)
ABI = ROOT / "native_bridge" / "research" / "raiktor_truce_evaluator_callsite_v1_abi.json"


class G2EvaluatedDaysCaptureEntryGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.compatibility = json.loads(COMPATIBILITY.read_text(encoding="utf-8"))
        cls.abi = json.loads(ABI.read_text(encoding="utf-8"))

    def test_artifact_is_explicitly_static_and_fail_closed(self) -> None:
        self.assertEqual(
            self.artifact["schema"],
            "xar.ck3.g2_evaluated_days_capture_entry_gap.v1",
        )
        self.assertEqual(
            self.artifact["result"], "NO_CURRENT_USABLE_PAUSED_EVALUATOR_ENTRY"
        )
        scope = self.artifact["scope"]
        for key in (
            "ck3_started",
            "process_attached",
            "save_mutated",
            "mutation_sent",
            "public_abi_changed",
            "public_readiness_changed",
            "offset_or_allowlist_guess",
            "purchase_or_payment_action",
        ):
            self.assertFalse(scope[key])
        self.assertFalse(self.artifact["assessment"]["paused_evaluator_entry_available_now"])

    def test_current_pins_and_abi_are_cross_bound(self) -> None:
        pins = self.artifact["current_pins"]
        root_binding = self.compatibility["root_binding"]
        self.assertEqual(pins["root"]["capability_id"], root_binding["capability_id"])
        self.assertEqual(pins["root"]["profile_id"], root_binding["profile_id"])
        self.assertEqual(
            pins["root"]["open_kaishek_commit"], root_binding["open_kaishek_commit"]
        )
        self.assertEqual(pins["open_kaishek"]["head"], root_binding["open_kaishek_commit"])
        self.assertEqual(pins["open_kaishek"]["origin_main"], pins["open_kaishek"]["head"])
        self.assertTrue(pins["open_kaishek"]["clean"])

        build = self.artifact["exact_build_review"]
        self.assertEqual(build["executable_sha256"], self.abi["build"]["executable_sha256"])
        abi = build["abi_fixture"]
        self.assertEqual(abi["status"], "static-ready")
        self.assertEqual(abi["evaluator_rva"], self.abi["evaluator"]["rva"])
        self.assertEqual(abi["shared_contract"]["duration_offset"], "0x108")
        self.assertEqual(abi["shared_contract"]["evaluation_context_offset"], "0x28")
        self.assertFalse(abi["shared_contract"]["expiry_semantics_observed"])

    def test_existing_entries_and_single_slot_plan_remain_bounded(self) -> None:
        paused = self.artifact["paused_capture_evidence"]["latest_paused_semantic_report"]
        self.assertTrue(paused["two_equal_read_only_terms_queries"])
        self.assertFalse(paused["evaluated_days_observable"])
        self.assertIsNone(paused["evaluated_days"])
        self.assertEqual(paused["mutation_commands"], [])
        self.assertFalse(paused["time_advanced"])

        passive = self.artifact["paused_capture_evidence"]["passive_callsite_candidate"]
        self.assertFalse(passive["direct_evaluator_enabled"])
        self.assertEqual(passive["mcp_queries"], [])
        self.assertEqual(passive["evaluator_requests"], [])
        self.assertFalse(passive["usable_for_evaluated_days"])

        shape = self.artifact["paused_capture_evidence"]["validated_index7_shape"]
        self.assertEqual(shape["rows"], 2)
        self.assertTrue(shape["byte_semantic_equal"])
        self.assertEqual(shape["truce_vtable_rva"], "0x4461CA8")
        self.assertEqual(shape["duration_script_value_relation"], "truce_effect+0x108")
        self.assertFalse(shape["duration_evaluator_called"])
        self.assertFalse(shape["evaluated_days_observed"])
        self.assertEqual(shape["mutation_commands"], [])

        direct = self.artifact["paused_capture_evidence"]["direct_evaluator_candidate"]
        self.assertNotEqual(
            direct["bound_open_kaishek_commit"],
            direct["current_open_kaishek_commit"],
        )
        self.assertFalse(direct["usable_for_current_pin"])
        self.assertIsNone(direct["historical_evaluated_days"])

        plan = self.artifact["next_single_slot_capture"]
        self.assertFalse(plan["run_authorized_in_this_review"])
        self.assertEqual(plan["slot_count"], 1)
        self.assertFalse(plan["instrumentation_modes"]["passive_observer_and_direct_capture_combined"])
        self.assertEqual(len(plan["checklist"]), 7)
        self.assertEqual(
            plan["checklist"][5]["must_hold"],
            [
                "same_paused_frame=true",
                "evaluator_call_count=2",
                "evaluator_results_equal=true",
                "evaluator_results_nonnegative=true",
                "cleanup_proven=true",
            ],
        )


if __name__ == "__main__":
    unittest.main()
