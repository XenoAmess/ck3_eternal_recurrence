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
    / "open_kaishek_ce458af_compatibility_audit_v1.json"
)
G2_COMPATIBILITY = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_open_kaishek_compatibility_v1.json"
)


class OpenKaishekCe458afCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.g2 = json.loads(G2_COMPATIBILITY.read_text(encoding="utf-8"))

    def test_report_is_green_static_and_exactly_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_incremental_compatibility_audit.v1",
        )
        self.assertEqual(self.report["status"], "GREEN_STATIC")
        self.assertEqual(
            self.report["root"]["canonical_commit"],
            "ce458af71a2a44decc085766720082a8b724edb8",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "98c13d02ba1c772836a35f782716a0b3679b7ee8",
        )
        self.assertNotEqual(
            self.report["open_kaishek"]["commit"],
            self.g2["root_binding"]["open_kaishek_commit"],
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_only_career_hc_requires_an_open_kaishek_change(self) -> None:
        decisions = self.report["decisions"]
        changed = [
            name
            for name, decision in decisions.items()
            if decision["open_kaishek_change_required"]
        ]
        self.assertEqual(changed, ["career_hc_workforce"])
        career = decisions["career_hc_workforce"]
        self.assertEqual(
            career["capability"],
            "game.command.query-zhongguo-career-hc-workforce-postcondition-v1",
        )
        self.assertFalse(career["default_adapter_advertised"])
        self.assertFalse(career["downstream_action_advertised"])
        self.assertFalse(career["native_certified"])
        self.assertFalse(career["runtime_certified"])

    def test_reviewed_no_change_boundaries_remain_closed(self) -> None:
        decisions = self.report["decisions"]
        self.assertFalse(
            decisions["projects_metrics"]["production_advertisement_promoted"]
        )
        self.assertFalse(decisions["promotion_compensation"]["production_live_ready"])
        self.assertFalse(decisions["g2_leaf_context"]["production_live"])
        for value in self.report["boundaries"].values():
            self.assertFalse(value)

    def test_recorded_offline_verification_is_green(self) -> None:
        verification = self.report["verification"]
        maven = verification["open_maven_reactor"]
        self.assertEqual(
            (maven["tests"], maven["failures"], maven["errors"], maven["skipped"]),
            (135, 0, 0, 0),
        )
        self.assertEqual(verification["open_domain_tests"], 8)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["product_corpus"]["errors"], 0)
        self.assertEqual(verification["root_contract_tests"], 35)
        self.assertEqual(verification["root_seam_tests"], 32)


if __name__ == "__main__":
    unittest.main()
