from __future__ import annotations

import copy
import unittest

from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_backing_reaggregation import (
    CurrentPhase3BackingState,
    reaggregate_current_phase3_backing,
)
from xar_autoplayer.simulation.battle_current_terminal import project_current_terminal_accounting
from xar_autoplayer.simulation.combat_core import BackingComponent


Q = 100_000
COMBAT = 335_544_325
PROVINCE = 2586
RESULTS: list[dict] = []


def _army(native: int, regiments: list[tuple[int, int]]) -> dict:
    return {
        "native_carmy_id": native,
        "public_cunit_id": 83_886_341 + native,
        "owner_character_id": 29_829 if native < 200 else 36_108,
        "ordered_regiments": [
            {"regiment_id": regiment, "current_soldiers": current}
            for regiment, current in regiments
        ],
    }


def _side(index: int, armies: list[dict]) -> dict:
    owner = 29_829 if index == 0 else 36_108
    ordered = [{key: value for key, value in army.items()
                if key != "ordered_regiments"} for army in armies]
    for army in ordered:
        army["combat_backlink_id"] = COMBAT
    entry = None
    if armies and armies[0]["ordered_regiments"]:
        army = armies[0]
        entry = {
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
        }
    current = 0 if entry is None else entry["current_fighting_raw"]
    return {
        "side_index": index, "role": "attacker" if index == 0 else "defender",
        "primary_participant_character_id": owner,
        "selected_commander_character_id": -1, "current_roll_points": 0,
        "ordered_armies": ordered, "levy_entries": [] if entry is None else [entry],
        "men_at_arms_entries": [], "stored_current_fighting_raw": current,
        "stored_levy_current_fighting_raw": current,
        "derived_current_fighting_raw": current,
        "derived_soft_casualties_raw": 0 if entry is None else 2*Q+7,
        "derived_main_fighting_entry_hard_casualties_raw": 0 if entry is None else Q+17,
        "non_main_start_minus_current_minus_soft_raw": 0,
        "participant_hard_ledger": [{"row_index": 0,
            "participant_character_id": owner, "hard_casualties_raw": 17*Q+19}],
        "participant_hard_total_raw": 17*Q+19,
        "stored_terminal_loss_baseline_raw": 30*Q+67,
    }


def _condition(own: list[dict], enemy: list[dict]):
    census = {
        "scale": 1, "source_combat_id": COMBAT,
        "source_target_province_id": PROVINCE, "enumeration_complete": True,
        "sides": [{"side_index": 0, "ordered_armies": own},
                  {"side_index": 1, "ordered_armies": enemy}],
    }
    snapshot = {
        "status": "available", "snapshot_revision": 58,
        "observed_date_raw": 53_251_272, "combat_id": COMBAT,
        "province_id": PROVINCE, "side_index": 0, "side_scope": "full_side",
        "phase": "done", "phase_raw": 3, "phase_day": 0,
        "base_combat_width": 10, "final_combat_width": 10,
        "roll_cadence_counter": 3, "base_advantage_raw": 0,
        "resolved_advantage_raw": 0,
        "attacker": _side(0, own), "defender": _side(1, enemy),
        "full_backing_inputs_v1": census,
    }
    return adapt_current_battle_condition(snapshot)


