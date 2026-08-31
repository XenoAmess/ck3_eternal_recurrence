"""Pure, deterministic chapter and cue timeline planning.

This module does not synthesize narration, probe media, invoke FFmpeg, or write
files.  A caller supplies both the optional real-audio duration resolver and a
pure draft estimator; no language or character-set timing assumptions live
here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Protocol, TypeAlias, runtime_checkable

from .errors import PromoToolchainError
from .model import Chapter, Cue, ProjectConfig


TIMESTAMP_QUANTUM = Decimal("0.000001")
SecondsLike: TypeAlias = Decimal | int | float | str


class StoryboardError(PromoToolchainError):
    """The project cannot produce an internally consistent timeline."""


def _seconds(
    value: SecondsLike,
    context: str,
    *,
    allow_zero: bool,
) -> Decimal:
    if isinstance(value, bool):
        raise StoryboardError(f"{context} must be a finite number")
    try:
        result = Decimal(str(value)).quantize(
            TIMESTAMP_QUANTUM, rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError) as exc:
        raise StoryboardError(f"{context} must be a finite number") from exc
    if not result.is_finite() or result < 0 or (not allow_zero and result == 0):
        qualifier = "non-negative" if allow_zero else "greater than zero"
        raise StoryboardError(f"{context} must be finite and {qualifier}")
    return result


def _timestamp(value: Decimal) -> str:
    return f"{value:.6f}"


@dataclass(frozen=True)
class ResolvedNarrationDuration:
    """A duration read from an already-existing narration artifact."""

    seconds: Decimal
    artifact_id: str

    def __init__(self, seconds: SecondsLike, artifact_id: str) -> None:
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            raise StoryboardError("resolved narration artifact_id must be non-empty")
        object.__setattr__(
            self,
            "seconds",
            _seconds(seconds, "resolved narration duration", allow_zero=False),
        )
        object.__setattr__(self, "artifact_id", artifact_id.strip())


@runtime_checkable
class NarrationDurationResolver(Protocol):
    """Return a verified real-audio duration, or ``None`` when unavailable."""

    def __call__(
        self,
        project: ProjectConfig,
        chapter: Chapter,
        cue: Cue,
    ) -> ResolvedNarrationDuration | None: ...


@runtime_checkable
class DraftDurationEstimator(Protocol):
    """Pure caller/preset-owned fallback; all estimation parameters live here."""

    def __call__(
        self,
        project: ProjectConfig,
        chapter: Chapter,
        cue: Cue,
    ) -> SecondsLike: ...


@dataclass(frozen=True)
class TimelineSpacing:
    cue_gap_seconds: Decimal
    chapter_gap_seconds: Decimal

    def __init__(
        self,
        *,
        cue_gap_seconds: SecondsLike,
        chapter_gap_seconds: SecondsLike,
    ) -> None:
        object.__setattr__(
            self,
            "cue_gap_seconds",
            _seconds(cue_gap_seconds, "cue gap", allow_zero=True),
        )
        object.__setattr__(
            self,
            "chapter_gap_seconds",
            _seconds(chapter_gap_seconds, "chapter gap", allow_zero=True),
        )


@dataclass(frozen=True)
class CueTiming:
    index: int
    chapter_id: str
    cue_id: str
    start_seconds: Decimal
    end_seconds: Decimal
    duration_source: str
    narration_artifact_id: str | None

    @property
    def duration_seconds(self) -> Decimal:
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "index": self.index,
            "chapter_id": self.chapter_id,
            "cue_id": self.cue_id,
            "start_seconds": _timestamp(self.start_seconds),
            "end_seconds": _timestamp(self.end_seconds),
            "duration_seconds": _timestamp(self.duration_seconds),
            "duration_source": self.duration_source,
        }
        if self.narration_artifact_id is not None:
            result["narration_artifact_id"] = self.narration_artifact_id
        return result


@dataclass(frozen=True)
class ChapterTiming:
    index: int
    chapter_id: str
    start_seconds: Decimal
    end_seconds: Decimal
    cue_ids: tuple[str, ...]

    @property
    def duration_seconds(self) -> Decimal:
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "chapter_id": self.chapter_id,
            "start_seconds": _timestamp(self.start_seconds),
            "end_seconds": _timestamp(self.end_seconds),
            "duration_seconds": _timestamp(self.duration_seconds),
            "cue_ids": list(self.cue_ids),
        }


@dataclass(frozen=True)
class StoryboardTimeline:
    start_seconds: Decimal
    end_seconds: Decimal
    chapters: tuple[ChapterTiming, ...]
    cues: tuple[CueTiming, ...]

    @property
    def duration_seconds(self) -> Decimal:
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict[str, object]:
        return {
            "start_seconds": _timestamp(self.start_seconds),
            "end_seconds": _timestamp(self.end_seconds),
            "duration_seconds": _timestamp(self.duration_seconds),
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "cues": [cue.to_dict() for cue in self.cues],
        }


def _available_artifact_ids(values: Iterable[str]) -> frozenset[str]:
    rows = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in rows):
        raise StoryboardError("available artifact ids must be non-empty strings")
    normalized = tuple(value.strip() for value in rows)
    if len(normalized) != len(set(normalized)):
        raise StoryboardError("available artifact ids must be unique")
    return frozenset(normalized)


def _validate_artifact_references(
    project: ProjectConfig,
    available_artifact_ids: frozenset[str],
) -> None:
    for chapter in project.chapters:
        missing = sorted(set(chapter.artifact_ids) - available_artifact_ids)
        if missing:
            raise StoryboardError(
                f"chapter {chapter.chapter_id!r} references unavailable artifacts: "
                + ", ".join(missing)
            )


def _require_expected_start(
    actual: Decimal,
    expected: Decimal,
    context: str,
) -> None:
    if actual < expected:
        raise StoryboardError(f"{context} overlaps the preceding interval")
    if actual > expected:
        raise StoryboardError(f"{context} has an unexpected gap")


def validate_storyboard_timeline(
    timeline: StoryboardTimeline,
    *,
    spacing: TimelineSpacing,
    duration_limit_seconds: SecondsLike | None,
) -> None:
    """Validate exact spacing, positive intervals, bounds, order, and limit."""

    if not timeline.chapters or not timeline.cues:
        raise StoryboardError("timeline must contain at least one chapter and cue")
    start = _seconds(timeline.start_seconds, "timeline start", allow_zero=True)
    end = _seconds(timeline.end_seconds, "timeline end", allow_zero=True)
    if start != 0:
        raise StoryboardError("global timeline must start at zero")
    if end <= start:
        raise StoryboardError("global timeline duration must be greater than zero")

    cue_offset = 0
    chapter_cursor = start
    for chapter_index, chapter in enumerate(timeline.chapters):
        if chapter.index != chapter_index:
            raise StoryboardError("chapter indexes must be ordered and gap-free")
        if not chapter.cue_ids:
            raise StoryboardError(
                f"chapter {chapter.chapter_id!r} must contain at least one cue"
            )
        if chapter_index:
            chapter_cursor += spacing.chapter_gap_seconds
        chapter_start = _seconds(
            chapter.start_seconds,
            f"chapter {chapter.chapter_id!r} start",
            allow_zero=True,
        )
        chapter_end = _seconds(
            chapter.end_seconds,
            f"chapter {chapter.chapter_id!r} end",
            allow_zero=True,
        )
        _require_expected_start(
            chapter_start,
            chapter_cursor,
            f"chapter {chapter.chapter_id!r}",
        )

        cue_cursor = chapter_start
        chapter_cues = timeline.cues[
            cue_offset : cue_offset + len(chapter.cue_ids)
        ]
        if tuple(cue.cue_id for cue in chapter_cues) != chapter.cue_ids:
            raise StoryboardError(
                f"chapter {chapter.chapter_id!r} cue references do not match "
                "the global cue timeline"
            )
        for local_index, cue in enumerate(chapter_cues):
            if cue.index != cue_offset + local_index:
                raise StoryboardError("cue indexes must be ordered and gap-free")
            if cue.chapter_id != chapter.chapter_id:
                raise StoryboardError(
                    f"cue {cue.cue_id!r} is assigned to the wrong chapter"
                )
            if local_index:
                cue_cursor += spacing.cue_gap_seconds
            cue_start = _seconds(
                cue.start_seconds,
                f"cue {cue.cue_id!r} start",
                allow_zero=True,
            )
            cue_end = _seconds(
                cue.end_seconds,
                f"cue {cue.cue_id!r} end",
                allow_zero=True,
            )
            _require_expected_start(
                cue_start,
                cue_cursor,
                f"cue {cue.cue_id!r}",
            )
            if cue_end <= cue_start:
                raise StoryboardError(
                    f"cue {cue.cue_id!r} duration must be greater than zero"
                )
            cue_cursor = cue_end

        if chapter_end <= chapter_start:
            raise StoryboardError(
                f"chapter {chapter.chapter_id!r} duration must be greater than zero"
            )
        _require_expected_start(
            chapter_end,
            cue_cursor,
            f"chapter {chapter.chapter_id!r} end",
        )
        chapter_cursor = chapter_end
        cue_offset += len(chapter.cue_ids)

    if cue_offset != len(timeline.cues):
        raise StoryboardError("global cue timeline contains unreferenced cues")
    _require_expected_start(end, chapter_cursor, "global timeline end")
    duration = end - start
    if duration_limit_seconds is not None:
        limit = _seconds(
            duration_limit_seconds,
            "duration limit",
            allow_zero=False,
        )
        if duration >= limit:
            raise StoryboardError(
                "global timeline duration must be strictly below the configured "
                f"limit ({_timestamp(duration)} >= {_timestamp(limit)})"
            )


def plan_storyboard(
    project: ProjectConfig,
    *,
    narration_duration_resolver: NarrationDurationResolver | None,
    draft_estimator: DraftDurationEstimator,
    spacing: TimelineSpacing,
    available_artifact_ids: Iterable[str] = (),
    validate_only: bool = False,
) -> StoryboardTimeline:
    """Plan a deterministic timeline without producing or changing artifacts.

    Normal planning asks the resolver for an existing narration artifact first
    and falls back to the caller-owned estimator.  ``validate_only`` skips the
    resolver entirely so validation cannot trigger audio probing or production.
    """

    if not isinstance(project, ProjectConfig):
        raise StoryboardError("project must be a ProjectConfig")
    project = ProjectConfig.from_mapping(project.to_dict())
    if not project.chapters:
        raise StoryboardError("project must contain at least one chapter")
    available = _available_artifact_ids(available_artifact_ids)
    _validate_artifact_references(project, available)

    cursor = Decimal("0.000000")
    cue_rows: list[CueTiming] = []
    chapter_rows: list[ChapterTiming] = []
    for chapter_index, chapter in enumerate(project.chapters):
        if not chapter.cues:
            raise StoryboardError(
                f"chapter {chapter.chapter_id!r} must contain at least one cue"
            )
        if chapter_index:
            cursor += spacing.chapter_gap_seconds
        chapter_start = cursor
        cue_ids: list[str] = []
        for local_index, cue in enumerate(chapter.cues):
            if local_index:
                cursor += spacing.cue_gap_seconds
            resolved = None
            if not validate_only and narration_duration_resolver is not None:
                resolved = narration_duration_resolver(project, chapter, cue)
                if resolved is not None and not isinstance(
                    resolved, ResolvedNarrationDuration
                ):
                    raise StoryboardError(
                        "narration duration resolver must return "
                        "ResolvedNarrationDuration or None"
                    )
            if resolved is None:
                duration = _seconds(
                    draft_estimator(project, chapter, cue),
                    f"draft duration for cue {cue.cue_id!r}",
                    allow_zero=False,
                )
                duration_source = "draft-estimate"
                narration_artifact_id = None
            else:
                narration_artifact_id = resolved.artifact_id
                if narration_artifact_id not in chapter.artifact_ids:
                    raise StoryboardError(
                        f"resolved narration artifact {narration_artifact_id!r} "
                        f"is not declared by chapter {chapter.chapter_id!r}"
                    )
                if narration_artifact_id not in available:
                    raise StoryboardError(
                        f"resolved narration artifact {narration_artifact_id!r} "
                        "is unavailable"
                    )
                duration = resolved.seconds
                duration_source = "resolved-narration"
            cue_start = cursor
            cursor += duration
            cue_rows.append(
                CueTiming(
                    index=len(cue_rows),
                    chapter_id=chapter.chapter_id,
                    cue_id=cue.cue_id,
                    start_seconds=cue_start,
                    end_seconds=cursor,
                    duration_source=duration_source,
                    narration_artifact_id=narration_artifact_id,
                )
            )
            cue_ids.append(cue.cue_id)
        chapter_rows.append(
            ChapterTiming(
                index=chapter_index,
                chapter_id=chapter.chapter_id,
                start_seconds=chapter_start,
                end_seconds=cursor,
                cue_ids=tuple(cue_ids),
            )
        )

    timeline = StoryboardTimeline(
        start_seconds=Decimal("0.000000"),
        end_seconds=cursor,
        chapters=tuple(chapter_rows),
        cues=tuple(cue_rows),
    )
    validate_storyboard_timeline(
        timeline,
        spacing=spacing,
        duration_limit_seconds=project.duration_limit_seconds,
    )
    return timeline


__all__ = [
    "ChapterTiming",
    "CueTiming",
    "DraftDurationEstimator",
    "NarrationDurationResolver",
    "ResolvedNarrationDuration",
    "SecondsLike",
    "StoryboardError",
    "StoryboardTimeline",
    "TimelineSpacing",
    "plan_storyboard",
    "validate_storyboard_timeline",
]
