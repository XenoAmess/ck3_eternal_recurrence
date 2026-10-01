"""Current authored-alternative reviews feed the bounded event planner."""
from __future__ import annotations

import copy
import unittest

from test_vanilla_event_registry_policy import (
    PLAYER, _context, _heir_death_context, _trait_gold_context,
)
from xar_autoplayer.vanilla_events.outcome import plan_registered_event_material_postcondition_v1
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


class CurrentBoundedCampaignUtilityTests(unittest.TestCase):
    def test_three_reviewed_utilities_feed_current_planner_without_live_claim(self):
        for key, constructor, native, count, direction, objective in (
            ("trait_specific.8001", _trait_gold_context, 1, 2, None,
             "increase_liquid_reserve_without_random_persistence"),
            ("tgp_travel_events.0030", _context, 1, 2, "decrease",
             "reduce_stress_without_delaying_travel"),
            ("death_management.1007", _heir_death_context, 0, 1, "increase",
             "acknowledge_unavoidable_heir_death_event"),
        ):
            with self.subTest(event=key):
                knowledge = query_vanilla_event_knowledge_v1(key, "1.20.0.3")
                profile = knowledge["analysis"]["selected_choice_campaign_utility_profile"]
                self.assertEqual(profile["objective_id"], objective)
                self.assertEqual(profile["selected_native_option_index"], native)
                self.assertIsNone(profile["cross_event_numeric_score"])
                self.assertEqual(profile["calibration_status"], "not_calibrated")
                self.assertEqual(profile["source_review"]["ck3_build"], "1.20.0.3")
                self.assertEqual(profile["source_review"]["readiness"], "static-ready")
                self.assertFalse(profile["source_review"]["live_acceptance_performed"])
                self.assertFalse(profile["source_review"]["legacy_profile_promoted_without_review"])
                self.assertFalse(knowledge["analysis"]["migration_1_20_0_3"]["new_live_evidence"])

                context = copy.deepcopy(constructor())
                selected = next(row for row in context["options"] if row["native_option_index"] == native)
                if direction:
                    selected["effect_indicators"] = {
                        "status": "available",
                        "coverage": "played-character-event-icon-indicators-1.20.0.3-v1",
                        "complete_effect_set": False,
                        "rows": [{"kind": "stress_and_fulfillment", "direction": direction,
                                  "secondary_direction": "decrease" if direction == "increase" else "increase",
                                  "magnitude": {"status": "unavailable"}, "affected_by_trait": True, "critical": False}],
                    }
                decision = recommend_registered_vanilla_event_option_v1(
                    context, played_character_id=PLAYER, snapshot_option_count=count, ck3_build="1.20.0.3",
                )
                self.assertEqual(decision["status"], "recommended")
                self.assertTrue(decision["campaign_utility_ready"])
                self.assertEqual(decision["campaign_utility_profile"]["objective_id"], objective)
                expectation = plan_registered_event_material_postcondition_v1(
                    decision, {"character_id": PLAYER, "stress_points": 34},
                    played_character_gold={"raw": 30_000_000, "scale": 100_000},
                    snapshot_id="current-utility-static-fixture:2", revision=2,
                )
                self.assertEqual(expectation["status"], "ready")
                self.assertTrue(expectation["material_change_required_for_evidence"])
                if direction:
                    # Restoring bounded utility must not manufacture a stress
                    # expectation when the current native facet is absent.
                    selected["effect_indicators"]["rows"] = []
                    no_facet = recommend_registered_vanilla_event_option_v1(
                        context, played_character_id=PLAYER, snapshot_option_count=count, ck3_build="1.20.0.3",
                    )
                    self.assertTrue(no_facet["campaign_utility_ready"])
                    self.assertIsNone(no_facet["choice_effect_profile"]["observable_postcondition"])
                historical = query_vanilla_event_knowledge_v1(key, "1.20.0.2")
                self.assertNotIn("selected_choice_campaign_utility_profile", historical["analysis"])


if __name__ == "__main__":
    unittest.main()
