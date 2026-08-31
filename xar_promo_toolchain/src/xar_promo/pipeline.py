"""Dependency-injected orchestration for one promotional-video attempt.

The pipeline deliberately owns sequencing, not project policy.  A caller supplies
the exact narration requests (or already prepared narration), subtitle renderer,
media inputs, render options, executables, and process runner.  Consequently this
module contains no game, product, locale, voice, or editorial defaults.

Every full run is an attempt in a caller-selected work directory.  An exception
becomes a structured RED result; the pipeline never cleans that directory, removes
partial output, rewrites process audit files, or records a human sign-off.
"""

from __future__ import annotations

import hashlib
import math
import mimetypes
import os
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable

from .errors import PromoToolchainError
from .model import ProjectConfig, RunManifest, SourceRecord
from .process import CommandResult
from .registry import AdapterFactory, PresetFactory
from .render import (
    RenderOptions,
    RenderPlan,
    execute_render_plan,
    plan_concat,
    plan_render,
)
from .sources import (
    PreparedVisual,
    VisualProbe,
    VisualResolver,
    VisualSource,
    prepare_visual,
    validate_visual_source,
)
from .tts import TtsCacheEntry, TtsProvider, TtsRequest


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_PHASES = (
    "draft",
    "visual",
    "narration",
    "subtitle",
    "segment-plan",
    "segment-render",
    "concat",
    "audit-record-ready",
)


class PipelineError(PromoToolchainError):
    """Base class for pipeline validation and explicit failure escalation."""


class PipelineValidationError(PipelineError):
    """A draft or injected dependency cannot form a deterministic attempt."""


class PipelineExecutionError(PipelineError):
    """Raised only when a caller explicitly requires a non-RED result."""

    def __init__(self, result: "PipelineResult") -> None:
        self.result = result
        failure = result.failure
        detail = "pipeline did not complete"
        if failure is not None:
            detail = f"{failure.phase}: {failure.exception_type}: {failure.message}"
        super().__init__(detail)


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise PipelineValidationError(
            f"{label} must be a portable identifier of at most 128 characters"
        )
    return value


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise PipelineValidationError(f"{label} must be non-empty NUL-free text")
    return value


def _relative_output(value: Path, label: str) -> Path:
    path = Path(value)
    portable = PurePath(path)
    if path.is_absolute() or not portable.parts or any(
        part in {"", ".", ".."} for part in portable.parts
    ):
        raise PipelineValidationError(f"{label} must be a normalized relative path")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _media_type(path: Path, fallback: str = "application/octet-stream") -> str:
    return mimetypes.guess_type(path.name)[0] or fallback


@dataclass(frozen=True, slots=True)
class NarrationArtifact:
    """One prepared narration file returned by a resolver or the TTS cache."""

    path: Path
    media_type: str
    origin: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        _required_text(self.media_type, "narration media_type")
        _identifier(self.origin, "narration origin")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class SegmentDraft:
    """Caller-authored inputs for one independently rendered segment.

    ``prepared_narration`` is the compatibility seam for legacy builders whose
    filenames, caches, and monkey-patch targets are observable contracts.  When it
    is present, neither ``narration_resolver`` nor the new TTS cache is touched.
    """

    segment_id: str
    visual_source: VisualSource
    render_options: RenderOptions
    subtitles: Mapping[str, str]
    narration_request: TtsRequest | None = None
    prepared_narration: Path | None = None
    start_seconds: float = 0.0

    def __post_init__(self) -> None:
        _identifier(self.segment_id, "segment_id")
        if not isinstance(self.visual_source, VisualSource):
            raise PipelineValidationError("visual_source must be a VisualSource")
        if self.prepared_narration is not None:
            object.__setattr__(
                self, "prepared_narration", Path(self.prepared_narration)
            )
        tracks = dict(self.subtitles)
        for locale, text in tracks.items():
            _required_text(locale, f"segment {self.segment_id} subtitle track")
            _required_text(text, f"segment {self.segment_id} subtitle text")
        object.__setattr__(self, "subtitles", MappingProxyType(tracks))
        if (
            isinstance(self.start_seconds, bool)
            or not isinstance(self.start_seconds, (int, float))
            or not math.isfinite(float(self.start_seconds))
            or self.start_seconds < 0
        ):
            raise PipelineValidationError(
                f"segment {self.segment_id} start_seconds must be finite and non-negative"
            )


