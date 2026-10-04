"""One independent .3 incapable-character event case; no horizon execution."""

from __future__ import annotations

import copy
import unittest

from xar_autoplayer.simulation.battle_phase_event_character_seam_12003 import (
    CharacterPhaseEventInputs12003, RootCharacterLocationScope12003,
    execute_selected_character_phase_event_12003, read_current_character_fields_12003,
)


Q = 100_000
ROOT = 29_829
LIEGE = 900_002
COMBAT = 335_544_325
DATE = 53_178_264
EVENT = "knight_becomes_incapable"


def _context(*, alive=True):
    return {
        "root_character_id": ROOT,
        "root_source_army_id": 83_886_341,
        "root_source_regiment_id": 81,
        "phase_roles": ["knight"],
        "combat_side_index": 0,
        "enemy_side_index": 1,
        "native_state_refs": {
            "root.exists": True, "root.alive": alive,
            "root.is_incapable": False, "root.traits.incapable": False,
            "root.skills.prowess_raw": 0,
            "root.traits.wounded.rank_raw": 0,
            "root.traits.fragile_bones.rank_raw": 0,
            "root.traits.fragile_bones.xp_raw": 0,
            "root.traits.one_legged": False, "root.traits.disfigured": False,
            "root.traits.one_eyed": False, "root.traits.maimed": False,
            "root.court_positions.garuda": False,
            "root.traits_and_culture_for_blademaster": {
                "education_martial": [False] * 5, "education_martial_prowess": [False] * 4,
                "intellect_good": [False] * 3, "lifestyle_blademaster": False,
                "lifestyle_blademaster_xp_raw": 0, "shrewd": False, "physique_good": False,
                "culture_blademaster_traits_more_common": False},
            "combat_side.character_membership": [ROOT, LIEGE],
            "enemy_side.character_membership": [],
            "combat_side.ordered_enemy_knights": [],
            "combat_side.commander": LIEGE,
        },
        "offline_state_refs": {},
        "candidate_rows": [],
    }


def _source():
    return {
        "combat_id": COMBAT, "snapshot_revision": 7, "observed_date_raw": DATE,
        "root_source_native_carmy_id": 101, "root_source_public_cunit_id": 83_886_341,
        "combat_province_id": 2586,
        "provenance": "independent_synthetic_character_inputs_not_an_actual_game_frame",
    }


def _observation(*, alive=True, incapable=False, prowess=0):
    flags = {key: None for key in ("wounded_1", "wounded_2", "wounded_3", "maimed",
                                  "one_legged", "one_eyed", "disfigured", "incapable")}
    flags["incapable"] = incapable
    row = {
        "character_id": ROOT, "status": "none", "actual_jailer_character_id": -1,
        "alive": alive,
        "current_person_state": {
            "scope": "current_character",
            "effective_prowess": {
                "status": "available" if prowess is not None else "unavailable",
                "points": prowess,
                "unavailable_reason": None if prowess is not None else "fixture_no_effective_property_read",
            },
            "injury_traits": {
                "status": "partial" if incapable is not None else "unavailable", "flags": flags,
                "wounded_rank": None,
                "unavailable_reason": "fixture_other_trait_flags_unobserved",
                "wounded_rank_unavailable_reason": "fixture_wounded_flags_unobserved",
            },
        },
    }
    return {"snapshot_revision": 7, "observed_date_raw": DATE, "character_observations": [row]}


