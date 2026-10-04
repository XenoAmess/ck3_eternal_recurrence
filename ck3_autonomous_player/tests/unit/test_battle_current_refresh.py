from __future__ import annotations

import copy
import unittest

from test_battle_current_condition import (
    COMBAT, DATE, Q, SUBJECT, _entry, _raw_frame, _side,
)
from xar_autoplayer.bridge.battle_control_contract import (
    normalize_active_combat_resume_inputs_v1,
    normalize_battle_control_snapshot_v1,
)
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_next_day import carry_frozen_main_tick
from xar_autoplayer.simulation.battle_current_refresh import refresh_current_battle_condition
from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick
from xar_autoplayer.simulation.combat_core import DrawState


def _counter(raw: dict, context_scale: int) -> None:
    sides = []
    for index, role in enumerate(("attacker", "defender")):
        side = raw[role]
        sides.append({
            "side_index": index,
            "primary_owner_character_id": side["primary_participant_character_id"],
            "counter_efficiency_raw": 0, "counter_resistance_raw": 0,
            "men_at_arms_entries": [{
                "bucket_index": row["bucket_index"], "regiment_id": row["regiment_id"],
                "native_carmy_id": row["native_carmy_id"],
                "current_fighting_raw": row["current_fighting_raw"],
                "status": "available", "class_index": 0, "stack_size_soldiers": 1,
                "current_chunk_raw": row["current_fighting_raw"],
                "targets": [{"class_index": 0, "effectiveness_raw": Q}],
            } for row in side["men_at_arms_entries"]],
        })
    raw["active_counter_inputs_v1"] = {
        "schema_version": 1, "status": "available", "operand_census_complete": True,
        "source_combat_id": COMBAT, "source_target_province_id": raw["province_id"],
        "scale": Q, "class_count": 1, "sides": sides,
        "contexts": [{
            "countered_side_index": index, "countering_side_index": 1-index,
            "countered_primary_owner_character_id": sides[index]["primary_owner_character_id"],
            "countering_primary_owner_character_id": sides[1-index]["primary_owner_character_id"],
            "context_scale_raw": context_scale,
        } for index in (0, 1)], "unavailable_reason": None,
    }


def _normalize(raw: dict) -> tuple[dict, dict]:
    frame = normalize_battle_control_snapshot_v1(raw,
        expected_subject_public_cunit_id=SUBJECT,
        expected_observed_date_raw=raw["observed_date_raw"],
        expected_snapshot_revision=raw["snapshot_revision"])
    receipt = {
        "schema_version": 1, "status": "unavailable", "input_observation_ready": False,
        "unavailable_reason": "same_frame_resume_operands_incomplete",
        "missing_required_domains": [
            "active_coalition_side_mapping", "active_regiment_counter_class_stack_context",
            "next_day_non_roll_advantage_sources",
            "battle_knight_participation_and_dynamic_entry_transitions",
        ],
        "source": {key: frame[key] for key in (
            "snapshot_revision", "observed_date_raw", "subject_public_cunit_id",
            "subject_native_carmy_id", "combat_id", "province_id")},
        "observed": {
            "phase": frame["phase"], "phase_day": frame["phase_day"],
            "elapsed_whole_days": frame["legality"]["elapsed_whole_days"],
            "roll_cadence_counter": frame["roll_cadence_counter"],
            "final_combat_width": frame["final_combat_width"],
        },
    }
    for index, role in enumerate(("attacker", "defender")):
        side = frame[role]
        point = 4 if index == 0 else 2
        receipt["observed"].update({
            f"side_{index}_current_roll_points": side["current_roll_points"],
            f"side_{index}_selected_commander_character_id": side["selected_commander_character_id"],
            f"side_{index}_selected_commander_next_roll_bounds": {
                "status": "available", "effective_min_roll": point,
                "effective_max_roll": point, "unavailable_reason": None},
            f"side_{index}_ordered_public_cunit_ids": [
                army["public_cunit_id"] for army in side["ordered_armies"]],
            f"side_{index}_entry_count": len(side["levy_entries"])+len(side["men_at_arms_entries"]),
        })
    return frame, normalize_active_combat_resume_inputs_v1(receipt, parent=frame)


