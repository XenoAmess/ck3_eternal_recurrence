from __future__ import annotations
import copy
import unittest

from xar_autoplayer.simulation.battle_current_entry_events_12003 import (
    CommittedKnightCleanup12003,
)
from xar_autoplayer.simulation.battle_current_named_person_outcomes_12003 import (
    NamedPersonOutcome12003,
    apply_committed_named_person_outcomes_12003,
)


def person(character_id, *, alive=True, jailer=-1):
    flags = {key: False for key in (
        "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
        "one_eyed", "disfigured", "incapable")}
    return {"character_id": character_id, "alive": alive,
            "status": "none" if jailer == -1 else "observed",
            "actual_jailer_character_id": jailer,
            "current_person_state": {
                "effective_prowess": {"status": "available", "points": 17,
                                      "unavailable_reason": None},
                "injury_traits": {"status": "available", "flags": flags,
                                  "wounded_rank": 0,
                                  "wounded_rank_unavailable_reason": None}}}


def observation():
    return {"snapshot_revision": 601, "observed_date_raw": 53251056,
            "battle_terminal_transition_ready": False,
            "character_observations": [person(29829),
                person(43706, jailer=30097), person(30097, alive=False)]}


class NamedPersonPrimaryConsequences12003Tests(unittest.TestCase):
    def test_selection_enqueue_and_actual_full_id_writeback_are_distinct(self):
        original = observation()
        frozen = copy.deepcopy(original)
        injury = copy.deepcopy(original["character_observations"][1]
                               ["current_person_state"]["injury_traits"])
        injury["flags"]["wounded_2"] = True
        injury["wounded_rank"] = 2
        callbacks = [
            NamedPersonOutcome12003(29829, "death", "selected_effect"),
            NamedPersonOutcome12003(43706, "death", "admitted_effect",
                source_context={"scheduled_character_id": 29829,
                                "current_regiment_character_id": 43706}),
            NamedPersonOutcome12003(43706, "death", "enqueued_pending"),
            NamedPersonOutcome12003(43706, "injury_traits", "committed_primary",
                writeback=injury, commit_writes_selected=True),
            NamedPersonOutcome12003(43706, "effective_prowess", "committed_primary",
                writeback={"status": "available", "points": -3,
                           "unavailable_reason": None}, commit_writes_selected=True),
            NamedPersonOutcome12003(30097, "death", "request_direct",
                commit_writes_selected=False),
            NamedPersonOutcome12003(29829, "death", "request_direct"),
        ]
        result = apply_committed_named_person_outcomes_12003(original, callbacks)
        rows = result["modeled_named_person_state_by_id"]
        self.assertEqual(original, frozen)
        self.assertEqual(result["origin_character_observation"], frozen)
        self.assertTrue(rows[29829]["alive"])
        self.assertTrue(rows[43706]["alive"])
        self.assertEqual(rows[43706]["actual_jailer_character_id"], 30097)
        self.assertEqual(rows[43706]["current_person_state"]["injury_traits"], injury)
        self.assertEqual(rows[43706]["current_person_state"]["effective_prowess"]["points"], -3)
        self.assertEqual(rows[29829]["current_person_state"]["injury_traits"]["wounded_rank"], 0)
        self.assertEqual(result["affected_character_ids_in_order"], (43706,))
        self.assertEqual([row["result"] for row in result["ordered_outcome_ledger"]],
            ["pending", "pending", "pending", "committed_primary_writeback",
             "committed_primary_writeback", "no_primary_writeback", "partial"])
        self.assertNotIn("modeled_death_metadata", rows[30097])
        self.assertEqual(result["cleanup_references_to_existing_owner"], ())
        self.assertIn("callback[6]:actual_primary_writeback_selected", result["missing_consequences"])
        self.assertFalse(result["observed_native_execution"])
        self.assertIsNone(result["normal_terminal_or_capture_selected"])

    def test_ordered_death_flush_guards_full_u64_metadata_and_cleanup_reference(self):
        original = observation()
        frozen = copy.deepcopy(original)
        cleanup = CommittedKnightCleanup12003(
            combat_id=1291845646, character_id=43706, linked_regiment_id=167772177,
            native_carmy_id=50331794, death_commit_selected=True,
            cleanup_branch_selected=True, court_link_present=True,
            court_knight_marker_nonzero=True)
        full_date = (1 << 63) + 53251056
        callbacks = [
            NamedPersonOutcome12003(None, "death", "flush", victim_pointer_present=False),
            NamedPersonOutcome12003(30097, "death", "flush",
                victim_pointer_present=True, death_data_pointer_is_null=False),
            NamedPersonOutcome12003(43706, "death", "flush",
                victim_pointer_present=True, death_data_pointer_is_null=True,
                date_object_raw_u64=full_date, reason_key=None,
                killer_full_character_id_raw=-1, artifact_full_id_raw=16777335,
                cleanup_reference=cleanup),
            # Source flush sees the marker installed by the prior same-victim row.
            NamedPersonOutcome12003(43706, "death", "flush",
                victim_pointer_present=True, death_data_pointer_is_null=True,
                date_object_raw_u64=7, reason_key="not_applied"),
            # Direct writer admission is separate and may rewrite an existing marker.
            NamedPersonOutcome12003(30097, "death", "committed_primary",
                commit_writes_selected=True, date_object_raw_u64=9,
                killer_full_character_id_raw=43706, artifact_full_id_raw=-1),
        ]
        result = apply_committed_named_person_outcomes_12003(original, callbacks)
        rows = result["modeled_named_person_state_by_id"]
        self.assertEqual(original, frozen)
        self.assertEqual([row["result"] for row in result["ordered_outcome_ledger"]],
            ["flush_skipped_null_victim", "flush_skipped_already_dead",
             "committed_death", "flush_skipped_already_dead", "committed_death"])
        self.assertEqual(result["affected_character_ids_in_order"], (43706, 30097))
        self.assertEqual(rows[43706]["modeled_death_metadata"], {
            "date_object_raw_u64": full_date, "reason_key": None,
            "killer_full_character_id_raw": -1, "artifact_full_id_raw": 16777335})
        self.assertFalse(rows[43706]["alive"])
        self.assertEqual(rows[43706]["status"], "observed")
        self.assertEqual(rows[43706]["actual_jailer_character_id"], 30097)
        self.assertEqual(rows[43706]["current_person_state"],
                         frozen["character_observations"][1]["current_person_state"])
        self.assertEqual(rows[30097]["modeled_death_metadata"]["killer_full_character_id_raw"], 43706)
        self.assertEqual(result["alive_for_terminal_candidate_by_id"][43706], False)
        self.assertIs(result["cleanup_references_to_existing_owner"][0], cleanup)
        self.assertEqual(result["missing_consequences"], ())
        self.assertEqual(result["actual_game_days_advanced"], 0)
        self.assertFalse(result["complete_transition"])
        self.assertFalse(result["complete_monte_carlo"])
