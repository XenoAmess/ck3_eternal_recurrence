#!/usr/bin/env python3
"""Build or validate the ZhongGuo 361 phase-two promo candidate.

This entry point is intentionally project-specific.  It resolves the reusable
``xar_promo`` registry/pipeline with the CK3 capture adapter and the ZhongGuo
phase-two preset, while keeping voice, sequel scope, real-character provenance,
and clean-capture policy out of the generic package.

``--validate-only`` is read-only.  A full build consumes an already-populated,
content-addressed Edge TTS cache, probes the real narration durations, and
retains the complete attempt.  It never invokes OCR or silently synthesizes
missing narration.  Rendering a candidate is not a release approval: missing
phase-two live claims or a byte-bound human sign-off remains RED.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SOURCE = REPOSITORY_ROOT / "xar_promo_toolchain" / "src"
if str(PACKAGE_SOURCE) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SOURCE))

from xar_promo.errors import ArtifactError, ManifestError, PromoToolchainError  # noqa: E402
from xar_promo.layout import FontSpec, SafeArea, WrapPolicy  # noqa: E402
from xar_promo.media import probe_media, require_streams  # noqa: E402
from xar_promo.operations import preserve_artifact, start_run  # noqa: E402
from xar_promo.pipeline import (  # noqa: E402
    PipelineDependencies,
    PipelineDraft,
    PipelineInvocation,
    PipelineResult,
    SegmentDraft,
    run_invocation,
)
from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    ADAPTER_ID,
    CAPTURE_CHAPTER_KIND,
    GENERATED_CHAPTER_KIND,
    PHASE2_POLICY,
    PRESET_ID,
    Phase2CaptureCandidate,
    build_narration_request,
    load_phase2_capture_candidate,
    load_phase2_project_config,
    validate_phase2_project_config,
    validate_rendered_duration,
)
from xar_promo.process import CommandResult, run_command  # noqa: E402
from xar_promo.project import load_document, sha256_file, validate_profile  # noqa: E402
from xar_promo.registry import ComponentRegistry  # noqa: E402
from xar_promo.render import RenderOptions  # noqa: E402
from xar_promo.sources import (  # noqa: E402
    GENERATED_CARD,
    VIDEO,
    VisualProbeResult,
    VisualSource,
)
from xar_promo.storyboard import (  # noqa: E402
    ResolvedNarrationDuration,
    TimelineSpacing,
    plan_storyboard,
)
from xar_promo.subtitles import (  # noqa: E402
    AssCue,
    AssDocumentConfig,
    AssStyleConfig,
    SubtitleTrackConfig,
    render_ass_document,
)
from xar_promo.tts import ProviderIdentity, TtsCache  # noqa: E402
from xar_promo.visuals import (  # noqa: E402
    BackgroundSpec,
    Box,
    CanvasSpec,
    LayerGroup,
    Palette,
    PillowFont,
    TextElement,
    TextStyle,
    TitleCardSpec,
    render_title_card,
)


DEFAULT_PROJECT_CONFIG = (
    REPOSITORY_ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
)
DEFAULT_EDGE_TTS_VERSION = "7.2.8"
DELIVERABLE_ARTIFACT_ID = "zhongguo-361-phase2-video"
DELIVERABLE_RELATIVE_PATH = Path("deliverable/zhongguo-361-phase2.mp4")
WIDTH = 1920
HEIGHT = 1080
FPS = 30
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class Phase2PromoBuildError(PromoToolchainError):
    """The project-specific entry cannot honestly produce the requested state."""


@dataclass(frozen=True, slots=True)
class Phase2BuildOutcome:
    result: PipelineResult
    candidate: Phase2CaptureCandidate
    release_ready: bool
    blockers: tuple[str, ...]
    run_manifest_path: Path | None


def _portable_id(value: str, *, prefix: str = "") -> str:
    candidate = f"{prefix}{value}"
    if _IDENTIFIER.fullmatch(candidate) is not None:
        return candidate
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:16]
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", candidate).strip("._-")[:100]
    result = f"{stem or 'item'}-{digest}"
    if _IDENTIFIER.fullmatch(result) is None:
        raise Phase2PromoBuildError(f"could not derive a portable id from {value!r}")
    return result


def _segment_id(chapter_id: str, cue_id: str) -> str:
    raw = f"{chapter_id}.{cue_id}"
    if len(raw) <= 96 and _IDENTIFIER.fullmatch(raw) is not None:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", raw).strip("._-")[:72]
    result = f"{stem or 'segment'}-{digest}"
    if len(result) > 96 or _IDENTIFIER.fullmatch(result) is None:
        raise Phase2PromoBuildError(
            f"could not derive a bounded segment id from {chapter_id!r}/{cue_id!r}"
        )
    return result


def _narration_artifact_id(chapter_id: str, cue_id: str) -> str:
    # This is exactly the generic pipeline's narration artifact id for the
    # segment, so a candidate run can preserve every config-declared input.
    return f"narration.{_segment_id(chapter_id, cue_id)}"


def _phase2_preset_factory(config):
    return validate_phase2_project_config(config)


def _phase2_ck3_adapter_factory(config, artifact_root: Path):
    # The preset's public loader calls the reusable CK3 adapter and then applies
    # only this project's provenance/clean-UI attestations to the verified bundle.
    return load_phase2_capture_candidate(config, artifact_root)


def _registry() -> ComponentRegistry:
    return ComponentRegistry(
        adapters=((ADAPTER_ID, _phase2_ck3_adapter_factory),),
        presets=((PRESET_ID, _phase2_preset_factory),),
        discover_entry_points=False,
    )


def _require_ready_authoring(config) -> None:
    planned = [chapter.chapter_id for chapter in config.chapters if chapter.state != "ready"]
    if planned:
        raise Phase2PromoBuildError(
            "phase-two project remains planned; no footage or release claim may be made: "
            + ", ".join(planned)
        )
    empty = [chapter.chapter_id for chapter in config.chapters if not chapter.cues]
    if empty:
        raise Phase2PromoBuildError(
            "ready phase-two chapters need authored narration/subtitle cues: "
            + ", ".join(empty)
        )
    cue_ids = [cue.cue_id for chapter in config.chapters for cue in chapter.cues]
    if len(cue_ids) != len(set(cue_ids)):
        raise Phase2PromoBuildError(
            "phase-two cue ids must be globally unique for narration/artifact binding"
        )


def _draft_duration(_project, _chapter, cue) -> Decimal:
    # Authoring-only estimate.  A full build replaces this with ffprobe-observed
    # cache audio through Storyboard's narration-duration resolver.
    text = cue.narration[PHASE2_POLICY.narration_locale]
    visible = sum(not character.isspace() for character in text)
    return Decimal(str(max(2.5, 0.8 + visible / 4.2)))


class _VisualProbe:
    def __init__(self, ffprobe: str, workdir: Path, command_runner: Callable[..., CommandResult]):
        self.ffprobe = ffprobe
        self.workdir = workdir
        self.command_runner = command_runner
        self.sequence = 0

    def __call__(self, path: Path) -> VisualProbeResult:
        self.sequence += 1
        inspected = require_streams(
            probe_media(
                self.ffprobe,
                path,
                audit_directory=self.workdir
                / "audit"
                / "visual-probe"
                / f"probe-{self.sequence:04d}",
                command_runner=self.command_runner,
            ),
            video=True,
        )
        stream = inspected.video_streams[0]
        if stream.width is None or stream.height is None:
            raise Phase2PromoBuildError(f"visual probe lacks dimensions: {path}")
        media_type = mimetypes.guess_type(path.name)[0]
        if media_type is None or not media_type.startswith(("image/", "video/")):
            media_type = "image/png" if stream.codec_name == "png" else "video/mp4"
        return VisualProbeResult(media_type, stream.width, stream.height)


class _GeneratedCardResolver:
    def __init__(self, zh_font_file: Path, en_font_file: Path):
        self.zh_font_file = zh_font_file
        self.en_font_file = en_font_file

    @staticmethod
    def _font(path: Path, *, key: str, family: str, size: int, weight: int) -> PillowFont:
        if not path.is_file():
            raise Phase2PromoBuildError(f"required generated-card font is missing: {path}")
        try:
            from PIL import ImageFont
        except ImportError as exc:
            raise Phase2PromoBuildError(
                "Pillow is required for generated phase-two cards"
            ) from exc
        try:
            handle = ImageFont.truetype(str(path), size=size)
        except OSError as exc:
            raise Phase2PromoBuildError(f"could not load generated-card font {path}: {exc}") from exc
        return PillowFont(FontSpec(key, family, size, weight), handle)

    def __call__(self, source: VisualSource, *, workdir: Path) -> Path:
        if source.kind != GENERATED_CARD or not source.requires_resolution:
            raise Phase2PromoBuildError(
                f"generated-card resolver rejected source {source.source_id!r}"
            )
        output = (workdir / source.path).resolve() if not source.path.is_absolute() else source.path.resolve()
        if output.exists():
            raise Phase2PromoBuildError(f"refusing to overwrite generated card: {output}")
        metadata = source.metadata
        zh_title = metadata.get("zh_title")
        en_title = metadata.get("en_title")
        if not isinstance(zh_title, str) or not zh_title.strip():
            raise Phase2PromoBuildError("generated card lacks zh_title metadata")
        if not isinstance(en_title, str) or not en_title.strip():
            raise Phase2PromoBuildError("generated card lacks en_title metadata")

        fonts = {
            "zh-title": self._font(
                self.zh_font_file,
                key="zh-title",
                family="Microsoft YaHei UI",
                size=72,
                weight=700,
            ),
            "en-title": self._font(
                self.en_font_file,
                key="en-title",
                family="Segoe UI",
                size=40,
                weight=600,
            ),
            "label": self._font(
                self.zh_font_file,
                key="label",
                family="Microsoft YaHei UI",
                size=28,
                weight=600,
            ),
        }
        palette = Palette(
            {
                "background-top": (16, 20, 31, 255),
                "background-bottom": (41, 19, 25, 255),
                "primary": (248, 238, 215, 255),
                "secondary": (204, 214, 230, 255),
                "accent": (244, 178, 76, 255),
            }
        )
        canvas = CanvasSpec(
            WIDTH,
            HEIGHT,
            SafeArea.from_margins(
                frame_width=WIDTH,
                frame_height=HEIGHT,
                left=96,
                top=80,
                right=96,
                bottom=80,
            ),
            palette,
            BackgroundSpec("gradient", "background-top", "background-bottom"),
        )
        punctuation = WrapPolicy(
            force_break_after=frozenset({"。", "！", "？"}),
            prefer_break_after=frozenset({"，", "；", ":", ",", ";"}),
            decimal_separators=frozenset({".", "。"}),
        )
        spec = TitleCardSpec(
            canvas=canvas,
            layers=LayerGroup(
                texts=(
                    TextElement(
                        "二期新增 · PHASE 2 INCREMENTS",
                        Box(120, 100, 1800, 170),
                        TextStyle("label", "accent", 42, 1, alignment="center"),
                    ),
                    TextElement(
                        zh_title,
                        Box(150, 270, 1770, 540),
                        TextStyle(
                            "zh-title",
                            "primary",
                            92,
                            3,
                            alignment="center",
                            vertical_alignment="center",
                            wrap_policy=punctuation,
                        ),
                    ),
                    TextElement(
                        en_title,
                        Box(190, 590, 1730, 800),
                        TextStyle(
                            "en-title",
                            "secondary",
                            54,
                            3,
                            alignment="center",
                            vertical_alignment="center",
                        ),
                    ),
                    TextElement(
                        "默认观众已看过一期 · ONLY NEW PHASE-TWO SYSTEMS",
                        Box(180, 890, 1740, 950),
                        TextStyle("label", "accent", 42, 1, alignment="center"),
                    ),
                )
            ),
        )
        payload = render_title_card(spec, fonts=fonts, assets={})
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise Phase2PromoBuildError(f"refusing to overwrite generated card: {output}") from exc
        return output


class _SubtitleRenderer:
    ZH_FONT = "Microsoft YaHei UI"
    EN_FONT = "Segoe UI"

    def __call__(self, segment: SegmentDraft, _narration, *, workdir: Path) -> str:
        del workdir
        if set(segment.subtitles) != set(PHASE2_POLICY.subtitle_locales):
            raise Phase2PromoBuildError(
                f"segment {segment.segment_id!r} lacks exact zh-CN/en subtitles"
            )
        duration = segment.render_options.duration_seconds
        tracks = (
            SubtitleTrackConfig(
                "zh-CN",
                "zh-CN",
                1,
                AssStyleConfig(
                    "ChinesePrimary",
                    self.ZH_FONT,
                    46,
                    outline=3,
                    shadow=1,
                    alignment=2,
                    margin_left=90,
                    margin_right=90,
                    margin_vertical=142,
                ),
            ),
            SubtitleTrackConfig(
                "en",
                "en",
                0,
                AssStyleConfig(
                    "EnglishSecondary",
                    self.EN_FONT,
                    30,
                    outline=2,
                    shadow=1,
                    alignment=2,
                    margin_left=110,
                    margin_right=110,
                    margin_vertical=64,
                ),
            ),
        )
        cues = tuple(
            AssCue(
                f"{locale}-line",
                locale,
                0,
                duration,
                segment.subtitles[locale],
            )
            for locale in PHASE2_POLICY.subtitle_locales
        )
        return render_ass_document(
            AssDocumentConfig(
                f"ZhongGuo phase two {segment.segment_id}",
                WIDTH,
                HEIGHT,
                duration_seconds=duration,
            ),
            tracks,
            cues,
            available_font_names={self.ZH_FONT, self.EN_FONT},
        )


def _validation_narration_resolver(segment: SegmentDraft, *, workdir: Path):
    del segment, workdir
    raise Phase2PromoBuildError("validation-only narration resolver must never execute")


class Phase2ProjectComposer:
    """Project-owned implementation of the frozen ``PipelineComposer`` seam."""

    def __init__(
        self,
        *,
        capture_root: Path,
        tts_cache_root: Path | None,
        edge_tts_version: str,
        ffmpeg: str,
        ffprobe: str,
        zh_font_file: Path,
        en_font_file: Path,
        command_runner: Callable[..., CommandResult] = run_command,
    ) -> None:
        self.capture_root = capture_root.expanduser().resolve()
        self.tts_cache_root = (
            None if tts_cache_root is None else tts_cache_root.expanduser().resolve()
        )
        self.edge_tts_version = edge_tts_version
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.zh_font_file = zh_font_file.expanduser().resolve()
        self.en_font_file = en_font_file.expanduser().resolve()
        self.command_runner = command_runner
        self.capture_candidate: Phase2CaptureCandidate | None = None
        self.real_narration_durations = False
        self.composed_config = None
        self.final_duration_seconds: float | None = None

    def _cached_narration(self, config, workdir: Path):
        if self.tts_cache_root is None:
            raise Phase2PromoBuildError(
                "full build requires --tts-cache with pre-generated Xiaoxiao narration"
            )
        identity = ProviderIdentity("edge-tts", self.edge_tts_version)
        cache = TtsCache(self.tts_cache_root)
        entries = {}
        durations = {}
        for chapter in config.chapters:
            for cue in chapter.cues:
                artifact_id = _narration_artifact_id(
                    chapter.chapter_id,
                    cue.cue_id,
                )
                if artifact_id not in chapter.artifact_ids:
                    raise Phase2PromoBuildError(
                        f"chapter {chapter.chapter_id!r} must declare cached narration "
                        f"artifact id {artifact_id!r}"
                    )
                request = build_narration_request(
                    cue.narration[PHASE2_POLICY.narration_locale]
                )
                try:
                    entry = cache.validate_cached(request, identity)
                except Exception as exc:
                    raise Phase2PromoBuildError(
                        f"missing or invalid offline narration cache for cue {cue.cue_id!r}: {exc}"
                    ) from exc
                segment_id = _segment_id(chapter.chapter_id, cue.cue_id)
                inspected = require_streams(
                    probe_media(
                        self.ffprobe,
                        entry.media_path,
                        audit_directory=workdir
                        / "audit"
                        / "narration-probe"
                        / segment_id,
                        command_runner=self.command_runner,
                    ),
                    audio=True,
                )
                duration = inspected.require_duration()
                key = (chapter.chapter_id, cue.cue_id)
                entries[key] = entry
                durations[key] = (duration, artifact_id)
        return entries, durations

    def __call__(
        self,
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
        del run, config_path, run_path
        config = preset_factory(config)
        self.composed_config = config
        candidate = adapter_factory(config, self.capture_root)
        if not isinstance(candidate, Phase2CaptureCandidate):
            raise Phase2PromoBuildError(
                "phase-two CK3 adapter must return Phase2CaptureCandidate"
            )
        self.capture_candidate = candidate

        entries: Mapping[tuple[str, str], object] = {}
        durations: Mapping[tuple[str, str], tuple[float, str]] = {}
        if not validate_only:
            entries, durations = self._cached_narration(config, workdir)

        def duration_resolver(_project, chapter, cue):
            value = durations.get((chapter.chapter_id, cue.cue_id))
            if value is None:
                return None
            seconds, artifact_id = value
            return ResolvedNarrationDuration(seconds, artifact_id)

        timeline = plan_storyboard(
            config,
            narration_duration_resolver=duration_resolver,
            draft_estimator=_draft_duration,
            spacing=TimelineSpacing(cue_gap_seconds=0, chapter_gap_seconds=0),
            available_artifact_ids=(
                artifact_id
                for chapter in config.chapters
                for artifact_id in chapter.artifact_ids
            ),
            validate_only=validate_only,
        )
        timing_by_cue = {
            (row.chapter_id, row.cue_id): row for row in timeline.cues
        }
        chapter_timing = {row.chapter_id: row for row in timeline.chapters}
        self.real_narration_durations = bool(timeline.cues) and all(
            row.duration_source == "resolved-narration" for row in timeline.cues
        )

        segments: list[SegmentDraft] = []
        for chapter in config.chapters:
            span = (
                candidate.bundle.clean_span(chapter.chapter_id)
                if chapter.kind == CAPTURE_CHAPTER_KIND
                else None
            )
            chapter_row = chapter_timing[chapter.chapter_id]
            if span is not None and float(chapter_row.duration_seconds) > span.duration_seconds:
                raise Phase2PromoBuildError(
                    f"chapter {chapter.chapter_id!r} narration needs "
                    f"{float(chapter_row.duration_seconds):.3f}s but clean span has "
                    f"{span.duration_seconds:.3f}s"
                )
            for cue in chapter.cues:
                key = (chapter.chapter_id, cue.cue_id)
                timing = timing_by_cue[key]
                segment_id = _segment_id(chapter.chapter_id, cue.cue_id)
                if chapter.kind == CAPTURE_CHAPTER_KIND:
                    if span is None:
                        raise Phase2PromoBuildError(
                            f"capture chapter {chapter.chapter_id!r} lacks its clean span"
                        )
                    relative_start = float(timing.start_seconds - chapter_row.start_seconds)
                    visual = VisualSource(
                        _portable_id(segment_id, prefix="capture."),
                        VIDEO,
                        candidate.bundle.raw_capture.path,
                        "ck3-capture-bundle",
                        metadata={
                            "clean_span_id": span.span_id,
                            "begin_mark": span.begin_mark,
                            "end_mark": span.end_mark,
                            "capture_sha256": candidate.bundle.raw_capture.sha256,
                        },
                    )
                    start_seconds = span.begin_seconds + relative_start
                elif chapter.kind == GENERATED_CHAPTER_KIND:
                    visual = VisualSource(
                        _portable_id(segment_id, prefix="card."),
                        GENERATED_CARD,
                        Path("visuals") / f"{segment_id}.png",
                        "zhongguo-phase2-card",
                        requires_resolution=True,
                        metadata={
                            "chapter_id": chapter.chapter_id,
                            "zh_title": chapter.title["zh-CN"],
                            "en_title": chapter.title["en"],
                        },
                    )
                    start_seconds = 0.0
                else:  # Defensive even though the preset already rejects this.
                    raise Phase2PromoBuildError(
                        f"unsupported phase-two chapter type: {chapter.kind}"
                    )
                entry = entries.get(key)
                segments.append(
                    SegmentDraft(
                        segment_id=segment_id,
                        visual_source=visual,
                        render_options=RenderOptions(
                            width=WIDTH,
                            height=HEIGHT,
                            fps=FPS,
                            duration_seconds=float(timing.duration_seconds),
                            crf=18,
                            preset="medium",
                        ),
                        subtitles=cue.subtitles,
                        narration_request=build_narration_request(
                            cue.narration[PHASE2_POLICY.narration_locale]
                        ),
                        prepared_narration=(
                            None if entry is None else entry.media_path  # type: ignore[attr-defined]
                        ),
                        start_seconds=start_seconds,
                    )
                )

        dependencies = PipelineDependencies(
            ffmpeg=self.ffmpeg,
            subtitle_renderer=_SubtitleRenderer(),
            command_runner=self.command_runner,
            visual_probe=_VisualProbe(self.ffprobe, workdir, self.command_runner),
            visual_resolver=_GeneratedCardResolver(
                self.zh_font_file,
                self.en_font_file,
            ),
            narration_resolver=(
                _validation_narration_resolver if validate_only else None
            ),
        )
        return PipelineInvocation(
            PipelineDraft(
                config=config,
                segments=tuple(segments),
                deliverable_relative_path=DELIVERABLE_RELATIVE_PATH,
                deliverable_artifact_id=DELIVERABLE_ARTIFACT_ID,
                deliverable_media_type="video/mp4",
            ),
            dependencies,
            workdir,
        )

    def verify_final_deliverable(self, result: PipelineResult) -> float:
        """Probe exact rendered bytes and apply the preset's strict duration gate."""

        if self.composed_config is None:
            raise Phase2PromoBuildError("phase-two composer has no bound project config")
        if result.audit_record is None:
            raise Phase2PromoBuildError("successful pipeline lacks an exact deliverable")
        deliverable = result.audit_record.deliverable
        inspected = require_streams(
            probe_media(
                self.ffprobe,
                deliverable.path,
                audit_directory=result.workdir / "audit" / "final-deliverable-probe",
                command_runner=self.command_runner,
            ),
            video=True,
            audio=True,
        )
        observed_duration = inspected.require_duration()
        self.final_duration_seconds = float(observed_duration)
        return validate_rendered_duration(
            observed_duration,
            self.composed_config,
        )


