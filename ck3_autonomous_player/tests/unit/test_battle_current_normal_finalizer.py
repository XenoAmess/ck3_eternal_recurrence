from __future__ import annotations

import copy
import unittest

from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_backing_reaggregation import CurrentPhase3BackingState
from xar_autoplayer.simulation.battle_current_normal_finalizer import (
    CurrentNormalFinalizerManagerInputs,
    project_current_normal_finalizer,
)
from xar_autoplayer.simulation.combat_core import BackingComponent


Q = 100_000
COMBAT = 335_544_325
PROVINCE = 2586
RESULTS: list[dict] = []


def _army(native: int, regiments: list[tuple[int, int]]) -> dict:
    return {
        "native_carmy_id": native, "public_cunit_id": 83_886_341 + native,
        "owner_character_id": 29_829 if native < 200 else 36_108,
        "ordered_regiments": [{"regiment_id": regiment, "current_soldiers": current}
                              for regiment, current in regiments],
    }


def _side(index: int, armies: list[dict]) -> dict:
    owner = 29_829 if index == 0 else 36_108
    ordered = [{key: value for key, value in army.items() if key != "ordered_regiments"}
               for army in armies]
    for army in ordered:
        army["combat_backlink_id"] = COMBAT
    entries = []
    if armies and armies[0]["ordered_regiments"]:
        army = armies[0]
        entries.append({
            "bucket": "levy", "bucket_index": 0,
            "regiment_id": army["ordered_regiments"][0]["regiment_id"],
            "native_carmy_id": army["native_carmy_id"],
            "public_cunit_id": army["public_cunit_id"],
            "owner_character_id": owner, "starting_raw": 8*Q+63,
            "current_fighting_raw": 5*Q+39, "soft_casualties_raw": 2*Q+7,
            "hard_casualties_raw": Q+17, "fights_in_main_phase": True,
            "effective_damage_raw": Q, "effective_toughness_raw": Q,
            "effective_pursuit_raw": 0, "effective_screen_raw": 0,
            "knight_character_id_raw": -1,
        })
    current = entries[0]["current_fighting_raw"] if entries else 0
    soft = 2*Q+7 if entries else 0
    entry_hard = Q+17 if entries else 0
    ledger = [{"row_index": 0, "participant_character_id": owner,
               "hard_casualties_raw": 17*Q+19}] if entries else []
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": owner, "selected_commander_character_id": -1,
        "current_roll_points": 0, "ordered_armies": ordered,
        "levy_entries": entries, "men_at_arms_entries": [],
        "stored_current_fighting_raw": current, "stored_levy_current_fighting_raw": current,
        "derived_current_fighting_raw": current, "derived_soft_casualties_raw": soft,
        "derived_main_fighting_entry_hard_casualties_raw": entry_hard,
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": ledger,
        "participant_hard_total_raw": 17*Q+19 if entries else 0,
        "stored_terminal_loss_baseline_raw": 30*Q+67 if entries else 0,
    }


def _condition():
    own = [_army(101, [(900, 101), (17, 200)]), _army(102, [(3, 9)]),
           _army(103, [(77, 2_147_483_647), (78, 2_147_483_647)])]
    enemy = []
    return adapt_current_battle_condition({
        "status": "available", "snapshot_revision": 58,
        "observed_date_raw": 53_251_272, "combat_id": COMBAT,
        "province_id": PROVINCE, "side_index": 0, "side_scope": "full_side",
        "phase": "done", "phase_raw": 3, "phase_day": 0,
        "base_combat_width": 10, "final_combat_width": 10,
        "roll_cadence_counter": 3, "base_advantage_raw": 0, "resolved_advantage_raw": 0,
        "attacker": _side(0, own), "defender": _side(1, enemy),
        "full_backing_inputs_v1": {
            "scale": 1, "source_combat_id": COMBAT,
            "source_target_province_id": PROVINCE, "enumeration_complete": True,
            "sides": [{"side_index": 0, "ordered_armies": own},
                      {"side_index": 1, "ordered_armies": enemy}],
        },
    })


