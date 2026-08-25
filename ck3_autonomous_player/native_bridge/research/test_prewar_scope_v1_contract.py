#!/usr/bin/env python3
"""Validate the standalone prewar preview ABI and synthetic source contract."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
ABI_PATH = HERE / "prewar_scope_v1_abi.json"
FIXTURE_PATH = HERE / "fixtures" / "prewar_scope_v1_source_contract.json"


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def project_objective_provinces(
    target_title_ids: list[int], title_rows: list[dict[str, object]]
) -> list[int]:
    """Mirror the bounded title-tier contract for the synthetic source graph."""

    by_id = {int(row["title_id"]): row for row in title_rows}
    provinces: list[int] = []
    seen_provinces: set[int] = set()
    resolved_titles = 0

    def visit(title_id: int, depth: int) -> None:
        nonlocal resolved_titles
        if depth > 8:
            raise AssertionError("fixture title hierarchy exceeds depth bound")
        resolved_titles += 1
        if resolved_titles > 4096:
            raise AssertionError("fixture title hierarchy exceeds title budget")
        row = by_id[title_id]
        if not row["full_id_matches"]:
            raise AssertionError("fixture contains stale full TitleID")
        tier = int(row["tier"])
        child_ids = [int(value) for value in row["de_jure_child_title_ids"]]
        if tier == 1:
            province_id = int(row["barony_province_id"])
            if province_id not in seen_provinces:
                seen_provinces.add(province_id)
                provinces.append(province_id)
            return
        if tier == 2:
            if not child_ids:
                raise AssertionError("county fixture lacks a capital barony")
            visit(child_ids[0], depth + 1)
            return
        if tier < 1:
            raise AssertionError("fixture title has an invalid tier")
        for child_id in child_ids:
            visit(child_id, depth + 1)

    for target_title_id in target_title_ids:
        visit(target_title_id, 0)
    return provinces


class PrewarScopeStaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.abi = load_json(ABI_PATH)
        cls.fixture = load_json(FIXTURE_PATH)

    def test_exact_build_and_non_production_boundary(self) -> None:
        self.assertEqual(self.abi["schema_version"], 1)
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.abi["contract"], self.fixture["contract"])
        self.assertEqual(self.abi["game_version"], self.fixture["game_version"])
        self.assertEqual(
            self.abi["ck3_exe_sha256"], self.fixture["ck3_exe_sha256"]
        )
        self.assertFalse(self.abi["advertised"])
        self.assertFalse(self.abi["production_wired"])
        self.assertFalse(self.abi["live_validated"])
        self.assertTrue(self.fixture["not_live_evidence"])
        readiness = self.abi["readiness"]
        self.assertTrue(readiness["objective_provinces_static_ready"])
        self.assertFalse(readiness["objective_provinces_live_ready"])
        self.assertFalse(readiness["objective_provinces_ready"])
        self.assertFalse(readiness["capability_advertised"])

    def test_root_chain_is_vtable_gated_and_not_war_overview(self) -> None:
        root = self.abi["ownership_and_root"]
        self.assertEqual(root["global_owner_slot_rva"], "0x570F7B8")
        steps = root["steps"]
        self.assertEqual(
            [step.get("validation") for step in steps[1:]],
            [
                "vtable == module+0x40B1D30",
                "vtable == module+0x40AF630",
                "vtable == module+0x411DE90",
            ],
        )
        boundary = self.abi["type_boundary"]
        self.assertFalse(boundary["preview_cwar_exists"])
        self.assertNotEqual(
            boundary["declare_window"]["primary_vtable_rva"],
            boundary["war_overview_window"]["primary_vtable_rva"],
        )
        self.assertIn("not a WarID", boundary["declare_plus_0x1298"])
        fixture_root = self.fixture["source_root_chain"]
        self.assertTrue(fixture_root["declare_parent_backpointer_matches_handler"])
        self.assertTrue(
            fixture_root["declare_context_matches_handler_current_context"]
        )
        required = root["active_window_predicate"]["known_required_fields"]
        self.assertTrue(any("declare+0xD0" in field for field in required))
        self.assertTrue(any("handler+0xF0" in field for field in required))
        active = root["active_window_predicate"]
        self.assertEqual(active["predicate_rva"], "0x1F30970")
        self.assertIn("0x36EBB00", active["call_boundary"])
        self.assertTrue(fixture_root["gui_state_predicate_mirrored_active"])

    def test_selected_materializer_is_gui_revision_not_preview_war(self) -> None:
        lifecycle = self.abi["selected_declaration"]["materialization_lifecycle"]
        self.assertEqual(lifecycle["selected_row_copier_rva"], "0x108A200")
        self.assertIn("0x1085F4C materializer", lifecycle["cb_row_change_sequence"])
        self.assertEqual(
            lifecycle["title_row_change_materializer_call"], "0x108A4B9"
        )
        self.assertIn("no preview CWar", lifecycle["meaning"])

    def test_send_materializer_binds_real_cwar_declaration_payload(self) -> None:
        selected = self.abi["selected_declaration"]
        submit = selected["submit_materialization"]
        payload_type = self.abi["type_boundary"]["war_declaration_payload"]
        source = self.fixture["source_command_bound_war_declaration"]
        preview = self.fixture["source_active_declare_preview"]
        selected_titles = [
            row["title_id"] for row in preview["title_rows"] if row["selected"]
        ]
        self.assertEqual(submit["send_binding_registration_rva"], "0x14E300")
        self.assertEqual(submit["command_materializer_rva"], "0x1087C80")
        self.assertEqual(submit["war_declaration_vtable_gate"], "module+0x411DAA0")
        self.assertEqual(payload_type["primary_vtable_rva"], source["vtable_rva"])
        self.assertEqual(payload_type["factory_registry_index"], 13)
        self.assertEqual(source["special_interaction_registry_index"], 13)
        self.assertEqual(
            source["casus_belli_database_ordinal"],
            preview["selected_casus_belli"]["database_ordinal"],
        )
        self.assertEqual(
            source["casus_belli_canonical_key"],
            preview["selected_casus_belli"]["canonical_key"],
        )
        self.assertEqual(
            source["claimant_character_id"],
            preview["selected_casus_belli"]["claimant_character_id"],
        )
        self.assertEqual(source["target_title_ids"], selected_titles)
        self.assertNotEqual(
            source["target_title_ids"],
            preview["selected_casus_belli"]["embedded_target_title_ids"],
        )
        self.assertTrue(source["command_clone_preserves_payload"])
        self.assertTrue(source["cwar_builder_targeted_titles_identity"])
        self.assertIn("vtable+0x40", submit["executor_special_virtual_call"])
        self.assertEqual(submit["cwar_declaration_execute_rva"], "0x24D7690")

    def test_selected_preview_uniquely_binds_declarable_row(self) -> None:
        snapshot = self.fixture["source_snapshot"]
        preview = self.fixture["source_active_declare_preview"]
        selected = preview["selected_casus_belli"]
        selected_titles = [
            row["title_id"] for row in preview["title_rows"] if row["selected"]
        ]
        matches = [
            row
            for row in snapshot["declarable_wars"]
            if row["target_character_id"]
            == preview["interaction_recipient_character_id"]
            and row["casus_belli_index"] == selected["database_ordinal"]
            and row["casus_belli_key"] == selected["canonical_key"]
            and row["claimant_character_id"] == selected["claimant_character_id"]
            and row["target_title_ids"] == selected_titles
        ]
        self.assertEqual(len(matches), 1)
        expected = self.fixture["expected_projection"]["candidate_binding"]
        self.assertEqual(matches[0]["declaration_id"], expected["declaration_id"])
        self.assertEqual(selected_titles, expected["objective_title_ids"])
        self.assertNotEqual(
            selected["embedded_target_title_ids"], expected["objective_title_ids"]
        )

    def test_forced_defender_reason_codes_remain_raw_and_typed(self) -> None:
        abi_reasons = self.abi["forced_defender_preview"]["reason_codes"]
        raw_rows = self.fixture["source_active_declare_preview"][
            "forced_defender_rows"
        ]
        expected_rows = self.fixture["expected_projection"]["participants"][2:]
        self.assertEqual(
            [row["native_reason_code"] for row in raw_rows],
            [row["native_reason_code"] for row in expected_rows],
        )
        for row in expected_rows:
            reason = abi_reasons[str(row["native_reason_code"])]
            self.assertEqual(row["reason"], reason["semantic"])
            self.assertEqual(
                row["join_certainty"], "native_preview_forced_current_frame"
            )
        faith_join = abi_reasons["1"]
        self.assertIn("RCX actor Character*", faith_join["collector_abi"])
        self.assertTrue(faith_join["collector_unresolved_call_boundary"])

    def test_forced_tributary_contract_subset_preserves_native_order(self) -> None:
        abi = self.abi["forced_tributary_contract_participants"]
        source = self.fixture["source_subject_contracts"]
        expected = self.fixture["expected_projection"][
            "forced_tributary_contract_participants"
        ]
        self.assertEqual(abi["subject_contract_type"]["rtti_name"], ".?AVCSubjectContract@@")
        self.assertEqual(
            abi["subject_contract_type"]["deleting_destructor_rva"],
            "0x2251B90",
        )
        self.assertEqual(
            abi["subject_contract_type"]["core_destructor_rva"],
            "0x2251C40",
        )
        self.assertEqual(abi["storage"]["slot_rva"], "0x570CCA0")
        self.assertEqual(abi["storage"]["fallback_object_rva"], "0x570CC50")
        self.assertIn("rejects fallback", abi["storage"]["fallback_policy"])
        self.assertEqual(abi["obligation"]["contract_predicate_rva"], "0x2255360")
        self.assertEqual(abi["obligation"]["term_default_comparator_rva"], "0x2253C40")
        self.assertEqual(
            abi["obligation"]["database_singleton_slot_rva"], "0x570C790"
        )
        self.assertTrue(source["database_singleton_nonnull"])
        self.assertTrue(source["obligation_term_pointer_matches_database_slot"])
        self.assertEqual(abi["war_builder"]["forced_contract_stage_rva"], "0x27A1EC0")
        self.assertEqual(abi["war_builder"]["participant_mutator_rva"], "0x2225FB0")
        self.assertEqual(
            abi["pdata_ranges"]["forced_contract_stage"],
            "0x27A1EC0..0x27A214B",
        )
        self.assertTrue(source["two_samples_equal"])

        by_id = {
            int(row["subject_contract_id"]): row
            for row in source["resolved_contracts"]
        }
        projected: list[tuple[int, str, int, int, int, int]] = []
        for primary in source["primaries"]:
            side = str(primary["side"])
            source_primary = int(primary["source_primary_character_id"])
            opposing_primary = int(primary["opposing_primary_character_id"])
            for native_order, raw_contract_id in enumerate(
                primary["subject_contract_ids_native_order"]
            ):
                contract_id = int(raw_contract_id)
                row = by_id[contract_id]
                self.assertTrue(row["full_id_matches"])
                self.assertTrue(row["subject_full_id_matches"])
                self.assertTrue(row["suzerain_full_id_matches"])
                self.assertTrue(row["obligation_term_matches_database_slot"])
                self.assertEqual(int(row["suzerain_character_id"]), source_primary)
                if not row["obligation_term_present"]:
                    continue
                active = int(row["active_level_index_raw"])
                default = int(row["default_level_index_raw"])
                if active == default:
                    continue
                subject = int(row["subject_character_id"])
                if side == "attacker" and subject == opposing_primary:
                    continue
                projected.append(
                    (subject, side, source_primary, contract_id, native_order, active)
                )

        self.assertEqual(
            projected,
            [
                (
                    int(row["character_id"]),
                    str(row["side"]),
                    int(row["source_primary_character_id"]),
                    int(row["subject_contract_id"]),
                    int(row["source_contract_native_order"]),
                    int(row["active_level_index_raw"]),
                )
                for row in expected
            ],
        )
        self.assertEqual(
            {row["source"] for row in expected},
            {"native_forced_tributary_contract"},
        )
        self.assertEqual(
            {row["inclusion_reason"] for row in expected},
            {"nondefault_tributary_war_participation_obligation"},
        )
        self.assertEqual(
            {row["obligation_type_key"] for row in expected},
            {"tributary_war_participation_obligation"},
        )
        self.assertEqual(
            {row["join_certainty"] for row in expected},
            {"native_builder_contract_forced_current_snapshot"},
        )
        self.assertNotIn(29097, {row[0] for row in projected})
        self.assertNotIn(4102, {row[0] for row in projected})
        self.assertNotIn(4202, {row[0] for row in projected})
        self.assertIn((29829, "defender", 29097, 150994950, 2, 1), projected)
        self.assertEqual(
            [
                row["source_contract_native_order"]
                for row in expected
                if row["side"] == "defender"
            ],
            [1, 2],
        )
        self.assertEqual(
            {
                row["expected_failure_stage"]
                for row in source["negative_vectors"]
            },
            {
                "subject_contract_identity",
                "subject_character_identity",
                "subject_contract_obligation_term_identity",
            },
        )

    def test_public_army_and_native_carmy_ids_are_distinct(self) -> None:
        expected = self.fixture["expected_projection"]
        participants = {
            row["character_id"] for row in expected["participants"]
        }
        expected_armies = expected["current_raised_armies"]
        self.assertTrue(
            all(
                row["army_id"] != row["native_carmy_id"]
                for row in expected_armies
            )
        )
        scope = self.abi["unit_and_army_scope"]
        self.assertEqual(scope["carmy_storage_slot_rva"], "0x570C730")
        self.assertEqual(
            scope["carmy_layout"]["public_army_id_backlink"].split()[0],
            "+0x124",
        )
        self.assertTrue(
            all(row["owner_character_id"] in participants for row in expected_armies)
        )
        self.assertNotIn(
            4999, {row["owner_character_id"] for row in expected_armies}
        )
        self.assertTrue(
            all(
                row["carmy_backlink_matches"]
                for row in self.fixture["source_cunits"]
                if row["owner_character_id"] in participants
            )
        )

    def test_selected_titles_project_to_exact_objective_provinces(self) -> None:
        source = self.fixture["source_command_bound_war_declaration"]
        expected = self.fixture["expected_projection"]["candidate_binding"]
        actual = project_objective_provinces(
            source["target_title_ids"], self.fixture["source_landed_titles"]
        )
        self.assertEqual(actual, [2585])
        self.assertEqual(actual, expected["objective_province_ids"])
        objective = self.abi["objective_arrival_contact"]["objective_province_ids"]
        self.assertEqual(objective["status"], "static_closed_live_pending")
        self.assertIn("verbatim", objective["identity_chain"]["cwar_target_array_copy"])
        self.assertEqual(
            objective["landed_title_projection"]["recursive_walker_rva"],
            "0x20B4D50",
        )

    def test_partial_readiness_never_claims_encounter_forecast(self) -> None:
        readiness = self.fixture["expected_projection"]["readiness"]
        for ready_key in (
            "exact_build_ready",
            "active_preview_root_ready",
            "candidate_binding_ready",
            "primary_participants_ready",
            "forced_defender_preview_ready",
            "forced_tributary_contract_participants_static_ready",
            "objective_title_ids_ready",
            "objective_provinces_static_ready",
            "objective_provinces_ready",
            "current_raised_armies_ready",
        ):
            self.assertTrue(readiness[ready_key], ready_key)
        for blocked_key in (
            "complete_initial_participants_ready",
            "forced_tributary_contract_participants_live_ready",
            "forced_tributary_contract_participants_ready",
            "objective_provinces_live_ready",
            "native_arrival_timeline_ready",
            "actual_contact_scope_ready",
            "combat_v3_prewar_scope_ready",
            "war_entry_forecast_inputs_ready",
            "capability_advertised",
        ):
            self.assertFalse(readiness[blocked_key], blocked_key)


if __name__ == "__main__":
    unittest.main()