def _result_mapping(
    result: PipelineResult,
    *,
    final_duration_seconds: float | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-pipeline-attempt",
        "status": result.status,
        "validate_only": result.validate_only,
        "signoff_recorded": result.signoff_recorded,
        "workdir": str(result.workdir),
        "phases": [phase.to_mapping() for phase in result.phases],
        "artifacts": [artifact.to_audit_mapping() for artifact in result.artifacts],
        "audit_record": (
            None if result.audit_record is None else result.audit_record.to_mapping()
        ),
    }
    if result.failure is not None:
        value["failure"] = {
            "phase": result.failure.phase,
            "exception_type": result.failure.exception_type,
            "message": result.failure.message,
            "stdout_paths": [str(path) for path in result.failure.stdout_paths],
            "stderr_paths": [str(path) for path in result.failure.stderr_paths],
            "partial_paths": [str(path) for path in result.failure.partial_paths],
            "retained_paths": [str(path) for path in result.failure.retained_paths],
        }
    if final_duration_seconds is not None:
        value["final_duration_gate"] = {
            "source": "exact-deliverable-ffprobe",
            "observed_seconds": final_duration_seconds,
            "exclusive_limit_seconds": PHASE2_POLICY.duration_limit_seconds_exclusive,
            "status": (
                "GREEN"
                if 0 < final_duration_seconds
                < PHASE2_POLICY.duration_limit_seconds_exclusive
                else "RED"
            ),
        }
    return value