def _carried_state():
    # These are explicit component after-values, not instructions to apply an
    # earlier loss. The actual whole-backing census remains the membership.
    return {
        (101, 900): CurrentPhase3BackingState(
            (BackingComponent(100, 71, 0), BackingComponent(60, 25, 1)), "absent"),
        (101, 17): CurrentPhase3BackingState((BackingComponent(300, 200, 0),), "valid"),
    }


class CurrentNormalFinalizerFocusedTests(unittest.TestCase):
    def test_normal_daily_postwork_preserves_carried_counts_and_ledger(self):
        condition = _condition()
        state = _carried_state()
        manager = CurrentNormalFinalizerManagerInputs(
            entry_kind="daily_row", combat_manager_row_admitted=True,
            pending_suppression_sweep=False,
            primary_hostile=None, finalized=None, processing=None,
            result_present=None, source_context={"kind": "explicit_synthetic_postwork"},
        )
        previous = copy.deepcopy((condition, state, manager))
        result = project_current_normal_finalizer(
            condition, manager=manager, current_state_by_regiment=state,
            recomputed_regiments={(101, 900), (101, 17)},
            captured_maximum_by_regiment={(102, 3): 23,
                                         (103, 77): 2_147_483_647,
                                         (103, 78): 2_147_483_647},
            winner_raw=0, wipe_raw=False,
        )
        self.assertEqual(result["status"], "available")
        dispatch = result["dispatch"]
        self.assertEqual(dispatch["branch"], "normal")
        self.assertIs(dispatch["normal_result_intent"], True)
        self.assertIs(dispatch["suppression_argument"], False)
        self.assertIs(dispatch["finalizer_invoked_conditionally"], True)
        self.assertIs(dispatch["removal_intent"], True)
        self.assertIs(dispatch["processing_for_selected_row"], False)
        self.assertEqual(result["typed_gaps"], ())
        self.assertIsNone(result["result_present_input"])
        self.assertEqual((result["winner_raw"], result["winner_side"], result["loser_side"]), (0, 0, 1))
        backing = result["backing_reaggregation"]
        own_backing = backing["sides"][0]
        rows = [row for army in own_backing["ordered_armies"] for row in army["ordered_regiments"]]
        self.assertEqual([row["regiment_id"] for row in rows], [900, 17, 3, 77, 78])
        self.assertEqual([row["current_soldiers"] for row in rows], [96, 1, 9, 2_147_483_647, 2_147_483_647])
        self.assertEqual([row["recomputed_in_count_context"] for row in rows], [True, True, False, False, False])
        self.assertEqual(own_backing["current_soldiers"], 4_294_967_400)
        account = result["normal_numeric_accounting"]
        own, empty = account["sides"]
        self.assertEqual(own["hard_loss_raw_q100000"], 2_300_021)
        self.assertEqual(own["result_row_baseline_whole_signed32"], 30)
        self.assertEqual(own["result_row_hard_whole_signed32"], 23)
        self.assertEqual(own["backing_current_whole_signed32"], 104)
        self.assertEqual(own["final_survivors_raw_q100000"], 10_400_000)
        self.assertEqual(empty["hard_loss_raw_q100000"], 0)
        self.assertEqual(empty["backing_current_whole_signed32"], 0)
        self.assertEqual(empty["final_survivors_raw_q100000"], 0)
        self.assertEqual(own["participant_hard_total_raw_q100000"], 1_700_019)
        self.assertEqual(own["participant_hard_ledger"], [
            {"row_index": 0, "participant_character_id": 29_829,
             "hard_casualties_raw": 1_700_019}])
        self.assertNotEqual(own["stored_current_fighting_raw_q100000"], own["final_survivors_raw_q100000"])
        self.assertIs(account["participant_hard_ledger_debited"], False)
        self.assertIs(account["current_components_debited"], False)
        self.assertIs(result["prior_losses_reapplied"], False)
        self.assertIs(result["owner_hard_ledger_debited"], False)
        self.assertEqual(result["war_battle_row_projection"]["status"], "partial")
        self.assertIsNone(result["war_battle_row_projection"]["row_created_conditionally"])
        self.assertIsNone(result["war_battle_row_projection"]["attacker_relative_delta_raw_q100000"])
        self.assertIs(result["complete_native_finalizer"], False)
        self.assertIs(result["actual_native_effects_executed"], False)
        self.assertIs(result["old_combat_removed_observed"], False)
        self.assertIs(result["war_settlement_observed"], False)
        self.assertIs(result["named_character_outcomes_predicted"], False)
        self.assertEqual((condition, state, manager), previous)
        RESULTS.append({
            "case": "normal_daily_with_unconsulted_missing_metadata",
            "status": result["status"], "dispatch_branch": dispatch["branch"],
            "native_order_backing_whole_counts": [96, 1, 9, 2_147_483_647, 2_147_483_647],
            "old_helper_unbounded_whole_sum": 4_294_967_400,
            "final_survivors_raw_q100000": [10_400_000, 0],
            "hard_loss_raw_q100000": [2_300_021, 0],
            "normal_result_row_whole_signed32": [30, 23],
            "participant_hard_ledger_raw_q100000_unchanged": 1_700_019,
            "inputs_unchanged": True, "prior_losses_reapplied": False,
            "actual_result_or_war_settlement_claimed": False,
        })

    def test_suppressed_daily_sweep_skips_missing_backing_not_zero(self):
        condition = _condition()
        missing_backing = {"enumeration_complete": False}
        manager = CurrentNormalFinalizerManagerInputs(
            entry_kind="daily_row", combat_manager_row_admitted=True,
            pending_suppression_sweep=True, primary_hostile=False,
            finalized=False, processing=None, result_present=None,
            source_context={"kind": "explicit_synthetic_pending_sweep"},
        )
        previous = copy.deepcopy((condition, missing_backing, manager))
        result = project_current_normal_finalizer(
            condition, manager=manager, current_state_by_regiment=None,
            backing_inputs_v1=missing_backing, winner_raw=-1, wipe_raw=None,
        )
        self.assertEqual(result["status"], "available")
        dispatch = result["dispatch"]
        self.assertEqual(dispatch["branch"], "suppressed")
        self.assertIs(dispatch["normal_result_intent"], False)
        self.assertIs(dispatch["suppression_argument"], True)
        self.assertIs(dispatch["finalizer_invoked_conditionally"], True)
        self.assertIs(dispatch["removal_intent"], True)
        self.assertIs(dispatch["processing_for_selected_row"], False)
        self.assertEqual(result["typed_gaps"], ())
        self.assertIsNone(result["backing_reaggregation"])
        self.assertIsNone(result["normal_numeric_accounting"])
        self.assertIsNone(result["losing_side_hard_raw_q100000"])
        self.assertEqual(result["winner_raw"], -1)
        self.assertIsNone(result["winner_side"])
        self.assertIsNone(result["loser_side"])
        row = result["war_battle_row_projection"]
        self.assertEqual(row["status"], "not_produced")
        self.assertIs(row["row_created_conditionally"], False)
        self.assertIsNone(row["attacker_relative_delta_raw_q100000"])
        self.assertIs(result["prior_losses_reapplied"], False)
        self.assertIs(result["owner_hard_ledger_debited"], False)
        self.assertIs(result["complete_native_finalizer"], False)
        self.assertIs(result["war_settlement_observed"], False)
        self.assertIs(result["named_character_outcomes_predicted"], False)
        self.assertEqual((condition, missing_backing, manager), previous)
        RESULTS.append({
            "case": "suppressed_daily_pending_sweep_with_missing_backing",
            "status": result["status"], "dispatch_branch": dispatch["branch"],
            "processing_derived_postwork": False, "winner_raw": -1,
            "winner_side": None, "loser_side": None,
            "normal_numeric_accounting": None, "backing_reaggregation": None,
            "war_row_created_conditionally": False,
            "missing_backing_was_zero_filled": False, "inputs_unchanged": True,
            "actual_result_or_war_settlement_claimed": False,
        })


if __name__ == "__main__":
    unittest.main()