class BattlePhaseEventCharacterSeamV62FixtureTests(unittest.TestCase):
    captured_results = []

    def test_incapable_primary_and_current_reader_keep_native_callbacks_partial(self):
        context = _context()
        original_context = copy.deepcopy(context)
        observed = _observation()
        original_observed = copy.deepcopy(observed)
        observation_source = {"native_revision": 7, "date_raw": DATE, "paused": True,
                              "kind": "synthetic_independent_character_query_not_an_inline_battle_sample"}
        read = read_current_character_fields_12003(
            observed, character_id=ROOT, source_context=observation_source)
        self.assertEqual(read.character_id, ROOT)
        self.assertTrue(read.alive)
        self.assertIs(read.incapable_trait, False)
        self.assertEqual(read.effective_prowess_points, 0)
        self.assertEqual(read.missing_inputs, ())
        self.assertEqual(observed["character_observations"][0]["current_person_state"]["injury_traits"]["status"],
                         "partial")

        location = RootCharacterLocationScope12003(
            character_id=ROOT, province_id=4100,
            source_provenance={"source": "synthetic_caller_current_root_location", "observed_by_caller": True})
        inputs = CharacterPhaseEventInputs12003(
            root_location_scope=location, current_person_observation=observed,
            observation_source=observation_source)
        result = execute_selected_character_phase_event_12003(
            context, script_outcomes=(), source_context=_source(), inputs=inputs)
        self.assertTrue(result.event_execution_consumed)
        self.assertFalse(result.condition_feedback_ready)
        self.assertEqual(len(result.character_primary_deltas), 1)
        delta = result.character_primary_deltas[0]
        self.assertEqual((delta["character_id"], delta["field"], delta["before"], delta["after"]),
                         (ROOT, "traits.incapable", False, True))
        self.assertEqual(delta["unit"], "trait_boolean")
        self.assertIsNone(delta["delta_raw"])
        after = result.execution["after_state"]
        self.assertTrue(after["root"]["traits"]["incapable"])
        self.assertTrue(after["root"]["alive"])
        self.assertEqual(after["root"]["prowess_raw"], 0)
        self.assertEqual(after["root"]["wounded_rank_raw"], 0)
        self.assertEqual(after["sides"]["combat_membership"], [ROOT, LIEGE])
        self.assertEqual(after["sides"]["combat_commander_character_id"], LIEGE)
        self.assertEqual(after["recompute"]["participant_detach_ids"], [])
        self.assertNotIn("battle_location", after["root"]["variable_updates"])
        self.assertEqual(result.current_person_reader.effective_prowess_points, 0)
        self.assertIs(result.current_person_reader.incapable_trait, False)
        self.assertTrue(result.typed_callback_gaps)
        self.assertIn("memory", repr(result.typed_callback_gaps).lower())
        self.assertIn("effective", repr(result.typed_callback_gaps).lower())
        self.assertEqual(len(result.memory_requests), 1)
        memory = result.memory_requests[0]
        self.assertEqual(memory["owner_character_id"], ROOT)
        self.assertEqual(memory["type"], "became_incapable_due_to_battle_concussion")
        self.assertEqual(memory["scope_aliases"], {"knight": ROOT, "new_memory_to": "battle_memory"})
        self.assertEqual(memory["variables"], {"battle_location": 4100})
        self.assertNotEqual(memory["variables"]["battle_location"], _source()["combat_province_id"])
        self.assertIsNone(memory["native_memory_id"])
        self.assertFalse(memory["native_memory_commit_observed"])
        self.assertTrue(memory["request_only"])
        self.assertEqual(context, original_context)
        self.assertEqual(observed, original_observed)

        missing_location = execute_selected_character_phase_event_12003(
            context, script_outcomes=(), source_context=_source(),
            inputs=CharacterPhaseEventInputs12003(current_person_observation=observed,
                                                 observation_source=observation_source))
        self.assertTrue(missing_location.character_primary_deltas[0]["after"])
        self.assertEqual(missing_location.memory_requests[0]["type"], memory["type"])
        self.assertIsNone(missing_location.memory_requests[0]["variables"]["battle_location"])
        self.assertFalse(missing_location.condition_feedback_ready)
        self.assertIn("location", repr(missing_location.typed_callback_gaps).lower())

        dead_context = _context(alive=False)
        dead_before = copy.deepcopy(dead_context)
        dead = execute_selected_character_phase_event_12003(
            dead_context, script_outcomes=(), source_context=_source(),
            inputs=CharacterPhaseEventInputs12003(current_person_observation=_observation(alive=False),
                                                 observation_source=observation_source))
        self.assertTrue(dead.event_execution_consumed)
        self.assertTrue(dead.condition_feedback_ready, dead.typed_callback_gaps)
        self.assertEqual(dead.character_primary_deltas, ())
        self.assertEqual(dead.memory_requests, ())
        self.assertEqual(dead.typed_callback_gaps, ())
        self.assertFalse(dead.execution["after_state"]["root"]["alive"])
        self.assertFalse(dead.execution["after_state"]["root"]["traits"]["incapable"])
        self.assertEqual(dead_context, dead_before)

        unknown = read_current_character_fields_12003(
            _observation(alive=False, incapable=None, prowess=None),
            character_id=ROOT, source_context=observation_source)
        self.assertIs(unknown.alive, False)
        self.assertIsNone(unknown.incapable_trait)
        self.assertIsNone(unknown.effective_prowess_points)
        self.assertTrue(unknown.missing_inputs)
        self.captured_results.append({
            "case": "incapable_trait_primary_reader_and_memory_source_boundary",
            "root_character_id": ROOT,
            "trait_before_after": [delta["before"], delta["after"]],
            "trait_delta_raw": delta["delta_raw"],
            "observed_effective_prowess_points": read.effective_prowess_points,
            "observed_trait_known_despite_partial_status": read.incapable_trait,
            "reader_is_before_observation_not_predicted_post_trait_effective_property": True,
            "alive_affected_condition_feedback_ready": result.condition_feedback_ready,
            "memory_type": memory["type"],
            "memory_battle_location": memory["variables"]["battle_location"],
            "combat_province_not_substituted": _source()["combat_province_id"],
            "memory_native_id": memory["native_memory_id"],
            "memory_commit_observed": memory["native_memory_commit_observed"],
            "missing_location_primary_retained": missing_location.character_primary_deltas[0]["after"],
            "missing_location_argument": missing_location.memory_requests[0]["variables"]["battle_location"],
            "dead_guard_condition_feedback_ready": dead.condition_feedback_ready,
            "dead_guard_trait_memory_writes": [len(dead.character_primary_deltas), len(dead.memory_requests)],
            "unknown_current_trait_and_prowess": [unknown.incapable_trait, unknown.effective_prowess_points],
            "actual_game_days_advanced": 0,
        })


if __name__ == "__main__":
    unittest.main()
