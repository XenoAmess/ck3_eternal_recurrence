from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.pipeline import (  # noqa: E402
    NarrationArtifact,
    PipelineDependencies,
    PipelineDraft,
    PipelineExecutionError,
    PipelineInvocation,
    SegmentDraft,
    run_invocation,
    run_pipeline,
)
from xar_promo.model import new_project_config  # noqa: E402
from xar_promo.process import (  # noqa: E402
    CommandResult,
    CommandSpec,
    run_command,
)
from xar_promo.render import RenderOptions  # noqa: E402
from xar_promo.sources import (  # noqa: E402
    GENERATED_CARD,
    VIDEO,
    VisualProbeResult,
    VisualSource,
)
from xar_promo.tts import (  # noqa: E402
    ProviderIdentity,
    TtsCache,
    TtsCacheValidationError,
    TtsRequest,
)


class _AudioValidator:
    validator_id = "pipeline-test-audio"
    validator_version = "1"

    def validate(self, path: Path, *, expected_format: str) -> dict[str, object]:
        payload = path.read_bytes()
        if not payload.startswith(b"TEST-AUDIO:"):
            raise TtsCacheValidationError("synthetic audio is invalid")
        return {"format": expected_format, "bytes": len(payload)}


class _TtsProvider:
    def __init__(self) -> None:
        self._identity = ProviderIdentity("pipeline-fake-tts", "1")
        self.calls: list[TtsRequest] = []

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    def synthesize(self, request: TtsRequest, destination: Path) -> None:
        self.calls.append(request)
        destination.write_bytes(b"TEST-AUDIO:" + request.text.encode("utf-8"))


class _SubtitleRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, tuple[str, ...], Path]] = []

    def __call__(
        self,
        segment: SegmentDraft,
        narration: NarrationArtifact,
        *,
        workdir: Path,
    ) -> str:
        self.calls.append(
            (
                segment.segment_id,
                narration.origin,
                tuple(segment.subtitles),
                workdir,
            )
        )
        events = "\\N".join(segment.subtitles.values())
        return "[Script Info]\nTitle: test\n[Events]\n" + events + "\n"


class _VisualProbe:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def __call__(self, path: Path) -> VisualProbeResult:
        self.calls.append(path)
        media_type = "image/png" if path.suffix.lower() == ".png" else "video/x-matroska"
        return VisualProbeResult(media_type=media_type, width=640, height=360)


class _SuccessfulRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[CommandSpec, Path]] = []

    def __call__(
        self, spec: CommandSpec, *, audit_directory: Path
    ) -> CommandResult:
        self.calls.append((spec, audit_directory))

        def complete(
            argv: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            for partial in spec.partial_artifacts:
                effective = partial if partial.is_absolute() else (spec.cwd / partial)
                effective.parent.mkdir(parents=True, exist_ok=True)
                effective.write_bytes(
                    f"rendered:{spec.label}:{len(self.calls)}".encode("utf-8")
                )
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=f"stdout-{len(self.calls)}",
                stderr=f"stderr-{len(self.calls)}",
            )

        return run_command(
            spec,
            audit_directory=audit_directory,
            run=complete,
        )


def _project():
    return new_project_config(
        "portable-promo",
        "Portable Promo",
        "narration-locale",
        ["subtitle-locale-a", "subtitle-locale-b"],
        "injected-adapter",
        "injected-preset",
    )


def _options(duration: float = 2.5) -> RenderOptions:
    return RenderOptions(width=640, height=360, fps=24, duration_seconds=duration)


def _segment(
    root: Path,
    segment_id: str,
    *,
    narration_request: TtsRequest | None = None,
    prepared_narration: Path | None = None,
    prepared_visual: bool = True,
) -> SegmentDraft:
    video = root / f"{segment_id}.source.mkv"
    if prepared_visual:
        video.write_bytes(b"SOURCE-VIDEO:" + segment_id.encode("ascii"))
    return SegmentDraft(
        segment_id=segment_id,
        visual_source=VisualSource(
            source_id=f"source.{segment_id}",
            kind=VIDEO if prepared_visual else GENERATED_CARD,
            path=video if prepared_visual else Path("generated-cards") / f"{segment_id}.png",
            origin="test-prepared" if prepared_visual else "test-generated",
            requires_resolution=not prepared_visual,
        ),
        render_options=_options(),
        subtitles={
            "subtitle-locale-a": f"Subtitle A for {segment_id}",
            "subtitle-locale-b": f"Subtitle B for {segment_id}",
        },
        narration_request=narration_request,
        prepared_narration=prepared_narration,
    )


