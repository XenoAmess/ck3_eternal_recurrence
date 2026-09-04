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
    / "open_kaishek_d53befa_f730aeb_compatibility_audit_v1.json"
)


class OpenKaishekB7PromotionTransportCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_is_green_static_and_exactly_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_b7_promotion_transport_compatibility_audit.v1",
        )
        self.assertEqual(self.report["status"], "GREEN_STATIC")
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "d53befaa4872662562f5db5d31757ca731e799e0",
        )
        self.assertEqual(
            self.report["root"]["b3_localization_freezer_commit"],
            "f730aeb677066e39aa7f19e53c66e2a84b842f88",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "270f8f52098191cff37f33cef24f441a36297b5b",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_only_fail_closed_transports_are_recorded_as_advertised(self) -> None:
        promotion = self.report["promotion_source_transport"]
        self.assertTrue(promotion["open_kaishek_change_required"])
        self.assertTrue(promotion["transport_capabilities_advertised"])
        self.assertEqual(promotion["fixed_widget_count"], 5)
        for key in (
            "query_product_capability_advertised",
            "action_product_capability_advertised",
            "query_native_certified",
            "query_runtime_certified",
            "action_native_certified",
            "action_runtime_certified",
            "action_ack_is_state_evidence",
            "production_live_ready",
        ):
            self.assertFalse(promotion[key], key)

    def test_b3_localization_freezer_is_a_hash_bound_no_change(self) -> None:
        b3 = self.report["b3_localization_freezer"]
        self.assertFalse(b3["open_kaishek_change_required"])
        self.assertTrue(b3["changed_files_are_tools_only"])
        for key, value in b3.items():
            if key not in {"open_kaishek_change_required", "changed_files_are_tools_only"}:
                self.assertFalse(value, key)

    def test_recorded_offline_verification_and_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (
                maven["tests"],
                maven["failures"],
                maven["errors"],
                maven["skipped"],
            ),
            (141, 0, 0, 0),
        )
        self.assertEqual(verification["open_domain_tests"], 8)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["main_product_corpus"]["errors"], 0)
        self.assertEqual(verification["zhongguo_product_corpus"]["errors"], 0)
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["status"], "GREEN_STATIC")
        self.assertEqual(verifier["checks"], 51)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["t2_execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
