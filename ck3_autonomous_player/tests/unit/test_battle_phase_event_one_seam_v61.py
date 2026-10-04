"""One new source-derived accolade-event seam; independent offline inputs."""

from __future__ import annotations

import copy
from dataclasses import replace
import unittest

from xar_autoplayer.simulation.battle_calendar_admission import DailyDateStageInput, LoadedScheduleInputs
from xar_autoplayer.simulation.battle_current_adapter import (
    CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide, CurrentLossInputs, CurrentLossSideInputs,
)
from xar_autoplayer.simulation.battle_current_conditional_horizon import ConditionalHorizonDay
from xar_autoplayer.simulation.battle_current_future_refresh import (
    CommanderCandidateInputs, FutureCommanderSideInputs, FutureMainRefreshInputs,
    FutureMainScope, RelationModifierInputs,
)
from xar_autoplayer.simulation.battle_current_next_day import CarriedBattleCondition
from xar_autoplayer.simulation.battle_current_phase_transition import CurrentMainPhaseTransitionInputs
from xar_autoplayer.simulation.battle_phase_event_feedback_12003 import (
    SelectedPhaseEventInput12003, apply_selected_phase_event_feedback_12003,
    run_selected_phase_feedback_horizon_12003,
)
from xar_autoplayer.simulation.battle_phase_events_12003 import PhaseEventScriptOutcome12003
from xar_autoplayer.simulation.battle_phase_event_one_seam_12003 import (
    AccoladeQualificationInputs12003, ScriptBooleanVariableState12003, ScriptNumericVariableState12003,
)
from xar_autoplayer.simulation.combat_core import (
    BackingComponent, CombatRegimentState, CommanderRollRequest, DrawState, RegimentKind,
)


Q = 100_000
ROOT = 29_829
ENEMY = 900_001
LIEGE = 900_002
COMBAT = 335_544_325
DATE = 53_178_264
EVENT = "knight_qualify_for_accolade"
ATTRIBUTES = ("skirmisher", "archer", "crossbowmen", "pike", "vanguard", "outrider", "lancer",
              "camelry", "elephantry", "horse_archer", "gunpowder", "fanatic", "valiant")
BASE_TYPES = ("skirmishers", "archers", "pikemen", "heavy_infantry", "light_cavalry", "heavy_cavalry",
              "camel_cavalry", "elephant_cavalry", "archer_cavalry", "gunpowder")
ANY_TYPES = tuple(key for key in BASE_TYPES if key != "archers")


def _source(condition):
    return {"combat_id": condition.combat_id, "snapshot_revision": condition.snapshot_revision,
            "observed_date_raw": condition.observed_date_raw,
            "root_source_native_carmy_id": 101, "root_source_public_cunit_id": 83_886_341,
            "modeled_dispatch_date_raw": DATE + 24,
            "source": "independent_synthetic_one_event_fixture_no_actual_frame_claim"}


