from __future__ import annotations

import copy
import unittest

from test_battle_current_condition import Q, _entry, _raw_frame, _side
from test_battle_current_refresh import _carried, _counter, _next_frame, _normalize
from xar_autoplayer.bridge.battle_terminal_transition_contract import normalize_battle_terminal_transition_v1
from xar_autoplayer.simulation.battle_current_knight_entry_refresh import associate_current_knight_entries
from xar_autoplayer.simulation.battle_current_refresh import refresh_current_battle_condition


def _person_leaf(frame: dict, points: dict[int, int | None], *, revision: int | None = None,
                 unavailable: bool = False) -> dict:
    revision = frame["snapshot_revision"] if revision is None else revision
    observations = []
    for character, value in points.items():
        flags = {key: False if value is not None else None for key in (
            "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
            "one_eyed", "disfigured", "incapable")}
        if value is not None:
            flags.update(wounded_2=True, maimed=True)
        observations.append({
            "character_id": character, "status": "none", "actual_jailer_character_id": -1,
            "alive": True if value is not None else None,
            "current_person_state": {
                "scope": "current_character", "effective_prowess": {
                    "status": "available" if value is not None else "unavailable",
                    "points": value, "unavailable_reason": None if value is not None else "fixture_read_failed"},
                "injury_traits": {
                    "status": "available" if value is not None else "unavailable", "flags": flags,
                    "wounded_rank": 2 if value is not None else None,
                    "wounded_rank_unavailable_reason": None if value is not None else "fixture_read_failed",
                    "unavailable_reason": None if value is not None else "fixture_read_failed"},
            },
        })
    raw = {
        "schema_version": 1, "contract_stage": "production_exact_battle_terminal_transition",
        "status": "unavailable" if unavailable else "available",
        "unavailable_reason": "journal_gap" if unavailable else None,
        "battle_terminal_transition_ready": False, "snapshot_revision": revision,
        "observed_date_raw": frame["observed_date_raw"], "prior_combat_id": -1,
        "subject_public_cunit_id": -1,
        "terminal_journal": {"requested_after_sequence": None, "oldest_available_sequence": 0,
                             "latest_sequence": 0, "event_sequence": None, "event_status": "not_observed"},
        "prior": None, "removal": None, "subject": None, "successor": None,
        "character_observations": observations,
    }
    return normalize_battle_terminal_transition_v1(raw, expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None, expected_after_terminal_sequence=None,
        expected_observed_date_raw=frame["observed_date_raw"], expected_snapshot_revision=revision,
        expected_character_ids=list(points))


def _source(frame: dict, revision: int | None = None) -> dict:
    return {"native_revision": frame["snapshot_revision"] if revision is None else revision,
            "date_raw": frame["observed_date_raw"], "paused": True,
            "player_character_id": 29829, "actor_character_id": 29829}


