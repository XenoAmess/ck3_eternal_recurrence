from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(0, str(PACKAGE_ROOT / "scripts"))

import run_pipeline_smoke as smoke  # noqa: E402

from xar_promo.process import CommandResult, CommandSpec  # noqa: E402
from xar_promo.sources import GENERATED_CARD, STILL, VisualProbeResult  # noqa: E402


class PipelineSmokeScriptTests(unittest.TestCase):
    def test_plan_is_deterministic_and_preserves_injected_executables(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            arguments = {
                "workdir": Path(raw) / "retained attempt",
                "ffmpeg": "vendor/tools/custom-ffmpeg",
                "ffprobe": Path("vendor/tools/custom-ffprobe"),
            }
            first = smoke.build_smoke_plan(**arguments)
            second = smoke.build_smoke_plan(**arguments)

        self.assertEqual(first, second)
        self.assertEqual(first.ffmpeg, "vendor/tools/custom-ffmpeg")
        self.assertEqual(first.ffprobe, "vendor/tools/custom-ffprobe")
        self.assertEqual(first.segment_ids, ("title", "still"))
        self.assertEqual(
            first.deliverable_relative_path,
            Path("deliverables/offline-pipeline-smoke.mp4"),
        )
        self.assertEqual(first.to_mapping(), second.to_mapping())

    def test_draft_uses_canonical_visual_sources_and_offline_wav_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            plan = smoke.build_smoke_plan(
                workdir=Path(raw) / "attempt",
                ffmpeg="ffmpeg-injected",
                ffprobe="ffprobe-injected",
            )
            draft = smoke.build_pipeline_draft(plan)

        self.assertEqual([item.segment_id for item in draft.segments], ["title", "still"])
        self.assertEqual(draft.segments[0].visual_source.kind, GENERATED_CARD)
        self.assertEqual(draft.segments[1].visual_source.kind, STILL)
        self.assertTrue(
            all(item.visual_source.requires_resolution for item in draft.segments)
        )
        self.assertEqual(
            [item.prepared_narration.suffix for item in draft.segments],
            [".wav", ".wav"],
        )
        self.assertTrue(all(item.narration_request is None for item in draft.segments))
        self.assertEqual(
            tuple(draft.config.subtitle_locales), ("locale-a", "locale-b")
        )

    def test_pipeline_dependencies_keep_every_effectful_seam_injected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            plan = smoke.build_smoke_plan(
                workdir=Path(raw) / "attempt",
                ffmpeg="tools/ffmpeg-custom",
                ffprobe="tools/ffprobe-custom",
            )

            def subtitle_renderer(*args: object, **kwargs: object) -> str:
                return "ASS"

            def visual_resolver(*args: object, **kwargs: object) -> Path:
                return Path(raw) / "visual.png"

            def visual_probe(path: Path) -> VisualProbeResult:
                return VisualProbeResult("image/png", 640, 360)

            def command_runner(
                spec: CommandSpec, *, audit_directory: Path
            ) -> CommandResult:
                return CommandResult(
                    spec, 0, "", "", "succeeded", audit_directory, ()
                )

            dependencies = smoke.build_pipeline_dependencies(
                plan,
                subtitle_renderer=subtitle_renderer,
                visual_resolver=visual_resolver,
                visual_probe=visual_probe,
                command_runner=command_runner,
            )

        self.assertEqual(dependencies.ffmpeg, "tools/ffmpeg-custom")
        self.assertIs(dependencies.subtitle_renderer, subtitle_renderer)
        self.assertIs(dependencies.visual_resolver, visual_resolver)
        self.assertIs(dependencies.visual_probe, visual_probe)
        self.assertIs(dependencies.command_runner, command_runner)
        self.assertIsNone(dependencies.tts_cache)
        self.assertIsNone(dependencies.tts_provider)


if __name__ == "__main__":
    unittest.main()
