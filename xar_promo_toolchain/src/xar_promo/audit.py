"""Append-only integrity audit reports for externally produced promo evidence.

The automated result covers artifact integrity and evidence completeness only.
It never creates a human approval.  When a native run manifest is supplied,
this module reads an already-recorded sign-off and binds that source document
by SHA-256 in the report.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .errors import ArtifactError, ManifestError
from .evidence import (
    REQUIRED_EVIDENCE_ROLES,
    EvidenceError,
    load_evidence_bundle,
    make_source_record,
    verify_source_record,
)
from .model import RunManifest, SourceRecord


FORMAT_VERSION = 1
REPORT_KIND = "xar_promo_audit_report"
_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")


class AuditError(ArtifactError):
    """An audit report or one of its immutable references is invalid."""


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuditError(f"{context} must be an object")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuditError(f"{context} must be a non-empty string")
    return value.strip()


def _only_keys(value: Mapping[str, Any], allowed: set[str], context: str) -> None:
    extras = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if extras:
        raise AuditError(f"{context} has unsupported fields: {', '.join(extras)}")
    if missing:
        raise AuditError(f"{context} is missing fields: {', '.join(missing)}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_json_object(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise AuditError(f"{context} was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(
            f"invalid JSON in {context}: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise AuditError(f"could not read {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{context} JSON root must be an object")
    return value


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise AuditError(f"refusing to overwrite existing audit report: {path}") from exc
    except OSError as exc:
        raise AuditError(f"could not write audit report {path}: {exc}") from exc


def _coerce_subject(
    value: SourceRecord | Mapping[str, Any], *, project_root: Path
) -> SourceRecord:
    try:
        return verify_source_record(value, project_root=project_root, context="audit subject")
    except EvidenceError as exc:
        raise AuditError(str(exc)) from exc


def _load_run_manifest(path: Path) -> RunManifest:
    raw = _read_json_object(path, "manual sign-off source")
    try:
        return RunManifest.from_mapping(raw)
    except ManifestError as exc:
        raise AuditError(f"manual sign-off source is not a valid run manifest: {exc}") from exc


def read_manual_signoff_state(
    run_manifest_path: Path,
    *,
    project_root: Path,
    subject: SourceRecord | Mapping[str, Any],
) -> dict[str, Any]:
    """Read an explicit core sign-off without creating or changing approval state."""

    subject_record = _coerce_subject(subject, project_root=project_root)
    source_record = make_source_record(
        run_manifest_path,
        project_root=project_root,
        artifact_id="manual-signoff-source",
        collection="derived",
        role="manual-signoff-source",
        label="Immutable source of explicit human sign-off state",
        media_type="application/json",
    )
    run = _load_run_manifest(run_manifest_path)
    matching_artifact_ids = {
        artifact.artifact_id
        for artifact in run.artifacts
        if artifact.bytes == subject_record.bytes and artifact.sha256 == subject_record.sha256
    }
    if not matching_artifact_ids:
        raise AuditError("manual sign-off source does not contain the audited artifact bytes")
    matching_signoffs = [
        signoff for signoff in run.signoffs if signoff.artifact_id in matching_artifact_ids
    ]
    result: dict[str, Any] = {
        "state": "not-recorded",
        "signoff_source": source_record.to_dict(),
    }
    if matching_signoffs:
        latest = max(matching_signoffs, key=lambda item: item.sequence)
        result["state"] = latest.decision
        result["record"] = latest.to_dict()
    return result


def _automated_result(
    subject: SourceRecord,
    bundle_record: SourceRecord,
    bundle: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    producers = sorted(
        {
            (
                entry["binding"]["producer"]["adapter_id"],
                entry["binding"]["producer"]["tool"],
                entry["binding"]["producer"]["tool_version"],
                entry["binding"]["producer"]["operation"],
            )
            for entry in bundle["entries"]
        }
    )
    return {
        "status": "passed",
        "scope": "artifact-integrity-and-evidence-completeness",
        "manual_approval_granted": False,
        "verifier": "xar_promo.audit/1",
        "subject_sha256": subject.sha256,
        "evidence_bundle_sha256": bundle_record.sha256,
        "evidence_plan_sha256": bundle["plan"]["sha256"],
        "sample_count": len(plan["samples"]),
        "evidence_artifact_count": len(bundle["entries"]),
        "required_roles": list(REQUIRED_EVIDENCE_ROLES),
        "external_producers": [
            {
                "adapter_id": adapter_id,
                "tool": tool,
                "tool_version": version,
                "operation": operation,
            }
            for adapter_id, tool, version, operation in producers
        ],
        "checks": [
            "subject-bytes-and-sha256",
            "sampling-plan-bytes-and-sha256",
            "source-bytes-and-sha256",
            "required-frame-and-ocr-coverage",
            "evidence-bytes-and-sha256",
            "external-producer-metadata",
        ],
    }


def write_audit_report(
    path: Path,
    *,
    project_root: Path,
    subject: SourceRecord | Mapping[str, Any],
    evidence_bundle_path: Path,
    signoff_run_manifest_path: Path | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Write one immutable report after all required evidence verifies.

    Missing or stale evidence raises before a report is created.  The automated
    block explicitly cannot grant approval.  Approval appears only when an
    already-existing sign-off in ``signoff_run_manifest_path`` is read.
    """

    subject_record = _coerce_subject(subject, project_root=project_root)
    try:
        bundle, plan = load_evidence_bundle(evidence_bundle_path, project_root=project_root)
        bundle_record = make_source_record(
            evidence_bundle_path,
            project_root=project_root,
            artifact_id="audit-evidence-bundle",
            collection="derived",
            role="evidence-bundle",
            label="Complete hash-bound visual evidence bundle",
            media_type="application/json",
        )
    except EvidenceError as exc:
        raise AuditError(str(exc)) from exc
    manual = (
        {"state": "not-provided"}
        if signoff_run_manifest_path is None
        else read_manual_signoff_state(
            signoff_run_manifest_path,
            project_root=project_root,
            subject=subject_record,
        )
    )
    timestamp = (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        if created_at_utc is None
        else _string(created_at_utc, "created_at_utc")
    )
    report = {
        "format_version": FORMAT_VERSION,
        "kind": REPORT_KIND,
        "created_at_utc": timestamp,
        "subject": subject_record.to_dict(),
        "evidence_bundle": bundle_record.to_dict(),
        "automated_audit": _automated_result(subject_record, bundle_record, bundle, plan),
        "manual_signoff": manual,
    }
    _write_new_json(path, report)
    return report


