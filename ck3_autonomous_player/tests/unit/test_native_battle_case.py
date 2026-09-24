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
    load_episode01_native_battle_case,
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


if __name__ == "__main__":
    unittest.main()
