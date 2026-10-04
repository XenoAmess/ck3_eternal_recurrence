from __future__ import annotations

import unittest
from dataclasses import replace

from xar_autoplayer.bridge.battle_control_contract import (
    normalize_active_combat_resume_inputs_v1,
    normalize_battle_control_snapshot_v1,
)
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick
from xar_autoplayer.simulation.battle_current_next_day import (
    carry_frozen_main_tick,
    prepare_next_main_tick,
)
from xar_autoplayer.simulation.combat_core import BackingComponent, DrawState


Q = 100_000
SUBJECT = 83_886_341
COMBAT = 335_544_325
DATE = 53_178_264


def _army(native_id, public_id, owner):
    return {"native_carmy_id": native_id, "public_cunit_id": public_id,
            "owner_character_id": owner, "combat_backlink_id": COMBAT}


def _entry(regiment, army, *, index, current, soft, hard, damage, bucket):
    return {
        "bucket": bucket, "bucket_index": index, "regiment_id": regiment,
        "native_carmy_id": army["native_carmy_id"],
        "public_cunit_id": army["public_cunit_id"],
        "owner_character_id": army["owner_character_id"],
        "starting_raw": current+soft+hard, "current_fighting_raw": current,
        "soft_casualties_raw": soft, "fights_in_main_phase": True,
        "hard_casualties_status": "available", "hard_casualties_raw": hard,
        "hard_casualties_source": "derived_starting_minus_current_minus_soft",
        "hard_casualties_unavailable_reason": None,
        "effective_max_size": 100, "effective_siege_raw": 0,
        "effective_damage_raw": damage, "effective_toughness_raw": Q,
        "effective_pursuit_raw": 0, "effective_screen_raw": 0, "entry_strength_raw": 0,
    }


def _side(index, armies, levy, maa, *, stored_current=None):
    rows = levy+maa
    current = sum(row["current_fighting_raw"] for row in rows)
    stored = current if stored_current is None else stored_current
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": armies[0]["owner_character_id"],
        "selected_commander_character_id": armies[0]["owner_character_id"],
        "current_roll_points": 11 if index == 0 else 13,
        "ordered_armies": armies, "levy_entries": levy, "men_at_arms_entries": maa,
        "stored_current_fighting_raw": stored,
        "stored_levy_current_fighting_raw": sum(row["current_fighting_raw"] for row in levy),
        "stored_current_matches_derived": stored == current,
        "stored_levy_current_matches_derived": True,
        "derived_current_fighting_raw": current,
        "derived_soft_casualties_raw": sum(row["soft_casualties_raw"] for row in rows),
        "derived_main_fighting_entry_hard_casualties_raw": sum(row["hard_casualties_raw"] for row in rows),
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": [
            {"row_index": i, "participant_character_id": army["owner_character_id"],
             "hard_casualties_raw": sum(row["hard_casualties_raw"] for row in rows
                                        if row["owner_character_id"] == army["owner_character_id"])}
            for i, army in enumerate(armies)
        ],
        "participant_hard_total_raw": sum(row["hard_casualties_raw"] for row in rows),
        "side_strength_raw": 0, "side_strength_scale": Q,
    }


