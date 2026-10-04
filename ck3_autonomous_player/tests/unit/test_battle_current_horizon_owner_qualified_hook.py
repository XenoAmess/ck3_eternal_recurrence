"""One new public-path owner callback composition check; no old fixtures."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from xar_autoplayer.simulation.battle_calendar_admission import DailyDateStageInput, LoadedScheduleInputs
from xar_autoplayer.simulation.battle_current_adapter import (
    CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide, CurrentLossInputs, CurrentLossSideInputs,
)
from xar_autoplayer.simulation.battle_current_terminal import TerminalBackingRegiment
from xar_autoplayer.simulation.battle_selected_owner_subset_retreat_12003 import (
    AdmittedSelectedOwnerRetreat12003, selected_owner_pursuit_inputs_from_current_condition_12003,
)
from xar_autoplayer.simulation.combat_core import BackingComponent, CombatRegimentState, DrawState, RegimentKind

module_path = Path(__file__).parents[2] / "src/xar_autoplayer/simulation/battle_current_conditional_horizon.py"
spec = importlib.util.spec_from_file_location(
    "xar_autoplayer.simulation.battle_current_horizon_owner_fixture", module_path)
horizon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = horizon
spec.loader.exec_module(horizon)


def entry(regiment, army, owner, current, soft, knight):
    backing = (BackingComponent(current // 100000, current // 100000),)
    state = CombatRegimentState(regiment, RegimentKind.MEN_AT_ARMS, current, soft,
        100000, 0, 0, backing)
    return CurrentBattleEntry(state=state, bucket="men_at_arms", bucket_index=regiment,
        native_carmy_id=army, public_cunit_id=army + 100, owner_character_id=owner,
        starting_raw=current + soft, effective_damage_raw=100000, fights_in_main_phase=True,
        hard_casualties_raw=0, knight_character_id_raw=knight, backing_components=backing,
        source_entry={"regiment_id": regiment, "native_carmy_id": army,
                      "knight_character_id_raw": knight})


def side(index, entries):
    current = sum(row.state.current_raw for row in entries)
    soft = sum(row.state.soft_casualties_raw for row in entries)
    armies = tuple({"native_carmy_id": row.native_carmy_id, "public_cunit_id": row.public_cunit_id,
                    "owner_character_id": row.owner_character_id, "combat_backlink_id": 42} for row in entries)
    ledger = tuple({"row_index": i, "participant_character_id": row.owner_character_id,
                    "hard_casualties_raw": 0} for i, row in enumerate(entries))
    return CurrentBattleSide(side_index=index, role="attacker" if index == 0 else "defender",
        primary_participant_character_id=entries[0].owner_character_id,
        selected_commander_character_id=-1, current_roll_points=0, roll_request=None,
        entries=tuple(entries), ordered_armies=armies, stored_current_fighting_raw=current,
        stored_levy_current_fighting_raw=0, derived_current_fighting_raw=current,
        derived_soft_casualties_raw=soft, derived_main_fighting_entry_hard_casualties_raw=0,
        non_main_start_minus_current_minus_soft_raw=0, participant_hard_ledger=ledger,
        participant_hard_total_raw=0, loss_inputs=None, levy_damage_raw=None,
        levy_damage_source="unavailable", levy_damage_native_observed=False,
        levy_damage_primary_participant_character_id=None)


class CurrentHorizonOwnerQualifiedHookTest(unittest.TestCase):
    def test_admitted_qualified_callback_keeps_backing_and_carries_q_once(self):
        selected = entry(22, 102, 302, 100000, 100000, 77)
        retained = entry(23, 103, 303, 1000000, 0, -1)
        source = {"status": "available", "snapshot_revision": 1, "observed_date_raw": 1000,
            "combat_id": 42, "province_id": 9, "forced_winner_raw": -1,
            "current_pursuit_inputs_v1": {"pursuit_stat_multiplier_raw": 100000,
                "base_toughness_multiplier_raw": 100000, "minimum_pursuit_multiplier_raw": 100000}}
        losses = CurrentLossInputs(100000, 42, 9, 100000, 100000, 100000, 100000,
            False, 0, (CurrentLossSideInputs(0, 100000, 0, 0), CurrentLossSideInputs(1, 100000, 0, 0)))
        initial = CurrentBattleCondition(snapshot_revision=1, observed_date_raw=1000,
            combat_id=42, province_id=9, subject_side_index=0, side_scope="full_side",
            phase="main", phase_raw=1, phase_day=2, base_combat_width=10, final_combat_width=10,
            roll_cadence_counter=0, base_advantage_raw=0, resolved_advantage_raw=0,
            sides=(side(0, (entry(21, 101, 301, 1000000, 0, -1),)), side(1, (selected, retained))),
            loss_inputs=losses, active_counter_inputs=None,
            pursuit_modifier_sides={"status": "available", "sides": [
                {"pursuit_efficiency_raw": 0, "retreat_losses_raw": 0},
                {"pursuit_efficiency_raw": 0, "retreat_losses_raw": 0}]},
            missing_inputs=(), source_snapshot=source)
        source_before = copy.deepcopy(source)
        operands = selected_owner_pursuit_inputs_from_current_condition_12003(initial, selected_side_index=1)
        self.assertIs(operands.knight_backing_qualifications_by_regiment[(102, 22)].knight_getter_result, True)
        event = AdmittedSelectedOwnerRetreat12003(42, 1, (302,), 8, True,
            pursuit_inputs_by_owner={302: operands}, source_context={"kind": "explicit caller boundary"})
        backing = {101: (TerminalBackingRegiment(101, 21, 10),),
                   102: (TerminalBackingRegiment(102, 22, 1),),
                   103: (TerminalBackingRegiment(103, 23, 10),)}
        day = horizon.ConditionalHorizonDay(
            DailyDateStageInput(1000, False, "explicit no accepted manager invocation"),
            LoadedScheduleInputs(None, None, "unreached calendar/body coefficients"),
            {"kind": "synthetic explicitly admitted callback scenario"}, entry_events=(),
            owner_retreats_before_admission=(event,), owner_retreat_backing_by_army=backing)
        with patch.object(horizon, "apply_selected_owner_subset_retreats_12003",
                          wraps=horizon.apply_selected_owner_subset_retreats_12003) as invoked:
            result = horizon.run_conditional_horizon(initial, timeline=(day,),
                draw_state=DrawState(0, 17), max_days=1)
        self.assertEqual(invoked.call_count, 1)
        self.assertEqual(result.status, "available")
        self.assertEqual(result.typed_gaps, ())
        owner_stage = result.trace[0]["stages"][0]
        self.assertEqual(owner_stage["stage"], "before_admission_owner_retreats")
        applied = owner_stage["result"]
        # Hand result: divisor1 + softQ/toughnessQ + minimumQ transfers softQ
        # to hardQ. Qualified true skips the whole backing write.
        self.assertEqual(applied.event_ledger[0]["new_hard_casualties_raw"], 100000)
        self.assertEqual(applied.event_ledger[0]["copied_entries_after"][0].state.soft_casualties_raw, 0)
        write = applied.event_ledger[0]["backing_writebacks"][0]
        self.assertTrue(write["qualified_knight_backing_early_return"])
        self.assertFalse(write["regular_backing_call_selected"])
        self.assertEqual(applied.backing_by_army[102][0].current_soldiers, 1)
        self.assertEqual(applied.departed_backing_by_army[102][0].current_soldiers, 1)
        after = result.final_state.condition.sides[1]
        self.assertEqual(tuple(row.owner_character_id for row in after.entries), (303,))
        self.assertEqual(after.participant_hard_ledger[0]["hard_casualties_raw"], 100000)
        self.assertEqual(after.stored_current_fighting_raw, 1000000)
        self.assertEqual(result.final_state.draw_state, DrawState(0, 17))
        self.assertEqual(result.modeled_date_raw, 1000)
        self.assertEqual(result.modeled_accepted_invocations, 0)
        self.assertIsNone(day.ai_context)
        self.assertFalse(owner_stage["ai_selection_inferred"])
        self.assertFalse(owner_stage["native_callback_timing_claimed"])
        self.assertEqual(initial.source_snapshot, source_before)
        self.assertEqual(result.actual_game_days_advanced, 0)
        self.assertFalse(result.complete_native_transition)
        self.assertFalse(result.complete_monte_carlo)
        self.assertFalse(result.win_probability_ready)


if __name__ == "__main__":
    unittest.main(verbosity=2)
