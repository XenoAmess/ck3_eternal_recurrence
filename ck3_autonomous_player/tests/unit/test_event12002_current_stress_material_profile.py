"""Current native stress facets feed the real production material planner."""
from __future__ import annotations

import copy
import unittest

from test_vanilla_event_registry_policy import PLAYER, _context, _heir_death_context
from xar_autoplayer.vanilla_events.outcome import plan_registered_event_material_postcondition_v1
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


class CurrentStressMaterialProfileTests(unittest.TestCase):
    def test_current_native_stress_profiles_feed_material_planner(self):
        for key, constructor, native, direction, relation, count in (
            ("death_management.1007", _heir_death_context, 0, "increase", "non_decreasing", 1),
            ("tgp_travel_events.0030", _context, 1, "decrease", "non_increasing", 2),
        ):
            knowledge = query_vanilla_event_knowledge_v1(key, "1.20.0.2")
            # The source-only profile remains conditional. Current native
            # evidence, rather than an unconditional authored forecast, binds
            # the material expectation returned by the production policy.
            self.assertIsNone(knowledge["analysis"]["selected_choice_effect_profile"]["observable_postcondition"])
            for kind in ("stress", "stress_and_fulfillment", None):
                with self.subTest(event=key, native_indicator=kind):
                    context = copy.deepcopy(constructor())
                    context["provenance"] = {"backend_id": "ck3-1.20.0.2-msvc-x64"}
                    selected = next(row for row in context["options"] if row["native_option_index"] == native)
                    selected["effect_indicators"] = {
                        "status": "available",
                        "coverage": "played-character-event-icon-indicators-1.20.0.2-v1",
                        "complete_effect_set": False,
                        "rows": [] if kind is None else [{"kind": kind, "direction": direction,
                            "secondary_direction": "decrease" if direction == "increase" else "increase",
                            "magnitude": {"status": "unavailable"}, "affected_by_trait": True, "critical": False}],
                    }
                    decision = recommend_registered_vanilla_event_option_v1(context, played_character_id=PLAYER,
                                snapshot_option_count=count, ck3_build="1.20.0.2")
                    self.assertEqual(decision["status"], "recommended")
                    expectation = plan_registered_event_material_postcondition_v1(
                        decision, {"character_id": PLAYER, "stress_points": 34},
                        snapshot_id="current-native-profile-fixture:2", revision=2,
                    )
                    if kind is None:
                        self.assertIsNone(expectation)
                    else:
                        self.assertEqual(expectation["status"], "ready")
                        self.assertEqual(expectation["metric"], "played_character.stress_points")
                        self.assertEqual(expectation["expected_relation"], relation)
                        self.assertTrue(expectation["material_change_required_for_evidence"])
                        self.assertFalse(decision["choice_effect_profile"]["complete_effect_set"])


if __name__ == "__main__":
    unittest.main()
