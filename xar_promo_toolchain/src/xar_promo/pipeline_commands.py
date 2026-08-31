"""Programmatic plan, build, and automated-audit command handlers.

The handlers in this module are deliberately CLI-agnostic.  They load the
native project/run contracts, resolve project components through the registry,
delegate project-specific composition to ``PipelineComposer``, and return a
typed outcome whose public exit status is always 0 or 2.

Human approval is outside this module.  In particular, the audit handler never
imports or calls the sign-off operation and always asks the audit layer to
record ``manual_signoff.state=not-provided``.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from .audit import write_audit_report
from .errors import ArtifactError, ManifestError, PromoToolchainError
from .evidence import load_evidence_bundle
from .model import ProjectConfig, RunManifest, SourceRecord
from .operations import preserve_artifact
from .pipeline import (
    PipelineArtifactRecord,
    PipelineComposer,
    PipelineResult,
    run_invocation,
)
from .project import LoadedDocument, load_document, sha256_file
from .registry import ComponentRegistry
from .runlog import append_automated_audit_record, append_phase_record


CommandName = Literal["plan", "build", "audit"]
CommandExitStatus = Literal[0, 2]
_ID_FRAGMENT = re.compile(r"[^A-Za-z0-9._-]+")


class PipelineCommandError(PromoToolchainError):
    """A command could not be completed against its native project contract."""


@dataclass(frozen=True, slots=True)
class CommandFailure:
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    """Typed, non-throwing result consumed by the CLI boundary.

    Operational failures are represented by ``exit_status=2`` and ``failure``.
    ``pipeline_result`` remains attached on RED builds so callers can inspect
    retained paths and phase diagnostics without re-running the attempt.
    """

    command: CommandName
    exit_status: CommandExitStatus
    status: Literal["succeeded", "failed"]
    document_path: Path
    config_path: Path | None = None
    run_path: Path | None = None
    adapter_id: str | None = None
    preset_id: str | None = None
    workdir: Path | None = None
    pipeline_result: PipelineResult | None = None
    preserved_artifacts: tuple[SourceRecord, ...] = ()
    audit_report_path: Path | None = None
    audit_report: Mapping[str, Any] | None = None
    failure: CommandFailure | None = None

    def __post_init__(self) -> None:
        if self.exit_status not in {0, 2}:
            raise ValueError("command exit_status must be 0 or 2")
        if (self.exit_status == 0) != (self.status == "succeeded"):
            raise ValueError("command status and exit_status disagree")
        if (self.failure is None) != (self.exit_status == 0):
            raise ValueError("failed commands need exactly one typed failure")
        object.__setattr__(self, "document_path", Path(self.document_path))
        for field_name in ("config_path", "run_path", "workdir", "audit_report_path"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, Path(value))
        object.__setattr__(self, "preserved_artifacts", tuple(self.preserved_artifacts))

    @property
    def succeeded(self) -> bool:
        return self.exit_status == 0


@dataclass(frozen=True, slots=True)
class _CommandContext:
    loaded: LoadedDocument
    config: ProjectConfig
    run: RunManifest | None
    config_path: Path
    run_path: Path | None


def _load_context(document_path: Path, *, require_run: bool) -> _CommandContext:
    loaded = load_document(document_path, check_files=True)
    if loaded.config is not None:
        if require_run:
            raise ManifestError("this command requires a native RunManifest")
        return _CommandContext(
            loaded=loaded,
            config=loaded.config,
            run=None,
            config_path=loaded.path,
            run_path=None,
        )
    if loaded.run is not None and loaded.bound_config is not None:
        config_path = (
            loaded.path.parent / Path(loaded.run.project_config.path)
        ).resolve()
        return _CommandContext(
            loaded=loaded,
            config=loaded.bound_config,
            run=loaded.run,
            config_path=config_path,
            run_path=loaded.path,
        )
    raise ManifestError("command handlers require a native ProjectConfig or RunManifest")


def _failure(error: BaseException) -> CommandFailure:
    return CommandFailure(
        exception_type=type(error).__name__,
        message=str(error) or type(error).__name__,
    )


def _pipeline_failure(result: PipelineResult) -> CommandFailure:
    if result.failure is None:
        return CommandFailure("PipelineExecutionError", "pipeline did not complete")
    detail = result.failure
    return CommandFailure(
        detail.exception_type,
        f"{detail.phase}: {detail.message}",
    )


def _runlog_status(status: str) -> str:
    return "succeeded" if status == "validated" else status


def _append_pipeline_phases(
    run_path: Path,
    *,
    command: Literal["build"],
    result: PipelineResult,
    available_artifact_ids: set[str],
) -> None:
    for phase in result.phases:
        append_phase_record(
            run_path,
            phase_id=f"{command}.{phase.phase}",
            status=_runlog_status(phase.status),
            artifact_ids=(
                artifact_id
                for artifact_id in phase.artifact_ids
                if artifact_id in available_artifact_ids
            ),
            detail=phase.detail,
        )


def _append_pre_pipeline_failure(
    context: _CommandContext | None,
    *,
    command: CommandName,
    error: BaseException,
) -> None:
    if context is None or context.run_path is None:
        return
    try:
        append_phase_record(
            context.run_path,
            phase_id=f"{command}.command-preparation",
            status="failed",
            detail=f"{type(error).__name__}: {str(error) or type(error).__name__}",
        )
    except Exception:
        # Preserve the primary failure.  The returned error remains actionable
        # even when a concurrently changed or damaged run ledger cannot append.
        return


def _resolve_components(
    context: _CommandContext,
    registry: ComponentRegistry,
) -> tuple[object, object]:
    return (
        registry.resolve_adapter(context.config.adapter),
        registry.resolve_preset(context.config.preset),
    )


def _red(
    command: CommandName,
    document_path: Path,
    error: BaseException,
    *,
    context: _CommandContext | None = None,
    workdir: Path | None = None,
    pipeline_result: PipelineResult | None = None,
    preserved_artifacts: tuple[SourceRecord, ...] = (),
    audit_report_path: Path | None = None,
    audit_report: Mapping[str, Any] | None = None,
) -> CommandOutcome:
    return CommandOutcome(
        command=command,
        exit_status=2,
        status="failed",
        document_path=document_path,
        config_path=None if context is None else context.config_path,
        run_path=None if context is None else context.run_path,
        adapter_id=None if context is None else context.config.adapter,
        preset_id=None if context is None else context.config.preset,
        workdir=workdir,
        pipeline_result=pipeline_result,
        preserved_artifacts=preserved_artifacts,
        audit_report_path=audit_report_path,
        audit_report=audit_report,
        failure=_failure(error),
    )


def handle_plan(
    document_path: Path,
    *,
    workdir: Path,
    registry: ComponentRegistry,
    composer: PipelineComposer,
) -> CommandOutcome:
    """Validate one composed plan without invoking production dependencies.

    A ProjectConfig or RunManifest may be supplied.  Both forms are strictly
    read-only: planning never appends the run ledger or creates the workdir.
    """

    source = Path(document_path).expanduser().resolve()
    attempt = Path(workdir).expanduser().resolve()
    context: _CommandContext | None = None
    try:
        context = _load_context(source, require_run=False)
        adapter_factory, preset_factory = _resolve_components(context, registry)
        invocation = composer(
            context.config,
            context.run,
            config_path=context.config_path,
            run_path=context.run_path,
            workdir=attempt,
            adapter_factory=adapter_factory,
            preset_factory=preset_factory,
            validate_only=True,
        )
        result = run_invocation(invocation, validate_only=True)
        if not result.succeeded:
            failure = _pipeline_failure(result)
            return _red(
                "plan",
                source,
                PipelineCommandError(failure.message),
                context=context,
                workdir=result.workdir,
                pipeline_result=result,
            )
        return CommandOutcome(
            command="plan",
            exit_status=0,
            status="succeeded",
            document_path=source,
            config_path=context.config_path,
            run_path=context.run_path,
            adapter_id=context.config.adapter,
            preset_id=context.config.preset,
            workdir=result.workdir,
            pipeline_result=result,
        )
    except Exception as error:
        return _red("plan", source, error, context=context, workdir=attempt)


def _verify_pipeline_artifact(record: PipelineArtifactRecord) -> None:
    if not record.path.is_file():
        raise ArtifactError(f"pipeline artifact was not found: {record.path}")
    if record.path.stat().st_size != record.bytes:
        raise ArtifactError(
            f"pipeline artifact {record.artifact_id!r} byte count changed before preservation"
        )
    if sha256_file(record.path) != record.sha256:
        raise ArtifactError(
            f"pipeline artifact {record.artifact_id!r} SHA-256 changed before preservation"
        )


def _preserve_pipeline_artifact(
    run_path: Path,
    record: PipelineArtifactRecord,
) -> SourceRecord:
    _verify_pipeline_artifact(record)
    preserved = preserve_artifact(
        run_path,
        record.path,
        artifact_id=record.artifact_id,
        collection="derived",
        role=record.role,
        label=record.path.name,
        media_type=record.media_type,
    )
    if (preserved.bytes, preserved.sha256) != (record.bytes, record.sha256):
        raise ArtifactError(
            f"preserved artifact {record.artifact_id!r} does not match pipeline bytes"
        )
    return preserved


def _fragment(value: str, *, fallback: str) -> str:
    normalized = _ID_FRAGMENT.sub("-", value).strip(".-")
    return (normalized or fallback)[:48]


def _retained_identity(path: Path, *, role: str, digest: str) -> str:
    seed = f"{role}\0{path.name}\0{digest}".encode("utf-8", errors="surrogatepass")
    suffix = hashlib.sha256(seed).hexdigest()[:24]
    return f"retained.{_fragment(role, fallback='material')}.{suffix}"


def _preserve_retained_materials(
    run_path: Path,
    result: PipelineResult,
    *,
    already_preserved_paths: set[Path],
) -> tuple[SourceRecord, ...]:
    failure = result.failure
    if failure is None:
        return ()
    stdout = {path.resolve() for path in failure.stdout_paths}
    stderr = {path.resolve() for path in failure.stderr_paths}
    partial = {path.resolve() for path in failure.partial_paths}
    records: list[SourceRecord] = []
    seen: set[Path] = set()
    for raw_path in failure.retained_paths:
        path = raw_path.resolve()
        if path in seen or path in already_preserved_paths or not path.is_file():
            continue
        seen.add(path)
        if path in stdout:
            role = "process-stdout"
        elif path in stderr:
            role = "process-stderr"
        elif path in partial:
            role = "partial-output"
        else:
            role = "failure-material"
        digest = sha256_file(path)
        records.append(
            preserve_artifact(
                run_path,
                path,
                artifact_id=_retained_identity(path, role=role, digest=digest),
                collection="derived",
                role=role,
                label=f"Retained {role}: {path.name}",
                media_type=None,
            )
        )
    return tuple(records)


def handle_build(
    run_manifest_path: Path,
    *,
    workdir: Path,
    registry: ComponentRegistry,
    composer: PipelineComposer,
    offline_tts: bool = False,
    max_tts_attempts: int = 3,
    retry_backoff_seconds: float = 1.0,
) -> CommandOutcome:
    """Execute a build, preserve every materialized artifact, and log phases.

    A RED pipeline remains RED, but its completed artifacts, partial outputs,
    stdout, stderr, and other retained files are copied into the run's immutable
    content-addressed storage before the outcome is returned.
    """

    source = Path(run_manifest_path).expanduser().resolve()
    attempt = Path(workdir).expanduser().resolve()
    context: _CommandContext | None = None
    result: PipelineResult | None = None
    preserved: list[SourceRecord] = []
    try:
        context = _load_context(source, require_run=True)
        if context.run_path is None:
            raise ManifestError("build requires a native RunManifest")
        adapter_factory, preset_factory = _resolve_components(context, registry)
        invocation = composer(
            context.config,
            context.run,
            config_path=context.config_path,
            run_path=context.run_path,
            workdir=attempt,
            adapter_factory=adapter_factory,
            preset_factory=preset_factory,
            validate_only=False,
        )
        result = run_invocation(
            invocation,
            validate_only=False,
            offline_tts=offline_tts,
            max_tts_attempts=max_tts_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
        )
    except Exception as error:
        _append_pre_pipeline_failure(context, command="build", error=error)
        return _red("build", source, error, context=context, workdir=attempt)

    preservation_errors: list[BaseException] = []
    completed_paths: set[Path] = set()
    retained_records: tuple[SourceRecord, ...] = ()
    for record in result.artifacts:
        try:
            preserved.append(_preserve_pipeline_artifact(context.run_path, record))
            completed_paths.add(record.path.resolve())
        except Exception as error:
            preservation_errors.append(error)
    try:
        retained_records = _preserve_retained_materials(
            context.run_path,
            result,
            already_preserved_paths=completed_paths,
        )
        preserved.extend(retained_records)
    except Exception as error:
        preservation_errors.append(error)

    try:
        available_ids = {record.artifact_id for record in preserved}
        _append_pipeline_phases(
            context.run_path,
            command="build",
            result=result,
            available_artifact_ids=available_ids,
        )
        if result.failure is not None and retained_records:
            append_phase_record(
                context.run_path,
                phase_id="build.failure-materials",
                status="failed",
                artifact_ids=(record.artifact_id for record in retained_records),
                detail=(
                    f"{result.failure.phase}: {result.failure.exception_type}: "
                    f"{result.failure.message}"
                ),
            )
        if preservation_errors:
            append_phase_record(
                context.run_path,
                phase_id="build.artifact-preservation",
                status="failed",
                artifact_ids=sorted(available_ids),
                detail="; ".join(
                    f"{type(error).__name__}: {str(error) or type(error).__name__}"
                    for error in preservation_errors
                ),
            )
    except Exception as error:
        preservation_errors.append(error)

    if preservation_errors:
        message = "; ".join(
            f"{type(error).__name__}: {str(error) or type(error).__name__}"
            for error in preservation_errors
        )
        return _red(
            "build",
            source,
            PipelineCommandError(message),
            context=context,
            workdir=result.workdir,
            pipeline_result=result,
            preserved_artifacts=tuple(preserved),
        )
    if not result.succeeded:
        failure = _pipeline_failure(result)
        return _red(
            "build",
            source,
            PipelineCommandError(failure.message),
            context=context,
            workdir=result.workdir,
            pipeline_result=result,
            preserved_artifacts=tuple(preserved),
        )
    return CommandOutcome(
        command="build",
        exit_status=0,
        status="succeeded",
        document_path=source,
        config_path=context.config_path,
        run_path=context.run_path,
        adapter_id=context.config.adapter,
        preset_id=context.config.preset,
        workdir=result.workdir,
        pipeline_result=result,
        preserved_artifacts=tuple(preserved),
    )


def _audit_input_id(record: SourceRecord) -> str:
    role = _fragment(record.role, fallback="evidence")
    identity = hashlib.sha256(
        f"{record.artifact_id}\0{record.path}\0{record.sha256}".encode("utf-8")
    ).hexdigest()[:16]
    return f"audit-input.{role}.{record.sha256.lower()[:12]}.{identity}"


def _preserve_source_record(
    run_path: Path,
    project_root: Path,
    record: SourceRecord,
) -> SourceRecord:
    return preserve_artifact(
        run_path,
        project_root / Path(record.path),
        artifact_id=_audit_input_id(record),
        collection=record.collection,
        role=record.role,
        label=f"Audit input {record.role} {record.sha256[:12]}",
        media_type=record.media_type,
    )


def _evidence_source_records(
    bundle: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> tuple[SourceRecord, ...]:
    records: list[SourceRecord] = [
        SourceRecord.from_mapping(bundle["plan"], "evidence bundle plan")
    ]
    for index, chapter in enumerate(plan["chapters"]):
        records.append(
            SourceRecord.from_mapping(
                chapter["source"]["artifact"],
                f"evidence plan chapters[{index}].source.artifact",
            )
        )
    for index, entry in enumerate(bundle["entries"]):
        records.append(
            SourceRecord.from_mapping(
                entry["binding"]["artifact"],
                f"evidence bundle entries[{index}].binding.artifact",
            )
        )
    unique: dict[tuple[str, str, str], SourceRecord] = {}
    for record in records:
        unique[(record.role, record.sha256, record.path)] = record
    return tuple(unique.values())


def _preserve_audit_file(
    run_path: Path,
    path: Path,
    *,
    role: str,
    artifact_id: str | None = None,
) -> SourceRecord:
    digest = sha256_file(path)
    name_identity = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:8]
    effective_id = artifact_id or (
        f"audit-input.{role}.{digest.lower()[:16]}.{name_identity}"
    )
    return preserve_artifact(
        run_path,
        path,
        artifact_id=effective_id,
        collection="derived",
        role=role,
        label=path.name,
        media_type="application/json",
    )


def handle_audit(
    run_manifest_path: Path,
    *,
    registry: ComponentRegistry,
    subject_artifact_id: str,
    evidence_bundle_path: Path,
    report_path: Path,
    report_artifact_id: str,
    created_at_utc: str | None = None,
) -> CommandOutcome:
    """Write and retain one automated audit without creating approval state."""

    source = Path(run_manifest_path).expanduser().resolve()
    context: _CommandContext | None = None
    report_target = Path(report_path).expanduser()
    report: Mapping[str, Any] | None = None
    preserved: list[SourceRecord] = []
    try:
        context = _load_context(source, require_run=True)
        if context.run_path is None or context.run is None:
            raise ManifestError("audit requires a native RunManifest")
        _resolve_components(context, registry)
        project_root = context.run_path.parent.resolve()
        bundle_path = Path(evidence_bundle_path).expanduser()
        if not bundle_path.is_absolute():
            bundle_path = project_root / bundle_path
        bundle_path = bundle_path.resolve()
        if not report_target.is_absolute():
            report_target = project_root / report_target
        report_target = report_target.resolve()

        subject = next(
            (
                artifact
                for artifact in context.run.artifacts
                if artifact.artifact_id == subject_artifact_id
            ),
            None,
        )
        if subject is None:
            raise ArtifactError(
                f"audit subject artifact id was not found: {subject_artifact_id}"
            )
        report = write_audit_report(
            report_target,
            project_root=project_root,
            subject=subject,
            evidence_bundle_path=bundle_path,
            signoff_run_manifest_path=None,
            created_at_utc=created_at_utc,
        )
        if report["manual_signoff"] != {"state": "not-provided"}:
            raise PipelineCommandError("automated audit unexpectedly read approval state")
        automated = report["automated_audit"]
        if automated.get("manual_approval_granted") is not False:
            raise PipelineCommandError("automated audit cannot grant manual approval")

        bundle, plan = load_evidence_bundle(
            bundle_path,
            project_root=project_root,
        )
        for evidence_record in _evidence_source_records(bundle, plan):
            preserved.append(
                _preserve_source_record(
                    context.run_path,
                    project_root,
                    evidence_record,
                )
            )
        preserved.append(
            _preserve_audit_file(
                context.run_path,
                bundle_path,
                role="evidence-bundle",
            )
        )
        report_record = _preserve_audit_file(
            context.run_path,
            report_target,
            role="audit",
            artifact_id=report_artifact_id,
        )
        preserved.append(report_record)

        append_automated_audit_record(
            context.run_path,
            check_id=automated["scope"],
            status=automated["status"],
            subject_artifact_id=subject.artifact_id,
            report_artifact_id=report_record.artifact_id,
            recorded_at=created_at_utc,
        )
        return CommandOutcome(
            command="audit",
            exit_status=0,
            status="succeeded",
            document_path=source,
            config_path=context.config_path,
            run_path=context.run_path,
            adapter_id=context.config.adapter,
            preset_id=context.config.preset,
            preserved_artifacts=tuple(preserved),
            audit_report_path=report_target,
            audit_report=report,
        )
    except Exception as error:
        return _red(
            "audit",
            source,
            error,
            context=context,
            preserved_artifacts=tuple(preserved),
            audit_report_path=report_target,
            audit_report=report,
        )


__all__ = [
    "CommandExitStatus",
    "CommandFailure",
    "CommandName",
    "CommandOutcome",
    "PipelineCommandError",
    "handle_audit",
    "handle_build",
    "handle_plan",
]
