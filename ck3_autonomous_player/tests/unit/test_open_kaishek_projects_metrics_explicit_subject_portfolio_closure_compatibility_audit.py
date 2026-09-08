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
    / "open_kaishek_projects_metrics_explicit_subject_portfolio_closure_compatibility_audit_v1.json"
)
G2_COMPATIBILITY = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_open_kaishek_compatibility_v1.json"
)


class OpenKaishekProjectsMetricsExplicitSubjectPortfolioClosureAuditTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.g2 = json.loads(G2_COMPATIBILITY.read_text(encoding="utf-8"))

    def test_report_identifies_exact_synced_commits_and_hashes(self) -> None:
        self.assertEqual(
            self.report["schema"],
            "xar.ck3.open_kaishek_projects_metrics_explicit_subject_portfolio_closure_compatibility_audit.v1",
        )
        self.assertEqual(
            self.report["status"],
            "SYNCED",
        )
        self.assertEqual(
            self.report["root"]["candidate_base_commit"],
            "45024edf723a75502728f8f07b345f4271697cfe",
        )
        self.assertEqual(
            self.report["open_kaishek"]["commit"],
            "d1c0362c1883c1c9ef66d4e5fc9e7c208fb1ba34",
        )
        self.assertEqual(
            self.report["open_kaishek"]["origin_main"],
            self.report["open_kaishek"]["commit"],
        )
        self.assertTrue(self.report["open_kaishek"]["clean"])
        expected_hashes = {
            "source_contract_sha256": "bea30b47cee6fdc66c04e48a42ebf5ac0115c62a8ea34698fcd0428530f4649a",
            "abi_sha256": "1624d793b9461dbf6d08c64f60219f3567bc9fdf2805afe94c60f6aaf4deac6c",
            "public_schema_sha256": "44f0429e8b5ab46db38611a9779198cefd97b0fe435c0c847f3cb57674732380",
            "python_contract_sha256": "b2dba9ee76457d0ec72bd87464eec145618e76482bb77d4b6687a03c88a60436",
        }
        for key, value in expected_hashes.items():
            self.assertEqual(self.report["root"][key], value)
            self.assertEqual(self.report["open_kaishek"][f"pinned_{key}"], value)
        self.assertEqual(
            self.report["open_kaishek"]["pinned_root_commit"],
            self.report["root"]["candidate_base_commit"],
        )

    def test_same_capability_now_has_a_new_public_contract_shape(self) -> None:
        delta = self.report["projects_metrics_delta"]
        self.assertFalse(delta["open_kaishek_change_required"])
        self.assertFalse(delta["capability_id_changed"])
        self.assertFalse(delta["schema_version_changed"])
        self.assertTrue(delta["mcp_parameter_additive_optional"])
        self.assertTrue(delta["legacy_mcp_calls_default_subject_to_paused_player"])
        self.assertTrue(delta["native_wire_shape_changed"])
        self.assertTrue(delta["native_subject_field_required"])
        self.assertTrue(delta["response_required_shape_changed"])
        self.assertEqual(
            delta["new_required_top_level_fields"],
            ["requested_subject_character_id", "credit_project_portfolio"],
        )
        self.assertEqual(len(delta["new_required_portfolio_fields"]), 10)
        self.assertEqual(
            delta["new_required_readiness_fields"],
            ["portfolio_observed", "portfolio_closed"],
        )
        self.assertEqual(
            (delta["allowlist_count_before"], delta["allowlist_count_after"]),
            (40, 49),
        )
        self.assertEqual(len(delta["new_allowlist_fields"]), 9)

    def test_sync_is_metadata_fixture_and_docs_not_new_runtime_semantics(self) -> None:
        delta = self.report["projects_metrics_delta"]
        for key in (
            "parser_vocabulary_change_required",
            "ir_change_required",
            "runtime_handler_change_required",
            "new_action_added",
            "default_candidate_enabled",
            "native_live_certification_promoted",
            "production_live_promoted",
        ):
            self.assertFalse(delta[key], key)
        required = self.report["required_open_kaishek_delta"]
        self.assertTrue(required["completed"])
        self.assertTrue(required["rebase_only"])
        self.assertTrue(required["merge_forbidden"])
        self.assertEqual(len(required["profile_metadata_and_descriptor"]), 2)
        self.assertEqual(len(required["fixture_and_preflight_coverage"]), 3)
        self.assertEqual(len(required["documentation"]), 2)

    def test_g2_semantics_stay_closed_after_exact_pin_sync(self) -> None:
        g2 = self.report["g2"]
        for key in (
            "semantic_change_required",
            "profile_change_required",
            "capability_change_required",
            "fixture_change_required",
            "pin_update_required_now",
        ):
            self.assertFalse(g2[key], key)
        self.assertFalse(g2["pin_update_required_after_open_kaishek_sync_commit"])
        self.assertEqual(
            g2["current_exact_open_kaishek_pin"],
            self.g2["root_binding"]["open_kaishek_commit"],
        )
        boundaries = self.report["boundaries"]
        self.assertTrue(boundaries["external_repository_modified_by_this_audit"])
        for key, value in boundaries.items():
            if key != "external_repository_modified_by_this_audit":
                self.assertFalse(value, key)

    def test_external_sync_verification_is_recorded(self) -> None:
        verification = self.report["verification"]
        self.assertTrue(verification["root_blob_hashes_match_open_kaishek_profile"])
        self.assertEqual(
            verification["open_kaishek_clean_package"],
            "BUILD_SUCCESS_12_MODULES_ZG361_53_TESTS_0_FAILURES_0_ERRORS",
        )
        self.assertEqual(verification["open_kaishek_cli_smoke"], "PASS")
        self.assertEqual(
            verification["open_kaishek_projects_fixture_preflight"],
            "GREEN_PARSER_VALIDATOR_0_DIAGNOSTICS",
        )
        self.assertEqual(
            verification["g2_cross_repository_verifier"], "GREEN_STATIC"
        )


if __name__ == "__main__":
    unittest.main()