class PipelineTests(unittest.TestCase):
    def test_deliverable_id_cannot_collide_with_pipeline_owned_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            narration = root / "prepared.wav"
            narration.write_bytes(b"PREPARED-NARRATION")
            segment = _segment(
                root,
                "opening",
                prepared_narration=narration,
            )
            calls: list[str] = []

            def forbidden(*_: object, **__: object) -> Any:
                calls.append("effect")
                raise AssertionError("artifact-id validation invoked a dependency")

            for artifact_id in (
                "visual.opening",
                "narration.opening",
                "subtitle.opening",
                "segment.opening",
                "concat.manifest",
            ):
                with self.subTest(artifact_id=artifact_id):
                    workdir = root / f"attempt-{artifact_id.replace('.', '-')}"
                    result = run_pipeline(
                        PipelineDraft(
                            config=_project(),
                            segments=(segment,),
                            deliverable_relative_path=Path("output/final.mkv"),
                            deliverable_artifact_id=artifact_id,
                            deliverable_media_type="video/x-matroska",
                        ),
                        workdir=workdir,
                        validate_only=True,
                        dependencies=PipelineDependencies(
                            ffmpeg="not-invoked",
                            subtitle_renderer=forbidden,
                            command_runner=forbidden,
                            visual_probe=forbidden,
                        ),
                    )
                    self.assertEqual(result.status, "failed")
                    self.assertEqual(result.failure.phase, "draft")
                    self.assertIn("pipeline-owned artifact id", result.failure.message)
                    self.assertFalse(workdir.exists())
            self.assertEqual(calls, [])

    def test_full_cached_tts_to_concat_returns_byte_bound_audit_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            provider = _TtsProvider()
            cache = TtsCache(root / "cache", validator=_AudioValidator())
            subtitles = _SubtitleRenderer()
            runner = _SuccessfulRunner()
            segments = tuple(
                _segment(
                    root,
                    segment_id,
                    narration_request=TtsRequest(
                        text=f"Narration for {segment_id}",
                        voice=voice,
                        audio_format="mp3",
                    ),
                )
                for segment_id, voice in (
                    ("opening", "caller-voice-alpha"),
                    ("closing", "caller-voice-beta"),
                )
            )
            draft = PipelineDraft(
                config=_project(),
                segments=segments,
                deliverable_relative_path=Path("deliverables/final.webm"),
                deliverable_artifact_id="release-candidate",
                deliverable_media_type="video/webm",
            )
            result = run_invocation(
                PipelineInvocation(
                    draft=draft,
                    workdir=root / "attempt",
                    dependencies=PipelineDependencies(
                        ffmpeg="caller-ffmpeg",
                        subtitle_renderer=subtitles,
                        command_runner=runner,
                        visual_probe=_VisualProbe(),
                        tts_cache=cache,
                        tts_provider=provider,
                    ),
                )
            )

            self.assertEqual(result.status, "succeeded")
            self.assertTrue(result.succeeded)
            self.assertIsNone(result.failure)
            self.assertFalse(result.signoff_recorded)
            self.assertEqual(
                [phase.phase for phase in result.phases],
                [
                    "draft",
                    "visual",
                    "narration",
                    "subtitle",
                    "segment-plan",
                    "segment-render",
                    "concat",
                    "audit-record-ready",
                ],
            )
            self.assertTrue(all(phase.status == "succeeded" for phase in result.phases))
            self.assertEqual(
                [request.voice for request in provider.calls],
                ["caller-voice-alpha", "caller-voice-beta"],
            )
            self.assertEqual(2, len(subtitles.calls))
            self.assertEqual(3, len(runner.calls))
            self.assertTrue(
                all(call[0].argv[0] == "caller-ffmpeg" for call in runner.calls)
            )
            deliverable = next(
                item for item in result.artifacts if item.role == "deliverable"
            )
            self.assertEqual(deliverable.media_type, "video/webm")
            self.assertTrue(deliverable.path.is_file())
            self.assertEqual(
                deliverable.sha256,
                hashlib.sha256(deliverable.path.read_bytes()).hexdigest().upper(),
            )
            source_record = deliverable.to_source_record(
                project_root=result.workdir,
                label="Pipeline deliverable awaiting audit",
            )
            self.assertEqual(source_record.path, "deliverables/final.webm")
            self.assertEqual(source_record.sha256, deliverable.sha256)
            self.assertIsNotNone(result.audit_record)
            audit = result.audit_record.to_mapping()
            self.assertEqual(audit["status"], "pending-project-audit")
            self.assertIs(audit["human_signoff_required"], True)
            self.assertEqual(audit["deliverable"]["sha256"], deliverable.sha256)
            self.assertIs(result.require_success(), result)

    def test_validate_only_is_read_only_and_invokes_no_generation_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workdir = root / "must-not-be-created"
            segment = _segment(
                root,
                "validate",
                narration_request=TtsRequest(
                    text="No provider call",
                    voice="validate-only-caller-voice",
                ),
                prepared_visual=False,
            )
            calls: list[str] = []

            class ExplodingCache:
                def get_or_create(self, *_: object, **__: object) -> Any:
                    calls.append("tts-cache")
                    raise AssertionError("validate-only called TTS")

            class ExplodingProvider:
                @property
                def identity(self) -> Any:
                    calls.append("tts-provider")
                    raise AssertionError("validate-only inspected provider")

            def explode(*_: object, **__: object) -> Any:
                calls.append("effectful-dependency")
                raise AssertionError("validate-only invoked a generation dependency")

            draft = PipelineDraft(
                config=_project(),
                segments=(segment,),
                deliverable_relative_path=Path("output/custom.container"),
                deliverable_artifact_id="candidate",
                deliverable_media_type="video/custom",
            )
            result = run_pipeline(
                draft,
                workdir=workdir,
                validate_only=True,
                dependencies=PipelineDependencies(
                    ffmpeg="not-invoked",
                    subtitle_renderer=explode,
                    command_runner=explode,
                    visual_probe=explode,
                    tts_cache=ExplodingCache(),
                    tts_provider=ExplodingProvider(),
                    visual_resolver=explode,
                    render_planner=explode,
                    concat_planner=explode,
                    plan_executor=explode,
                    draft_validator=lambda _: calls.append("draft-validator"),
                ),
            )

            self.assertEqual(result.status, "validated")
            self.assertTrue(result.validate_only)
            self.assertFalse(workdir.exists())
            self.assertEqual(calls, ["draft-validator"])
            self.assertEqual(result.artifacts, ())
            self.assertIsNone(result.audit_record)
            self.assertIsNone(result.failure)
            self.assertFalse(result.signoff_recorded)
            self.assertEqual(result.phases[0].status, "validated")
            self.assertTrue(
                all(phase.status == "skipped" for phase in result.phases[1:])
            )

    def test_prepared_audio_and_legacy_resolver_bypass_new_tts_cache(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            prepared = root / "legacy-fixed" / "narration.en.opening.mp3"
            prepared.parent.mkdir()
            prepared.write_bytes(b"LEGACY-PREPARED")
            first = _segment(
                root,
                "prepared",
                prepared_narration=prepared,
            )
            second = _segment(root, "resolved", prepared_visual=False)
            resolver_calls: list[tuple[str, Path]] = []
            visual_calls: list[tuple[str, Path]] = []

            def legacy_resolver(
                segment: SegmentDraft, *, workdir: Path
            ) -> NarrationArtifact:
                resolver_calls.append((segment.segment_id, workdir))
                path = workdir / "legacy-narration" / f"{segment.segment_id}.wav"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"LEGACY-RESOLVER")
                return NarrationArtifact(
                    path=path,
                    media_type="audio/wav",
                    origin="legacy-wrapper",
                    metadata={"old_cache_contract": True},
                )

            def legacy_visual_resolver(
                source: VisualSource, *, workdir: Path
            ) -> Path:
                visual_calls.append((source.source_id, workdir))
                path = workdir / source.path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"LEGACY-GENERATED-CARD")
                return path.resolve()

            subtitles = _SubtitleRenderer()
            runner = _SuccessfulRunner()
            result = run_pipeline(
                PipelineDraft(
                    config=_project(),
                    segments=(first, second),
                    deliverable_relative_path=Path("output/final.mkv"),
                    deliverable_artifact_id="legacy-compatible",
                    deliverable_media_type="video/x-matroska",
                ),
                workdir=root / "attempt",
                dependencies=PipelineDependencies(
                    ffmpeg="fake-ffmpeg",
                    subtitle_renderer=subtitles,
                    command_runner=runner,
                    visual_probe=_VisualProbe(),
                    visual_resolver=legacy_visual_resolver,
                    narration_resolver=legacy_resolver,
                ),
            )

            self.assertTrue(result.succeeded)
            self.assertEqual(resolver_calls, [("resolved", (root / "attempt").resolve())])
            self.assertEqual(visual_calls, [("source.resolved", (root / "attempt").resolve())])
            self.assertEqual(
                [(item[0], item[1]) for item in subtitles.calls],
                [("prepared", "prepared"), ("resolved", "legacy-wrapper")],
            )
            narration_paths = {
                item.artifact_id: item.path
                for item in result.artifacts
                if item.role == "narration"
            }
            self.assertEqual(narration_paths["narration.prepared"], prepared.resolve())
            self.assertEqual(
                narration_paths["narration.resolved"],
                (root / "attempt/legacy-narration/resolved.wav").resolve(),
            )

    def test_render_failure_keeps_partial_stdio_workdir_and_never_signs_off(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            provider = _TtsProvider()
            cache = TtsCache(root / "cache", validator=_AudioValidator())
            segment = _segment(
                root,
                "failure",
                narration_request=TtsRequest(
                    text="This render intentionally fails.",
                    voice="failure-test-voice",
                ),
            )
            runner_calls: list[Path] = []

            def failing_runner(
                spec: CommandSpec, *, audit_directory: Path
            ) -> CommandResult:
                runner_calls.append(audit_directory)

                def fail(
                    argv: list[str], **_: object
                ) -> subprocess.CompletedProcess[str]:
                    for partial in spec.partial_artifacts:
                        effective = partial if partial.is_absolute() else spec.cwd / partial
                        effective.parent.mkdir(parents=True, exist_ok=True)
                        effective.write_bytes(b"RETAIN-THIS-PARTIAL")
                    return subprocess.CompletedProcess(
                        argv,
                        17,
                        stdout="retained stdout",
                        stderr="retained stderr",
                    )

                return run_command(
                    spec,
                    audit_directory=audit_directory,
                    run=fail,
                )

            workdir = root / "failed-attempt"
            result = run_pipeline(
                PipelineDraft(
                    config=_project(),
                    segments=(segment,),
                    deliverable_relative_path=Path("deliverable/final.mp4"),
                    deliverable_artifact_id="must-not-exist",
                    deliverable_media_type="video/mp4",
                ),
                workdir=workdir,
                dependencies=PipelineDependencies(
                    ffmpeg="fake-ffmpeg",
                    subtitle_renderer=_SubtitleRenderer(),
                    command_runner=failing_runner,
                    visual_probe=_VisualProbe(),
                    tts_cache=cache,
                    tts_provider=provider,
                ),
            )

            self.assertEqual(result.status, "failed")
            self.assertFalse(result.succeeded)
            self.assertTrue(workdir.is_dir())
            self.assertEqual(result.phases[-1].phase, "segment-render")
            self.assertEqual(result.phases[-1].status, "failed")
            self.assertIsNone(result.audit_record)
            self.assertFalse(result.signoff_recorded)
            self.assertIsNotNone(result.failure)
            failure = result.failure
            self.assertEqual(failure.stdout, "retained stdout")
            self.assertEqual(failure.stderr, "retained stderr")
            self.assertEqual(len(failure.partial_paths), 1)
            self.assertEqual(
                failure.partial_paths[0].read_bytes(), b"RETAIN-THIS-PARTIAL"
            )
            self.assertEqual(len(failure.stdout_paths), 1)
            self.assertEqual(len(failure.stderr_paths), 1)
            self.assertEqual(
                failure.stdout_paths[0].read_text(encoding="utf-8"),
                "retained stdout",
            )
            self.assertEqual(
                failure.stderr_paths[0].read_text(encoding="utf-8"),
                "retained stderr",
            )
            self.assertIn(failure.partial_paths[0], failure.retained_paths)
            self.assertFalse((workdir / "deliverable/final.mp4").exists())
            with self.assertRaises(PipelineExecutionError) as raised:
                result.require_success()
            self.assertIs(raised.exception.result, result)


if __name__ == "__main__":
    unittest.main()
