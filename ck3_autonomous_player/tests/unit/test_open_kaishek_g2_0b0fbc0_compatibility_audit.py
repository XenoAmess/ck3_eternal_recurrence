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
    / "open_kaishek_g2_0b0fbc0_compatibility_audit_v1.json"
)
G2_COMPATIBILITY = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_open_kaishek_compatibility_v1.json"
)


class OpenKaishekG2ProductionLeafCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.compatibility = json.loads(
            G2_COMPATIBILITY.read_text(encoding="utf-8")
        )

    def test_report_is_green_static_and_exactly_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_g2_production_leaf_compatibility_audit.v1",
        )
        self.assertEqual(self.report["status"], "GREEN_STATIC")
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "0b0fbc047610a8ef25f47a59f7b42c83c176d69e",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            self.compatibility["root_binding"]["open_kaishek_commit"],
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_public_contract_shape_is_unchanged(self) -> None:
        public = self.report["public_contract"]
        expected = self.compatibility["open_kaishek"]
        self.assertFalse(public["schema_changed"])
        for key in (
            "capability_id",
            "profile_id",
            "required_fields",
            "invariants",
        ):
            self.assertEqual(public[key], expected[key])
        decision = self.report["decision"]
        self.assertTrue(decision["open_kaishek_change_required"])
        for key, value in decision.items():
            if (
                key.endswith("_change_required")
                and key != "open_kaishek_change_required"
            ):
                self.assertFalse(value)

    def test_provider_transition_preserves_readiness_boundary(self) -> None:
        provider = self.report["provider_transition"]
        fixture = self.compatibility["provider_transition"]
        self.assertTrue(provider["private_leaf_reader_live_observed"])
        self.assertTrue(provider["default_production_leaf_reader_installed"])
        for key in (
            "default_production_binary_live_validated",
            "native_certified",
            "runtime_certified",
            "production_live",
            "expiry_observable",
        ):
            self.assertFalse(provider[key])
        for key in (
            "private_leaf_reader_live_observed",
            "default_production_leaf_reader_installed",
            "default_production_binary_live_validated",
            "expiry_observable",
        ):
            self.assertEqual(provider[key], fixture[key])

    def test_recorded_offline_verification_is_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (maven["tests"], maven["failures"], maven["errors"], maven["skipped"]),
            (136, 0, 0, 0),
        )
        self.assertEqual(verification["open_domain_tests"], 8)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["product_corpus"]["errors"], 0)
        self.assertEqual(
            verification["root_static_compatibility_verifier"], "GREEN_STATIC"
        )
        for value in self.report["boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
