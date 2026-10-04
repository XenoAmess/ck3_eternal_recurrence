"""One new public-horizon check for the optional manager hookup only."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from xar_autoplayer.simulation.battle_calendar_admission import DailyDateStageInput, LoadedScheduleInputs
from xar_autoplayer.simulation.battle_current_adapter import CurrentBattleCondition, CurrentBattleSide
from xar_autoplayer.simulation.battle_current_backing_reaggregation import CurrentPhase3BackingState
from xar_autoplayer.simulation.battle_current_normal_finalizer import CurrentNormalFinalizerManagerInputs
from xar_autoplayer.simulation.combat_core import BackingComponent, DrawState

# The runner supplies only the new projected horizon; all dependencies are the
# already-published implementations. No old fixture/test imports are needed.
module_path = Path(__file__).parents[2] / "src/xar_autoplayer/simulation/battle_current_conditional_horizon.py"
spec = importlib.util.spec_from_file_location(
    "xar_autoplayer.simulation.battle_current_horizon_manager_fixture", module_path)
horizon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = horizon
spec.loader.exec_module(horizon)


def condition():
    sides = []
    for index, count in enumerate((7, 3)):
        sides.append(CurrentBattleSide(
            side_index=index, role="attacker" if index == 0 else "defender",
            primary_participant_character_id=301 + index,
            selected_commander_character_id=-1, current_roll_points=0,
            roll_request=None, entries=(), ordered_armies=(),
            stored_current_fighting_raw=count * 100000,
            stored_levy_current_fighting_raw=count * 100000,
            derived_current_fighting_raw=count * 100000, derived_soft_casualties_raw=0,
            derived_main_fighting_entry_hard_casualties_raw=0,
            non_main_start_minus_current_minus_soft_raw=0,
            participant_hard_ledger=(), participant_hard_total_raw=0,
            loss_inputs=None, levy_damage_raw=None, levy_damage_source="unavailable",
            levy_damage_native_observed=False, levy_damage_primary_participant_character_id=None,
        ))
    return CurrentBattleCondition(
        snapshot_revision=1, observed_date_raw=1000, combat_id=42, province_id=9,
        subject_side_index=0, side_scope="full_side", phase="done", phase_raw=3,
        phase_day=0, base_combat_width=10, final_combat_width=10,
        roll_cadence_counter=0, base_advantage_raw=0, resolved_advantage_raw=0,
        sides=tuple(sides), loss_inputs=None, active_counter_inputs=None,
        pursuit_modifier_sides=None, missing_inputs=(), source_snapshot={},
    )


def run(terminal):
    day = horizon.ConditionalHorizonDay(
        DailyDateStageInput(1000, False, "synthetic explicit phase3 row"),
        LoadedScheduleInputs(None, None, "unreached calendar coefficients"),
        {"kind": "new_glue_only_fixture"}, terminal=terminal,
    )
    return horizon.run_conditional_horizon(condition(), timeline=(day,),
        draw_state=DrawState(0, 17), max_days=1)


class CurrentHorizonNormalFinalizerHookTest(unittest.TestCase):
    def test_normal_numeric_once_and_suppressed_without_census(self):
        census = {"enumeration_complete": True, "sides": []}
        states = {}
        for side_index, count in enumerate((7, 3)):
            army, regiment = 101 + side_index, 11 + side_index
            census["sides"].append({"side_index": side_index, "ordered_armies": [{
                "native_carmy_id": army, "public_cunit_id": 201 + side_index,
                "owner_character_id": 301 + side_index,
                "ordered_regiments": [{"regiment_id": regiment, "current_soldiers": count}],
            }]})
            states[(army, regiment)] = CurrentPhase3BackingState(
                (BackingComponent(count, count),), "absent")
        normal = horizon.ConditionalTerminalInputs(
            census, frozenset(states), None, {"kind": "explicit current after-values"},
            current_state_by_regiment=states, side_baseline_raw_by_side={0: 1000000, 1: 500000},
            normal_finalizer_manager=CurrentNormalFinalizerManagerInputs(
                "daily_row", True, pending_suppression_sweep=False),
            normal_finalizer_winner_raw=0, wipe_raw=False,
        )
        with patch.object(horizon, "project_current_normal_finalizer",
                          wraps=horizon.project_current_normal_finalizer) as invoked:
            normal_result = run(normal)
        self.assertEqual(invoked.call_count, 1)
        self.assertEqual(normal_result.status, "available")
        final = normal_result.terminal_result
        self.assertEqual(final["dispatch"]["branch"], "normal")
        self.assertEqual([row["final_survivors_raw_q100000"]
                          for row in final["normal_numeric_accounting"]["sides"]], [700000, 300000])
        self.assertEqual(final["losing_side_hard_raw_q100000"], 200000)
        self.assertFalse(final["prior_losses_reapplied"])
        self.assertFalse(final["complete_native_finalizer"])

        suppressed = horizon.ConditionalTerminalInputs(
            None, None, None, {"kind": "explicit suppression; no count operands"},
            normal_finalizer_manager=CurrentNormalFinalizerManagerInputs(
                "suppression_sweep", True, primary_hostile=False,
                finalized=False, processing=False),
            normal_finalizer_winner_raw=-1,
        )
        with patch.object(horizon, "project_current_normal_finalizer",
                          wraps=horizon.project_current_normal_finalizer) as invoked:
            suppressed_result = run(suppressed)
        self.assertEqual(invoked.call_count, 1)
        self.assertEqual(suppressed_result.status, "available")
        self.assertEqual(suppressed_result.typed_gaps, ())
        final = suppressed_result.terminal_result
        self.assertEqual(final["dispatch"]["branch"], "suppressed")
        self.assertEqual(final["winner_raw"], -1)
        self.assertIsNone(final["normal_numeric_accounting"])
        self.assertIsNone(final["backing_reaggregation"])
        self.assertFalse(suppressed_result.complete_native_transition)
        self.assertFalse(suppressed_result.complete_monte_carlo)
        self.assertFalse(suppressed_result.win_probability_ready)
        self.assertEqual(suppressed_result.actual_game_days_advanced, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