class BattleCurrentKnightEntryRefreshTests(unittest.TestCase):
    """Two focused production-shaped current-observation cases; no live claim."""

    def test_injured_retained_knight_keeps_authoritative_current_and_stored_stats(self):
        raw = _raw_frame(1)
        raw["attacker"]["men_at_arms_entries"][0]["knight_character_id_raw"] = 34333
        _, _, carried = _carried(raw)
        self.assertEqual(carried.condition.sides[0].entries[1].state.current_raw, 450000)
        fresh = _next_frame(raw)
        frame, resume = _normalize(fresh)
        refreshed = refresh_current_battle_condition(carried, frame, active_resume_inputs=resume)
        person = _person_leaf(frame, {34333: 0})
        before = copy.deepcopy((frame, person, refreshed.ledger))
        result = associate_current_knight_entries(refreshed, previous_condition=carried.condition,
            current_person_observation=person, person_query_source=_source(frame), control_query_source=_source(frame))
        self.assertIs(result.refreshed, refreshed)
        self.assertIs(result.condition, refreshed.condition)
        self.assertEqual((frame, person, refreshed.ledger), before)
        entry = result.condition.sides[0].entries[1]
        self.assertEqual(entry.state.current_raw, 600000)
        self.assertFalse(entry.fights_in_main_phase)
        self.assertEqual((entry.effective_damage_raw, entry.state.toughness_raw), (300000, Q))
        rows = result.ledger["sides"][0]["entries_in_native_order"]
        self.assertEqual([row["identity"]["regiment_id"] for row in rows], [90, 7])
        self.assertEqual(rows[1]["membership"], "retained")
        self.assertEqual(rows[1]["knight_identity_change"], "retained")
        state = rows[1]["current_person_observation"]["current_person_state"]
        self.assertEqual(state["effective_prowess"]["points"], 0)
        self.assertTrue(state["injury_traits"]["flags"]["wounded_2"])
        self.assertTrue(state["injury_traits"]["flags"]["maimed"])
        self.assertEqual(result.ledger["binding"]["status"], "same_paused_native_sample_coordinates")
        self.assertEqual((refreshed.draw_state.counter, refreshed.draw_state.salt), (carried.draw_state.counter, carried.draw_state.salt))
        self.assertFalse(result.ledger["previous_predicted_losses_reapplied"])
        self.assertFalse(result.ledger["person_state_used_to_remove_entry"])
        self.assertFalse(result.ledger["person_state_used_to_replace_stored_stats"])
        self.assertFalse(result.ledger["draw_consumed"])

    def test_rebound_new_absent_order_and_independent_posteffect_person_rows(self):
        raw = _raw_frame(2)
        enemy_a, enemy_b = raw["defender"]["ordered_armies"]
        raw["defender"]["men_at_arms_entries"][1]["knight_character_id_raw"] = 36108
        absent = _entry(103, enemy_b, bucket="men_at_arms", index=2,
                        current=0, damage=0, toughness=0, main=False)
        absent["knight_character_id_raw"] = 34334
        raw["defender"]["men_at_arms_entries"].append(absent)
        _counter(raw, Q)
        _, _, carried = _carried(raw)
        fresh = _next_frame(raw)
        entries = [
            _entry(3, enemy_b, bucket="men_at_arms", index=0, current=400000, damage=0, toughness=Q, old_hard=350000),
            _entry(5, enemy_b, bucket="men_at_arms", index=1, current=0, damage=0, toughness=0, main=False),
            _entry(99, enemy_a, bucket="men_at_arms", index=2, current=600000, damage=0, toughness=Q, old_hard=250000),
            _entry(101, enemy_a, bucket="men_at_arms", index=3, current=0, damage=0, toughness=0, main=False),
        ]
        entries[0]["knight_character_id_raw"] = 34335
        entries[1]["knight_character_id_raw"] = -1
        entries[3]["knight_character_id_raw"] = 34333
        fresh["defender"] = _side(1, [enemy_b, enemy_a], [], entries,
                                  [(enemy_b["owner_character_id"], 350000), (enemy_a["owner_character_id"], 250000)])
        _counter(fresh, Q)
        frame, resume = _normalize(fresh)
        refreshed = refresh_current_battle_condition(carried, frame, active_resume_inputs=resume)
        person = _person_leaf(frame, {34333: None, 34335: 0}, revision=frame["snapshot_revision"]+1, unavailable=True)
        before = copy.deepcopy(person)
        result = associate_current_knight_entries(refreshed, previous_condition=carried.condition,
            current_person_observation=person, person_query_source=_source(frame, frame["snapshot_revision"]+1),
            control_query_source=_source(frame))
        self.assertIs(result.condition, refreshed.condition)
        self.assertEqual(person, before)
        rows = result.ledger["sides"][1]["entries_in_native_order"]
        self.assertEqual([row["identity"]["regiment_id"] for row in rows], [3, 5, 99, 101])
        self.assertEqual(rows[0]["knight_identity_change"], "rebound")
        self.assertTrue(rows[0]["order_changed"])
        self.assertEqual(rows[0]["current_person_observation"]["current_person_state"]["effective_prowess"]["points"], 0)
        self.assertEqual(rows[1]["membership"], "new_in_fresh_frame")
        self.assertEqual(rows[1]["knight_identity"]["raw"], -1)
        self.assertFalse(rows[1]["person_row_present"])
        self.assertEqual(rows[2]["knight_identity"], {"present": False, "raw": None, "kind": "absent"})
        self.assertIsNone(rows[3]["current_person_observation"]["current_person_state"]["effective_prowess"]["points"])
        self.assertIsNone(rows[3]["current_person_observation"]["alive"])
        self.assertEqual(rows[3]["person_attribution"], "independent_current_character_observation")
        gone = result.ledger["sides"][1]["absent_entries_in_previous_native_order"]
        self.assertEqual([row["identity"]["regiment_id"] for row in gone], [103])
        self.assertIsNone(gone[0]["absence_cause"])
        self.assertEqual([entry.state.current_raw for entry in result.condition.sides[1].entries], [400000, 0, 600000, 0])
        self.assertEqual([row["character_id"] for row in result.ledger["character_observations_in_request_order"]], [34333, 34335])
        self.assertEqual(result.ledger["binding"]["status"], "native_sample_coordinates_unbound_or_mismatched")
        self.assertFalse(result.ledger["binding"]["is_runtime_gate"])
        self.assertFalse(result.complete_transition)
        self.assertFalse(result.complete_monte_carlo)


if __name__ == "__main__":
    unittest.main()
