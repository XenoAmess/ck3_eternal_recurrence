from __future__ import annotations

from dataclasses import replace
import unittest

from xar_autoplayer.bridge.battle_control_contract import (
    normalize_active_combat_resume_inputs_v1,
    normalize_battle_control_snapshot_v1,
)
from xar_autoplayer.simulation.battle_calendar_admission import DailyDateStageInput, LoadedScheduleInputs
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_conditional_horizon import (
    ConditionalHorizonDay, ConditionalTerminalInputs, run_conditional_horizon,
)
from xar_autoplayer.simulation.battle_current_future_refresh import (
    CommanderCandidateInputs, FutureCommanderSideInputs, FutureMainRefreshInputs,
    FutureMainScope, RelationModifierInputs,
)
from xar_autoplayer.simulation.battle_current_phase_transition import (
    CurrentAutomaticRetreatInputs, CurrentMainPhaseTransitionInputs,
)
from xar_autoplayer.simulation.battle_current_pursuit import CurrentPursuitSourceContext
from xar_autoplayer.simulation.combat_core import BackingComponent, CommanderRollRequest, DrawState


Q = 100_000
SUBJECT = 83_886_341
COMBAT = 335_544_325
DATE = 53_178_264


def _army(native, public, owner):
    return {"native_carmy_id": native, "public_cunit_id": public,
            "owner_character_id": owner, "combat_backlink_id": COMBAT}


def _entry(regiment, army, *, index, current, damage):
    return {
        "bucket": "levy", "bucket_index": index, "regiment_id": regiment,
        "native_carmy_id": army["native_carmy_id"], "public_cunit_id": army["public_cunit_id"],
        "owner_character_id": army["owner_character_id"], "starting_raw": current,
        "current_fighting_raw": current, "soft_casualties_raw": 0, "fights_in_main_phase": True,
        "hard_casualties_status": "available", "hard_casualties_raw": 0,
        "hard_casualties_source": "derived_starting_minus_current_minus_soft",
        "hard_casualties_unavailable_reason": None, "effective_max_size": 100,
        "effective_siege_raw": 0, "effective_damage_raw": damage, "effective_toughness_raw": Q,
        "effective_pursuit_raw": 0, "effective_screen_raw": 0, "entry_strength_raw": 0,
    }


def _side(index, armies, entries):
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": armies[0]["owner_character_id"],
        "selected_commander_character_id": armies[0]["owner_character_id"],
        "current_roll_points": 0, "ordered_armies": armies, "levy_entries": entries,
        "men_at_arms_entries": [], "stored_current_fighting_raw": 10_000_000,
        "stored_levy_current_fighting_raw": 10_000_000,
        "stored_current_matches_derived": True, "stored_levy_current_matches_derived": True,
        "derived_current_fighting_raw": 10_000_000, "derived_soft_casualties_raw": 0,
        "derived_main_fighting_entry_hard_casualties_raw": 0,
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": [
            {"row_index": i, "participant_character_id": army["owner_character_id"], "hard_casualties_raw": 0}
            for i, army in enumerate(armies)
        ], "participant_hard_total_raw": 0, "side_strength_raw": 0, "side_strength_scale": Q,
    }