class CurrentPhase3BackingReaggregationFocusedTests(unittest.TestCase):
    def test_carried_mixed_counts_preserve_native_order_and_do_not_debit_twice(self):
        # Census membership/order is genuine input. Its observed pre-transfer
        # integers are not the already-carried component after-values below.
        condition = _condition(
            [_army(101, [(900, 101), (17, 200), (500, 7)]),
             _army(102, [(3, 9)])], [])
        previous = copy.deepcopy(condition)
        state = {
            (101, 900): CurrentPhase3BackingState(
                (BackingComponent(100, 71, 0), BackingComponent(60, 25, 1),
                 BackingComponent(2_147_483_647, 0, 0)), "absent"),
            (101, 17): CurrentPhase3BackingState((BackingComponent(300, 200, 0),), "valid"),
            (101, 500): CurrentPhase3BackingState(
                (BackingComponent(41, 0, 3), BackingComponent(99, 7, 3),
                 BackingComponent(11, 0, 0), BackingComponent(19, -2, 3)), "invalid"),
            # This row is outside the selected clear/reaggregation scope.
            # Its supplied state would count41 if wrongly recomputed.
            (102, 3): CurrentPhase3BackingState((BackingComponent(41, 0, 3),), "invalid"),
        }
        old_state = copy.deepcopy(state)
        result = reaggregate_current_phase3_backing(
            condition, current_state_by_regiment=state,
            recomputed_regiments={(101, 900), (101, 17), (101, 500)},
            captured_maximum_by_regiment={(102, 3): 23})
        self.assertEqual(result["status"], "available")
        side = result["sides"][0]
        self.assertEqual([row["native_carmy_id"] for row in side["ordered_armies"]], [101, 102])
        rows = [row for army in side["ordered_armies"] for row in army["ordered_regiments"]]
        self.assertEqual([row["regiment_id"] for row in rows], [900, 17, 500, 3])
        self.assertEqual([row["current_soldiers"] for row in rows], [96, 1, 46, 9])
        self.assertEqual([row["maximum_soldiers"] for row in rows], [-2_147_483_489, 1, 170, 23])
        self.assertEqual((side["current_soldiers"], side["maximum_soldiers"]), (152, -2_147_483_295))
        self.assertEqual(side["terminal_current_raw_q100000"], 15_200_000)
        self.assertEqual([(row.native_carmy_id, row.regiment_id, row.current_soldiers)
                          for row in result["backing_current_by_side"][0]],
                         [(101, 900, 96), (101, 17, 1), (101, 500, 46), (102, 3, 9)])
        terminal = project_current_terminal_accounting(
            condition, stop_reason="explicit_phase3_fixture", winner_side=0,
            normal_result_intent=True, backing_current_by_side=result["backing_current_by_side"])
        self.assertEqual(terminal["sides"][0]["final_survivors_raw_q100000"], 15_200_000)
        self.assertEqual(terminal["sides"][1]["final_survivors_raw_q100000"], 0)
        self.assertEqual(condition, previous)
        self.assertEqual(state, old_state)
        self.assertEqual(condition.sides[0].participant_hard_total_raw, 1_700_019)
        self.assertEqual(condition.sides[0].entries[0].state.soft_casualties_raw, 200_007)
        self.assertNotEqual(terminal["sides"][0]["stored_current_fighting_raw_q100000"],
                            terminal["sides"][0]["final_survivors_raw_q100000"])
        RESULTS.append({"case": "mixed_order_and_carried_after_values", "status": result["status"],
                        "current": [96, 1, 46, 9], "maximum": [-2_147_483_489, 1, 170, 23],
                        "total_current": 152, "total_maximum": -2_147_483_295,
                        "terminal_q100000": 15_200_000, "input_and_ledgers_unchanged": True})

    def test_genuine_zero_differs_from_unavailable_strict_link(self):
        condition = _condition([_army(101, [(700, 0)]), _army(102, [])],
                               [_army(202, [(8, 10), (9, 1)])])
        result = reaggregate_current_phase3_backing(condition, current_state_by_regiment={
            (101, 700): CurrentPhase3BackingState((), "absent"),
            (202, 8): CurrentPhase3BackingState((BackingComponent(17, 10, 0),), "unavailable"),
            (202, 9): CurrentPhase3BackingState(None, "valid"),
        })
        self.assertEqual(result["status"], "partial")
        zero, unknown = result["sides"]
        self.assertEqual((zero["current_soldiers"], zero["maximum_soldiers"]), (0, 0))
        self.assertEqual(zero["terminal_current_raw_q100000"], 0)
        self.assertEqual(zero["ordered_armies"][1]["ordered_regiments"], [])
        self.assertEqual([(row.regiment_id, row.current_soldiers)
                          for row in result["backing_current_by_side"][0]], [(700, 0)])
        unavailable, valid = unknown["ordered_armies"][0]["ordered_regiments"]
        self.assertIsNone(unavailable["current_soldiers"])
        self.assertIsNone(unavailable["maximum_soldiers"])
        self.assertTrue(unavailable["unavailable_inputs"])
        self.assertEqual((valid["current_soldiers"], valid["maximum_soldiers"]), (1, 1))
        self.assertIsNone(unknown["current_soldiers"])
        self.assertIsNone(unknown["maximum_soldiers"])
        self.assertIsNone(unknown["terminal_current_raw_q100000"])
        self.assertIsNone(result["backing_current_by_side"][1])
        terminal = project_current_terminal_accounting(
            condition, stop_reason="explicit_phase3_fixture", winner_side=0,
            normal_result_intent=True, backing_current_by_side=result["backing_current_by_side"])
        self.assertEqual(terminal["sides"][0]["final_survivors_raw_q100000"], 0)
        self.assertIsNone(terminal["sides"][1]["final_survivors_raw_q100000"])
        RESULTS.append({"case": "legitimate_zero_and_unavailable_strict_link", "status": result["status"],
                        "side0_current": 0, "side0_maximum": 0, "side0_terminal_q100000": 0,
                        "side1_current": None, "side1_terminal_q100000": None,
                        "unknown_row_current": None, "independently_valid_link_current": 1})


if __name__ == "__main__":
    unittest.main()
