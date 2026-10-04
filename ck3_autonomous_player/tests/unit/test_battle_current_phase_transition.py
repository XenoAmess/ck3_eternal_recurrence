from __future__ import annotations

from dataclasses import replace
import unittest

from xar_autoplayer.simulation.battle_current_adapter import (
    CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide,
    CurrentLossInputs, CurrentLossSideInputs,
)
from xar_autoplayer.simulation.battle_current_phase_transition import (
    CurrentAutomaticRetreatInputs, CurrentMainPhaseTransitionInputs,
    project_current_main_phase_transition,
)
from xar_autoplayer.simulation.battle_current_pursuit import (
    CurrentPursuitSourceContext, run_current_pursuit_ticks,
)
from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick
from xar_autoplayer.simulation.combat_core import (
    CombatRegimentState, DrawState, RegimentKind,
)


Q = 100_000
EPOCH = 0x029C55C0


def _entry(side: int, regiment: int, index: int, current: int, soft: int,
           *, kind: RegimentKind = RegimentKind.LEVY,
           eligible: bool = True) -> CurrentBattleEntry:
    return CurrentBattleEntry(
        state=CombatRegimentState(regiment, kind, current, soft, Q,
                                  pursuit_raw=0, screen_raw=0),
        bucket=kind.value, bucket_index=index, native_carmy_id=101+side,
        public_cunit_id=83_886_341+side,
        owner_character_id=29_829 if side == 0 else 36_108,
        starting_raw=current+soft, effective_damage_raw=Q,
        fights_in_main_phase=eligible, hard_casualties_raw=0,
        knight_character_id_raw=None, backing_components=None,
        source_entry={"regiment_id": regiment, "current_fighting_raw": current,
                      "soft_casualties_raw": soft},
    )


def _side(index: int, entries: tuple[CurrentBattleEntry, ...], *,
          loss: CurrentLossSideInputs | None = None,
          cached: int | None = None, levy_damage: int | None = None) -> CurrentBattleSide:
    owner = 29_829 if index == 0 else 36_108
    current = sum(entry.state.current_raw for entry in entries)
    levy = sum(entry.state.current_raw for entry in entries
               if entry.state.kind is RegimentKind.LEVY)
    armies = ({"native_carmy_id": 101+index,
               "public_cunit_id": 83_886_341+index,
               "owner_character_id": owner, "combat_backlink_id": 335_544_325},)
    if index == 1:
        armies += ({"native_carmy_id": 103, "public_cunit_id": 83_886_343,
                    "owner_character_id": 36_109,
                    "combat_backlink_id": 335_544_325},)
    return CurrentBattleSide(
        side_index=index, role="attacker" if index == 0 else "defender",
        primary_participant_character_id=owner,
        selected_commander_character_id=-1, current_roll_points=0,
        roll_request=None, entries=entries, ordered_armies=armies,
        stored_current_fighting_raw=current if cached is None else cached,
        stored_levy_current_fighting_raw=levy if cached is None else cached,
        derived_current_fighting_raw=current,
        derived_soft_casualties_raw=sum(entry.state.soft_casualties_raw for entry in entries),
        derived_main_fighting_entry_hard_casualties_raw=0,
        non_main_start_minus_current_minus_soft_raw=0,
        participant_hard_ledger=({"row_index": 0,
                                  "participant_character_id": owner,
                                  "hard_casualties_raw": 0},),
        participant_hard_total_raw=0, loss_inputs=loss,
        levy_damage_raw=levy_damage,
        levy_damage_source="current_loss_inputs_v1.native_primary_levy_damage",
        levy_damage_native_observed=levy_damage is not None,
        levy_damage_primary_participant_character_id=owner if levy_damage is not None else None,
    )


