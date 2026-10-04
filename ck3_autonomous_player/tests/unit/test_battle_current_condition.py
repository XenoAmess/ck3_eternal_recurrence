from __future__ import annotations

import unittest

from xar_autoplayer.bridge.battle_control_contract import (
    normalize_active_combat_resume_inputs_v1,
    normalize_battle_control_snapshot_v1,
)
from xar_autoplayer.simulation.battle_current_adapter import (
    adapt_current_battle_condition,
)
from xar_autoplayer.simulation.battle_current_runner import (
    next_roll_distribution,
    run_frozen_main_tick,
)
from xar_autoplayer.simulation.combat_core import (
    BackingComponent,
    CommanderRollRequest,
    DrawState,
)


Q = 100_000
SUBJECT = 83_886_341
COMBAT = 335_544_325
DATE = 53_178_264


def _army(native_id: int, public_id: int, owner: int) -> dict:
    return {
        "native_carmy_id": native_id,
        "public_cunit_id": public_id,
        "owner_character_id": owner,
        "combat_backlink_id": COMBAT,
    }


def _entry(regiment: int, army: dict, *, bucket: str, index: int,
           current: int, damage: int, toughness: int, main: bool = True,
           old_hard: int = 0) -> dict:
    return {
        "bucket": bucket, "bucket_index": index, "regiment_id": regiment,
        "native_carmy_id": army["native_carmy_id"],
        "public_cunit_id": army["public_cunit_id"],
        "owner_character_id": army["owner_character_id"],
        "starting_raw": current + old_hard,
        "current_fighting_raw": current, "soft_casualties_raw": 0,
        "fights_in_main_phase": main,
        "hard_casualties_status": "available" if main else "unavailable",
        "hard_casualties_raw": old_hard if main else None,
        "hard_casualties_source": (
            "derived_starting_minus_current_minus_soft" if main else None
        ),
        "hard_casualties_unavailable_reason": (
            None if main else "non_main_reserve_not_distinguishable_from_hard"
        ),
        "effective_max_size": 100, "effective_siege_raw": 0,
        "effective_damage_raw": damage, "effective_toughness_raw": toughness,
        "effective_pursuit_raw": 0, "effective_screen_raw": 0,
        "entry_strength_raw": 0,
    }


def _side(index: int, armies: list[dict], levy: list[dict], maa: list[dict],
          owner_hard: list[tuple[int, int]]) -> dict:
    rows = levy + maa
    current = sum(row["current_fighting_raw"] for row in rows)
    levy_current = sum(row["current_fighting_raw"] for row in levy)
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": armies[0]["owner_character_id"],
        "selected_commander_character_id": armies[0]["owner_character_id"],
        "current_roll_points": 4 if index == 0 else 2,
        "ordered_armies": armies, "levy_entries": levy,
        "men_at_arms_entries": maa,
        "stored_current_fighting_raw": current,
        "stored_levy_current_fighting_raw": levy_current,
        "stored_current_matches_derived": True,
        "stored_levy_current_matches_derived": True,
        "derived_current_fighting_raw": current,
        "derived_soft_casualties_raw": 0,
        "derived_main_fighting_entry_hard_casualties_raw": sum(
            row["hard_casualties_raw"] for row in rows
            if row["fights_in_main_phase"]
        ),
        "non_main_start_minus_current_minus_soft_raw": sum(
            row["starting_raw"] - row["current_fighting_raw"]
            for row in rows if not row["fights_in_main_phase"]
        ),
        "participant_hard_ledger": [
            {"row_index": i, "participant_character_id": owner,
             "hard_casualties_raw": hard}
            for i, (owner, hard) in enumerate(owner_hard)
        ],
        "participant_hard_total_raw": sum(hard for _, hard in owner_hard),
        "side_strength_raw": 0, "side_strength_scale": Q,
    }


