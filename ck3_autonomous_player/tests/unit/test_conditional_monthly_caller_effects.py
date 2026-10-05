"""One new service case: budget-based caller effects and ordered ID append."""
from copy import deepcopy
import unittest

from test_conditional_monthly_loss_budgets import monthly_budget_packet, MemoryStrengthService


def caller_packet():
    packet = monthly_budget_packet()
    packet["regiment_replenishment_records_v1"][0]["native_loss_writer_skipped"] = True
    packet["loss_application_inputs_v1"].update(
        siege_rate_raw=16667, raid_rate_raw=25000, siege_loss_budget=2, raid_loss_budget=3)
    packet["army_update_clock_v1"].update(
        last_supply_update_date_raw=120, last_supply_update_date_storage_raw64=(3 << 32) + 120)
    rows = []
    for reference, resolved, fallback, side, counter in (
        (10, 10, False, 0, 2147483646),
        (20, -1, True, 0, -2),
        (40, 40, False, -1, None),
        (10, 10, False, 0, 2147483646),
        (21, -1, True, 0, -2),
        (10, 10, False, 1, 10),
    ):
        rows.append({
            "stored_index": len(rows), "war_reference_id": reference,
            "resolved_war_id": resolved, "used_fallback": fallback,
            "native_selected_side": side, "native_counter_30_raw": counter,
            "status": "available", "unavailable_reason": None,
        })
    packet["monthly_caller_effect_inputs_v1"] = {
        "status": "available", "ready": True, "unavailable_reason": None,
        "army_byte_22_raw": 0, "current_date_storage_raw64": (1 << 32) + 264,
        "unit_actor_character_id": 29829, "war_counter_rows": rows,
        "manager_army_id_list_2a5a8": [0, 0, 7],
    }
    return packet


