#!/usr/bin/env python3
"""Offline contract tests for the Project Causality 08:20 promo adapter."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_project_causality_promo as promo  # noqa: E402
import build_full_agent_showcase as showcase  # noqa: E402


class ProjectCausalityPromoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeline = json.loads(
            promo.DEFAULT_TIMELINE.read_text(encoding="utf-8-sig")
        )

    def test_timeline_is_contiguous_and_exactly_eight_twenty(self) -> None:
        rows = promo.validate_timeline(self.timeline, claims_path=promo.DEFAULT_CLAIMS)
        self.assertEqual(35, len(rows))
        self.assertEqual(0.0, rows[0]["start"])
        self.assertEqual(500.0, rows[-1]["end"])
        self.assertEqual(15000, int(rows[-1]["end"] * promo.TARGET_FPS))
        for current, following in zip(rows, rows[1:]):
            self.assertEqual(current["end"], following["start"])

    def test_manifest_is_chinese_primary_bilingual_and_claim_bound(self) -> None:
        manifest = promo.materialize_manifest()
        self.assertEqual(35, len(manifest["chapters"]))
        self.assertEqual("zh-CN-XiaoxiaoNeural", manifest["voice"])
        self.assertEqual(500.0, manifest["target_duration_seconds"])
        self.assertFalse(manifest["publication_authorized"])
        for source, chapter in zip(self.timeline["cues"], manifest["chapters"]):
            self.assertEqual(source["narration_zh"], chapter["narration_en"])
            self.assertEqual(source["narration_zh"], chapter["subtitle_zh"])
            self.assertEqual(source["subtitle_en"], chapter["subtitle_secondary"])
            self.assertEqual("zho", chapter["audio_language"])
            self.assertTrue(chapter["claim_ids"])

    def test_generated_content_excludes_forbidden_phase_two_material(self) -> None:
        serialized = json.dumps(promo.materialize_manifest(), ensure_ascii=False).lower()
        self.assertNotIn("phase 2", serialized)
        self.assertNotIn("二期", serialized)

    def test_every_timeline_claim_resolves(self) -> None:
        known = promo._claim_ids(promo.DEFAULT_CLAIMS)
        used = {
            claim_id
            for cue in self.timeline["cues"]
            for claim_id in cue["claim_ids"]
        }
        self.assertTrue(used)
        self.assertLessEqual(used, known)

    def test_bilingual_subtitles_share_one_timed_cue(self) -> None:
        manifest = promo.materialize_manifest()
        first = manifest["chapters"][0]
        chapter = showcase.Chapter(
            index=0,
            chapter_id=first["id"],
            kind="title_card",
            title_en=first["title_en"],
            title_zh=first["title_zh"],
            narration_en=first["narration_en"],
            subtitle_zh=first["subtitle_zh"],
            status_en=first["status"]["en"],
            status_zh=first["status"]["zh"],
            classification=first["status"]["classification"],
            body_en=[],
            body_zh=[],
            sources=[],
            source_path=None,
            start_seconds=0.0,
            end_seconds=None,
            min_duration_seconds=8.0,
            tail_padding_seconds=0.25,
            fit="contain",
            raw=first,
            narration_duration_seconds=6.0,
            shot_duration_seconds=8.0,
            subtitle_secondary=first["subtitle_secondary"],
        )
        showcase.prepare_subtitle_layouts([chapter], showcase.find_fonts())
        cues = showcase._chapter_subtitle_cues(chapter)
        self.assertEqual(1, len(cues))
        self.assertIn(showcase.SUBTITLE_BILINGUAL_SEPARATOR, cues[0][2])
        ass = showcase._ass_document(cues)
        self.assertIn(r"\fs30", ass)
        self.assertIn("A ruler dies.", ass)


if __name__ == "__main__":
    unittest.main()