def _context():
    refs = {
        "root.exists": True, "root.alive": True, "root.skills.prowess_raw": 12 * Q,
        "root.traits.wounded.rank_raw": 0, "root.traits.fragile_bones.rank_raw": 0,
        "root.traits.fragile_bones.xp_raw": 0, "root.traits.one_legged": False,
        "root.traits.disfigured": False, "root.traits.one_eyed": False,
        "root.traits.maimed": False, "root.court_positions.garuda": False,
        "root.traits_and_culture_for_blademaster": {
            "education_martial": [False] * 5, "education_martial_prowess": [False] * 4,
            "intellect_good": [False] * 3, "lifestyle_blademaster": False,
            "lifestyle_blademaster_xp_raw": 0, "shrewd": False, "physique_good": False,
            "culture_blademaster_traits_more_common": False},
        "combat_side.character_membership": [ROOT, LIEGE],
        "enemy_side.character_membership": [ENEMY],
        "combat_side.ordered_enemy_knights": [], "combat_side.commander": LIEGE,
        "derived.knight_army_has_nonzero_maa": True,
        "root.can_be_acclaimed": True, "root.accolade_prowess_requirement_raw": 8 * Q,
        "root.knight_army.maa_regiment_count_raw": 3 * Q,
        "root.liege.full_character_id": LIEGE, "root.liege.scope_present": True,
        "root.liege.variables.accolade_progress": {"present": True, "value_raw": 4 * Q},
        # Chance alias differs from stored variable, so it cannot supply the before numeric delta.
        "root.liege.accolade_progress_raw": 99 * Q,
    }
    refs.update({f"root.variables.{attribute}_attribute_unlock": {"present": True, "value": False}
                 for attribute in ATTRIBUTES})
    return {"root_character_id": ROOT, "root_source_army_id": 83_886_341, "root_source_regiment_id": 81,
            "phase_roles": ["knight"],
            "combat_side_index": 0, "enemy_side_index": 1,
            "native_state_refs": refs, "offline_state_refs": {}, "candidate_rows": []}


def _entry(regiment, native, public, owner, index, knight=None):
    component = BackingComponent(1, 1)
    return CurrentBattleEntry(
        state=CombatRegimentState(regiment, RegimentKind.MEN_AT_ARMS, Q, 0, Q,
                                  pursuit_raw=0, screen_raw=0, components=(component,)),
        bucket="men_at_arms", bucket_index=index, native_carmy_id=native,
        public_cunit_id=public, owner_character_id=owner, starting_raw=Q,
        effective_damage_raw=0, fights_in_main_phase=True, hard_casualties_raw=0,
        knight_character_id_raw=knight, backing_components=(component,),
        source_entry={"regiment_id": regiment, "current_fighting_raw": Q,
                      "effective_damage_raw": 0, "effective_toughness_raw": Q})


def _condition():
    loss_sides = tuple(CurrentLossSideInputs(i, Q, 0, 0, actor, 0)
                       for i, actor in enumerate((LIEGE, ENEMY)))
    loss = CurrentLossInputs(Q, COMBAT, 2586, Q, Q, 50_000, Q, False, 0, loss_sides)
    sides = []
    counter_sides = []
    for i, (native, public, owner, regiment_ids) in enumerate(
            ((101, 83_886_341, LIEGE, (81, 82, 83, 84)), (303, 33_554_657, ENEMY, (99,)))):
        entries = tuple(_entry(regiment, native, public, owner, index,
                               ROOT if i == 0 and index == 0 else None)
                        for index, regiment in enumerate(regiment_ids))
        total = len(entries) * Q
        army = {"native_carmy_id": native, "public_cunit_id": public,
                "owner_character_id": owner, "combat_backlink_id": COMBAT}
        sides.append(CurrentBattleSide(
            side_index=i, role="attacker" if i == 0 else "defender",
            primary_participant_character_id=owner, selected_commander_character_id=owner,
            current_roll_points=0, roll_request=CommanderRollRequest(True, 0, 0, previous_roll=0),
            entries=entries, ordered_armies=(army,), stored_current_fighting_raw=total,
            stored_levy_current_fighting_raw=0, derived_current_fighting_raw=total,
            derived_soft_casualties_raw=0, derived_main_fighting_entry_hard_casualties_raw=0,
            non_main_start_minus_current_minus_soft_raw=0,
            participant_hard_ledger=({"row_index": 0, "participant_character_id": owner,
                                      "hard_casualties_raw": 0},), participant_hard_total_raw=0,
            loss_inputs=loss_sides[i], levy_damage_raw=0,
            levy_damage_source="fixture_explicit_zero_primary_levy_damage", levy_damage_native_observed=False,
            levy_damage_primary_participant_character_id=owner))
        counter_sides.append({"side_index": i, "men_at_arms_entries": [
            {"regiment_id": entry.state.regiment_id, "native_carmy_id": native,
             "status": "available", "current_fighting_raw": Q,
             "current_chunk_raw": Q, "stack_size_soldiers": 1, "class_index": 0, "targets": []}
            for entry in entries]})
    counter = {"status": "available", "operand_census_complete": True, "class_count": 1,
               "sides": counter_sides, "contexts": [
                   {"countered_side_index": i, "countering_side_index": 1-i,
                    "context_scale_raw": Q} for i in range(2)]}
    return CurrentBattleCondition(
        snapshot_revision=7, observed_date_raw=DATE, combat_id=COMBAT, province_id=2586,
        subject_side_index=0, side_scope="full_side", phase="main", phase_raw=1, phase_day=4,
        base_combat_width=10, final_combat_width=10, roll_cadence_counter=0,
        base_advantage_raw=0, resolved_advantage_raw=0, sides=tuple(sides), loss_inputs=loss,
        active_counter_inputs=counter, pursuit_modifier_sides=None, missing_inputs=(),
        source_snapshot={"snapshot_revision": 7, "observed_date_raw": DATE, "combat_id": COMBAT,
                         "forced_winner_raw": -1, "roll_cadence_interval": 5,
                         "current_loss_inputs_v1": {"runtime_advantage_scaling_raw": Q},
                         "source": "independent_synthetic_current_state_not_live"})


