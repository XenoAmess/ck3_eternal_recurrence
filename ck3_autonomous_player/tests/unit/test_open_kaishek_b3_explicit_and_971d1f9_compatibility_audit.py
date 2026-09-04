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
    / "open_kaishek_b3_explicit_and_971d1f9_compatibility_audit_v1.json"
)


class OpenKaishekB3ExplicitAndCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_exact_commits_and_no_code_change_are_pinned(self) -> None:
        self.assertEqual(self.report["status"], "GREEN_STATIC_NO_CODE_CHANGE")
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "971d1f9cdf0220e964e0064879ed301df4b3fb99",
        )
        self.assertEqual(
            self.report["open_kaishek"]["audit_commit"],
            "b10b762eefaaf13eb53ded19b88a553d940aed24",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["audit_commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])
        self.assertFalse(self.report["open_kaishek"]["code_changed"])

    def test_only_existing_explicit_and_structure_changed(self) -> None:
        delta = self.report["companion_delta"]
        self.assertEqual(delta["product_corpus_paths_changed"], 1)
        self.assertEqual(delta["byte_delta"], 74)
        self.assertEqual(delta["explicit_and_count_delta"], 1)
        for key in (
            "new_parser_construct",
            "new_validator_schema",
            "metadata_contract_changed",
            "frontend_first_enters_product_corpus",
            "path_length_workaround_enters_product_corpus",
            "parser_change_required",
            "validator_change_required",
            "ir_change_required",
            "runtime_change_required",
            "capability_change_required",
        ):
            self.assertFalse(delta[key], key)

    def test_parser_results_and_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        self.assertEqual(
            verification["baseline_zhongguo_corpus"]["errors"], 0
        )
        self.assertEqual(
            verification["current_zhongguo_corpus"]["errors"], 0
        )
        self.assertEqual(
            verification["current_main_product_corpus"]["errors"], 0
        )
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["checks"], 59)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