def _condition(*, refreshed=False):
    own = _army(101, SUBJECT, 29_829)
    enemy_a = _army(303, 33_554_657, 36_109)
    enemy_b = _army(202, 357, 36_108)
    attacker = _side(0, [own], [
        _entry(81, own, index=0, current=1_000_000, soft=0, hard=0,
               damage=400_000, bucket="levy")], [])
    if refreshed:
        defender = _side(1, [enemy_b, enemy_a], [], [
            _entry(3, enemy_b, index=0, current=600_000, soft=100_000, hard=350_000,
                   damage=0, bucket="men_at_arms"),
            _entry(99, enemy_a, index=1, current=400_000, soft=50_000, hard=500_000,
                   damage=0, bucket="men_at_arms")], stored_current=1_200_000)
        revision, date, phase_day, cadence, width = 8, DATE+24, 5, 2, 8
        backing = {3: (BackingComponent(6, 6),), 99: (BackingComponent(4, 4),)}
    else:
        defender = _side(1, [enemy_a, enemy_b], [], [
            _entry(99, enemy_a, index=0, current=500_000, soft=0, hard=200_000,
                   damage=0, bucket="men_at_arms"),
            _entry(3, enemy_b, index=1, current=500_000, soft=0, hard=300_000,
                   damage=0, bucket="men_at_arms")])
        revision, date, phase_day, cadence, width = 7, DATE, 4, 0, 5
        backing = {99: (BackingComponent(1, 1), BackingComponent(4, 4)),
                   3: (BackingComponent(4, 4), BackingComponent(1, 1))}
    backing[81] = (BackingComponent(10, 10),)
    frame = {
        "schema_version": 1, "contract_stage": "production_exact_ongoing_combat",
        "status": "available", "battle_control_ready": True,
        "snapshot_revision": revision, "observed_date_raw": date,
        "subject_public_cunit_id": SUBJECT, "subject_native_carmy_id": 101,
        "combat_id": COMBAT, "province_id": 2586,
        "selected_public_cunit_id": SUBJECT, "selected_native_carmy_id": 101,
        "selected_owner_character_id": 29_829, "combat_province_id": 2586,
        "side_index": 0, "side_scope": "full_side",
        "affected_public_cunit_ids_in_stored_order": [SUBJECT],
        "unaffected_same_side_public_cunit_ids_in_stored_order": [],
        "side_flags": {"disallow_retreat": False, "allow_early_retreat": True, "skip_pursuit": False},
        "legality": {"status": "available", "native_boolean": True,
                     "phase_raw": 1, "phase": "main", "retreat_elapsed_baseline_date_raw": date,
                     "elapsed_whole_days": 0, "minimum_elapsed_whole_days_exclusive": 14,
                     "landless_gate_allows_retreat": True, "legal_now": True,
                     "reason_codes_in_native_order": [], "native_reason_keys_in_native_order": [],
                     "earliest_day_gate_date_raw": date+15*24},
        "phase": "main", "phase_raw": 1, "phase_day": phase_day,
        "winner_side": "none", "winner_raw": -1,
        "forced_winner_side": "none", "forced_winner_raw": -1,
        "finalized": False, "battle_result_id": None,
        "base_combat_width": width, "final_combat_width": width,
        "roll_cadence_counter": cadence, "base_advantage_raw": 0, "resolved_advantage_raw": 0,
        "attacker": attacker, "defender": defender,
        "current_loss_inputs_v1": {
            "scale": Q, "source_combat_id": COMBAT, "source_target_province_id": 2586,
            "stored_advantage_damage_factor_raw": Q, "runtime_damage_scaling_raw": 25_000,
            "runtime_main_hard_conversion_raw": 50_000, "runtime_pursuit_hard_conversion_raw": Q,
            "province_has_holding": False, "province_winter_hard_conversion_modifier_raw": 0,
            "sides": [
                {"side_index": i, "outgoing_advantage_factor_raw": Q,
                 "own_hard_conversion_modifier_raw": 0, "opposing_hard_conversion_modifier_raw": 0,
                 "primary_participant_character_id": side["primary_participant_character_id"],
                 "levy_damage_raw": 400_000 if i == 0 else 0}
                for i, side in enumerate((attacker, defender))
            ],
        },
    }
    counter_sides = [
        {"side_index": i, "primary_owner_character_id": side["primary_participant_character_id"],
         "counter_efficiency_raw": 0, "counter_resistance_raw": 0,
         "men_at_arms_entries": [
             {"bucket_index": row["bucket_index"], "regiment_id": row["regiment_id"],
              "native_carmy_id": row["native_carmy_id"], "current_fighting_raw": row["current_fighting_raw"],
              "status": "available", "class_index": 0, "stack_size_soldiers": 1,
              "current_chunk_raw": row["current_fighting_raw"], "targets": []}
             for row in side["men_at_arms_entries"]]}
        for i, side in enumerate((attacker, defender))
    ]
    frame["active_counter_inputs_v1"] = {
        "schema_version": 1, "status": "available", "operand_census_complete": True,
        "source_combat_id": COMBAT, "source_target_province_id": 2586,
        "scale": Q, "class_count": 1, "sides": counter_sides,
        "contexts": [
            {"countered_side_index": i, "countering_side_index": 1-i,
             "countered_primary_owner_character_id": counter_sides[i]["primary_owner_character_id"],
             "countering_primary_owner_character_id": counter_sides[1-i]["primary_owner_character_id"],
             "context_scale_raw": Q} for i in (0, 1)
        ], "unavailable_reason": None,
    }
    normalized = normalize_battle_control_snapshot_v1(frame,
        expected_subject_public_cunit_id=SUBJECT, expected_observed_date_raw=date,
        expected_snapshot_revision=revision)
    receipt = {
        "schema_version": 1, "status": "unavailable", "input_observation_ready": False,
        "unavailable_reason": "same_frame_resume_operands_incomplete",
        "missing_required_domains": ["active_coalition_side_mapping", "active_regiment_counter_class_stack_context",
                                     "next_day_non_roll_advantage_sources", "battle_knight_participation_and_dynamic_entry_transitions"],
        "source": {key: normalized[key] for key in ("snapshot_revision", "observed_date_raw",
                   "subject_public_cunit_id", "subject_native_carmy_id", "combat_id", "province_id")},
        "observed": {"phase": "main", "phase_day": phase_day, "elapsed_whole_days": 0,
                     "roll_cadence_counter": cadence, "final_combat_width": width},
    }
    for i, side in enumerate((attacker, defender)):
        point = 4 if i == 0 else 2
        receipt["observed"].update({
            f"side_{i}_current_roll_points": side["current_roll_points"],
            f"side_{i}_selected_commander_character_id": side["selected_commander_character_id"],
            f"side_{i}_selected_commander_next_roll_bounds": {
                "status": "available", "effective_min_roll": point, "effective_max_roll": point,
                "unavailable_reason": None},
            f"side_{i}_ordered_public_cunit_ids": [army["public_cunit_id"] for army in side["ordered_armies"]],
            f"side_{i}_entry_count": len(side["levy_entries"])+len(side["men_at_arms_entries"]),
        })
    resume = normalize_active_combat_resume_inputs_v1(receipt, parent=normalized)
    return adapt_current_battle_condition(normalized, active_resume_inputs=resume,
                                          backing_components_by_regiment_id=backing)


