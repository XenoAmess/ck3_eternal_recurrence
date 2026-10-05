"""Offline source-arithmetic fixtures through the production strength consumer."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.army_loss_allocation_projection import (
    EligibleArmyRegiment,
    LossAllocationInputs,
    project_native_loss_requests,
    project_native_loss_sequence,
    project_observed_army_loss_requests,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP


def observed_army(*, supply=0, siege=2, raid=0):
    rows = []
    for regiment_id, current, tier in ((31, 0, 0), (41, 2, 0), (4, 1, 0), (7, 9, 2)):
        rows.append({
            "army_regiment_id": regiment_id,
            "current_soldiers": current, "maximum_soldiers": current, "scale": 1,
            "maa_type_status": "available", "maa_type_key": f"type_{tier}",
            "siege_tier_observable": True, "siege_tier": tier,
            "composition_unavailable_reason": None,
        })
    return {
        "status": "available", "army_id": 81, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 4,
        "current_soldiers": 12, "maximum_soldiers": 12,
        "ai_base_power_raw": 1, "ai_base_power_scale": 100000,
        "unavailable_reason": None, "regiment_strengths": rows,
        "loss_application_inputs_v1": {
            "status": "available", "unavailable_reason": None,
            "fraction_scale": 100000, "soldier_scale": 1,
            "raid_association_id": -1, "whole_soldiers": 12,
            "definition_le_zero_soldiers": 3, "supply_eligible_soldiers": 12,
            "definition_le_zero_supply_eligible_soldiers": 3,
            "current_supply_loss_budget": supply,
            "siege_loss_budget": siege, "raid_loss_budget": raid,
            "siege_rate_raw": 1000, "raid_rate_raw": 1000,
            "siege_active": siege > 0, "raid_active": raid > 0,
        },
    }


class OfflineStrengthService(GameplayBridgeService):
    """In-memory query responses only; no native endpoint or game process."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def snapshot(self):
        return {
            "paused": True, "revision": 2, "native_revision": 140,
            "snapshot_id": "offline-loss-fixture", "date_raw": 1,
            "player_armies": [{"army_id": 81}], "active_wars": [],
        }

    def capabilities(self):
        return {"action_steps": [QUERY_ARMY_STRENGTHS_STEP]}

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return {"status": "available", "army_strengths": self.rows}


class ArmyLossAllocationProjectionTests(unittest.TestCase):
    def test_production_query_preserves_order_and_zero_writer_request(self):
        army = observed_army()
        service = OfflineStrengthService([army])
        result = service.query_army_strengths([81], expected_revision=2)
        projection = result["loss_allocation_requests_v1"][0]
        requests = projection["passes"][2]["requests"]
        self.assertEqual([row["army_regiment_id"] for row in requests], [31, 41, 4])
        self.assertEqual([row["requested_soldiers"] for row in requests], [0, 1, 1])
        self.assertEqual([row["remaining_eligible_before"] for row in requests], [3, 3, 1])
        self.assertEqual([row["writer_quantity_raw"] for row in requests], [0, 100000, 100000])
        self.assertTrue(projection["writer_requests_ready"])
        self.assertFalse(projection["applied_loss_ready"])
        self.assertIsNone(projection["applied_soldier_loss"])
        self.assertEqual(result["army_strengths"][0], army)
        self.assertEqual(service.calls, [(QUERY_ARMY_STRENGTHS_STEP, 2)])

    def test_sequence_uses_actual_stage_inputs_and_only_preferred_overflow(self):
        inputs = lambda total, rows: LossAllocationInputs(
            total, tuple(EligibleArmyRegiment(*row) for row in rows)
        )
        projection = project_native_loss_sequence(
            supply_budget_soldiers=10, siege_budget_soldiers=1, raid_budget_soldiers=1,
            supply_preferred=inputs(4, [(10, 4)]),
            supply_residual=inputs(10, [(10, 0), (20, 10)]),
            post_supply_siege_raid_preferred=inputs(1, [(10, 1)]),
            post_preferred_siege_raid_residual=inputs(4, [(10, 0), (20, 4)]),
        )
        passes = projection["passes"]
        self.assertEqual([row["phase"] for row in passes], [
            "supply_preferred", "supply_residual", "siege_raid_preferred", "siege_raid_residual"
        ])
        self.assertEqual([row["request_budget_soldiers"] for row in passes], [10, 6, 2, 1])
        self.assertEqual([row["requested_soldiers"] for row in passes[1]["requests"]], [0, 6])
        self.assertEqual([row["requested_soldiers"] for row in passes[2]["requests"]], [1])
        self.assertEqual([row["requested_soldiers"] for row in passes[3]["requests"]], [0, 1])
        self.assertTrue(projection["writer_requests_ready"])
        self.assertIsNone(projection["applied_soldier_loss"])

    def test_positive_supply_does_not_guess_predicate_or_post_supply_current(self):
        projection = project_observed_army_loss_requests([observed_army(supply=2)])[0]
        self.assertEqual(projection["status"], "unavailable")
        self.assertEqual(projection["passes"], [])
        self.assertIn("per_regiment_native_2a956d0", projection["missing_inputs"])
        self.assertIn("post_supply_current_soldiers", projection["missing_inputs"])
        self.assertFalse(projection["writer_requests_ready"])
        self.assertIsNone(projection["applied_soldier_loss"])

    def test_readonly_overflow_cannot_reuse_preferred_snapshot_for_residual(self):
        projection = project_observed_army_loss_requests([observed_army(siege=5)])[0]
        self.assertEqual(projection["status"], "partial")
        self.assertEqual(len(projection["passes"]), 3)
        self.assertEqual(projection["passes"][2]["caller_overflow_residual_soldiers"], 2)
        self.assertEqual(projection["missing_inputs"], ["siege_raid_residual_stage_inputs"])
        self.assertFalse(projection["writer_requests_ready"])

    def test_native_imul_low32_and_signed_division_toward_zero(self):
        projection = project_native_loss_requests(
            request_budget_soldiers=50000, native_eligible_total_soldiers=100000,
            ordered_eligible_rows=[EligibleArmyRegiment(9, 50000), EligibleArmyRegiment(3, 50000)],
            phase="siege_raid_preferred",
        )
        requests = projection["requests"]
        self.assertEqual([row["multiply_signed32"] for row in requests], [-1794967296, -897517296])
        self.assertEqual([row["requested_soldiers"] for row in requests], [-17949, -17950])
        self.assertEqual(projection["remaining_request_budget_soldiers"], 85899)
        self.assertEqual(projection["caller_overflow_residual_soldiers"], 0)

    def test_unobservable_tier_does_not_select_by_unit_name(self):
        army = observed_army()
        army["regiment_strengths"][0]["siege_tier_observable"] = False
        army["regiment_strengths"][0]["siege_tier"] = None
        projection = project_observed_army_loss_requests([army])[0]
        self.assertEqual(projection["status"], "partial")
        self.assertEqual(projection["missing_inputs"], ["siege_raid_preferred_stage_inputs"])
        self.assertFalse(projection["writer_requests_ready"])


if __name__ == "__main__":
    unittest.main()