def _condition(sides: tuple[CurrentBattleSide, CurrentBattleSide],
               loss: CurrentLossInputs | None = None) -> CurrentBattleCondition:
    return CurrentBattleCondition(
        snapshot_revision=58, observed_date_raw=EPOCH+23,
        combat_id=335_544_325, province_id=2586,
        subject_side_index=1, side_scope="full_side", phase="main", phase_raw=1,
        phase_day=4, base_combat_width=10, final_combat_width=10,
        roll_cadence_counter=3, base_advantage_raw=0, resolved_advantage_raw=0,
        sides=sides, loss_inputs=loss, active_counter_inputs=None,
        pursuit_modifier_sides={
            "status": "available", "scale": Q,
            "source_combat_id": 335_544_325, "source_target_province_id": 2586,
            "unavailable_reason": None,
            "sides": [{"side_index": index,
                       "encounter_role": "attacker" if index == 0 else "defender",
                       "pursuit_efficiency_raw": 0, "retreat_losses_raw": 0}
                      for index in (0, 1)],
        },
        missing_inputs=(),
        source_snapshot={"forced_winner_raw": -1, "winner_raw": -1,
                         "side_flags": {"skip_pursuit": False}},
    )


class CurrentMainPhaseTransitionFocusedTests(unittest.TestCase):
    def test_complete_entry_refresh_keeps_positive_sides_in_main_without_winner(self):
        condition = _condition(tuple(
            _side(index, (
                _entry(index, 90+index, 0, Q+3+4*index, 0, eligible=False),
                _entry(index, 70+index, 0, Q+5+6*index, 0,
                       kind=RegimentKind.MEN_AT_ARMS, eligible=False),
            ), cached=0)
            for index in (0, 1)
        ))
        result = project_current_main_phase_transition(condition)
        self.assertEqual((result["status"], result["branch"]), ("available", "continue_main"))
        self.assertIsNone(result["winner_side"])
        self.assertIsNone(result["loser_side"])
        self.assertIsNone(result["pursuit_start_condition"])
        self.assertIsNone(result["normal_result_intent"])
        self.assertEqual(result["forced_winner_raw"], -1)
        self.assertEqual(result["forced_winner_source"], "source_snapshot.forced_winner_raw")
        self.assertEqual([row["source_stored_current_fighting_raw"]
                          for row in result["refreshed_sides"]], [0, 0])
        self.assertEqual([row["refreshed_current_fighting_raw"]
                          for row in result["refreshed_sides"]], [200_008, 200_018])
        self.assertEqual([row["refreshed_levy_current_fighting_raw"]
                          for row in result["refreshed_sides"]], [100_003, 100_007])
        for row in result["refreshed_sides"]:
            self.assertFalse(row["main_eligibility_filters_refresh"])
        self.assertEqual(result["modeled_accepted_invocation_offset"], 1)
        self.assertEqual(result["dispatched_phase_day"], 5)
        self.assertEqual(result["transition_condition"].phase_raw, 1)
        self.assertEqual(condition.phase_day, 4)
        # Unknown Combat+700 differs from the observed native -1 sentinel.
        unknown = project_current_main_phase_transition(
            replace(condition, source_snapshot={"side_flags": {"skip_pursuit": False}}))
        self.assertEqual((unknown["status"], unknown["branch"]),
                         ("partial", "forced_winner_unobserved"))
        self.assertIsNone(unknown["winner_side"])

    def test_real_main_result_carries_once_then_initializes_and_runs_pursuit(self):
        side_loss = (CurrentLossSideInputs(0, Q, 0, 0),
                     CurrentLossSideInputs(1, Q, 0, 0))
        loss = CurrentLossInputs(
            Q, 335_544_325, 2586, Q, Q, 0, 25_000, False, 0, side_loss)
        condition = _condition((
            _side(0, (_entry(0, 1, 0, 1_000_000, 0),),
                  loss=side_loss[0], levy_damage=Q),
            _side(1, (_entry(1, 99, 0, 100_000, 100_007),
                      _entry(1, 7, 1, 100_000, 50_009)),
                  loss=side_loss[1], levy_damage=0),
        ), loss)
        main = run_frozen_main_tick(condition, draw_state=DrawState(15, 7))
        self.assertEqual(main["status"], "available")
        self.assertEqual([row["current_fighting_raw_after"]
                          for row in main["sides"][1]["losses"]["entries"]], [0, 0])
        self.assertFalse(main["complete_transition"])
        witness = {"kind": "explicit_dispatch_fixture", "native_carmy_id": 102,
                   "native_third_argument": None}
        inputs = CurrentMainPhaseTransitionInputs(
            automatic_retreat_inputs=CurrentAutomaticRetreatInputs(
                disallowed=False, allow_early=False, result_start_date_raw=EPOCH+23,
                minimum_elapsed_days=2, owner_land_rule_allows=True,
                source_context=witness),
            dispatch_date_raw=EPOCH+72,
            pursuit_rules=CurrentPursuitSourceContext(
                pursuit_phase_days=3, pursuit_stat_multiplier_raw=0,
                base_toughness_multiplier_raw=0, minimum_pursuit_multiplier_raw=Q,
                source_context={"kind": "explicit_loaded_rules_fixture"}),
            source_context=witness,
        )
        result = project_current_main_phase_transition(condition, main, inputs=inputs)
        self.assertEqual((result["status"], result["branch"]), ("available", "pursuit_started"))
        self.assertEqual((result["winner_side"], result["loser_side"]), (0, 1))
        self.assertEqual(result["winner_source"], "refreshed_side1_nonpositive")
        self.assertEqual(result["timing"],
                         "following_accepted_main_entry_after_completed_P1_transfer")
        self.assertEqual((result["modeled_accepted_invocation_offset"],
                          result["dispatched_phase_day"]), (2, 6))
        self.assertFalse(result["same_completed_main_tick_exit"])
        self.assertEqual(result["refreshed_sides"][1]["source_stored_current_fighting_raw"],
                         200_000)
        self.assertEqual(result["refreshed_sides"][1]["refreshed_current_fighting_raw"], 0)
        self.assertEqual(result["losing_first_army"]["native_carmy_id"], 102)
        self.assertEqual(result["automatic_permission_details"]["elapsed_whole_days"], 3)
        self.assertEqual(result["automatic_permission_details"]["minimum_elapsed_days"], 2)
        self.assertTrue(result["losing_first_army_can_enter_pursuit"])
        self.assertEqual(result["losing_side_skip_pursuit_source"],
                         "source_snapshot.side_flags.skip_pursuit (subject is loser)")
        start = result["pursuit_start_condition"]
        self.assertEqual((start.phase_raw, start.phase_day), (2, 0))
        self.assertEqual(result["initial_loser_levy_soft_raw"], 350_016)
        self.assertEqual(result["initial_loser_maa_soft_raw"], 0)
        self.assertEqual(result["pursuit_inputs"].initial_pools.levy_soft_raw, 350_016)
        self.assertEqual([entry.state.soft_casualties_raw for entry in start.sides[1].entries],
                         [200_007, 150_009])
        self.assertEqual(start.source_snapshot, condition.source_snapshot)
        self.assertEqual(start.sides[1].entries[0].source_entry["current_fighting_raw"],
                         100_000)
        self.assertEqual(start.observed_date_raw, condition.observed_date_raw)
        self.assertEqual(start.snapshot_revision, condition.snapshot_revision)
        pursuit = run_current_pursuit_ticks(start, inputs=result["pursuit_inputs"], max_ticks=1)
        self.assertEqual((pursuit["status"], pursuit["ticks"][0]["branch"]),
                         ("available", "pursuit_casualties"))
        self.assertEqual(pursuit["new_hard_casualties_raw"], 29_167)
        self.assertEqual([row["soft_casualties_raw_after"]
                          for row in pursuit["ticks"][0]["entries"]], [183_340, 137_509])
        self.assertEqual(pursuit["updated_condition"].sides[1].participant_hard_total_raw,
                         29_167)
        self.assertIsNone(result["normal_result_intent"])
        # Actual loser skip finishes synchronously; normal intent is supplied
        # for this branch rather than inferred from phase3 alone.
        skipped = project_current_main_phase_transition(
            replace(condition, source_snapshot=dict(condition.source_snapshot,
                    side_flags={"skip_pursuit": True})), main,
            inputs=replace(inputs, normal_result_intent=True))
        self.assertEqual(skipped["branch"], "pursuit_skipped_synchronously")
        self.assertEqual((skipped["transition_condition"].phase_raw,
                          skipped["transition_condition"].phase_day), (3, 0))
        self.assertTrue(skipped["normal_result_intent"])
        self.assertEqual([entry.state.soft_casualties_raw
                          for entry in skipped["transition_condition"].sides[1].entries],
                         [200_007, 150_009])
        for key in ("complete_monte_carlo", "ai_retreat_decision_predicted",
                    "same_completed_main_tick_exit"):
            self.assertFalse(result[key])
        self.assertEqual(result["actual_game_days_advanced"], 0)
        self.assertEqual([entry.state.current_raw for entry in condition.sides[1].entries],
                         [100_000, 100_000])
