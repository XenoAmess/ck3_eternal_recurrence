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
    / "open_kaishek_ff89dcd_7aae7e0_compatibility_audit_v1.json"
)


class OpenKaishekG2PrivateCleanupDispatchCompatibilityAuditTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_exact_root_and_open_kaishek_commits_are_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_g2_private_cleanup_dispatch_compatibility_audit.v1",
        )
        self.assertEqual(
            self.report["status"],
            "STATIC_READY_PRIVATE_DISPATCH_LIVE_NOT_RUN",
        )
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "ff89dcdbefb9d8fc86ce4722df847946e96d0e81",
        )
        self.assertEqual(
            self.report["root"]["source_commit"],
            "7aae7e064b6e224dd3a5b95070b54d9205c32cf4",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "3c4e6982b5d821f1fcdb9c3ced2a581497c9a6eb",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_dispatch_is_private_exact_store_and_not_live(self) -> None:
        dispatch = self.report["private_cleanup_dispatch"]
        self.assertTrue(dispatch["open_kaishek_change_required"])
        self.assertTrue(dispatch["metadata_only"])
        self.assertTrue(dispatch["query_dispatch_present"])
        self.assertTrue(dispatch["query_private"])
        self.assertTrue(dispatch["query_read_only"])
        self.assertTrue(dispatch["adapter_issues_cleanup_query"])
        self.assertTrue(dispatch["war_id_absence_admission_only"])
        self.assertTrue(dispatch["destroyed_result_from_exact_stores"])
        self.assertTrue(dispatch["same_lifecycle_native_cleanup_required"])
        for key in (
            "capability_descriptor_added",
            "default_enabled",
            "live_tested",
            "external_cleanup_injection_allowed",
            "old_war_absence_sufficient",
            "public_capability_added",
            "production_live",
            "live_authorized",
            "public_readiness_promoted",
            "action_readiness_promoted",
            "source_specific_attribution_ready",
            "decision_ready",
            "automatic_surrender_ready",
            "gen_034_resolved",
        ):
            self.assertFalse(dispatch[key], key)

    def test_verification_and_t2_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (maven["tests"], maven["failures"], maven["errors"], maven["skipped"]),
            (147, 0, 0, 0),
        )
        self.assertEqual(verification["open_cleanup_metadata_tests"], 3)
        self.assertEqual(verification["root_focused_tests"], 22)
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
