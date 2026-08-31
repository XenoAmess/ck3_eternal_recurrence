"""Deterministic ffmpeg filter graphs, concat manifests, and render plans."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from .errors import PromoToolchainError
from .process import CommandResult, CommandSpec, run_command


class RenderPlanError(PromoToolchainError):
    """A render plan is invalid or cannot be safely materialized."""


@dataclass(frozen=True)
class RenderOptions:
    width: int
    height: int
    fps: int
    duration_seconds: float
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    pixel_format: str = "yuv420p"
    preset: str = "medium"
    crf: int = 20
    audio_bitrate: str = "192k"
    audio_sample_rate: int = 48_000
    audio_channels: int = 2
    pad_color: str = "black"

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise ValueError("render geometry and fps must be positive")
        if not math.isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ValueError("render duration must be positive and finite")
        if self.crf < 0 or self.crf > 63:
            raise ValueError("render crf must be in the inclusive range 0..63")
        if self.audio_sample_rate <= 0 or self.audio_channels <= 0:
            raise ValueError("audio sample rate and channel count must be positive")
        for label, value in (
            ("video codec", self.video_codec),
            ("audio codec", self.audio_codec),
            ("pixel format", self.pixel_format),
            ("preset", self.preset),
            ("audio bitrate", self.audio_bitrate),
            ("pad color", self.pad_color),
        ):
            if not value or "\x00" in value:
                raise ValueError(f"{label} must be a non-empty NUL-free string")


@dataclass(frozen=True)
class GeneratedTextFile:
    path: Path
    content: str
    encoding: str = "utf-8"


@dataclass(frozen=True)
class PlannedCommand:
    spec: CommandSpec
    audit_directory: Path


@dataclass(frozen=True)
class RenderPlan:
    commands: tuple[PlannedCommand, ...]
    generated_files: tuple[GeneratedTextFile, ...]
    partial_output: Path
    final_output: Path

    def __post_init__(self) -> None:
        if not self.commands:
            raise ValueError("render plan must contain at least one command")
        if self.partial_output == self.final_output:
            raise ValueError("partial and final render outputs must be distinct")


def seconds(value: float) -> str:
    """Format a finite timestamp identically across command-plan builds."""

    if not math.isfinite(value) or value < 0:
        raise ValueError("seconds must be finite and non-negative")
    return f"{value:.6f}"


def escape_filter_value(value: str | os.PathLike[str]) -> str:
    """Escape one libavfilter single-quoted option value.

    This is filtergraph escaping only.  No command-shell quoting is performed or
    needed because commands are always passed as argv with ``shell=False``.
    """

    raw = os.fspath(value).replace("\\", "/")
    if "\x00" in raw or "\n" in raw or "\r" in raw:
        raise RenderPlanError("filter values must be NUL-free single-line text")
    special = frozenset("\\':,;[]")
    return "".join(f"\\{character}" if character in special else character for character in raw)


def ass_burn_in_filter(path: str | os.PathLike[str]) -> str:
    """Build an ASS burn-in filter without assuming any locale or font."""

    return f"ass=filename='{escape_filter_value(path)}'"


def build_filtergraph(
    options: RenderOptions,
    *,
    ass_path: str | os.PathLike[str] | None = None,
) -> str:
    """Build a two-input video+narration filtergraph.

    Input 0 supplies video and input 1 supplies audio.  The graph normalizes
    geometry, frame rate, sample rate and duration.  ASS burn-in is optional and
    does not encode a particular language policy.
    """

    duration = seconds(options.duration_seconds)
    video_filters = [
        f"trim=duration={duration}",
        "setpts=PTS-STARTPTS",
        (
            f"scale={options.width}:{options.height}:"
            "force_original_aspect_ratio=decrease:flags=lanczos"
        ),
        (
            f"pad={options.width}:{options.height}:(ow-iw)/2:(oh-ih)/2:"
            f"color={options.pad_color}"
        ),
        "setsar=1",
        f"fps={options.fps}",
        f"tpad=stop_mode=clone:stop_duration={duration}",
        f"trim=duration={duration}",
    ]
    if ass_path is not None:
        video_filters.append(ass_burn_in_filter(ass_path))
    video_filters.append(f"format={options.pixel_format}")
    audio_filters = [
        f"aresample={options.audio_sample_rate}",
        "aformat=sample_fmts=fltp:channel_layouts=stereo"
        if options.audio_channels == 2
        else "aformat=sample_fmts=fltp",
        "apad",
        f"atrim=duration={duration}",
        "asetpts=N/SR/TB",
    ]
    return (
        "[0:v]" + ",".join(video_filters) + "[v];"
        "[1:a]" + ",".join(audio_filters) + "[a]"
    )


def _safe_concat_path(path: Path) -> str:
    value = path.as_posix()
    if not value or any(character in value for character in ("\x00", "\n", "\r", "'")):
        raise RenderPlanError(
            "concat paths must be non-empty and contain no NUL, newline or apostrophe"
        )
    return value


def _effective_path(path: Path, cwd: Path | None) -> Path:
    return path if path.is_absolute() or cwd is None else cwd / path


def concat_manifest(
    segment_paths: Sequence[Path],
    *,
    manifest_directory: Path | None = None,
) -> str:
    """Return a deterministic ffmpeg concat-demuxer manifest."""

    if not segment_paths:
        raise RenderPlanError("concat requires at least one segment")
    rows: list[str] = []
    for item in segment_paths:
        path = Path(item)
        if manifest_directory is not None:
            try:
                path = Path(os.path.relpath(path, start=manifest_directory))
            except ValueError:
                # Windows paths on different drives cannot be relativized.
                pass
        rows.append(f"file '{_safe_concat_path(path)}'")
    return "\n".join(rows) + "\n"


def plan_render(
    *,
    ffmpeg: str | os.PathLike[str],
    video_input: Path,
    audio_input: Path,
    partial_output: Path,
    final_output: Path,
    audit_directory: Path,
    options: RenderOptions,
    ass_path: Path | None = None,
    start_seconds: float = 0.0,
    working_directory: Path | None = None,
) -> RenderPlan:
    """Plan one normalized video/audio encode with optional ASS burn-in."""

    cwd = None if working_directory is None else Path(working_directory)
    effective_partial = _effective_path(Path(partial_output), cwd)
    effective_final = _effective_path(Path(final_output), cwd)
    start = seconds(start_seconds)
    graph = build_filtergraph(options, ass_path=ass_path)
    argv: list[str | os.PathLike[str]] = [
        ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-n",
    ]
    if start_seconds != 0:
        argv.extend(("-ss", start))
    argv.extend(
        (
            "-i",
            video_input,
            "-i",
            audio_input,
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            seconds(options.duration_seconds),
            "-c:v",
            options.video_codec,
            "-preset",
            options.preset,
            "-crf",
            str(options.crf),
            "-pix_fmt",
            options.pixel_format,
            "-c:a",
            options.audio_codec,
            "-b:a",
            options.audio_bitrate,
            "-ar",
            str(options.audio_sample_rate),
            "-ac",
            str(options.audio_channels),
            "-movflags",
            "+faststart",
            partial_output,
        )
    )
    spec = CommandSpec.create(
        argv,
        label="render media segment",
        cwd=cwd,
        partial_artifacts=(partial_output,),
    )
    return RenderPlan(
        commands=(PlannedCommand(spec, Path(audit_directory) / "render"),),
        generated_files=(),
        partial_output=effective_partial,
        final_output=effective_final,
    )


def plan_concat(
    *,
    ffmpeg: str | os.PathLike[str],
    segment_paths: Sequence[Path],
    concat_path: Path,
    partial_output: Path,
    final_output: Path,
    audit_directory: Path,
    working_directory: Path | None = None,
) -> RenderPlan:
    """Plan a stream-copy concat and retain its exact manifest as an input."""

    cwd = None if working_directory is None else Path(working_directory)
    effective_concat = _effective_path(Path(concat_path), cwd)
    effective_segments = tuple(_effective_path(Path(path), cwd) for path in segment_paths)
    effective_partial = _effective_path(Path(partial_output), cwd)
    effective_final = _effective_path(Path(final_output), cwd)
    content = concat_manifest(
        effective_segments, manifest_directory=effective_concat.parent
    )
    spec = CommandSpec.create(
        (
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-n",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            partial_output,
        ),
        label="concatenate media segments",
        cwd=cwd,
        partial_artifacts=(partial_output,),
    )
    return RenderPlan(
        commands=(PlannedCommand(spec, Path(audit_directory) / "concat"),),
        generated_files=(GeneratedTextFile(effective_concat, content),),
        partial_output=effective_partial,
        final_output=effective_final,
    )


def _materialize_text_file(item: GeneratedTextFile) -> None:
    payload = item.content.encode(item.encoding)
    item.path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with item.path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        try:
            existing = item.path.read_bytes()
        except OSError:
            existing = None
        if existing != payload:
            raise RenderPlanError(
                f"refusing to overwrite conflicting generated render input: {item.path}"
            ) from exc


CommandRunner = Callable[..., CommandResult]


def execute_render_plan(
    plan: RenderPlan,
    *,
    command_runner: CommandRunner = run_command,
) -> tuple[CommandResult, ...]:
    """Execute a plan and promote its partial output only after success.

    No cleanup occurs on exceptions.  The command runner retains stdout/stderr
    and the external program's partial artifact exactly where the plan put it.
    """

    if plan.final_output.exists():
        raise RenderPlanError(f"refusing to overwrite final output: {plan.final_output}")
    if plan.partial_output.exists():
        raise RenderPlanError(
            f"stale partial output must be audited or moved before retry: {plan.partial_output}"
        )
    for item in plan.generated_files:
        _materialize_text_file(item)
    plan.partial_output.parent.mkdir(parents=True, exist_ok=True)

    results: list[CommandResult] = []
    for command in plan.commands:
        results.append(
            command_runner(command.spec, audit_directory=command.audit_directory)
        )
    if not plan.partial_output.is_file():
        raise RenderPlanError(
            f"render commands succeeded without producing partial output: {plan.partial_output}"
        )
    plan.final_output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(plan.partial_output, plan.final_output)
    return tuple(results)


__all__ = [
    "GeneratedTextFile",
    "PlannedCommand",
    "RenderOptions",
    "RenderPlan",
    "RenderPlanError",
    "ass_burn_in_filter",
    "build_filtergraph",
    "concat_manifest",
    "escape_filter_value",
    "execute_render_plan",
    "plan_concat",
    "plan_render",
    "seconds",
]
