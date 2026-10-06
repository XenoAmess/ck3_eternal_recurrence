"""One production query case for the new associated refill ADD/refresh stage."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP


def record(index, persistent, chunk, regiment, current, maximum, state, prepared):
    return {
        "status": "available", "unavailable_reason": None,
        "record_index": index, "persistent_regiment_id": persistent,
        "chunk_index": chunk, "chunk_army_regiment_id": regiment,
        "current_soldiers": current, "maximum_soldiers": maximum,
        "effective_current_soldiers": maximum if state == 3 and current == 0 else current,
        "state_raw": state, "native_can_replenish": False,
        "native_chunk_can_replenish": True,
        "persistent_monthly_replenishment_fraction_raw": 0,
        "persistent_prepared_replenishment_fraction_raw": prepared,
        "persistent_monthly_replenishment_fraction_scale": 100000,
        "persistent_prepared_replenishment_fraction_scale": 100000,
    }


def packet():
    first = [record(0, 130, 0, 30, 80, 100, 0, 10000),
             record(1, 130, 0, 30, 80, 100, 0, 10000),
             record(2, 130, 1, 30, 0, 100, 3, 10000),
             record(3, 130, 2, 30, 8, 9, 0, 10000)]
    first.extend(record(chunk + 1, 130, chunk, 30, 0, 0, 0, 10000)
                 for chunk in range(3, 7))
    data, strengths = [], []
    for regiment, current, maximum, skipped, records in (
        (30, 268, 309, False, first),
        (20, 1, 3, False, [record(0, 120, 0, 20, 1, 3, 0, 1 << 62)]),
        (10, 1, 1, True, [record(0, 110, 0, 10, 0, 2, 0, 0)]),
    ):
        strengths.append({
            "army_regiment_id": regiment, "current_soldiers": current,
            "maximum_soldiers": maximum, "scale": 1,
            "maa_type_status": "available", "maa_type_key": "tier_0",
            "siege_tier_observable": True, "siege_tier": 0,
            "composition_unavailable_reason": None,
            "native_supply_loss_eligible": True,
            "supply_loss_eligibility_unavailable_reason": None,
        })
        data.append({
            "army_regiment_id": regiment, "source": "native_all_data_records",
            "status": "available", "ready": True,
            "native_data_record_count": len(records), "unavailable_reason": None,
            "native_loss_writer_skipped": skipped,
            "loss_writer_admission_unavailable_reason": None, "records": records,
        })
    return {
        "status": "available", "army_id": 0, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 3,
        "current_soldiers": 270, "maximum_soldiers": 313,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
        "unavailable_reason": None, "regiment_strengths": strengths,
        "regiment_replenishment_records_v1": data,
        "loss_application_inputs_v1": {
            "status": "available", "unavailable_reason": None,
            "fraction_scale": 100000, "soldier_scale": 1,
            "raid_association_id": -1, "whole_soldiers": 270,
            "definition_le_zero_soldiers": 270, "supply_eligible_soldiers": 270,
            "definition_le_zero_supply_eligible_soldiers": 270,
            "current_supply_loss_budget": 0, "siege_loss_budget": 0,
            "raid_loss_budget": 0, "siege_rate_raw": 0, "raid_rate_raw": 0,
            "siege_active": False, "raid_active": False,
        },
    }


class MemoryStrengthService(GameplayBridgeService):
    def __init__(self, row):
        self.row = row

    def snapshot(self):
        return {"paused": True, "revision": 2, "native_revision": 3, "date_raw": 0,
                "player_armies": [{"army_id": 0}], "active_wars": []}

    def capabilities(self):
        return {"action_steps": [QUERY_ARMY_STRENGTHS_STEP]}

    def execute_step(self, step, *, expected_revision=None):
        return {"status": "available", "army_strengths": [self.row]}


class AssociatedRefillCurrentAssemblyTests(unittest.TestCase):
    def test_production_query_applies_one_physical_add_and_refreshes_aliases(self):
        source = packet()
        original = deepcopy(source)
        answer = MemoryStrengthService(source).query_army_strengths([0], expected_revision=2)
        allocation = answer["loss_allocation_requests_v1"][0]
        replay = allocation["same_input_conditional_associated_refill_current_v1"]
        self.assertEqual(replay["status"], "available")
        self.assertTrue(replay["associated_chunks_ready"])
        self.assertTrue(replay["associated_current_maximum_ready"])
        chunks = {(row["persistent_regiment_id"], row["chunk_index"]): row
                  for row in replay["physical_chunks"]}
        added = chunks[130, 0]
        self.assertEqual((added["same_input_q"], added["current_soldiers"],
                          added["physical_add_count"], len(added["data_occurrences"])),
                         (10, 90, 1, 2))
        self.assertEqual(chunks[130, 1]["current_soldiers"], 0)
        self.assertEqual((chunks[130, 2]["same_input_q"], chunks[130, 2]["physical_add_count"]), (0, 1))
        # 3*(2**62) wraps to−2**62; native trunc0 then low32 yields this
        # negative q. Dispatcher ADD preserves it without an extra zero clamp.
        self.assertEqual((chunks[120, 0]["same_input_q"], chunks[120, 0]["current_soldiers"]),
                         (-1796327121, -1796327120))
        self.assertEqual([row["current_soldiers"] for row in replay["conditional_regiment_strengths"]],
                         [288, -1796327120, 1])
        self.assertEqual([row["maximum_soldiers"] for row in replay["conditional_regiment_strengths"]],
                         [309, 3, 1])
        self.assertTrue(replay["persistent_core_coverage"][0]["all_seven_requests_observed"])
        self.assertFalse(replay["complete_persistent_requests_ready"])
        self.assertTrue(all(row["pair_clear_reachable"] is False for row in replay["physical_chunks"]))
        self.assertFalse(replay["actual_replenishment"])
        self.assertIsNone(replay["actual_post_stage_current"])
        self.assertFalse(replay["full_regular_refill_ready"])
        self.assertFalse(replay["full_monthly_ready"])
        self.assertFalse(allocation["applied_loss_ready"])
        self.assertEqual(source, original)
        self.assertEqual(answer["army_strengths"][0]["current_soldiers"], 270)

        legacy = deepcopy(source)
        legacy["regiment_replenishment_records_v1"][0]["records"][0].pop("chunk_army_regiment_id")
        partial = MemoryStrengthService(legacy).query_army_strengths([0])["loss_allocation_requests_v1"][0][
            "same_input_conditional_associated_refill_current_v1"]
        self.assertEqual(partial["status"], "partial")
        self.assertFalse(partial["associated_current_maximum_ready"])
        self.assertIsNone(partial["conditional_regiment_strengths"])
        self.assertTrue(partial["regiment_refreshes"][2]["current_maximum_ready"])

        independent = deepcopy(source)
        independent.pop("loss_application_inputs_v1")
        output = MemoryStrengthService(independent).query_army_strengths([0])["loss_allocation_requests_v1"][0]
        self.assertFalse(output["writer_requests_ready"])
        self.assertTrue(output["same_input_conditional_associated_refill_current_v1"]["associated_current_maximum_ready"])


if __name__ == "__main__":
    unittest.main()