def _future():
    relation = RelationModifierInputs(
        generic_raw=0, role_raw=0, terrain_raw=0, target_definition_applies=False,
        target_definition_raw=0, holding_applies=False, holding_raw=0,
        opposing_effect_modifier_raw=0, opposing_effect_rows=(), relation_kind_raw=0, relation_raw=0,
        source_label="fixture_explicit_zero_stable_relation_inputs")
    sides = tuple(FutureCommanderSideInputs(
        candidates=(CommanderCandidateInputs(
            candidate_character_id=actor, effective_martial=1,
            opaque_opposing_primary_raw=0, opaque_province_context_raw=0,
            character_relation_inputs=relation, source_label="fixture_complete_single_commander_census",
            army_1ae_present=False, army_1ae_raw=0, army_1ae_gate=False,
            primary_identity_modifier_raw=0, side_gathering=False,
            candidate_has_flag_1a5=False, loaded_gathering_points=0,
            roll_request=CommanderRollRequest(True, 0, 0, previous_roll=0)),),
        candidate_census_complete=True, side_relation_inputs=relation,
        source_label="fixture_conditional_unchanged_direct_combat_context")
        for actor in (LIEGE, ENEMY))
    return FutureMainRefreshInputs(
        scope=FutureMainScope(True, True, True, True, True, True, True, True, 1),
        side_inputs=sides, modeled_tick_index=1, roll_cadence_interval=5,
        roll_cadence_interval_source="fixture_explicit_loaded_interval5",
        loaded_advantage_scaling_raw=Q, loaded_advantage_scaling_source="fixture_explicit_current_loaded_Q",
        resolve_boundary="after_modeled_due_rolls")


def _day():
    return ConditionalHorizonDay(
        admission=DailyDateStageInput(DATE, True, "synthetic_conditional_date_stage", endpoint_paused=True),
        loaded=LoadedScheduleInputs(maneuver_days=None, roll_cadence_interval=5,
                                    source="fixture_explicit_loaded_schedule"),
        source_context={"source": "independent_new_event_single_day_fixture"}, entry_events=(),
        phase_events=({"event_key": EVENT},), ai_context={"action_selected": False},
        future_main=_future(), transition=CurrentMainPhaseTransitionInputs(forced_winner_raw=-1))


def _carried(condition):
    return CarriedBattleCondition(
        condition, DrawState(13, 17), "independent_selected_accolade_event_fixture", (), 0,
        _source(condition), tuple({"side_index": side.side_index,
                                  "stored_current_fighting_raw": side.stored_current_fighting_raw,
                                  "participant_hard_total_raw": side.participant_hard_total_raw}
                                 for side in condition.sides))


