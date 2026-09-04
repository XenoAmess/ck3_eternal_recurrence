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
    / "open_kaishek_a01f8cb_beb1774_compatibility_audit_v1.json"
)


class OpenKaishekG2CleanupExpiryAdapterCompatibilityAuditTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_is_exactly_pinned_and_live_blocked(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_g2_postwar_cleanup_expiry_adapter_compatibility_audit.v1",
        )
        self.assertEqual(
            self.report["status"],
            "GREEN_STATIC_ADAPTER_LIVE_BLOCKED_ON_CLEANUP_DISPATCH",
        )
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "a01f8cb684d39e2ea8e95fbf0f20f170b6f1a396",
        )
        self.assertEqual(
            self.report["root"]["source_commit"],
            "beb17743a6440650eec2ca9c0bf270733bce2527",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "1ca6a455d63d1ff6e92389c7fff5b39681863524",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_adapter_records_only_metadata_and_negative_boundary(self) -> None:
        adapter = self.report["postwar_cleanup_expiry_adapter"]
        self.assertTrue(adapter["open_kaishek_change_required"])
        self.assertTrue(adapter["metadata_only"])
        self.assertTrue(adapter["actual_expiry_query_dispatch_present"])
        self.assertTrue(adapter["cleanup_candidate_library_present"])
        self.assertTrue(adapter["same_lifecycle_native_cleanup_required"])
        self.assertTrue(adapter["synthetic_fixture"])
        for key in (
            "capability_descriptor_added",
            "cleanup_query_dispatch_present",
            "old_war_absence_sufficient",
            "python_adapter_may_infer_cleanup",
            "fixture_is_live",
            "public_capability_added",
            "live_authorized",
            "public_readiness_promoted",
            "action_readiness_promoted",
            "runtime_cleanup_ready",
            "source_specific_attribution_ready",
            "decision_ready",
            "automatic_surrender_ready",
            "gen_034_resolved",
        ):
            self.assertFalse(adapter[key], key)

    def test_verification_and_execution_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (maven["tests"], maven["failures"], maven["errors"], maven["skipped"]),
            (147, 0, 0, 0),
        )
        self.assertEqual(verification["open_cleanup_adapter_metadata_tests"], 3)
        self.assertEqual(verification["root_focused_tests"], 16)
        self.assertEqual(verification["root_audit_tests"], 3)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["main_product_corpus"]["errors"], 0)
        self.assertEqual(verification["zhongguo_product_corpus"]["errors"], 0)
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["status"], "GREEN_STATIC")
        self.assertEqual(verifier["checks"], 59)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["t2_execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
