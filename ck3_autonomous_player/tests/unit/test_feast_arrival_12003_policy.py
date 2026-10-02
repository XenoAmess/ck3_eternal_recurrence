"""The actual feast.7002 scope shape through the existing production pipeline."""

from __future__ import annotations

import unittest

from test_event_window_context_v1_bridge import _frame, _scope
from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.outcome import (
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


class FeastArrival12003PolicyTests(unittest.TestCase):
    def test_sole_host_choice_uses_actual_prestige_observations(self) -> None:
        player = 31853
        context = _frame()
        context.update({
            "event_definition_key": "feast.7002",
            "snapshot_revision": 23, "date_raw": 53328600,
            "current_event_instance_id": 14,
            "root_scope": _scope(character_id=player),
            "saved_scopes": [
                {"name": "activity", "name_identifier": 1,
                 "scope": _scope(raw_type_index=3, type_key="activity", character_id=None)},
                {"name": "host", "name_identifier": 2, "scope": _scope(character_id=player)},
                {"name": "province", "name_identifier": 3,
                 "scope": _scope(raw_type_index=8, type_key="province", character_id=None)},
            ],
            "provenance": {
                "root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC408",
                "manager_offset": "+0x28", "backend_id": "ck3-1.20.0.3-native-event-window-v1",
            },
        })
        option = context["options"][0]
        option.update({
            "native_option_index": 0, "shown": True, "enabled": True,
            "fallback": False, "cancel": False,
            "resolved_name": "We have a lovely time ahead of us!", "unavailable_reason": "",
        })
        option["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.3-v1"
        option["effect_indicators"]["rows"] = []
        context = normalize_current_event_window_context_v1(
            context, expected_event_instance_id=14, expected_date_raw=53328600,
            expected_snapshot_revision=23,
        )
        for build in ("1.19.0.6", "1.20.0.2"):
            self.assertEqual(query_vanilla_event_knowledge_v1("feast.7002", build)["status"], "unavailable")
        knowledge = query_vanilla_event_knowledge_v1("feast.7002", "1.20.0.3")
        self.assertEqual(knowledge["status"], "available")
        self.assertFalse(knowledge["analysis"]["new_live_evidence"])
        snapshot = {
            "snapshot_id": "native:23", "revision": 2, "native_revision": 23,
            "date_raw": 53328600, "paused": True, "backend_id": "native-headless",
            "played_character": {"character_id": player, "alive": True},
            "played_character_prestige": {"raw": 42_000_000, "scale": 100_000},
            "active_event": {"instance_id": 14, "option_count": 1},
        }
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "accepted": True,
                "status": "available", "snapshot_revision": 23,
                "current_event_instance_id": 14, "date_raw": 53328600,
                "current_event_window_context": context,
                "queried_snapshot_id": "native:23", "queried_revision": 2,
                "queried_native_revision": 23,
            },
        }]
        plan = choose_one_life_turn(
            history, snapshot=snapshot,
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "select-event-option-1"},
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 0)
        self.assertTrue(plan["event_decision"]["checks"]["scope:host:character_id"])
        self.assertEqual(plan["event_campaign_utility"]["comparison_kind"], "sole_legal_route")
        expectation = plan["event_material_postcondition"]
        self.assertEqual(expectation["status"], "ready")
        self.assertEqual(expectation["metric"], "played_character_prestige.raw")
        self.assertEqual(expectation["expected_relation"], "strictly_increasing")
        selection = {
            "postcondition_verified": True,
            "starting_snapshot_id": "native:23", "starting_revision": 2,
            "ending_snapshot_id": "native:24", "ending_revision": 3,
            "starting_played_character_prestige": {
                "status": "available", "character_id": player, "prestige_raw": 42_000_000, "scale": 100_000,
            },
            "ending_played_character_prestige": {
                "status": "available", "character_id": player, "prestige_raw": 45_500_000, "scale": 100_000,
            },
        }
        material = evaluate_registered_event_material_postcondition_v1(expectation, selection)
        self.assertEqual(material["status"], "verified_change")
        self.assertEqual(material["delta"], 3_500_000)
        selection["ending_played_character_prestige"]["prestige_raw"] = 42_000_000
        no_change = evaluate_registered_event_material_postcondition_v1(expectation, selection)
        self.assertEqual(no_change["status"], "failed")
        self.assertEqual(no_change["unavailable_reason"], "prestige_not_increased")
        old_decision = {**plan["event_decision"], "ck3_build": "1.20.0.2"}
        self.assertIsNone(plan_registered_event_material_postcondition_v1(
            old_decision, snapshot["played_character"],
            played_character_prestige=snapshot["played_character_prestige"],
            snapshot_id="native:23", revision=2,
        ))


if __name__ == "__main__":
    unittest.main()