@dataclass(frozen=True, slots=True)
class PipelineDraft:
    """A core project config plus the concrete media assembly for one attempt."""

    config: ProjectConfig
    segments: tuple[SegmentDraft, ...]
    deliverable_relative_path: Path
    deliverable_artifact_id: str
    deliverable_media_type: str

    def __post_init__(self) -> None:
        if not isinstance(self.config, ProjectConfig):
            raise PipelineValidationError("config must be a ProjectConfig")
        object.__setattr__(self, "segments", tuple(self.segments))
        object.__setattr__(
            self,
            "deliverable_relative_path",
            _relative_output(
                Path(self.deliverable_relative_path),
                "deliverable_relative_path",
            ),
        )
        _identifier(self.deliverable_artifact_id, "deliverable_artifact_id")
        _required_text(self.deliverable_media_type, "deliverable_media_type")


@dataclass(frozen=True, slots=True)
class PipelineArtifactRecord:
    """Exact bytes produced or consumed by an attempt."""

    artifact_id: str
    role: str
    path: Path
    bytes: int
    sha256: str
    media_type: str
    state: str = "complete"

    @classmethod
    def from_path(
        cls,
        path: Path,
        *,
        artifact_id: str,
        role: str,
        media_type: str | None = None,
        state: str = "complete",
    ) -> "PipelineArtifactRecord":
        source = Path(path).resolve()
        if not source.is_file():
            raise PipelineValidationError(f"artifact file is missing: {source}")
        return cls(
            artifact_id=_identifier(artifact_id, "artifact_id"),
            role=_identifier(role, "artifact role"),
            path=source,
            bytes=source.stat().st_size,
            sha256=_sha256(source),
            media_type=media_type or _media_type(source),
            state=_identifier(state, "artifact state"),
        )

    def to_audit_mapping(self) -> dict[str, object]:
        return {
            "id": self.artifact_id,
            "role": self.role,
            "path": str(self.path),
            "bytes": self.bytes,
            "sha256": self.sha256,
            "media_type": self.media_type,
            "state": self.state,
        }

    def to_source_record(
        self,
        *,
        project_root: Path,
        collection: str = "derived",
        label: str | None = None,
    ) -> SourceRecord:
        """Project this verified file into the core/audit ``SourceRecord`` ABI."""

        root = Path(project_root).resolve()
        try:
            relative = self.path.resolve().relative_to(root).as_posix()
        except ValueError as error:
            raise PipelineValidationError(
                f"artifact must be inside project_root {root}: {self.path}"
            ) from error
        return SourceRecord.from_mapping(
            {
                "id": self.artifact_id,
                "collection": collection,
                "role": self.role,
                "path": relative,
                "label": label or self.path.name,
                "bytes": self.bytes,
                "sha256": self.sha256,
                "media_type": self.media_type,
                "source_name": self.path.name,
            },
            "pipeline artifact",
        )


@dataclass(frozen=True, slots=True)
class PipelinePhaseRecord:
    sequence: int
    phase: str
    status: str
    artifact_ids: tuple[str, ...] = ()
    detail: str | None = None

    def to_mapping(self) -> dict[str, object]:
        result: dict[str, object] = {
            "sequence": self.sequence,
            "phase": self.phase,
            "status": self.status,
            "artifact_ids": list(self.artifact_ids),
        }
        if self.detail is not None:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True, slots=True)
