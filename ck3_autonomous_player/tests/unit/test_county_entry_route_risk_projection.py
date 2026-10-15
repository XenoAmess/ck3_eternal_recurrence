from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.army_current_unit_arrival_prestore_disembark_write_projection import (
    project_current_unit_arrival_prestore_disembark_write_v1,
)
from xar_autoplayer.bridge.war_contract import normalize_army_strengths


def sample():
    strength = {
        "status": "available", "army_id": 18, "native_carmy_id": 18,
        "scope_role": "player", "war_ids": [], "regiment_count": 1,
        "current_soldiers": 900, "maximum_soldiers": 1500,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100_000, "unavailable_reason": None,
        "county_entry_inputs_v1": {
            "status": "available", "source": "native_current_county_entry_inputs",
            "unavailable_reason": None, "whole_soldiers": 900, "current_loss_budget": 137,
            "effective_fraction_raw": 5_000, "minimum_multiplier_raw": 100_000,
            "loaded_minimum_soldiers": 100, "fraction_scale": 100_000, "soldier_scale": 1,
            "condition": {"status": "available", "source": "current_stored_route_first_province",
                          "unavailable_reason": None, "actor_character_id": 21,
                          "source_province_id": 100, "target_province_id": 101, "mode": 1, "passes": True},
            "multiplier_floor_inputs_v1": {
                "status": "available", "source": "native_current_county_multiplier_floor_inputs",
                "unavailable_reason": None, "fraction_scale": 100_000,
                "base_floor_raw": 0, "army_1d4_nonzero_floor_raw": 100_000, "army_1d4_raw": 0,
            },
        },
        "loss_application_inputs_v1": {
            "status": "available", "unavailable_reason": None, "fraction_scale": 100_000, "soldier_scale": 1,
            "raid_association_id": -1, "whole_soldiers": 900, "definition_le_zero_soldiers": 80,
            "supply_eligible_soldiers": 900, "definition_le_zero_supply_eligible_soldiers": 80,
            "current_supply_loss_budget": 0, "siege_loss_budget": 0, "raid_loss_budget": 0,
            "siege_rate_raw": 0, "raid_rate_raw": 0, "siege_active": False, "raid_active": False,
        },
        "current_movement_progress": {
            "status": "available", "source": "native_current_route_edge", "unit_state_raw": 0,
            "accumulated_movement_weight_raw": 106, "cached_edge_speed_raw": 1,
            "normalized_edge_progress": {"raw": 99_000, "scale": 100_000},
            "first_route_edge_remaining_duration": {"raw": 1_000, "scale": 100_000},
            "unavailable_reason": None, "current_province_type_tag_u32": 0x50726F76,
            "first_route_target_province_type_tag_u32": 0x50726F76,
            "unit_kind_18_raw_i32": 0, "current_province_definition_byte_1b_u8": 1,
            "first_route_target_province_definition_byte_1b_u8": 1,
            "loaded_disembark_penalty_days_rule_i32": 30,
        },
    }
    context = {"army_id": 18, "current_province_id": 100, "route_province_ids": [101, 102],
               "route_read_status": "complete_nonempty", "route_source_count": 2}
    arrival = {"arrival_transition_input_ready": True, "unavailable_reason": None,
               "conditional_first_province_assignment_selected": True,
               "subject_army_id_u32": 18, "subject_carmy_id_u32": 18, "subject_stored_id_positions": [0]}
    prefix = {"movement_prefix_input_ready": True,
              "conditional_unit_170_raw_after_next_new_date_entry_prefix": 0,
              "subject_army_id_u32": 18, "subject_carmy_id_u32": 18}
    return strength, context, arrival, prefix


def explain(strength, context, arrival, prefix):
    normalized = normalize_army_strengths([strength])[0]
    return project_current_unit_arrival_prestore_disembark_write_v1(
        normalized, arrival_transition=arrival, army_context=context, movement_prefix=prefix,
    )["county_entry_risk_v1"]


