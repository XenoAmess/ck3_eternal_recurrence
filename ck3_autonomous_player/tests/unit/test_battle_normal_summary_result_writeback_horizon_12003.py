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
)
from xar_autoplayer.simulation import battle_current_conditional_horizon as horizon
from xar_autoplayer.simulation.combat_core import DrawState


Q = 100_000
COMBAT = 42
PROVINCE = 9
RESULTS: list[dict] = []


def _army(native: int, owner: int, regiments: tuple[tuple[int, int], ...]) -> dict:
    return {
        "native_carmy_id": native, "public_cunit_id": native + 1000,
        "owner_character_id": owner,
        "ordered_regiments": [{"regiment_id": regiment, "current_soldiers": current}
                              for regiment, current in regiments],
    }


def _side(index: int, armies: list[dict]) -> dict:
    owner = 29_829 if index == 0 else 35_991
    current, soft, baseline = (
        (200_001, 100_002, 600_008) if index == 0 else
        (300_005, 100_007, 800_013)
    )
    army = armies[0]
    entry_hard = 1_000_000 - current - soft
    entry = {
        "bucket": "levy", "bucket_index": 0,
        "regiment_id": army["ordered_regiments"][0]["regiment_id"],
        "native_carmy_id": army["native_carmy_id"],
        "public_cunit_id": army["public_cunit_id"],
        "owner_character_id": owner,
        "starting_raw": 1_000_000, "current_fighting_raw": current,
        "soft_casualties_raw": soft, "hard_casualties_raw": entry_hard,
        "fights_in_main_phase": True,
        "effective_damage_raw": Q, "effective_toughness_raw": Q,
        "effective_pursuit_raw": 0, "effective_screen_raw": 0,
        "knight_character_id_raw": -1,
    }
    ordered = [{key: value for key, value in row.items() if key != "ordered_regiments"}
               for row in armies]
    for row in ordered:
        row["combat_backlink_id"] = COMBAT
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": owner,
        "selected_commander_character_id": -1, "current_roll_points": 0,
        "ordered_armies": ordered, "levy_entries": [entry], "men_at_arms_entries": [],
        "stored_current_fighting_raw": current, "stored_levy_current_fighting_raw": current,
        "derived_current_fighting_raw": current, "derived_soft_casualties_raw": soft,
        "derived_main_fighting_entry_hard_casualties_raw": entry_hard,
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": [{"row_index": 0,
            "participant_character_id": owner, "hard_casualties_raw": 3_700_019}],
        "participant_hard_total_raw": 3_700_019,
        "stored_terminal_loss_baseline_raw": baseline,
    }


def _condition_and_census():
    own = [_army(101, 29_829, ((901, 2_147_483_647), (902, 2_147_483_647))),
           _army(102, 29_829, ((903, 13),))]
    enemy = [_army(201, 35_991, ((911, 9), (912, 4)))]
    census = {
        "scale": 1, "source_combat_id": COMBAT,
        "source_target_province_id": PROVINCE, "enumeration_complete": True,
        "sides": [{"side_index": 0, "ordered_armies": own},
                  {"side_index": 1, "ordered_armies": enemy}],
    }
    condition = adapt_current_battle_condition({
        "status": "available", "snapshot_revision": 1, "observed_date_raw": 1000,
        "combat_id": COMBAT, "province_id": PROVINCE,
        "side_index": 0, "side_scope": "full_side",
        "phase": "done", "phase_raw": 3, "phase_day": 0,
        "base_combat_width": 10, "final_combat_width": 10,
        "roll_cadence_counter": 0, "base_advantage_raw": 0, "resolved_advantage_raw": 0,
        "attacker": _side(0, own), "defender": _side(1, enemy),
        "full_backing_inputs_v1": census,
    })
    maximums = {(army["native_carmy_id"], row["regiment_id"]): row["current_soldiers"]
        for side in census["sides"] for army in side["ordered_armies"]
        for row in army["ordered_regiments"]}
    return condition, census, maximums


