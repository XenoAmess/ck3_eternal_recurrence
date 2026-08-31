"""Typed append-only phase and automated-audit records for a RunManifest."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .errors import PromoToolchainError
from .model import RunManifest, SourceRecord
from .operations import _append_run_records
from .project import load_document


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")
PHASE_STATUSES = frozenset({"started", "succeeded", "failed", "skipped"})
AUDIT_STATUSES = frozenset({"passed", "failed", "error"})


class RunLogError(PromoToolchainError):
    """A phase or automated-audit fact violates the typed run-log contract."""


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RunLogError(f"{context} must be an object")
    return dict(value)


def _keys(
    value: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str],
    context: str,
) -> None:
    missing = sorted(required - set(value))
    extras = sorted(set(value) - required - optional)
    if missing:
        raise RunLogError(f"{context} is missing fields: {', '.join(missing)}")
    if extras:
        raise RunLogError(f"{context} has unsupported fields: {', '.join(extras)}")


def _identifier(value: Any, context: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value.strip()) is None:
        raise RunLogError(f"{context} must be a portable identifier")
    return value.strip()


def _text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunLogError(f"{context} must be a non-empty string")
    return value.strip()


def _integer(value: Any, context: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RunLogError(f"{context} must be an integer >= {minimum}")
    return value


def _digest(value: Any, context: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value.strip()) is None:
        raise RunLogError(f"{context} must be a SHA-256")
    return value.strip().upper()


def _status(value: Any, allowed: frozenset[str], context: str) -> str:
    result = _text(value, context)
    if result not in allowed:
        raise RunLogError(
            f"{context} must be one of: {', '.join(sorted(allowed))}"
        )
    return result


def _utc_timestamp(value: str | dt.datetime | None, context: str) -> str:
    if value is None:
        parsed = dt.datetime.now(dt.timezone.utc)
    elif isinstance(value, dt.datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        raw = value.strip()
        try:
            parsed = dt.datetime.fromisoformat(
                raw[:-1] + "+00:00" if raw.endswith("Z") else raw
            )
        except ValueError as exc:
            raise RunLogError(f"{context} must be an ISO-8601 UTC timestamp") from exc
    else:
        raise RunLogError(f"{context} must be an ISO-8601 UTC timestamp")
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise RunLogError(f"{context} must use UTC")
    parsed = parsed.astimezone(dt.timezone.utc)
    timespec = "microseconds" if parsed.microsecond else "seconds"
    return parsed.isoformat(timespec=timespec).replace("+00:00", "Z")


@dataclass(frozen=True)
class ArtifactReference:
    artifact_id: str
    artifact_bytes: int
    artifact_sha256: str

    @classmethod
    def from_source_record(cls, value: SourceRecord) -> "ArtifactReference":
        if not isinstance(value, SourceRecord):
            raise RunLogError("artifact reference source must be a SourceRecord")
        return cls(value.artifact_id, value.bytes, value.sha256)

    @classmethod
    def from_mapping(
        cls,
        value: Any,
        context: str = "artifact reference",
    ) -> "ArtifactReference":
        row = _object(value, context)
        required = {"artifact_id", "artifact_bytes", "artifact_sha256"}
        _keys(row, required=required, optional=set(), context=context)
        return cls(
            artifact_id=_identifier(row["artifact_id"], f"{context}.artifact_id"),
            artifact_bytes=_integer(
                row["artifact_bytes"], f"{context}.artifact_bytes", minimum=0
            ),
            artifact_sha256=_digest(
                row["artifact_sha256"], f"{context}.artifact_sha256"
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_bytes": self.artifact_bytes,
            "artifact_sha256": self.artifact_sha256,
        }


def _artifact_reference(value: ArtifactReference | SourceRecord) -> ArtifactReference:
    if isinstance(value, ArtifactReference):
        return ArtifactReference.from_mapping(value.to_dict())
    return ArtifactReference.from_source_record(value)


@dataclass(frozen=True)
class PhaseRecord:
    sequence: int
    record_id: str
    phase_id: str
    status: str
    recorded_at: str
    artifacts: tuple[ArtifactReference, ...]
    detail: str | None = None

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        phase_id: str,
        status: str,
        recorded_at: str | dt.datetime,
        artifacts: Iterable[ArtifactReference | SourceRecord] = (),
        detail: str | None = None,
    ) -> "PhaseRecord":
        sequence = _integer(sequence, "phase sequence", minimum=1)
        references = tuple(_artifact_reference(item) for item in artifacts)
        artifact_ids = [item.artifact_id for item in references]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise RunLogError("phase artifacts must not repeat an artifact id")
        return cls(
            sequence=sequence,
            record_id=f"phase-{sequence:06d}",
            phase_id=_identifier(phase_id, "phase_id"),
            status=_status(status, PHASE_STATUSES, "phase status"),
            recorded_at=_utc_timestamp(recorded_at, "phase recorded_at"),
            artifacts=references,
            detail=None if detail is None else _text(detail, "phase detail"),
        )

    @classmethod
    def from_mapping(cls, value: Any, context: str = "phase record") -> "PhaseRecord":
        row = _object(value, context)
        required = {
            "sequence",
            "id",
            "phase_id",
            "status",
            "recorded_at",
            "artifacts",
        }
        _keys(row, required=required, optional={"detail"}, context=context)
        raw_artifacts = row["artifacts"]
        if not isinstance(raw_artifacts, list):
            raise RunLogError(f"{context}.artifacts must be an array")
        record = cls.create(
            sequence=row["sequence"],
            phase_id=row["phase_id"],
            status=row["status"],
            recorded_at=row["recorded_at"],
            artifacts=(
                ArtifactReference.from_mapping(item, f"{context}.artifacts[{index}]")
                for index, item in enumerate(raw_artifacts)
            ),
            detail=row.get("detail"),
        )
        if row["id"] != record.record_id:
            raise RunLogError(
                f"{context}.id must be {record.record_id!r} for its sequence"
            )
        return record

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "sequence": self.sequence,
            "id": self.record_id,
            "phase_id": self.phase_id,
            "status": self.status,
            "recorded_at": self.recorded_at,
            "artifacts": [item.to_dict() for item in self.artifacts],
        }
        if self.detail is not None:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True)
class AutomatedAuditRecord:
    sequence: int
    record_id: str
    check_id: str
    status: str
    recorded_at: str
    subject: ArtifactReference
    report: ArtifactReference

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        check_id: str,
        status: str,
        recorded_at: str | dt.datetime,
        subject: ArtifactReference | SourceRecord,
        report: ArtifactReference | SourceRecord,
    ) -> "AutomatedAuditRecord":
        sequence = _integer(sequence, "audit sequence", minimum=1)
        return cls(
            sequence=sequence,
            record_id=f"audit-{sequence:06d}",
            check_id=_identifier(check_id, "check_id"),
            status=_status(status, AUDIT_STATUSES, "audit status"),
            recorded_at=_utc_timestamp(recorded_at, "audit recorded_at"),
            subject=_artifact_reference(subject),
            report=_artifact_reference(report),
        )

    @classmethod
    def from_mapping(
        cls,
        value: Any,
        context: str = "automated audit record",
    ) -> "AutomatedAuditRecord":
        row = _object(value, context)
        required = {
            "sequence",
            "id",
            "check_id",
            "status",
            "recorded_at",
            "subject",
            "report",
        }
        _keys(row, required=required, optional=set(), context=context)
        record = cls.create(
            sequence=row["sequence"],
            check_id=row["check_id"],
            status=row["status"],
            recorded_at=row["recorded_at"],
            subject=ArtifactReference.from_mapping(
                row["subject"], f"{context}.subject"
            ),
            report=ArtifactReference.from_mapping(
                row["report"], f"{context}.report"
            ),
        )
        if row["id"] != record.record_id:
            raise RunLogError(
                f"{context}.id must be {record.record_id!r} for its sequence"
            )
        return record

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "id": self.record_id,
            "check_id": self.check_id,
            "status": self.status,
            "recorded_at": self.recorded_at,
            "subject": self.subject.to_dict(),
            "report": self.report.to_dict(),
        }


def _artifact_map(run: RunManifest) -> dict[str, SourceRecord]:
    return {item.artifact_id: item for item in run.artifacts}


def _verify_reference(
    reference: ArtifactReference,
    artifacts: Mapping[str, SourceRecord],
    context: str,
) -> None:
    artifact = artifacts.get(reference.artifact_id)
    if artifact is None:
        raise RunLogError(
            f"{context} references missing artifact {reference.artifact_id!r}"
        )
    if (reference.artifact_bytes, reference.artifact_sha256) != (
        artifact.bytes,
        artifact.sha256,
    ):
        raise RunLogError(
            f"{context} does not match artifact bytes and SHA-256 for "
            f"{reference.artifact_id!r}"
        )


def phase_records_from_run(run: RunManifest) -> tuple[PhaseRecord, ...]:
    artifacts = _artifact_map(run)
    result: list[PhaseRecord] = []
    for index, raw in enumerate(run.phase_history, start=1):
        record = PhaseRecord.from_mapping(raw, f"phase_history[{index - 1}]")
        if record.sequence != index:
            raise RunLogError("phase_history must be an ordered gap-free sequence")
        for artifact_index, reference in enumerate(record.artifacts):
            _verify_reference(
                reference,
                artifacts,
                f"phase_history[{index - 1}].artifacts[{artifact_index}]",
            )
        result.append(record)
    return tuple(result)


def automated_audit_records_from_run(
    run: RunManifest,
) -> tuple[AutomatedAuditRecord, ...]:
    artifacts = _artifact_map(run)
    result: list[AutomatedAuditRecord] = []
    for index, raw in enumerate(run.audits, start=1):
        record = AutomatedAuditRecord.from_mapping(
            raw, f"audits[{index - 1}]"
        )
        if record.sequence != index:
            raise RunLogError("audits must be an ordered gap-free sequence")
        _verify_reference(record.subject, artifacts, f"audits[{index - 1}].subject")
        _verify_reference(record.report, artifacts, f"audits[{index - 1}].report")
        result.append(record)
    return tuple(result)


def _native_run(run_path: Path) -> tuple[Any, RunManifest]:
    loaded = load_document(run_path, check_files=True)
    if loaded.run is None:
        raise RunLogError("runlog writes require a native RunManifest")
    phase_records_from_run(loaded.run)
    automated_audit_records_from_run(loaded.run)
    return loaded, loaded.run


def _source_records(
    run: RunManifest,
    artifact_ids: Iterable[str],
    context: str,
) -> tuple[SourceRecord, ...]:
    requested = tuple(_identifier(item, f"{context} artifact id") for item in artifact_ids)
    if len(requested) != len(set(requested)):
        raise RunLogError(f"{context} artifact ids must be unique")
    artifacts = _artifact_map(run)
    missing = [artifact_id for artifact_id in requested if artifact_id not in artifacts]
    if missing:
        raise RunLogError(
            f"{context} references missing artifacts: {', '.join(missing)}"
        )
    return tuple(artifacts[artifact_id] for artifact_id in requested)


def append_phase_record(
    run_path: Path,
    *,
    phase_id: str,
    status: str,
    artifact_ids: Iterable[str] = (),
    detail: str | None = None,
    recorded_at: str | dt.datetime | None = None,
) -> PhaseRecord:
    """Append one typed phase fact through the public atomic core seam."""

    loaded, run = _native_run(run_path)
    record = PhaseRecord.create(
        sequence=len(run.phase_history) + 1,
        phase_id=phase_id,
        status=status,
        recorded_at=_utc_timestamp(recorded_at, "phase recorded_at"),
        artifacts=_source_records(run, artifact_ids, "phase"),
        detail=detail,
    )
    updated = _append_run_records(
        loaded.path,
        phase_records=[record.to_dict()],
    )
    return phase_records_from_run(updated)[-1]


def append_automated_audit_record(
    run_path: Path,
    *,
    check_id: str,
    status: str,
    subject_artifact_id: str,
    report_artifact_id: str,
    recorded_at: str | dt.datetime | None = None,
) -> AutomatedAuditRecord:
    """Append one automated result; this API cannot create human sign-off."""

    loaded, run = _native_run(run_path)
    subject, report = _source_records(
        run,
        (subject_artifact_id, report_artifact_id),
        "automated audit",
    )
    record = AutomatedAuditRecord.create(
        sequence=len(run.audits) + 1,
        check_id=check_id,
        status=status,
        recorded_at=_utc_timestamp(recorded_at, "audit recorded_at"),
        subject=subject,
        report=report,
    )
    updated = _append_run_records(
        loaded.path,
        audit_records=[record.to_dict()],
    )
    return automated_audit_records_from_run(updated)[-1]


__all__ = [
    "AUDIT_STATUSES",
    "PHASE_STATUSES",
    "ArtifactReference",
    "AutomatedAuditRecord",
    "PhaseRecord",
    "RunLogError",
    "append_automated_audit_record",
    "append_phase_record",
    "automated_audit_records_from_run",
    "phase_records_from_run",
]
