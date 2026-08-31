"""Compatibility projections for the repository's pre-package video builders.

The generic modules intentionally enforce stricter input contracts than the two
legacy entry points.  These adapters use the generic implementation whenever it
is byte-compatible and retain the established legacy result for historical edge
cases.  Project-specific story, styling, cache paths, and release policy stay in
the legacy wrappers.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .errors import PromoToolchainError
from .model import new_project_config
from .pipeline import (
    PipelineDependencies,
    PipelineDraft,
    PipelineResult,
    SegmentDraft,
    run_pipeline,
)
from .render import RenderOptions, RenderPlanError, concat_manifest, seconds
from .sources import EVIDENCE_CARD, GENERATED_CARD, STILL, VIDEO, SourceKind, VisualSource
from .subtitles import SubtitleError, ass_escape, ass_timestamp


class LegacyCompatibilityError(PromoToolchainError):
    """A legacy projection cannot preserve its established observable result."""


@dataclass(frozen=True, slots=True)
class LegacyPipelineSegment:
    """Normalized legacy chapter inputs used by the read-only pipeline seam.

    Legacy builders remain responsible for their source checks, visual generation,
    narration cache, and exact render bytes.  This record carries only enough
    information to validate the equivalent generic pipeline shape.
    """

    segment_id: str
    visual_kind: str
    source_path: Path | None
    subtitle_tracks: Mapping[str, str]
    duration_seconds: float
    start_seconds: float = 0.0


_LEGACY_VISUAL_KINDS: dict[str, SourceKind] = {
    "video": VIDEO,
    "still": STILL,
    "generated-card": GENERATED_CARD,
    "evidence-card": EVIDENCE_CARD,
}


def _portable_identifier(value: str, sequence: int) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-")
    return f"legacy-{sequence:04d}-{(slug or 'segment')[:96]}"


def _unreachable_dependency(*_args: object, **_kwargs: object) -> object:
    raise LegacyCompatibilityError(
        "a read-only legacy pipeline projection invoked an effectful dependency"
    )


def validate_legacy_pipeline_projection(
    segments: Sequence[LegacyPipelineSegment],
    *,
    work_directory: Path,
    ffmpeg: str | Path,
    width: int,
    height: int,
    fps: int,
    crf: int,
    render_preset: str,
) -> PipelineResult:
    """Validate legacy orchestration through the generic pipeline without effects.

    Every visual is deliberately expressed as resolver-backed normalized media.
    The legacy entry points have already validated the real source bytes, while
    their adapters still own generated cards and source normalization.  Using a
    planned resolver output avoids adding stricter filename rules to their public
    CLI.  ``run_pipeline(validate_only=True)`` guarantees that none of the
    sentinels below can be called and that no attempt directory is created.
    """

    materialized = tuple(segments)
    if not materialized:
        raise LegacyCompatibilityError(
            "a legacy pipeline projection needs at least one segment"
        )

    subtitle_locales = sorted(
        {
            locale
            for item in materialized
            for locale in item.subtitle_tracks
            if isinstance(locale, str) and locale
        }
    )
    if not subtitle_locales:
        subtitle_locales = ["legacy-subtitle"]
    config = new_project_config(
        "legacy-promo",
        "Legacy promotional video",
        "legacy-narration",
        subtitle_locales,
        "legacy-adapter",
        "legacy-preset",
    )

    projected: list[SegmentDraft] = []
    for sequence, item in enumerate(materialized, start=1):
        kind = _LEGACY_VISUAL_KINDS.get(item.visual_kind)
        if kind is None:
            raise LegacyCompatibilityError(
                f"unsupported legacy visual kind: {item.visual_kind!r}"
            )
        segment_id = _portable_identifier(item.segment_id, sequence)
        suffix = ".mkv" if kind.media_family == "video" else ".png"
        metadata: dict[str, object] = {"legacy_visual_kind": item.visual_kind}
        if item.source_path is not None:
            metadata["legacy_source_path"] = str(Path(item.source_path).resolve())
        projected.append(
            SegmentDraft(
                segment_id=segment_id,
                visual_source=VisualSource(
                    source_id=f"visual-{sequence:04d}",
                    kind=kind,
                    path=Path("legacy-visuals") / f"{segment_id}{suffix}",
                    origin="legacy-adapter",
                    requires_resolution=True,
                    metadata=metadata,
                ),
                render_options=RenderOptions(
                    width=width,
                    height=height,
                    fps=fps,
                    duration_seconds=item.duration_seconds,
                    preset=render_preset or "legacy",
                    crf=crf,
                ),
                subtitles=dict(item.subtitle_tracks),
                start_seconds=item.start_seconds,
            )
        )

    draft = PipelineDraft(
        config=config,
        segments=tuple(projected),
        deliverable_relative_path=Path("deliverables") / "legacy-validation.mp4",
        deliverable_artifact_id="legacy-deliverable",
        deliverable_media_type="video/mp4",
    )
    # A fresh, uncreated child prevents an unrelated retained legacy cache from
    # colliding with pipeline-owned names.  Validation itself remains read-only.
    attempt = (
        Path(work_directory).expanduser().resolve()
        / f".xar-promo-readonly-{uuid.uuid4().hex}"
    )
    result = run_pipeline(
        draft,
        workdir=attempt,
        dependencies=PipelineDependencies(
            ffmpeg=ffmpeg or "ffmpeg",
            subtitle_renderer=_unreachable_dependency,
            command_runner=_unreachable_dependency,
            visual_probe=_unreachable_dependency,
            visual_resolver=_unreachable_dependency,
            narration_resolver=_unreachable_dependency,
        ),
        validate_only=True,
    )
    if not result.succeeded:
        failure = result.failure
        detail = "pipeline validation failed"
        if failure is not None:
            detail = f"{failure.phase}: {failure.exception_type}: {failure.message}"
        raise LegacyCompatibilityError(detail)
    return result


def compatible_ass_timestamp(value: float) -> str:
    """Use the generic formatter without changing legacy banker rounding/clamping."""

    centiseconds = max(0, int(round(value * 100)))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, fraction = divmod(remainder, 100)
    legacy = f"{hours}:{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"
    try:
        projected = ass_timestamp(value)
    except (SubtitleError, TypeError, ValueError):
        return legacy
    return projected if projected == legacy else legacy


def compatible_ass_escape(text: str) -> str:
    """Use generic ASS escaping while retaining legacy tab/control treatment."""

    legacy = (
        text.replace("\\", r"\\")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("\r\n", r"\N")
        .replace("\r", r"\N")
        .replace("\n", r"\N")
    )
    try:
        projected = ass_escape(text)
    except SubtitleError:
        return legacy
    return projected if projected == legacy else legacy


def compatible_seconds(value: float) -> str:
    """Use generic command-time formatting with the old invalid-value fallback."""

    legacy = f"{value:.6f}"
    try:
        projected = seconds(value)
    except (TypeError, ValueError):
        return legacy
    return projected if projected == legacy else legacy


def compatible_concat_manifest(
    segment_paths: Sequence[Path], *, build_directory: Path
) -> str:
    """Project the exact legacy relative concat list through the generic renderer."""

    materialized = tuple(Path(path) for path in segment_paths)
    rows: list[str] = []
    for path in materialized:
        relative = path.relative_to(build_directory).as_posix()
        if "'" in relative:
            raise LegacyCompatibilityError(
                f"concat path unexpectedly contains an apostrophe: {relative}"
            )
        rows.append(f"file '{relative}'")
    legacy = "\n".join(rows) + "\n"
    try:
        projected = concat_manifest(
            materialized,
            manifest_directory=build_directory,
        )
    except RenderPlanError:
        return legacy
    return projected if projected == legacy else legacy


__all__ = [
    "LegacyCompatibilityError",
    "LegacyPipelineSegment",
    "compatible_ass_escape",
    "compatible_ass_timestamp",
    "compatible_concat_manifest",
    "compatible_seconds",
    "validate_legacy_pipeline_projection",
]
