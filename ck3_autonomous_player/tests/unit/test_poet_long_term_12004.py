"""New registered-consumer cases; qualification is performed by Root."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.outcome import (
    plan_registered_event_material_postcondition_v1,
    evaluate_registered_event_material_postcondition_v1,
)


def _scope(character_id):
    return {"status": "available", "raw_type_index": 4, "type_key": "character",
        "subtype": 0, "typed_identity": {"status": "available",
            "kind": "character", "character_id": character_id}}


def _stress():
    return {"kind": "stress", "direction": "decrease",
        "magnitude": {"status": "unavailable"}, "affected_by_trait": True,
        "critical": False}


def _event(relief):
    options = []
    for index in range(3):
        rows = []
        if index in (0, 1):
            rows.append({"kind": "trait", "operation": "add", "trait": {
                "status": "available", "native_id": 100 + index,
                "key": "lifestyle_poet" if index == 0 else "journaller"}})
        if index in relief:
            rows.append(_stress())
        options.append({"rendered_index": index, "native_option_index": index,
            "shown": True, "enabled": True, "fallback": False, "cancel": False,
            "effect_indicators": {"status": "available", "coverage":
                "played-character-event-icon-indicators-1.20.0.4-v1",
                "complete_effect_set": False, "rows": rows}})
    return {"schema": "current-event-window-context-v1", "schema_version": 1,
        "status": "available", "event_definition_key": "trait_specific.9001",
        "snapshot_revision": 51, "date_raw": 53288232,
        "current_event_instance_id": 17, "window_match_count": 1,
        "root_scope": _scope(29829),
        "saved_scopes": [{"name": "subject", "scope": _scope(30400)}],
        "options": options, "readiness": {
            "event_definition_identity_ready": True, "root_scope_ready": True,
            "saved_scopes_ready": True, "option_presentation_ready": True},
        "provenance": {"backend_id": "ck3-1.20.0.4-native-event-window-v1"}}


def _decision(stress, relief):
    return recommend_registered_vanilla_event_option_v1(
        _event(relief), played_character_id=29829, snapshot_option_count=3,
        ck3_build="1.20.0.4",
        played_character={"character_id": 29829, "stress_points": stress})


def _traits(native_revision, poet):
    return {"schema": "xar.ck3.player-event-trait-membership/v1",
        "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "status": "available", "snapshot_revision": native_revision,
        "date_raw": 53288232, "played_character_id": 29829,
        "traits": {"lifestyle_poet": poet, "journaller": False},
        "unavailable_reason": None}


class PoetLongTerm12004Tests(unittest.TestCase):
    def test_registered_choice_uses_current_stress_and_permanent_relief(self):
        decision = _decision(120, {1, 2})
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_native_option_index"], 1)
        self.assertEqual(decision["choice_effect_profile"]["observable_postcondition"]["metric"],
            "played_character.event_traits.journaller")
        self.assertFalse(decision["semantic_decision_ready"])

    def test_registered_choice_can_use_immediate_relief(self):
        decision = _decision(120, {2})
        self.assertEqual(decision["selected_native_option_index"], 2)
        expectation = plan_registered_event_material_postcondition_v1(
            decision, {"character_id": 29829, "stress_points": 120},
            snapshot_id="native:51", revision=7)
        self.assertEqual(expectation["metric"], "played_character.stress_points")
        self.assertEqual(expectation["expected_relation"], "strictly_decreasing")
        selection = {"postcondition_verified": True,
            "starting_snapshot_id": "native:51", "ending_snapshot_id": "native:52",
            "starting_revision": 7, "ending_revision": 8,
            "starting_played_character_stress": {"status": "available",
                "character_id": 29829, "stress_points": 120},
            "ending_played_character_stress": {"status": "available",
                "character_id": 29829, "stress_points": 110}}
        self.assertEqual(evaluate_registered_event_material_postcondition_v1(
            expectation, selection)["status"], "verified_change")

    def test_below_threshold_and_poet_relief_retain_permanent_poet(self):
        self.assertEqual(_decision(20, {1, 2})["selected_native_option_index"], 0)
        self.assertEqual(_decision(120, {0, 1, 2})["selected_native_option_index"], 0)

    def test_trait_material_gain_requires_independent_actual_membership(self):
        decision = _decision(20, {2})
        expectation = plan_registered_event_material_postcondition_v1(
            decision, {"character_id": 29829, "event_trait_membership": _traits(51, False)},
            snapshot_id="native:51", revision=7, native_revision=51, date_raw=53288232)
        selection = {"postcondition_verified": True,
            "starting_snapshot_id": "native:51", "ending_snapshot_id": "native:52",
            "starting_revision": 7, "ending_revision": 8,
            "starting_played_character_event_traits": _traits(51, False),
            "ending_played_character_event_traits": _traits(52, True)}
        self.assertEqual(evaluate_registered_event_material_postcondition_v1(
            expectation, selection)["status"], "verified_change")
        selection.pop("ending_played_character_event_traits")
        self.assertEqual(evaluate_registered_event_material_postcondition_v1(
            expectation, selection)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
