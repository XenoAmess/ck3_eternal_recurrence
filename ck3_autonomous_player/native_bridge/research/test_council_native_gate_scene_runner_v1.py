"""Focused no-launch checks for reusable Council paused-scene provenance."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import run_council_native_gate_scene_v1 as scene
from run_council_native_gate_scene_v1 import source_round, validate_expected_frame


class CouncilNativeGateSceneRunnerTests(unittest.TestCase):
    def test_accepts_monotonic_source_round_without_fixing_one_old_scene(self) -> None:
        self.assertEqual(source_round({"source_round": "R761"}), "R761")
        self.assertEqual(source_round({"source_round": "R739"}), "R739")
        self.assertEqual(source_round({"source_round": "R0050"}), "R0050")

    def test_rejects_missing_or_non_monotonic_round(self) -> None:
        for value in (None, "R0", "R0000", "R-1", "761", "R761-extra"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source_round({"source_round": value})

    def test_preserves_zero_padded_new_round_at_dispatch_without_launch(self) -> None:
        arguments = ["run_council_native_gate_scene_v1.py", "--candidate-root", "candidate",
                     "--new-round", "R0051", "--evidence", "evidence"]
        with patch("sys.argv", arguments), \
             patch.object(scene, "verify_candidate", return_value={}), \
             patch.object(Path, "read_text", return_value='{"source_round":"R0050"}'), \
             patch.object(scene, "run", return_value=0) as run:
            self.assertEqual(scene.main(), 0)
        self.assertEqual(run.call_args.args[1], "R0051")

    def test_accepts_proven_vacant_or_occupied_steward(self) -> None:
        common = {"government_key": "feudal_government",
                  "played_character_id": 31853, "date_raw": 53333040}
        vacant = {**common, "steward_vacant": True,
                  "steward_incumbent_character_id": None}
        occupied = {**common, "steward_vacant": False,
                    "steward_incumbent_character_id": 32716}
        self.assertIs(validate_expected_frame(vacant), vacant)
        self.assertIs(validate_expected_frame(occupied), occupied)

    def test_rejects_inconsistent_steward_vacancy(self) -> None:
        common = {"government_key": "feudal_government",
                  "played_character_id": 31853, "date_raw": 53333040}
        for frame in ({**common, "steward_vacant": True,
                       "steward_incumbent_character_id": 32716},
                      {**common, "steward_vacant": False,
                       "steward_incumbent_character_id": None}):
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                validate_expected_frame(frame)


if __name__ == "__main__":
    unittest.main()
