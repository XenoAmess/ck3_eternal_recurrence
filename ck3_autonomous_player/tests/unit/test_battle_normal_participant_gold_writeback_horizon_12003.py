from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from xar_autoplayer.simulation.battle_calendar_admission import (
    DailyDateStageInput, LoadedScheduleInputs,
)
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_normal_finalizer import (
    CurrentNormalFinalizerManagerInputs, CurrentNormalSummaryInputs,
    CurrentNormalOwnerRow, CurrentNormalParticipantResourceInputs,
)
from xar_autoplayer.simulation import battle_current_conditional_horizon as horizon
from xar_autoplayer.simulation.combat_core import DrawState


Q = 100_000
RESULTS: list[dict] = []


def _side(index: int, owner: int, army: dict) -> dict:
    current, soft, baseline = (
        (200_001, 100_002, 600_008) if index == 0 else
        (300_005, 100_007, 800_013)
    )
    hard = 1_000_000 - current - soft
    identity = {key: value for key, value in army.items() if key != "ordered_regiments"}
    identity["combat_backlink_id"] = 42
    entry = {
        "bucket": "levy", "bucket_index": 0,
        "regiment_id": army["ordered_regiments"][0]["regiment_id"],
        "native_carmy_id": army["native_carmy_id"],
        "public_cunit_id": army["public_cunit_id"], "owner_character_id": owner,
        "starting_raw": 1_000_000, "current_fighting_raw": current,
        "soft_casualties_raw": soft, "hard_casualties_raw": hard,
        "fights_in_main_phase": True, "effective_damage_raw": Q,
        "effective_toughness_raw": Q, "effective_pursuit_raw": 0,
        "effective_screen_raw": 0, "knight_character_id_raw": -1,
    }
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": owner,
        "selected_commander_character_id": -1, "current_roll_points": 0,
        "ordered_armies": [identity], "levy_entries": [entry], "men_at_arms_entries": [],
        "stored_current_fighting_raw": current, "stored_levy_current_fighting_raw": current,
        "derived_current_fighting_raw": current, "derived_soft_casualties_raw": soft,
        "derived_main_fighting_entry_hard_casualties_raw": hard,
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": [{"row_index": 0,
            "participant_character_id": owner, "hard_casualties_raw": 200_000}],
        "participant_hard_total_raw": 200_000,
        "stored_terminal_loss_baseline_raw": baseline,
    }


def _condition_and_census():
    armies = [{
        "native_carmy_id": 101 + index, "public_cunit_id": 1101 + index,
        "owner_character_id": owner,
        "ordered_regiments": [{"regiment_id": 901 + index, "current_soldiers": count}],
    } for index, (owner, count) in enumerate(((34_333, 7), (29_829, 3)))]
    census = {
        "scale": 1, "source_combat_id": 42, "source_target_province_id": 9,
        "enumeration_complete": True,
        "sides": [{"side_index": index, "ordered_armies": [army]}
                  for index, army in enumerate(armies)],
    }
    condition = adapt_current_battle_condition({
        "status": "available", "snapshot_revision": 1, "observed_date_raw": 1000,
        "combat_id": 42, "province_id": 9, "side_index": 1, "side_scope": "full_side",
        "phase": "done", "phase_raw": 3, "phase_day": 0,
        "base_combat_width": 10, "final_combat_width": 10,
        "roll_cadence_counter": 0, "base_advantage_raw": 0, "resolved_advantage_raw": 0,
        "attacker": _side(0, 34_333, armies[0]),
        "defender": _side(1, 29_829, armies[1]), "full_backing_inputs_v1": census,
    })
    maximums = {(army["native_carmy_id"], army["ordered_regiments"][0]["regiment_id"]):
                 army["ordered_regiments"][0]["current_soldiers"] for army in armies}
    return condition, census, maximums