class AuditRecordReady:
    """A byte-bound deliverable awaiting project audit and human review."""

    project_id: str
    deliverable: PipelineArtifactRecord
    phase_records: tuple[PipelinePhaseRecord, ...]
    status: str = "pending-project-audit"
    human_signoff_required: bool = True

    def to_mapping(self) -> dict[str, object]:
        return {
            "kind": "pipeline-deliverable-ready",
            "project_id": self.project_id,
            "status": self.status,
            "human_signoff_required": self.human_signoff_required,
            "deliverable": self.deliverable.to_audit_mapping(),
            "phase_history": [item.to_mapping() for item in self.phase_records],
        }


@dataclass(frozen=True, slots=True)
class PipelineFailure:
    phase: str
    exception_type: str
    message: str
    stdout: str
    stderr: str
    partial_paths: tuple[Path, ...]
    stdout_paths: tuple[Path, ...]
    stderr_paths: tuple[Path, ...]
    retained_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class PipelineResult:
    status: str
    validate_only: bool
    workdir: Path
    phases: tuple[PipelinePhaseRecord, ...]
    artifacts: tuple[PipelineArtifactRecord, ...]
    audit_record: AuditRecordReady | None
    failure: PipelineFailure | None
    signoff_recorded: bool = False

    @property
    def succeeded(self) -> bool:
        return self.status in {"validated", "succeeded"}

    def require_success(self) -> "PipelineResult":
        if not self.succeeded:
            raise PipelineExecutionError(self)
        return self


@runtime_checkable
class NarrationResolver(Protocol):
    """Adapter seam for legacy or project-specific narration preparation."""

    def __call__(
        self, segment: SegmentDraft, *, workdir: Path
    ) -> NarrationArtifact: ...


@runtime_checkable
class SubtitleRenderer(Protocol):
    """Render caller-configured subtitle/layout policy to one ASS document."""

    def __call__(
        self,
        segment: SegmentDraft,
        narration: NarrationArtifact,
        *,
        workdir: Path,
    ) -> str: ...