def _initial_condition(*, damage_scaling=Q):
    own = _army(101, SUBJECT, 29_829)
    enemy_a = _army(303, 33_554_657, 36_109)
    enemy_b = _army(202, 357, 36_108)
    attacker = _side(0, [own], [_entry(81, own, index=0, current=10_000_000, damage=Q)])
    defender = _side(1, [enemy_a, enemy_b], [
        _entry(99, enemy_a, index=0, current=5_000_000, damage=0),
        _entry(3, enemy_b, index=1, current=5_000_000, damage=0),
    ])
    frame = {
        "schema_version": 1, "contract_stage": "production_exact_ongoing_combat",
        "status": "available", "battle_control_ready": True,
        "snapshot_revision": 7, "observed_date_raw": DATE,
        "subject_public_cunit_id": SUBJECT, "subject_native_carmy_id": 101,
        "combat_id": COMBAT, "province_id": 2586,
        "selected_public_cunit_id": SUBJECT, "selected_native_carmy_id": 101,
        "selected_owner_character_id": 29_829, "combat_province_id": 2586,
        "side_index": 0, "side_scope": "full_side",
        "affected_public_cunit_ids_in_stored_order": [SUBJECT],
        "unaffected_same_side_public_cunit_ids_in_stored_order": [],
        "side_flags": {"disallow_retreat": False, "allow_early_retreat": True, "skip_pursuit": False},
        "legality": {"status": "available", "native_boolean": True, "phase_raw": 1, "phase": "main",
                     "retreat_elapsed_baseline_date_raw": DATE, "elapsed_whole_days": 0,
                     "minimum_elapsed_whole_days_exclusive": 14, "landless_gate_allows_retreat": True,
                     "legal_now": True, "reason_codes_in_native_order": [],
                     "native_reason_keys_in_native_order": [], "earliest_day_gate_date_raw": DATE+15*24},
        "phase": "main", "phase_raw": 1, "phase_day": 4,
        "winner_side": "none", "winner_raw": -1, "forced_winner_side": "none", "forced_winner_raw": -1,
        "finalized": False, "battle_result_id": None, "base_combat_width": 100, "final_combat_width": 100,
        "roll_cadence_counter": 0, "roll_cadence_interval": 5,
        "base_advantage_raw": 0, "resolved_advantage_raw": 0, "attacker": attacker, "defender": defender,
        "pursuit_modifier_sides": {
            "status": "available", "source_combat_id": COMBAT,
            "source_target_province_id": 2586, "scale": Q,
            "sides": [{"side_index": i, "encounter_role": "attacker" if i == 0 else "defender",
                       "pursuit_efficiency_raw": 0, "retreat_losses_raw": 0} for i in range(2)],
            "unavailable_reason": None,
        },
        "current_loss_inputs_v1": {
            "scale": Q, "source_combat_id": COMBAT, "source_target_province_id": 2586,
            "stored_advantage_damage_factor_raw": Q, "runtime_damage_scaling_raw": damage_scaling,
            "runtime_main_hard_conversion_raw": 50_000, "runtime_pursuit_hard_conversion_raw": Q,
            "runtime_advantage_scaling_raw": Q, "province_has_holding": False,
            "province_winter_hard_conversion_modifier_raw": 0,
            "sides": [
                {"side_index": i, "outgoing_advantage_factor_raw": Q,
                 "own_hard_conversion_modifier_raw": 0, "opposing_hard_conversion_modifier_raw": 0,
                 "primary_participant_character_id": side["primary_participant_character_id"],
                 "levy_damage_raw": Q if i == 0 else 0}
                for i, side in enumerate((attacker, defender))
            ],
        },
        "full_backing_inputs_v1": {
            "scale": 1, "source_combat_id": COMBAT, "source_target_province_id": 2586,
            "enumeration_complete": True,
            "sides": [
                {"side_index": i, "ordered_armies": [
                    {key: army[key] for key in ("native_carmy_id", "public_cunit_id", "owner_character_id")}
                    | {"ordered_regiments": [{"regiment_id": row["regiment_id"],
                                              "current_soldiers": 100 if i == 0 else 50}
                                             for row in side["levy_entries"]
                                             if row["native_carmy_id"] == army["native_carmy_id"]]}
                    for army in side["ordered_armies"]
                ]} for i, side in enumerate((attacker, defender))
            ],
        },
        "active_counter_inputs_v1": {
            "schema_version": 1, "status": "available", "operand_census_complete": True,
            "source_combat_id": COMBAT, "source_target_province_id": 2586, "scale": Q, "class_count": 1,
            "sides": [{"side_index": i, "primary_owner_character_id": side["primary_participant_character_id"],
                       "counter_efficiency_raw": 0, "counter_resistance_raw": 0, "men_at_arms_entries": []}
                      for i, side in enumerate((attacker, defender))],
            "contexts": [
                {"countered_side_index": i, "countering_side_index": 1-i,
                 "countered_primary_owner_character_id": side["primary_participant_character_id"],
                 "countering_primary_owner_character_id": (attacker, defender)[1-i]["primary_participant_character_id"],
                 "context_scale_raw": Q} for i, side in enumerate((attacker, defender))
            ], "unavailable_reason": None,
        },
    }
    normalized = normalize_battle_control_snapshot_v1(frame,
        expected_subject_public_cunit_id=SUBJECT, expected_observed_date_raw=DATE, expected_snapshot_revision=7)
    receipt = {
        "schema_version": 1, "status": "unavailable", "input_observation_ready": False,
        "unavailable_reason": "same_frame_resume_operands_incomplete",
        "missing_required_domains": ["active_coalition_side_mapping", "active_regiment_counter_class_stack_context",
                                     "next_day_non_roll_advantage_sources", "battle_knight_participation_and_dynamic_entry_transitions"],
        "source": {key: normalized[key] for key in ("snapshot_revision", "observed_date_raw",
                   "subject_public_cunit_id", "subject_native_carmy_id", "combat_id", "province_id")},
        "observed": {"phase": "main", "phase_day": 4, "elapsed_whole_days": 0,
                     "roll_cadence_counter": 0, "roll_cadence_interval": 5, "final_combat_width": 100},
    }
    for i, side in enumerate((attacker, defender)):
        receipt["observed"].update({
            f"side_{i}_current_roll_points": 0,
            f"side_{i}_selected_commander_character_id": side["selected_commander_character_id"],
            f"side_{i}_selected_commander_next_roll_bounds": {
                "status": "available", "effective_min_roll": 0, "effective_max_roll": 0,
                "unavailable_reason": None},
            f"side_{i}_ordered_public_cunit_ids": [army["public_cunit_id"] for army in side["ordered_armies"]],
            f"side_{i}_entry_count": len(side["levy_entries"]),
        })
    resume = normalize_active_combat_resume_inputs_v1(receipt, parent=normalized)
    return adapt_current_battle_condition(normalized, active_resume_inputs=resume,
        backing_components_by_regiment_id={81: (BackingComponent(100, 100),),
                                          99: (BackingComponent(50, 50),), 3: (BackingComponent(50, 50),)})


