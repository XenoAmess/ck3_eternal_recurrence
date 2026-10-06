"""One new production service case for selected refill through monthly effects."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from test_conditional_monthly_loss_budgets import monthly_budget_packet
from test_post_refill_land_rate_service_join import row as land_row, data_snapshot, MemoryRoute


def assembly_packet() -> dict:
    packet = land_row()
    monthly = monthly_budget_packet()
    for key in ("army_update_clock_v1", "monthly_loss_budget_inputs_v1", "loss_application_inputs_v1"):
        packet[key] = monthly[key]
    packet.update(regiment_count=2, current_soldiers=210, maximum_soldiers=300,
                  current_supply_raw=1040000, current_supply_scale=100000,
                  current_supply_capacity_raw=6000000, current_supply_capacity_scale=100000)
    packet["army_update_clock_v1"].update(
        last_supply_update_date_raw=120, last_supply_update_date_storage_raw64=(3 << 32) + 120)
    strengths = []
    for identity, current, maximum, tier, eligible in ((11001, 160, 200, 0, True), (11002, 50, 100, 1, False)):
        regiment = deepcopy(monthly["regiment_strengths"][0])
        regiment.update(army_regiment_id=identity, current_soldiers=current, maximum_soldiers=maximum,
                        siege_tier=tier, maa_type_key=f"tier_{tier}", native_supply_loss_eligible=eligible)
        strengths.append(regiment)
    packet["regiment_strengths"] = strengths
    ineligible = data_snapshot(20000)
    ineligible.update(army_regiment_id=11002, native_data_record_count=1)
    ineligible["records"] = [ineligible["records"][0]]
    ineligible["records"][0].update(persistent_regiment_id=50002, chunk_army_regiment_id=11002,
                                    current_soldiers=50, effective_current_soldiers=50)
    packet["regiment_replenishment_records_v1"] = [data_snapshot(), ineligible]
    for occurrence in packet["current_province_supply_contributors_v1"]["occurrences"]:
        occurrence["regiments"].append({
            "stored_index": 1, "army_regiment_id": 11002, "status": "available",
            "unavailable_reason": None, "current_soldiers": 50, "maximum_soldiers": 100,
            "native_supply_loss_eligible": False, "replenishment_records_v1": None})
    packet["loss_application_inputs_v1"].update(
        whole_soldiers=210, definition_le_zero_soldiers=160, supply_eligible_soldiers=160,
        definition_le_zero_supply_eligible_soldiers=160, siege_rate_raw=16667, raid_rate_raw=5000)
    packet["monthly_caller_effect_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "army_byte_22_raw": 0, "current_date_storage_raw64": (1 << 32) + 264,
        "unit_actor_character_id": 33388, "manager_army_id_list_2a5a8": [12, 7],
        "war_counter_rows": [{
            "stored_index": index, "war_reference_id": 99, "resolved_war_id": 99,
            "used_fallback": False, "native_selected_side": 0, "native_counter_30_raw": 5,
            "status": "available", "unavailable_reason": None} for index in range(2)],
    }
    return packet


class SelectedRefillMonthlyAssemblyServiceTests(unittest.TestCase):
    def test_refill_stock_crossing_writer_frame_and_independent_partial_branches(self) -> None:
        outputs = {}

        def query(name: str, packet: dict) -> tuple[dict, dict]:
            before = deepcopy(packet)
            service = MemoryRoute(packet)
            result = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(packet, before)
            self.assertEqual(result["native_readiness"], {"current_strength": True, "full_monthly": False})
            self.assertEqual(result["army_strengths"][0]["current_soldiers"], 210)
            self.assertEqual(result["army_strengths"][0]["current_supply_raw"], 1040000)
            self.assertEqual(result["army_strengths"][0]["current_supply_change_monthly_raw"], 700000)
            original = result["loss_allocation_requests_v1"][0]
            self.assertFalse(original["applied_loss_ready"])
            self.assertIsNone(original["applied_soldier_loss"])
            value = result["same_input_conditional_selected_refill_monthly_assembly_v1"][0]
            self.assertEqual(value["joined_post_refill_land_rate"],
                             result["same_input_conditional_post_refill_land_supply_rate_v1"][0])
            for key in ("actual_replenishment", "actual_loss", "actual_effects",
                        "full_regular_refill_ready", "full_monthly_ready"):
                self.assertFalse(value[key])
            self.assertIsNone(value["actual_post_stage_current"])
            self.assertIsNone(value["actual_post_supply_usage_soldiers"])
            outputs[name] = result
            if target := os.environ.get("XAR_SELECTED_ASSEMBLY_OUTPUT"):
                Path(target).write_text(json.dumps(outputs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return result, value

        result, value = query("nonzero-refill-stock-crossing", assembly_packet())
        self.assertTrue(value["conditional_assembly_ready"])
        self.assertTrue(value["conditional_physical_refill_ready"])
        self.assertTrue(value["conditional_physical_loss_ready"])
        self.assertEqual(value["derived_subject_frame"]["count_by_native_flags"],
                         {"0": 250, "1": 180, "2": 180, "3": 180})
        self.assertEqual([row["current_soldiers"] for row in value["derived_subject_frame"]["regiment_strengths"]],
                         [180, 70])
        physical = value["selected_refill_union"]["physical_chunks"]
        selected = {row["persistent_regiment_id"]: row for row in physical if row["chunk_index"] == 0}
        self.assertEqual([(selected[identity]["same_input_q"], selected[identity]["physical_add_count"],
                           selected[identity]["current_soldiers"]) for identity in (50001, 50002)],
                         [(10, 1, 90), (20, 1, 70)])
        self.assertEqual(len(selected[50001]["data_occurrences"]), 2)
        data = value["derived_subject_frame"]["DATA"][0]
        self.assertEqual(len(data["records"]), 8)
        self.assertEqual([data["records"][index]["current_soldiers"] for index in (0, 7)], [90, 90])
        usage = value["joined_post_refill_land_rate"]["same_input_conditional_province_supply_usage_v1"]
        self.assertEqual(usage["conditional_supply_usage_soldiers"], 360)
        self.assertEqual([row["stored_index"] for row in usage["occurrences"]], [0, 1])
        self.assertEqual(value["selected_land_rate_raw"], -50000)
        self.assertEqual(value["conditional_post_stock_raw"], 990000)
        budgets = value["monthly_loss_budgets"]
        self.assertEqual(budgets["supply_state_index"], 2)
        self.assertEqual([budgets[f"{prefix}_budget_soldiers"] for prefix in ("supply", "siege", "raid")], [18, 41, 12])
        old = result["loss_allocation_requests_v1"][0]["same_input_conditional_monthly_loss_budgets_v1"]
        self.assertEqual(old["conditional_post_supply_raw"], 1740000)
        self.assertEqual([old[f"{prefix}_budget_soldiers"] for prefix in ("supply", "siege", "raid")], [0, 35, 10])
        sequence = budgets["same_input_conditional_loss_sequence_v1"]
        self.assertTrue(sequence["conditional_sequence_ready"])
        self.assertEqual(sequence["passes"][0]["requests"][0]["current_soldiers_read"], 180)
        writer = sequence["passes"][0]["requests"][0]["conditional_chunk_writeback"]
        self.assertEqual(writer["writes"][0]["current_before"], 90)
        self.assertTrue(sequence["initial_state_basis"].startswith("derived_selected_refill"))
        self.assertTrue(writer["input_basis"].startswith("derived_same_stage"))
        self.assertTrue(all(stage["input_basis"].startswith("derived_") for stage in sequence["passes"]))
        effects = value["monthly_caller_effects"]
        self.assertTrue(effects["conditional_caller_effects_ready"])
        self.assertEqual(effects["war_counter_increment_soldiers"], 59)
        self.assertEqual([row["conditional_counter_after_raw"] for row in effects["war_counter_writes"]], [64, 123])
        self.assertEqual(effects["conditional_supply_update_date_raw64"], (1 << 32) + 264)
        self.assertIsNone(effects["actual_caller_passed_date_raw64"])

        missing_rate = assembly_packet()
        missing_rate["current_land_supply_rate_inputs_v1"].update(
            status="unavailable", current_observation_ready=False, loaded_min_loss_raw=None,
            unavailable_reason="loaded_min_loss_unavailable")
        _, value = query("missing-required-rate-independent-counts", missing_rate)
        self.assertFalse(value["conditional_assembly_ready"])
        self.assertFalse(value["selected_land_rate_ready"])
        self.assertIsNone(value["selected_land_rate_raw"])
        self.assertFalse(value["conditional_post_stock_ready"])
        self.assertEqual(value["derived_subject_frame"]["count_by_native_flags"]["0"], 250)
        self.assertEqual([value["monthly_loss_budgets"][f"{prefix}_budget_soldiers"] for prefix in ("siege", "raid")],
                         [41, 12])

        rejected = assembly_packet()
        rejected["monthly_loss_budget_inputs_v1"]["unit_native_170_raw"] = 3
        for key in ("current_land_supply_rate_inputs_v1", "current_land_resupply_v1", "current_province_supply_contributors_v1"):
            del rejected[key]
        _, value = query("rejected-updater-no-unused-rate", rejected)
        self.assertTrue(value["conditional_assembly_ready"])
        self.assertFalse(value["rate_required_by_updater"])
        self.assertFalse(value["selected_land_rate_ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 1040000)
        self.assertEqual([value["monthly_loss_budgets"][f"{prefix}_budget_soldiers"] for prefix in ("supply", "siege", "raid")],
                         [0, 41, 12])
        self.assertEqual(value["monthly_caller_effects"]["conditional_supply_update_date_raw64"], (3 << 32) + 120)
        self.assertEqual(value["missing_inputs"], [])

        missing_subject = assembly_packet()
        missing_subject["regiment_replenishment_records_v1"] = missing_subject["regiment_replenishment_records_v1"][:1]
        _, value = query("missing-ineligible-subject-DATA-independent-supply", missing_subject)
        self.assertFalse(value["conditional_assembly_ready"])
        self.assertTrue(value["selected_land_rate_ready"])
        self.assertTrue(value["conditional_post_stock_ready"])
        self.assertEqual(value["monthly_loss_budgets"]["supply_budget_soldiers"], 18)
        self.assertIsNone(value["monthly_loss_budgets"]["siege_budget_soldiers"])
        self.assertIsNone(value["monthly_loss_budgets"]["raid_budget_soldiers"])
        self.assertEqual(value["derived_subject_frame"]["count_by_native_flags"],
                         {"0": None, "1": 180, "2": 180, "3": 180})
        self.assertIsNone(value["derived_subject_frame"]["regiment_strengths"][1]["current_soldiers"])
        self.assertFalse(value["conditional_loss_sequence_ready"])


if __name__ == "__main__":
    unittest.main()