def verify_audit_report(
    path: Path,
    *,
    project_root: Path,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Re-run every deterministic check and verify all report references."""

    if expected_sha256 is not None:
        digest = _string(expected_sha256, "expected_sha256").upper()
        if _SHA256.fullmatch(digest) is None:
            raise AuditError("expected_sha256 must contain 64 hexadecimal characters")
        if not path.is_file() or _sha256_file(path) != digest:
            raise AuditError("audit report SHA-256 does not match the expected digest")
    row = _read_json_object(path, "audit report")
    _only_keys(
        row,
        {
            "format_version",
            "kind",
            "created_at_utc",
            "subject",
            "evidence_bundle",
            "automated_audit",
            "manual_signoff",
        },
        "audit report",
    )
    if row["format_version"] != FORMAT_VERSION or row["kind"] != REPORT_KIND:
        raise AuditError("audit report must declare xar_promo_audit_report format v1")
    _string(row["created_at_utc"], "created_at_utc")
    subject = _coerce_subject(row["subject"], project_root=project_root)
    try:
        bundle_record = verify_source_record(
            row["evidence_bundle"], project_root=project_root, context="audit evidence bundle"
        )
        if bundle_record.role != "evidence-bundle":
            raise AuditError("audit evidence bundle record has the wrong role")
        bundle_path = project_root.resolve() / Path(bundle_record.path)
        bundle, plan = load_evidence_bundle(bundle_path, project_root=project_root)
    except EvidenceError as exc:
        raise AuditError(str(exc)) from exc
    expected_automated = _automated_result(subject, bundle_record, bundle, plan)
    if row["automated_audit"] != expected_automated:
        raise AuditError("automated audit result does not match current immutable evidence")

    manual = _object(row["manual_signoff"], "manual_signoff")
    state = manual.get("state")
    if state == "not-provided":
        if manual != {"state": "not-provided"}:
            raise AuditError("not-provided manual sign-off cannot contain approval data")
    else:
        if state not in {"not-recorded", "approved", "rejected"}:
            raise AuditError("manual_signoff.state is unsupported")
        source = verify_source_record(
            manual.get("signoff_source"),
            project_root=project_root,
            context="manual sign-off source",
        )
        source_path = project_root.resolve() / Path(source.path)
        expected_manual = read_manual_signoff_state(
            source_path,
            project_root=project_root,
            subject=subject,
        )
        if manual != expected_manual:
            raise AuditError("manual sign-off state does not match its immutable source")
    return row
