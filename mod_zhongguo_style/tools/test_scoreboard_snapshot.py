#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for immutable scoreboard and review-regression projections."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

from gen_scoreboard_snapshot import (
    BASE_FIELDS,
    B1_DISCLOSURE_A_OBJECT_FIELDS,
    B1_DISCLOSURE_B_OBJECT_FIELDS,
    B1_DISCLOSURE_C_LEGACY_OBJECT_FIELDS,
    B1_MANAGER_OBJECT_FIELDS,
    B1_OBJECT_CONTRACTS,
    B1_OBJECT_FIELDS,
    B1_SELF_OBJECT_FIELDS_BY_ROUTE,
    B1_TEAM_PUBLIC_FIELDS,
    B1ObjectFieldSpec,
    CASE_FIELDS,
    DETAIL_CASE_FIELDS,
    DETAIL_CLEAR_ACTION,
    DETAIL_CLEAR_GUI,
    DETAIL_PAGES,
    DETAIL_CONTENT_WIDTH,
    DETAIL_REDUNDANT_BINDING_FIELD_NAMES,
    DISCLOSURE_A_CASE_FIELDS,
    DISCLOSURE_A_FIELD_NAMES,
    DISCLOSURE_ACL_MODE,
    DISCLOSURE_B_CASE_FIELDS,
    DISCLOSURE_B_FIELD_NAMES,
    DISCLOSURE_POLICY_VARS,
    MUTABLE_DISCLOSURE_A_CASE_FIELDS,
    MUTABLE_DISCLOSURE_B_CASE_FIELDS,
    MUTABLE_RECEIVED_CASE_FIELDS,
    RECEIVED_CASE_FIELDS,
    RECEIVED_BINDING_FIELD_NAMES,
    SENSITIVE_RECEIVED_FIELDS,
    SENSITIVE_RECEIVED_SOURCE_VARS,
    FieldSpec,
    GEOMETRY_RESOLUTIONS,
    GEOMETRY_UI_SCALES,
    LEDGER_CONTENT_WIDTH,
    MOD_ROOT,
    PANEL_HORIZONTAL_FRAME_MARGIN,
    PANEL_MIN_PHYSICAL_MARGIN,
    PANEL_VIEWPORT_PERCENT,
    SLOT_COUNT,
    SURFACE_FIXED_CHROME_BUDGETS,
    SURFACE_MIN_SCROLL_VIEWPORTS,
    TABLE_CONTENT_WIDTH,
    TOGGLE_POSITION,
    TOGGLE_SIZE,
    disclosure_case_is_current,
    disclosure_policy_is_current,
    b1_disclosed_object_fields,
    disclosed_case_fields,
    outputs,
    received_case_fields,
    row_gui,
)


