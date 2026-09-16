"""Focused no-launch checks for reusable Council paused-scene provenance."""

from __future__ import annotations

import unittest

from run_council_native_gate_scene_v1 import source_round


class CouncilNativeGateSceneRunnerTests(unittest.TestCase):
    def test_accepts_monotonic_source_round_without_fixing_one_old_scene(self) -> None:
        self.assertEqual(source_round({"source_round": "R761"}), "R761")
        self.assertEqual(source_round({"source_round": "R739"}), "R739")

    def test_rejects_missing_or_non_monotonic_round(self) -> None:
        for value in (None, "R0", "R-1", "761", "R761-extra"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source_round({"source_round": value})


if __name__ == "__main__":
    unittest.main()