def _future_main():
    relation = RelationModifierInputs(
        generic_raw=0, role_raw=0, terrain_raw=0, target_definition_applies=False, target_definition_raw=0,
        holding_applies=False, holding_raw=0, opposing_effect_modifier_raw=0, opposing_effect_rows=(),
        relation_kind_raw=0, relation_raw=0, source_label="explicit_zero_fixture_relation_primitives")
    sides = []
    for candidates in ((29_829,), (36_109, 36_108)):
        sides.append(FutureCommanderSideInputs(candidates=tuple(
            CommanderCandidateInputs(candidate_character_id=actor, effective_martial=1,
                opaque_opposing_primary_raw=0, opaque_province_context_raw=0, character_relation_inputs=relation,
                source_label="fixture_complete_native_order_commander_census", army_1ae_present=False,
                army_1ae_raw=0, army_1ae_gate=False, primary_identity_modifier_raw=0, side_gathering=False,
                candidate_has_flag_1a5=False, loaded_gathering_points=0,
                roll_request=CommanderRollRequest(True, 0, 0, previous_roll=0))
            for actor in candidates), candidate_census_complete=True, side_relation_inputs=relation,
            source_label="fixture_fixed_owner_context"))
    return FutureMainRefreshInputs(
        scope=FutureMainScope(True, True, True, True, True, True, True, True, 2),
        side_inputs=tuple(sides), modeled_tick_index=1, roll_cadence_interval=5,
        roll_cadence_interval_source="fixture_loaded_interval5", loaded_advantage_scaling_raw=Q,
        loaded_advantage_scaling_source="fixture_loaded_advantage_coefficient",
        resolve_boundary="after_modeled_due_rolls")


def _transition():
    pursuit = CurrentPursuitSourceContext(winner_side=0, pursuit_phase_days=1,
        pursuit_stat_multiplier_raw=0, base_toughness_multiplier_raw=Q,
        minimum_pursuit_multiplier_raw=0, skip_pursuit=False,
        source_context={"source": "explicit_runtime_duration1_and_floor_fixture"})
    return CurrentMainPhaseTransitionInputs(forced_winner_raw=-1, losing_side_skip_pursuit=False,
        automatic_retreat_inputs=CurrentAutomaticRetreatInputs(disallowed=False, allow_early=True,
            result_start_date_raw=DATE, minimum_elapsed_days=14, owner_land_rule_allows=True,
            source_context={"first_losing_native_carmy_id": 303, "owner_character_id": 36_109,
                            "source": "fixture_actual_first_loser_operands_at_each_dispatch"}),
        pursuit_rules=pursuit, normal_result_intent=True,
        source_context={"source": "conditional_first_loser_context"})


def _day(index, *, terminal=None):
    return ConditionalHorizonDay(
        admission=DailyDateStageInput(DATE+24*index, True, "caller_conditional_date_stage", endpoint_paused=True),
        loaded=LoadedScheduleInputs(maneuver_days=None, roll_cadence_interval=5, source="explicit_runtime_fixture"),
        source_context={"timeline_index": index, "qualified_as": "synthetic_caller_conditional_inputs"},
        entry_events=(), phase_events=(), ai_context={"action_selected": False, "source": "explicit_no_AI_action"},
        future_main=_future_main(), transition=_transition(), terminal=terminal)