@runtime_checkable
class TtsCacheLike(Protocol):
    def get_or_create(
        self,
        request: TtsRequest,
        provider: TtsProvider,
        *,
        offline: bool = False,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> TtsCacheEntry: ...


RenderPlanner = Callable[..., RenderPlan]
ConcatPlanner = Callable[..., RenderPlan]
PlanExecutor = Callable[..., tuple[CommandResult, ...]]
CommandRunner = Callable[..., CommandResult]
DraftValidator = Callable[[PipelineDraft], None]


@dataclass(frozen=True, slots=True)
class PipelineDependencies:
    """All effectful or project-policy dependencies used by the orchestrator."""

    ffmpeg: str | os.PathLike[str]
    subtitle_renderer: SubtitleRenderer
    command_runner: CommandRunner
    visual_probe: VisualProbe
    tts_cache: TtsCacheLike | None = None
    tts_provider: TtsProvider | None = None
    visual_resolver: VisualResolver | None = None
    narration_resolver: NarrationResolver | None = None
    draft_validator: DraftValidator | None = None
    render_planner: RenderPlanner = plan_render
    concat_planner: ConcatPlanner = plan_concat
    plan_executor: PlanExecutor = execute_render_plan


@dataclass(frozen=True, slots=True)
class PipelineInvocation:
    """The exact draft, dependencies, and attempt directory produced by composition."""

    draft: PipelineDraft
    dependencies: PipelineDependencies
    workdir: Path

    def __post_init__(self) -> None:
        if not isinstance(self.draft, PipelineDraft):
            raise PipelineValidationError("invocation draft must be PipelineDraft")
        if not isinstance(self.dependencies, PipelineDependencies):
            raise PipelineValidationError(
                "invocation dependencies must be PipelineDependencies"
            )
        object.__setattr__(self, "workdir", Path(self.workdir))


@runtime_checkable
class PipelineComposer(Protocol):
    """Project-owned bridge from resolved registry components to one invocation.

    Generic command handlers resolve the two factories but do not guess their
    open-ended call signatures.  The injected composer owns that project-specific
    operation and should use :func:`xar_promo.storyboard.plan_storyboard` when it
    turns config cues into concrete segment timing.
    """

    def __call__(
        self,
        config: ProjectConfig,
        run: RunManifest | None,
        *,
        config_path: Path,
        run_path: Path | None,
        workdir: Path,
        adapter_factory: AdapterFactory,
        preset_factory: PresetFactory,
        validate_only: bool,
    ) -> PipelineInvocation: ...


def _output_paths(
    draft: PipelineDraft, workdir: Path
) -> tuple[dict[str, tuple[Path, Path, Path]], Path, Path, Path]:
    suffix = draft.deliverable_relative_path.suffix
    if not suffix:
        raise PipelineValidationError("deliverable_relative_path needs a file suffix")
    segments: dict[str, tuple[Path, Path, Path]] = {}
    for sequence, segment in enumerate(draft.segments, start=1):
        stem = f"{sequence:04d}-{segment.segment_id}"
        segments[segment.segment_id] = (
            workdir / "subtitles" / f"{stem}.ass",
            workdir / "partial" / f"{stem}.partial{suffix}",
            workdir / "segments" / f"{stem}{suffix}",
        )
    deliverable = workdir / draft.deliverable_relative_path
    concat_manifest = workdir / "concat" / "segments.txt"
    concat_partial = workdir / "partial" / (
        f"{deliverable.stem}.partial{deliverable.suffix}"
    )
    return segments, deliverable, concat_manifest, concat_partial


def _validate_draft(
    draft: PipelineDraft,
    workdir: Path,
    dependencies: PipelineDependencies,
) -> None:
    if not draft.segments:
        raise PipelineValidationError("a pipeline draft needs at least one segment")
    identifiers = [item.segment_id for item in draft.segments]
    if len(identifiers) != len(set(identifiers)):
        raise PipelineValidationError("segment ids must be unique")
    automatic_artifact_ids = {"concat.manifest"}
    for segment_id in identifiers:
        automatic_artifact_ids.update(
            {
                f"visual.{segment_id}",
                f"narration.{segment_id}",
                f"subtitle.{segment_id}",
                f"segment.{segment_id}",
            }
        )
    if draft.deliverable_artifact_id in automatic_artifact_ids:
        raise PipelineValidationError(
            "deliverable_artifact_id conflicts with a pipeline-owned artifact id: "
            f"{draft.deliverable_artifact_id}"
        )
    for segment in draft.segments:
        validate_visual_source(
            segment.visual_source,
            workdir=workdir,
            validate_only=True,
        )
        if (
            segment.visual_source.requires_resolution
            and dependencies.visual_resolver is None
        ):
            raise PipelineValidationError(
                f"segment {segment.segment_id} needs a visual resolver"
            )
        if (
            segment.prepared_narration is not None
            and not segment.prepared_narration.is_file()
        ):
            raise PipelineValidationError(
                f"prepared narration is missing: {segment.prepared_narration}"
            )
        if (
            segment.prepared_narration is None
            and dependencies.narration_resolver is None
            and (
                segment.narration_request is None
                or dependencies.tts_cache is None
                or dependencies.tts_provider is None
            )
        ):
            raise PipelineValidationError(
                f"segment {segment.segment_id} needs TTS cache/provider or a resolver"
            )
    if not callable(dependencies.subtitle_renderer):
        raise PipelineValidationError("subtitle_renderer must be callable")
    if not callable(dependencies.visual_probe):
        raise PipelineValidationError("visual_probe must be callable")
    for label, value in (
        ("command_runner", dependencies.command_runner),
        ("render_planner", dependencies.render_planner),
        ("concat_planner", dependencies.concat_planner),
        ("plan_executor", dependencies.plan_executor),
    ):
        if not callable(value):
            raise PipelineValidationError(f"{label} must be callable")
    _required_text(os.fspath(dependencies.ffmpeg), "ffmpeg executable")
    segment_paths, deliverable, concat_manifest, concat_partial = _output_paths(
        draft, workdir
    )
    candidates = [deliverable, concat_manifest, concat_partial]
    for subtitle, partial, rendered in segment_paths.values():
        candidates.extend((subtitle, partial, rendered))
    collisions = [path for path in candidates if path.exists()]
    if collisions:
        raise PipelineValidationError(
            "attempt output already exists; use a new workdir and retain the old one: "
            + ", ".join(str(path) for path in collisions)
        )
    canonical_candidates = [path.resolve() for path in candidates]
    if len(canonical_candidates) != len(set(canonical_candidates)):
        raise PipelineValidationError("pipeline-owned output paths must be distinct")
    if dependencies.draft_validator is not None:
        dependencies.draft_validator(draft)


def _phase(
    records: list[PipelinePhaseRecord],
    phase: str,
    status: str,
    *,
    artifacts: Sequence[PipelineArtifactRecord] = (),
    detail: str | None = None,
) -> None:
    records.append(
        PipelinePhaseRecord(
            sequence=len(records) + 1,
            phase=phase,
            status=status,
            artifact_ids=tuple(item.artifact_id for item in artifacts),
            detail=detail,
        )
    )


def _write_new_text(path: Path, content: str) -> None:
    if not isinstance(content, str) or not content:
        raise PipelineValidationError("subtitle_renderer must return non-empty text")
    payload = content.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as error:
        raise PipelineValidationError(
            f"refusing to overwrite subtitle process material: {path}"
        ) from error


def _cached_narration(entry: TtsCacheEntry) -> NarrationArtifact:
    metadata = {
        "fingerprint": entry.fingerprint,
        "cache_hit": entry.cache_hit,
        "metadata_path": str(entry.metadata_path),
    }
    return NarrationArtifact(
        entry.media_path,
        _media_type(entry.media_path, "audio/octet-stream"),
        "tts-cache",
        metadata,
    )


def _resolve_visual(
    segment: SegmentDraft,
    dependencies: PipelineDependencies,
    workdir: Path,
) -> PreparedVisual:
    return prepare_visual(
        segment.visual_source,
        workdir=workdir,
        resolver=dependencies.visual_resolver,
        probe=dependencies.visual_probe,
    )


def _resolve_narration(
    segment: SegmentDraft,
    dependencies: PipelineDependencies,
    workdir: Path,
    *,
    offline_tts: bool,
    max_tts_attempts: int,
    retry_backoff_seconds: float,
) -> NarrationArtifact:
    if segment.prepared_narration is not None:
        return NarrationArtifact(
            segment.prepared_narration,
            _media_type(segment.prepared_narration, "audio/octet-stream"),
            "prepared",
        )
    if dependencies.narration_resolver is not None:
        artifact = dependencies.narration_resolver(segment, workdir=workdir)
        if not isinstance(artifact, NarrationArtifact):
            raise PipelineValidationError(
                "narration_resolver must return NarrationArtifact"
            )
        return artifact
    if (
        segment.narration_request is None
        or dependencies.tts_cache is None
        or dependencies.tts_provider is None
    ):
        raise PipelineValidationError(
            f"segment {segment.segment_id} has no narration preparation path"
        )
    return _cached_narration(
        dependencies.tts_cache.get_or_create(
            segment.narration_request,
            dependencies.tts_provider,
            offline=offline_tts,
            max_attempts=max_tts_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
        )
    )


def _existing_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.resolve() for path in root.rglob("*") if path.is_file()), key=str))


