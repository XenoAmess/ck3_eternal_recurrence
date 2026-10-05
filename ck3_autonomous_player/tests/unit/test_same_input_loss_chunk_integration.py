"""New C+D integration case: conditional initial preferred DATA only."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP


def army_inputs(supply_budget, second_tier=0):
    strengths, data_rows = [], []
    for regiment_id, current, tier, skipped in ((30, 2, 0, False), (10, 4, second_tier, True)):
        strengths.append({
            "army_regiment_id": regiment_id, "current_soldiers": current,
            "maximum_soldiers": current, "scale": 1,
            "maa_type_status": "available", "maa_type_key": f"type_{tier}",
            "siege_tier_observable": True, "siege_tier": tier,
            "composition_unavailable_reason": None,
            "native_supply_loss_eligible": True,
            "supply_loss_eligibility_unavailable_reason": None,
        })
        data_rows.append({
            "army_regiment_id": regiment_id, "source": "native_all_data_records",
            "status": "available", "ready": True, "native_data_record_count": 1,
            "unavailable_reason": None, "native_loss_writer_skipped": skipped,
            "loss_writer_admission_unavailable_reason": None,
            "records": [{
                "status": "available", "unavailable_reason": None,
                "record_index": 0, "persistent_regiment_id": 100 + regiment_id,
                "chunk_index": 0, "chunk_army_regiment_id": regiment_id,
                "current_soldiers": current, "maximum_soldiers": current,
                "effective_current_soldiers": current, "state_raw": 0,
                "native_can_replenish": False, "native_chunk_can_replenish": False,
                "persistent_monthly_replenishment_fraction_raw": 0,
                "persistent_prepared_replenishment_fraction_raw": 0,
                "persistent_monthly_replenishment_fraction_scale": 100000,
                "persistent_prepared_replenishment_fraction_scale": 100000,
            }],
        })
    preferred_total = 6 if second_tier <= 0 else 2
    return {
        "status": "available", "army_id": 0, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 2,
        "current_soldiers": 6, "maximum_soldiers": 6,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
        "unavailable_reason": None, "regiment_strengths": strengths,
        "regiment_replenishment_records_v1": data_rows,
        "loss_application_inputs_v1": {
            "status": "available", "unavailable_reason": None,
            "fraction_scale": 100000, "soldier_scale": 1,
            "raid_association_id": -1, "whole_soldiers": 6,
            "definition_le_zero_soldiers": preferred_total, "supply_eligible_soldiers": 6,
            "definition_le_zero_supply_eligible_soldiers": preferred_total,
            "current_supply_loss_budget": supply_budget,
            "siege_loss_budget": 3, "raid_loss_budget": 0,
            "siege_rate_raw": 1000, "raid_rate_raw": 1000,
            "siege_active": True, "raid_active": False,
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


class SameInputLossChunkIntegrationTests(unittest.TestCase):
    def test_registered_strength_consumer_projects_only_initial_preferred_frame(self):
        for supply_budget in (3, 0):
            with self.subTest(supply_budget=supply_budget):
                service = MemoryStrengthService(army_inputs(supply_budget))
                result = service.query_army_strengths([0], expected_revision=2)
                allocation = result["loss_allocation_requests_v1"][0]
                conditional = allocation["same_input_conditional_chunk_writeback_v1"]
                self.assertEqual(conditional["phase"], "supply_preferred" if supply_budget else "siege_raid_preferred")
                self.assertTrue(conditional["same_input_chunk_writeback_ready"])
                self.assertEqual([row["army_regiment_id"] for row in conditional["requests"]], [30, 10])
                self.assertEqual(conditional["requests"][0]["physical_current_delta"], -1)
                self.assertEqual(conditional["requests"][0]["physical_chunks_after"][0]["current_soldiers"], 1)
                self.assertTrue(conditional["requests"][1]["writer_skipped"])
                self.assertEqual(conditional["requests"][1]["physical_current_delta"], 0)
                self.assertFalse(conditional["actual_loss"])
                self.assertIsNone(conditional["actual_post_stage_current"])
                self.assertFalse(allocation["applied_loss_ready"])
                self.assertIsNone(allocation["applied_soldier_loss"])
                self.assertEqual(service.calls, 1)
                if supply_budget:
                    self.assertIn("post_supply_current_soldiers", allocation["missing_inputs"])
                    self.assertFalse(allocation["writer_requests_ready"])
                    self.assertNotIn("siege_raid_preferred", [row["phase"] for row in allocation["passes"]])

        allocation = MemoryStrengthService(army_inputs(0, second_tier=2)).query_army_strengths([0])["loss_allocation_requests_v1"][0]
        conditional = allocation["same_input_conditional_chunk_writeback_v1"]
        self.assertEqual([row["army_regiment_id"] for row in conditional["requests"]], [30])
        self.assertEqual(conditional["requests"][0]["physical_current_delta"], -2)
        self.assertIn("siege_raid_residual_stage_inputs", allocation["missing_inputs"])
        self.assertNotIn("siege_raid_residual", [row["phase"] for row in allocation["passes"]])
        self.assertTrue(conditional["same_input_chunk_writeback_ready"])
        self.assertFalse(allocation["writer_requests_ready"])


if __name__ == "__main__":
    unittest.main()