class ConditionalMonthlyCallerEffectsTests(unittest.TestCase):
    def test_query_uses_original_budget_cells_and_tail_gate_without_actual_receipts(self):
        def query(packet):
            original = deepcopy(packet)
            service = MemoryStrengthService(packet)
            allocation = service.query_army_strengths([0], expected_revision=2)["loss_allocation_requests_v1"][0]
            effects = allocation["same_input_conditional_monthly_caller_effects_v1"]
            budget = allocation["same_input_conditional_monthly_loss_budgets_v1"]
            self.assertEqual(packet, original)
            self.assertEqual(service.calls, 1)
            self.assertFalse(effects["actual_effects"])
            self.assertFalse(effects["actual_loss"])
            self.assertIsNone(effects["actual_post_state"])
            self.assertIsNone(effects["actual_caller_passed_date_raw64"])
            self.assertEqual(effects["conditional_date_input_basis"],
                             "current_frame_date_storage_as_explicit_entry_argument")
            self.assertFalse(effects["full_monthly_applied_loss_ready"])
            self.assertFalse(allocation["applied_loss_ready"])
            self.assertIsNone(allocation["applied_soldier_loss"])
            return budget, effects

        budget, effects = query(caller_packet())
        self.assertEqual((budget["supply_budget_soldiers"], budget["siege_budget_soldiers"],
                          budget["raid_budget_soldiers"]), (1, 2, 3))
        self.assertTrue(effects["conditional_caller_effects_ready"])
        self.assertEqual(effects["army_byte_22_before"], 0)
        self.assertEqual(effects["conditional_byte_22_after"], 1)
        self.assertEqual(effects["conditional_supply_update_date_raw64"], (1 << 32) + 264)
        self.assertEqual(effects["war_counter_increment_soldiers"], 3)
        # Writer skip preserves all12 troops, while every selected native
        # cell receives the original S+J=3; raid3 is excluded from that add.
        replay = budget["same_input_conditional_loss_sequence_v1"]
        self.assertEqual(replay["conditional_final_current_soldiers"], 12)
        self.assertEqual(replay["conditional_physical_current_delta"], 0)
        self.assertEqual([row["stored_index"] for row in effects["war_counter_writes"]], [0, 1, 3, 4, 5])
        self.assertEqual([row["conditional_counter_after_raw"] for row in effects["war_counter_writes"]],
                         [-2147483647, 1, -2147483644, 4, 13])
        self.assertEqual(effects["war_counter_writes"][2]["conditional_counter_before_raw"], -2147483647)
        self.assertEqual(effects["war_counter_writes"][3]["conditional_counter_before_raw"], 1)
        self.assertEqual([row["write_occurrences"] for row in effects["conditional_war_counter_cells_after"]],
                         [2, 2, 1])
        self.assertEqual(effects["war_counter_skipped_occurrences"][0]["stored_index"], 2)
        self.assertEqual(effects["tail_original_budget_total_soldiers"], 6)
        self.assertFalse(effects["conditional_id_append_required"])
        self.assertEqual(effects["conditional_manager_army_id_list_2a5a8_after"], [0, 0, 7])

        raid_only = caller_packet()
        raid_only["monthly_loss_budget_inputs_v1"]["unit_native_170_raw"] = 3
        raid_only["loss_application_inputs_v1"].update(
            siege_active=False, siege_loss_budget=0, raid_rate_raw=100000, raid_loss_budget=12)
        raid_only["regiment_replenishment_records_v1"][0]["native_loss_writer_skipped"] = False
        raid_only["monthly_caller_effect_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="unneeded_war_rows", war_counter_rows=None)
        raid_budget, appended = query(raid_only)
        self.assertEqual((raid_budget["supply_budget_soldiers"], raid_budget["siege_budget_soldiers"],
                          raid_budget["raid_budget_soldiers"]), (0, 0, 12))
        self.assertFalse(raid_budget["supply_updater_admitted"])
        self.assertEqual(appended["conditional_supply_update_date_raw64"], (3 << 32) + 120)
        self.assertEqual(appended["war_counter_increment_soldiers"], 0)
        self.assertTrue(appended["war_counter_ready"])
        self.assertEqual(appended["war_counter_writes"], [])
        self.assertEqual(appended["tail_original_budget_total_soldiers"], 12)
        self.assertEqual(appended["tail_conditional_post_loss_current_soldiers"], 0)
        self.assertTrue(appended["conditional_id_append_required"])
        self.assertEqual(appended["conditional_manager_army_id_list_2a5a8_after"], [0, 0, 7, 0])
        self.assertTrue(appended["conditional_caller_effects_ready"])

        # Unknown row stops full cell poststate, while independent date and
        # tail/no-append effects retain their available samequery operands.
        partial = caller_packet()
        partial["monthly_caller_effect_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="selected_side_unavailable")
        partial["monthly_caller_effect_inputs_v1"]["war_counter_rows"][1].update(
            status="unavailable", unavailable_reason="selected_side_unavailable",
            resolved_war_id=None, used_fallback=None,
            native_selected_side=None, native_counter_30_raw=None)
        _, prefix = query(partial)
        self.assertFalse(prefix["war_counter_ready"])
        self.assertEqual(len(prefix["war_counter_writes"]), 1)
        self.assertIsNone(prefix["conditional_war_counter_cells_after"])
        self.assertTrue(prefix["conditional_supply_update_date_ready"])
        self.assertTrue(prefix["conditional_manager_army_id_list_ready"])

        # Low32 date264 cannot supply an absent64-bit passed-date high half.
        no_date64 = caller_packet()
        no_date64["monthly_caller_effect_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="date64_unavailable",
            current_date_storage_raw64=None)
        _, date_missing = query(no_date64)
        self.assertFalse(date_missing["conditional_supply_update_date_ready"])
        self.assertIsNone(date_missing["conditional_supply_update_date_raw64"])
        self.assertTrue(date_missing["conditional_byte_22_ready"])
        self.assertTrue(date_missing["war_counter_ready"])
        self.assertIn("current_date_storage_raw64", date_missing["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
