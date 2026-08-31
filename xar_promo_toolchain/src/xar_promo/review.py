"""Deterministic planning for a human promotional-video review package.

The package produced here is deliberately *not* a sign-off.  It binds a
finished artifact, its already collected ffprobe result, a storyboard timeline,
and shell-free frame-extraction commands into material a human can review.  All
human fields remain empty and every checklist item remains pending.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .errors import PromoToolchainError
from .media import MediaProbe, MediaStream
from .process import CommandResult, CommandSpec, command_token, run_command
from .render import PlannedCommand, seconds


REVIEW_TEMPLATE_KIND = "xar-promo-human-review-template"
REVIEW_TEMPLATE_VERSION = 1
PENDING_REVIEW_STATE = "pending-human-review"


class ReviewPlanError(PromoToolchainError):
    """A review package cannot be planned or materialized safely."""


@dataclass(frozen=True)
class StoryboardChapter:
    """One validated chapter on the rendered artifact timeline."""

    chapter_id: str
    start_seconds: Decimal
    end_seconds: Decimal
    boundary_seconds: tuple[Decimal, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.chapter_id,
            "start_seconds": _timestamp(self.start_seconds),
            "end_seconds": _timestamp(self.end_seconds),
            "boundary_seconds": [
                _timestamp(value) for value in self.boundary_seconds
            ],
        }


@dataclass(frozen=True)
class ReviewFrame:
    """A single, deduplicated point-in-time frame extraction."""

    frame_id: str
    timestamp_seconds: Decimal
    roles: tuple[str, ...]
    chapter_ids: tuple[str, ...]
    partial_output: Path
    final_output: Path
    command: PlannedCommand

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.frame_id,
            "timestamp_seconds": _timestamp(self.timestamp_seconds),
            "roles": list(self.roles),
            "chapter_ids": list(self.chapter_ids),
            "path": self.final_output.as_posix(),
        }


@dataclass(frozen=True)
class ReviewPackagePlan:
    """Immutable command plan plus JSON-ready human review material."""

    artifact_summary: Mapping[str, object]
    chapters: tuple[StoryboardChapter, ...]
    checklist: tuple[Mapping[str, object], ...]
    frames: tuple[ReviewFrame, ...]
    review_template: Mapping[str, object]


def _decimal(value: Any, context: str) -> Decimal:
    if isinstance(value, bool):
        raise ReviewPlanError(f"{context} must be a finite number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ReviewPlanError(f"{context} must be a finite number") from exc
    if not result.is_finite():
        raise ReviewPlanError(f"{context} must be a finite number")
    return result


def _timestamp(value: Decimal) -> str:
    if not value.is_finite() or value < 0:
        raise ReviewPlanError("review timestamps must be finite and non-negative")
    return f"{value:.6f}"


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewPlanError(f"{context} must be a non-empty string")
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ReviewPlanError(f"{context} must be NUL-free single-line text")
    return value


def _timeline_rows(
    timeline: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> tuple[Sequence[Mapping[str, Any]], Sequence[Any]]:
    if isinstance(timeline, Mapping):
        rows = timeline.get("chapters")
        global_boundaries = timeline.get("boundary_seconds", ())
    elif isinstance(timeline, Sequence) and not isinstance(
        timeline, (str, bytes, bytearray)
    ):
        rows = timeline
        global_boundaries = ()
    else:
        raise ReviewPlanError(
            "storyboard timeline must be a chapter array or an object containing chapters"
        )
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ReviewPlanError("storyboard timeline chapters must be an array")
    if not isinstance(global_boundaries, Sequence) or isinstance(
        global_boundaries, (str, bytes, bytearray)
    ):
        raise ReviewPlanError("storyboard timeline boundary_seconds must be an array")
    return rows, global_boundaries


def normalize_storyboard_timeline(
    timeline: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    duration_seconds: float,
) -> tuple[tuple[StoryboardChapter, ...], tuple[Decimal, ...]]:
    """Validate the small generic timeline surface used by the reviewer.

    Each chapter has ``id``, ``start_seconds`` and ``end_seconds`` and may have
    ``boundary_seconds`` for important internal cuts.  The root object may also
    have ``boundary_seconds`` for cuts not owned by a chapter.  Gaps are valid;
    overlap and reordering are rejected instead of silently changing authorial
    intent.
    """

    duration = _decimal(duration_seconds, "artifact duration")
    if duration <= 0:
        raise ReviewPlanError("artifact duration must be greater than zero")
    raw_rows, raw_global_boundaries = _timeline_rows(timeline)
    if not raw_rows:
        raise ReviewPlanError("storyboard timeline must contain at least one chapter")

    chapters: list[StoryboardChapter] = []
    seen: set[str] = set()
    previous_end = Decimal(0)
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, Mapping):
            raise ReviewPlanError(f"storyboard chapters[{index}] must be an object")
        chapter_id = _string(raw.get("id"), f"storyboard chapters[{index}].id")
        if chapter_id in seen:
            raise ReviewPlanError(f"storyboard repeats chapter id {chapter_id!r}")
        seen.add(chapter_id)
        start = _decimal(
            raw.get("start_seconds"), f"storyboard chapters[{index}].start_seconds"
        )
        end = _decimal(
            raw.get("end_seconds"), f"storyboard chapters[{index}].end_seconds"
        )
        if start < 0 or end <= start:
            raise ReviewPlanError(
                f"storyboard chapter {chapter_id!r} must have 0 <= start < end"
            )
        if end > duration:
            raise ReviewPlanError(
                f"storyboard chapter {chapter_id!r} exceeds artifact duration"
            )
        if chapters and start < previous_end:
            raise ReviewPlanError(
                f"storyboard chapter {chapter_id!r} overlaps or precedes its predecessor"
            )
        raw_boundaries = raw.get("boundary_seconds", ())
        if not isinstance(raw_boundaries, Sequence) or isinstance(
            raw_boundaries, (str, bytes, bytearray)
        ):
            raise ReviewPlanError(
                f"storyboard chapter {chapter_id!r} boundary_seconds must be an array"
            )
        boundaries = tuple(
            _decimal(value, f"storyboard chapter {chapter_id!r} boundary_seconds")
            for value in raw_boundaries
        )
        if tuple(sorted(set(boundaries))) != boundaries:
            raise ReviewPlanError(
                f"storyboard chapter {chapter_id!r} boundaries must be unique and ordered"
            )
        if any(value <= start or value >= end for value in boundaries):
            raise ReviewPlanError(
                f"storyboard chapter {chapter_id!r} boundaries must be strictly internal"
            )
        chapters.append(StoryboardChapter(chapter_id, start, end, boundaries))
        previous_end = end

    global_boundaries = tuple(
        _decimal(value, "storyboard boundary_seconds")
        for value in raw_global_boundaries
    )
    if tuple(sorted(set(global_boundaries))) != global_boundaries:
        raise ReviewPlanError(
            "storyboard root boundaries must be unique and ordered"
        )
    if any(value <= 0 or value >= duration for value in global_boundaries):
        raise ReviewPlanError(
            "storyboard root boundaries must be strictly inside artifact duration"
        )
    return tuple(chapters), global_boundaries


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _tags(stream: MediaStream) -> Mapping[str, Any]:
    value = stream.raw.get("tags", {})
    return value if isinstance(value, Mapping) else {}


def _fraction(value: Fraction | None) -> str | None:
    return None if value is None else f"{value.numerator}/{value.denominator}"


def summarize_artifact(
    artifact_path: Path,
    probe: MediaProbe,
    *,
    working_directory: Path | None = None,
) -> dict[str, object]:
    """Hash the artifact and summarize only facts present in ffprobe output."""

    declared_path = Path(artifact_path)
    effective = (
        declared_path
        if declared_path.is_absolute() or working_directory is None
        else Path(working_directory) / declared_path
    )
    if not effective.is_file():
        raise ReviewPlanError(f"review artifact was not found: {effective}")
    duration = probe.require_duration()
    if not probe.video_streams:
        raise ReviewPlanError("review artifact probe contains no video stream")

    video_tracks = [
        {
            "index": stream.index,
            "codec": stream.codec_name,
            "width": stream.width,
            "height": stream.height,
            "average_frame_rate": _fraction(stream.average_frame_rate),
        }
        for stream in probe.video_streams
    ]
    audio_tracks = [
        {
            "index": stream.index,
            "codec": stream.codec_name,
            "sample_rate": stream.sample_rate,
            "channels": stream.channels,
        }
        for stream in probe.audio_streams
    ]
    subtitle_tracks = []
    for stream in probe.streams:
        if stream.codec_type != "subtitle":
            continue
        tags = _tags(stream)
        language = tags.get("language")
        title = tags.get("title")
        subtitle_tracks.append(
            {
                "index": stream.index,
                "codec": stream.codec_name,
                "language": language if isinstance(language, str) else None,
                "title": title if isinstance(title, str) else None,
            }
        )
    primary = probe.video_streams[0]
    format_name = probe.format.get("format_name")
    return {
        "path": command_token(declared_path),
        "bytes": effective.stat().st_size,
        "sha256": _sha256_file(effective),
        "duration_seconds": seconds(duration),
        "container": format_name if isinstance(format_name, str) else None,
        "resolution": {"width": primary.width, "height": primary.height},
        "video_tracks": video_tracks,
        "audio_tracks": audio_tracks,
        "subtitle_tracks": subtitle_tracks,
    }


def _frame_interval(probe: MediaProbe) -> Decimal:
    rate = probe.video_streams[0].average_frame_rate
    if rate is None or rate <= 0:
        return Decimal(1) / Decimal(30)
    return Decimal(rate.denominator) / Decimal(rate.numerator)


def _frame_points(
    chapters: tuple[StoryboardChapter, ...],
    global_boundaries: tuple[Decimal, ...],
    *,
    duration: Decimal,
    frame_interval: Decimal,
) -> list[tuple[Decimal, tuple[str, ...], tuple[str, ...]]]:
    points: dict[Decimal, tuple[set[str], set[str]]] = {}

    def add(timestamp: Decimal, role: str, chapter_id: str | None = None) -> None:
        clipped = min(max(timestamp, Decimal(0)), max(Decimal(0), duration - frame_interval))
        roles, chapter_ids = points.setdefault(clipped, (set(), set()))
        roles.add(role)
        if chapter_id is not None:
            chapter_ids.add(chapter_id)

    add(Decimal(0), "artifact-first")
    add(duration - frame_interval, "artifact-final")
    for chapter in chapters:
        add(chapter.start_seconds, "chapter-start", chapter.chapter_id)
        add(
            max(chapter.start_seconds, chapter.end_seconds - frame_interval),
            "chapter-end",
            chapter.chapter_id,
        )
        for boundary in chapter.boundary_seconds:
            add(boundary - frame_interval, "boundary-before", chapter.chapter_id)
            add(boundary, "boundary-after", chapter.chapter_id)
    for boundary in global_boundaries:
        add(boundary - frame_interval, "boundary-before")
        add(boundary, "boundary-after")
    return [
        (timestamp, tuple(sorted(roles)), tuple(sorted(chapter_ids)))
        for timestamp, (roles, chapter_ids) in sorted(points.items())
    ]


def _checklist(
    chapters: tuple[StoryboardChapter, ...],
    *,
    duration: Decimal,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = [
        {
            "id": "watch-complete-at-1x",
            "required": True,
            "state": "pending",
            "instruction": (
                "Watch continuously at exactly 1.0x from 0.000000 through "
                f"{_timestamp(duration)} without skipping, scrubbing, or fast playback."
            ),
        },
        {
            "id": "verify-picture-and-sound",
            "required": True,
            "state": "pending",
            "instruction": (
                "Confirm picture and sound remain present, synchronized, and free of "
                "unexpected interruption for the complete viewing."
            ),
        },
        {
            "id": "verify-subtitles-and-on-screen-text",
            "required": True,
            "state": "pending",
            "instruction": (
                "Confirm intended subtitles and on-screen text are readable, timed, "
                "and inside the visible frame."
            ),
        },
        {
            "id": "verify-first-and-final-frame",
            "required": True,
            "state": "pending",
            "instruction": (
                "Inspect the extracted first and final frames for clean entry and exit."
            ),
        },
    ]
    for index, chapter in enumerate(chapters, start=1):
        rows.append(
            {
                "id": f"verify-chapter-{index:04d}",
                "chapter_id": chapter.chapter_id,
                "required": True,
                "state": "pending",
                "instruction": (
                    f"Inspect chapter {chapter.chapter_id!r} continuously and compare "
                    "its start, end, and declared boundary frames with the storyboard."
                ),
            }
        )
    return tuple(rows)


def _review_template(
    artifact_summary: Mapping[str, object],
    chapters: tuple[StoryboardChapter, ...],
    checklist: tuple[Mapping[str, object], ...],
    frames: tuple[ReviewFrame, ...],
) -> dict[str, object]:
    return {
        "format_version": REVIEW_TEMPLATE_VERSION,
        "kind": REVIEW_TEMPLATE_KIND,
        "state": PENDING_REVIEW_STATE,
        "template_only": True,
        "is_signoff": False,
        "approval_granted": False,
        "artifact": dict(artifact_summary),
        "timeline": {"chapters": [chapter.to_dict() for chapter in chapters]},
        "full_watch": {
            "required_playback_speed": 1.0,
            "no_skipping": True,
            "checklist": [dict(row) for row in checklist],
        },
        "frame_evidence": [frame.to_dict() for frame in frames],
        "human_response": {
            "reviewer": None,
            "reviewed_at": None,
            "decision": None,
            "notes": None,
            "checklist_results": {},
        },
    }


def plan_review_package(
    *,
    ffmpeg: str | os.PathLike[str],
    artifact_path: Path,
    probe: MediaProbe,
    storyboard_timeline: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    output_directory: Path,
    audit_directory: Path,
    working_directory: Path | None = None,
) -> ReviewPackagePlan:
    """Plan a generic review package without executing media tools or approving it."""

    duration_float = probe.require_duration()
    artifact_summary = summarize_artifact(
        Path(artifact_path), probe, working_directory=working_directory
    )
    chapters, global_boundaries = normalize_storyboard_timeline(
        storyboard_timeline, duration_seconds=duration_float
    )
    duration = _decimal(duration_float, "artifact duration")
    # Container duration can extend beyond the video stream (for example AAC
    # encoder padding in MP4).  Review metadata must retain that honest format
    # duration, while frame seeks must stop within actual video coverage.
    video_duration = probe.video_streams[0].duration_seconds
    frame_duration = (
        duration
        if video_duration is None
        else min(duration, _decimal(video_duration, "primary video duration"))
    )
    points = _frame_points(
        chapters,
        global_boundaries,
        duration=frame_duration,
        frame_interval=_frame_interval(probe),
    )

    cwd = None if working_directory is None else Path(working_directory)
    output_root = Path(output_directory)
    frames: list[ReviewFrame] = []
    for index, (timestamp, roles, chapter_ids) in enumerate(points, start=1):
        frame_id = f"frame-{index:06d}"
        final_output = output_root / "frames" / f"{frame_id}.png"
        partial_output = output_root / "frames" / f".{frame_id}.partial.png"
        effective_final = (
            final_output
            if final_output.is_absolute() or cwd is None
            else cwd / final_output
        )
        effective_partial = (
            partial_output
            if partial_output.is_absolute() or cwd is None
            else cwd / partial_output
        )
        spec = CommandSpec.create(
            (
                ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-i",
                artifact_path,
                "-ss",
                seconds(float(timestamp)),
                "-map",
                "0:v:0",
                "-frames:v",
                "1",
                "-f",
                "image2",
                partial_output,
            ),
            label=f"extract human-review frame {frame_id}",
            cwd=cwd,
            partial_artifacts=(partial_output,),
        )
        frames.append(
            ReviewFrame(
                frame_id,
                timestamp,
                roles,
                chapter_ids,
                effective_partial,
                effective_final,
                PlannedCommand(spec, Path(audit_directory) / "frames" / frame_id),
            )
        )

    checklist = _checklist(chapters, duration=duration)
    frozen_frames = tuple(frames)
    template = _review_template(
        artifact_summary, chapters, checklist, frozen_frames
    )
    return ReviewPackagePlan(
        artifact_summary,
        chapters,
        checklist,
        frozen_frames,
        template,
    )


CommandRunner = Callable[..., CommandResult]


def execute_review_frame_plan(
    plan: ReviewPackagePlan,
    *,
    command_runner: CommandRunner = run_command,
) -> tuple[CommandResult, ...]:
    """Extract planned frames, retaining every failed command and partial image."""

    for frame in plan.frames:
        if frame.final_output.exists():
            raise ReviewPlanError(
                f"refusing to overwrite review frame: {frame.final_output}"
            )
        if frame.partial_output.exists():
            raise ReviewPlanError(
                "stale review-frame partial must be audited or moved before retry: "
                f"{frame.partial_output}"
            )
    results: list[CommandResult] = []
    for frame in plan.frames:
        frame.partial_output.parent.mkdir(parents=True, exist_ok=True)
        result = command_runner(
            frame.command.spec,
            audit_directory=frame.command.audit_directory,
        )
        results.append(result)
        if not frame.partial_output.is_file():
            raise ReviewPlanError(
                "frame command succeeded without producing its partial artifact: "
                f"{frame.partial_output}"
            )
        frame.final_output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(frame.partial_output, frame.final_output)
    return tuple(results)


def _validate_pending_template(value: Mapping[str, object]) -> None:
    human = value.get("human_response")
    if (
        value.get("kind") != REVIEW_TEMPLATE_KIND
        or value.get("state") != PENDING_REVIEW_STATE
        or value.get("template_only") is not True
        or value.get("is_signoff") is not False
        or value.get("approval_granted") is not False
        or not isinstance(human, Mapping)
        or human.get("reviewer") is not None
        or human.get("reviewed_at") is not None
        or human.get("decision") is not None
    ):
        raise ReviewPlanError(
            "review template must remain pending and cannot contain a sign-off decision"
        )


def write_review_template(path: Path, plan: ReviewPackagePlan) -> Path:
    """Write the pending template exclusively; this never records a sign-off."""

    value = dict(plan.review_template)
    _validate_pending_template(value)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ReviewPlanError(
            f"refusing to overwrite human-review template: {target}"
        ) from exc
    return target


__all__ = [
    "PENDING_REVIEW_STATE",
    "REVIEW_TEMPLATE_KIND",
    "REVIEW_TEMPLATE_VERSION",
    "ReviewFrame",
    "ReviewPackagePlan",
    "ReviewPlanError",
    "StoryboardChapter",
    "execute_review_frame_plan",
    "normalize_storyboard_timeline",
    "plan_review_package",
    "summarize_artifact",
    "write_review_template",
]