def _failure_record(
    error: Exception,
    *,
    phase: str,
    workdir: Path,
    active_plan: RenderPlan | None,
) -> PipelineFailure:
    result = getattr(error, "result", None)
    stdout = result.stdout if isinstance(result, CommandResult) else ""
    stderr = result.stderr if isinstance(result, CommandResult) else ""
    partials: list[Path] = []
    stdout_paths: list[Path] = []
    stderr_paths: list[Path] = []
    if isinstance(result, CommandResult):
        partials.extend(
            item.path.resolve() for item in result.partial_artifacts if item.exists
        )
        stdout_path = (result.audit_directory / "stdout.txt").resolve()
        stderr_path = (result.audit_directory / "stderr.txt").resolve()
        if stdout_path.is_file():
            stdout_paths.append(stdout_path)
        if stderr_path.is_file():
            stderr_paths.append(stderr_path)
    if active_plan is not None and active_plan.partial_output.is_file():
        partials.append(active_plan.partial_output.resolve())
    retained = _existing_files(workdir)
    return PipelineFailure(
        phase=phase,
        exception_type=type(error).__name__,
        message=str(error),
        stdout=stdout,
        stderr=stderr,
        partial_paths=tuple(dict.fromkeys(partials)),
        stdout_paths=tuple(dict.fromkeys(stdout_paths)),
        stderr_paths=tuple(dict.fromkeys(stderr_paths)),
        retained_paths=retained,
    )