def _write_new_json(path: Path, value: Mapping[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise Phase2PromoBuildError(f"refusing to overwrite process material: {path}") from exc
    return path


def _write_entry_failure(workdir: Path, phase: str, error: Exception) -> Path:
    return _write_new_json(
        workdir / "phase2-entry-failure.json",
        {
            "schema_version": 1,
            "kind": "zhongguo-361-phase2-entry-failure",
            "status": "RED",
            "phase": phase,
            "exception_type": type(error).__name__,
            "message": str(error),
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
        },
    )


def _persist_candidate_run(config_path: Path, result: PipelineResult, run_id: str) -> Path:
    if result.audit_record is None:
        raise Phase2PromoBuildError("successful build lacks a byte-bound deliverable record")
    run_path = start_run(
        config_path,
        run_id=run_id,
        run_directory=result.workdir / "candidate-run",
    )
    config = load_phase2_project_config(config_path)
    required_ids = {
        artifact_id
        for chapter in config.chapters
        for artifact_id in chapter.artifact_ids
    }
    selected = {
        artifact.artifact_id: artifact
        for artifact in result.artifacts
        if artifact.artifact_id in required_ids or artifact.role == "deliverable"
    }
    missing = sorted(required_ids - set(selected))
    if missing:
        raise Phase2PromoBuildError(
            "pipeline result lacks config-declared candidate artifacts: "
            + ", ".join(missing)
        )
    deliverable = result.audit_record.deliverable
    selected[deliverable.artifact_id] = deliverable
    for artifact in selected.values():
        preserve_artifact(
            run_path,
            artifact.path,
            artifact_id=artifact.artifact_id,
            collection="derived",
            role=artifact.role,
            label=(
                "ZhongGuo 361 phase-two unreviewed promo candidate"
                if artifact.role == "deliverable"
                else artifact.path.name
            ),
            media_type=artifact.media_type,
        )
    return run_path


def _approved_deliverable(
    run_manifest_path: Path | None,
    *,
    config_path: Path,
    result: PipelineResult,
) -> bool:
    if run_manifest_path is None:
        return False
    loaded = load_document(run_manifest_path, check_files=True)
    validate_profile(loaded, "release")
    if loaded.run is None:
        return False
    if (
        loaded.run.project_config.bytes != config_path.stat().st_size
        or loaded.run.project_config.sha256 != sha256_file(config_path)
    ):
        raise Phase2PromoBuildError(
            "signed run is not bound to the exact phase-two project config bytes"
        )
    latest_by_artifact = {
        signoff.artifact_id: signoff for signoff in loaded.run.signoffs
    }
    if result.audit_record is None:
        return any(
            artifact.role == "deliverable"
            and artifact.artifact_id in latest_by_artifact
            and latest_by_artifact[artifact.artifact_id].decision == "approved"
            for artifact in loaded.run.artifacts
        )
    subject = result.audit_record.deliverable
    target = next(
        (
            artifact
            for artifact in loaded.run.artifacts
            if artifact.artifact_id == subject.artifact_id
            and artifact.role == "deliverable"
        ),
        None,
    )
    latest = latest_by_artifact.get(subject.artifact_id)
    return bool(
        target is not None
        and latest is not None
        and latest.decision == "approved"
        and (target.bytes, target.sha256) == (subject.bytes, subject.sha256)
    )


def execute(
    args: argparse.Namespace,
    *,
    registry: ComponentRegistry | None = None,
    composer_factory=None,
    pipeline_runner=None,
) -> Phase2BuildOutcome:
    config_path = args.project_config.expanduser().resolve()
    capture_root = args.capture_root.expanduser().resolve()
    workdir = args.work_dir.expanduser().resolve()
    if not args.validate_only and workdir.exists():
        raise Phase2PromoBuildError(
            f"full build requires a new attempt directory; retain the existing one: {workdir}"
        )

    failure_phase = "entry-preflight"
    final_duration_seconds: float | None = None
    try:
        config = load_phase2_project_config(config_path)
        _require_ready_authoring(config)
        selected_registry = _registry() if registry is None else registry
        adapter_factory = selected_registry.resolve_adapter(config.adapter)
        preset_factory = selected_registry.resolve_preset(config.preset)
        factory = Phase2ProjectComposer if composer_factory is None else composer_factory
        composer = factory(
            capture_root=capture_root,
            tts_cache_root=args.tts_cache,
            edge_tts_version=args.edge_tts_version,
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
            zh_font_file=args.zh_font_file,
            en_font_file=args.en_font_file,
        )
        invocation = composer(
            config,
            None,
            config_path=config_path,
            run_path=None,
            workdir=workdir,
            adapter_factory=adapter_factory,
            preset_factory=preset_factory,
            validate_only=args.validate_only,
        )
        candidate = composer.capture_candidate
        if candidate is None:
            raise Phase2PromoBuildError("phase-two composer did not retain its capture candidate")
        runner = run_invocation if pipeline_runner is None else pipeline_runner
        result = runner(
            invocation,
            validate_only=args.validate_only,
            offline_tts=True,
        )
        if not isinstance(result, PipelineResult):
            raise Phase2PromoBuildError("pipeline runner must return PipelineResult")
        if not args.validate_only and result.succeeded:
            failure_phase = "final-duration"
            try:
                final_duration_seconds = composer.verify_final_deliverable(result)
            except Exception:
                _write_new_json(
                    workdir / "phase2-pipeline-result.json",
                    _result_mapping(
                        result,
                        final_duration_seconds=getattr(
                            composer,
                            "final_duration_seconds",
                            None,
                        ),
                    ),
                )
                raise
    except Exception as exc:
        if not args.validate_only and not workdir.exists():
            _write_entry_failure(workdir, failure_phase, exc)
        elif not args.validate_only and workdir.is_dir():
            marker = workdir / "phase2-entry-failure.json"
            if not marker.exists():
                _write_entry_failure(workdir, failure_phase, exc)
        raise

    run_path: Path | None = None
    if not args.validate_only:
        _write_new_json(
            workdir / "phase2-pipeline-result.json",
            _result_mapping(
                result,
                final_duration_seconds=final_duration_seconds,
            ),
        )
        if result.succeeded:
            run_path = _persist_candidate_run(config_path, result, args.run_id)

    blockers: list[str] = []
    if not result.succeeded:
        detail = "pipeline failed"
        if result.failure is not None:
            detail = (
                f"pipeline {result.failure.phase} failed: "
                f"{result.failure.exception_type}: {result.failure.message}"
            )
        blockers.append(detail)
    if not composer.real_narration_durations:
        blockers.append(
            "storyboard uses authoring estimates; final render needs ffprobe-observed cached narration"
        )
    if not candidate.phase_two_runtime_claims_verified:
        blockers.append("phase-two project-specific live runtime claim matrix is not verified")
    try:
        human_approved = _approved_deliverable(
            args.signed_run_manifest,
            config_path=config_path,
            result=result,
        )
    except (ArtifactError, ManifestError) as exc:
        raise Phase2PromoBuildError(f"invalid signed run manifest: {exc}") from exc
    if not human_approved:
        blockers.append("exact rendered bytes lack an approved full-duration human sign-off")
    blockers.extend(candidate.blockers)
    blockers = list(dict.fromkeys(blockers))
    return Phase2BuildOutcome(
        result=result,
        candidate=candidate,
        release_ready=not blockers,
        blockers=tuple(blockers),
        run_manifest_path=run_path,
    )


def _default_font(name: str) -> Path:
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    return windows / "Fonts" / name


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--project-config",
        type=Path,
        default=DEFAULT_PROJECT_CONFIG,
        help="phase-two xar_promo ProjectConfig",
    )
    result.add_argument("--capture-root", type=Path, required=True)
    result.add_argument("--work-dir", type=Path, required=True)
    result.add_argument(
        "--tts-cache",
        type=Path,
        help="content-addressed xar_promo TTS cache; required for full build",
    )
    result.add_argument("--edge-tts-version", default=DEFAULT_EDGE_TTS_VERSION)
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    result.add_argument("--zh-font-file", type=Path, default=_default_font("msyh.ttc"))
    result.add_argument("--en-font-file", type=Path, default=_default_font("segoeui.ttf"))
    result.add_argument("--run-id", default="phase2-candidate")
    result.add_argument(
        "--signed-run-manifest",
        type=Path,
        help="optional existing run whose approved deliverable must match exact candidate bytes",
    )
    result.add_argument(
        "--validate-only",
        action="store_true",
        help="read-only config/capture/draft validation; no TTS, probes, directories, or media writes",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outcome = execute(args)
    except KeyboardInterrupt:
        print("RELEASE: RED\nERROR: interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"RELEASE: RED\nERROR: {exc}", file=sys.stderr)
        return 2

    label = "VALIDATION" if args.validate_only else "CANDIDATE BUILD"
    print(f"{label}: {'GREEN' if outcome.result.succeeded else 'RED'}")
    print(f"RELEASE: {'GREEN' if outcome.release_ready else 'RED'}")
    print(f"CAPTURE: {outcome.candidate.bundle.artifact_root}")
    print(f"WORK: {outcome.result.workdir}")
    if outcome.run_manifest_path is not None:
        print(f"UNREVIEWED RUN: {outcome.run_manifest_path}")
    for blocker in outcome.blockers:
        print(f"BLOCKER: {blocker}")
    return 0 if outcome.release_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