def _inputs(*, count=3, fixed=True):
    return AccoladeQualificationInputs12003(
        liege_full_character_id=LIEGE, liege_scope_present=True,
        liege_accolade_progress=ScriptNumericVariableState12003(True, 4 * Q),
        root_unlock_variables={f"{attribute}_attribute_unlock": ScriptBooleanVariableState12003(True, False)
                               for attribute in ATTRIBUTES},
        count_base_by_type={key: count if key == "skirmishers" else 0 for key in BASE_TYPES},
        count_exact_type={key: 0 for key in ("crossbowmen", "shenbigong", "accolade_maa_crossbowers")},
        total_army_maa_regiment_count=3,
        any_unit_type={key: key == "skirmishers" for key in ANY_TYPES},
        any_non_crossbow_archer=False, any_crossbow_variant=False,
        attribute_trigger_by_attribute={key: False for key in ATTRIBUTES},
        enemy_any_faith_hostility_at_least_evil=False,
        # These independent script-size queries are explicitly not substituted from combat Q troop accounts.
        own_side_army_size_raw=100 * Q, enemy_side_army_size_raw=1000 * Q,
        fixed_current_combat_context=fixed)


def _selected(condition, inputs, *, branch=0):
    tape = (() if branch is None else (PhaseEventScriptOutcome12003(
        purpose=f"{EVENT}:attribute_unlock:source_order", branch_index=branch),))
    return SelectedPhaseEventInput12003(
        context=_context(), event_key=EVENT, script_outcomes=tape,
        source_context=_source(condition), one_seam_inputs=inputs)


def _delta(result, actor, field):
    return next(row for row in result.character_numeric_deltas
                if row["character_id"] == actor and row["field"] == field)