class NormalParticipantGoldWritebackHorizon12003Test(unittest.TestCase):
    def test_public_horizon_distinguishes_integer_zero_share_and_gold_beneficiary(self):
        condition, census, maximums = _condition_and_census()
        participants = CurrentNormalParticipantResourceInputs(
            ordered_participant_full_ids=(34_333, 29_829),
            attacker_membership_by_participant={34_333: True, 29_829: False},
            owner_rows_by_side={
                0: (CurrentNormalOwnerRow(34_333, 250), CurrentNormalOwnerRow(35_991, 750)),
                1: (CurrentNormalOwnerRow(29_829, 1000),),
            },
            resolved_receiver_full_id_by_participant={34_333: 34_333, 29_829: 29_829},
            living_extension_present_by_participant={29_829: True},
            gold_before_raw_by_participant={29_829: 12_345},
            source_context={
                "kind": "explicit_conditional_2650F50_return_tape_and_264E380_outputs",
                "upstream_enumeration_or_membership_observed": False,
                "before_scope": "immediately_before_285EE87_only",
            },
        )
        summary_inputs = CurrentNormalSummaryInputs(
            evaluated_raw_by_kind={3: 10_000_000_000, 4: 20_000_000_000, 5: 35_000_000_000},
            source_context={"kind": "conditional_evaluator_results_not_actual_native_calls"},
        )
        terminal = horizon.ConditionalTerminalInputs(
            census, frozenset(), None, {"kind": "NEW1_participant_immediate_gold_store"},
            captured_maximum_by_regiment=maximums,
            side_baseline_raw_by_side={0: 600_008, 1: 800_013},
            normal_finalizer_manager=CurrentNormalFinalizerManagerInputs(
                "daily_row", True, pending_suppression_sweep=False, result_present=True,
            ),
            normal_finalizer_winner_raw=1, wipe_raw=False,
            normal_summary_inputs=summary_inputs,
            normal_participant_resource_inputs=participants,
        )
        row = horizon.ConditionalHorizonDay(
            DailyDateStageInput(1000, False, "already-phase3 conditional row"),
            LoadedScheduleInputs(None, None, "unreached calendar coefficients"),
            {"kind": "NEW1_participant_gold_writeback"}, terminal=terminal,
        )
        before = copy.deepcopy((condition, census, maximums, participants, terminal))
        with patch.object(horizon, "project_current_normal_finalizer",
                          wraps=horizon.project_current_normal_finalizer) as normal_call:
            result = horizon.run_conditional_horizon(
                condition, timeline=(row,), draw_state=DrawState(0, 17), max_days=1,
            )
        self.assertEqual(normal_call.call_count, 1)
        self.assertEqual(result.status, "available")
        final = result.terminal_result
        self.assertEqual(final["dispatch"]["branch"], "normal")
        projection = final["participant_resource_projection"]
        self.assertEqual(projection["status"], "available")
        self.assertIs(projection["summary_recomputed"], False)
        rows = projection["participants"]
        self.assertEqual([item["participant_full_id"] for item in rows], [34_333, 29_829])
        zero, beneficiary = rows
        self.assertEqual((zero["selected_side_index"], zero["side_total_signed32"],
                          zero["owner_weight_signed32"], zero["share_integer_quotient"],
                          zero["share_raw_q100000"]), (0, 1000, 250, 0, 0))
        self.assertEqual(tuple(zero["scaled_raw_slots"]), (0,) * 10)
        skipped = zero["slot0_writeback"]
        self.assertEqual(skipped["status"], "skipped")
        self.assertIs(skipped["store_reached"], False)
        self.assertIsNone(skipped["before_raw_q100000"])
        self.assertIsNone(skipped["after_at_store_raw_q100000"])
        self.assertEqual((beneficiary["selected_side_index"], beneficiary["side_total_signed32"],
                          beneficiary["owner_weight_signed32"], beneficiary["share_integer_quotient"],
                          beneficiary["share_raw_q100000"]), (1, 1000, 1000, 1, 100_000))
        self.assertEqual(beneficiary["beneficiary_character_id"], 29_829)
        store = beneficiary["slot0_writeback"]
        self.assertEqual(store["status"], "available")
        self.assertIs(store["store_reached"], True)
        self.assertEqual((store["before_raw_q100000"], store["delta_raw_q100000"],
                          store["after_at_store_raw_q100000"]),
                         (12_345, 70_000_600, 70_012_945))
        self.assertEqual(store["currency_alias"], "personal_gold")
        self.assertIsNone(store["final_gold_raw_q100000"])
        self.assertEqual(beneficiary["scaled_raw_slots"][0], 70_000_600)
        self.assertIs(projection["actual_balance_committed"], False)
        self.assertIs(projection["complete_receiver_effects"], False)
        self.assertIs(final["complete_native_finalizer"], False)
        self.assertIs(final["actual_native_effects_executed"], False)
        self.assertIs(final["prior_losses_reapplied"], False)
        self.assertEqual([item["hard_loss_raw_q100000"]
                          for item in final["normal_numeric_accounting"]["sides"]],
                         [300_005, 400_001])
        self.assertEqual(result.actual_game_days_advanced, 0)
        self.assertFalse(result.complete_native_transition)
        self.assertFalse(result.complete_monte_carlo)
        self.assertFalse(result.win_probability_ready)
        self.assertEqual((condition, census, maximums, participants, terminal), before)
        RESULTS.append({
            "case": "public_horizon_participant_integer_share_and_immediate_gold_store_NEW1",
            "status": "GREEN", "production_public_horizon_calls": 1,
            "production_normal_adapter_calls": normal_call.call_count,
            "participant_resource_projection": projection,
            "summary_slot0_raw": final["normal_summary_projection"]["summary_raw_slots"][0],
            "actual_upstream_enumeration_observed": False,
            "actual_native_effects_executed": False,
            "actual_return_time_or_committed_gold_claimed": False,
            "stats38_modeled": False, "inputs_unchanged": True,
            "game_days_advanced": 0,
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
