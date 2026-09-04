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
    / "open_kaishek_714be35_projects_9536342_compatibility_audit_v1.json"
)


class OpenKaishekG2WarLossProjectsCompatibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_report_is_green_static_and_exactly_pinned(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_g2_war_loss_projects_compatibility_audit.v1",
        )
        self.assertEqual(self.report["status"], "GREEN_STATIC")
        self.assertEqual(
            self.report["root"]["g2_integration_commit"],
            "714be35d1e4420889e92775be10d7826b2508da1",
        )
        self.assertEqual(
            self.report["root"]["g2_candidate_commit"],
            "2911ed72b6179a5c8a19649deedfa919d235beb1",
        )
        self.assertEqual(
            self.report["root"]["projects_metrics_commit"],
            "953634265ebf298cec3f2cf3065060e577dc8d17",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "a54164625b3ebb7d738d16236ca3080686fa9984",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])

    def test_war_loss_remains_metadata_only_and_closed(self) -> None:
        candidate = self.report["war_bound_loss_candidate"]
        self.assertTrue(candidate["open_kaishek_change_required"])
        self.assertTrue(candidate["metadata_only"])
        self.assertTrue(candidate["read_only"])
        self.assertEqual(
            (
                candidate["frozen_pre_termination_soldiers"],
                candidate["destroyed_post_termination_soldiers"],
                candidate["proven_boundary_soldiers_lost"],
            ),
            (598, 0, 598),
        )
        self.assertEqual(
            candidate["static_artifact_sha256"],
            "6b85024d6964dd715d88f502c5d21bc6987a7debad2a309955e25f3334ddc991",
        )
        for key, value in candidate.items():
            if key not in {
                "open_kaishek_change_required",
                "metadata_only",
                "read_only",
                "static_artifact_sha256",
                "source_contract_sha256",
                "candidate_header_sha256",
                "candidate_source_sha256",
                "frozen_pre_termination_soldiers",
                "destroyed_post_termination_soldiers",
                "proven_boundary_soldiers_lost",
            }:
                self.assertFalse(value, key)

    def test_projects_syncs_only_real_public_schema_delta(self) -> None:
        projects = self.report["projects_metrics_delta"]
        self.assertTrue(projects["open_kaishek_change_required"])
        self.assertEqual(
            projects["public_schema_change"], "checkpoint_state-v2-required"
        )
        self.assertEqual(
            (
                projects["provider_allowlist_fields_before"],
                projects["provider_allowlist_fields_after"],
            ),
            (24, 40),
        )
        self.assertTrue(projects["direct_cp26_fields_provider_internal"])
        self.assertTrue(projects["central_stage_order_7_8_provider_internal"])
        self.assertEqual(
            projects["public_schema_sha256"],
            "3763b17f937d4c36c5643a41d54ccd449cd23a8f5f94cddb4a4edbed7bbdbfd4",
        )
        for key in (
            "default_candidate_enabled",
            "production_live",
            "parser_vocabulary_changed",
            "ir_changed",
            "runtime_handler_changed",
            "action_added",
        ):
            self.assertFalse(projects[key], key)

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
            (138, 0, 0, 0),
        )
        self.assertEqual(verification["open_domain_tests"], 8)
        self.assertEqual(verification["open_cli_smoke"], "PASS")
        self.assertEqual(verification["product_corpus"]["errors"], 0)
        verifier = verification["root_static_compatibility_verifier"]
        self.assertEqual(verifier["status"], "GREEN_STATIC")
        self.assertEqual(verifier["checks"], 45)
        self.assertTrue(verifier["all_checks"])
        for value in self.report["t2_execution_boundaries"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
