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
    / "open_kaishek_04c1a00_f16cdf0_compatibility_audit_v1.json"
)


class OpenKaishekG2ActualExpiryCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_is_green_static_and_exactly_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_g2_actual_expiry_compatibility_audit.v1",
        )
        self.assertEqual(self.report["status"], "GREEN_STATIC")
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "04c1a00f0599378dfa8810be14ce535b2ed17f21",
        )
        self.assertEqual(
            self.report["root"]["checkout_base_commit"],
            "a77b2d5b4db5039f461ef5c3656f53679eab75c3",
        )
        self.assertEqual(
            self.report["root"]["retention_ticket_commit"],
            "f16cdf0d63df06f4e6b0bbde08f6324e25c3d885",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "1394dca6976c79913da740367898c0fd35e102e7",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_actual_expiry_remains_default_off_and_uncertified(self) -> None:
        candidate = self.report["actual_truce_expiry_candidate"]
        self.assertTrue(candidate["open_kaishek_change_required"])
        self.assertTrue(candidate["metadata_only"])
        self.assertTrue(candidate["read_only"])
        self.assertFalse(candidate["capability_descriptor_added"])
        self.assertEqual(candidate["cmake_default"], "OFF")
        for key in (
            "capability_advertised_by_default",
            "ack_sufficient",
            "native_certified",
            "runtime_certified",
            "production_live",
            "actual_expiry_observable",
        ):
            self.assertFalse(candidate[key], key)

    def test_retention_ticket_is_pinned_without_action_readiness(self) -> None:
        ticket = self.report["retention_ticket"]
        self.assertTrue(ticket["open_kaishek_change_required"])
        self.assertTrue(ticket["metadata_only"])
        self.assertEqual(
            (
                ticket["retained_pre_termination_soldiers"],
                ticket["retained_evaluated_days"],
            ),
            (598, 1825),
        )
        for key in (
            "live_authorized",
            "termination_action_bound",
            "decision_ready",
            "automatic_surrender_ready",
            "gen_034_resolved",
        ):
            self.assertFalse(ticket[key], key)

    def test_recorded_verification_and_execution_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (
                maven["tests"],
                maven["failures"],
                maven["errors"],
                maven["skipped"],
            ),
            (144, 0, 0, 0),
        )
        self.assertEqual(verification["open_domain_tests"], 8)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["main_product_corpus"]["errors"], 0)
        self.assertEqual(verification["zhongguo_product_corpus"]["errors"], 0)
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["status"], "GREEN_STATIC")
        self.assertEqual(verifier["checks"], 55)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["t2_execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
