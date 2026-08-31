#!/usr/bin/env python3
"""Run a small, fully offline, real-media promotional pipeline smoke.

The caller supplies a fresh work directory and the ffmpeg/ffprobe executables.
All inputs, command audits, partial artifacts, outputs, review material, and
reports stay in that directory.  This script never removes an attempt and never
records a human sign-off.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys
import traceback
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.layout import FontSpec, SafeArea  # noqa: E402
from xar_promo.media import (  # noqa: E402
    MediaProbe,
    probe_media,
    require_streams,
    write_bound_media_probe,
)
from xar_promo.model import ProjectConfig  # noqa: E402
from xar_promo.pipeline import (  # noqa: E402
    PipelineDependencies,
    PipelineDraft,
    PipelineResult,
    SegmentDraft,
    run_pipeline,
)
from xar_promo.process import (  # noqa: E402
    CommandResult,
    CommandSpec,
    command_token,
    run_command,
)
from xar_promo.render import RenderOptions  # noqa: E402
from xar_promo.review import (  # noqa: E402
    ReviewPackagePlan,
    execute_review_frame_plan,
    plan_review_package,
    write_review_template,
)
from xar_promo.sources import (  # noqa: E402
    GENERATED_CARD,
    STILL,
    VisualProbeResult,
    VisualSource,
)
from xar_promo.subtitles import (  # noqa: E402
    AssCue,
    AssDocumentConfig,
    AssStyleConfig,
    SubtitleTrackConfig,
    render_ass_document,
)
from xar_promo.visuals import (  # noqa: E402
    BackgroundSpec,
    Box,
    CanvasSpec,
    LayerGroup,
    LowerThirdSpec,
    OverlaySpec,
    Palette,
    PanelElement,
    PillowFont,
    StillSpec,
    TextElement,
    TextStyle,
    TitleCardSpec,
    render_still,
    render_title_card,
)


WIDTH = 640
HEIGHT = 360
FPS = 24
SEGMENT_DURATION_SECONDS = 1.5
SAMPLE_RATE = 48_000


class SmokeError(RuntimeError):
    """The retained smoke attempt did not reach its GREEN report."""


@dataclass(frozen=True)
class SmokePlan:
    workdir: Path
    ffmpeg: str
    ffprobe: str
    project_id: str
    segment_ids: tuple[str, ...]
    deliverable_relative_path: Path

    @property
    def deliverable_path(self) -> Path:
        return self.workdir / self.deliverable_relative_path

    @property
    def report_path(self) -> Path:
        return self.workdir / "smoke-report.json"

    @property
    def report_hash_path(self) -> Path:
        return self.workdir / "smoke-report.sha256"

    def to_mapping(self) -> dict[str, object]:
        return {
            "workdir": self.workdir.as_posix(),
            "ffmpeg": self.ffmpeg,
            "ffprobe": self.ffprobe,
            "project_id": self.project_id,
            "segment_ids": list(self.segment_ids),
            "deliverable_relative_path": self.deliverable_relative_path.as_posix(),
        }


def build_smoke_plan(
    *,
    workdir: Path,
    ffmpeg: str | os.PathLike[str],
    ffprobe: str | os.PathLike[str],
) -> SmokePlan:
    """Build the pure, deterministic plan used by unit tests and the real run."""

    root = Path(workdir).expanduser().resolve()
    return SmokePlan(
        workdir=root,
        ffmpeg=command_token(ffmpeg),
        ffprobe=command_token(ffprobe),
        project_id="offline-pipeline-smoke",
        segment_ids=("title", "still"),
        deliverable_relative_path=Path("deliverables/offline-pipeline-smoke.mp4"),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_bytes_new(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as exc:
        raise SmokeError(f"refusing to overwrite retained smoke material: {path}") from exc
    return path


def _write_json_new(path: Path, value: object) -> Path:
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return _write_bytes_new(path, payload)


def _write_wav(path: Path, *, frequency_hz: float) -> Path:
    """Create deterministic stereo PCM narration without a network dependency."""

    if path.exists():
        raise SmokeError(f"refusing to overwrite retained narration: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = round(SEGMENT_DURATION_SECONDS * SAMPLE_RATE)
    fade_frames = round(0.03 * SAMPLE_RATE)
    payload = bytearray()
    for index in range(frame_count):
        envelope = min(1.0, index / fade_frames, (frame_count - index - 1) / fade_frames)
        sample = round(
            0.10
            * 32767
            * max(0.0, envelope)
            * math.sin(2.0 * math.pi * frequency_hz * index / SAMPLE_RATE)
        )
        payload.extend(struct.pack("<hh", sample, sample))
    with path.open("xb") as raw_output:
        with wave.open(raw_output, "wb") as output:
            output.setnchannels(2)
            output.setsampwidth(2)
            output.setframerate(SAMPLE_RATE)
            output.writeframes(payload)
        raw_output.flush()
        os.fsync(raw_output.fileno())
    return path


def _project_config() -> ProjectConfig:
    chapters = []
    for chapter_id, title, primary, secondary in (
        (
            "title",
            "Offline pipeline",
            "A reusable offline media pipeline",
            "Una canalización multimedia reutilizable",
        ),
        (
            "still",
            "Real render path",
            "Real Pillow, ASS, FFmpeg, concat, and probe",
            "Pillow, ASS, FFmpeg, unión y análisis reales",
        ),
    ):
        chapters.append(
            {
                "id": chapter_id,
                "type": "smoke",
                "state": "ready",
                "title": {"locale-a": title},
                "cues": [
                    {
                        "id": f"cue-{chapter_id}",
                        "narration": {"locale-a": primary},
                        "subtitles": {
                            "locale-a": primary,
                            "locale-b": secondary,
                        },
                    }
                ],
                "artifact_ids": [],
            }
        )
    return ProjectConfig.from_mapping(
        {
            "format_version": 1,
            "kind": "xar_promo_project_config",
            "project": {
                "id": "offline-pipeline-smoke",
                "title": "Offline Pipeline Smoke",
            },
            "pipeline": {"adapter": "generic", "preset": "offline-smoke"},
            "locales": {
                "narration": "locale-a",
                "subtitles": ["locale-a", "locale-b"],
            },
            "constraints": {"duration_limit_seconds": 30},
            "chapters": chapters,
        }
    )


def _render_options() -> RenderOptions:
    return RenderOptions(
        width=WIDTH,
        height=HEIGHT,
        fps=FPS,
        duration_seconds=SEGMENT_DURATION_SECONDS,
        preset="veryfast",
        crf=23,
        audio_bitrate="128k",
    )


def build_pipeline_draft(plan: SmokePlan) -> PipelineDraft:
    """Compose two generated visual sources and two injected offline WAVs."""

    options = _render_options()
    title_audio = plan.workdir / "inputs/audio/title.wav"
    still_audio = plan.workdir / "inputs/audio/still.wav"
    segments = (
        SegmentDraft(
            segment_id="title",
            visual_source=VisualSource(
                "title",
                GENERATED_CARD,
                Path("visuals/title.png"),
                "pillow-smoke",
                requires_resolution=True,
            ),
            render_options=options,
            subtitles={
                "locale-a": "A reusable offline media pipeline",
                "locale-b": "Una canalización multimedia reutilizable",
            },
            prepared_narration=title_audio,
        ),
        SegmentDraft(
            segment_id="still",
            visual_source=VisualSource(
                "still",
                STILL,
                Path("visuals/still.png"),
                "pillow-smoke",
                requires_resolution=True,
            ),
            render_options=options,
            subtitles={
                "locale-a": "Real Pillow, ASS, FFmpeg, concat, and probe",
                "locale-b": "Pillow, ASS, FFmpeg, unión y análisis reales",
            },
            prepared_narration=still_audio,
        ),
    )
    return PipelineDraft(
        config=_project_config(),
        segments=segments,
        deliverable_relative_path=plan.deliverable_relative_path,
        deliverable_artifact_id="offline-smoke-deliverable",
        deliverable_media_type="video/mp4",
    )


def _canvas() -> CanvasSpec:
    return CanvasSpec(
        width=WIDTH,
        height=HEIGHT,
        safe_area=SafeArea(WIDTH, HEIGHT, 28, 24, WIDTH - 28, HEIGHT - 24),
        palette=Palette(
            {
                "background": (9, 17, 31, 255),
                "background-end": (28, 46, 70, 255),
                "primary": (245, 248, 252, 255),
                "secondary": (153, 219, 238, 255),
                "panel": (4, 10, 22, 218),
                "outline": (76, 191, 196, 255),
            }
        ),
        background=BackgroundSpec(
            kind="gradient",
            color_role="background",
            end_color_role="background-end",
        ),
    )


def _pillow_fonts() -> tuple[Mapping[str, PillowFont], object]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SmokeError(
            "Pillow is required for the real smoke; install the 'visual' extra"
        ) from exc
    fonts = {
        "headline": PillowFont(
            FontSpec("headline", "Pillow bundled default", 34),
            ImageFont.load_default(size=34),
        ),
        "body": PillowFont(
            FontSpec("body", "Pillow bundled default", 20),
            ImageFont.load_default(size=20),
        ),
    }
    return fonts, (Image, ImageDraw)


def _visual_resolver(source: VisualSource, *, workdir: Path) -> Path:
    fonts, pillow = _pillow_fonts()
    Image, ImageDraw = pillow
    canvas = _canvas()
    if source.source_id == "title":
        payload = render_title_card(
            TitleCardSpec(
                canvas=canvas,
                layers=LayerGroup(
                    panels=(
                        PanelElement(
                            Box(52, 76, 588, 284),
                            "panel",
                            outline_role="outline",
                            outline_width=2,
                            radius=16,
                        ),
                    ),
                    texts=(
                        TextElement(
                            "Offline Promotional Pipeline",
                            Box(76, 108, 564, 164),
                            TextStyle(
                                "headline",
                                "primary",
                                line_height_px=44,
                                max_lines=1,
                                alignment="center",
                            ),
                        ),
                        TextElement(
                            "Generated title card, deterministic media plan",
                            Box(88, 190, 552, 236),
                            TextStyle(
                                "body",
                                "secondary",
                                line_height_px=28,
                                max_lines=2,
                                alignment="center",
                            ),
                        ),
                    ),
                ),
            ),
            fonts=fonts,
            assets={},
        )
    elif source.source_id == "still":
        source_image = Image.new("RGBA", (800, 450), (18, 36, 56, 255))
        draw = ImageDraw.Draw(source_image, "RGBA")
        draw.rectangle((70, 55, 730, 395), fill=(30, 80, 100, 255), outline=(100, 220, 205, 255), width=8)
        draw.ellipse((285, 80, 515, 310), fill=(235, 166, 72, 255), outline=(255, 232, 178, 255), width=8)
        payload = render_still(
            StillSpec(
                canvas=canvas,
                asset_key="source",
                fit_mode="crop",
                overlay=OverlaySpec(
                    lower_third=LowerThirdSpec(
                        panels=(
                            PanelElement(
                                Box(52, 270, 588, 326),
                                "panel",
                                outline_role="outline",
                                outline_width=1,
                                radius=10,
                            ),
                        ),
                        texts=(
                            TextElement(
                                "Real Pillow still -> media pipeline",
                                Box(70, 284, 570, 314),
                                TextStyle(
                                    "body",
                                    "primary",
                                    line_height_px=26,
                                    max_lines=1,
                                    alignment="center",
                                ),
                            ),
                        ),
                    )
                ),
            ),
            fonts=fonts,
            assets={"source": source_image},
        )
    else:
        raise SmokeError(f"unknown smoke visual source: {source.source_id}")
    output = (workdir / source.path).resolve()
    _write_bytes_new(output, payload)
    return output


def _pillow_probe(path: Path) -> VisualProbeResult:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SmokeError("Pillow is required to inspect smoke visuals") from exc
    with Image.open(path) as image:
        image.load()
        media_type = Image.MIME.get(image.format or "")
        if media_type is None:
            raise SmokeError(f"Pillow could not identify media type for {path}")
        return VisualProbeResult(media_type, image.width, image.height)


def _subtitle_renderer(
    segment: SegmentDraft, narration: object, *, workdir: Path
) -> str:
    del narration, workdir
    primary = AssStyleConfig(
        name="Primary",
        font_name="Arial",
        font_size=25,
        alignment=2,
        margin_left=28,
        margin_right=28,
        margin_vertical=25,
    )
    secondary = AssStyleConfig(
        name="Secondary",
        font_name="Arial",
        font_size=22,
        primary_colour="&H00E0D090",
        alignment=8,
        margin_left=28,
        margin_right=28,
        margin_vertical=24,
    )
    tracks = (
        SubtitleTrackConfig("track-a", "locale-a", 0, primary),
        SubtitleTrackConfig("track-b", "locale-b", 1, secondary),
    )
    end = segment.render_options.duration_seconds - 0.05
    cues = (
        AssCue(
            f"{segment.segment_id}-a",
            "track-a",
            0.05,
            end,
            segment.subtitles["locale-a"],
        ),
        AssCue(
            f"{segment.segment_id}-b",
            "track-b",
            0.05,
            end,
            segment.subtitles["locale-b"],
        ),
    )
    return render_ass_document(
        AssDocumentConfig(
            title=f"Offline smoke {segment.segment_id}",
            play_res_x=segment.render_options.width,
            play_res_y=segment.render_options.height,
            duration_seconds=segment.render_options.duration_seconds,
        ),
        tracks,
        cues,
        available_font_names=("Arial",),
    )


CommandRunner = Callable[..., CommandResult]


def build_pipeline_dependencies(
    plan: SmokePlan,
    *,
    subtitle_renderer: Callable[..., str] = _subtitle_renderer,
    visual_resolver: Callable[..., Path] = _visual_resolver,
    visual_probe: Callable[[Path], VisualProbeResult] = _pillow_probe,
    command_runner: CommandRunner = run_command,
) -> PipelineDependencies:
    """Expose all effectful seams so CI tests need no media executable."""

    return PipelineDependencies(
        ffmpeg=plan.ffmpeg,
        subtitle_renderer=subtitle_renderer,
        command_runner=command_runner,
        visual_probe=visual_probe,
        visual_resolver=visual_resolver,
    )


def _dependency_version(
    executable: str,
    *,
    name: str,
    workdir: Path,
    command_runner: CommandRunner,
) -> str:
    result = command_runner(
        CommandSpec.create((executable, "-version"), label=f"inspect {name} version"),
        audit_directory=workdir / "audit/dependencies" / name,
    )
    rows = (result.stdout or result.stderr).splitlines()
    return rows[0].strip() if rows else "version output was empty"


def _artifact_rows(result: PipelineResult) -> list[dict[str, object]]:
    return [item.to_audit_mapping() for item in result.artifacts]


def _inventory(root: Path, *, excluded: Sequence[Path] = ()) -> list[dict[str, object]]:
    ignored = {item.resolve() for item in excluded}
    rows = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=str):
        if path.resolve() in ignored:
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return rows


def _storyboard(duration_seconds: float) -> dict[str, object]:
    if duration_seconds <= SEGMENT_DURATION_SECONDS:
        raise SmokeError("concatenated deliverable is too short for both chapters")
    return {
        "boundary_seconds": [SEGMENT_DURATION_SECONDS],
        "chapters": [
            {
                "id": "title",
                "start_seconds": 0,
                "end_seconds": SEGMENT_DURATION_SECONDS,
            },
            {
                "id": "still",
                "start_seconds": SEGMENT_DURATION_SECONDS,
                "end_seconds": duration_seconds,
            },
        ],
    }


def execute_smoke(
    plan: SmokePlan,
    *,
    pipeline_runner: Callable[..., PipelineResult] = run_pipeline,
    media_prober: Callable[..., MediaProbe] = probe_media,
    review_planner: Callable[..., ReviewPackagePlan] = plan_review_package,
    review_executor: Callable[..., tuple[CommandResult, ...]] = execute_review_frame_plan,
    review_writer: Callable[..., Path] = write_review_template,
    command_runner: CommandRunner = run_command,
) -> dict[str, object]:
    """Execute one real attempt and leave every byte in ``plan.workdir``."""

    try:
        plan.workdir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise SmokeError(
            f"smoke workdir already exists and must be retained: {plan.workdir}"
        ) from exc

    ffmpeg_version = _dependency_version(
        plan.ffmpeg,
        name="ffmpeg",
        workdir=plan.workdir,
        command_runner=command_runner,
    )
    ffprobe_version = _dependency_version(
        plan.ffprobe,
        name="ffprobe",
        workdir=plan.workdir,
        command_runner=command_runner,
    )
    title_wav = _write_wav(
        plan.workdir / "inputs/audio/title.wav", frequency_hz=440.0
    )
    still_wav = _write_wav(
        plan.workdir / "inputs/audio/still.wav", frequency_hz=554.37
    )
    draft = build_pipeline_draft(plan)
    dependencies = build_pipeline_dependencies(
        plan,
        command_runner=command_runner,
    )
    validated = pipeline_runner(
        draft,
        workdir=plan.workdir,
        dependencies=dependencies,
        validate_only=True,
        offline_tts=True,
    ).require_success()
    result = pipeline_runner(
        draft,
        workdir=plan.workdir,
        dependencies=dependencies,
        validate_only=False,
        offline_tts=True,
    ).require_success()
    if result.audit_record is None or result.signoff_recorded:
        raise SmokeError(
            "pipeline succeeded without a pending audit candidate or recorded a sign-off"
        )
    audit_candidate_path = _write_json_new(
        plan.workdir / "audit/pipeline-audit-candidate.json",
        result.audit_record.to_mapping(),
    )

    probe = media_prober(
        plan.ffprobe,
        plan.deliverable_path,
        audit_directory=plan.workdir / "audit/probe-deliverable",
        command_runner=command_runner,
    )
    require_streams(probe, video=True, audio=True)
    bound_probe_path = plan.workdir / "audit/probe-deliverable.bound.json"
    bound_probe = write_bound_media_probe(
        bound_probe_path,
        media_path=plan.deliverable_path,
        probe=probe,
    )
    timeline = _storyboard(probe.require_duration())
    review_plan = review_planner(
        ffmpeg=plan.ffmpeg,
        artifact_path=plan.deliverable_path,
        probe=probe,
        storyboard_timeline=timeline,
        output_directory=plan.workdir / "review",
        audit_directory=plan.workdir / "audit/review",
    )
    review_executor(review_plan, command_runner=command_runner)
    review_template_path = review_writer(
        plan.workdir / "review/review-template.json", review_plan
    )

    try:
        import PIL
    except ImportError as exc:
        raise SmokeError("Pillow disappeared during the real smoke") from exc
    inventory = _inventory(
        plan.workdir,
        excluded=(plan.report_path, plan.report_hash_path),
    )
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "xar-promo-real-pipeline-smoke-report",
        "status": "green",
        "plan": plan.to_mapping(),
        "dependencies": {
            "pillow": PIL.__version__,
            "ffmpeg": ffmpeg_version,
            "ffprobe": ffprobe_version,
        },
        "offline_narration": {
            "network_tts_used": False,
            "format": "stereo PCM WAV",
            "sample_rate": SAMPLE_RATE,
            "files": [title_wav.as_posix(), still_wav.as_posix()],
        },
        "pipeline": {
            "validate_status": validated.status,
            "run_status": result.status,
            "signoff_recorded": result.signoff_recorded,
            "phases": [item.to_mapping() for item in result.phases],
            "artifacts": _artifact_rows(result),
        },
        "audit_candidate": {
            "path": audit_candidate_path.relative_to(plan.workdir).as_posix(),
            "bytes": audit_candidate_path.stat().st_size,
            "sha256": _sha256(audit_candidate_path),
            "state": result.audit_record.status,
            "human_signoff_required": result.audit_record.human_signoff_required,
        },
        "probe_and_review": {
            "bound_probe_path": bound_probe_path.relative_to(
                plan.workdir
            ).as_posix(),
            "bound_probe_bytes": bound_probe_path.stat().st_size,
            "bound_probe_sha256": _sha256(bound_probe_path),
            "subject_bytes": bound_probe.subject_bytes,
            "subject_sha256": bound_probe.subject_sha256,
            "artifact_summary": dict(review_plan.artifact_summary),
            "storyboard_timeline": timeline,
            "review_template_path": review_template_path.relative_to(
                plan.workdir
            ).as_posix(),
            "review_template_sha256": _sha256(review_template_path),
            "review_state": review_plan.review_template["state"],
            "is_signoff": review_plan.review_template["is_signoff"],
            "approval_granted": review_plan.review_template["approval_granted"],
            "extracted_frame_count": len(review_plan.frames),
        },
        "retention": {
            "workdir_preserved": True,
            "cleanup_performed": False,
            "command_audits": [
                row["path"]
                for row in inventory
                if str(row["path"]).endswith("command.json")
            ],
            "files": inventory,
        },
    }
    _write_json_new(plan.report_path, report)
    report_hash = _sha256(plan.report_path)
    _write_bytes_new(
        plan.report_hash_path,
        f"{report_hash}  {plan.report_path.name}\n".encode("ascii"),
    )
    report["report_sha256"] = report_hash
    return report


def _write_failure_record(plan: SmokePlan, error: BaseException) -> None:
    if not plan.workdir.is_dir():
        return
    target = plan.workdir / "smoke-failure.json"
    if target.exists():
        return
    try:
        _write_json_new(
            target,
            {
                "format_version": 1,
                "kind": "xar-promo-real-pipeline-smoke-failure",
                "status": "red",
                "exception_type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
                "workdir_preserved": True,
                "cleanup_performed": False,
                "retained_files": _inventory(plan.workdir, excluded=(target,)),
            },
        )
    except Exception:
        # Never trade the original retained failure for reporting convenience.
        pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--ffprobe", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    plan = build_smoke_plan(
        workdir=args.workdir,
        ffmpeg=args.ffmpeg,
        ffprobe=args.ffprobe,
    )
    try:
        report = execute_smoke(plan)
    except BaseException as error:
        _write_failure_record(plan, error)
        print(f"RED: {type(error).__name__}: {error}", file=sys.stderr)
        print(f"retained workdir: {plan.workdir}", file=sys.stderr)
        return 1
    print(f"GREEN: {plan.report_path}")
    print(f"SHA-256: {report['report_sha256']}")
    print(f"retained workdir: {plan.workdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
