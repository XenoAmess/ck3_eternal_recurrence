"""One new offline authority/consumer case for the positive-supply branch."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.army_loss_allocation_projection import project_observed_army_loss_requests
from xar_autoplayer.bridge.war_contract import normalize_army_strengths


class SupplyLossEligibilityConsumerTests(unittest.TestCase):
    def test_positive_supply_preserves_native_false_and_only_unlocks_preferred_requests(self):
        rows = []
        for regiment_id, current, tier, eligible in (
            (30, 0, 0, True), (10, 2, 0, True), (20, 5, 0, False), (40, 5, 2, True)
        ):
            rows.append({
                "army_regiment_id": regiment_id, "current_soldiers": current,
                "maximum_soldiers": current, "scale": 1,
                "maa_type_status": "available", "maa_type_key": f"type_{tier}",
                "siege_tier_observable": True, "siege_tier": tier,
                "composition_unavailable_reason": None,
                "native_supply_loss_eligible": eligible,
                "supply_loss_eligibility_unavailable_reason": None,
            })
        army = {
            "status": "available", "army_id": 0, "native_carmy_id": 0,
            "scope_role": "player", "war_ids": [], "regiment_count": 4,
            "current_soldiers": 12, "maximum_soldiers": 12,
            "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
            "unavailable_reason": None, "regiment_strengths": rows,
            "loss_application_inputs_v1": {
                "status": "available", "unavailable_reason": None,
                "fraction_scale": 100000, "soldier_scale": 1,
                "raid_association_id": -1, "whole_soldiers": 12,
                "definition_le_zero_soldiers": 7, "supply_eligible_soldiers": 7,
                "definition_le_zero_supply_eligible_soldiers": 2,
                "current_supply_loss_budget": 2, "siege_loss_budget": 1,
                "raid_loss_budget": 0, "siege_rate_raw": 1000, "raid_rate_raw": 1000,
                "siege_active": True, "raid_active": False,
            },
        }
        scope = [{"army_id": 0, "scope_role": "player", "war_ids": []}]

        def consume():
            normalized = normalize_army_strengths([army], expected_scope=scope)
            return normalized[0], project_observed_army_loss_requests(normalized)[0]

        normalized, projection = consume()
        self.assertIs(normalized["regiment_strengths"][2]["native_supply_loss_eligible"], False)
        self.assertEqual([row["phase"] for row in projection["passes"]], ["supply_preferred", "supply_residual"])
        requests = projection["passes"][0]["requests"]
        self.assertEqual([row["army_regiment_id"] for row in requests], [30, 10])
        self.assertEqual([row["requested_soldiers"] for row in requests], [0, 2])
        self.assertEqual(projection["status"], "partial")
        self.assertIn("post_supply_current_soldiers", projection["missing_inputs"])
        self.assertNotIn("per_regiment_native_2a956d0", projection["missing_inputs"])
        self.assertFalse(projection["applied_loss_ready"])
        self.assertIsNone(projection["applied_soldier_loss"])

        rows[2]["native_supply_loss_eligible"] = None
        rows[2]["supply_loss_eligibility_unavailable_reason"] = "supply_loss_eligibility_not_bound"
        normalized, projection = consume()
        self.assertIsNone(normalized["regiment_strengths"][2]["native_supply_loss_eligible"])
        self.assertEqual(projection["passes"], [])
        self.assertIn("per_regiment_native_2a956d0", projection["missing_inputs"])

        for row in rows:
            del row["native_supply_loss_eligible"]
            del row["supply_loss_eligibility_unavailable_reason"]
        normalized, projection = consume()
        self.assertNotIn("native_supply_loss_eligible", normalized["regiment_strengths"][0])
        self.assertEqual(projection["status"], "unavailable")
        self.assertEqual(projection["passes"], [])


if __name__ == "__main__":
    unittest.main()
