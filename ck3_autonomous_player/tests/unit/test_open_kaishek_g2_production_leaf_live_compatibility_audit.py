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
    / "open_kaishek_g2_production_leaf_live_compatibility_audit_v1.json"
)
G2_COMPATIBILITY = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_open_kaishek_compatibility_v1.json"
)


class OpenKaishekG2ProductionLeafLiveCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.compatibility = json.loads(
            G2_COMPATIBILITY.read_text(encoding="utf-8")
        )

    def test_report_is_green_and_exactly_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_g2_production_leaf_live_compatibility_audit.v1",
        )
        self.assertEqual(self.report["status"], "GREEN_STATIC")
        self.assertEqual(
            self.report["capability_stage"], "production-live primitive"
        )
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "a37bfcc6fdc1c852c7f5e167449b68fc9b5c5c02",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            self.compatibility["root_binding"]["open_kaishek_commit"],
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertEqual(
            self.report["open_kaishek"]["default_checkout_head"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_live_evidence_freezes_dual_query_and_nonmutation(self) -> None:
        evidence = self.report["live_evidence"]
        self.assertEqual(
            evidence["report_sha256"],
            "ad6eef83dcca07c3ae280f01cade6bbd0c1912ff0e086d797604d5f06c99f7c2",
        )
        self.assertEqual(evidence["elapsed_seconds"], 151.766)
        self.assertEqual(
            (evidence["first_query_sequence"], evidence["second_query_sequence"]),
            (1, 2),
        )
        self.assertEqual(evidence["evaluated_days"], 1825)
        self.assertTrue(evidence["paused"])
        self.assertTrue(evidence["normalized_queries_equal"])
        self.assertFalse(evidence["time_advanced"])
        self.assertEqual(evidence["mutation_commands"], [])
        self.assertTrue(evidence["source_inputs_unchanged"])
        self.assertTrue(evidence["cleanup_proven"])
        self.assertEqual(evidence["ck3_processes_after_cleanup"], 0)

    def test_only_read_only_duration_primitive_is_promoted(self) -> None:
        public = self.report["public_contract"]
        fixture = self.compatibility["open_kaishek"]
        provider = self.compatibility["provider_transition"]
        self.assertFalse(public["schema_changed"])
        self.assertTrue(public["read_only"])
        self.assertTrue(public["native_certified"])
        self.assertTrue(public["runtime_certified"])
        self.assertTrue(public["production_live"])
        self.assertEqual(public["capability_id"], fixture["capability_id"])
        self.assertEqual(public["profile_id"], fixture["profile_id"])
        self.assertTrue(provider["production_live_read_only_primitive"])
        for value in self.report["closed_boundaries"].values():
            self.assertFalse(value)

    def test_offline_verification_and_t2_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (maven["tests"], maven["failures"], maven["errors"], maven["skipped"]),
            (136, 0, 0, 0),
        )
        self.assertEqual(verification["open_domain_tests"], 8)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["product_corpus"]["errors"], 0)
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["status"], "GREEN_STATIC")
        self.assertEqual(verifier["checks"], 37)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["t2_execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
