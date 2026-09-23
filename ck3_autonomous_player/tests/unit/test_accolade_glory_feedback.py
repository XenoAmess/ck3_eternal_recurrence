from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.accolade_glory_feedback import (
    AccoladeGloryProjectionUnavailable,
    project_accolade_glory_write,
    stock_phase_glory_delta_raw,
)


class AccoladeGloryFeedbackTests(unittest.TestCase):
    def test_stock_values_and_positive_gain_cross_exact_rank_threshold(self) -> None:
        self.assertEqual(stock_phase_glory_delta_raw("minimal_glory_gain"), 1_000_000)
        self.assertEqual(stock_phase_glory_delta_raw("minor_glory_gain"), 2_500_000)
        result = project_accolade_glory_write(
            accolade_id=91,
            glory_before_raw=29_000_000,
            delta_raw=stock_phase_glory_delta_raw("minimal_glory_gain"),
            owner_gain_modifier_raw=50_000,
        )
        self.assertEqual(result["effective_delta_raw"], 1_500_000)
        self.assertEqual(result["glory_raw_after"], 30_500_000)
        self.assertEqual((result["rank_before"], result["rank_after"]), (1, 2))
        self.assertTrue(result["on_accolade_rank_change_expected"])
        self.assertFalse(result["battle_horizon_feedback_ready"])
        self.assertFalse(result["active_attack_allowed"])

    def test_negative_delta_ignores_positive_gain_modifier_and_clamps(self) -> None:
        result = project_accolade_glory_write(
            accolade_id=91,
            glory_before_raw=30_000_000,
            delta_raw=-40_000_000,
            owner_gain_modifier_raw=90_000,
        )
        self.assertEqual(result["effective_delta_raw"], -40_000_000)
        self.assertEqual(result["actual_change_raw"], -30_000_000)
        self.assertEqual(result["glory_raw_after"], 0)
        self.assertEqual((result["rank_before"], result["rank_after"]), (2, 1))

    def test_no_rank_change_still_has_glory_callback(self) -> None:
        result = project_accolade_glory_write(
            accolade_id=91,
            glory_before_raw=10_000_000,
            delta_raw=1_000_000,
            owner_gain_modifier_raw=0,
        )
        self.assertTrue(result["on_accolade_glory_change_expected"])
        self.assertFalse(result["on_accolade_rank_change_expected"])

    def test_unproved_inputs_fail_closed(self) -> None:
        for kwargs in (
            {"accolade_id": True},
            {"glory_before_raw": -1},
            {"owner_gain_modifier_raw": -100_001},
            {"delta_raw": (1 << 63) - 1},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(
                AccoladeGloryProjectionUnavailable
            ):
                project_accolade_glory_write(
                    **{
                        "accolade_id": 91,
                        "glory_before_raw": 29_000_000,
                        "delta_raw": 1_000_000,
                        "owner_gain_modifier_raw": 0,
                        **kwargs,
                    }
                )
        with self.assertRaises(AccoladeGloryProjectionUnavailable):
            stock_phase_glory_delta_raw("fabricated_gain")


if __name__ == "__main__":
    unittest.main()
