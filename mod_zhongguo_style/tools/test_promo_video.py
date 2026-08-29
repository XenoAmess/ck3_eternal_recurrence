#!/usr/bin/env python3
"""Offline tests for the ZhongGuo 361 promo pipeline."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import types
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
            "头部 30% 得 3.75、中间 60% 得 3.5、尾部 10% 得 3.25",
            "地方国库、个人金币、贤能和一年俸禄",
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

    def test_release_rendered_fields_reject_fixture_text(self) -> None:
        original = _absolute_sources(
            json.loads(FULL_MANIFEST.read_text(encoding="utf-8"))
        )
        original["project_status"] = "captured_release_candidate"
        original["chapters"][0]["status"]["zh"] = "361制实机验收"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture-overlay-release.json"
            path.write_text(
                json.dumps(original, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                promo.PromoError,
                "release rendered field contains fixture/test-only text",
            ):
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

    def test_video_shot_duration_covers_the_complete_mark_interval(self) -> None:
        _manifest, chapters = promo.load_manifest(FULL_MANIFEST)
        chapter = chapters[0]
        chapter.promo_type = "video_clip"
        chapter.start_seconds = 80.0
        chapter.end_seconds = 131.0
        chapter.min_duration_seconds = 4.0
        chapter.tail_padding_seconds = 1.2

        duration = promo._required_shot_duration(
            chapter, narration_duration_seconds=27.0
        )

        self.assertEqual(51.0, duration)


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
    @staticmethod
    def _minimal_release_project() -> tuple[dict, list[types.SimpleNamespace]]:
        manifest = {
            "_placeholder_count": 0,
            "_estimated_duration_seconds": 1.0,
            "project_status": "captured_release_candidate",
            "release_manifest_provenance": {},
        }
        chapter = types.SimpleNamespace(
            chapter_id="00-title",
            promo_type="title_card",
            material_status="generated",
            raw={},
            status_zh="",
            status_en="",
        )
        return manifest, [chapter]

    @staticmethod
    def _verified_report_for(manifest_path: Path) -> dict:
        return {
            "evaluation_sha256": "E" * 64,
            "evaluation": {
                "result": "GREEN",
                "release_manifest": {
                    "path": str(manifest_path.resolve()),
                    "bytes": manifest_path.stat().st_size,
                    "sha256": promo.shared._sha256(manifest_path),
                },
            },
        }

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
                mock.patch.object(promo.visual_audit, "verify_report") as verify_audit,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = promo.build(args)
            communicate.assert_not_called()
            verify_audit.assert_not_called()
            self.assertEqual(output.resolve(), result[0])
            self.assertFalse(output.exists())
            self.assertFalse(work.exists())

    def test_visual_audit_re_evaluates_and_binds_the_exact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "release-manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            report_path = root / "visual-audit.json"
            report_path.write_text("{}\n", encoding="utf-8")
            expected_sha = promo.shared._sha256(report_path)
            verified = self._verified_report_for(manifest_path)
            with mock.patch.object(
                promo.visual_audit, "verify_report", return_value=verified
            ) as verify_report:
                binding = promo.verify_visual_audit_binding(
                    manifest_path=manifest_path,
                    report_path=report_path,
                    expected_sha256=expected_sha,
                    required=True,
                )
            verify_report.assert_called_once_with(report_path.resolve(), expected_sha)
            self.assertEqual("GREEN", binding["result"])
            self.assertEqual(expected_sha, binding["report"]["sha256"])
            self.assertEqual(
                promo.shared._sha256(manifest_path),
                binding["release_manifest"]["sha256"],
            )

            wrong_manifest = dict(verified)
            wrong_manifest["evaluation"] = dict(verified["evaluation"])
            wrong_manifest["evaluation"]["release_manifest"] = {
                **verified["evaluation"]["release_manifest"],
                "path": str(root / "different-release-manifest.json"),
            }
            with (
                mock.patch.object(
                    promo.visual_audit,
                    "verify_report",
                    return_value=wrong_manifest,
                ),
                self.assertRaisesRegex(promo.PromoError, "different release manifest"),
            ):
                promo.verify_visual_audit_binding(
                    manifest_path=manifest_path,
                    report_path=report_path,
                    expected_sha256=expected_sha,
                    required=True,
                )

    def test_visual_audit_arguments_are_paired_and_release_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifest_path = Path(temporary) / "release-manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(promo.PromoError, "release media requires"):
                promo.verify_visual_audit_binding(
                    manifest_path=manifest_path,
                    report_path=None,
                    expected_sha256=None,
                    required=True,
                )
            with self.assertRaisesRegex(promo.PromoError, "provided together"):
                promo.verify_visual_audit_binding(
                    manifest_path=manifest_path,
                    report_path=Path(temporary) / "audit.json",
                    expected_sha256=None,
                    required=False,
                )
            with self.assertRaisesRegex(promo.PromoError, "64 hexadecimal"):
                promo.verify_visual_audit_binding(
                    manifest_path=manifest_path,
                    report_path=Path(temporary) / "audit.json",
                    expected_sha256="not-a-sha",
                    required=False,
                )

    def test_release_validation_requires_and_re_evaluates_visual_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "release-manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            report_path = root / "visual-audit.json"
            report_path.write_text("{}\n", encoding="utf-8")
            expected_sha = promo.shared._sha256(report_path)

            def dependencies(manifest: dict, chapters: list[types.SimpleNamespace]):
                return (
                    mock.patch.object(promo, "load_manifest", return_value=(manifest, chapters)),
                    mock.patch.object(
                        promo.shared,
                        "find_program",
                        side_effect=[Path("ffmpeg"), Path("ffprobe")],
                    ),
                    mock.patch.object(promo.shared, "find_fonts", return_value=object()),
                    mock.patch.object(promo.shared, "preflight_video_sources"),
                    mock.patch.object(promo, "prepare_subtitle_layouts"),
                )

            manifest, chapters = self._minimal_release_project()
            with contextlib.ExitStack() as stack:
                for patcher in dependencies(manifest, chapters):
                    stack.enter_context(patcher)
                with self.assertRaisesRegex(
                    validator.ValidationError, "release media requires"
                ):
                    validator.validate_project(manifest_path, stage="release")

            manifest, chapters = self._minimal_release_project()
            verified = self._verified_report_for(manifest_path)
            with contextlib.ExitStack() as stack:
                for patcher in dependencies(manifest, chapters):
                    stack.enter_context(patcher)
                verify_report = stack.enter_context(
                    mock.patch.object(
                        promo.visual_audit, "verify_report", return_value=verified
                    )
                )
                checked, _chapters = validator.validate_project(
                    manifest_path,
                    stage="release",
                    visual_audit_report=report_path,
                    expected_audit_sha256=expected_sha,
                )
            verify_report.assert_called_once_with(report_path.resolve(), expected_sha)
            self.assertEqual("GREEN", checked["_visual_audit_binding"]["result"])

    def test_formal_build_requires_audit_before_writes_and_draft_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "release-manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            output = root / "output" / "promo.mp4"
            work = root / "work"
            manifest, chapters = self._minimal_release_project()
            base_args = [
                "--manifest",
                str(manifest_path),
                "--output",
                str(output),
                "--work-dir",
                str(work),
                "--validate-only",
            ]
            with (
                mock.patch.object(promo, "load_manifest", return_value=(manifest, chapters)),
                self.assertRaisesRegex(promo.PromoError, "release media requires"),
            ):
                promo.build(promo.parser().parse_args(base_args))
            self.assertFalse(output.exists())
            self.assertFalse(work.exists())

            report_path = root / "visual-audit.json"
            report_path.write_text("{}\n", encoding="utf-8")
            expected_sha = promo.shared._sha256(report_path)
            manifest, chapters = self._minimal_release_project()
            with (
                mock.patch.object(promo, "load_manifest", return_value=(manifest, chapters)),
                mock.patch.object(
                    promo.visual_audit,
                    "verify_report",
                    return_value=self._verified_report_for(manifest_path),
                ) as verify_report,
                mock.patch.object(
                    promo.shared,
                    "find_program",
                    side_effect=[Path("ffmpeg"), Path("ffprobe")],
                ),
                mock.patch.object(promo.shared, "find_fonts", return_value=object()),
                mock.patch.object(promo.shared, "preflight_video_sources"),
                mock.patch.object(promo, "prepare_subtitle_layouts"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                promo.build(
                    promo.parser().parse_args(
                        base_args
                        + [
                            "--visual-audit-report",
                            str(report_path),
                            "--expected-audit-sha256",
                            expected_sha,
                        ]
                    )
                )
            verify_report.assert_called_once_with(report_path.resolve(), expected_sha)
            self.assertFalse(output.exists())
            self.assertFalse(work.exists())

    def test_sidecar_persists_audit_binding_and_release_validation_requires_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "release-manifest.json"
            manifest_path.write_text("{}\n", encoding="utf-8")
            output = root / "promo.mp4"
            output.write_bytes(b"video")
            subtitle = root / "promo.ass"
            subtitle.write_text("subtitle", encoding="utf-8")
            binding = {
                "verification": "audit_promo_visuals.verify_report re-evaluation",
                "result": "GREEN",
                "report": {"path": "audit.json", "bytes": 1, "sha256": "A" * 64},
                "evaluation_sha256": "B" * 64,
                "release_manifest": {
                    "path": str(manifest_path.resolve()),
                    "bytes": manifest_path.stat().st_size,
                    "sha256": promo.shared._sha256(manifest_path),
                },
            }
            sidecar_path = promo.write_sidecar(
                manifest_path=manifest_path,
                manifest={"_placeholder_count": 0, "project_status": "captured_release_candidate"},
                chapters=[],
                output=output,
                output_info={
                    "duration": 1.0,
                    "video": {"width": 2560, "height": 1440},
                    "audio": {"sample_rate": "48000", "tags": {"language": "zho"}},
                },
                global_ass=subtitle,
                take_id="release-test",
                ffmpeg=Path("ffmpeg"),
                ffprobe=Path("ffprobe"),
                visual_audit_binding=binding,
            )
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(binding, sidecar["visual_audit"])

            del sidecar["visual_audit"]
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            manifest = {"_placeholder_count": 0, "_visual_audit_binding": binding}
            with self.assertRaisesRegex(
                validator.ValidationError, "sidecar visual audit does not match"
            ):
                validator.validate_media(
                    manifest_path=manifest_path,
                    manifest=manifest,
                    chapters=[],
                    video_path=output,
                    sidecar_path=sidecar_path,
                    stage="release",
                )

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
