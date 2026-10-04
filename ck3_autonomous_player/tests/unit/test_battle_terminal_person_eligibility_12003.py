from __future__ import annotations
import copy
import unittest

from xar_autoplayer.simulation.battle_current_adapter import CurrentBattleCondition, CurrentBattleSide
from xar_autoplayer.simulation.battle_current_named_person_outcomes_12003 import (
    NamedPersonOutcome12003, apply_committed_named_person_outcomes_12003,
)
from xar_autoplayer.simulation.battle_current_normal_finalizer import (
    CurrentNormalFinalizerManagerInputs, project_current_normal_finalizer,
)
from xar_autoplayer.simulation.battle_terminal_person_eligibility_12003 import (
    TerminalPersonCandidate12003, project_named_person_terminal_eligibility_12003,
)


def terminal_condition():
    sides = tuple(CurrentBattleSide(
        side_index=i, role=role, primary_participant_character_id=primary,
        selected_commander_character_id=primary, current_roll_points=0,
        roll_request=None, entries=(), ordered_armies=(),
        stored_current_fighting_raw=0, stored_levy_current_fighting_raw=0,
        derived_current_fighting_raw=0, derived_soft_casualties_raw=0,
        derived_main_fighting_entry_hard_casualties_raw=0,
        non_main_start_minus_current_minus_soft_raw=0,
        participant_hard_ledger=(), participant_hard_total_raw=0,
        loss_inputs=None, levy_damage_raw=None, levy_damage_source="unavailable",
        levy_damage_native_observed=False, levy_damage_primary_participant_character_id=None,
    ) for i, role, primary in ((0, "attacker", 29829), (1, "defender", 30097)))
    return CurrentBattleCondition(
        snapshot_revision=6201, observed_date_raw=53251056,
        combat_id=16777317, province_id=2669, subject_side_index=0,
        side_scope="constructed_terminal_condition", phase="done", phase_raw=3,
        phase_day=0, base_combat_width=0, final_combat_width=0,
        roll_cadence_counter=0, base_advantage_raw=0, resolved_advantage_raw=0,
        sides=sides, loss_inputs=None, active_counter_inputs=None,
        pursuit_modifier_sides=None, missing_inputs=("backing_and_terminal_baselines",),
        source_snapshot={})


class TerminalPersonComposition12003Tests(unittest.TestCase):
    def test_real_producers_pending_commit_and_independent_stock_guards(self):
        original = {"snapshot_revision": 6201,
                    "battle_terminal_transition_ready": False,
                    "character_observations": [
                        {"character_id": 43706, "alive": True, "status": "none",
                         "actual_jailer_character_id": -1, "current_person_state": None},
                        {"character_id": 30097, "alive": True, "status": "none",
                         "actual_jailer_character_id": -1, "current_person_state": None}]}
        frozen = copy.deepcopy(original)
        named = apply_committed_named_person_outcomes_12003(original, (
            NamedPersonOutcome12003(43706, "death", "enqueued_pending"),
            NamedPersonOutcome12003(30097, "death", "flush",
                victim_pointer_present=True, death_data_pointer_is_null=True),
        ))
        condition = terminal_condition()
        manager = CurrentNormalFinalizerManagerInputs(
            entry_kind="daily_row", combat_manager_row_admitted=True,
            pending_suppression_sweep=False, primary_hostile=True,
            result_present=False)
        normal = project_current_normal_finalizer(condition, manager=manager, winner_raw=0)
        self.assertTrue(normal["dispatch"]["normal_result_intent"])
        self.assertEqual(normal["status"], "partial")
        self.assertFalse(normal["named_character_outcomes_predicted"])
        candidates = (
            TerminalPersonCandidate12003(43706, "losing_knight", "capture",
                is_imprisoned=False, prisoner_install_context_selected=True),
            TerminalPersonCandidate12003(30097, "losing_commander", "capture",
                is_imprisoned=False, prisoner_install_context_selected=True),
            TerminalPersonCandidate12003(55555, "losing_knight", "death"),
        )
        common = dict(winner_primary_character_id=29829,
            loser_primary_character_id=30097, war_tutorial=False, candidates=candidates)
        joined = project_named_person_terminal_eligibility_12003(
            named, normal, primary_participants_really_at_war=True, **common)
        rows = joined["ordered_candidate_guard_results"]
        self.assertEqual(original, frozen)
        self.assertTrue(joined["normal_envelope_covered_guards_passed"])
        self.assertEqual([row["character_id"] for row in rows], [43706, 30097, 55555])
        self.assertEqual([row["covered_normal_candidate_guards_passed"] for row in rows],
                         [True, False, None])
        self.assertEqual([row["covered_prisoner_install_guards_passed"] for row in rows],
                         [True, False, None])
        self.assertTrue(joined["origin_character_observation"]["character_observations"][1]["alive"])
        self.assertFalse(joined["modeled_person_state"][30097]["alive"])
        self.assertIs(joined["normal_finalizer_projection"], normal)
        self.assertIs(joined["named_person_outcomes"], named)
        self.assertIsNone(joined["capture_or_death_writeback_selected"])
        self.assertFalse(joined["actual_native_effects_executed"])
        # Broader manager hostility never substitutes for .1001 actual war.
        nonwar = project_named_person_terminal_eligibility_12003(
            named, normal, primary_participants_really_at_war=False, **common)
        self.assertFalse(nonwar["normal_envelope_covered_guards_passed"])
        self.assertFalse(nonwar["ordered_candidate_guard_results"][0]
                         ["covered_normal_candidate_guards_passed"])
        # An already selected .1002 context is independent of the .1001 trigger.
        self.assertTrue(nonwar["ordered_candidate_guard_results"][0]
                        ["covered_prisoner_install_guards_passed"])
        fallback = project_current_normal_finalizer(condition, manager=manager, winner_raw=-1)
        unresolved = project_named_person_terminal_eligibility_12003(
            named, fallback, winner_primary_character_id=None,
            loser_primary_character_id=None, primary_participants_really_at_war=True,
            war_tutorial=False, candidates=())
        self.assertTrue(fallback["dispatch"]["normal_result_intent"])
        self.assertIsNone(unresolved["normal_envelope_covered_guards_passed"])
        self.assertEqual(unresolved["normal_envelope_missing_operands"],
                         ("winner_primary_context", "loser_primary_context"))
        self.assertEqual(joined["actual_game_days_advanced"], 0)
        self.assertFalse(joined["complete_native_finalizer"])
