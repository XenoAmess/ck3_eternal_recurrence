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
    / "open_kaishek_cac1e85_promotion_candidate_compatibility_audit_v1.json"
)


class OpenKaishekPromotionCandidateCompatibilityAuditTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_exact_root_and_open_kaishek_commits_are_pinned(self) -> None:
        self.assertEqual(
            self.report["status"],
            "STATIC_READY_PRIVATE_CANDIDATE_DEFAULT_OFF_LIVE_NOT_RUN",
        )
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "cac1e85b616827a9ae11d755dd71f119325e6f3f",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "6b9e9c239430c5f364465f5a027d90de14464129",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_default_off_and_explicit_on_boundary_is_exact(self) -> None:
        candidate = self.report["promotion_compensation_candidate"]
        self.assertTrue(candidate["private_candidate_advertises"])
        self.assertTrue(candidate["descriptor_read_only"])
        self.assertTrue(candidate["descriptor_deterministic"])
        for key in (
            "default_switch_enabled",
            "default_adapter_advertised",
            "descriptor_native_certified",
            "descriptor_runtime_certified",
            "candidate_live_tested",
            "public_api_changed",
            "production_live",
        ):
            self.assertFalse(candidate[key], key)
        native = self.report["native_static_verification"]
        self.assertFalse(native["default_off"]["cmake_option"])
        self.assertTrue(native["explicit_on"]["cmake_option"])
        for mode in ("default_off", "explicit_on"):
            self.assertEqual(native[mode]["registry_tests"], 1)
            self.assertEqual(native[mode]["registry_failures"], 0)

    def test_static_verification_and_execution_boundaries_are_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (maven["tests"], maven["failures"], maven["errors"], maven["skipped"]),
            (147, 0, 0, 0),
        )
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["zhongguo_product_corpus"]["errors"], 0)
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["checks"], 63)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