class NormalSummaryResultWritebackHorizon12003Test(unittest.TestCase):
    def test_public_horizon_projects_concrete_summary_result_overwrites(self):
        condition, census, maximums = _condition_and_census()
        before = {"0x48": 111, "0x50": 222, "0x58": 333}
        summary_inputs = CurrentNormalSummaryInputs(
            evaluated_raw_by_kind={3: 10_000_000_000, 4: 20_000_000_000, 5: 35_000_000_000},
            source_context={
                "kind": "explicit_synthetic_evaluated_37542F0_results",
                "caller_result_raw_before_by_offset": before,
                "actual_native_evaluation_observed": False,
            },
        )
        terminal = horizon.ConditionalTerminalInputs(
            census, frozenset(), None,
            {"kind": "source_closed_normal_summary_result_writeback_NEW1"},
            captured_maximum_by_regiment=maximums,
            side_baseline_raw_by_side={0: 600_008, 1: 800_013},
            normal_finalizer_manager=CurrentNormalFinalizerManagerInputs(
                "daily_row", True, pending_suppression_sweep=False,
                primary_hostile=None, finalized=None, processing=None,
                result_present=True,
            ),
            normal_finalizer_winner_raw=0, wipe_raw=False,
            normal_summary_inputs=summary_inputs,
        )
        row = horizon.ConditionalHorizonDay(
            DailyDateStageInput(1000, False, "explicit already-phase3 fixture row"),
            LoadedScheduleInputs(None, None, "unreached calendar coefficients"),
            {"kind": "NEW1_normal_summary_result_writeback"}, terminal=terminal,
        )
        original = copy.deepcopy((condition, census, maximums, summary_inputs, terminal, before))
        # This is the sole new public-horizon call. The spy delegates to the
        # production normal adapter; it supplies no replacement result.
        with patch.object(horizon, "project_current_normal_finalizer",
                          wraps=horizon.project_current_normal_finalizer) as normal_call:
            result = horizon.run_conditional_horizon(
                condition, timeline=(row,), draw_state=DrawState(0, 17), max_days=1,
            )
        self.assertEqual(normal_call.call_count, 1)
        self.assertEqual(result.status, "available")
        self.assertEqual(result.typed_gaps, ())
        final = result.terminal_result
        self.assertIsNotNone(final)
        self.assertEqual(final["dispatch"]["branch"], "normal")
        self.assertIs(final["dispatch"]["normal_result_intent"], True)
        self.assertEqual(final["status"], "available")
        account = final["normal_numeric_accounting"]
        self.assertEqual([side["hard_loss_raw_q100000"] for side in account["sides"]],
                         [300_005, 400_001])
        self.assertEqual([side["backing_current_whole_signed32"] for side in account["sides"]],
                         [11, 13])
        self.assertEqual([side["final_survivors_raw_q100000"] for side in account["sides"]],
                         [1_100_000, 1_300_000])
        self.assertEqual(final["losing_side_hard_raw_q100000"], 400_001)
        self.assertEqual([side["participant_hard_total_raw_q100000"] for side in account["sides"]],
                         [3_700_019, 3_700_019])
        self.assertIs(account["participant_hard_ledger_debited"], False)
        self.assertIs(account["current_components_debited"], False)
        self.assertIs(final["prior_losses_reapplied"], False)

        summary = final["normal_summary_projection"]
        self.assertEqual(summary["status"], "available")
        self.assertEqual(summary["combined_hard_raw_q100000"], 700_006)
        self.assertEqual(summary["scale"], 100_000)
        self.assertEqual(summary["denominator_raw_q100000"], 100_000_000)
        self.assertEqual(tuple(summary["summary_raw_slots"]),
                         (70_000_600, 140_001_200, 245_002_100, 0, 0, 0, 0, 0, 0, 0))
        self.assertEqual([evaluation["kind"] for evaluation in summary["evaluations"]],
                         [3, 5, 4])
        self.assertEqual([evaluation["fixed_mul_raw_q100000"]
                          for evaluation in summary["evaluations"]],
                         [70_000_600_000, 245_002_100_000, 140_001_200_000])
        self.assertEqual([evaluation["fixed_mul_branch"]
                          for evaluation in summary["evaluations"]],
                         ["signed_max_split", "signed_max_split", "signed_max_split"])
        self.assertEqual([evaluation["fixed_div_branch"]
                          for evaluation in summary["evaluations"]],
                         ["fast", "fast", "fast"])
        after = summary["result_raw_by_offset"]
        self.assertEqual({offset: after[offset] for offset in before},
                         {"0x48": 70_000_600, "0x50": 140_001_200, "0x58": 245_002_100})
        for offset, value in before.items():
            self.assertNotEqual(after[offset], value)
        self.assertEqual(summary["result_writeback"], {
            "operation": "overwrite", "bytes": 80,
            "start_offset": "0x48", "end_exclusive_offset": "0x98",
        })
        self.assertIs(summary["actual_evaluator_executed"], False)
        self.assertIs(summary["actual_balance_committed"], False)
        self.assertIs(summary["complete_native_finalizer"], False)
        self.assertIs(final["complete_native_finalizer"], False)
        self.assertIs(final["actual_native_effects_executed"], False)
        self.assertTrue(any(gap.stage == "normal_summary"
                            for gap in final["unmodeled_effect_branches"]))
        self.assertIs(final["old_combat_removed_observed"], False)
        self.assertIs(final["war_settlement_observed"], False)
        self.assertIs(final["named_character_outcomes_predicted"], False)
        self.assertFalse(result.complete_native_transition)
        self.assertFalse(result.complete_monte_carlo)
        self.assertFalse(result.win_probability_ready)
        self.assertEqual(result.actual_game_days_advanced, 0)
        self.assertEqual(result.modeled_date_raw, 1000)
        self.assertEqual(result.modeled_accepted_invocations, 0)
        self.assertEqual((condition, census, maximums, summary_inputs, terminal, before), original)
        RESULTS.append({
            "case": "public_horizon_normal_summary_result_overwrites_NEW1",
            "status": "GREEN", "production_public_horizon_calls": 1,
            "production_normal_adapter_calls": normal_call.call_count,
            "result_raw_before_by_offset": before,
            "normal_summary_projection": summary,
            "hard_loss_raw_q100000": [300_005, 400_001],
            "final_survivors_raw_q100000": [1_100_000, 1_300_000],
            "complete_native_finalizer": False, "actual_native_effects_executed": False,
            "actual_resource_balance_committed": False, "stats38_modeled": False,
            "inputs_unchanged": True, "game_days_advanced": 0,
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
