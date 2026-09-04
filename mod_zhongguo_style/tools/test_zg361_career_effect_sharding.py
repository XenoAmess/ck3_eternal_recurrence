#!/usr/bin/env python3
"""Focused file-boundary contracts for the B6 career effect families."""

from __future__ import annotations

import unittest

import gen_361_career_hc_runtime as career_hc
import gen_361_career_learning_runtime as career_learning
from zg361_effect_sharding import MAX_EFFECTS_PER_SHARD, top_level_effect_blocks


class CareerEffectShardingTests(unittest.TestCase):
    def assert_family(self, generator: object, expected_effects: int) -> None:
        rendered = generator.effect_shard_outputs()
        self.assertFalse(generator.LEGACY_EFFECTS_PATH.exists())
        self.assertEqual(generator.generated_effect_residue(set(rendered)), ())

        actual: list[tuple[str, str]] = []
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), payload)
                blocks = top_level_effect_blocks(payload, generated_header=generator.HEADER)
                self.assertGreaterEqual(len(blocks), 1)
                self.assertLessEqual(len(blocks), MAX_EFFECTS_PER_SHARD)
                self.assertIn("# Purpose shard:", payload.decode("utf-8-sig"))
                actual.extend(blocks)

        expected = top_level_effect_blocks(
            generator.render_effects(), generated_header=generator.HEADER
        )
        self.assertEqual(len(expected), expected_effects)
        self.assertEqual(tuple(actual), expected)

    def test_career_hc_effect_boundaries(self) -> None:
        self.assert_family(career_hc, 267)

    def test_career_learning_effect_boundaries(self) -> None:
        self.assert_family(career_learning, 125)


if __name__ == "__main__":
    unittest.main()
