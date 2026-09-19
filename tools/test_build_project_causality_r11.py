#!/usr/bin/env python3
"""Offline contract tests for the Project Causality r11 retime builder."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_full_agent_showcase as showcase  # noqa: E402
import build_project_causality_r11 as r11  # noqa: E402


def chapter(chapter_id: str, *, source_key: str = "r6") -> showcase.Chapter:
    return showcase.Chapter(
        index=0,
        chapter_id=chapter_id,
        kind="title_card",
        title_en="TITLE",
        title_zh="标题",
        narration_en="测试旁白。",
        subtitle_zh="第一行。第二行。第三行。第四行。",
        subtitle_secondary="First. Second. Third. Fourth.",
        status_en="TEST",
        status_zh="测试",
        classification="static-ready",
        body_en=[],
        body_zh=[],
        sources=[],
        source_path=None,
        start_seconds=0.0,
        end_seconds=None,
        min_duration_seconds=1.0,
        tail_padding_seconds=1.25,
        fit="contain",
        raw={"r11_source_manifest_key": source_key},
        narration_duration_seconds=10.0,
        shot_duration_seconds=11.25,
    )


class ProjectCausalityR11Tests(unittest.TestCase):
    def test_checked_in_composition_contract_totals_98_cues(self) -> None:
        config = json.loads(r11.DEFAULT_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(98, sum(row["expected_count"] for row in config["composition"]))
        self.assertEqual(98, config["contracts"]["expected_cue_count"])
        self.assertEqual(3600, config["timing"]["maximum_film_seconds"])
        self.assertEqual([360, 720], [
            config["timing"]["agent_showcase_minimum_seconds"],
            config["timing"]["agent_showcase_maximum_seconds"],
        ])
        self.assertFalse(config["contracts"]["audio_tempo_filter_allowed"])
        self.assertFalse(config["contracts"]["old_burned_subtitle_video_allowed"])

    def test_pcm_wav_duration_is_measured_not_estimated_from_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cue.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(48000)
                output.writeframes(b"\x00\x00" * 72000)
            self.assertAlmostEqual(1.5, r11._wav_duration(path), places=6)

    def test_paired_bilingual_blocks_end_after_natural_narration(self) -> None:
        cue = chapter("paired")
        cue.raw.update(
            {
                "subtitle_block_policy": "paired-balanced",
                "subtitle_tail_hold_seconds": 1.0,
            }
        )
        cue.subtitle_lines = ["一", "二", "三", "四"]
        cue.subtitle_cue_blocks = [["一", "二", "三"], ["四"]]
        cue.subtitle_secondary_lines = ["one", "two", "three", "four"]
        blocks = showcase._chapter_subtitle_cues(cue, timeline_offset=5.0)
        self.assertEqual(2, len(blocks))
        self.assertAlmostEqual(16.0, blocks[-1][1], places=6)
        self.assertTrue(all(showcase.SUBTITLE_BILINGUAL_SEPARATOR in row[2] for row in blocks))
        self.assertLess(blocks[0][0], blocks[0][1])
        self.assertEqual(blocks[0][1], blocks[1][0])

    def test_provisional_robert_section_is_eight_minutes_without_audio_speedup(self) -> None:
        chapters = []
        for index in range(10):
            cue = chapter(f"agent-{index}", source_key="agent")
            cue.index = index
            cue.min_duration_seconds = 42.0
            cue.raw["r11_audio_tempo"] = 1.0
            chapters.append(cue)
        r11.allocate_provisional_robert_timing(chapters, target_seconds=480.0)
        self.assertAlmostEqual(480.0, sum(row.shot_duration_seconds or 0 for row in chapters))
        self.assertTrue(all((row.shot_duration_seconds or 0) >= 11.25 for row in chapters))
        self.assertTrue(all(row.raw["r11_audio_tempo"] == 1.0 for row in chapters))

    def test_clean_video_override_uses_one_contiguous_source_interval(self) -> None:
        cues = [chapter(f"coa-{index}") for index in range(3)]
        for index, cue in enumerate(cues):
            cue.index = index
            cue.kind = "video_clip"
            cue.shot_duration_seconds = 10.0
        with tempfile.TemporaryDirectory() as temporary:
            master = Path(temporary) / "coa.webm"
            master.write_bytes(b"clean-coa-fixture")
            r11.apply_clean_video_overrides(
                cues,
                {
                    "clean_video_overrides": [
                        {
                            "id": "coa-clean",
                            "master": str(master),
                            "source_start_seconds": 5,
                            "source_end_seconds": 50,
                            "cue_ids": [row.chapter_id for row in cues],
                        }
                    ]
                },
            )
        self.assertEqual([1.5, 1.5, 1.5], [row.raw["source_playback_rate"] for row in cues])
        self.assertEqual(5.0, cues[0].start_seconds)
        self.assertEqual(50.0, cues[-1].end_seconds)
        self.assertEqual(cues[0].end_seconds, cues[1].start_seconds)
        self.assertEqual(cues[1].end_seconds, cues[2].start_seconds)

    def test_robert_edit_rejects_any_source_time_gap(self) -> None:
        ids = ["a", "b"]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            master = directory / "master.mkv"
            master.write_bytes(b"fixture")
            edit = directory / "edit.json"
            edit.write_text(
                json.dumps(
                    {
                        "schema": "project-causality-r11-robert-continuous-edit.v1",
                        "master": str(master),
                        "spans": [
                            {
                                "cue_id": "a",
                                "source_start_seconds": 0,
                                "source_end_seconds": 10,
                                "playback_rate": 1,
                            },
                            {
                                "cue_id": "b",
                                "source_start_seconds": 11,
                                "source_end_seconds": 20,
                                "playback_rate": 1,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(r11.R11BuildError, "continuity breaks"):
                r11.load_robert_edit(edit, ids)

    def test_robert_edit_maps_contiguous_source_to_piecewise_speed(self) -> None:
        cues = [chapter("a", source_key="agent"), chapter("b", source_key="agent")]
        for index, cue in enumerate(cues):
            cue.index = index
        with tempfile.TemporaryDirectory() as temporary:
            master = Path(temporary) / "master.mkv"
            master.write_bytes(b"fixture-master")
            spans = [
                r11.RobertSpan("a", 0.0, 20.0, 1.0),
                r11.RobertSpan("b", 20.0, 60.0, 2.0),
            ]
            r11.apply_robert_edit(
                cues,
                master=master,
                spans=spans,
                minimum_seconds=40.0,
                maximum_seconds=50.0,
            )
        self.assertEqual([1.0, 2.0], [row.raw["source_playback_rate"] for row in cues])
        self.assertEqual([20.0, 20.0], [row.shot_duration_seconds for row in cues])
        self.assertEqual(cues[0].end_seconds, cues[1].start_seconds)


if __name__ == "__main__":
    unittest.main()