def _failed_result(
    error: Exception,
    *,
    phase: str,
    validate_only: bool,
    workdir: Path,
    phases: list[PipelinePhaseRecord],
    artifacts: list[PipelineArtifactRecord],
    active_plan: RenderPlan | None = None,
) -> PipelineResult:
    _phase(phases, phase, "failed", detail=f"{type(error).__name__}: {error}")
    return PipelineResult(
        status="failed",
        validate_only=validate_only,
        workdir=workdir,
        phases=tuple(phases),
        artifacts=tuple(artifacts),
        audit_record=None,
        failure=_failure_record(
            error, phase=phase, workdir=workdir, active_plan=active_plan
        ),
        signoff_recorded=False,
    )


def run_pipeline(
    draft: PipelineDraft,
    *,
    workdir: Path,
    dependencies: PipelineDependencies,
    validate_only: bool = False,
    offline_tts: bool = False,
    max_tts_attempts: int = 3,
    retry_backoff_seconds: float = 1.0,
) -> PipelineResult:
    """Validate or execute one draft-to-audit-candidate attempt.

    Validation is strictly read-only: it does not create ``workdir``, resolve or
    synthesize narration, invoke subtitle/layout code, plan media commands, run
    FFmpeg, or write a deliverable.  A full run returns RED rather than erasing
    evidence when any injected stage raises.
    """

    attempt_root = Path(workdir).expanduser().resolve()
    phases: list[PipelinePhaseRecord] = []
    artifacts: list[PipelineArtifactRecord] = []
    try:
        if not isinstance(validate_only, bool) or not isinstance(offline_tts, bool):
            raise PipelineValidationError(
                "validate_only and offline_tts must be boolean"
            )
        if (
            isinstance(max_tts_attempts, bool)
            or not isinstance(max_tts_attempts, int)
            or max_tts_attempts < 1
        ):
            raise PipelineValidationError("max_tts_attempts must be a positive integer")
        if (
            isinstance(retry_backoff_seconds, bool)
            or not isinstance(retry_backoff_seconds, (int, float))
            or not math.isfinite(float(retry_backoff_seconds))
            or retry_backoff_seconds < 0
        ):
            raise PipelineValidationError(
                "retry_backoff_seconds must be finite and non-negative"
            )
        _validate_draft(draft, attempt_root, dependencies)
    except Exception as error:
        return _failed_result(
            error,
            phase="draft",
            validate_only=validate_only,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
        )

    if validate_only:
        _phase(
            phases,
            "draft",
            "validated",
            detail=f"{len(draft.segments)} segment(s)",
        )
        for name in _PHASES[1:]:
            _phase(phases, name, "skipped", detail="validate-only")
        return PipelineResult(
            status="validated",
            validate_only=True,
            workdir=attempt_root,
            phases=tuple(phases),
            artifacts=(),
            audit_record=None,
            failure=None,
            signoff_recorded=False,
        )

    try:
        attempt_root.mkdir(parents=True, exist_ok=True)
    except Exception as error:
        return _failed_result(
            error,
            phase="draft",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
        )
    _phase(
        phases,
        "draft",
        "succeeded",
        detail=f"{len(draft.segments)} segment(s)",
    )
    output_paths, deliverable_path, concat_path, concat_partial = _output_paths(
        draft, attempt_root
    )

    visuals: dict[str, PreparedVisual] = {}
    visual_records: list[PipelineArtifactRecord] = []
    try:
        for segment in draft.segments:
            visual = _resolve_visual(segment, dependencies, attempt_root)
            visuals[segment.segment_id] = visual
            record = PipelineArtifactRecord.from_path(
                visual.path,
                artifact_id=f"visual.{segment.segment_id}",
                role="visual-input",
                media_type=visual.media_type,
            )
            visual_records.append(record)
            artifacts.append(record)
    except Exception as error:
        return _failed_result(
            error,
            phase="visual",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
        )
    _phase(phases, "visual", "succeeded", artifacts=visual_records)

    narrations: dict[str, NarrationArtifact] = {}
    narration_records: list[PipelineArtifactRecord] = []
    try:
        for segment in draft.segments:
            narration = _resolve_narration(
                segment,
                dependencies,
                attempt_root,
                offline_tts=offline_tts,
                max_tts_attempts=max_tts_attempts,
                retry_backoff_seconds=retry_backoff_seconds,
            )
            if not narration.path.is_file():
                raise PipelineValidationError(
                    f"narration preparation returned a missing file: {narration.path}"
                )
            narrations[segment.segment_id] = narration
            record = PipelineArtifactRecord.from_path(
                narration.path,
                artifact_id=f"narration.{segment.segment_id}",
                role="narration",
                media_type=narration.media_type,
            )
            narration_records.append(record)
            artifacts.append(record)
    except Exception as error:
        return _failed_result(
            error,
            phase="narration",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
        )
    _phase(phases, "narration", "succeeded", artifacts=narration_records)

    subtitle_paths: dict[str, Path] = {}
    subtitle_records: list[PipelineArtifactRecord] = []
    try:
        for segment in draft.segments:
            subtitle_path = output_paths[segment.segment_id][0]
            document = dependencies.subtitle_renderer(
                segment,
                narrations[segment.segment_id],
                workdir=attempt_root,
            )
            _write_new_text(subtitle_path, document)
            subtitle_paths[segment.segment_id] = subtitle_path
            record = PipelineArtifactRecord.from_path(
                subtitle_path,
                artifact_id=f"subtitle.{segment.segment_id}",
                role="subtitle",
                media_type="text/x-ass",
            )
            subtitle_records.append(record)
            artifacts.append(record)
    except Exception as error:
        return _failed_result(
            error,
            phase="subtitle",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
        )
    _phase(phases, "subtitle", "succeeded", artifacts=subtitle_records)

    plans: dict[str, RenderPlan] = {}
    try:
        for segment in draft.segments:
            _, partial_path, final_path = output_paths[segment.segment_id]
            plans[segment.segment_id] = dependencies.render_planner(
                ffmpeg=dependencies.ffmpeg,
                video_input=visuals[segment.segment_id].path.resolve(),
                audio_input=narrations[segment.segment_id].path.resolve(),
                partial_output=partial_path,
                final_output=final_path,
                audit_directory=attempt_root
                / "audit"
                / "segments"
                / segment.segment_id,
                options=segment.render_options,
                ass_path=subtitle_paths[segment.segment_id],
                start_seconds=float(segment.start_seconds),
                working_directory=attempt_root,
            )
    except Exception as error:
        return _failed_result(
            error,
            phase="segment-plan",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
        )
    _phase(
        phases,
        "segment-plan",
        "succeeded",
        detail=f"{len(plans)} immutable render plan(s)",
    )

    segment_records: list[PipelineArtifactRecord] = []
    active_plan: RenderPlan | None = None
    try:
        for segment in draft.segments:
            active_plan = plans[segment.segment_id]
            dependencies.plan_executor(
                active_plan, command_runner=dependencies.command_runner
            )
            record = PipelineArtifactRecord.from_path(
                active_plan.final_output,
                artifact_id=f"segment.{segment.segment_id}",
                role="rendered-segment",
                media_type=draft.deliverable_media_type,
            )
            segment_records.append(record)
            artifacts.append(record)
    except Exception as error:
        return _failed_result(
            error,
            phase="segment-render",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
            active_plan=active_plan,
        )
    _phase(phases, "segment-render", "succeeded", artifacts=segment_records)

    concat_plan: RenderPlan | None = None
    try:
        concat_plan = dependencies.concat_planner(
            ffmpeg=dependencies.ffmpeg,
            segment_paths=tuple(
                plans[item.segment_id].final_output for item in draft.segments
            ),
            concat_path=concat_path,
            partial_output=concat_partial,
            final_output=deliverable_path,
            audit_directory=attempt_root / "audit" / "concat",
            working_directory=attempt_root,
        )
        dependencies.plan_executor(
            concat_plan, command_runner=dependencies.command_runner
        )
        concat_record = PipelineArtifactRecord.from_path(
            concat_path,
            artifact_id="concat.manifest",
            role="concat-manifest",
            media_type="text/plain",
        )
        deliverable_record = PipelineArtifactRecord.from_path(
            deliverable_path,
            artifact_id=draft.deliverable_artifact_id,
            role="deliverable",
            media_type=draft.deliverable_media_type,
        )
        artifacts.extend((concat_record, deliverable_record))
    except Exception as error:
        return _failed_result(
            error,
            phase="concat",
            validate_only=False,
            workdir=attempt_root,
            phases=phases,
            artifacts=artifacts,
            active_plan=concat_plan,
        )
    _phase(
        phases,
        "concat",
        "succeeded",
        artifacts=(concat_record, deliverable_record),
    )
    _phase(
        phases,
        "audit-record-ready",
        "succeeded",
        artifacts=(deliverable_record,),
        detail="pending project audit and explicit human sign-off",
    )
    audit_record = AuditRecordReady(
        project_id=draft.config.project_id,
        deliverable=deliverable_record,
        phase_records=tuple(phases),
    )
    return PipelineResult(
        status="succeeded",
        validate_only=False,
        workdir=attempt_root,
        phases=tuple(phases),
        artifacts=tuple(artifacts),
        audit_record=audit_record,
        failure=None,
        signoff_recorded=False,
    )


def run_invocation(
    invocation: PipelineInvocation,
    *,
    validate_only: bool = False,
    offline_tts: bool = False,
    max_tts_attempts: int = 3,
    retry_backoff_seconds: float = 1.0,
) -> PipelineResult:
    """Execute a composer-produced invocation without reinterpreting it."""

    if not isinstance(invocation, PipelineInvocation):
        raise PipelineValidationError("invocation must be PipelineInvocation")
    return run_pipeline(
        invocation.draft,
        workdir=invocation.workdir,
        dependencies=invocation.dependencies,
        validate_only=validate_only,
        offline_tts=offline_tts,
        max_tts_attempts=max_tts_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )


__all__ = [
    "AuditRecordReady",
    "NarrationArtifact",
    "NarrationResolver",
    "PipelinePhaseRecord",
    "PipelineArtifactRecord",
    "PipelineDependencies",
    "PipelineDraft",
    "PipelineError",
    "PipelineExecutionError",
    "PipelineFailure",
    "PipelineInvocation",
    "PipelineComposer",
    "PipelineResult",
    "PipelineValidationError",
    "SegmentDraft",
    "SubtitleRenderer",
    "TtsCacheLike",
    "run_invocation",
    "run_pipeline",
]