def _next_frame(raw: dict) -> dict:
    fresh = copy.deepcopy(raw)
    fresh.update(snapshot_revision=raw["snapshot_revision"]+1,
                 observed_date_raw=raw["observed_date_raw"]+24,
                 phase_day=raw["phase_day"]+1)
    fresh["legality"].update(
        retreat_elapsed_baseline_date_raw=fresh["observed_date_raw"],
        earliest_day_gate_date_raw=fresh["observed_date_raw"]+15*24)
    return fresh


def _carried(raw: dict):
    frame, resume = _normalize(raw)
    original = adapt_current_battle_condition(frame, active_resume_inputs=resume)
    tick = run_frozen_main_tick(original, draw_state=DrawState(11, 17))
    return original, tick, carry_frozen_main_tick(original, tick)


class BattleCurrentRefreshFixtureTests(unittest.TestCase):
    """Two offline production-shaped cases; no actual-frame or RNG-parity claim."""

    def test_fresh_effective_counter_and_nonroll_values_replace_forecast(self):
        raw = _raw_frame(1)
        enemy = raw["defender"]["ordered_armies"][0]
        raw["defender"] = _side(1, [enemy], [
            _entry(80, enemy, bucket="levy", index=0,
                   current=400_000, damage=Q, toughness=200_000)], [
            _entry(8, enemy, bucket="men_at_arms", index=0,
                   current=600_000, damage=Q, toughness=Q)], [(enemy["owner_character_id"], 0)])
        _counter(raw, 0)
        original, tick, carried = _carried(raw)
        self.assertEqual(tick["outgoing_damage_raw_by_side"], [650_000, 250_000])
        self.assertEqual((carried.draw_state.counter, carried.draw_state.salt), (13, 17))
        self.assertNotEqual(carried.condition.sides[0].entries[0].state.current_raw, 400_000)

        fresh = _next_frame(raw)
        fresh.update(base_advantage_raw=200_000, resolved_advantage_raw=450_000)
        fresh["attacker"]["current_roll_points"] = 7
        fresh["defender"]["current_roll_points"] = 3
        fresh["attacker"]["levy_entries"][0]["effective_damage_raw"] = 300_000
        fresh["attacker"]["men_at_arms_entries"][0].update(
            effective_damage_raw=400_000, effective_toughness_raw=200_000,
            effective_pursuit_raw=300_000, effective_screen_raw=400_000)
        fresh["defender"]["men_at_arms_entries"][0]["effective_damage_raw"] = 0
        fresh["current_loss_inputs_v1"]["sides"][0].update(
            levy_damage_raw=300_000, outgoing_advantage_factor_raw=120_000)
        _counter(fresh, Q)
        frame, resume = _normalize(fresh)
        untouched = copy.deepcopy(frame)
        result = refresh_current_battle_condition(carried, frame, active_resume_inputs=resume)
        condition = result.condition

        self.assertEqual(frame, untouched)
        self.assertEqual(condition.source_snapshot, frame)
        self.assertEqual((condition.snapshot_revision, condition.observed_date_raw), (6, DATE+24))
        self.assertEqual([entry.state.current_raw for entry in condition.sides[0].entries], [400_000, 600_000])
        maa = condition.sides[0].entries[1]
        self.assertEqual((maa.effective_damage_raw, maa.state.toughness_raw,
                          maa.state.pursuit_raw, maa.state.screen_raw),
                         (400_000, 200_000, 300_000, 400_000))
        self.assertFalse(maa.fights_in_main_phase)
        self.assertEqual((condition.base_advantage_raw, condition.resolved_advantage_raw), (200_000, 450_000))
        self.assertEqual([side.current_roll_points for side in condition.sides], [7, 3])
        self.assertEqual(condition.loss_inputs.sides[0].outgoing_advantage_factor_raw, 120_000)
        self.assertEqual(condition.active_counter_inputs["contexts"][0]["context_scale_raw"], Q)
        self.assertEqual((result.draw_state.counter, result.draw_state.salt), (13, 17))
        self.assertEqual(result.context.simulated_main_ticks, 0)
        self.assertFalse(result.complete_transition)
        self.assertFalse(result.complete_monte_carlo)
        self.assertFalse(result.actual_next_draw_claimed)
        next_tick = run_frozen_main_tick(condition, draw_state=result.draw_state)
        self.assertEqual(next_tick["counter_retention_raw_by_side"], ((55_000,), (55_000,)))
        self.assertEqual(next_tick["outgoing_damage_raw_by_side"], [756_000, 100_000])
        self.assertEqual(next_tick["rolls"]["input_draw_state"], {"counter": 13, "salt": 17})
        self.assertEqual(next_tick["rolls"]["output_draw_state"], {"counter": 15, "salt": 17})
        self.assertEqual(original.base_advantage_raw, 0)

    def test_zero_null_absence_and_changed_entry_count_are_not_carried_forward(self):
        raw = _raw_frame(2)
        _, _, carried = _carried(raw)
        fresh = _next_frame(raw)
        enemy_a, enemy_b = fresh["defender"]["ordered_armies"]
        fresh["defender"] = _side(1, [enemy_b, enemy_a], [], [
            _entry(3, enemy_b, bucket="men_at_arms", index=0,
                   current=400_000, damage=0, toughness=Q, old_hard=350_000),
            _entry(5, enemy_b, bucket="men_at_arms", index=1,
                   current=0, damage=0, toughness=0),
            _entry(99, enemy_a, bucket="men_at_arms", index=2,
                   current=600_000, damage=0, toughness=Q, old_hard=250_000)],
            [(enemy_b["owner_character_id"], 350_000), (enemy_a["owner_character_id"], 250_000)])
        for index, side in enumerate((fresh["attacker"], fresh["defender"])):
            fresh["current_loss_inputs_v1"]["sides"][index].update(
                primary_participant_character_id=side["primary_participant_character_id"],
                levy_damage_raw=0 if index == 0 else None)
        del fresh["active_counter_inputs_v1"]
        frame, resume = _normalize(fresh)
        result = refresh_current_battle_condition(carried, frame, active_resume_inputs=resume)
        side = result.condition.sides[1]

        self.assertEqual([entry.state.regiment_id for entry in side.entries], [3, 5, 99])
        self.assertEqual([entry.state.current_raw for entry in side.entries], [400_000, 0, 600_000])
        self.assertEqual([entry.hard_casualties_raw for entry in side.entries], [350_000, 0, 250_000])
        self.assertEqual([army["public_cunit_id"] for army in side.ordered_armies], [357, 33_554_657])
        self.assertEqual(side.participant_hard_total_raw, 600_000)
        self.assertEqual(result.condition.sides[0].levy_damage_raw, 0)
        self.assertIsNone(side.loss_inputs.levy_damage_raw)
        self.assertIsNone(result.condition.active_counter_inputs)
        self.assertIn("active_counter_inputs_v1", result.condition.missing_inputs)
        self.assertIsNone(side.entries[1].backing_components)
        self.assertEqual((result.draw_state.counter, result.draw_state.salt), (13, 17))
        self.assertEqual(result.context.simulated_main_ticks, 0)
        self.assertEqual(result.condition.source_snapshot, frame)
        self.assertEqual(len(carried.condition.sides[1].entries), 2)
        self.assertFalse(result.complete_transition)
        self.assertFalse(result.complete_monte_carlo)


if __name__ == "__main__":
    unittest.main()
