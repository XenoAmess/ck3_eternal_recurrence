from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
REPORT = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "open_kaishek_ee4fab9_b2_lazy_trigger_compatibility_audit_v1.json"
)


class OpenKaishekB2LazyTriggerCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_exact_companion_and_open_kaishek_horizon_is_pinned(self) -> None:
        self.assertEqual(self.report["status"], "GREEN_STATIC_NO_CODE_CHANGE")
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "ee4fab944737685b21d7cc1f18ff572cf0238d90",
        )
        self.assertEqual(
            self.report["open_kaishek"]["audit_commit"],
            "37cab82ec54a70fde79351af7240ed3d49c96adb",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["audit_commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])
        self.assertFalse(self.report["open_kaishek"]["code_changed"])

    def test_existing_ast_and_effect_file_boundaries_are_preserved(self) -> None:
        delta = self.report["companion_delta"]
        self.assertEqual(delta["product_corpus_paths_changed"], 20)
        self.assertEqual(delta["trigger_if_assignment_line_delta"], 65)
        self.assertEqual(delta["trigger_else_assignment_line_delta"], 27)
        self.assertGreaterEqual(
            delta["minimum_top_level_effects_per_changed_file"], 1
        )
        self.assertLessEqual(
            delta["maximum_top_level_effects_per_changed_file"], 10
        )
        for key in (
            "lossless_entry_block_ast_already_supported",
            "trigger_if_conditional_key_role_already_supported",
            "trigger_else_lossless_generic_key_already_supported",
        ):
            self.assertTrue(delta[key], key)
        for key in (
            "changed_file_exceeds_ten_effects",
            "changed_file_exceeds_twenty_effects",
            "new_parser_construct",
            "parser_change_required",
            "validator_change_required",
            "ir_change_required",
            "runtime_change_required",
            "capability_change_required",
            "public_api_change_required",
        ):
            self.assertFalse(delta[key], key)

    def test_static_green_does_not_claim_ck3_semantics_or_live_readiness(self) -> None:
        semantic = self.report["ck3_semantic_evidence_boundary"]
        self.assertEqual(semantic["pre_fix_live_error_signatures"], 93)
        self.assertFalse(semantic["post_fix_live_retest_at_exact_commit"])
        self.assertFalse(semantic["open_kaishek_certifies_lazy_evaluation_semantics"])
        self.assertFalse(semantic["static_parse_green_is_ck3_semantic_proof"])
        verification = self.report["verification"]
        self.assertEqual(verification["open_maven_reactor"]["tests"], 147)
        self.assertEqual(verification["current_zhongguo_corpus"]["errors"], 0)
        self.assertEqual(
            verification["root_static_compatibility_verifier"]["checks"], 63
        )
        for value in self.report["execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
