"""Subprocess-only fake registry components and PipelineComposer."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import CommandResult, CommandSpec, run_command
from xar_promo.render import RenderOptions
from xar_promo.sources import GENERATED_CARD, STILL, VisualProbeResult, VisualSource
from xar_promo.storyboard import TimelineSpacing, plan_storyboard


def adapter_factory(*_: object, **__: object) -> object:
    raise AssertionError("the composer, not the CLI, owns adapter factory invocation")


def preset_factory(*_: object, **__: object) -> object:
    raise AssertionError("the composer, not the CLI, owns preset factory invocation")


def _required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing subprocess fixture environment variable {name}")
    return Path(value).resolve()


def _runner(spec: CommandSpec, *, audit_directory: Path) -> CommandResult:
    fail = os.environ.get("XAR_PROMO_CLI_FIXTURE_MODE") == "build-failure"

    def execute(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        for partial in spec.partial_artifacts:
            path = partial if partial.is_absolute() else spec.cwd / partial
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"cli-fixture:{spec.label}".encode("utf-8"))
        return subprocess.CompletedProcess(
            argv,
            23 if fail else 0,
            stdout="cli retained stdout" if fail else "cli render stdout",
            stderr="cli retained stderr" if fail else "cli render stderr",
        )

    return run_command(spec, audit_directory=audit_directory, run=execute)


def compose(
    config,
    run,
    *,
    config_path: Path,
    run_path: Path | None,
    workdir: Path,
    adapter_factory,
    preset_factory,
    validate_only: bool,
) -> PipelineInvocation:
    if not callable(adapter_factory) or not callable(preset_factory):
        raise RuntimeError("registry did not resolve callable component factories")
    timeline = plan_storyboard(
        config,
        narration_duration_resolver=lambda *_: None,
        draft_estimator=lambda *_: 1,
        spacing=TimelineSpacing(cue_gap_seconds=0, chapter_gap_seconds=0),
        available_artifact_ids=(),
        validate_only=validate_only,
    )
    generated = validate_only
    visual = VisualSource(
        source_id="visual.cli-cue",
        kind=GENERATED_CARD if generated else STILL,
        path=(Path("planned/generated-card.png") if generated else _required_path("XAR_PROMO_CLI_FIXTURE_VISUAL")),
        origin="cli-subprocess-fixture",
        requires_resolution=generated,
    )

    def visual_resolver(source: VisualSource, *, workdir: Path) -> Path:
        raise AssertionError("read-only plan invoked the visual resolver")

    def visual_probe(_: Path) -> VisualProbeResult:
        return VisualProbeResult(media_type="image/png", width=640, height=360)

    def subtitle_renderer(*_: object, **__: object) -> str:
        return "[Script Info]\nTitle: CLI subprocess fixture\n[Events]\n"

    segment = SegmentDraft(
        segment_id="cli-cue",
        visual_source=visual,
        render_options=RenderOptions(
            width=640,
            height=360,
            fps=24,
            duration_seconds=float(timeline.duration_seconds),
        ),
        subtitles={"und": "CLI subtitle"},
        prepared_narration=_required_path("XAR_PROMO_CLI_FIXTURE_NARRATION"),
    )
    return PipelineInvocation(
        draft=PipelineDraft(
            config=config,
            segments=(segment,),
            deliverable_relative_path=Path("deliverables/final.mp4"),
            deliverable_artifact_id="final-video",
            deliverable_media_type="video/mp4",
        ),
        dependencies=PipelineDependencies(
            ffmpeg="fake-cli-ffmpeg",
            subtitle_renderer=subtitle_renderer,
            command_runner=_runner,
            visual_probe=visual_probe,
            visual_resolver=visual_resolver if generated else None,
        ),
        workdir=workdir,
    )