def _raw_frame(case: int) -> dict:
    own = _army(101, SUBJECT, 29_829)
    enemy_a = _army(303, 33_554_657, 36_109)
    enemy_b = _army(202, 357, 36_108)
    if case == 1:
        attacker = _side(0, [own], [
            _entry(90, own, bucket="levy", index=0,
                   current=400_000, damage=200_000, toughness=Q),
        ], [
            _entry(7, own, bucket="men_at_arms", index=0,
                   current=600_000, damage=300_000, toughness=Q, main=False),
        ], [(29_829, 0)])
        defender = _side(1, [enemy_b], [
            _entry(80, enemy_b, bucket="levy", index=0,
                   current=1_000_000, damage=Q, toughness=200_000),
        ], [], [(36_108, 0)])
        damage_scaling, conversion = 50_000, 50_000
    else:
        attacker = _side(0, [own], [
            _entry(41, own, bucket="levy", index=0,
                   current=1_000_000, damage=700_000, toughness=Q),
        ], [], [(29_829, 0)])
        defender = _side(1, [enemy_a, enemy_b], [], [
            _entry(99, enemy_a, bucket="men_at_arms", index=0,
                   current=500_000, damage=0, toughness=Q, old_hard=200_000),
            _entry(3, enemy_b, bucket="men_at_arms", index=1,
                   current=500_000, damage=0, toughness=Q, old_hard=300_000),
        ], [(36_109, 200_000), (36_108, 300_000)])
        damage_scaling, conversion = 10_000, Q
    frame = {
        "schema_version": 1, "contract_stage": "production_exact_ongoing_combat",
        "status": "available", "battle_control_ready": True,
        "snapshot_revision": 5, "observed_date_raw": DATE,
        "subject_public_cunit_id": SUBJECT, "subject_native_carmy_id": 101,
        "combat_id": COMBAT, "province_id": 2586,
        "selected_public_cunit_id": SUBJECT, "selected_native_carmy_id": 101,
        "selected_owner_character_id": 29_829, "combat_province_id": 2586,
        "side_index": 0, "side_scope": "full_side",
        "affected_public_cunit_ids_in_stored_order": [SUBJECT],
        "unaffected_same_side_public_cunit_ids_in_stored_order": [],
        "side_flags": {"disallow_retreat": False, "allow_early_retreat": True,
                       "skip_pursuit": False},
        "legality": {
            "status": "available", "native_boolean": True,
            "phase_raw": 1, "phase": "main",
            "retreat_elapsed_baseline_date_raw": DATE,
            "elapsed_whole_days": 0, "minimum_elapsed_whole_days_exclusive": 14,
            "landless_gate_allows_retreat": True, "legal_now": True,
            "reason_codes_in_native_order": [], "native_reason_keys_in_native_order": [],
            "earliest_day_gate_date_raw": DATE + 15 * 24,
        },
        "phase": "main", "phase_raw": 1, "phase_day": 4,
        "winner_side": "none", "winner_raw": -1,
        "forced_winner_side": "none", "forced_winner_raw": -1,
        "finalized": False, "battle_result_id": None,
        "base_combat_width": 5, "final_combat_width": 5,
        "roll_cadence_counter": 0, "base_advantage_raw": 0,
        "resolved_advantage_raw": 0, "attacker": attacker, "defender": defender,
        "current_loss_inputs_v1": {
            "scale": Q, "source_combat_id": COMBAT, "source_target_province_id": 2586,
            "stored_advantage_damage_factor_raw": Q,
            "runtime_damage_scaling_raw": damage_scaling,
            "runtime_main_hard_conversion_raw": conversion,
            "runtime_pursuit_hard_conversion_raw": Q,
            "province_has_holding": False,
            "province_winter_hard_conversion_modifier_raw": 0,
            "sides": [
                {"side_index": i, "outgoing_advantage_factor_raw": Q,
                 "own_hard_conversion_modifier_raw": 0,
                 "opposing_hard_conversion_modifier_raw": 0}
                for i in (0, 1)
            ],
        },
    }
    sides = []
    for i, side in enumerate((attacker, defender)):
        sides.append({
            "side_index": i,
            "primary_owner_character_id": side["primary_participant_character_id"],
            "counter_efficiency_raw": 0, "counter_resistance_raw": 0,
            "men_at_arms_entries": [
                {"bucket_index": row["bucket_index"], "regiment_id": row["regiment_id"],
                 "native_carmy_id": row["native_carmy_id"],
                 "current_fighting_raw": row["current_fighting_raw"],
                 "status": "available", "class_index": 0,
                 "stack_size_soldiers": 1,
                 "current_chunk_raw": row["current_fighting_raw"], "targets": []}
                for row in side["men_at_arms_entries"]
            ],
        })
    frame["active_counter_inputs_v1"] = {
        "schema_version": 1, "status": "available", "operand_census_complete": True,
        "source_combat_id": COMBAT, "source_target_province_id": 2586,
        "scale": Q, "class_count": 1, "sides": sides,
        "contexts": [
            {"countered_side_index": i, "countering_side_index": 1-i,
             "countered_primary_owner_character_id": sides[i]["primary_owner_character_id"],
             "countering_primary_owner_character_id": sides[1-i]["primary_owner_character_id"],
             "context_scale_raw": Q} for i in (0, 1)
        ],
        "unavailable_reason": None,
    }
    if case == 1:
        for i, side in enumerate((attacker, defender)):
            frame["current_loss_inputs_v1"]["sides"][i].update({
                "primary_participant_character_id": side["primary_participant_character_id"],
                "levy_damage_raw": 200_000 if i == 0 else Q,
            })
    return frame