class BattlePhaseEventOneSeamV61FixtureTests(unittest.TestCase):
    captured_results = []

    def test_accolade_prefix_and_selected_unlock_enter_typed_horizon_only_when_complete(self):
        condition = _condition()
        before = _carried(condition)
        positive = _selected(condition, _inputs())
        original_context = copy.deepcopy(positive.context)
        result = apply_selected_phase_event_feedback_12003(before, selected=(positive,))
        reset = _delta(result, LIEGE, "accolade_progress")
        unlock = _delta(result, ROOT, "skirmisher_attribute_unlock")
        self.assertEqual((reset["before"], reset["after"], reset["delta_raw"]), (4 * Q, 0, -4 * Q))
        self.assertEqual(reset["unit"], "script_variable_Q100000")
        self.assertEqual((unlock["before"], unlock["after"], unlock["delta_raw"]), (False, True, None))
        self.assertEqual(unlock["unit"], "script_variable_boolean")
        execution = result.executions[0]
        self.assertEqual(execution["branch_weights_raw"], [30 * Q] + [0] * 12)
        self.assertEqual(execution["after_state"]["root"]["variable_updates"], {"skirmisher_attribute_unlock": True})
        self.assertEqual(execution["after_state"]["root"]["liege_variable_updates"], {"accolade_progress": 0})
        self.assertEqual(result.carried, before)
        self.assertTrue(result.event_execution_consumed)
        self.assertTrue(result.feedback_ready, result.typed_gaps)
        self.assertEqual(result.typed_gaps, ())
        self.assertFalse(result.full_script_feedback_ready)
        self.assertEqual(positive.context, original_context)

        continued = run_selected_phase_feedback_horizon_12003(
            condition, day=_day(), selected=(positive,), draw_state=before.draw_state,
            caller_seed_provenance={"source": "caller_owned_synthetic_stream", "native_rng": False})
        self.assertTrue(continued.event_tape_consumed)
        self.assertEqual(continued.horizon.status, "available", continued.horizon.typed_gaps)
        self.assertEqual(continued.horizon.modeled_accepted_invocations, 1)
        self.assertEqual(continued.horizon.modeled_date_raw, DATE + 24)
        final = continued.horizon.final_state.condition
        self.assertEqual((final.phase_raw, final.phase_day, final.roll_cadence_counter), (1, 5, 1))
        self.assertEqual(continued.horizon.final_state.draw_state, DrawState(15, 17))
        self.assertEqual(final.source_snapshot, condition.source_snapshot)
        for old_side, fresh_side in zip(condition.sides, final.sides):
            self.assertEqual(fresh_side.entries, old_side.entries)
            self.assertEqual(fresh_side.participant_hard_total_raw, 0)
            self.assertEqual(fresh_side.selected_commander_character_id, old_side.selected_commander_character_id)
        tick = next(stage["result"] for stage in continued.horizon.trace[0]["stages"]
                    if stage["stage"] == "future_main_and_internal_P2_carry")
        self.assertEqual(tick.result["outgoing_damage_raw_by_side"], [0, 0])

        zero_selected = _selected(condition, _inputs(count=0), branch=None)
        zero = apply_selected_phase_event_feedback_12003(before, selected=(zero_selected,))
        zero_reset = _delta(zero, LIEGE, "accolade_progress")
        self.assertEqual((zero_reset["after"], zero_reset["delta_raw"]), (0, -4 * Q))
        self.assertEqual(zero.executions[0]["branch_weights_raw"], [0] * 13)
        self.assertEqual(zero.executions[0]["after_state"]["root"]["variable_updates"], {})
        self.assertFalse(zero.feedback_ready)
        self.assertTrue(zero.typed_gaps)
        self.assertEqual(zero.carried, before)
        stopped = run_selected_phase_feedback_horizon_12003(
            condition, day=_day(), selected=(zero_selected,), draw_state=before.draw_state)
        self.assertEqual(stopped.horizon.status, "partial")
        self.assertTrue(stopped.event_tape_consumed)
        self.assertEqual(stopped.horizon.final_state.draw_state, before.draw_state)
        self.assertEqual(stopped.horizon.final_state.simulated_main_ticks, 0)
        self.assertEqual(_delta(stopped.feedback, LIEGE, "accolade_progress")["after"], 0)

        incomplete = apply_selected_phase_event_feedback_12003(
            before, selected=(_selected(condition, _inputs(fixed=None)),))
        self.assertEqual(_delta(incomplete, LIEGE, "accolade_progress")["after"], 0)
        self.assertEqual(_delta(incomplete, ROOT, "skirmisher_attribute_unlock")["after"], True)
        self.assertFalse(incomplete.feedback_ready)
        self.assertIn("fixed_current_combat_context", repr(incomplete.typed_gaps))
        self.assertEqual(incomplete.carried, before)
        self.captured_results.append({
            "case": "knight_accolade_selected_and_prefix_partial_source_seam",
            "source_branch_count": 13, "selected_branch_index": 0,
            "branch_weights_raw": execution["branch_weights_raw"],
            "stored_progress_before_after_delta_raw": [reset["before"], reset["after"], reset["delta_raw"]],
            "chance_alias_raw_unused_as_storage": 99 * Q,
            "root_unlock_before_after": [unlock["before"], unlock["after"]],
            "positive_feedback_ready": result.feedback_ready,
            "horizon_accepted_invocations": continued.horizon.modeled_accepted_invocations,
            "horizon_phase_day_cadence": [final.phase_day, final.roll_cadence_counter],
            "current_entry_accounts_unchanged": True,
            "all_zero_progress_after_raw": zero_reset["after"],
            "all_zero_feedback_ready": zero.feedback_ready,
            "all_zero_horizon_status": stopped.horizon.status,
            "all_zero_horizon_draw_counter": stopped.horizon.final_state.draw_state.counter,
            "missing_explicit_fixed_context_feedback_ready": incomplete.feedback_ready,
            "full_script_feedback_ready": result.full_script_feedback_ready,
        })


if __name__ == "__main__":
    unittest.main()
