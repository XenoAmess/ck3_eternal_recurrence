from __future__ import annotations

from copy import deepcopy
import unittest

from test_faction_demand1001_context import _frames
from xar_autoplayer.vanilla_events.faction_demand1001_ordinary import (
    plan_faction_demand1001_ordinary_v1,
)
from xar_autoplayer.bridge.player_faction_alerts_contract import QUERY_PLAYER_FACTION_ALERTS_V1_STEP


class OrdinaryPopulistAdapterTests(unittest.TestCase):
    def test_known_projection_query_compare_bound_choice_and_stale_choice(self):
        # Reuse only the known seven-role/native2,3 fixture; no old suite run.
        event, alerts = _frames()
        event["snapshot_revision"] = 66
        snapshot = {
            "snapshot_id": "native:66", "revision": 7, "native_revision": 66,
            "date_raw": event["date_raw"], "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True},
            "active_event": {"instance_id": 23, "option_count": 4},
            "episode_run_id": "fixture-episode", "diagnostics": {"connection_generation": 2},
            "active_wars": [], "played_character_gold": {"raw": 106140557, "scale": 100000},
        }
        steps = {QUERY_PLAYER_FACTION_ALERTS_V1_STEP, "select-event-option-3", "select-event-option-4"}
        kwargs = {"war_entry_assessments": {}, "action_steps": steps}
        query = plan_faction_demand1001_ordinary_v1(event, snapshot, faction_alerts=None, **kwargs)
        self.assertEqual(query["selected_step"], QUERY_PLAYER_FACTION_ALERTS_V1_STEP)
        plan = plan_faction_demand1001_ordinary_v1(event, snapshot, faction_alerts=alerts, **kwargs)
        decision = plan["event_decision"]
        self.assertEqual(decision["status"], "comparison_required")
        self.assertEqual(decision["binding"]["faction_snapshot_revision"], 65)
        self.assertEqual(decision["binding"]["event_snapshot_revision"], 66)
        self.assertEqual([row["api_option_number"] for row in decision["candidates"]], [3, 4])
        self.assertEqual(decision["candidates"][0]["effects"]["player_direct_county_and_duchy_loss_ids"], [102, 201])
        self.assertEqual(decision["candidates"][1]["effects"]["target_title_id"], 301)
        self.assertIsNone(decision["value_inputs"]["strategic_power_assessment"])
        self.assertFalse(decision["value_inputs"]["executable_force_coverage_ready"])
        self.assertIsNone(plan["selected_step"])
        selection = {"binding": deepcopy(decision["binding"]), "selected_native_option_index": 3,
                     "policy": "fixture-owned-ordinary-war-policy", "reason": "fixture explicit territorial defense"}
        chosen = plan_faction_demand1001_ordinary_v1(event, snapshot, faction_alerts=alerts,
                                                   selection=selection, **kwargs)
        self.assertEqual(chosen["selected_step"], "select-event-option-4")
        self.assertEqual(chosen["faction_demand_postcondition"]["kind"], "new_faction_defensive_war")
        self.assertFalse(chosen["faction_demand_postcondition"]["verification_ready"])
        self.assertFalse(chosen["event_decision"]["semantic_optimal"])
        changed = deepcopy(selection)
        changed["binding"]["connection_generation"] += 1
        rejected = plan_faction_demand1001_ordinary_v1(event, snapshot, faction_alerts=alerts,
                                                     selection=changed, **kwargs)
        self.assertIsNone(rejected["selected_step"])
        self.assertEqual(rejected["event_decision"]["unavailable_reason"], "ordinary_strategy_selection_binding_invalid")
        selection["selected_native_option_index"] = 2
        incomplete = plan_faction_demand1001_ordinary_v1(event, snapshot, faction_alerts=alerts,
                                                       selection=selection, **kwargs)
        self.assertIsNone(incomplete["selected_step"])
        self.assertEqual(incomplete["event_decision"]["unavailable_reason"], "complete_acceptance_outcome_required")


if __name__ == "__main__":
    unittest.main()
