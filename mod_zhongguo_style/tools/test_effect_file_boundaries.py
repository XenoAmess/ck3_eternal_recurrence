#!/usr/bin/env python3
"""Focused tests for the B2+ scripted-effect boundary audit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import effect_file_boundaries as boundary


def effect_source(count: int, *, indent_nested: bool = False) -> str:
    blocks = [f"effect_{index:03d} = {{\n}}" for index in range(count)]
    if indent_nested:
        blocks.append("outer = {\n\tnested = {\n\t}\n}")
    return "\n\n".join(blocks) + "\n"


class EffectFileBoundaryTests(unittest.TestCase):
    def test_parser_counts_only_unindented_assignments(self) -> None:
        names = boundary.top_level_effect_names(
            '# ignored = {\nalpha = {\nnested = {\n}\nlabel = "{ not structure }"\n}\nbeta = { }\n'
        )
        self.assertEqual(("alpha", "beta"), names)

    def test_target_miss_is_reported_but_not_a_principle_violation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "zg361_phase2_example_effects.txt").write_text(
                effect_source(11), encoding="utf-8-sig"
            )
            report = boundary.audit_report(root)
        self.assertEqual("GREEN", report["result"])
        self.assertEqual(1, report["target_miss_count"])
        self.assertEqual(0, report["violation_count"])

    def test_more_than_twenty_new_effects_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "zg361_phase2_example_effects.txt").write_text(
                effect_source(21), encoding="utf-8-sig"
            )
            report = boundary.audit_report(root)
        self.assertEqual("RED", report["result"])
        self.assertEqual(1, report["violation_count"])

    def test_more_than_200_kib_is_red_even_with_one_effect(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            payload = "large_effect = {\n" + ("\t# padding\n" * 20_000) + "}\n"
            (root / "zg361_large_effects.txt").write_text(
                payload, encoding="utf-8-sig"
            )
            report = boundary.audit_report(root)
        self.assertEqual("RED", report["result"])
        self.assertEqual(1, report["byte_violation_count"])
        self.assertEqual(1, report["violation_count"])

    def test_exactly_200_kib_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "zg361_boundary_effects.txt"
            prefix = "\ufeffboundary_effect = {\n"
            suffix = "}\n"
            padding = boundary.MAX_BYTES_PER_FILE - len(
                (prefix + suffix).encode("utf-8")
            )
            path.write_bytes((prefix + (" " * padding) + suffix).encode("utf-8"))
            report = boundary.audit_report(root)
        self.assertEqual("GREEN", report["result"])
        self.assertEqual(0, report["byte_violation_count"])

    def test_legacy_names_do_not_bypass_the_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "zg361_b1_runtime_effects.txt").write_text(
                effect_source(21), encoding="utf-8-sig"
            )
            report = boundary.audit_report(root)
        self.assertEqual("RED", report["result"])
        self.assertEqual(1, report["target_miss_count"])
        self.assertEqual(1, report["violation_count"])


if __name__ == "__main__":
    unittest.main()
