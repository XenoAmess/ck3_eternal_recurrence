#!/usr/bin/env python3
"""Offline tests for the ZhongGuo 361 promo pipeline."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOOLS_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = TOOLS_DIRECTORY.parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_promo_video as promo  # noqa: E402
import export_promo_script as exporter  # noqa: E402
import import_promo_acceptance_stills as acceptance_importer  # noqa: E402
import validate_promo_video as validator  # noqa: E402


FULL_MANIFEST = PROJECT_DIRECTORY / "promo" / "promo-manifest.json"
SMOKE_MANIFEST = PROJECT_DIRECTORY / "promo" / "smoke-manifest.json"
GENERATED_SCRIPT = PROJECT_DIRECTORY / "promo" / "script.md"


def _absolute_sources(payload: dict) -> dict:
    """Keep copied manifest tests focused on their intended invariant."""
    for chapter in payload["chapters"]:
        for key in ("source", "evidence_sources"):
            value = chapter.get(key)
            records = value if isinstance(value, list) else [value]
            for record in records:
                if not isinstance(record, dict) or "path" not in record:
                    continue
                record["path"] = str(
                    (FULL_MANIFEST.parent / record["path"]).resolve()
                )
    return payload


class PromoManifestTests(unittest.TestCase):
    def test_full_manifest_has_required_scope_topics_and_duration_guard(self) -> None:
        manifest, chapters = promo.load_manifest(FULL_MANIFEST)
        self.assertEqual(17, len(chapters))
        self.assertEqual(8, manifest["_placeholder_count"])
        self.assertGreater(manifest["_estimated_duration_seconds"], 7 * 60)
        self.assertLess(manifest["_estimated_duration_seconds"], 9 * 60)
        self.assertEqual("title_card", chapters[0].promo_type)
        self.assertEqual("generated", chapters[0].material_status)
        topics = {topic for chapter in chapters for topic in chapter.promo_topics}
        self.assertTrue(promo.REQUIRED_TOPICS.issubset(topics))
        corpus = " ".join(chapter.narration_en for chapter in chapters)
        for phrase in (
            "所有天朝制公爵及以上",
            "伯爵和男爵",
            "地方国库、个人金币和一年俸禄",
            "京察定期弹出、半强制，而且免费",
            "直接写明上司是谁、你拿多少分、同组第几、绩效几档",
            "361 张逐项政策卡",
            "17 类后果 profile",
            "14 本组织账",
        ):
            self.assertIn(phrase, corpus)

    def test_smoke_manifest_is_short_and_explicitly_not_final(self) -> None:
        manifest, chapters = promo.load_manifest(SMOKE_MANIFEST)
        self.assertEqual(1, len(chapters))
        self.assertLess(manifest["_estimated_duration_seconds"], 60)
        self.assertIn("not_a_promo_candidate", manifest["project_status"])
        self.assertIn("不是宣传成片", chapters[0].narration_en)

    def test_voice_is_exact_and_long_script_is_rejected(self) -> None:
        original = _absolute_sources(
            json.loads(FULL_MANIFEST.read_text(encoding="utf-8"))
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wrong_voice = dict(original)
            wrong_voice["voice"] = "zh-CN-YunxiNeural"
            wrong_voice_path = root / "wrong-voice.json"
            wrong_voice_path.write_text(
                json.dumps(wrong_voice, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(promo.PromoError, "voice must be exactly"):
                promo.load_manifest(wrong_voice_path)

            too_long = dict(original)
            too_long["minimum_chapter_seconds"] = 120
            too_long_path = root / "too-long.json"
            too_long_path.write_text(
                json.dumps(too_long, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(promo.PromoError, "offline duration estimate"):
                promo.load_manifest(too_long_path)

    def test_missing_topic_cannot_be_hidden_behind_a_tag(self) -> None:
        original = _absolute_sources(
            json.loads(FULL_MANIFEST.read_text(encoding="utf-8"))
        )
        for chapter in original["chapters"]:
            for cue in chapter["cues"]:
                cue["zh"] = cue["zh"].replace("强制分布", "配额分派")
                cue["spoken_zh"] = cue.get("spoken_zh", cue["zh"]).replace(
                    "强制分布", "配额分派"
                )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-keyword.json"
            path.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(promo.PromoError, "lacks Chinese script keyword"):
                promo.load_manifest(path)

    def test_361_copy_distinguishes_policy_cards_from_absent_subsystems(self) -> None:
        _manifest, chapters = promo.load_manifest(FULL_MANIFEST)
        corpus = " ".join(chapter.narration_en for chapter in chapters)
        for phrase in (
            "361 张逐项政策卡",
            "17 类后果 profile",
            "14 本组织账",
            "不是独立招聘模拟器",
            "不是一套带项目编号的项目管理器",
        ):
            self.assertIn(phrase, corpus)
        for unsupported_claim in (
            "形成晋升包",
            "跨部门答辩",
            "目标、期限、支持预算和中期检查",
            "冻结项目、责任和时间线",
        ):
            self.assertNotIn(unsupported_claim, corpus)


class SubtitleAndRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fonts = promo.shared.find_fonts()

    def test_every_cue_fits_both_measured_subtitle_safe_areas(self) -> None:
        _manifest, chapters = promo.load_manifest(FULL_MANIFEST)
        promo.prepare_subtitle_layouts(chapters, self.fonts)
        for chapter in chapters:
            self.assertEqual(len(chapter.promo_cues), len(chapter.promo_layouts))
            for layout in chapter.promo_layouts:
                self.assertLessEqual(len(layout["zh_lines"]), promo.SUBTITLE_MAX_LINES)
                self.assertLessEqual(len(layout["en_lines"]), promo.SUBTITLE_MAX_LINES)
                self.assertLessEqual(max(layout["zh_widths"]), promo.SUBTITLE_MAX_WIDTH)
                self.assertLessEqual(max(layout["en_widths"]), promo.SUBTITLE_MAX_WIDTH)

    def test_ass_keeps_chinese_and_english_simultaneous(self) -> None:
        _manifest, chapters = promo.load_manifest(SMOKE_MANIFEST)
        promo.prepare_subtitle_layouts(chapters, self.fonts)
        chapter = chapters[0]
        chapter.promo_cue_durations = [1.0] * len(chapter.promo_cues)
        chapter.shot_duration_seconds = 4.0
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bilingual.ass"
            promo.write_chapter_ass(chapter, path)
            text = path.read_text(encoding="utf-8-sig")
        self.assertIn("Style: ChinesePrimary", text)
        self.assertIn("Style: EnglishSecondary", text)
        self.assertEqual(len(chapter.promo_cues), text.count("ChinesePrimary,,"))
        self.assertEqual(len(chapter.promo_cues), text.count("EnglishSecondary,,"))
        first_zh = next(row for row in text.splitlines() if "ChinesePrimary,," in row)
        first_en = next(row for row in text.splitlines() if "EnglishSecondary,," in row)
        self.assertEqual(first_zh.split(",")[1:3], first_en.split(",")[1:3])

    def test_placeholder_frame_is_renderable_and_keeps_capture_identity(self) -> None:
        _manifest, chapters = promo.load_manifest(FULL_MANIFEST)
        chapter = next(row for row in chapters if row.promo_type == "placeholder_card")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "placeholder.png"
            promo._render_placeholder(chapter, self.fonts, destination)
            self.assertTrue(destination.is_file())
            with promo.shared.Image.open(destination) as image:
                self.assertEqual((promo.WIDTH, promo.HEIGHT), image.size)
                self.assertEqual("RGB", image.mode)

    def test_fixture_live_stills_keep_explicit_partial_classification(self) -> None:
        _manifest, chapters = promo.load_manifest(FULL_MANIFEST)
        imported = [
            chapter
            for chapter in chapters
            if chapter.classification == "fixture-live-still-partial"
        ]
        self.assertEqual(
            {
                "03-forced-distribution",
                "04-calibration",
                "06-jingcha",
                "07-scoreboard-receipt",
                "08-money-and-grade",
                "12-appeal",
            },
            {chapter.chapter_id for chapter in imported},
        )
        for chapter in imported:
            self.assertEqual("still", chapter.promo_type)
            self.assertEqual("captured", chapter.material_status)
            self.assertIn("CLEAN", chapter.status_en)
            self.assertGreaterEqual(len(chapter.sources), 3)


class AcceptanceStillImportTests(unittest.TestCase):
    def test_green_import_is_append_only_and_records_copy_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "green-run"
            source.mkdir()
            (source / "cell").mkdir()
            report = {"result": "GREEN", "cell": {"result": "GREEN"}}
            (source / "report.json").write_text(json.dumps(report), encoding="utf-8")
            (source / "evidence-index.json").write_text("{}", encoding="utf-8")
            for relative in acceptance_importer.RUN_FILES:
                path = source / relative
                if path.exists():
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(relative.encode("utf-8"))
            destination = root / "promo-import"
            index = acceptance_importer.import_run(
                artifact=source, destination=destination
            )
            payload = json.loads(index.read_text(encoding="utf-8"))
            self.assertEqual("fixture-live acceptance stills; not a clean promotional recording", payload["classification"])
            self.assertEqual(len(acceptance_importer.RUN_FILES), len(payload["files"]))
            with self.assertRaisesRegex(acceptance_importer.ImportError, "already exists"):
                acceptance_importer.import_run(artifact=source, destination=destination)


class BuildAndValidationTests(unittest.TestCase):
    def test_validate_only_never_calls_tts_or_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "missing" / "smoke.mp4"
            work = root / "missing-work"
            args = promo.parser().parse_args(
                [
                    "--manifest",
                    str(SMOKE_MANIFEST),
                    "--output",
                    str(output),
                    "--work-dir",
                    str(work),
                    "--validate-only",
                ]
            )
            communicate = mock.Mock(
                side_effect=AssertionError("validate-only attempted network TTS")
            )
            with (
                mock.patch.object(
                    promo.shared.edge_tts, "Communicate", communicate
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = promo.build(args)
            communicate.assert_not_called()
            self.assertEqual(output.resolve(), result[0])
            self.assertFalse(output.exists())
            self.assertFalse(work.exists())

    def test_release_gate_rejects_placeholder_animatic(self) -> None:
        with self.assertRaisesRegex(validator.ValidationError, "forbids placeholders"):
            with contextlib.redirect_stdout(io.StringIO()):
                validator.validate_project(FULL_MANIFEST, stage="release")

    def test_release_gate_rejects_a_zero_placeholder_smoke_manifest(self) -> None:
        with self.assertRaisesRegex(
            validator.ValidationError, "captured_release_candidate"
        ):
            with contextlib.redirect_stdout(io.StringIO()):
                validator.validate_project(SMOKE_MANIFEST, stage="release")

    def test_generated_script_is_reproducible(self) -> None:
        rendered = exporter.render(FULL_MANIFEST.resolve())
        self.assertEqual(
            rendered,
            GENERATED_SCRIPT.read_text(encoding="utf-8-sig"),
        )
        self.assertIn("中文配音 / 主字幕", rendered)
        self.assertIn("English subtitle", rendered)

    def test_archive_moves_instead_of_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "candidate.mp4"
            original.write_bytes(b"preserve-this-take")
            archived = promo._archive_output(original)
            self.assertFalse(original.exists())
            self.assertTrue(archived.is_file())
            self.assertEqual(b"preserve-this-take", archived.read_bytes())
            self.assertIn("superseded", archived.parts)


if __name__ == "__main__":
    unittest.main()
