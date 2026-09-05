#!/usr/bin/env python3
"""Boundary and equivalence contracts for the foundational effect families."""

from __future__ import annotations

import unittest

import effect_file_boundaries as boundaries
import gen_361_b1_runtime as b1
import gen_361_mechanisms as mechanisms
from zg361_effect_sharding import MAX_EFFECTS_PER_SHARD, top_level_effect_blocks


class FoundationEffectShardingTests(unittest.TestCase):
    def assert_generated_family(
        self,
        rendered: dict,
        expected_blocks: tuple[tuple[str, str], ...],
        residue: tuple,
    ) -> None:
        self.assertTrue(rendered)
        self.assertEqual(residue, ())
        observed: list[tuple[str, str]] = []
        for path, payload in sorted(rendered.items()):
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), payload)
                blocks = top_level_effect_blocks(payload)
                self.assertGreaterEqual(len(blocks), 1)
                self.assertLessEqual(len(blocks), MAX_EFFECTS_PER_SHARD)
                self.assertIn("# Purpose shard:", payload.decode("utf-8-sig"))
                observed.extend(blocks)
        self.assertEqual(tuple(observed), expected_blocks)

    def test_mechanism_effects_are_exactly_sharded(self) -> None:
        catalogue = mechanisms.load_mechanisms(mechanisms.MOD_ROOT)
        rendered = mechanisms.effect_shard_outputs(catalogue)
        self.assertFalse(mechanisms.LEGACY_EFFECTS_PATH.exists())
        expected = top_level_effect_blocks(mechanisms.render_effects(catalogue))
        self.assert_generated_family(
            rendered,
            expected,
            mechanisms.generated_effect_residue(set(rendered)),
        )
        self.assertEqual(len(rendered), 186)

    def test_b1_effects_are_exactly_sharded(self) -> None:
        rendered = b1.effect_shard_outputs()
        self.assertTrue(all(not path.exists() for path in b1.LEGACY_EFFECT_PATHS))
        expected = tuple(
            block
            for source in b1.render_effect_parts()
            for block in top_level_effect_blocks(source)
        )
        self.assert_generated_family(
            rendered,
            expected,
            b1.generated_effect_residue(set(rendered)),
        )
        self.assertEqual(len(rendered), 12)

    def test_repository_has_no_effect_count_exception(self) -> None:
        report = boundaries.audit_report()
        self.assertEqual(report["policy"]["pre_b2_compatibility_files"], [])
        self.assertEqual(report["target_miss_count"], 0)
        self.assertEqual(report["violation_count"], 0)
        self.assertLessEqual(
            report["maximum_non_legacy_effect_count"],
            boundaries.TARGET_MAX,
        )
        self.assertEqual(report["result"], "GREEN")


if __name__ == "__main__":
    unittest.main()
