from __future__ import annotations

from dataclasses import replace
import unittest

from xar_autoplayer.simulation.battle_current_adapter import (
    CurrentBattleCondition,
    CurrentBattleEntry,
    CurrentBattleSide,
    CurrentLossInputs,
    CurrentLossSideInputs,
)
from xar_autoplayer.simulation.battle_current_pursuit import run_current_pursuit_ticks
from xar_autoplayer.simulation.combat_core import (
    BackingComponent,
    CombatRegimentState,
    RegimentKind,
)


Q = 100_000


def _entry(regiment_id: int, index: int, current: int,
           soft: int, soldiers: int) -> CurrentBattleEntry:
    components = (BackingComponent(soldiers, soldiers),)
    return CurrentBattleEntry(
        state=CombatRegimentState(
            regiment_id=regiment_id, kind=RegimentKind.LEVY,
            current_raw=current, soft_casualties_raw=soft, toughness_raw=Q,
            pursuit_raw=0, screen_raw=0, components=components,
        ),
        bucket="levy", bucket_index=index, native_carmy_id=102,
        public_cunit_id=83_886_342, owner_character_id=36_108,
        starting_raw=current+soft, effective_damage_raw=Q,
        fights_in_main_phase=True, hard_casualties_raw=0,
        knight_character_id_raw=None, backing_components=components,
        source_entry={"regiment_id": regiment_id},
    )


def _side(index: int, entries: tuple[CurrentBattleEntry, ...],
          loss: CurrentLossSideInputs) -> CurrentBattleSide:
    current = sum(entry.state.current_raw for entry in entries)
    soft = sum(entry.state.soft_casualties_raw for entry in entries)
    owner = 29_829 if index == 0 else 36_108
    ledger = ({"row_index": 0, "participant_character_id": owner,
               "hard_casualties_raw": 100_007},) if index == 1 else ()
    return CurrentBattleSide(
        side_index=index, role="attacker" if index == 0 else "defender",
        primary_participant_character_id=owner,
        selected_commander_character_id=-1, current_roll_points=0,
        roll_request=None, entries=entries,
        ordered_armies=({"native_carmy_id": 101+index,
                        "public_cunit_id": 83_886_341+index,
                        "owner_character_id": owner,
                        "combat_backlink_id": 335_544_325},),
        stored_current_fighting_raw=current,
        stored_levy_current_fighting_raw=current,
        derived_current_fighting_raw=current,
        derived_soft_casualties_raw=soft,
        derived_main_fighting_entry_hard_casualties_raw=0,
        non_main_start_minus_current_minus_soft_raw=0,
        participant_hard_ledger=ledger,
        participant_hard_total_raw=100_007 if index == 1 else 0,
        loss_inputs=loss, levy_damage_raw=None,
        levy_damage_source="unavailable", levy_damage_native_observed=False,
        levy_damage_primary_participant_character_id=None,
    )


def _condition() -> CurrentBattleCondition:
    side_loss = (
        CurrentLossSideInputs(0, Q, 0, 0),
        CurrentLossSideInputs(1, Q, 0, 0),
    )
    loss = CurrentLossInputs(
        scale=Q, source_combat_id=335_544_325,
        source_target_province_id=2586, stored_advantage_damage_factor_raw=Q,
        runtime_damage_scaling_raw=Q, runtime_main_hard_conversion_raw=25_000,
        runtime_pursuit_hard_conversion_raw=25_000,
        province_has_holding=False,
        province_winter_hard_conversion_modifier_raw=0, sides=side_loss,
    )
    losing_entries = (
        _entry(99, 0, 500_005, 300_001, 10),
        _entry(7, 1, 700_007, 600_000, 20),
    )
    return CurrentBattleCondition(
        snapshot_revision=57, observed_date_raw=53_178_264,
        combat_id=335_544_325, province_id=2586,
        subject_side_index=0, side_scope="full_side", phase="pursuit", phase_raw=2,
        phase_day=2, base_combat_width=5, final_combat_width=5,
        roll_cadence_counter=0, base_advantage_raw=0, resolved_advantage_raw=0,
        sides=(_side(0, (), side_loss[0]),
               _side(1, losing_entries, side_loss[1])),
        loss_inputs=loss, active_counter_inputs=None,
        pursuit_modifier_sides={
            "status": "available", "scale": Q,
            "source_combat_id": 335_544_325,
            "source_target_province_id": 2586,
            "unavailable_reason": None,
            "sides": [
                {"side_index": index,
                 "encounter_role": "attacker" if index == 0 else "defender",
                 "pursuit_efficiency_raw": 0, "retreat_losses_raw": 0}
                for index in (0, 1)
            ],
        },
        missing_inputs=(),
        source_snapshot={
            "current_pursuit_inputs_v1": {
                "scale": Q, "source_combat_id": 335_544_325,
                "pursuit_phase_days": 3,
                "base_toughness_multiplier_raw": 0,
                "minimum_pursuit_multiplier_raw": Q,
                "pursuit_stat_multiplier_raw": 0,
                "losing_side_index": 1,
                "initial_loser_levy_soft_raw": 1_200_000,
                "initial_loser_maa_soft_raw": 0,
                "losing_side_skip_pursuit": False,
            },
        },
    )