class BattleCurrentNextDayFixtureTests(unittest.TestCase):
    """Independent Q100000 expectations across the two new P2 production paths."""

    def _carried(self):
        original = _condition()
        tick = run_frozen_main_tick(original, draw_state=DrawState(11, 17))
        self.assertEqual(tick["outgoing_damage_raw_by_side"], [500_000, 0])
        self.assertEqual([row["sampled_roll_points"] for row in tick["rolls"]["sides"]], [4, 2])
        return original, carry_frozen_main_tick(original, tick)

    def test_conditional_carry_preserves_native_caches_and_parallel_ledgers(self):
        original, carried = self._carried()
        condition = carried.condition
        side = condition.sides[1]
        self.assertEqual([row.state.regiment_id for row in side.entries], [99, 3])
        self.assertEqual([army["public_cunit_id"] for army in side.ordered_armies], [33_554_657, 357])
        self.assertEqual([row.state.current_raw for row in side.entries], [250_000, 250_000])
        self.assertEqual([row.state.soft_casualties_raw for row in side.entries], [125_000, 125_000])
        self.assertEqual([row.hard_casualties_raw for row in side.entries], [325_000, 425_000])
        self.assertEqual([[component.current_soldiers for component in row.backing_components]
                          for row in side.entries], [[0, 4], [3, 1]])
        self.assertEqual([row["participant_character_id"] for row in side.participant_hard_ledger], [36_109, 36_108])
        self.assertEqual([row["hard_casualties_raw"] for row in side.participant_hard_ledger], [325_000, 425_000])
        self.assertEqual(side.participant_hard_total_raw, 750_000)
        self.assertEqual(side.stored_current_fighting_raw, 1_000_000)
        self.assertEqual(side.stored_levy_current_fighting_raw, 0)
        derived = carried.derived_side_totals[1]
        self.assertEqual(derived["derived_current_fighting_raw"], 500_000)
        self.assertEqual(derived["derived_soft_casualties_raw"], 250_000)
        self.assertEqual(derived["derived_main_fighting_entry_hard_casualties_raw"], 750_000)
        self.assertEqual(derived["stored_current_fighting_raw"], 1_000_000)
        self.assertEqual(derived["participant_hard_total_raw"], 750_000)
        self.assertEqual([row.state.current_raw for row in original.sides[1].entries], [500_000, 500_000])
        self.assertEqual([row["hard_casualties_raw"] for row in original.sides[1].participant_hard_ledger], [200_000, 300_000])
        self.assertEqual(condition.source_snapshot, original.source_snapshot)
        context = prepare_next_main_tick(carried)
        self.assertEqual(context.scope_kind, "conditional_frozen_continuation")
        self.assertTrue(context.conditional_assumptions)
        self.assertEqual(context.simulated_main_ticks, 1)
        self.assertEqual((context.draw_state.counter, context.draw_state.salt), (13, 17))
        self.assertEqual((context.condition.snapshot_revision, context.condition.observed_date_raw), (7, DATE))
        self.assertEqual(context.condition.phase_day, 4)
        self.assertEqual(context.condition.roll_cadence_counter, 0)
        self.assertEqual(context.condition.final_combat_width, 5)
        self.assertEqual([side.current_roll_points for side in context.condition.sides], [11, 13])
        self.assertEqual(context.condition.loss_inputs.stored_advantage_damage_factor_raw, Q)
        # A caller-declared modeled cadence4 and loaded interval5 wrap to0.
        # The original observed snapshot stays intact; calendar admission is absent.
        modeled_cadence = replace(carried, condition=replace(condition, roll_cadence_counter=4))
        wrapped = prepare_next_main_tick(modeled_cadence, roll_days=5,
                                         roll_days_source="caller_explicit_loaded_slot_5C69B48_fixture")
        self.assertEqual(wrapped.scope_kind, "conditional_frozen_continuation")
        self.assertEqual(wrapped.condition.roll_cadence_counter, 0)
        self.assertEqual(wrapped.condition.phase_day, 4)
        self.assertEqual(wrapped.condition.source_snapshot, original.source_snapshot)
        self.assertEqual((wrapped.draw_state.counter, wrapped.draw_state.salt), (13, 17))

    def test_explicit_refresh_replaces_state_without_reapplying_prior_loss(self):
        _, carried = self._carried()
        refreshed = _condition(refreshed=True)
        context = prepare_next_main_tick(carried, refreshed_condition=refreshed,
                                         roll_days=5, roll_days_source="caller_override_not_applied_to_refresh")
        self.assertEqual(context.scope_kind, "caller_authoritative_refresh")
        self.assertEqual(context.condition, refreshed)
        self.assertEqual(context.simulated_main_ticks, 0)
        self.assertEqual((context.draw_state.counter, context.draw_state.salt), (13, 17))
        self.assertEqual((context.condition.snapshot_revision, context.condition.observed_date_raw), (8, DATE+24))
        self.assertEqual((context.condition.phase_day, context.condition.roll_cadence_counter), (5, 2))
        self.assertEqual(context.condition.final_combat_width, 8)
        side = context.condition.sides[1]
        self.assertEqual([row.state.regiment_id for row in side.entries], [3, 99])
        self.assertEqual([army["public_cunit_id"] for army in side.ordered_armies], [357, 33_554_657])
        self.assertEqual([row.state.current_raw for row in side.entries], [600_000, 400_000])
        self.assertEqual([row.state.soft_casualties_raw for row in side.entries], [100_000, 50_000])
        self.assertEqual([row.hard_casualties_raw for row in side.entries], [350_000, 500_000])
        self.assertEqual([[component.current_soldiers for component in row.backing_components]
                          for row in side.entries], [[6], [4]])
        self.assertEqual(side.stored_current_fighting_raw, 1_200_000)
        self.assertEqual(side.derived_current_fighting_raw, 1_000_000)
        self.assertEqual([row["hard_casualties_raw"] for row in side.participant_hard_ledger], [350_000, 500_000])
        self.assertEqual(side.participant_hard_total_raw, 850_000)
        self.assertEqual(carried.condition.sides[1].participant_hard_total_raw, 750_000)


if __name__ == "__main__":
    unittest.main()