class CountyEntryRouteRiskProjectionTests(unittest.TestCase):
    def test_existing_service_seam_forwards_same_query_prefix_and_native_budget_partition(self):
        from xar_autoplayer.bridge import service
        strength, context, arrival, prefix = sample()
        original = deepcopy(strength)
        with patch.object(service, "project_current_unit_next_movement_prefix_v1", return_value=prefix), \
             patch.object(service, "project_current_unit_next_first_edge_selection_v1", return_value={}), \
             patch.object(service, "project_current_unit_next_arrival_transition_v1", return_value=arrival):
            output = service.GameplayBridgeService._unit_next_movement_projection_rows(
                {"queried_snapshot_id": "test", "queried_revision": 7, "queried_native_revision": 9},
                normalize_army_strengths([strength]), snapshot={"snapshot_id": "test", "revision": 7,
                    "native_revision": 9, "player_armies": [context]},
            )
        risk = output["current_unit_arrival_prestore_disembark_write_v1"][0]["projection"]["county_entry_risk_v1"]
        self.assertTrue(risk["conditional_positive_county_budget_selected"])
        self.assertEqual(risk["observed_current_native_budget"]["current_loss_budget"], 137)
        self.assertEqual(risk["conditional_allocation"]["primary_budget_soldiers"], 80)
        self.assertEqual(risk["conditional_allocation"]["residual_budget_soldiers"], 57)
        self.assertIsNone(risk["conditional_allocation"]["actual_physical_debit_soldiers"])
        self.assertEqual(risk["decision"]["review"], "review_current_edge_before_advancing")
        self.assertIsNone(risk["decision"]["selected_new_target_province_id"])
        self.assertEqual(strength, original)

    def test_observed_false_condition_and_zero_budget_close_local_positive_gate_without_physical_zero_claim(self):
        for mode in ("condition_false", "budget_zero"):
            with self.subTest(mode=mode):
                strength, context, arrival, prefix = sample()
                if mode == "condition_false":
                    strength["county_entry_inputs_v1"]["condition"]["passes"] = False
                else:
                    strength["county_entry_inputs_v1"]["current_loss_budget"] = 0
                risk = explain(strength, context, arrival, None)
                self.assertIs(risk["conditional_positive_county_budget_selected"], False)
                self.assertIs(risk["actual_county_loss_observed"], False)
                self.assertIsNone(risk["complete_county_or_periodic_loss"])
                self.assertEqual(risk["decision"]["readonly_choices"], [])
        strength, context, arrival, prefix = sample()
        arrival["conditional_first_province_assignment_selected"] = False
        risk = explain(strength, context, arrival, prefix)
        self.assertIs(risk["conditional_positive_county_budget_selected"], False)
        self.assertIs(risk["conditional_positive_county_budget_if_this_edge_arrives"], True)
        self.assertEqual(risk["decision"]["review"], "review_current_edge_before_advancing")

    def test_missing_fresh_route_or_prefix_returns_specific_observation_without_invented_target(self):
        strength, context, arrival, prefix = sample()
        for selected_context, selected_prefix, missing in (
            (None, prefix, "same_query_player_armies.current_province_id/complete_route/revision"),
            (context, None, "current_unit_next_movement_prefix_v1.conditional_unit_170_raw_after_next_new_date_entry_prefix"),
        ):
            risk = explain(strength, selected_context, arrival, selected_prefix)
            self.assertIsNone(risk["conditional_positive_county_budget_selected"])
            self.assertIn(missing, [item["field"] for item in risk["required_observations"]])
            self.assertEqual(risk["observed_current_native_budget"]["current_loss_budget"], 137)
            self.assertIsNone(risk["decision"]["selected_new_target_province_id"])
        context.update(route_read_status="complete_empty", route_source_count=0, route_province_ids=[])
        risk = explain(strength, context, arrival, prefix)
        self.assertIs(risk["fresh_route_context_ready"], True)
        self.assertIs(risk["first_route_edge_present"], False)
        self.assertEqual(risk["decision"]["review"], "no_current_first_edge_to_assess")
        self.assertIsNone(risk["conditional_positive_county_budget_if_this_edge_arrives"])
        strength["county_entry_inputs_v1"]["condition"].update(
            status="unavailable", unavailable_reason="no_stored_route", actor_character_id=None,
            source_province_id=None, target_province_id=None, mode=None, passes=None)
        risk = explain(strength, None, arrival, None)
        self.assertIs(risk["observed_complete_empty_route"], True)
        self.assertIs(risk["fresh_route_context_ready"], False)
        self.assertIs(risk["first_route_edge_present"], False)
        self.assertEqual(risk["decision"]["review"], "no_current_first_edge_to_assess")

    def test_loaded_positive_second_floor_distinguishes_special_zero_from_ordinary_or_unknown_zero(self):
        strength, context, arrival, prefix = sample()
        inputs = strength["county_entry_inputs_v1"]
        inputs.update(current_loss_budget=0, effective_fraction_raw=0, minimum_multiplier_raw=0)
        inputs["condition"]["mode"] = 0
        inputs["multiplier_floor_inputs_v1"]["army_1d4_raw"] = 9
        risk = explain(strength, context, arrival, prefix)
        self.assertIs(risk["multiplier_zero_predicate"]["passes"], True)
        del inputs["multiplier_floor_inputs_v1"]
        risk = explain(strength, context, arrival, prefix)
        self.assertIsNone(risk["multiplier_zero_predicate"]["passes"])
        inputs["multiplier_floor_inputs_v1"] = sample()[0]["county_entry_inputs_v1"]["multiplier_floor_inputs_v1"]
        inputs["condition"]["mode"] = 1
        risk = explain(strength, context, arrival, prefix)
        self.assertIs(risk["multiplier_zero_predicate"]["passes"], False)
        strength, context, arrival, prefix = sample()
        strength["county_entry_inputs_v1"]["multiplier_floor_inputs_v1"]["base_floor_raw"] = 10_000
        risk = explain(strength, context, arrival, prefix)
        self.assertEqual(risk["multiplier_branch_explanation"]["inferred_ordinary_army_property_1a7_raw"], 0)
        self.assertIs(risk["multiplier_branch_explanation"]["army_1d4_nonzero_floor_demanded"], False)


if __name__ == "__main__":
    unittest.main()
