"""Two synthetic, source-derived .3 feedback cases; no native execution."""

from __future__ import annotations

import copy
from dataclasses import replace
import unittest

from test_battle_current_conditional_horizon import (
    COMBAT, DATE, _day, _initial_condition,
)
from test_battle_phase_events_12003 import (
    ENEMY_ID, ROOT_ID, _context, _manifest, _selected_enemy_outcomes,
)
from xar_autoplayer.simulation.battle_current_conditional_horizon import _totals
from xar_autoplayer.simulation.battle_current_next_day import CarriedBattleCondition
from xar_autoplayer.simulation.battle_phase_event_feedback_12003 import (
    KnightCachedStatRefresh12003,
    SelectedPhaseEventInput12003,
    apply_selected_phase_event_feedback_12003,
    run_selected_phase_feedback_horizon_12003,
)
from xar_autoplayer.simulation.combat_core import DrawState, RegimentKind


Q = 100_000


def _source(condition):
    return {
        "combat_id": condition.combat_id,
        "snapshot_revision": condition.snapshot_revision,
        "observed_date_raw": condition.observed_date_raw,
        "modeled_dispatch_date_raw": DATE + 24,
        "modeled_phase_day": condition.phase_day + 1,
        "provenance": "synthetic_caller_condition_not_an_actual_game_sample",
    }


def _event_context():
    context = _context(wounded_rank_raw=Q)
    context.update(root_source_army_id=101, root_source_regiment_id=81)
    return context


def _carried(condition):
    return CarriedBattleCondition(
        condition=condition,
        draw_state=DrawState(13, 17),
        scope_kind="synthetic_selected_event_feedback_fixture",
        conditional_assumptions=("source_order_selected_tape",),
        simulated_main_ticks=0,
        origin_observed_frame={key: _source(condition)[key] for key in
                               ("combat_id", "snapshot_revision", "observed_date_raw")},
        derived_side_totals=_totals(condition),
    )


def _knight_condition():
    initial = _initial_condition(damage_scaling=25_000)
    defender = initial.sides[1]
    original = defender.entries[0]
    knight = replace(
        original,
        bucket="men_at_arms",
        knight_character_id_raw=ENEMY_ID,
        effective_damage_raw=2 * Q,
        state=replace(original.state, kind=RegimentKind.MEN_AT_ARMS,
                      toughness_raw=3 * Q, pursuit_raw=4 * Q, screen_raw=5 * Q),
    )
    return replace(initial, sides=(initial.sides[0], replace(defender, entries=(knight, defender.entries[1]))))


def _refresh(condition, *, points=23, effectiveness=125_000, boundary=True):
    entry = condition.sides[1].entries[0]
    return KnightCachedStatRefresh12003(
        combat_id=COMBAT,
        side_index=1,
        regiment_id=entry.state.regiment_id,
        native_carmy_id=entry.native_carmy_id,
        public_cunit_id=entry.public_cunit_id,
        knight_character_id=ENEMY_ID,
        after_effective_prowess_points=points,
        effectiveness_raw=effectiveness,
        loaded_damage_multiplier=100,
        loaded_toughness_multiplier=10,
        valid_special_knight=True,
        refresh_boundary_selected=boundary,
        source_context=_source(condition),
    )


def _wounded(condition, *, refreshes=()):
    return SelectedPhaseEventInput12003(
        context=_event_context(),
        event_key="commander_wounded",
        script_outcomes=_selected_enemy_outcomes(event_key="commander_wounded", prowess_branch=1),
        source_context=_source(condition),
        manifest=_manifest(),
        knight_refreshes=refreshes,
    )


def _delta(result, actor, field):
    return next(row for row in result.character_numeric_deltas
                if row["character_id"] == actor and row["field"] == field)


