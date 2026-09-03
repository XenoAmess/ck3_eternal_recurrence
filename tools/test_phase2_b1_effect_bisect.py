#!/usr/bin/env python3
"""Focused regression tests for the disposable B1 effect bisect helper."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import phase2_b1_effect_bisect as bisect
from phase2_workforce_block_segments import find_blocks


ROOT = Path(__file__).resolve().parents[1]
MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
sys.path.insert(0, str(MOD_TOOLS))
from gen_361_b1_runtime import render_effects


class Phase2B1EffectBisectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # The release output is intentionally split across two files.  Bisect
        # fixtures still operate on the frozen semantic monolith rendered from
        # the same generator source, rather than treating part 1 as complete.
        cls.data = render_effects()
        _header, cls.blocks = find_blocks(cls.data)

    def test_exact_source_identity(self) -> None:
        self.assertEqual(len(self.data), 495_777)
        self.assertEqual(
            hashlib.sha256(self.data).hexdigest(),
            bisect.EXPECTED_EFFECT_SHA256,
        )
        self.assertEqual(len(self.blocks), 77)

    def test_all_stub_is_exact_known_control(self) -> None:
        rendered, rows = bisect.render_effect_variant(self.data, [])
        self.assertTrue(rendered.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(len(rendered), 14_429)
        self.assertEqual(
            hashlib.sha256(rendered).hexdigest(),
            "c1c610f27edfa0be059612053ca07571a8d75568152f1439d03c3e607bf3a119",
        )
        _header, observed = find_blocks(rendered)
        self.assertEqual(
            [row["name"] for row in observed],
            [row["name"] for row in self.blocks],
        )
        self.assertTrue(all(row["body_mode"] == "stub" for row in rows))

    def test_balanced_arms_match_known_cut_and_hashes(self) -> None:
        self.assertEqual(bisect.balanced_cut(self.blocks), 41)
        left = bisect.real_indices_for_mode("left-real", self.blocks)
        right = bisect.real_indices_for_mode("right-real", self.blocks)
        self.assertEqual(left, list(range(41)))
        self.assertEqual(right, list(range(41, 77)))
        left_bytes, _ = bisect.render_effect_variant(self.data, left)
        right_bytes, _ = bisect.render_effect_variant(self.data, right)
        self.assertEqual(len(left_bytes), 259_244)
        self.assertEqual(len(right_bytes), 250_962)
        self.assertEqual(
            hashlib.sha256(left_bytes).hexdigest(),
            "e3c7622262e013ad03d922e24252f803777ec7d507bfbbba214f83318f9ca725",
        )
        self.assertEqual(
            hashlib.sha256(right_bytes).hexdigest(),
            "898d6a73810975da97834d7c75b1c4015db7363307e2355067d22fa80b832fe2",
        )

    def test_explicit_ranges_and_invalid_selection(self) -> None:
        self.assertEqual(
            bisect.real_indices_for_mode("ranges", self.blocks, "0-4,7,9-10"),
            [0, 1, 2, 3, 4, 7, 9, 10],
        )
        with self.assertRaises(bisect.B1BisectError):
            bisect.real_indices_for_mode("ranges", self.blocks, None)
        with self.assertRaises(bisect.B1BisectError):
            bisect.render_effect_variant(self.data, [77])

    def test_balanced_file_split_preserves_all_definition_bodies(self) -> None:
        parts, rows = bisect.render_balanced_file_split(self.data)
        self.assertEqual([relative for relative, _data in parts], [
            bisect.EFFECT_RELATIVE,
            bisect.SPLIT_EFFECT_RELATIVE,
        ])
        observed = []
        for _relative, data in parts:
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
            _header, blocks = find_blocks(data)
            observed.extend(blocks)
        self.assertEqual(
            [row["name"] for row in observed],
            [row["name"] for row in self.blocks],
        )
        for expected, actual in zip(self.blocks, observed, strict=True):
            expected_bytes = self.data[
                int(expected["start_byte"]):int(expected["end_byte"])
            ]
            relative, part_data = parts[int(rows[int(expected["index"])]["output_part"]) - 1]
            del relative
            actual_bytes = part_data[
                int(actual["start_byte"]):int(actual["end_byte"])
            ]
            self.assertEqual(actual_bytes, expected_bytes)


if __name__ == "__main__":
    unittest.main()
