"""Create configs/runs and append immutable run evidence."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import ArtifactError, ManifestError, SignoffError
from .model import ConfigBinding, RunManifest, SignoffRecord, SourceRecord, new_project_config, new_run_manifest
from .project import load_document, sha256_file


PROJECT_CONFIG_NAME = "promo-project.json"
DEFAULT_RUN_ID = "run-0001"
DEFAULT_RUN_MANIFEST = Path("runs") / DEFAULT_RUN_ID / "run-manifest.json"


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _write_exclusive(path: Path, payload: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return True
    except FileExistsError:
        return False


def _replace_run(path: Path, old: RunManifest, new: RunManifest) -> None:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest().upper()
    history = path.parent / old.artifact_policy.manifest_history_directory / "sha256" / digest[:2] / f"{digest}.json"
    if not _write_exclusive(history, payload) and history.read_bytes() != payload:
        raise ArtifactError(f"manifest history collision at {history}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_bytes(_json_bytes(new.to_dict()))
    os.replace(temporary, path)


def initialize_project(
    directory: Path,
    *,
    project_id: str,
    title: str,
    narration_locale: str,
    subtitle_locales: list[str],
    adapter: str,
    preset: str,
    run_id: str,
) -> tuple[Path, Path]:
    new_run_manifest(
        run_id,
        ConfigBinding("project-config.json", 0, "0" * 64),
    )
    root = directory.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / PROJECT_CONFIG_NAME
    run_path = root / "runs" / run_id / "run-manifest.json"
    if config_path.exists() or run_path.exists():
        raise ManifestError("refusing to overwrite an existing project config or run manifest")
    config = new_project_config(project_id, title, narration_locale, subtitle_locales, adapter, preset)
    config_payload = _json_bytes(config.to_dict())
    if not _write_exclusive(config_path, config_payload):
        raise ManifestError(f"refusing to overwrite existing project config: {config_path}")
    created_run = start_run(config_path, run_id=run_id, run_directory=run_path.parent)
    return config_path, created_run


def start_run(
    config_path: Path,
    *,
    run_id: str,
    run_directory: Path | None = None,
) -> Path:
    """Create a new run bound to the current exact ProjectConfig bytes."""

    new_run_manifest(
        run_id,
        ConfigBinding("project-config.json", 0, "0" * 64),
    )
    config_path = config_path.expanduser().resolve()
    loaded = load_document(config_path, check_files=True)
    if loaded.config is None:
        raise ManifestError("start-run requires a native ProjectConfig")
    run_root = (
        run_directory.expanduser().resolve()
        if run_directory is not None
        else config_path.parent / "runs" / run_id
    )
    run_path = run_root / "run-manifest.json"
    if run_path.exists():
        raise ManifestError(f"refusing to overwrite existing run manifest: {run_path}")
    config_payload = config_path.read_bytes()
    config_digest = hashlib.sha256(config_payload).hexdigest().upper()
    snapshot_path = (
        run_root
        / "artifacts"
        / "project-config"
        / "sha256"
        / config_digest[:2]
        / f"{config_digest}.json"
    )
    if not _write_exclusive(snapshot_path, config_payload):
        if snapshot_path.read_bytes() != config_payload:
            raise ArtifactError(f"project-config snapshot collision at {snapshot_path}")
    relative = os.path.relpath(snapshot_path, run_path.parent).replace("\\", "/")
    binding = ConfigBinding(
        relative,
        len(config_payload),
        config_digest,
    )
    run = new_run_manifest(run_id, binding)
    for name in (
        run.artifact_policy.raw_directory,
        run.artifact_policy.derived_directory,
        run.artifact_policy.manifest_history_directory,
    ):
        (run_path.parent / name).mkdir(parents=True, exist_ok=True)
    if not _write_exclusive(run_path, _json_bytes(run.to_dict())):
        raise ManifestError(f"refusing to overwrite existing run manifest: {run_path}")
    return run_path


def _suffix(path: Path) -> str:
    return re.sub(r"[^a-z0-9.]", "", "".join(path.suffixes).lower())[:32] or ".bin"


def preserve_artifact(
    run_path: Path,
    source: Path,
    *,
    artifact_id: str,
    collection: str,
    role: str,
    label: str | None,
    media_type: str | None,
) -> SourceRecord:
    if collection not in {"raw", "derived"}:
        raise ArtifactError("collection must be raw or derived")
    loaded = load_document(run_path, check_files=True)
    if loaded.run is None:
        raise ManifestError("preserve requires a native run manifest")
    run = loaded.run
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ArtifactError(f"source file was not found: {source}")
    digest, size = sha256_file(source), source.stat().st_size
    base = run.artifact_policy.raw_directory if collection == "raw" else run.artifact_policy.derived_directory
    relative = Path(base) / "sha256" / digest[:2] / f"{digest}{_suffix(source)}"
    destination = loaded.path.parent / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.stat().st_size != size or sha256_file(destination) != digest:
            raise ArtifactError(f"refusing to overwrite conflicting artifact: {destination}")
    else:
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer, 1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        if destination.stat().st_size != size or sha256_file(destination) != digest:
            raise ArtifactError(f"artifact failed post-copy verification: {destination}")
    record = SourceRecord.from_mapping(
        {
            "id": artifact_id,
            "collection": collection,
            "role": role,
            "path": relative.as_posix(),
            "label": label or source.name,
            "bytes": size,
            "sha256": digest,
            "media_type": media_type or mimetypes.guess_type(source.name)[0] or "application/octet-stream",
            "source_name": source.name,
        },
        "artifact",
    )
    existing = next((item for item in run.artifacts if item.artifact_id == record.artifact_id), None)
    if existing is not None:
        if existing == record:
            return existing
        raise ArtifactError(f"artifact id {artifact_id!r} is already bound to different metadata")
    updated = RunManifest(run.run_id, run.project_config, run.artifact_policy, run.phase_history, run.artifacts + (record,), run.audits, run.signoffs)
    RunManifest.from_mapping(updated.to_dict())
    _replace_run(loaded.path, run, updated)
    return record


def record_signoff(
    run_path: Path,
    *,
    artifact_id: str,
    reviewer: str,
    decision: str,
    note: str | None,
    reviewed_at: str | None,
) -> SignoffRecord:
    loaded = load_document(run_path, check_files=True)
    if loaded.run is None:
        raise ManifestError("signoff writes only to a native run manifest")
    run = loaded.run
    artifact = next((item for item in run.artifacts if item.artifact_id == artifact_id), None)
    if artifact is None:
        raise SignoffError(f"artifact id was not found: {artifact_id}")
    if not reviewer.strip() or decision not in {"approved", "rejected"}:
        raise SignoffError("reviewer must be non-empty and decision approved or rejected")
    sequence = len(run.signoffs) + 1
    timestamp = reviewed_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    record = SignoffRecord.from_mapping(
        {
            "sequence": sequence,
            "id": f"signoff-{sequence:06d}",
            "artifact_id": artifact.artifact_id,
            "artifact_bytes": artifact.bytes,
            "artifact_sha256": artifact.sha256,
            "reviewer": reviewer.strip(),
            "decision": decision,
            "reviewed_at": timestamp,
            **({"note": note} if note else {}),
        },
        "signoff",
    )
    updated = RunManifest(run.run_id, run.project_config, run.artifact_policy, run.phase_history, run.artifacts, run.audits, run.signoffs + (record,))
    RunManifest.from_mapping(updated.to_dict())
    _replace_run(loaded.path, run, updated)
    return record


def _append_run_records(
    run_path: Path,
    *,
    phase_records: Sequence[Mapping[str, Any]] = (),
    audit_records: Sequence[Mapping[str, Any]] = (),
) -> RunManifest:
    """Internal atomic append primitive for the typed :mod:`xar_promo.runlog` API.

    Callers supply record bodies; this seam owns sequence assignment, complete
    RunManifest validation, content-addressed history, and atomic replacement.
    It never appends artifacts or human sign-offs, which retain their narrower
    dedicated operations.
    """

    if not phase_records and not audit_records:
        raise ManifestError("_append_run_records requires at least one new record")
    loaded = load_document(run_path, check_files=True)
    if loaded.run is None:
        raise ManifestError("_append_run_records requires a native run manifest")
    run = loaded.run

    def sequenced(
        existing: tuple[dict[str, Any], ...],
        additions: Sequence[Mapping[str, Any]],
        label: str,
    ) -> tuple[dict[str, Any], ...]:
        rows = list(existing)
        for offset, raw in enumerate(additions, start=1):
            if not isinstance(raw, Mapping):
                raise ManifestError(f"{label} append row {offset} must be an object")
            row = dict(raw)
            expected = len(rows) + 1
            declared = row.get("sequence")
            if declared is not None and declared != expected:
                raise ManifestError(
                    f"{label} append row {offset} sequence must be {expected}"
                )
            row["sequence"] = expected
            rows.append(row)
        return tuple(rows)

    updated = RunManifest(
        run.run_id,
        run.project_config,
        run.artifact_policy,
        sequenced(run.phase_history, phase_records, "phase_history"),
        run.artifacts,
        sequenced(run.audits, audit_records, "audits"),
        run.signoffs,
    )
    RunManifest.from_mapping(updated.to_dict())
    _replace_run(loaded.path, run, updated)
    return updated
