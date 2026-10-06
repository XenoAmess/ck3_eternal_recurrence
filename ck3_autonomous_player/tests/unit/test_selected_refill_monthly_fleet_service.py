"""One production service compound for fixed-context fleet monthly assembly."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from test_selected_refill_monthly_assembly_service import assembly_packet, MemoryRoute


def fleet_packet() -> dict:
    packet = assembly_packet()
    packet["current_supply_change_monthly_raw"] = -50000
    packet["current_land_resupply_v1"].update(
        status="not_land", current_observation_ready=False,
        owner_character_id=None, native_land_branch_applicable=False,
        native_resupply_eligible=None)
    packet["current_land_supply_rate_inputs_v1"].update(
        status="not_land", current_observation_ready=False,
        owner_character_id=None, native_land_branch_applicable=False,
        commander_raw_full_id=None, commander_resolved_full_id=None,
        commander_used_native_fallback=None,
        native_province_component_applicable=None, province_component_raw=None,
        commander_modifier_1a9_raw=None)
    # Fleet rate has no Province contributor/usage dependency. Subject DATA
    # still supplies the selected physical refill and subsequent loss writer.
    del packet["current_province_supply_contributors_v1"]
    return packet


class SelectedRefillMonthlyFleetServiceTests(unittest.TestCase):
    def test_fleet_fixed_context_rate_and_independent_partial_branches(self) -> None:
        outputs = {}

        def query(name: str, packet: dict) -> tuple[dict, dict]:
            before = deepcopy(packet)
            service = MemoryRoute(packet)
            result = service.query_army_strengths([11], expected_revision=42)
            outputs[name] = result
            if target := os.environ.get("XAR_FLEET_SELECTED_ASSEMBLY_OUTPUT"):
                Path(target).write_text(
                    json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
            self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(packet, before)
            self.assertEqual(result["status"], "available")
            self.assertEqual(result["scope_status"], "available")
            self.assertEqual(result["native_readiness"],
                             {"current_strength": True, "full_monthly": False})
            native = result["army_strengths"][0]
            self.assertEqual(native["current_soldiers"], 210)
            self.assertEqual(native["current_supply_raw"], 1040000)
            self.assertEqual(native["current_supply_change_monthly_raw"],
                             packet["current_supply_change_monthly_raw"])
            self.assertEqual(native["regiment_strengths"], packet["regiment_strengths"])
            self.assertEqual(native["regiment_replenishment_records_v1"],
                             packet["regiment_replenishment_records_v1"])
            self.assertIsNone(native.get("current_province_supply_contributors_v1"))
            for family in ("current_land_resupply_v1", "current_land_supply_rate_inputs_v1"):
                self.assertEqual(native[family], packet[family])
            self.assertFalse(native["monthly_loss_budget_inputs_v1"]
                                   ["native_fleet_supply_loss_suppressed"])
            original = result["loss_allocation_requests_v1"][0]
            self.assertFalse(original["applied_loss_ready"])
            self.assertIsNone(original["applied_soldier_loss"])
            value = result["same_input_conditional_selected_refill_monthly_assembly_v1"][0]
            joined = result["same_input_conditional_post_refill_land_supply_rate_v1"][0]
            self.assertEqual(value["joined_post_refill_land_rate"], joined)
            self.assertFalse(value["selected_land_rate_ready"])
            self.assertIsNone(value["selected_land_rate_raw"])
            self.assertFalse(joined["conditional_full_land_rate_ready"])
            self.assertIsNone(joined["conditional_post_refill_supply_rate_raw"])
            self.assertEqual(joined["current_resupply_inputs_v1"],
                             packet["current_land_resupply_v1"])
            self.assertEqual(joined["current_land_rate_inputs_v1"],
                             packet["current_land_supply_rate_inputs_v1"])
            for key in ("actual_replenishment", "actual_loss", "actual_effects",
                        "full_regular_refill_ready", "full_monthly_ready"):
                self.assertFalse(value[key])
            self.assertIsNone(value["actual_post_stage_current"])
            self.assertIsNone(value["actual_post_supply_usage_soldiers"])
            self.assertEqual(value["derived_subject_frame"]["count_by_native_flags"],
                             {"0": 250, "1": 180, "2": 180, "3": 180})
            self.assertEqual([value["monthly_loss_budgets"][f"{prefix}_budget_soldiers"]
                              for prefix in ("siege", "raid")], [41, 12])
            return result, value

        _, value = query("fleet-negative-refill-stock-crossing", fleet_packet())
        self.assertTrue(value["conditional_assembly_ready"])
        self.assertTrue(value["conditional_physical_refill_ready"])
        self.assertTrue(value["conditional_physical_loss_ready"])
        self.assertTrue(value["rate_required_by_updater"])
        self.assertEqual(value["selected_full_supply_rate_mode"], "fleet")
        self.assertTrue(value["selected_full_supply_rate_ready"])
        self.assertEqual(value["selected_full_supply_rate_raw"], -50000)
        self.assertEqual(value["selected_full_supply_rate_input_basis"],
                         "observed_current_fleet_rate_fixed_context")
        self.assertTrue(value["selected_fleet_rate_ready"])
        self.assertEqual(value["selected_fleet_rate_raw"], -50000)
        self.assertTrue(value["conditional_post_stock_ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 990000)
        self.assertEqual([row["current_soldiers"]
                          for row in value["derived_subject_frame"]["regiment_strengths"]],
                         [180, 70])
        chunks = {row["persistent_regiment_id"]: row
                  for row in value["selected_refill_union"]["physical_chunks"]
                  if row["chunk_index"] == 0}
        self.assertEqual([(chunks[identity]["same_input_q"],
                           chunks[identity]["physical_add_count"],
                           chunks[identity]["current_soldiers"])
                          for identity in (50001, 50002)], [(10, 1, 90), (20, 1, 70)])
        self.assertEqual(len(chunks[50001]["data_occurrences"]), 2)
        data = value["derived_subject_frame"]["DATA"][0]
        self.assertEqual([data["records"][index]["current_soldiers"]
                          for index in (0, 7)], [90, 90])
        budgets = value["monthly_loss_budgets"]
        self.assertEqual(budgets["supply_state_index"], 2)
        self.assertEqual([budgets[f"{prefix}_budget_soldiers"]
                          for prefix in ("supply", "siege", "raid")], [18, 41, 12])
        sequence = budgets["same_input_conditional_loss_sequence_v1"]
        self.assertTrue(sequence["conditional_sequence_ready"])
        self.assertEqual(sequence["passes"][0]["requests"][0]["current_soldiers_read"], 180)
        writer = sequence["passes"][0]["requests"][0]["conditional_chunk_writeback"]
        self.assertEqual(writer["writes"][0]["current_before"], 90)
        self.assertLess(writer["writes"][0]["current_after"], 90)
        self.assertTrue(sequence["initial_state_basis"].startswith("derived_selected_refill"))
        self.assertTrue(writer["input_basis"].startswith("derived_same_stage"))

        missing = fleet_packet()
        missing["current_supply_change_monthly_raw"] = None
        _, value = query("fleet-missing-rate-independent-siege-raid", missing)
        self.assertFalse(value["conditional_assembly_ready"])
        self.assertEqual(value["selected_full_supply_rate_mode"], "fleet")
        self.assertFalse(value["selected_full_supply_rate_ready"])
        self.assertIsNone(value["selected_full_supply_rate_raw"])
        self.assertFalse(value["selected_fleet_rate_ready"])
        self.assertIsNone(value["selected_fleet_rate_raw"])
        self.assertFalse(value["conditional_post_stock_ready"])
        self.assertIsNone(value["conditional_post_stock_raw"])
        self.assertIsNone(value["monthly_loss_budgets"]["supply_budget_soldiers"])

        zero = fleet_packet()
        zero["current_supply_change_monthly_raw"] = 0
        _, value = query("fleet-observed-zero-no-unobserved-cause", zero)
        self.assertTrue(value["conditional_assembly_ready"])
        self.assertEqual(value["selected_full_supply_rate_mode"], "fleet")
        self.assertTrue(value["selected_full_supply_rate_ready"])
        self.assertEqual(value["selected_full_supply_rate_raw"], 0)
        self.assertEqual(value["selected_full_supply_rate_input_basis"],
                         "observed_current_fleet_rate_fixed_context")
        self.assertTrue(value["selected_fleet_rate_ready"])
        self.assertEqual(value["selected_fleet_rate_raw"], 0)
        self.assertEqual(value["conditional_post_stock_raw"], 1040000)
        self.assertEqual(value["monthly_loss_budgets"]["supply_budget_soldiers"], 0)
        # A public zero rate is usable without claiming its unobserved terrain,
        # date or commander cause. No positive terrain772 flag is supplied.

        unknown = fleet_packet()
        unknown["current_movement_progress"] = {
            "status": "not_applicable", "source": "native_current_route_edge",
            "unit_state_raw": 4, "accumulated_movement_weight_raw": None,
            "cached_edge_speed_raw": None, "normalized_edge_progress": None,
            "first_route_edge_remaining_duration": None, "unavailable_reason": None,
        }
        for family in ("current_land_resupply_v1", "current_land_supply_rate_inputs_v1"):
            unknown[family].update(
                status="unavailable", current_observation_ready=False,
                unavailable_reason="native_supply_change_branch_unavailable",
                native_land_branch_applicable=None)
        result, value = query("unknown-native-branch-ui-embarked-is-insufficient", unknown)
        self.assertEqual(result["army_strengths"][0]["current_movement_progress"]["unit_state_raw"], 4)
        self.assertFalse(value["conditional_assembly_ready"])
        self.assertEqual(value["selected_full_supply_rate_mode"], "unknown")
        self.assertFalse(value["selected_full_supply_rate_ready"])
        self.assertIsNone(value["selected_full_supply_rate_raw"])
        self.assertFalse(value["selected_fleet_rate_ready"])
        self.assertIsNone(value["selected_fleet_rate_raw"])
        self.assertFalse(value["conditional_post_stock_ready"])
        self.assertIsNone(value["monthly_loss_budgets"]["supply_budget_soldiers"])

        rejected = fleet_packet()
        rejected["current_supply_change_monthly_raw"] = None
        rejected["monthly_loss_budget_inputs_v1"]["unit_native_170_raw"] = 3
        _, value = query("rejected-updater-unused-fleet-rate-null", rejected)
        self.assertTrue(value["conditional_assembly_ready"])
        self.assertFalse(value["rate_required_by_updater"])
        self.assertFalse(value["selected_full_supply_rate_ready"])
        self.assertIsNone(value["selected_full_supply_rate_raw"])
        self.assertFalse(value["selected_fleet_rate_ready"])
        self.assertIsNone(value["selected_fleet_rate_raw"])
        self.assertTrue(value["conditional_post_stock_ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 1040000)
        self.assertEqual(value["monthly_loss_budgets"]["supply_budget_soldiers"], 0)
        self.assertEqual(value["monthly_caller_effects"]["conditional_supply_update_date_raw64"],
                         (3 << 32) + 120)
        self.assertEqual(value["missing_inputs"], [])


if __name__ == "__main__":
    unittest.main()