def _terminal(condition):
    identities = frozenset(((101, 81), (303, 99), (202, 3)))
    return ConditionalTerminalInputs(
        backing_inputs_v1=condition.source_snapshot["full_backing_inputs_v1"], recomputed_regiments=identities,
        normal_result_intent=True, source_context={"source": "fixture_complete_census_and_count_witnesses"},
        allow_carried_entry_components=True, knight_link_state_by_regiment={identity: "absent" for identity in identities},
        captured_maximum_by_regiment={(101, 81): 100, (303, 99): 50, (202, 3): 50},
        side_baseline_raw_by_side={0: 10_000_000, 1: 10_000_000}, winner_side=0, wipe_raw=False)


def _stage(row, name):
    return next(stage for stage in row["stages"] if stage["stage"] == name)


class BattleCurrentConditionalHorizonFixtureTests(unittest.TestCase):
    captured_results = []

    def test_main_next_entry_pursuit_and_numeric_terminal_compose_once(self):
        initial = _initial_condition()
        terminal = _terminal(initial)
        result = run_conditional_horizon(initial,
            timeline=tuple(_day(i, terminal=terminal if i == 3 else None) for i in range(4)),
            draw_state=DrawState(0, 17), max_days=4,
            caller_seed_provenance={"fixture_stream": "caller_owned", "native_rng": False})
        self.captured_results.append(("main-pursuit-terminal", result))
        self.assertEqual(result.status, "available", result.typed_gaps)
        self.assertEqual(result.stop_reason, "conditional_terminal_accounted")
        self.assertEqual(result.typed_gaps, ())
        self.assertEqual(len(result.trace), 4)
        self.assertEqual(result.modeled_date_raw, DATE+96)
        self.assertEqual(result.modeled_accepted_invocations, 4)
        first = result.trace[0]
        first_state = first["state_after"].condition
        self.assertEqual(first_state.phase_raw, 1)
        self.assertEqual(first_state.phase_day, 5)
        self.assertEqual(first_state.roll_cadence_counter, 1)
        self.assertFalse(first["postloss_winner_recheck_performed"])
        tick = _stage(first, "future_main_and_internal_P2_carry")["result"]
        self.assertEqual(tick.result["outgoing_damage_raw_by_side"], [10_000_000, 0])
        self.assertEqual([row.state.regiment_id for row in first_state.sides[1].entries], [99, 3])
        self.assertEqual([row.state.current_raw for row in first_state.sides[1].entries], [0, 0])
        self.assertEqual([row.state.soft_casualties_raw for row in first_state.sides[1].entries], [2_500_000, 2_500_000])
        self.assertEqual([row.hard_casualties_raw for row in first_state.sides[1].entries], [2_500_000, 2_500_000])
        self.assertEqual([row.backing_components[0].current_soldiers for row in first_state.sides[1].entries], [25, 25])
        self.assertEqual(first_state.sides[1].participant_hard_total_raw, 5_000_000)
        check = _stage(result.trace[1], "accepted_main_exit_check")
        self.assertFalse(check["simulation_result_supplied"])
        self.assertFalse(check["casualty_carry_performed"])
        self.assertEqual(check["result"]["branch"], "pursuit_started")
        self.assertEqual(check["result"]["winner_side"], 0)
        initializer = result.trace[1]["state_after"].condition
        self.assertEqual((initializer.phase_raw, initializer.phase_day, initializer.roll_cadence_counter), (2, 0, 1))
        self.assertEqual(initializer.sides[1].participant_hard_total_raw, 5_000_000)
        self.assertEqual(check["result"]["initial_loser_levy_soft_raw"], 5_000_000)
        pursued = result.trace[2]["state_after"].condition
        self.assertEqual((pursued.phase_raw, pursued.phase_day), (2, 1))
        self.assertEqual([row.state.soft_casualties_raw for row in pursued.sides[1].entries], [0, 0])
        self.assertEqual([row.hard_casualties_raw for row in pursued.sides[1].entries], [5_000_000, 5_000_000])
        self.assertEqual([row.backing_components[0].current_soldiers for row in pursued.sides[1].entries], [0, 0])
        self.assertEqual(pursued.sides[1].participant_hard_total_raw, 10_000_000)
        final = result.final_state.condition
        finish = _stage(result.trace[3], "accepted_pursuit")["result"]["ticks"][0]
        self.assertEqual(finish["dispatched_phase_day"], 2)
        self.assertEqual(finish["branch"], "pursuit_finished")
        self.assertEqual(finish["new_hard_casualties_raw"], 0)
        self.assertEqual((final.phase_raw, final.phase_day), (3, 0))
        self.assertEqual(final.sides[1].participant_hard_total_raw, 10_000_000)
        self.assertEqual([row["hard_casualties_raw"] for row in final.sides[1].participant_hard_ledger], [5_000_000, 5_000_000])
        backing = result.terminal_result["backing"]
        self.assertEqual([side["current_soldiers"] for side in backing["sides"]], [100, 0])
        self.assertEqual([side["terminal_current_raw_q100000"] for side in backing["sides"]], [10_000_000, 0])
        self.assertEqual([army["native_carmy_id"] for army in backing["sides"][1]["ordered_armies"]], [303, 202])
        self.assertFalse(backing["owner_hard_ledger_debited"])
        self.assertFalse(backing["prior_losses_reapplied"])
        accounting = result.terminal_result["accounting"]
        self.assertEqual([side["final_survivors_raw_q100000"] for side in accounting["sides"]], [10_000_000, 0])
        self.assertEqual([side["hard_loss_raw_q100000"] for side in accounting["sides"]], [0, 10_000_000])
        self.assertFalse(result.terminal_result["component_after_values_debited_again"])
        self.assertFalse(result.terminal_result["native_finalizer_effects_complete"])
        self.assertEqual((result.final_state.draw_state.counter, result.final_state.draw_state.salt), (2, 17))
        self.assertEqual(final.source_snapshot, initial.source_snapshot)
        self.assertEqual(final.snapshot_revision, 7)
        self.assertEqual(final.observed_date_raw, DATE)
        self.assert_boundaries(result)

    def test_each_external_unknown_stops_typed_and_preserves_closed_trace(self):
        initial = _initial_condition(damage_scaling=25_000)
        cases = (
            ("phase_events", "continuing_main_external_inputs", "explicit phase-script-event timeline"),
            ("entry_events", "before_admission_entries", "explicit join/death entry-event timeline"),
            ("ai_context", "continuing_main_external_inputs", "explicit no-selected-AI-action timeline or selected-action adapter"),
        )
        for field, expected_stage, expected_input in cases:
            with self.subTest(missing=field):
                unresolved = replace(_day(1), **{field: None})
                result = run_conditional_horizon(initial, timeline=(_day(0), unresolved),
                    draw_state=DrawState(0, 17), max_days=2)
                self.captured_results.append(("missing-"+field, result))
                self.assertEqual(result.status, "partial")
                self.assertEqual(result.stop_reason, "required_external_input_missing")
                self.assertIsNone(result.terminal_result)
                self.assertEqual(len(result.trace), 2)
                self.assertEqual(len(result.typed_gaps), 1)
                gap = result.typed_gaps[0]
                self.assertEqual((gap.timeline_index, gap.stage, gap.missing_input), (1, expected_stage, expected_input))
                self.assertTrue(gap.implementation_entry)
                first = result.trace[0]
                tick = _stage(first, "future_main_and_internal_P2_carry")["result"]
                self.assertEqual(tick.result["outgoing_damage_raw_by_side"], [2_500_000, 0])
                self.assertFalse(first["postloss_winner_recheck_performed"])
                final = result.final_state.condition
                self.assertEqual([row.state.current_raw for row in final.sides[1].entries], [3_750_000, 3_750_000])
                self.assertEqual([row.state.soft_casualties_raw for row in final.sides[1].entries], [625_000, 625_000])
                self.assertEqual([row.hard_casualties_raw for row in final.sides[1].entries], [625_000, 625_000])
                self.assertEqual([row.backing_components[0].current_soldiers for row in final.sides[1].entries], [44, 44])
                self.assertEqual(final.sides[1].participant_hard_total_raw, 1_250_000)
                self.assertEqual(result.final_state, first["state_after"])
                self.assertEqual(result.trace[1]["state_after"], first["state_after"])
                self.assertFalse(any(stage["stage"] == "future_main_and_internal_P2_carry"
                                     for stage in result.trace[1]["stages"]))
                self.assertEqual((result.final_state.draw_state.counter, result.final_state.draw_state.salt), (2, 17))
                self.assertEqual(final.source_snapshot, initial.source_snapshot)
                self.assert_boundaries(result)

    def assert_boundaries(self, result):
        self.assertFalse(result.native_rng_state_observed)
        self.assertFalse(result.actual_next_draw_claimed)
        self.assertEqual(result.actual_game_days_advanced, 0)
        self.assertFalse(result.complete_native_transition)
        self.assertFalse(result.complete_monte_carlo)
        self.assertFalse(result.win_probability_ready)


if __name__ == "__main__":
    unittest.main()
