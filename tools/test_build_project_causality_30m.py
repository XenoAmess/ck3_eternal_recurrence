#!/usr/bin/env python3
"""Offline contract tests for the 30-minute Project Causality film adapter."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_project_causality_30m as film  # noqa: E402


class ProjectCausalityThirtyMinuteBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = json.loads(film.DEFAULT_SCRIPT.read_text(encoding="utf-8"))

    def test_script_matches_authoritative_structure(self) -> None:
        rows = film.validate_script(
            self.script,
            structure_path=film.DEFAULT_STRUCTURE,
            gates_path=film.DEFAULT_GATES,
            claims_path=film.DEFAULT_CLAIMS,
        )
        self.assertEqual(31, len(rows))
        self.assertEqual(0, rows[0]["start"])
        self.assertEqual(1800, rows[-1]["end"])
        self.assertEqual(86, sum(len(row["lines"]) for row in rows))

    def test_manifest_is_exact_bilingual_and_claim_bound(self) -> None:
        manifest = film.materialize_manifest()
        self.assertEqual(1800.0, manifest["target_duration_seconds"])
        self.assertEqual(54000, manifest["target_frames"])
        self.assertTrue(manifest["enforce_exact_total_seconds"])
        self.assertFalse(manifest["publication_authorized"])
        self.assertEqual(86, len(manifest["chapters"]))
        self.assertAlmostEqual(
            1800.0,
            sum(row["min_duration_seconds"] for row in manifest["chapters"]),
        )
        for row in manifest["chapters"]:
            self.assertEqual(row["narration_en"], row["subtitle_zh"])
            self.assertTrue(row["subtitle_secondary"])
            self.assertTrue(row["claim_ids"])

    def test_four_chapter_gates_have_delayed_theme_declarations(self) -> None:
        manifest = film.materialize_manifest()
        gates = [row for row in manifest["chapters"] if row.get("chapter_gate")]
        self.assertEqual(4, len(gates))
        self.assertEqual(4, len({row["source"] for row in gates}))
        self.assertEqual(4, len({row["sound_effect"] for row in gates}))
        for row in gates:
            self.assertEqual(20.0, row["min_duration_seconds"])
            self.assertEqual(12.0, row["narration_delay_seconds"])
            self.assertEqual("章门", row["status"]["zh"])
            self.assertTrue(Path(row["sound_effect"]).is_file())

    def test_removed_or_unreleased_material_is_absent(self) -> None:
        serialized = json.dumps(film.materialize_manifest(), ensure_ascii=False).lower()
        self.assertNotIn("食人赋能", serialized)
        self.assertNotIn("phase 2", serialized)
        self.assertNotIn("二期", serialized)

    def test_spoken_copy_does_not_read_titles_or_production_notes(self) -> None:
        spoken_zh = "\n".join(
            line["zh"]
            for segment in self.script["segments"]
            for line in segment["lines"]
        )
        spoken_en = "\n".join(
            line["en"]
            for segment in self.script["segments"]
            for line in segment["lines"]
        )
        for forbidden in (
            "project因果律",
            "伪天司的辉煌愿景",
            "副标题",
            "本片要证明",
            "这套组合体叫",
        ):
            self.assertNotIn(forbidden, spoken_zh)
        for forbidden in (
            "Project Causality",
            "False Celestial Chancellor",
            "This film argues",
            "subtitled",
        ):
            self.assertNotIn(forbidden, spoken_en)
        declarations = {
            segment["id"]: segment["lines"][0]["zh"]
            for segment in self.script["segments"]
            if segment.get("chapter_gate") is True
        }
        self.assertFalse(declarations["03-spell-declaration"].startswith("咒"))
        self.assertFalse(declarations["10-method-declaration"].startswith("术"))
        self.assertFalse(declarations["17-principle-declaration"].startswith("道"))
        self.assertFalse(declarations["22-vision-declaration"].startswith("辉煌愿景"))

    def test_video_sources_are_raw_or_production_captures_not_edited_segments(self) -> None:
        manifest = film.materialize_manifest()
        sources = [
            row["source"].replace("\\", "/").lower()
            for row in manifest["chapters"]
            if row["type"] == "video_clip"
        ]
        self.assertTrue(sources)
        self.assertFalse(
            any("/full-capability-showcase-work/" in source for source in sources)
        )
        agent_sources = [
            row
            for row in manifest["chapters"]
            if row["type"] == "video_clip"
            and "full-capability-showcase-sources"
            in row["source"].replace("\\", "/").lower()
        ]
        self.assertEqual(4, len(agent_sources))
        self.assertEqual(2, len({row["source"] for row in agent_sources}))
        self.assertTrue(
            all(row.get("crop_embedded_lower_third") is True for row in agent_sources)
        )
        by_id = {row["id"]: row for row in manifest["chapters"]}
        self.assertEqual("evidence_card", by_id["09-agent-current-state-03"]["type"])
        self.assertEqual("evidence_card", by_id["25-loop-b-02"]["type"])

    def test_validate_only_does_not_require_render_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            args = film.parser().parse_args(
                ["--validate-only", "--manifest-output", str(manifest)]
            )
            with mock.patch.object(
                film.showcase,
                "build",
                return_value=(manifest.with_suffix(".mp4"), manifest.with_suffix(".video.json")),
            ) as build:
                self.assertEqual((None, None), film.run(args))
            builder_args = build.call_args.args[0]
            self.assertTrue(builder_args.validate_only)
            self.assertEqual(
                manifest.with_name("manifest.validation.mp4").resolve(),
                builder_args.output.resolve(),
            )
            self.assertEqual(
                (manifest.parent / ".project-causality-validation-work").resolve(),
                builder_args.work_dir.resolve(),
            )


if __name__ == "__main__":
    unittest.main()
