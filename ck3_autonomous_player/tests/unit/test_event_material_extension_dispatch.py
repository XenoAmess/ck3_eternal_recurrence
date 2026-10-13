"""New registry-to-leaf seams; existing M2 qualification cases stay untouched."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from test_bookmark1070_material import material_case, snapshot
from test_feast_brawl_utility_context import _character, _inputs
from xar_autoplayer.vanilla_events.outcome import (
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


class EventMaterialExtensionDispatchTests(unittest.TestCase):
    def test_registry_bookmark_profile_dispatches_actual_new_army_leaf(self):
        knowledge = query_vanilla_event_knowledge_v1("bookmark.1070", "1.20.0.4")
        decision = {
            "status": "recommended", "event_definition_key": "bookmark.1070",
            "ck3_build": "1.20.0.4", "selected_native_option_index": 2,
            "selected_option_number": 3,
            "choice_effect_profile": knowledge["analysis"]["selected_choice_effect_profile"],
        }
        before = snapshot()
        expected = plan_registered_event_material_postcondition_v1(
            decision, before["played_character"], snapshot=before,
            snapshot_id=before["snapshot_id"], revision=before["revision"],
            native_revision=before["native_revision"], date_raw=before["date_raw"],
        )
        self.assertEqual(expected["status"], "ready")
        _, selection = material_case()
        result = evaluate_registered_event_material_postcondition_v1(expected, selection)
        self.assertEqual(result["status"], "verified_change")
        self.assertEqual(result["observed_current_soldiers"], 250)
        self.assertFalse(result["levy_type_identity_observed"])

    def test_registered_feast_policy_forwards_current_opinions_and_effects(self):
        event, _, reads = _inputs((12, 100), fighter_ids=(77701, 77702))
        event.update(schema="current-event-window-context-v1", schema_version=1,
                     status="available", window_match_count=1)
        event["saved_scopes"].extend([
            {"name": "activity", "scope": {"status": "available", "type_key": "activity"}},
            {"name": "host", "scope": _character(29829)},
            {"name": "province", "scope": {"status": "available", "type_key": "province"}},
        ])
        for option in event["options"]:
            option.update(fallback=False, cancel=False)
        selected = recommend_registered_vanilla_event_option_v1(
            event, played_character_id=29829, snapshot_option_count=3,
            ck3_build="1.20.0.4", event_opinion_observations=reads,
        )
        self.assertEqual(selected["status"], "recommended", selected.get("failed_checks"))
        self.assertEqual(selected["selected_native_option_index"], 0)
        self.assertEqual(selected["choice_effect_profile"]["selected_native_option_index"], 0)
        self.assertEqual(selected["campaign_utility_profile"]["selected_native_option_index"], 0)
        self.assertEqual(selected["feast_brawl_decision_context"]["comparison_status"],
                         "current_inputs_compared")
        self.assertFalse(selected["semantic_optimal"])
        fallback = recommend_registered_vanilla_event_option_v1(
            event, played_character_id=29829, snapshot_option_count=3,
            ck3_build="1.20.0.4",
        )
        self.assertEqual(fallback["selected_native_option_index"], 1)
        self.assertEqual(fallback["feast_brawl_decision_context"]["comparison_status"],
                         "bounded_fallback")


if __name__ == "__main__":
    unittest.main()
