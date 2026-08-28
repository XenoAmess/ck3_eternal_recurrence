from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    is_life_advance_step,
    parse_war_objective_hold_sentinel_advance_speed,
    parse_war_objective_hold_sentinel_advance_step,
    war_objective_hold_sentinel_advance_step,
)


class WarObjectiveHoldSentinelContractTests(unittest.TestCase):
    def test_canonical_step_binds_war_subject_objective_and_bound(self) -> None:
        step = war_objective_hold_sentinel_advance_step(
            33_554_527,
            201_326_874,
            2_635,
            53_257_080,
        )

        self.assertEqual(
            step,
            "war-objective-hold-sentinel-advance-war-33554527-"
            "army-201326874-at-2635-until-53257080",
        )
        self.assertEqual(
            parse_war_objective_hold_sentinel_advance_step(step),
            (33_554_527, 201_326_874, 2_635, 53_257_080),
        )
        self.assertEqual(
            parse_war_objective_hold_sentinel_advance_speed(step), 3
        )
        self.assertTrue(is_life_advance_step(step))

    def test_explicit_ab_speed_is_bound_in_the_typed_step(self) -> None:
        for speed in (1, 2, 4, 5):
            with self.subTest(speed=speed):
                step = war_objective_hold_sentinel_advance_step(
                    33_554_527,
                    201_326_874,
                    2_635,
                    53_257_080,
                    timeline_speed=speed,
                )
                self.assertTrue(step.endswith(f"-speed-{speed}"))
                self.assertEqual(
                    parse_war_objective_hold_sentinel_advance_step(step),
                    (33_554_527, 201_326_874, 2_635, 53_257_080),
                )
                self.assertEqual(
                    parse_war_objective_hold_sentinel_advance_speed(step),
                    speed,
                )
                self.assertTrue(is_life_advance_step(step))

        for speed in (0, 6, True):
            with self.subTest(speed=speed):
                with self.assertRaises(ValueError):
                    war_objective_hold_sentinel_advance_step(
                        33_554_527,
                        201_326_874,
                        2_635,
                        53_257_080,
                        timeline_speed=speed,
                    )

    def test_noncanonical_or_out_of_range_step_is_rejected(self) -> None:
        malformed = (
            "war-objective-hold-sentinel-advance-war-0-army-11-at-20-until-24",
            "war-objective-hold-sentinel-advance-war-1-army-0-at-20-until-24",
            "war-objective-hold-sentinel-advance-war-1-army-11-at-0-until-24",
            "war-objective-hold-sentinel-advance-war-1-army-11-at-20-until-0",
            "war-objective-hold-sentinel-advance-war-01-army-11-at-20-until-24",
            "war-objective-hold-sentinel-advance-war-1-army-11-at-20-until-024",
            "war-objective-hold-sentinel-advance-war-1-army-11-at-20",
            "war-objective-hold-sentinel-advance-war-2147483648-army-11-at-20-until-24",
            "war-objective-hold-sentinel-advance-war-1-army-11-at-20-until-24-speed-3",
            "war-objective-hold-sentinel-advance-war-1-army-11-at-20-until-24-speed-6",
        )
        for step in malformed:
            with self.subTest(step=step):
                self.assertIsNone(
                    parse_war_objective_hold_sentinel_advance_step(step)
                )
                self.assertFalse(is_life_advance_step(step))

        for values in (
            (0, 11, 20, 24),
            (1, 0, 20, 24),
            (1, 11, 0, 24),
            (1, 11, 20, 0),
            (True, 11, 20, 24),
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    war_objective_hold_sentinel_advance_step(*values)


if __name__ == "__main__":
    unittest.main()