class CurrentPursuitFocusedTests(unittest.TestCase):
    def test_frozen_pool_q_rounding_and_last_allocation_precede_zero_loss_finish(self):
        condition = _condition()
        result = run_current_pursuit_ticks(condition, max_ticks=2)
        self.assertEqual(result["status"], "available")
        self.assertEqual(len(result["ticks"]), 2)
        allocation, finish = result["ticks"]
        self.assertEqual((allocation["phase_day_before"],
                          allocation["dispatched_phase_day"]), (2, 3))
        self.assertEqual(allocation["branch"], "pursuit_casualties")
        # Frozen native initial pool is 1200000, current soft is 900001.
        # The day budget is 400000; converted per-entry shares plus stored-order
        # remainder retain native signed-Q truncation (33333 + 66666 + 0).
        self.assertEqual(allocation["new_hard_casualties_raw"], 99_999)
        rows = allocation["entries"]
        self.assertEqual([row["regiment_id"] for row in rows], [99, 7])
        self.assertEqual([row["new_hard_casualties_raw"] for row in rows],
                         [33_333, 66_666])
        self.assertEqual([row["soft_casualties_raw_after"] for row in rows],
                         [266_668, 533_334])
        for row in rows:
            self.assertEqual(row["current_fighting_raw_after"],
                             row["current_fighting_raw_before"])
        self.assertEqual((finish["phase_day_before"],
                          finish["dispatched_phase_day"]), (3, 4))
        self.assertEqual(finish["branch"], "pursuit_finished")
        self.assertEqual(finish["new_hard_casualties_raw"], 0)
        self.assertEqual(result["new_hard_casualties_raw"], 99_999)
        self.assertEqual((result["phase_raw_after"], result["phase_day_after"]), (3, 0))
        self.assertEqual(result["stop_reason"], "normal_result")
        self.assertTrue(result["normal_result_intent"])
        updated = result["updated_condition"]
        self.assertEqual([entry.state.soft_casualties_raw
                          for entry in updated.sides[1].entries], [266_668, 533_334])
        self.assertEqual(updated.sides[1].participant_hard_total_raw, 200_006)
        self.assertFalse(allocation["ledger_is_an_additional_fighting_deduction"])
        self.assertEqual([entry.state.soft_casualties_raw
                          for entry in condition.sides[1].entries], [300_001, 600_000])
        self.assertEqual(condition.source_snapshot["current_pursuit_inputs_v1"]
                         ["initial_loser_levy_soft_raw"], 1_200_000)
        # The same observed remaining pool also bounds an oversized floor
        # budget: 1200000 unconverted becomes at most the current 900001.
        block = dict(condition.source_snapshot["current_pursuit_inputs_v1"])
        block["minimum_pursuit_multiplier_raw"] = 3*Q
        bounded = run_current_pursuit_ticks(
            replace(condition, source_snapshot={"current_pursuit_inputs_v1": block}),
            max_ticks=1,
        )
        self.assertEqual(bounded["new_hard_casualties_raw"], 225_000)
        self.assertEqual([row["soft_casualties_raw_after"]
                          for row in bounded["ticks"][0]["entries"]], [225_001, 450_000])