def _normalized_frame(case: int) -> dict:
    return normalize_battle_control_snapshot_v1(
        _raw_frame(case), expected_subject_public_cunit_id=SUBJECT,
        expected_observed_date_raw=DATE, expected_snapshot_revision=5,
    )


def _normalized_roll_receipt(frame: dict) -> dict:
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
            "phase": "main", "phase_day": 4, "elapsed_whole_days": 0,
            "roll_cadence_counter": 0, "final_combat_width": 5,
        },
    }
    for i, role in enumerate(("attacker", "defender")):
        side = frame[role]
        bounds = 4 if i == 0 else 2
        receipt["observed"].update({
            f"side_{i}_current_roll_points": side["current_roll_points"],
            f"side_{i}_selected_commander_character_id": side["selected_commander_character_id"],
            f"side_{i}_selected_commander_next_roll_bounds": {
                "status": "available", "effective_min_roll": bounds,
                "effective_max_roll": bounds, "unavailable_reason": None,
            },
            f"side_{i}_ordered_public_cunit_ids": [
                army["public_cunit_id"] for army in side["ordered_armies"]
            ],
            f"side_{i}_entry_count": len(side["levy_entries"])+len(side["men_at_arms_entries"]),
        })
    return normalize_active_combat_resume_inputs_v1(receipt, parent=frame)