class BattlePhaseEventFeedback12003FixtureTests(unittest.TestCase):
    captured_results = []

    def test_selected_noop_enters_horizon_and_numeric_literal_refresh_is_exact(self):
        initial = _initial_condition(damage_scaling=25_000)
        noop = SelectedPhaseEventInput12003(
            context=_event_context(), event_key="commander_none", source_context=_source(initial), manifest=_manifest())
        day = replace(_day(0), phase_events=({"event_key": "commander_none"},))
        wrapped = run_selected_phase_feedback_horizon_12003(
            initial, day=day, selected=(noop,), draw_state=DrawState(13, 17),
            caller_seed_provenance={"stream": "caller_owned_fixture", "native_rng": False})
        self.assertTrue(wrapped.event_tape_consumed)
        self.assertTrue(wrapped.feedback.feedback_ready)
        self.assertEqual(wrapped.feedback.character_numeric_deltas, ())
        self.assertEqual(wrapped.horizon.status, "available", wrapped.horizon.typed_gaps)
        self.assertEqual(wrapped.horizon.modeled_accepted_invocations, 1)
        self.assertEqual(wrapped.horizon.modeled_date_raw, DATE + 24)
        after = wrapped.horizon.final_state.condition
        self.assertEqual(after.phase_day, initial.phase_day + 1)
        self.assertEqual(after.roll_cadence_counter, 1)
        self.assertEqual(wrapped.horizon.final_state.draw_state, DrawState(15, 17))
        tick_stage = next(stage for stage in wrapped.horizon.trace[0]["stages"]
                          if stage["stage"] == "future_main_and_internal_P2_carry")
        self.assertEqual(tick_stage["result"].result["outgoing_damage_raw_by_side"], [2_500_000, 0])
        self.assertEqual([row.state.current_raw for row in after.sides[1].entries], [3_750_000, 3_750_000])
        self.assertEqual(after.sides[1].participant_hard_total_raw, 1_250_000)
        self.assertEqual(after.source_snapshot, initial.source_snapshot)

        condition = _knight_condition()
        before = _carried(condition)
        selected = _wounded(condition, refreshes=(_refresh(condition),))
        input_copy = copy.deepcopy(selected.context)
        result = apply_selected_phase_event_feedback_12003(before, selected=(selected,))
        wound = _delta(result, ROOT_ID, "wounded_rank_raw")
        prowess = _delta(result, ENEMY_ID, "prowess_raw")
        self.assertEqual((wound["before"], wound["after"], wound["delta_raw"]), (Q, 2 * Q, Q))
        self.assertEqual((prowess["before"], prowess["after"], prowess["delta_raw"]), (20 * Q, 21 * Q, Q))
        fresh = result.carried.condition.sides[1].entries[0]
        self.assertEqual(fresh.effective_damage_raw, 287_500_000)
        self.assertEqual(fresh.state.toughness_raw, 28_750_000)
        self.assertEqual((fresh.state.pursuit_raw, fresh.state.screen_raw), (0, 0))
        # Explicit effective prowess 23 differs from base prowess21: no inferred skill-to-cache calculator.
        self.assert_preserved_accounts(before, result.carried)
        self.assertEqual(selected.context, input_copy)
        self.assertTrue(result.event_execution_consumed)
        self.assertFalse(result.feedback_ready)
        self.assertTrue(result.typed_gaps)
        self.assertTrue(result.executions[0]["feedback_pending"])
        self.captured_results.append({
            "case": "selected_noop_horizon_and_explicit_literal_numeric_feedback",
            "accepted_invocations": wrapped.horizon.modeled_accepted_invocations,
            "outgoing_damage_raw_by_side": [2_500_000, 0],
            "defender_current_raw": [3_750_000, 3_750_000],
            "defender_hard_total_raw": 1_250_000,
            "wound_before_after_delta_raw": [Q, 2 * Q, Q],
            "base_prowess_before_after_delta_raw": [20 * Q, 21 * Q, Q],
            "explicit_after_effective_prowess_points": 23,
            "knight_damage_raw": fresh.effective_damage_raw,
            "knight_toughness_raw": fresh.state.toughness_raw,
            "full_callbacks_ready": result.feedback_ready,
        })

    def test_mixed_unknown_retains_known_feedback_and_tape_waits_for_main(self):
        condition = _knight_condition()
        before = _carried(condition)
        known = _wounded(condition, refreshes=(_refresh(condition),))
        unknown = SelectedPhaseEventInput12003(
            context=_event_context(), event_key="knight_become_berserker",
            source_context=_source(condition), manifest=_manifest())
        mixed = apply_selected_phase_event_feedback_12003(before, selected=(known, unknown))
        self.assertFalse(mixed.feedback_ready)
        self.assertTrue(mixed.typed_gaps)
        self.assertIn("knight_become_berserker", repr(mixed.typed_gaps))
        self.assertEqual(mixed.ledger["event_execution_consumed"], [True, False])
        self.assertEqual(_delta(mixed, ENEMY_ID, "prowess_raw")["after"], 21 * Q)
        self.assertEqual(mixed.carried.condition.sides[1].entries[0].effective_damage_raw, 287_500_000)
        self.assertTrue(mixed.executions[0]["feedback_pending"])
        self.assert_preserved_accounts(before, mixed.carried)

        missing = apply_selected_phase_event_feedback_12003(
            before, selected=(_wounded(condition, refreshes=(_refresh(condition, points=None),)),))
        self.assertEqual(_delta(missing, ENEMY_ID, "prowess_raw")["after"], 21 * Q)
        self.assertEqual(missing.carried.condition.sides[1].entries[0], condition.sides[1].entries[0])
        self.assertFalse(missing.feedback_ready)
        clamped = apply_selected_phase_event_feedback_12003(
            before, selected=(_wounded(condition, refreshes=(_refresh(condition, points=0),)),))
        clamped_entry = clamped.carried.condition.sides[1].entries[0]
        self.assertEqual((clamped_entry.effective_damage_raw, clamped_entry.state.toughness_raw),
                         (12_500_000, 1_250_000))
        zero = apply_selected_phase_event_feedback_12003(
            before, selected=(_wounded(condition, refreshes=(_refresh(condition, effectiveness=0),)),))
        fresh_zero = zero.carried.condition.sides[1].entries[0]
        self.assertEqual((fresh_zero.effective_damage_raw, fresh_zero.state.toughness_raw), (0, 0))
        self.assert_preserved_accounts(before, zero.carried)

        day = replace(_day(0), phase_events=(
            {"event_key": "commander_wounded"}, {"event_key": "knight_become_berserker"}))
        partial = run_selected_phase_feedback_horizon_12003(
            condition, day=day, selected=(known, unknown), draw_state=before.draw_state)
        self.assertTrue(partial.event_tape_consumed)
        self.assertEqual(partial.horizon.status, "partial")
        self.assertEqual(partial.horizon.final_state.condition.sides[1].entries[0].effective_damage_raw, 287_500_000)
        self.assertEqual(partial.horizon.final_state.draw_state, before.draw_state)
        self.assertEqual(partial.horizon.final_state.simulated_main_ticks, 0)

        one_event_day = replace(day, phase_events=({"event_key": "commander_wounded"},))
        not_admitted_day = replace(one_event_day, admission=replace(day.admission, date_stage_executed=False))
        not_admitted = run_selected_phase_feedback_horizon_12003(
            condition, day=not_admitted_day, selected=(known,), draw_state=before.draw_state)
        self.assertFalse(not_admitted.event_tape_consumed)
        self.assertIsNone(not_admitted.feedback)
        self.assertEqual(not_admitted.horizon.final_state.condition, condition)
        self.assertEqual(not_admitted.horizon.final_state.draw_state, before.draw_state)

        forced_source = dict(condition.source_snapshot, forced_winner_raw=0)
        forced = replace(condition, source_snapshot=forced_source)
        forced_day = replace(one_event_day, transition=replace(day.transition, forced_winner_raw=0))
        exited = run_selected_phase_feedback_horizon_12003(
            forced, day=forced_day, selected=(known,), draw_state=before.draw_state)
        self.assertFalse(exited.event_tape_consumed)
        self.assertIsNone(exited.feedback)
        self.assertEqual(exited.horizon.final_state.draw_state, before.draw_state)
        self.captured_results.append({
            "case": "mixed_unknown_known_preserved_and_admission_gates",
            "known_base_prowess_after_raw": 21 * Q,
            "known_cached_damage_raw": 287_500_000,
            "unknown_leaf": "knight_become_berserker",
            "missing_effective_operand_preserves_prior_cache": True,
            "zero_effective_points_clamp_damage_toughness_raw": [12_500_000, 1_250_000],
            "legal_zero_cached_damage_toughness_raw": [0, 0],
            "partial_horizon_draw_counter": partial.horizon.final_state.draw_state.counter,
            "not_admitted_tape_consumed": not_admitted.event_tape_consumed,
            "forced_exit_tape_consumed": exited.event_tape_consumed,
        })

    def assert_preserved_accounts(self, before, after):
        self.assertEqual(after.draw_state, before.draw_state)
        self.assertEqual(after.origin_observed_frame, before.origin_observed_frame)
        self.assertEqual(after.condition.source_snapshot, before.condition.source_snapshot)
        self.assertEqual(after.condition.snapshot_revision, before.condition.snapshot_revision)
        self.assertEqual(after.condition.observed_date_raw, before.condition.observed_date_raw)
        self.assertEqual(after.condition.phase_day, before.condition.phase_day)
        for original_side, fresh_side in zip(before.condition.sides, after.condition.sides):
            self.assertEqual(fresh_side.ordered_armies, original_side.ordered_armies)
            self.assertEqual(fresh_side.participant_hard_ledger, original_side.participant_hard_ledger)
            self.assertEqual(fresh_side.participant_hard_total_raw, original_side.participant_hard_total_raw)
            for old, new in zip(original_side.entries, fresh_side.entries):
                self.assertEqual((new.bucket, new.bucket_index, new.native_carmy_id, new.public_cunit_id,
                                  new.owner_character_id, new.state.regiment_id),
                                 (old.bucket, old.bucket_index, old.native_carmy_id, old.public_cunit_id,
                                  old.owner_character_id, old.state.regiment_id))
                self.assertEqual((new.starting_raw, new.state.current_raw, new.state.soft_casualties_raw,
                                  new.hard_casualties_raw, new.backing_components),
                                 (old.starting_raw, old.state.current_raw, old.state.soft_casualties_raw,
                                  old.hard_casualties_raw, old.backing_components))


if __name__ == "__main__":
    unittest.main()