class ScoreboardSnapshotTests(unittest.TestCase):
    def test_case_detail_schema_uses_only_existing_frozen_product_fields(self) -> None:
        product_effects = "\n".join(
            (
                MOD_ROOT / "common" / "scripted_effects" / filename
            ).read_text(encoding="utf-8-sig")
            for filename in ("zg361_effects.txt", "zg361_b1_runtime_effects.txt")
        )
        self.assertTrue(all(isinstance(field, FieldSpec) for field in BASE_FIELDS))
        self.assertTrue(all(isinstance(field, FieldSpec) for field in CASE_FIELDS))
        self.assertTrue(
            all(isinstance(field, B1ObjectFieldSpec) for field in B1_OBJECT_FIELDS)
        )
        self.assertEqual(
            {field.page for field in CASE_FIELDS},
            {"facts", "peer", "quota", "audit"},
        )
        self.assertEqual(DETAIL_PAGES, ("facts", "peer", "quota", "audit"))
        for field in CASE_FIELDS:
            self.assertIn(
                f"name = {field.source_var}",
                product_effects,
                f"detail field {field.name} is not backed by a written product variable",
            )
        for field in B1_OBJECT_FIELDS:
            self.assertIn(
                f"name = {field.source_var}",
                product_effects,
                f"B1 detail field {field.name} is not backed by a written product variable",
            )
        self.assertTrue(
            SENSITIVE_RECEIVED_FIELDS.isdisjoint(
                {field.name for field in RECEIVED_CASE_FIELDS}
            )
        )
        self.assertTrue(
            SENSITIVE_RECEIVED_SOURCE_VARS.isdisjoint(
                {field.source_var for field in RECEIVED_CASE_FIELDS}
            )
        )

    def test_gray_leaver_fields_and_frozen_title_reach_managed_slots(self) -> None:
        gray_fields = {
            "roster_employment_state": "zg361_b1_roster_employment_state",
            "leaver_route": "zg361_b1_leaver_route",
            "leaver_honest_grade": "zg361_b1_leaver_honest_grade",
            "leaver_final_grade": "zg361_b1_leaver_final_grade",
            "leaver_quota_source": "zg361_b1_leaver_quota_source",
            "leaver_effective_year": "zg361_b1_leaver_effective_year",
            "leaver_receipt_state": "zg361_b1_leaver_receipt_state",
        }
        case_by_name = {field.name: field for field in CASE_FIELDS}
        for name, source in gray_fields.items():
            with self.subTest(field=name):
                self.assertIn(name, case_by_name)
                self.assertEqual(case_by_name[name].source_var, source)
                self.assertEqual(case_by_name[name].page, "audit")

        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        first_slot = effects.split(
            "zg361_write_managed_scoreboard_slot_effect = {", 1
        )[1].split("\n\t\telse_if = {", 1)[0]
        self.assertIn("has_variable = zg361_b1_roster_frozen_title", first_slot)
        self.assertIn(
            "value = scope:zg361_scoreboard_snapshot_entry.var:zg361_b1_roster_frozen_title",
            first_slot,
        )
        self.assertIn(
            "value = scope:zg361_scoreboard_snapshot_entry.primary_title",
            first_slot,
        )
        for name in gray_fields:
            self.assertIn(f"name = zg361_sb_m_01_{name}", first_slot)
            self.assertIn(
                f'text = "zg361_scoreboard_detail_field_{name}"', gui
            )

        # The data schema may grow, but #040 must not introduce another HUD
        # button/window/widget identity or compete with native action wiring.
        self.assertEqual(gui.count('name = "zg361_scoreboard_toggle"'), 1)
        self.assertEqual(gui.count('name = "zg361_scoreboard_window"'), 1)

        required_by_page = {
            "facts": {
                "self_choice",
                "self_score",
                "self_gap",
                "shadow_response",
                "shadow_delta",
            },
            "peer": {
                "peer_n",
                "peer_mean",
                "peer_variance",
                "peer_normalized_score",
                "peer_shape",
                "peer_reciprocity_risk",
                "peer_timely_n",
                "peer_credit_total",
                "evaluator_credit",
            },
            "quota": {
                "calibration_score",
                "calibration_score_before_shadow",
                "shadow_to_quota_delta",
                "quota_snapshot",
                "forced_down",
            },
            "audit": {
                "case_owner",
                "cycle_serial",
                "case_serial",
                "b1_case_owner",
                "b1_cycle_serial",
                "b1_case_serial",
                "b1_fact_sheet_serial",
                "b1_peer_sealed",
                "b1_self_receipt_serial",
                "b1_peer_receipt_serial",
                "b1_shadow_receipt_serial",
                "b1_band_receipt_serial",
            },
        }
        for page, required in required_by_page.items():
            actual = {field.name for field in CASE_FIELDS if field.page == page}
            self.assertTrue(required <= actual, f"{page} is missing {required - actual}")

    def test_selected_detail_schema_has_no_remove_only_case_binding_duplicates(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        slot_guis = rendered[
            MOD_ROOT
            / "common"
            / "scripted_guis"
            / "zg361_generated_scoreboard_slots.txt"
        ].decode("utf-8-sig")
        expected = {
            "case_owner",
            "cycle_serial",
            "case_serial",
            "b1_case_owner",
            "b1_cycle_serial",
            "b1_case_serial",
            "b1_case_state",
        }
        self.assertEqual(DETAIL_REDUNDANT_BINDING_FIELD_NAMES, expected)
        self.assertEqual(
            {field.name for field in CASE_FIELDS}
            - {field.name for field in DETAIL_CASE_FIELDS},
            expected,
        )
        for field in expected:
            dead_detail_var = f"zg361_sb_detail_{field}"
            self.assertNotIn(dead_detail_var, effects)
            self.assertNotIn(dead_detail_var, slot_guis)
            # The real source records retain their independently frozen tuples.
            self.assertIn(f"zg361_sb_m_01_{field}", effects)
            self.assertIn(f"zg361_sb_self_{field}", effects)
        for binding in ("owner", "cycle_serial", "case_serial"):
            canonical = f"zg361_sb_detail_binding_{binding}"
            self.assertIn(f"remove_variable = {canonical}", effects)
            self.assertIn(f"set_variable = {{ name = {canonical}", slot_guis)
        # Unlike the seven remove-only duplicates, result case_state has a real
        # mutable producer and remains part of the selected-detail schema.
        self.assertIn(
            "set_variable = { name = zg361_sb_detail_case_state",
            effects,
        )

    def test_single_case_detail_projection_and_selector_cardinality(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        slot_guis = rendered[
            MOD_ROOT
            / "common"
            / "scripted_guis"
            / "zg361_generated_scoreboard_slots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )

        self.assertEqual(
            len(re.findall(r"zg361_sb_m_\d{2}_select_gui\s*=\s*\{", slot_guis)),
            SLOT_COUNT,
        )
        self.assertEqual(slot_guis.count("zg361_sb_self_select_gui = {"), 1)
        self.assertEqual(gui.count('name = "zg361_scoreboard_window"'), 1)
        self.assertEqual(gui.count('name = "zg361_scoreboard_toggle"'), 1)
        for action_probe_target in (
            "zg361_scoreboard_entry_managed",
            "zg361_scoreboard_entry_received",
            "zg361_scoreboard_entry_system",
            "zg361_scoreboard_tab_managed",
            "zg361_scoreboard_tab_received",
            "zg361_scoreboard_tab_system",
            "zg361_scoreboard_page_managed",
            "zg361_scoreboard_page_received",
            "zg361_scoreboard_page_system",
            "zg361_scoreboard_modal_backdrop_close",
            "zg361_scoreboard_header_close",
        ):
            self.assertEqual(
                gui.count(f'name = "{action_probe_target}"'),
                1,
                action_probe_target,
            )
        self.assertEqual(gui.count('name = "zg361_scoreboard_detail_panel"'), 1)
        for page in DETAIL_PAGES:
            self.assertEqual(
                gui.count(f'name = "zg361_scoreboard_detail_page_{page}"'), 1
            )
            self.assertEqual(
                gui.count(f'name = "zg361_scoreboard_detail_tab_{page}"'), 1
            )

        received_names = {field.name for field in RECEIVED_CASE_FIELDS}
        for field in CASE_FIELDS:
            self.assertIn(f"zg361_sb_m_01_{field.name}", effects)
            if field.name in received_names:
                self.assertIn(f"zg361_sb_self_{field.name}", effects)
            else:
                self.assertNotIn(f"name = zg361_sb_self_{field.name}", effects)
            self.assertNotIn(f"zg361_sb_r_01_{field.name}", effects)
            if field.visible:
                self.assertIn(f"zg361_sb_detail_{field.name}", slot_guis)
            else:
                self.assertNotIn(f"zg361_sb_detail_{field.name}", slot_guis)
        for field in B1_OBJECT_FIELDS:
            self.assertIn(f"zg361_sb_m_01_{field.name}", effects)
            self.assertIn(f"zg361_sb_self_{field.name}", effects)
            self.assertNotIn(f"zg361_sb_r_01_{field.name}", effects)
            self.assertIn(f"zg361_sb_detail_{field.name}", slot_guis)
        for sensitive in SENSITIVE_RECEIVED_FIELDS:
            self.assertNotRegex(
                effects + slot_guis + gui,
                re.compile(rf"zg361_sb_r_\d{{2}}_{re.escape(sensitive)}"),
            )
        self.assertNotIn("Character.MakeScope.Var('zg361_b1_", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_result_", gui)
        self.assertIn("zg361_scoreboard_detail_unavailable", gui)

    def test_dossier_selectors_require_complete_frozen_case_identity(self) -> None:
        rendered = outputs()
        slot_guis = rendered[
            MOD_ROOT
            / "common"
            / "scripted_guis"
            / "zg361_generated_scoreboard_slots.txt"
        ].decode("utf-8-sig")

        managed = slot_guis.split("zg361_sb_m_01_select_gui = {", 1)[1].split(
            "\n}\n", 1
        )[0]
        for field in ("char", "rank", "case_owner", "cycle_serial", "case_serial"):
            self.assertIn(f"has_variable = zg361_sb_m_01_{field}", managed)
        for token in (
            "has_variable = zg361_scoreboard_managed_owner",
            "has_variable = zg361_scoreboard_managed_cycle_serial",
            "var:zg361_sb_m_01_case_owner = var:zg361_scoreboard_managed_owner",
            "var:zg361_sb_m_01_cycle_serial = var:zg361_scoreboard_managed_cycle_serial",
        ):
            self.assertIn(token, managed)

        self_selector = slot_guis.split("zg361_sb_self_select_gui = {", 1)[1].split(
            "\n}\n", 1
        )[0]
        for field in ("char", "case_owner", "cycle_serial", "case_serial"):
            self.assertIn(f"has_variable = zg361_sb_self_{field}", self_selector)
        for field in ("owner", "cycle_serial", "case_serial"):
            self.assertIn(
                f"has_variable = zg361_scoreboard_received_{field}", self_selector
            )
        for field in ("case_owner", "cycle_serial", "case_serial"):
            header = "owner" if field == "case_owner" else field
            self.assertIn(
                f"var:zg361_sb_self_{field} = "
                f"var:zg361_scoreboard_received_{header}",
                self_selector,
            )
        self.assertNotIn("var:zg361_sb_self_char = root", self_selector)

    def test_received_self_buffer_rejects_different_owner_cycle_or_case(self) -> None:
        effects = outputs()[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        copy_self = effects.split(
            "zg361_copy_received_scoreboard_slots_effect = {", 1
        )[1].split(
            "\n\tif = {\n\t\tlimit = { scope:zg361_scoreboard_source = { "
            "has_variable = zg361_sb_m_01_char",
            1,
        )[0]
        owner_guard = "var:zg361_result_case_owner = scope:zg361_scoreboard_source"
        cycle_guard = (
            "var:zg361_scoreboard_managed_cycle_serial = "
            "root.var:zg361_result_cycle_serial"
        )
        case_guard = (
            "name = zg361_scoreboard_received_case_serial "
            "value = var:zg361_result_case_serial"
        )
        self_write = "name = zg361_sb_self_char"

        self.assertIn(owner_guard, copy_self)
        self.assertIn(cycle_guard, copy_self)
        self.assertIn(case_guard, copy_self)
        self.assertIn(self_write, copy_self)
        self.assertLess(copy_self.index(owner_guard), copy_self.index(cycle_guard))
        self.assertLess(copy_self.index(cycle_guard), copy_self.index(case_guard))
        self.assertLess(copy_self.index(case_guard), copy_self.index(self_write))
        # Mutation-style negative cases: removing any identity token
        # makes the static availability proof fail, rather than silently opening
        # a dossier for another reviewer, publication cycle or case.
        for missing_guard in (owner_guard, cycle_guard, case_guard):
            mutated = copy_self.replace(missing_guard, "always = yes", 1)
            self.assertFalse(
                owner_guard in mutated
                and cycle_guard in mutated
                and case_guard in mutated
                and mutated.index(owner_guard) < mutated.index(cycle_guard)
                and mutated.index(cycle_guard) < mutated.index(case_guard)
                and mutated.index(case_guard) < mutated.index(self_write)
            )

    def test_received_acl_excludes_peer_identities_and_unstructured_text(self) -> None:
        effects = outputs()[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        copy_self = effects.split(
            "zg361_copy_received_scoreboard_slots_effect = {", 1
        )[1].split("\n\tif = {\n\t\tlimit = { scope:zg361_scoreboard_source", 1)[0]
        for field in RECEIVED_CASE_FIELDS:
            self.assertIn(f"name = zg361_sb_self_{field.name}", copy_self)
        for sensitive in SENSITIVE_RECEIVED_FIELDS:
            self.assertNotIn(f"zg361_sb_self_{sensitive}", copy_self)
        for source_var in SENSITIVE_RECEIVED_SOURCE_VARS:
            self.assertNotIn(source_var, copy_self)
        injected = CASE_FIELDS + (
            FieldSpec(
                "peer_slot_1_evaluator",
                "zg361_b1_peer_slot_1_evaluator",
                "peer",
                "character",
            ),
            FieldSpec("raw_comment", "zg361_b1_raw_comment", "peer"),
            FieldSpec("recusal_identity", "zg361_b1_recusal_identity", "peer"),
        )
        filtered = received_case_fields(injected)
        self.assertEqual(filtered, RECEIVED_CASE_FIELDS)

    def test_disclosure_a_b_c_field_contract_and_legacy_fallback(self) -> None:
        expected_a = {
            "kpi_frozen",
            "values_frozen",
            "evidence_governance",
            "evidence_capability",
            "evidence_growth",
            "evidence_superior",
            "evidence_values",
            "evidence_collaboration",
            "evidence_jingcha",
            "evidence_organization",
            "final_grade",
            "grade_reason",
            "appeal_open",
            "appeal_outcome",
        }
        self.assertEqual(DISCLOSURE_A_FIELD_NAMES, expected_a)
        self.assertEqual(
            {field.name for field in DISCLOSURE_A_CASE_FIELDS}, expected_a
        )
        self.assertEqual(DISCLOSURE_B_FIELD_NAMES, {"final_grade"})
        self.assertEqual(
            {field.name for field in DISCLOSURE_B_CASE_FIELDS}, {"final_grade"}
        )
        self.assertEqual(
            disclosed_case_fields(policy_available=1, self_mode=3),
            DISCLOSURE_A_CASE_FIELDS,
        )
        self.assertEqual(
            disclosed_case_fields(policy_available=1, self_mode=1),
            DISCLOSURE_B_CASE_FIELDS,
        )
        # Explicit C and a pre-#013 save both preserve the former received ACL.
        self.assertEqual(
            disclosed_case_fields(policy_available=0, self_mode=0),
            RECEIVED_CASE_FIELDS,
        )
        self.assertEqual(
            disclosed_case_fields(policy_available=None, self_mode=None),
            RECEIVED_CASE_FIELDS,
        )
        # A configured but unknown/partial mode cannot widen into legacy C.
        self.assertEqual(
            disclosed_case_fields(policy_available=1, self_mode=0), ()
        )
        internal_quota_trade = {
            "cohort_n",
            "absolute_grade",
            "calibration_score",
            "calibration_score_before_shadow",
            "shadow_to_quota_delta",
            "quota_snapshot",
            "forced_down",
        }
        for fields in (DISCLOSURE_A_CASE_FIELDS, DISCLOSURE_B_CASE_FIELDS):
            names = {field.name for field in fields}
            self.assertTrue(names.isdisjoint(internal_quota_trade))
            self.assertTrue(names.isdisjoint(SENSITIVE_RECEIVED_FIELDS))

    def test_b1_object_schema_is_independent_and_acl_intersection_is_default_deny(self) -> None:
        b1_names = {field.name for field in B1_OBJECT_FIELDS}
        self.assertTrue(b1_names.isdisjoint({field.name for field in CASE_FIELDS}))
        self.assertTrue(
            b1_names.isdisjoint({field.name for field in RECEIVED_CASE_FIELDS})
        )
        self.assertEqual(B1_MANAGER_OBJECT_FIELDS, B1_OBJECT_FIELDS)
        self.assertEqual(B1_DISCLOSURE_A_OBJECT_FIELDS, B1_OBJECT_FIELDS)
        self.assertEqual(B1_DISCLOSURE_B_OBJECT_FIELDS, ())
        self.assertEqual(B1_DISCLOSURE_C_LEGACY_OBJECT_FIELDS, ())
        self.assertEqual(B1_TEAM_PUBLIC_FIELDS, ())
        for mechanism_id, route in B1_SELF_OBJECT_FIELDS_BY_ROUTE:
            expected = B1_SELF_OBJECT_FIELDS_BY_ROUTE[(mechanism_id, route)]
            self.assertEqual(
                b1_disclosed_object_fields(
                    mechanism_id=mechanism_id,
                    route=route,
                    disclosure_acl_mode=3,
                ),
                expected,
            )
            for acl_mode in (0, 1, 2):
                self.assertEqual(
                    b1_disclosed_object_fields(
                        mechanism_id=mechanism_id,
                        route=route,
                        disclosure_acl_mode=acl_mode,
                    ),
                    (),
                )
        forbidden_identity_or_money = re.compile(
            r"(?:evaluator|reviewer|dissenter|attendee|raw|recusal|swap|"
            r"gold|treasury|salary|bonus|reward)",
            re.I,
        )
        forbidden_binding_suffix = re.compile(r"_(?:owner|subject|case|state)$")
        for field in B1_OBJECT_FIELDS:
            self.assertIsNone(forbidden_identity_or_money.search(field.name))
            self.assertIsNone(forbidden_identity_or_money.search(field.source_var))
            self.assertIsNone(forbidden_binding_suffix.search(field.name))
            self.assertIsNone(forbidden_binding_suffix.search(field.source_var))
        final_grade = next(field for field in CASE_FIELDS if field.name == "final_grade")
        self.assertEqual(final_grade.source_var, "zg361_result_grade")
        self.assertNotIn("final_grade", b1_names)

    def test_b1_objects_use_strict_five_tuple_gates_and_no_received_team_slots(self) -> None:
        effects = outputs()[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        for contract in B1_OBJECT_CONTRACTS:
            marker = f"# B1_OBJECT_{contract.mechanism_id}_{contract.route}_BEGIN"
            self.assertIn(marker, effects)
            section = effects.split(marker, 1)[1].split(
                f"# B1_OBJECT_{contract.mechanism_id}_{contract.route}_END", 1
            )[0]
            for binding in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"{contract.prefix}_{binding}", section)
            self.assertIn("var:zg361_b1_case_owner", section)
            self.assertIn("var:zg361_b1_case_subject = this", section)
            self.assertIn("var:zg361_b1_cycle_serial", section)
            self.assertIn("var:zg361_b1_case_serial", section)
            self.assertIn("var:zg361_b1_case_state", section)
        self.assertIn(
            "var:zg361_b1_band_order_object_case = "
            "var:zg361_b1_m145_receipt_serial",
            effects,
        )
        for field in B1_OBJECT_FIELDS:
            self.assertNotRegex(
                effects,
                re.compile(rf"zg361_sb_r_\d{{2}}_{re.escape(field.name)}"),
            )

    def test_b1_post_mark_patch_is_one_shot_and_preserves_publish_before_elimination(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        patch = effects.split("zg361_patch_scoreboard_b1_post_mark_effect = {", 1)[1]
        for token in (
            "var:zg361_b1_cycle_state = 8",
            "NOT = { has_character_flag = zg361_b1_cycle_active }",
            "zg361_scoreboard_b1_post_mark_patch_serial",
            "variable = zg361_b1_subjects",
            "var:zg361_b1_case_state = 8",
            "var:zg361_result_case_owner",
            "var:zg361_result_cycle_serial",
            "var:zg361_result_case_serial",
            "var:zg361_sb_self_disclosure_acl_mode = 3",
        ):
            self.assertIn(token, patch)
        self.assertIn("zg361_sb_m_01_b1_141_review_outcome", patch)
        for mechanism_id in (142, 143, 144, 145):
            self.assertNotIn(f"zg361_sb_m_01_b1_{mechanism_id}_", patch)
        core = (
            MOD_ROOT / "common" / "scripted_effects" / "zg361_effects.txt"
        ).read_text(encoding="utf-8-sig")
        settlement = core.split("zg361_apply_pending_grades_effect = {", 1)[1].split(
            "\n}\n\n", 1
        )[0]
        ordered = (
            "zg361_publish_scoreboard_effect = yes",
            "zg361_process_elimination_effect = yes",
            "zg361_b1_mark_published_effect = yes",
            "zg361_patch_scoreboard_b1_post_mark_effect = yes",
            "remove_character_flag = zg361_review_in_progress",
        )
        self.assertTrue(all(token in settlement for token in ordered))
        self.assertEqual(
            [settlement.index(token) for token in ordered],
            sorted(settlement.index(token) for token in ordered),
        )

    def test_generated_received_copy_freezes_policy_and_applies_a_b_c(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        copy_self = effects.split(
            "zg361_copy_received_scoreboard_slots_effect = {", 1
        )[1].split("\n\tif = {\n\t\tlimit = { scope:zg361_scoreboard_source", 1)[0]
        policy_freeze = effects.split(
            "zg361_freeze_received_disclosure_policy_effect = {", 1
        )[1].split("\n}\n\n# Current scope = player official", 1)[0]

        for name, source_var in DISCLOSURE_POLICY_VARS:
            self.assertIn(f"has_variable = {source_var}", policy_freeze)
            self.assertIn(
                f"name = zg361_sb_self_{name} value = var:{source_var}",
                policy_freeze,
            )
            self.assertIn(
                f"name = zg361_sb_self_{name} value = 0", policy_freeze
            )
        self.assertIn(
            "var:zg361_b1_disclosure_policy_id = var:zg361_b1_case_serial",
            policy_freeze,
        )
        self.assertIn(
            f"name = zg361_sb_self_{DISCLOSURE_ACL_MODE} value = 0",
            policy_freeze,
        )
        self.assertIn(
            "zg361_freeze_received_disclosure_policy_effect = yes", copy_self
        )
        # The generic copy surface remains free of identity-bearing ABI tokens;
        # the dedicated helper is invoked only behind the tuple gate.
        self.assertNotIn("evaluator_id", copy_self)

        def marked(begin: str, end: str) -> str:
            return copy_self.split(begin, 1)[1].split(end, 1)[0]

        a = marked("# DISCLOSURE_A_BEGIN", "# DISCLOSURE_A_END")
        b = marked("# DISCLOSURE_B_BEGIN", "# DISCLOSURE_B_END")
        c = marked(
            "# DISCLOSURE_C_LEGACY_BEGIN", "# DISCLOSURE_C_LEGACY_END"
        )

        def destinations(body: str) -> set[str]:
            return set(re.findall(r"name = zg361_sb_self_([a-z0-9_]+)", body))

        self.assertEqual(
            destinations(a),
            DISCLOSURE_A_FIELD_NAMES
            | {field.name for field in B1_DISCLOSURE_A_OBJECT_FIELDS},
        )
        self.assertEqual(destinations(b), DISCLOSURE_B_FIELD_NAMES)
        self.assertEqual(
            destinations(c),
            {field.name for field in RECEIVED_CASE_FIELDS}
            - RECEIVED_BINDING_FIELD_NAMES,
        )
        for sensitive in SENSITIVE_RECEIVED_SOURCE_VARS:
            self.assertNotIn(sensitive, a + b)
        for internal in (
            "zg361_b1_calibration_score",
            "zg361_b1_shadow_to_quota_delta",
            "zg361_b1_quota_snapshot",
            "zg361_b1_forced_down",
        ):
            self.assertNotIn(internal, a + b)
        # The manager projection remains separate from the frozen #013 policy.
        self.assertNotIn("zg361_sb_m_01_disclosure_", effects)

    def test_mutable_updates_cannot_widen_the_frozen_disclosure_route(self) -> None:
        effects = outputs()[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        phase2 = effects.split(
            "# Current scope = player official after witnessed/acknowledged 3.25 settlement.",
            1,
        )[1]
        expected = {
            "A": {field.name for field in MUTABLE_DISCLOSURE_A_CASE_FIELDS},
            "B": {field.name for field in MUTABLE_DISCLOSURE_B_CASE_FIELDS},
            "C_LEGACY": {field.name for field in MUTABLE_RECEIVED_CASE_FIELDS},
        }
        for label, field_names in expected.items():
            sections = re.findall(
                rf"# DISCLOSURE_{label}_MUTABLE_BEGIN(?P<body>.*?)"
                rf"# DISCLOSURE_{label}_MUTABLE_END",
                phase2,
                re.S,
            )
            # self buffer + selected detail, for settlement + regrade.
            self.assertEqual(len(sections), 4, label)
            for body in sections:
                destinations = set(
                    re.findall(
                        r"name = zg361_sb_(?:self|detail)_([a-z0-9_]+)", body
                    )
                )
                self.assertEqual(destinations, field_names, label)
        self.assertNotIn(
            "var:zg361_sb_self_b1_case_serial = var:zg361_sb_self_case_serial",
            phase2,
        )
        self.assertEqual(expected["B"], {"final_grade"})
        self.assertEqual(
            expected["A"],
            {"final_grade", "appeal_open", "appeal_outcome"},
        )

    def test_received_selector_hides_absent_b_fields_instead_of_placeholder_rows(self) -> None:
        rendered = outputs()
        slot_guis = rendered[
            MOD_ROOT
            / "common"
            / "scripted_guis"
            / "zg361_generated_scoreboard_slots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        selector = slot_guis.split("zg361_sb_self_select_gui = {", 1)[1].split(
            "\n}\n", 1
        )[0]

        def marked(begin: str, end: str) -> str:
            return selector.split(begin, 1)[1].split(end, 1)[0]

        a = marked("# DISCLOSURE_A_SELECT_BEGIN", "# DISCLOSURE_A_SELECT_END")
        b = marked("# DISCLOSURE_B_SELECT_BEGIN", "# DISCLOSURE_B_SELECT_END")
        c = marked(
            "# DISCLOSURE_C_LEGACY_SELECT_BEGIN",
            "# DISCLOSURE_C_LEGACY_SELECT_END",
        )
        self.assertEqual(
            set(re.findall(r"name = zg361_sb_detail_([a-z0-9_]+)", a)),
            DISCLOSURE_A_FIELD_NAMES
            | {field.name for field in B1_DISCLOSURE_A_OBJECT_FIELDS},
        )
        self.assertEqual(
            set(re.findall(r"name = zg361_sb_detail_([a-z0-9_]+)", b)),
            DISCLOSURE_B_FIELD_NAMES,
        )
        self.assertEqual(
            set(re.findall(r"name = zg361_sb_detail_([a-z0-9_]+)", c)),
            {field.name for field in RECEIVED_CASE_FIELDS if field.visible},
        )
        self.assertIn("zg361_sb_detail_binding_owner", selector)
        self.assertIn("zg361_sb_detail_binding_cycle_serial", selector)
        self.assertIn("zg361_sb_detail_binding_case_serial", selector)

        # Managed details retain missing-value placeholders; received details
        # remove any row whose field was not copied by the frozen ACL.
        for field in (
            "grade_reason",
            "quota_snapshot",
            "b1_141_review_outcome",
        ):
            gate = (
                "[Or(GetScriptedGui('zg361_scoreboard_detail_managed_gui')."
                "IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), "
                f"GetScriptedGui('zg361_sb_detail_{field}_available_gui')."
                "IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]"
            )
            self.assertIn(f'hbox = {{ visible = "{gate}"', gui)
            self.assertIn(f'text = "zg361_scoreboard_detail_field_{field}"', gui)
        for binding in (
            "case_owner",
            "cycle_serial",
            "case_serial",
            "case_state",
            "b1_case_owner",
            "b1_cycle_serial",
            "b1_case_serial",
            "b1_case_state",
        ):
            self.assertNotIn(
                f'text = "zg361_scoreboard_detail_field_{binding}"', gui
            )
            self.assertNotIn(f"zg361_sb_detail_{binding}_available_gui", slot_guis)

    def test_received_binding_accepts_independent_cases_and_rejects_stale_owner_cycle_policy(self) -> None:
        current = dict(
            result_owner="manager-a",
            result_cycle=8,
            result_case=903,
            b1_owner="manager-a",
            b1_cycle=8,
            b1_case=41,
            published_owner="manager-a",
            published_cycle=8,
        )
        self.assertTrue(disclosure_case_is_current(**current))
        for field, stale in (
            ("result_owner", "manager-b"),
            ("result_cycle", 7),
            ("b1_owner", "manager-b"),
            ("b1_cycle", 7),
            ("published_owner", "manager-b"),
            ("published_cycle", 7),
        ):
            mutated = dict(current)
            mutated[field] = stale
            self.assertFalse(disclosure_case_is_current(**mutated), field)
        # Independent cursors: neither case number is compared to the other.
        for field, another_valid_case in (
            ("result_case", 1903),
            ("b1_case", 141),
        ):
            mutated = dict(current)
            mutated[field] = another_valid_case
            self.assertTrue(disclosure_case_is_current(**mutated), field)
        for mode in (3, 1):
            self.assertTrue(
                disclosure_policy_is_current(
                    policy_available=1,
                    policy_id=41,
                    self_mode=mode,
                    b1_case=41,
                )
            )
        for stale_policy_id in (40, 903):
            self.assertFalse(
                disclosure_policy_is_current(
                    policy_available=1,
                    policy_id=stale_policy_id,
                    self_mode=3,
                    b1_case=41,
                )
            )

        effects = outputs()[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        copy_self = effects.split(
            "zg361_copy_received_scoreboard_slots_effect = {", 1
        )[1].split("\n\tif = {\n\t\tlimit = { scope:zg361_scoreboard_source", 1)[0]
        tuple_gate = copy_self.split("# Freeze the complete #013 ABI", 1)[0]
        for guard in (
            "var:zg361_result_case_owner = scope:zg361_scoreboard_source",
            "var:zg361_scoreboard_managed_cycle_serial = root.var:zg361_result_cycle_serial",
            "var:zg361_b1_case_owner = var:zg361_result_case_owner",
            "var:zg361_b1_cycle_serial = var:zg361_result_cycle_serial",
        ):
            self.assertIn(guard, tuple_gate)
        self.assertNotIn(
            "var:zg361_b1_case_serial = var:zg361_result_case_serial",
            copy_self,
        )
        self.assertIn(
            "name = zg361_sb_self_case_serial value = var:zg361_result_case_serial",
            copy_self,
        )
        self.assertIn(
            "name = zg361_sb_self_b1_case_serial value = var:zg361_b1_case_serial",
            copy_self,
        )
        self.assertNotIn(
            "var:zg361_sb_self_b1_case_serial = var:zg361_sb_self_case_serial",
            outputs()[
                MOD_ROOT
                / "common"
                / "scripted_guis"
                / "zg361_generated_scoreboard_slots.txt"
            ].decode("utf-8-sig"),
        )
        freeze_call = copy_self.index(
            "zg361_freeze_received_disclosure_policy_effect = yes"
        )
        first_visible_write = copy_self.index("name = zg361_sb_self_char")
        self.assertLess(
            copy_self.index("var:zg361_b1_cycle_serial = var:zg361_result_cycle_serial"),
            freeze_call,
        )
        self.assertLess(freeze_call, first_visible_write)
        policy_binding = effects.index(
            "var:zg361_b1_disclosure_policy_id = var:zg361_b1_case_serial"
        )
        helper_definition = effects.index(
            "zg361_freeze_received_disclosure_policy_effect = {"
        )
        self.assertLess(helper_definition, policy_binding)

    def test_scoreboard_outputs_are_reproducible_utf8_bom(self) -> None:
        first = outputs()
        second = outputs()
        self.assertEqual(first, second)
        for path, data in first.items():
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"), path.name)

    def test_detail_selection_is_cleared_by_publication_and_navigation(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        slot_guis = rendered[
            MOD_ROOT
            / "common"
            / "scripted_guis"
            / "zg361_generated_scoreboard_slots.txt"
        ].decode("utf-8-sig")
        for prefix in ("m", "r"):
            clear = effects.split(
                f"zg361_clear_scoreboard_{prefix}_slots_effect = {{", 1
            )[1].split("}\n", 1)[0]
            self.assertIn("zg361_clear_scoreboard_detail_effect = yes", clear)
        self.assertIn('name = "zg361_scoreboard_detail_back"', gui)
        self.assertGreaterEqual(
            gui.count("GetVariableSystem.Set('zg361_scoreboard_view', 'list')"),
            9,
        )
        self.assertGreaterEqual(
            gui.count(
                "GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')"
            ),
            9,
        )
        self.assertIn(
            "GetScriptedGui('zg361_scoreboard_detail_managed_gui').IsShown",
            gui,
        )
        self.assertIn(
            "GetScriptedGui('zg361_scoreboard_detail_received_gui').IsShown",
            gui,
        )
        self.assertEqual(slot_guis.count(f"{DETAIL_CLEAR_GUI} = {{"), 1)
        self.assertGreaterEqual(gui.count(DETAIL_CLEAR_ACTION), 6)
        toggle = gui.split('name = "zg361_scoreboard_toggle"', 1)[1].split(
            "\n\t}", 1
        )[0]
        self.assertEqual(toggle.count(DETAIL_CLEAR_ACTION), 3)
        for close_marker in (
            'name = "zg361_scoreboard_detail_back"',
            "shortcut = close_window",
        ):
            self.assertIn(close_marker, gui)

    def test_character_and_dossier_controls_are_siblings(self) -> None:
        for prefix in ("m", "r"):
            row = row_gui(prefix, 1)
            character_index = next(
                index
                for index, line in enumerate(row)
                if line.strip() == "button_tertiary = {"
            )
            detail_index = next(
                index
                for index, line in enumerate(row)
                if f'name = "zg361_scoreboard_detail_button_{prefix}_01"' in line
            )
            self.assertGreater(detail_index, character_index)
            self.assertTrue(row[character_index].startswith("\t"))
            self.assertTrue(row[detail_index].startswith("\t"))
            self.assertFalse(row[detail_index].startswith("\t\t"))
            self.assertNotIn(
                "button_standard = {",
                "\n".join(row[character_index:detail_index]),
            )
        self.assertIn("zg361_sb_m_01_select_gui", "\n".join(row_gui("m", 1)))
        received_row = "\n".join(row_gui("r", 1))
        self.assertIn("zg361_sb_self_select_gui", received_row)
        self.assertIn("Character.IsPlayer", received_row)

    def test_exact_slots_and_no_live_score_reads(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode("utf-8-sig")
        for prefix in ("m", "r"):
            for slot in range(1, SLOT_COUNT + 1):
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_char", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_kpi", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_grade", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_title", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_promotion", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_pip", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_char", gui)
        self.assertNotIn("GetList('zg361_scoreboard_managed')", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_kpi')", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_rank')", gui)
        self.assertNotIn("Character.GetPrimaryTitle", gui)
        self.assertNotIn("GetScriptedGui('zg361_scoreboard_promotion_gui')", gui)
        self.assertNotIn("GetScriptedGui('zg361_scoreboard_pip_gui')", gui)
        self.assertNotIn("zg361_scoreboard_former_official", gui)
        self.assertIn(".Var('zg361_sb_m_01_title').Title", gui)
        self.assertIn("zg361_scoreboard_managed_shown_n", gui)
        self.assertIn("zg361_scoreboard_received_shown_n", gui)
        self.assertEqual(
            effects.count(
                "limit = { has_variable = zg361_scoreboard_slot_cursor "
                "var:zg361_scoreboard_slot_cursor ="
            ),
            SLOT_COUNT,
        )

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in outputs().items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])

    def test_phase2_case_updates_follow_frozen_owner_cycle_and_case(self) -> None:
        effects = outputs()[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        phase2 = effects.split(
            "# Current scope = player official after witnessed/acknowledged 3.25 settlement.",
            1,
        )[1]
        for effect in (
            "zg361_update_settled_325_scoreboard_slots_effect",
            "zg361_update_regraded_scoreboard_slots_effect",
        ):
            self.assertIn(effect, phase2)
        self.assertIn("var:zg361_result_case_owner = {", phase2)
        self.assertIn("zg361_scoreboard_managed_cycle_serial", phase2)
        self.assertIn("zg361_scoreboard_received_cycle_serial", phase2)
        self.assertIn("zg361_scoreboard_received_case_serial", phase2)
        self.assertIn(
            "var:zg361_scoreboard_received_owner = var:zg361_result_case_owner",
            phase2,
        )
        for slot in (1, SLOT_COUNT):
            frozen_case = f"zg361_sb_m_{slot:02d}_case_serial"
            self.assertIn(f"has_variable = {frozen_case}", phase2)
            self.assertIn(
                f"var:{frozen_case} = "
                "scope:zg361_scoreboard_case_entry.var:zg361_result_case_serial",
                phase2,
            )
        self.assertIn(
            "var:zg361_sb_detail_binding_case_serial = "
            "scope:zg361_scoreboard_case_entry.var:zg361_result_case_serial",
            phase2,
        )
        self.assertNotIn("\tliege = {", phase2)
        self.assertNotIn("\tevery_vassal = {", phase2)
        self.assertEqual(
            phase2.count("scope:zg361_scoreboard_case_entry.var:zg361_streak_bottom"),
            SLOT_COUNT * 2,
        )

    def test_generated_clausewitz_outputs_are_brace_balanced(self) -> None:
        def balance(text: str) -> int:
            cleaned = []
            for line in text.splitlines():
                line = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
                cleaned.append(line.split("#", 1)[0])
            return "\n".join(cleaned).count("{") - "\n".join(cleaned).count("}")

        for path, data in outputs().items():
            if path.suffix not in {".txt", ".gui"}:
                continue
            text = data.decode("utf-8-sig")
            self.assertEqual(balance(text), 0, path.name)
            self.assertNotEqual(balance(text.rsplit("}", 1)[0]), 0, path.name)

    def test_eighty_row_cap_is_explicitly_reported_as_shown_over_full(self) -> None:
        product_effects = (
            MOD_ROOT / "common" / "scripted_effects" / "zg361_effects.txt"
        ).read_text(encoding="utf-8-sig")
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        self.assertRegex(
            product_effects,
            re.compile(
                r"name\s*=\s*zg361_scoreboard_managed_shown_n\s+"
                r"value\s*=\s*\{\s*value\s*=\s*var:zg361_cohort_n\s+"
                r"max\s*=\s*80\s*\}",
                re.S,
            ),
        )
        self.assertRegex(
            product_effects,
            re.compile(
                r"ordered_in_list\s*=\s*\{.*?"
                r"list\s*=\s*zg361_scoreboard_candidates.*?"
                r"max\s*=\s*\{\s*"
                r"value\s*=\s*list_size:zg361_scoreboard_candidates\s+"
                r"max\s*=\s*80\s*\}",
                re.S,
            ),
        )
        self.assertNotIn(
            "var:zg361_scoreboard_managed_shown_n > 80", product_effects
        )
        for source in ("managed", "received"):
            shown = f"zg361_scoreboard_{source}_shown_n"
            total = f"zg361_scoreboard_{source}_n"
            self.assertRegex(gui, re.compile(rf"Var\('{shown}'\).*? / .*?Var\('{total}'\)"))
            shown_available = f"zg361_scoreboard_{source}_shown_available_gui"
            self.assertIn(f"GetScriptedGui('{shown_available}').IsShown", gui)
            self.assertRegex(
                gui,
                re.compile(
                    rf"Not\(GetScriptedGui\('{shown_available}'\).*?"
                    rf"Var\('{total}'\)"
                ),
            )

    def test_toggle_is_hud_aligned_and_suppressed_by_native_overlays(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        width, height = TOGGLE_SIZE
        x, y = TOGGLE_POSITION
        self.assertIn(
            f'name = "zg361_scoreboard_toggle" size = {{ {width} {height} }} '
            f"parentanchor = top|right position = {{ {x} {y} }}",
            gui,
        )
        toggle = re.search(
            r'name = "zg361_scoreboard_toggle"(?P<body>.*?)\n\t\}', gui, re.S
        )
        self.assertIsNotNone(toggle)
        body = toggle.group("body") if toggle else ""
        for gate in (
            "Not(IsPauseMenuShown)",
            "IsDefaultGUIMode",
            "Not(IsGameViewOpen('struggle'))",
            "hide_ui_main_tabs",
            "Not(IsRightWindowOpen)",
            "Not(IsGameViewOpen('outliner'))",
            "Not(IsGameViewOpen('barbershop'))",
        ):
            self.assertIn(gate, body)
        self.assertIn("using = Animation_ShowHide_Quick", body)

        # CK3 lays this HUD out in a 1920x1080 reference space. The toggle's
        # right edge stays 60 units left of the screen, clearing the native
        # 50-unit main-tab rail; 1440p scales the same safe rectangle by 4/3.
        logical_width, logical_height = 1920, 1080
        left = logical_width + x - width
        right = logical_width + x
        top = y
        bottom = y + height
        self.assertEqual((left, right, top, bottom), (1680, 1860, 90, 134))
        self.assertGreaterEqual(logical_width - right, 50)
        self.assertGreaterEqual(left, 0)
        self.assertLessEqual(bottom, logical_height)
        scale_1440p = 2560 / logical_width
        self.assertEqual(
            tuple(round(value * scale_1440p) for value in (left, right, top, bottom)),
            (2240, 2480, 120, 179),
        )

    def test_responsive_panel_uses_bounded_two_axis_scroll_surfaces(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        self.assertIn(
            f'name = "zg361_scoreboard_panel" size = {{ '
            f"{PANEL_VIEWPORT_PERCENT}% {PANEL_VIEWPORT_PERCENT}% }} "
            "parentanchor = center widgetanchor = center",
            gui,
        )
        self.assertNotIn(
            'name = "zg361_scoreboard_panel" size = { 1220 820 }', gui
        )

        scroll_contracts = {
            "zg361_scoreboard_table_managed": TABLE_CONTENT_WIDTH,
            "zg361_scoreboard_table_received": TABLE_CONTENT_WIDTH,
            "zg361_scoreboard_ledger_scroll": LEDGER_CONTENT_WIDTH,
            **{
                f"zg361_scoreboard_detail_scroll_{page}": DETAIL_CONTENT_WIDTH
                for page in DETAIL_PAGES
            },
        }
        for name, content_width in scroll_contracts.items():
            marker = f'name = "{name}"'
            self.assertEqual(gui.count(marker), 1)
            body = gui.split(marker, 1)[1].split(
                'blockoverride "scrollbox_content" {', 1
            )[0]
            self.assertIn("layoutpolicy_horizontal = expanding", body)
            self.assertIn("layoutpolicy_vertical = expanding", body)
            self.assertIn("scrollbarpolicy_horizontal = as_needed", body)
            self.assertIn("scrollbarpolicy_vertical = as_needed", body)
            self.assertIn(
                "scrollbar_horizontal = { using = Scrollbar_Horizontal }", body
            )
            self.assertIn(
                "scrollbar_vertical = { using = Scrollbar_Vertical }", body
            )
            content = gui.split(marker, 1)[1].split(
                'blockoverride "scrollbox_content" {', 1
            )[1]
            self.assertIn("set_parent_size_to_minimum = yes", content)
            self.assertIn(f"minimumsize = {{ {content_width} 0 }}", content)

        self.assertEqual(gui.count("scrollbarpolicy_horizontal = as_needed"), 7)
        self.assertEqual(gui.count("scrollbarpolicy_vertical = as_needed"), 7)
        self.assertEqual(gui.count("using = Scrollbar_Horizontal"), 7)
        self.assertEqual(gui.count("using = Scrollbar_Vertical"), 7)

    def test_three_by_three_geometry_and_modal_blocking_contract(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        self.assertEqual(
            GEOMETRY_RESOLUTIONS,
            ((1366, 768), (1920, 1080), (2560, 1440)),
        )
        self.assertEqual(GEOMETRY_UI_SCALES, (1.0, 1.25, 1.5))
        self.assertEqual(
            SURFACE_FIXED_CHROME_BUDGETS,
            {"list": 200, "ledger": 236, "detail": 417},
        )
        self.assertEqual(
            SURFACE_MIN_SCROLL_VIEWPORTS,
            {"list": 250, "ledger": 210, "detail": 37},
        )
        self.assertIn(
            'name = "zg361_scoreboard_modal" size = { 100% 100% }', gui
        )
        self.assertIn(
            "alwaystransparent = no filter_mouse = all using = Background_Full_Dim",
            gui,
        )
        self.assertRegex(
            gui,
            re.compile(
                r"button_normal\s*=\s*\{\s*"
                r'name\s*=\s*"zg361_scoreboard_modal_backdrop_close"\s*'
                r"size\s*=\s*\{\s*100%\s+100%\s*\}"
            ),
        )
        self.assertRegex(
            gui,
            re.compile(
                r'name\s*=\s*"zg361_scoreboard_panel".*?'
                r"alwaystransparent\s*=\s*no\s+filter_mouse\s*=\s*all"
            ),
        )

        tested_cells = 0
        horizontal_overflow_cells = 0
        expected_horizontal_overflow = {
            (1366, 768, 1.25),
            (1366, 768, 1.5),
            (1920, 1080, 1.5),
        }
        panel_ratio = PANEL_VIEWPORT_PERCENT / 100
        toggle_width, toggle_height = TOGGLE_SIZE
        toggle_x, toggle_y = TOGGLE_POSITION
        for width, height in GEOMETRY_RESOLUTIONS:
            for ui_scale in GEOMETRY_UI_SCALES:
                with self.subTest(resolution=(width, height), ui_scale=ui_scale):
                    tested_cells += 1
                    logical_width = width / ui_scale
                    logical_height = height / ui_scale
                    panel_logical_width = logical_width * panel_ratio
                    panel_logical_height = logical_height * panel_ratio
                    panel_physical_width = panel_logical_width * ui_scale
                    panel_physical_height = panel_logical_height * ui_scale
                    panel_left = (width - panel_physical_width) / 2
                    panel_top = (height - panel_physical_height) / 2
                    panel_right = panel_left + panel_physical_width
                    panel_bottom = panel_top + panel_physical_height

                    self.assertGreaterEqual(panel_left, PANEL_MIN_PHYSICAL_MARGIN)
                    self.assertGreaterEqual(panel_top, PANEL_MIN_PHYSICAL_MARGIN)
                    self.assertLessEqual(panel_right, width)
                    self.assertLessEqual(panel_bottom, height)
                    for surface, fixed_chrome in (
                        SURFACE_FIXED_CHROME_BUDGETS.items()
                    ):
                        self.assertGreaterEqual(
                            panel_logical_height - fixed_chrome,
                            SURFACE_MIN_SCROLL_VIEWPORTS[surface],
                            surface,
                        )

                    content_viewport_width = (
                        panel_logical_width - PANEL_HORIZONTAL_FRAME_MARGIN
                    )
                    self.assertGreater(content_viewport_width, 0)
                    overflows_horizontally = (
                        TABLE_CONTENT_WIDTH > content_viewport_width
                    )
                    self.assertEqual(
                        overflows_horizontally,
                        (width, height, ui_scale)
                        in expected_horizontal_overflow,
                    )
                    if overflows_horizontally:
                        horizontal_overflow_cells += 1

                    toggle_left = width + toggle_x * ui_scale - toggle_width * ui_scale
                    toggle_right = width + toggle_x * ui_scale
                    toggle_top = toggle_y * ui_scale
                    toggle_bottom = toggle_top + toggle_height * ui_scale
                    self.assertGreaterEqual(toggle_left, 0)
                    self.assertLessEqual(toggle_right, width)
                    self.assertGreaterEqual(toggle_top, 0)
                    self.assertLessEqual(toggle_bottom, height)
                    self.assertGreaterEqual(
                        width - toggle_right,
                        50 * ui_scale + 10 * ui_scale,
                    )

                    modal_rect = (0, 0, width, height)
                    self.assertEqual(modal_rect, (0, 0, width, height))
                    self.assertGreaterEqual(panel_left, modal_rect[0])
                    self.assertGreaterEqual(panel_top, modal_rect[1])
                    self.assertLessEqual(panel_right, modal_rect[2])
                    self.assertLessEqual(panel_bottom, modal_rect[3])

        self.assertEqual(tested_cells, 9)
        self.assertEqual(
            horizontal_overflow_cells,
            len(expected_horizontal_overflow),
        )

    def test_responsive_scrollbars_add_no_product_action_buttons(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        expected_direct = {
            "button_standard = {": SLOT_COUNT * 2 + 4,
            "button_normal = {": 1,
            "button_tab = {": 3 + len(DETAIL_PAGES),
            "button_tertiary = {": SLOT_COUNT * 2,
        }
        for marker, expected in expected_direct.items():
            self.assertEqual(gui.count(marker), expected, marker)
        self.assertEqual(sum(expected_direct.values()), 332)
        self.assertEqual(gui.count('blockoverride "button_close"'), 1)

        # The seven as-needed horizontal scroll surfaces instantiate the
        # vanilla Scrollbar_Horizontal template.  They introduce no product
        # action node in this generated file; the template owns four bounded
        # navigation descendants (track, slider, decrement and increment).
        horizontal_surfaces = gui.count("using = Scrollbar_Horizontal")
        vertical_surfaces = gui.count("using = Scrollbar_Vertical")
        self.assertEqual(horizontal_surfaces, 7)
        self.assertEqual(vertical_surfaces, 7)
        self.assertNotIn("scrollbar = {", gui)
        vanilla_navigation_descendants = 4
        self.assertEqual(
            horizontal_surfaces * vanilla_navigation_descendants,
            28,
        )
        preexisting_vertical_surfaces = 6
        new_vertical_surfaces = vertical_surfaces - preexisting_vertical_surfaces
        self.assertEqual(new_vertical_surfaces, 1)
        self.assertEqual(
            (horizontal_surfaces + new_vertical_surfaces)
            * vanilla_navigation_descendants,
            32,
        )

    def test_all_interactive_controls_keep_the_modal_contract(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        toggle = re.search(
            r'name = "zg361_scoreboard_toggle"(?P<body>.*?)\n\t\}', gui, re.S
        )
        self.assertIsNotNone(toggle)
        self.assertEqual(
            (toggle.group("body") if toggle else "").count("button_standard = {"),
            3,
        )
        toggle_body = toggle.group("body") if toggle else ""
        self.assertIn("zg361_mechanism_ledger_available_gui", toggle_body)
        self.assertIn(
            "GetVariableSystem.Set('zg361_scoreboard_tab', 'system')",
            toggle_body,
        )
        self.assertIn(
            "Not(GetScriptedGui('zg361_scoreboard_managed_available_gui')",
            toggle_body,
        )
        self.assertIn(
            "Not(GetScriptedGui('zg361_scoreboard_received_available_gui')",
            toggle_body,
        )
        self.assertEqual(gui.count("button_tertiary = {"), SLOT_COUNT * 2)
        self.assertEqual(
            gui.count('onclick = "[DefaultOnCharacterClick(Character.GetID)]"'),
            SLOT_COUNT * 2,
        )
        # Every row opens the frozen character, then dismisses the modal.
        row_pattern = re.compile(
            r"button_tertiary\s*=\s*\{.*?"
            r"onclick\s*=\s*\"\[DefaultOnCharacterClick\(Character.GetID\)\]\".*?"
            r"onclick\s*=\s*\"\[GetVariableSystem.Clear\('zg361_scoreboard_open'\)\]\"",
            re.S,
        )
        self.assertEqual(len(row_pattern.findall(gui)), SLOT_COUNT * 2)
        for tab in ("managed", "received", "system"):
            self.assertIn(
                f"onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', '{tab}')]\"",
                gui,
            )
            self.assertIn(
                f"down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', '{tab}')]\"",
                gui,
            )
        self.assertRegex(
            gui,
            re.compile(
                r"button_normal\s*=\s*\{\s*"
                r'name\s*=\s*"zg361_scoreboard_modal_backdrop_close"\s*'
                r"size\s*=\s*\{\s*100%\s+100%\s*\}.*?"
                r"GetVariableSystem.Clear\('zg361_scoreboard_open'\).*?"
                r"GetVariableSystem.Set\('zg361_scoreboard_view', 'list'\).*?"
                r"GetVariableSystem.Set\('zg361_scoreboard_detail_tab', 'facts'\).*?"
                r"shortcut\s*=\s*close_window",
                re.S,
            ),
        )
        self.assertRegex(
            gui,
            re.compile(
                r'blockoverride\s+"button_close"\s*\{.*?'
                r"GetVariableSystem.Clear\('zg361_scoreboard_open'\).*?"
                r'shortcut\s*=\s*close_window',
                re.S,
            ),
        )
        self.assertNotIn('shortcut = "close_window"', gui)
        modal = re.search(
            r'name = "zg361_scoreboard_modal"(?P<body>.*?)\n\t\twidget = \{',
            gui,
            re.S,
        )
        self.assertIsNotNone(modal)
        self.assertIn(
            "GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown",
            modal.group("body") if modal else "",
        )
        for gate in (
            "Not(IsPauseMenuShown)",
            "IsDefaultGUIMode",
            "Not(IsGameViewOpen('struggle'))",
            "hide_ui_main_tabs",
            "Not(IsRightWindowOpen)",
            "Not(IsGameViewOpen('outliner'))",
            "Not(IsGameViewOpen('barbershop'))",
        ):
            self.assertIn(gate, modal.group("body") if modal else "")

    def test_row_content_cannot_intercept_the_character_button(self) -> None:
        # The character portion of the row is one button. Every rendered leaf
        # passes pointer input through to it; the dossier control is its sibling.
        row = row_gui("m", 1)
        interactive_leaves = [
            line
            for line in row
            if "text_single = {" in line or "portrait_head_small = {" in line
        ]
        self.assertEqual(len(interactive_leaves), 12)
        for line in interactive_leaves:
            self.assertIn("alwaystransparent = yes", line)
        portrait = next(line for line in interactive_leaves if "portrait_head_small" in line)
        self.assertIn('blockoverride "portrait_button"', portrait)


def _calibrate_demote_fixture(rows: list[dict[str, int | bool]]) -> bool:
    """Mirror the CK3 selector: freeze both real candidates, then swap once."""
    demotable = [row for row in rows if row["grade"] == 2 and not row["newcomer"]]
    rescuable = [row for row in rows if row["grade"] == 1]
    if not demotable or not rescuable:
        return False
    demote = max(demotable, key=lambda row: int(row["rank"]))
    rescue = min(rescuable, key=lambda row: int(row["rank"]))
    rescue["grade"] = 2
    demote["grade"] = 1
    return True


class ReviewRegressionTests(unittest.TestCase):
    def test_calibration_c_all_newcomer_fixture_is_noop(self) -> None:
        rows = [
            {"rank": 1, "grade": 3, "newcomer": True},
            {"rank": 2, "grade": 2, "newcomer": True},
            {"rank": 3, "grade": 2, "newcomer": True},
        ]
        before = [dict(row) for row in rows]
        self.assertFalse(_calibrate_demote_fixture(rows))
        self.assertEqual(rows, before)

    def test_calibration_c_mixed_fixture_is_atomic_and_protects_newcomer(self) -> None:
        rows = [
            {"rank": 7, "grade": 2, "newcomer": True},
            {"rank": 8, "grade": 2, "newcomer": False},
            {"rank": 9, "grade": 1, "newcomer": False},
        ]
        counts_before = {grade: sum(row["grade"] == grade for row in rows) for grade in (1, 2, 3)}
        self.assertTrue(_calibrate_demote_fixture(rows))
        counts_after = {grade: sum(row["grade"] == grade for row in rows) for grade in (1, 2, 3)}
        self.assertEqual(counts_after, counts_before)
        self.assertEqual(rows[0]["grade"], 2)
        self.assertEqual(rows[1]["grade"], 1)
        self.assertEqual(rows[2]["grade"], 2)

    def test_product_and_live_fixture_use_the_atomic_contract(self) -> None:
        effects = (MOD_ROOT / "common" / "scripted_effects" / "zg361_effects.txt").read_text(
            encoding="utf-8-sig"
        )
        events = (MOD_ROOT / "events" / "zg361_events.txt").read_text(
            encoding="utf-8-sig"
        )
        triggers = (
            MOD_ROOT / "common" / "scripted_triggers" / "zg361_triggers.txt"
        ).read_text(encoding="utf-8-sig")
        fixture = (
            MOD_ROOT.parent
            / "tools"
            / "fixtures"
            / "zg361_acceptance"
            / "common"
            / "scripted_effects"
            / "zga_effects.txt"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("trigger = { zg361_can_calibrate_demote_trigger = yes }", events)
        self.assertRegex(
            triggers,
            re.compile(
                r"zg361_can_calibrate_demote_trigger\s*=.*?"
                r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{\s*"
                r"has_variable\s*=\s*zg361_pending_grade\s*\}\s*"
                r"var:zg361_pending_grade\s*=\s*2.*?"
                r"trigger_else\s*=\s*\{\s*always\s*=\s*no\s*\}.*?"
                r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{\s*"
                r"has_variable\s*=\s*zg361_pending_grade\s*\}\s*"
                r"var:zg361_pending_grade\s*=\s*1.*?"
                r"trigger_else\s*=\s*\{\s*always\s*=\s*no\s*\}",
                re.S,
            ),
        )
        self.assertRegex(
            triggers,
            re.compile(
                r"zg361_is_current_liege_review_record_trigger\s*=\s*\{.*?"
                r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{.*?"
                r"has_variable\s*=\s*zg361_last_reviewer.*?"
                r"has_variable\s*=\s*zg361_last_review_serial.*?"
                r"liege\s*=\s*\{\s*has_variable\s*=\s*zg361_review_serial\s*\}.*?"
                r"var:zg361_last_reviewer\s*=\s*liege.*?"
                r"var:zg361_last_review_serial\s*=\s*liege\.var:zg361_review_serial.*?"
                r"trigger_else\s*=\s*\{\s*always\s*=\s*no\s*\}",
                re.S,
            ),
        )
        self.assertIn("save_temporary_scope_as = zg361_calibration_demote_target", effects)
        self.assertIn("save_temporary_scope_as = zg361_calibration_rescue_target", effects)
        assignment_at = effects.index("zg361_assign_pending_grades_effect = yes")
        calibration_at = effects.index(
            "trigger_event = { id = zg361.10", assignment_at
        )
        self.assertNotIn(
            "remove_character_flag = zg361_newcomer_this_cycle",
            effects[assignment_at:calibration_at],
        )
        self.assertRegex(
            effects,
            re.compile(
                r"NOT\s*=\s*\{\s*has_variable\s*=\s*zg361_prev_merit_level\s*\}.*?"
                r"root\s*=\s*\{\s*has_character_flag\s*=\s*"
                r"zg361_review_baseline_initialized\s*\}.*?"
                r"add_character_flag\s*=\s*zg361_newcomer_this_cycle",
                re.S,
            ),
        )
        assignment = re.search(
            r"zg361_assign_pending_grades_effect\s*=\s*\{(?P<body>.*?)^\}",
            effects,
            re.M | re.S,
        )
        self.assertIsNotNone(assignment)
        assignment_body = assignment.group("body") if assignment else ""
        self.assertRegex(
            assignment_body,
            re.compile(
                r"every_in_list\s*=\s*\{\s*"
                r"list\s*=\s*zg361_cohort.*?"
                r"NOT\s*=\s*\{\s*has_character_flag\s*=\s*"
                r"zg361_newcomer_this_cycle\s*\}.*?"
                r"add_to_list\s*=\s*zg361_bottom_candidates",
                re.S,
            ),
        )
        self.assertRegex(
            assignment_body,
            re.compile(
                r"ordered_in_list\s*=\s*\{\s*"
                r"list\s*=\s*zg361_bottom_candidates.*?"
                r"max\s*=\s*list_size:zg361_bottom_candidates",
                re.S,
            ),
        )
        zero_based_gate = (
            "root.var:zg361_bottom_cursor < root.var:zg361_bottom_slots"
        )
        bottom_increment = (
            "root = { change_variable = { name = zg361_bottom_cursor add = 1 } }"
        )
        self.assertIn(zero_based_gate, assignment_body)
        self.assertIn(bottom_increment, assignment_body)
        self.assertLess(
            assignment_body.index(zero_based_gate),
            assignment_body.index(bottom_increment),
        )
        self.assertNotIn(
            "zg361_bottom_cursor <= root.var:zg361_bottom_slots",
            assignment_body,
        )
        settlement = re.search(
            r"zg361_apply_pending_grades_effect\s*=\s*\{(?P<body>.*?)^\}",
            effects,
            re.M | re.S,
        )
        self.assertIsNotNone(settlement)
        self.assertIn(
            "add_character_flag = zg361_review_baseline_initialized",
            settlement.group("body") if settlement else "",
        )
        self.assertRegex(
            settlement.group("body") if settlement else "",
            re.compile(
                r"zg361_apply_grade_effect\s*=\s*yes\s*"
                r"remove_character_flag\s*=\s*zg361_newcomer_this_cycle"
            ),
        )
        self.assertRegex(
            effects,
            re.compile(
                r"zg361_calibrate_demote_effect\s*=.*?"
                r"NOT\s*=\s*\{\s*has_character_flag\s*=\s*zg361_newcomer_this_cycle.*?"
                r"scope:zg361_calibration_rescue_target\s*=.*?pending_grade\s+value\s*=\s*2.*?"
                r"scope:zg361_calibration_demote_target\s*=.*?pending_grade\s+value\s*=\s*1",
                re.S,
            ),
        )
        fixture_regression = re.search(
            r"zga_verify_calibration_c_regressions_effect\s*=\s*\{"
            r"(?P<body>.*?)^\}",
            fixture,
            re.M | re.S,
        )
        self.assertIsNotNone(fixture_regression)
        fixture_body = fixture_regression.group("body") if fixture_regression else ""
        self.assertIn(
            "var:zga_all_new_protected_actual = var:zg361_cohort_n", fixture_body
        )
        self.assertEqual(fixture_body.count("zga_original_pending_grade"), 9)
        self.assertIn(
            "var:zga_mixed_35_actual = var:zga_mixed_35_actual_before",
            fixture_body,
        )
        self.assertIn(
            "var:zga_mixed_325_actual = var:zga_mixed_325_actual_before",
            fixture_body,
        )
        self.assertNotIn(
            "change_variable = { name = zg361_pending_35_n", fixture_body
        )
        self.assertNotIn(
            "change_variable = { name = zg361_pending_325_n", fixture_body
        )
        for marker in (
            "calibration_c_all_newcomer_noop",
            "calibration_c_mixed_newcomer_atomic_swap",
        ):
            self.assertIn(f"ZGA: TEST PASS {marker}", fixture)


if __name__ == "__main__":
    sys.exit(unittest.main())