class BattleCurrentConditionFixtureTests(unittest.TestCase):
    """Two production-path cases with hand-calculated expected Q100000 results."""

    def test_current_native_order_and_positive_non_main_maa(self):
        frame = _normalized_frame(1)
        receipt = _normalized_roll_receipt(frame)
        condition = adapt_current_battle_condition(frame, active_resume_inputs=receipt)
        result = run_frozen_main_tick(condition, draw_state=DrawState(0, 0))
        self.check_case_one(condition, result)

    def test_integer_components_and_owner_hard_ledger_are_separate(self):
        frame = _normalized_frame(2)
        condition = adapt_current_battle_condition(frame,
            backing_components_by_regiment_id={
                99: (BackingComponent(1, 1), BackingComponent(4, 4)),
                3: (BackingComponent(4, 4), BackingComponent(1, 1)),
            })
        result = run_frozen_main_tick(condition, draw_state=DrawState(0, 0))
        self.check_case_two(condition, result)

    def check_case_one(self, condition, result):
        self.assertEqual(result["status"], "available")
        self.assertEqual([entry.state.regiment_id for entry in condition.sides[0].entries], [90, 7])
        self.assertEqual(condition.sides[0].entries[1].state.current_raw, 600_000)
        self.assertFalse(condition.sides[0].entries[1].fights_in_main_phase)
        self.assertEqual(result["outgoing_damage_raw_by_side"], [650_000, 250_000])
        sides = result["sides"]
        self.assertEqual([side["attack"]["effective_attack_after_counter_raw"] for side in sides],
                         [2_600_000, 1_000_000])
        self.assertEqual(sides[0]["attack"]["all_retained_maa_attack_raw"], 1_800_000)
        for i, side in enumerate(sides):
            self.assertEqual(side["attack"]["levy_damage_source"],
                             f"current_loss_inputs_v1.sides[{i}].levy_damage_raw")
            self.assertTrue(side["attack"]["native_primary_levy_getter_observed_by_runner"])
        self.assertEqual([side["attack"]["levy_damage_primary_participant_character_id"]
                          for side in sides], [29_829, 36_108])
        own_rows = sides[0]["losses"]["entries"]
        self.assertEqual([row["regiment_id"] for row in own_rows], [90, 7])
        self.assertEqual([row["current_fighting_raw_after"] for row in own_rows], [300_000, 450_000])
        self.assertEqual([row["new_hard_casualties_raw"] for row in own_rows], [50_000, 75_000])
        self.assertEqual([row["new_soft_casualties_raw"] for row in own_rows], [50_000, 75_000])
        self.assertIsNone(own_rows[1]["hard_casualties_raw_after"])
        self.assertTrue(all(row["backing_components"] is None for row in own_rows))
        self.assertEqual(sides[1]["losses"]["entries"][0]["current_fighting_raw_after"], 675_000)
        self.assertEqual([side["losses"]["new_hard_casualties_raw"] for side in sides], [125_000, 162_500])
        self.assertEqual([side["losses"]["new_soft_casualties_raw"] for side in sides], [125_000, 162_500])
        rolls = result["rolls"]
        self.assertEqual(rolls["input_draw_state"], {"counter": 0, "salt": 0})
        self.assertEqual(rolls["output_draw_state"], {"counter": 2, "salt": 0})
        self.assertEqual([row["sampled_roll_points"] for row in rolls["sides"]], [4, 2])
        for row in rolls["sides"]:
            self.assertIsInstance(row["sampled_draw31"], int)
            self.assertTrue(0 <= row["sampled_draw31"] < 2**31)
            self.assertEqual(row["distribution"]["span"], 1)
            self.assertEqual(row["distribution"]["base_preimage_count_per_point"], 2**31)
            self.assertEqual(row["distribution"]["extra_preimage_prefix_length"], 0)
        self.assertFalse(rolls["native_rng_state_observed"])
        self.assertFalse(rolls["sample_updates_current_loss_factor"])
        self.assertIsNone(rolls["next_roll_cadence_counter"])
        self.assertFalse(result["actual_next_draw_claimed"])
        self.assertFalse(result["complete_monte_carlo"])

    def check_case_two(self, condition, result):
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["outgoing_damage_raw_by_side"], [350_000, 0])
        side = result["sides"][1]
        self.assertEqual([row["public_cunit_id"] for row in side["ordered_armies"]], [33_554_657, 357])
        losses = side["losses"]
        rows = losses["entries"]
        self.assertEqual([row["regiment_id"] for row in rows], [99, 3])
        self.assertEqual([row["current_fighting_raw_after"] for row in rows], [325_000, 325_000])
        self.assertEqual([row["new_hard_casualties_raw"] for row in rows], [175_000, 175_000])
        self.assertEqual([row["hard_casualties_raw_before"] for row in rows], [200_000, 300_000])
        self.assertEqual([row["hard_casualties_raw_after"] for row in rows], [375_000, 475_000])
        self.assertEqual([row["new_soft_casualties_raw"] for row in rows], [0, 0])
        self.assertEqual([[c["current_soldiers_after"] for c in row["backing_components"]]
                          for row in rows], [[0, 4], [3, 1]])
        self.assertEqual([[c["whole_soldier_loss"] for c in row["backing_components"]]
                          for row in rows], [[1, 0], [1, 0]])
        self.assertEqual([row["backing_whole_soldier_loss"] for row in rows], [1, 1])
        self.assertEqual(losses["owner_hard_ledger_deltas"], [
            {"owner_character_id": 36_109, "hard_casualties_raw_delta": 175_000},
            {"owner_character_id": 36_108, "hard_casualties_raw_delta": 175_000},
        ])
        self.assertEqual(losses["participant_hard_total_raw_before"], 500_000)
        self.assertEqual(losses["participant_hard_total_raw_after"], 850_000)
        self.assertEqual([
            (row["row_index"], row["participant_character_id"],
             row["hard_casualties_raw_before"], row["hard_casualties_raw_delta"],
             row["hard_casualties_raw_after"])
            for row in losses["participant_hard_ledger"]
        ], [(0, 36_109, 200_000, 175_000, 375_000),
            (1, 36_108, 300_000, 175_000, 475_000)])
        self.assertFalse(losses["ledger_deltas_are_additional_fighting_deductions"])
        self.assertEqual(result["sides"][0]["attack"]["levy_damage_source"],
                         "uniform_current_entry_proxy_for_primary_owner_levy_damage")
        self.assertEqual(side["attack"]["levy_damage_source"], "not_needed_zero_cached_levy")
        self.assertFalse(result["sides"][0]["attack"]["native_primary_levy_getter_observed_by_runner"])
        self.assertEqual(result["rolls"]["output_draw_state"], {"counter": 0, "salt": 0})
        self.assertEqual([row["status"] for row in result["rolls"]["sides"]], ["unavailable", "unavailable"])
        self.assertFalse(result["complete_monte_carlo"])


if __name__ == "__main__":
    unittest.main()
