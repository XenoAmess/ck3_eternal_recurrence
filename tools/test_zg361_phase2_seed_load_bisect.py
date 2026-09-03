#!/usr/bin/env python3
"""Tests for the frozen seed-entry effect-group diagnostic builder."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent

import sys

sys.path.insert(0, str(TOOLS))

import zg361_phase2_seed_load_bisect as bisect
from phase2_workforce_block_segments import find_blocks


class Phase2SeedLoadBisectTests(unittest.TestCase):
    def _require_parent(self) -> None:
        if not (bisect.DEFAULT_PARENT_ROOT / "product").is_dir():
            self.skipTest("local frozen seed r3-final parent is not present")

    def test_scripts_are_utf8_bom(self) -> None:
        self.assertTrue(Path(bisect.__file__).read_bytes().startswith(bisect.BOM))
        self.assertTrue(Path(__file__).read_bytes().startswith(bisect.BOM))

    def test_frozen_parent_groups_are_exact(self) -> None:
        self._require_parent()
        parent = bisect.validate_parent()
        groups = bisect.group_metadata(parent["by_kind"]["effect"])
        self.assertEqual(bisect.EXPECTED_GROUPS, {
            name: {key: value[key] for key in ("files", "definitions", "bytes")}
            for name, value in groups.items()
        })
        self.assertEqual(68, sum(int(value["files"]) for value in groups.values()))
        self.assertEqual(314, sum(int(value["definitions"]) for value in groups.values()))

    def test_stub_renderer_preserves_bom_names_and_balance(self) -> None:
        source = (
            bisect.BOM
            + b"# header\r\n"
            + b"zg361_first_effect = {\r\n\tset_variable = { name = x value = 1 }\r\n}\r\n"
            + b"zg361_second_effect = {\r\n\ttrigger_event = zg361probe.1\r\n}\r\n"
        )
        rendered, rows = bisect.render_effect_variant(source, [])
        self.assertTrue(rendered.startswith(bisect.BOM))
        _header, blocks = find_blocks(rendered)
        self.assertEqual(
            ["zg361_first_effect", "zg361_second_effect"],
            [str(block["name"]) for block in blocks],
        )
        self.assertEqual(["stub", "stub"], [str(row["body_mode"]) for row in rows])
        self.assertIn(b"zg361_first_effect = {}", rendered)
        self.assertIn(b"zg361_second_effect = {}", rendered)

    def test_existing_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-seed-load-existing-") as temp:
            with self.assertRaisesRegex(bisect.SeedLoadBisectError, "already exists"):
                bisect.materialize(
                    output=Path(temp),
                    projection_name="phase2-seed-entry-all-effect-stub-test",
                )

    def test_all_effect_stub_is_exact_and_replayable(self) -> None:
        self._require_parent()
        with tempfile.TemporaryDirectory(prefix="zg361-seed-load-bisect-") as temp:
            output = Path(temp) / "candidate"
            report = bisect.materialize(
                output=output,
                projection_name="phase2-seed-entry-all-effect-stub-test",
            )
            self.assertEqual("GREEN_STATIC_DIAGNOSTIC", report["status"])
            self.assertTrue(report["diagnostic_only"])
            self.assertTrue(report["forbidden_for_seed_release"])
            self.assertEqual(245, report["candidate"]["files"])
            self.assertEqual(68, report["selection"]["effect_files"])
            self.assertEqual(314, report["selection"]["stubbed_definitions"])
            self.assertEqual(0, report["selection"]["real_definitions"])
            self.assertTrue(report["checks"]["path_set"]["same_as_parent"])
            retained = report["checks"]["retained_byte_identity"]
            self.assertEqual(177, retained["files"])
            self.assertEqual(135, retained["inherited_incident_files"])
            self.assertEqual(35, retained["retained_overlay_events"])
            self.assertEqual(2, retained["retained_overlay_court_positions"])
            self.assertEqual(5, retained["retained_overlay_localization"])
            self.assertTrue(
                report["checks"]["deterministic_materialization"]["source_equals_replay"]
            )
            self.assertEqual(
                bisect.tree_rows(output / "source"),
                bisect.tree_rows(output / "product"),
            )
            self.assertEqual(
                bisect.tree_rows(output / "source"),
                bisect.tree_rows(output / "materialized-check"),
            )

    def test_ab_ac_restore_is_exact_and_other_groups_are_stubbed(self) -> None:
        self._require_parent()
        parent = bisect.validate_parent()
        parent_rows = {
            str(row["path"]): row
            for row in parent["rows"]
        }
        with tempfile.TemporaryDirectory(prefix="zg361-seed-load-h1-") as temp:
            output = Path(temp) / "candidate"
            report = bisect.materialize(
                output=output,
                projection_name="phase2-seed-entry-effect-h1-ab-ac-test",
                real_groups=("ac", "ab", "ab"),
            )

            self.assertEqual("effect-group-restore", report["mode"])
            self.assertEqual(["ab", "ac"], report["selection"]["real_groups"])
            self.assertEqual(28, report["selection"]["real_effect_files"])
            self.assertEqual(40, report["selection"]["stub_effect_files"])
            self.assertEqual(164, report["selection"]["real_definitions"])
            self.assertEqual(150, report["selection"]["stubbed_definitions"])
            self.assertTrue(report["diagnostic_only"])
            self.assertTrue(report["forbidden_for_seed_release"])

            modes = report["selection"]["effect_file_modes"]
            self.assertEqual(68, len(modes))
            self.assertEqual(28, sum(row["body_mode"] == "real" for row in modes))
            self.assertEqual(40, sum(row["body_mode"] == "stub" for row in modes))
            candidate_rows = {
                str(row["path"]): row
                for row in bisect.tree_rows(output / "source")
            }
            for row in modes:
                path = str(row["path"])
                if row["group"] in {"ab", "ac"}:
                    self.assertEqual("real", row["body_mode"])
                    self.assertEqual(parent_rows[path], candidate_rows[path])
                else:
                    self.assertEqual("stub", row["body_mode"])
                    self.assertNotEqual(parent_rows[path], candidate_rows[path])

            self.assertEqual(
                bisect.tree_rows(output / "source"),
                bisect.tree_rows(output / "product"),
            )
            self.assertEqual(
                bisect.tree_rows(output / "source"),
                bisect.tree_rows(output / "materialized-check"),
            )


if __name__ == "__main__":
    unittest.main()
