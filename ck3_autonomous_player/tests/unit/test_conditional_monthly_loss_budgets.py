"""One service-consumer case for source-bound post-updater caller budgets."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP


def monthly_budget_packet():
    return {
        "status": "available", "army_id": 0, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 1,
        "current_soldiers": 12, "maximum_soldiers": 12,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
        "unavailable_reason": None,
        "current_supply_raw": 1050000, "current_supply_scale": 100000,
        "current_supply_change_monthly_raw": -100000,
        "current_supply_change_monthly_scale": 100000,
        "current_supply_capacity_raw": 6000000, "current_supply_capacity_scale": 100000,
        "current_movement_progress": {
            "status": "not_applicable", "source": "native_current_route_edge",
            "unit_state_raw": 3, "accumulated_movement_weight_raw": None,
            "cached_edge_speed_raw": None, "normalized_edge_progress": None,
            "first_route_edge_remaining_duration": None, "unavailable_reason": None,
        },
        "army_update_clock_v1": {
            "status": "available", "ready": True, "unavailable_reason": None,
            "current_date_raw": 264, "native_day_index": 11,
            "selected_bucket_phase": 11, "observed_army_bucket_phase": 11,
            "last_supply_update_date_raw": 0, "last_supply_update_date_storage_raw64": 0,
            "grace_anchor_date_raw": 0, "grace_anchor_date_storage_raw64": 0,
            "loaded_grace_days": 10,
        },
        "monthly_loss_budget_inputs_v1": {
            "status": "available", "ready": True, "unavailable_reason": None,
            "scale": 100000, "unit_native_170_raw": 0,
            "native_unit_in_combat": False, "native_unit_gathering": False,
            "army_gathering_count_raw": 0,
            "loaded_supply_state_levels": [60, 10, 0],
            "loaded_supply_state_fractions_raw": [0, 0, 10000],
            "native_fleet_supply_loss_suppressed": False,
            "commander_valid": True, "commander_supply_modifier_id": 77,
            "commander_supply_modifier_raw": 0,
        },
        "regiment_strengths": [{
            "army_regiment_id": 10, "current_soldiers": 12,
            "maximum_soldiers": 12, "scale": 1,
            "maa_type_status": "available", "maa_type_key": "tier_0",
            "siege_tier_observable": True, "siege_tier": 0,
            "composition_unavailable_reason": None,
            "native_supply_loss_eligible": True,
            "supply_loss_eligibility_unavailable_reason": None,
        }],
        "regiment_replenishment_records_v1": [{
            "army_regiment_id": 10, "source": "native_all_data_records",
            "status": "available", "ready": True, "native_data_record_count": 1,
            "unavailable_reason": None, "native_loss_writer_skipped": False,
            "loss_writer_admission_unavailable_reason": None,
            "records": [{
                "status": "available", "unavailable_reason": None,
                "record_index": 0, "persistent_regiment_id": 110,
                "chunk_index": 0, "chunk_army_regiment_id": 10,
                "current_soldiers": 12, "maximum_soldiers": 12,
                "effective_current_soldiers": 12, "state_raw": 0,
                "native_can_replenish": False, "native_chunk_can_replenish": False,
                "persistent_monthly_replenishment_fraction_raw": 0,
                "persistent_prepared_replenishment_fraction_raw": 0,
                "persistent_monthly_replenishment_fraction_scale": 100000,
                "persistent_prepared_replenishment_fraction_scale": 100000,
            }],
        }],
        "loss_application_inputs_v1": {
            "status": "available", "unavailable_reason": None,
            "fraction_scale": 100000, "soldier_scale": 1,
            "raid_association_id": 0, "whole_soldiers": 12,
            "definition_le_zero_soldiers": 12, "supply_eligible_soldiers": 12,
            "definition_le_zero_supply_eligible_soldiers": 12,
            "current_supply_loss_budget": 0, "siege_loss_budget": 0,
            "raid_loss_budget": 0, "siege_rate_raw": 5000, "raid_rate_raw": 5000,
            "siege_active": True, "raid_active": True,
        },
    }


class MemoryStrengthService(GameplayBridgeService):
    def __init__(self, row):
        self.row, self.calls = row, 0

    def snapshot(self):
        return {"paused": True, "revision": 2, "native_revision": 3, "date_raw": 264,
                "player_armies": [{"army_id": 0}], "active_wars": []}

    def capabilities(self):
        return {"action_steps": [QUERY_ARMY_STRENGTHS_STEP]}

    def execute_step(self, step, *, expected_revision=None):
        self.calls += 1
        return {"status": "available", "army_strengths": [self.row]}


class ConditionalMonthlyLossBudgetsTests(unittest.TestCase):
    def test_query_distinguishes_current_budget_from_conditional_post_updater_budget(self):
        def query(packet):
            original = deepcopy(packet)
            service = MemoryStrengthService(packet)
            allocation = service.query_army_strengths([0], expected_revision=2)["loss_allocation_requests_v1"][0]
            projection = allocation["same_input_conditional_monthly_loss_budgets_v1"]
            self.assertEqual(packet, original)
            self.assertEqual(service.calls, 1)
            self.assertFalse(allocation["applied_loss_ready"])
            self.assertIsNone(allocation["applied_soldier_loss"])
            self.assertFalse(projection["actual_loss"])
            self.assertIsNone(projection["actual_post_stage_current"])
            self.assertFalse(projection["full_monthly_applied_loss_ready"])
            return allocation, projection

        packet = monthly_budget_packet()
        allocation, projection = query(packet)
        # Public D19140 state3 is not raw Unit+170=0. The whole -1 change
        # crosses a loaded threshold, while the actual readonly budget stays0.
        self.assertTrue(projection["supply_updater_admitted"])
        self.assertTrue(projection["conditional_budgets_ready"])
        self.assertEqual(projection["conditional_post_supply_raw"], 950000)
        self.assertEqual(projection["supply_state_index"], 2)
        self.assertEqual(projection["supply_effective_fraction_raw"], 10000)
        self.assertEqual(projection["supply_budget_soldiers"], 1)
        self.assertEqual(projection["current_readonly_supply_loss_budget"], 0)
        self.assertEqual(allocation["supply_budget_soldiers"], 0)
        self.assertEqual((projection["siege_budget_soldiers"], projection["raid_budget_soldiers"],
                          projection["combined_siege_raid_budget_soldiers"]), (0, 0, 0))
        # Combining the fractions first would incorrectly round 1.2 to1.
        self.assertEqual(12 * (5000 + 5000) // 100000, 1)
        old = allocation["same_input_conditional_loss_sequence_v1"]
        derived = projection["same_input_conditional_loss_sequence_v1"]
        self.assertEqual(old["conditional_final_current_soldiers"], 12)
        self.assertEqual(derived["conditional_final_current_soldiers"], 11)
        self.assertEqual(derived["input_basis"], "derived_budget_and_loss_subsystem")

        rejected = monthly_budget_packet()
        rejected["current_movement_progress"]["unit_state_raw"] = 0
        rejected["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="missing_later_inputs",
            unit_native_170_raw=3, loaded_supply_state_levels=None,
            loaded_supply_state_fractions_raw=None, commander_supply_modifier_raw=None)
        rejected["current_supply_change_monthly_raw"] = None
        _, no_update = query(rejected)
        self.assertFalse(no_update["supply_updater_admitted"])
        self.assertEqual(no_update["admission_rejection"], "unit_native_170_raw")
        self.assertEqual(no_update["supply_budget_soldiers"], 0)
        self.assertTrue(no_update["conditional_budgets_ready"])
        self.assertEqual(no_update["missing_inputs"], [])

        fleet = monthly_budget_packet()
        fleet["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="missing_later_inputs",
            native_fleet_supply_loss_suppressed=True, loaded_supply_state_levels=None,
            loaded_supply_state_fractions_raw=None, commander_supply_modifier_raw=None)
        _, suppressed = query(fleet)
        self.assertTrue(suppressed["supply_updater_admitted"])
        self.assertEqual(suppressed["supply_budget_soldiers"], 0)
        self.assertTrue(suppressed["conditional_budgets_ready"])

        no_commander = monthly_budget_packet()
        no_commander["monthly_loss_budget_inputs_v1"].update(
            commander_valid=False, commander_supply_modifier_id=None,
            commander_supply_modifier_raw=None, loaded_supply_state_fractions_raw=[0, 0, 150000])
        _, unclamped = query(no_commander)
        self.assertEqual(unclamped["supply_effective_fraction_raw"], 150000)
        self.assertEqual(unclamped["supply_budget_soldiers"], 12)

        for date in (239, 240):
            boundary = monthly_budget_packet()
            boundary["army_update_clock_v1"]["current_date_raw"] = date
            _, at_grace = query(boundary)
            self.assertFalse(at_grace["supply_updater_admitted"])
            self.assertEqual(at_grace["admission_rejection"], "native_grace_strict_greater")
            self.assertEqual(at_grace["conditional_post_supply_raw"], 1050000)

        partial = monthly_budget_packet()
        partial["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="raw_unit_unavailable",
            unit_native_170_raw=None)
        _, unknown = query(partial)
        self.assertIsNone(unknown["supply_updater_admitted"])
        self.assertFalse(unknown["supply_budget_ready"])
        self.assertTrue(unknown["siege_budget_ready"])
        self.assertTrue(unknown["raid_budget_ready"])
        self.assertEqual(unknown["missing_inputs"], ["unit_native_170_raw"])

        empty_levels = monthly_budget_packet()
        empty_levels["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="unneeded_fraction_vector",
            loaded_supply_state_levels=[], loaded_supply_state_fractions_raw=None,
            commander_supply_modifier_raw=None)
        _, zero = query(empty_levels)
        self.assertEqual(zero["supply_state_index"], -1)
        self.assertEqual(zero["supply_budget_soldiers"], 0)
        self.assertTrue(zero["conditional_budgets_ready"])

        half = monthly_budget_packet()
        half["monthly_loss_budget_inputs_v1"]["commander_supply_modifier_raw"] = -50000
        _, modified = query(half)
        self.assertEqual(modified["supply_effective_fraction_raw"], 5000)
        self.assertEqual(modified["supply_budget_soldiers"], 0)

        slow = monthly_budget_packet()
        slow["monthly_loss_budget_inputs_v1"].update(
            loaded_supply_state_fractions_raw=[0, 0, (1 << 63) - 1],
            commander_supply_modifier_raw=-99998)
        _, high_quotient = query(slow)
        #24E5114 uses high/Q: q*2=184467440737094, remainder
        # contribution1, then clamp100000. Dividing low=2 first would
        # wrap the product to-2 and incorrectly produce component0.
        self.assertEqual(high_quotient["supply_effective_fraction_raw"], 100000)
        self.assertEqual(high_quotient["supply_budget_soldiers"], 12)


if __name__ == "__main__":
    unittest.main()
