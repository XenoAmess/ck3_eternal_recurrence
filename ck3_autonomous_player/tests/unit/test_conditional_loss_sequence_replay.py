"""One new production-consumer case spanning all four derived loss stages."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP


def full_stage_packet():
    strengths, data = [], []
    # Stored order30,40,10,20: physical alias, state3 refresh-only, skipped,
    # then a positive-tier row reachable through each residual pass.
    for regiment, current, maximum, tier, eligible, skipped, physical, state, aliases in (
        (30, 4, 4, 0, True, False, 2, 0, 2),
        (40, 0, 3, 0, False, False, 0, 3, 1),
        (10, 2, 2, 0, True, True, 2, 0, 1),
        (20, 6, 6, 2, True, False, 6, 0, 1),
    ):
        strengths.append({
            "army_regiment_id": regiment, "current_soldiers": current,
            "maximum_soldiers": maximum, "scale": 1,
            "maa_type_status": "available", "maa_type_key": f"tier_{tier}",
            "siege_tier_observable": True, "siege_tier": tier,
            "composition_unavailable_reason": None,
            "native_supply_loss_eligible": eligible,
            "supply_loss_eligibility_unavailable_reason": None,
        })
        records = [{
            "status": "available", "unavailable_reason": None,
            "record_index": index, "persistent_regiment_id": 100 + regiment,
            "chunk_index": 0, "chunk_army_regiment_id": regiment,
            "current_soldiers": physical, "maximum_soldiers": maximum // aliases,
            "effective_current_soldiers": maximum if state == 3 and physical == 0 else physical,
            "state_raw": state, "native_can_replenish": False,
            "native_chunk_can_replenish": False,
            "persistent_monthly_replenishment_fraction_raw": 0,
            "persistent_prepared_replenishment_fraction_raw": 0,
            "persistent_monthly_replenishment_fraction_scale": 100000,
            "persistent_prepared_replenishment_fraction_scale": 100000,
        } for index in range(aliases)]
        data.append({
            "army_regiment_id": regiment, "source": "native_all_data_records",
            "status": "available", "ready": True, "native_data_record_count": aliases,
            "unavailable_reason": None, "native_loss_writer_skipped": skipped,
            "loss_writer_admission_unavailable_reason": None, "records": records,
        })
    return {
        "status": "available", "army_id": 0, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 4,
        "current_soldiers": 12, "maximum_soldiers": 15,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
        "unavailable_reason": None, "regiment_strengths": strengths,
        "regiment_replenishment_records_v1": data,
        "loss_application_inputs_v1": {
            "status": "available", "unavailable_reason": None,
            "fraction_scale": 100000, "soldier_scale": 1,
            "raid_association_id": 0, "whole_soldiers": 12,
            "definition_le_zero_soldiers": 6, "supply_eligible_soldiers": 12,
            "definition_le_zero_supply_eligible_soldiers": 6,
            "current_supply_loss_budget": 8, "siege_loss_budget": 5,
            "raid_loss_budget": 2, "siege_rate_raw": 1000, "raid_rate_raw": 1000,
            "siege_active": True, "raid_active": True,
        },
    }


class MemoryStrengthService(GameplayBridgeService):
    def __init__(self, row):
        self.row = row
        self.calls = 0

    def snapshot(self):
        return {"paused": True, "revision": 2, "native_revision": 3, "date_raw": 0,
                "player_armies": [{"army_id": 0}], "active_wars": []}

    def capabilities(self):
        return {"action_steps": [QUERY_ARMY_STRENGTHS_STEP]}

    def execute_step(self, step, *, expected_revision=None):
        self.calls += 1
        return {"status": "available", "army_strengths": [self.row]}


class ConditionalLossSequenceReplayTests(unittest.TestCase):
    def test_query_interleaves_all_four_passes_without_claiming_actual_stage(self):
        packet = full_stage_packet()
        original = deepcopy(packet)
        service = MemoryStrengthService(packet)
        answer = service.query_army_strengths([0], expected_revision=2)
        allocation = answer["loss_allocation_requests_v1"][0]
        replay = allocation["same_input_conditional_loss_sequence_v1"]
        self.assertTrue(replay["conditional_sequence_ready"])
        self.assertEqual([row["phase"] for row in replay["passes"]], [
            "supply_preferred", "supply_residual", "siege_raid_preferred", "siege_raid_residual"])
        self.assertEqual([row["native_filter_flags"] for row in replay["passes"]], [3, 2, 1, 0])
        self.assertEqual([row["native_eligible_total_soldiers"] for row in replay["passes"]], [6, 8, 2, 9])
        self.assertEqual([row["request_budget_soldiers"] for row in replay["passes"]], [8, 2, 7, 5])
        self.assertEqual([[row["requested_soldiers"] for row in stage["requests"]]
                          for stage in replay["passes"]], [[4, 2], [0, 0, 2], [0, 0, 2], [0, 1, 1, 3]])
        # Alias current changes−4 despite a unique physical debit−2. Next
        # pass must use refreshed0, not4−requested4 for other record domains.
        first = replay["passes"][0]["requests"][0]["conditional_chunk_writeback"]
        self.assertEqual(first["physical_current_delta"], -2)
        self.assertEqual(first["conditional_raised_regiment_refresh"]["current_soldiers"], 0)
        # A selected zero-parent row refreshes state3 current0 to3 in siege
        # preferred; it remains3 after residual's transient−1 is restored0.
        zero = replay["passes"][2]["requests"][1]
        self.assertEqual(zero["current_soldiers_read"], 0)
        self.assertEqual(zero["requested_soldiers"], 0)
        self.assertEqual(zero["conditional_chunk_writeback"]["conditional_raised_regiment_refresh"]["current_soldiers"], 3)
        residual_zero = replay["passes"][3]["requests"][1]["conditional_chunk_writeback"]
        self.assertEqual([row["current_after"] for row in residual_zero["writes"]], [-1, 0])
        self.assertEqual([row["current_soldiers"] for row in replay["conditional_final_regiment_strengths"]], [0, 3, 2, 1])
        self.assertEqual(replay["conditional_final_current_soldiers"], 6)
        self.assertEqual(replay["conditional_physical_current_delta"], -7)
        self.assertTrue(replay["conditional_physical_chunks_ready"])
        self.assertEqual(len(replay["conditional_physical_chunks_after"]), 4)
        self.assertEqual(packet, original)
        self.assertEqual(service.calls, 1)
        self.assertFalse(replay["actual_loss"])
        self.assertIsNone(replay["actual_post_stage_current"])
        self.assertFalse(allocation["applied_loss_ready"])
        self.assertIsNone(allocation["applied_soldier_loss"])
        self.assertIn("post_supply_current_soldiers", allocation["missing_inputs"])

        # A legacy absent admission is incomplete, not false/ordinary. The
        # derived remainder is withheld instead of recycling initial DATA.
        legacy = full_stage_packet()
        legacy["regiment_replenishment_records_v1"][0].pop("native_loss_writer_skipped")
        legacy["regiment_replenishment_records_v1"][0].pop("loss_writer_admission_unavailable_reason")
        unavailable = MemoryStrengthService(legacy).query_army_strengths([0])["loss_allocation_requests_v1"][0]
        partial = unavailable["same_input_conditional_loss_sequence_v1"]
        self.assertFalse(partial["conditional_sequence_ready"])
        self.assertIsNone(partial["conditional_final_regiment_strengths"])
        self.assertEqual(partial["missing_inputs"][0]["inputs"], ["native_loss_writer_skipped"])
        self.assertFalse(partial["actual_loss"])
        self.assertIsNone(partial["actual_post_stage_current"])


if __name__ == "__main__":
    unittest.main()
