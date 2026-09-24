from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.native_battle_case import (
    NativeBattleCaseError,
    _validate,
    _validate_repeatability,
    _validate_phase_event_observations,
    load_episode01_native_battle_case,
    load_episode01_native_battle_repeatability,
    load_episode01_phase_event_observations,
    original_daily_timeline,
)


class NativeBattleCaseTests(unittest.TestCase):
    def test_original_outcome_and_replay_divergence_stay_separate(self) -> None:
        case = load_episode01_native_battle_case()
        self.assertEqual(len(original_daily_timeline()), 31)
        self.assertEqual([row["day"] for row in case["joins"]], [1, 2, 12, 22])
        self.assertEqual(case["winner_relative_to_player"], "enemy")
        self.assertEqual(case["battle_warscore_player_delta_raw_q100000"], -5_000_000)
        self.assertEqual(case["first_numeric_divergence_source_day"], 6)
        self.assertTrue(case["phase_traces"][1]["replay_matches_original_day"])
        self.assertFalse(case["phase_traces"][2]["replay_matches_original_day"])
        self.assertFalse(case["phase_trace_may_bind_to_original_daily_transition"])
        self.assertFalse(case["calibrated_win_probability_available"])
        self.assertFalse(case["planner_usable"])

    def test_evidence_cannot_be_promoted_by_switching_a_flag(self) -> None:
        case = load_episode01_native_battle_case()
        for key in ("planner_usable", "calibrated_win_probability_available",
                    "same_random_trajectory_proven", "phase_trace_may_bind_to_original_daily_transition"):
            promoted = copy.deepcopy(case)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate(promoted)

    def test_checkpoint_replays_diverge_without_authorizing_win_probability(self) -> None:
        report = load_episode01_native_battle_repeatability()
        self.assertEqual([row["winner_side_raw"] for row in report["trials"]], [0, 0, 0])
        self.assertEqual([row["first_regiment_current_divergence_day"]
                          for row in report["pairwise_divergence"]], [6, 6, 6])
        self.assertEqual([row["mode"] for row in report["trials"]], [
            "live_continuation_after_contact_save", "checkpoint_restore", "checkpoint_restore",
        ])
        self.assertFalse(report["calibrated_win_probability_available"])
        for key in ("independent_random_draws_proven", "calibrated_win_probability_available",
                    "planner_usable"):
            promoted = copy.deepcopy(report)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate_repeatability(promoted)

    def test_phase_event_ledger_is_not_mistaken_for_effect_execution(self) -> None:
        report = load_episode01_phase_event_observations()
        self.assertEqual(report["battle_event_row_count"], 6)
        self.assertEqual([row["source_day"] for row in report["event_fire_pairs"]],
                         [5, 7, 9, 15, 16, 19])
        self.assertTrue(all(not row["observed_character_core_deltas_within_fire"]
                            for row in report["event_fire_pairs"]))
        wounded = report["event_fire_pairs"][0]["target_character_observations"][0]
        self.assertEqual(wounded["same_fire_before"]["prowess"], 8)
        self.assertEqual(wounded["same_fire_after"]["prowess"], 8)
        self.assertEqual(wounded["next_source_day_record0"]["prowess"], 8)
        self.assertEqual(wounded["next_source_day_record2"]["prowess"], 6)
        killed = report["event_fire_pairs"][3]["target_character_observations"][0]
        self.assertFalse(killed["same_fire_after"]["death_marker_present"])
        self.assertTrue(killed["next_source_day_record2"]["death_marker_present"])
        self.assertFalse(report["effect_execution_or_complete_feedback_proven"])
        for key in ("effect_execution_or_complete_feedback_proven", "planner_usable"):
            promoted = copy.deepcopy(report)
            promoted[key] = True
            with self.subTest(key=key), self.assertRaises(NativeBattleCaseError):
                _validate_phase_event_observations(promoted)


if __name__ == "__main__":
    unittest.main()
