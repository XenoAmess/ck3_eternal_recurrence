"""Deterministic evidence plans and hash-bound external evidence bundles.

This module deliberately does not extract frames or run OCR.  It records which
external adapter/tool is expected to produce each artifact, then binds the
files that adapter produced by byte count and SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

from .errors import ArtifactError, ManifestError
from .model import SourceRecord


FORMAT_VERSION = 1
PLAN_KIND = "xar_promo_evidence_plan"
BUNDLE_KIND = "xar_promo_evidence_bundle"
TIMESTAMP_QUANTUM = Decimal("0.000001")
REQUIRED_EVIDENCE_ROLES = ("frame", "ocr")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_PRODUCER_FIELDS = {
    "adapter_id",
    "tool",
    "tool_version",
    "operation",
    "execution",
}


class EvidenceError(ArtifactError):
    """Evidence is absent, stale, or does not satisfy its declared plan."""


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{context} must be an object")
    return value


def _array(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceError(f"{context} must be an array")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{context} must be a non-empty string")
    return value.strip()


def _identifier(value: Any, context: str) -> str:
    result = _string(value, context)
    if _IDENTIFIER.fullmatch(result) is None:
        raise EvidenceError(
            f"{context} must be a portable identifier containing only "
            "letters, digits, '.', '_' or '-'"
        )
    return result


def _only_keys(value: Mapping[str, Any], allowed: set[str], context: str) -> None:
    extras = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if extras:
        raise EvidenceError(f"{context} has unsupported fields: {', '.join(extras)}")
    if missing:
        raise EvidenceError(f"{context} is missing fields: {', '.join(missing)}")


def _decimal(value: Any, context: str) -> Decimal:
    if isinstance(value, bool):
        raise EvidenceError(f"{context} must be a finite non-negative number")
    try:
        result = Decimal(str(value)).quantize(TIMESTAMP_QUANTUM, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise EvidenceError(f"{context} must be a finite non-negative number") from exc
    if not result.is_finite() or result < 0:
        raise EvidenceError(f"{context} must be a finite non-negative number")
    return result


def _timestamp(value: Decimal) -> str:
    return f"{value:.6f}"


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
        raise EvidenceError(f"{context} was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceError(
            f"invalid JSON in {context}: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise EvidenceError(f"could not read {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{context} JSON root must be an object")
    return value


def _write_new_json(path: Path, value: Mapping[str, Any], context: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise EvidenceError(f"refusing to overwrite existing {context}: {path}") from exc
    except OSError as exc:
        raise EvidenceError(f"could not write {context} {path}: {exc}") from exc


def normalize_external_producer(value: Any, context: str = "producer") -> dict[str, str]:
    """Validate metadata for a tool invocation performed outside this module."""

    row = _object(value, context)
    _only_keys(row, _PRODUCER_FIELDS, context)
    result = {key: _string(row.get(key), f"{context}.{key}") for key in sorted(_PRODUCER_FIELDS)}
    if result["execution"] != "external":
        raise EvidenceError(f"{context}.execution must be 'external'")
    return result


def make_source_record(
    path: Path,
    *,
    project_root: Path,
    artifact_id: str,
    collection: str,
    role: str,
    label: str,
    media_type: str | None = None,
    source_name: str | None = None,
) -> SourceRecord:
    """Create a core ``SourceRecord`` bound to existing bytes under a project root."""

    root = project_root.resolve()
    canonical = path.resolve()
    if not canonical.is_file():
        raise EvidenceError(f"artifact was not found: {canonical}")
    try:
        relative = canonical.relative_to(root).as_posix()
    except ValueError as exc:
        raise EvidenceError(f"artifact must be inside project root {root}: {canonical}") from exc
    payload: dict[str, Any] = {
        "id": artifact_id,
        "collection": collection,
        "role": role,
        "path": relative,
        "label": label,
        "bytes": canonical.stat().st_size,
        "sha256": _sha256_file(canonical),
    }
    if media_type is not None:
        payload["media_type"] = media_type
    if source_name is not None:
        payload["source_name"] = source_name
    try:
        return SourceRecord.from_mapping(payload, artifact_id)
    except ManifestError as exc:
        raise EvidenceError(str(exc)) from exc


def verify_source_record(
    value: SourceRecord | Mapping[str, Any],
    *,
    project_root: Path,
    context: str = "artifact",
) -> SourceRecord:
    """Verify that a record still names the exact file bytes it was bound to."""

    try:
        record = value if isinstance(value, SourceRecord) else SourceRecord.from_mapping(value, context)
    except ManifestError as exc:
        raise EvidenceError(str(exc)) from exc
    path = (project_root.resolve() / Path(record.path)).resolve()
    if not path.is_file():
        raise EvidenceError(f"{context} was not found: {path}")
    if path.stat().st_size != record.bytes:
        raise EvidenceError(f"{context} byte count does not match its binding")
    if _sha256_file(path) != record.sha256:
        raise EvidenceError(f"{context} SHA-256 does not match its binding")
    return record


def bind_external_artifact(
    path: Path,
    *,
    project_root: Path,
    artifact_id: str,
    collection: str,
    role: str,
    label: str,
    media_type: str,
    producer: Mapping[str, Any],
    source_name: str | None = None,
) -> dict[str, Any]:
    """Record bytes plus the external adapter/tool that produced them."""

    return {
        "artifact": make_source_record(
            path,
            project_root=project_root,
            artifact_id=artifact_id,
            collection=collection,
            role=role,
            label=label,
            media_type=media_type,
            source_name=source_name,
        ).to_dict(),
        "producer": normalize_external_producer(producer),
    }


def verify_external_binding(
    value: Any,
    *,
    project_root: Path,
    context: str,
) -> dict[str, Any]:
    row = _object(value, context)
    _only_keys(row, {"artifact", "producer"}, context)
    record = verify_source_record(row["artifact"], project_root=project_root, context=f"{context}.artifact")
    return {
        "artifact": record.to_dict(),
        "producer": normalize_external_producer(row["producer"], f"{context}.producer"),
    }


def deterministic_timestamps(start_seconds: Any, end_seconds: Any, interval_seconds: Any) -> list[str]:
    """Return stable six-decimal samples, always including both endpoints."""

    start = _decimal(start_seconds, "start_seconds")
    end = _decimal(end_seconds, "end_seconds")
    interval = _decimal(interval_seconds, "interval_seconds")
    if interval <= 0:
        raise EvidenceError("interval_seconds must be greater than zero")
    if end < start:
        raise EvidenceError("end_seconds must be greater than or equal to start_seconds")
    result = [start]
    cursor = start + interval
    while cursor < end:
        result.append(cursor)
        cursor += interval
    if result[-1] != end:
        result.append(end)
    return [_timestamp(item) for item in result]


def _normalize_chapters(
    chapters: Iterable[Mapping[str, Any]],
    *,
    project_root: Path,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(chapters):
        row = _object(raw, f"chapters[{index}]")
        _only_keys(row, {"id", "kind", "source", "start_seconds", "end_seconds"}, f"chapters[{index}]")
        chapter_id = _identifier(row["id"], f"chapters[{index}].id")
        kind = _string(row["kind"], f"chapters[{index}].kind")
        if kind not in {"video", "still"}:
            raise EvidenceError(f"chapters[{index}].kind must be video or still")
        start = _decimal(row["start_seconds"], f"chapters[{index}].start_seconds")
        end = _decimal(row["end_seconds"], f"chapters[{index}].end_seconds")
        if end < start:
            raise EvidenceError(f"chapters[{index}] ends before it starts")
        result.append(
            {
                "id": chapter_id,
                "kind": kind,
                "source": verify_external_binding(
                    row["source"], project_root=project_root, context=f"chapters[{index}].source"
                ),
                "start_seconds": _timestamp(start),
                "end_seconds": _timestamp(end),
            }
        )
    result.sort(key=lambda item: item["id"])
    ids = [item["id"] for item in result]
    if len(ids) != len(set(ids)):
        raise EvidenceError("chapters contains duplicate ids")
    if not result:
        raise EvidenceError("chapters must contain at least one chapter")
    return result


def _assemble_plan(
    chapters: list[dict[str, Any]],
    interval: Decimal,
    frame_producer: dict[str, str],
    ocr_producer: dict[str, str],
) -> dict[str, Any]:
    groups: dict[tuple[str, str], dict[str, set[str]]] = {}
    for chapter in chapters:
        artifact = chapter["source"]["artifact"]
        timestamps = (
            [_timestamp(_decimal(chapter["start_seconds"], "chapter start"))]
            if chapter["kind"] == "still"
            else deterministic_timestamps(chapter["start_seconds"], chapter["end_seconds"], interval)
        )
        for timestamp in timestamps:
            key = (artifact["sha256"], timestamp)
            group = groups.setdefault(key, {"chapter_ids": set(), "source_artifact_ids": set()})
            group["chapter_ids"].add(chapter["id"])
            group["source_artifact_ids"].add(artifact["id"])
    ordered = sorted(groups.items(), key=lambda item: (item[0][0], Decimal(item[0][1])))
    samples = []
    for index, ((source_sha256, timestamp), group) in enumerate(ordered, start=1):
        samples.append(
            {
                "id": f"sample-{index:06d}",
                "source_sha256": source_sha256,
                "timestamp_seconds": timestamp,
                "chapter_ids": sorted(group["chapter_ids"]),
                "source_artifact_ids": sorted(group["source_artifact_ids"]),
            }
        )
    return {
        "format_version": FORMAT_VERSION,
        "kind": PLAN_KIND,
        "sampling": {
            "interval_seconds": _timestamp(interval),
            "timestamp_precision_decimal_places": 6,
            "endpoint_policy": "include-start-and-end",
            "deduplication_key": ["source_sha256", "timestamp_seconds"],
            "required_roles": list(REQUIRED_EVIDENCE_ROLES),
            "external_producers": {
                "frame": frame_producer,
                "ocr": ocr_producer,
            },
        },
        "chapters": chapters,
        "samples": samples,
    }


def build_sampling_plan(
    chapters: Iterable[Mapping[str, Any]],
    *,
    project_root: Path,
    interval_seconds: Any,
    frame_producer: Mapping[str, Any],
    ocr_producer: Mapping[str, Any],
) -> dict[str, Any]:
    """Build deterministic metadata; this function does no media processing."""

    interval = _decimal(interval_seconds, "interval_seconds")
    if interval <= 0:
        raise EvidenceError("interval_seconds must be greater than zero")
    normalized = _normalize_chapters(chapters, project_root=project_root)
    return _assemble_plan(
        normalized,
        interval,
        normalize_external_producer(frame_producer, "frame_producer"),
        normalize_external_producer(ocr_producer, "ocr_producer"),
    )


def validate_sampling_plan(value: Any, *, project_root: Path) -> dict[str, Any]:
    row = _object(value, "evidence plan")
    _only_keys(row, {"format_version", "kind", "sampling", "chapters", "samples"}, "evidence plan")
    if row["format_version"] != FORMAT_VERSION or row["kind"] != PLAN_KIND:
        raise EvidenceError("evidence plan must declare xar_promo_evidence_plan format v1")
    sampling = _object(row["sampling"], "sampling")
    _only_keys(
        sampling,
        {
            "interval_seconds",
            "timestamp_precision_decimal_places",
            "endpoint_policy",
            "deduplication_key",
            "required_roles",
            "external_producers",
        },
        "sampling",
    )
    if sampling["timestamp_precision_decimal_places"] != 6:
        raise EvidenceError("sampling timestamp precision must be six decimal places")
    if sampling["endpoint_policy"] != "include-start-and-end":
        raise EvidenceError("sampling endpoint policy is unsupported")
    if sampling["deduplication_key"] != ["source_sha256", "timestamp_seconds"]:
        raise EvidenceError("sampling deduplication key is unsupported")
    if sampling["required_roles"] != list(REQUIRED_EVIDENCE_ROLES):
        raise EvidenceError("sampling must require frame and ocr evidence")
    producers = _object(sampling["external_producers"], "sampling.external_producers")
    _only_keys(producers, set(REQUIRED_EVIDENCE_ROLES), "sampling.external_producers")
    interval = _decimal(sampling["interval_seconds"], "sampling.interval_seconds")
    if interval <= 0:
        raise EvidenceError("sampling.interval_seconds must be greater than zero")
    normalized = _normalize_chapters(_array(row["chapters"], "chapters"), project_root=project_root)
    expected = _assemble_plan(
        normalized,
        interval,
        normalize_external_producer(producers["frame"], "sampling.external_producers.frame"),
        normalize_external_producer(producers["ocr"], "sampling.external_producers.ocr"),
    )
    if row != expected:
        raise EvidenceError("evidence plan does not match its deterministic sampling metadata")
    return expected


def write_sampling_plan(
    path: Path,
    chapters: Iterable[Mapping[str, Any]],
    *,
    project_root: Path,
    interval_seconds: Any,
    frame_producer: Mapping[str, Any],
    ocr_producer: Mapping[str, Any],
) -> dict[str, Any]:
    plan = build_sampling_plan(
        chapters,
        project_root=project_root,
        interval_seconds=interval_seconds,
        frame_producer=frame_producer,
        ocr_producer=ocr_producer,
    )
    _write_new_json(path, plan, "evidence plan")
    return plan


def load_sampling_plan(path: Path, *, project_root: Path) -> dict[str, Any]:
    return validate_sampling_plan(_read_json_object(path, "evidence plan"), project_root=project_root)


def write_evidence_bundle(
    path: Path,
    *,
    project_root: Path,
    plan_path: Path,
    submissions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind externally generated frame/OCR files to every planned sample."""

    plan = load_sampling_plan(plan_path, project_root=project_root)
    plan_record = make_source_record(
        plan_path,
        project_root=project_root,
        artifact_id="evidence-plan",
        collection="derived",
        role="evidence-plan",
        label="Deterministic evidence sampling plan",
        media_type="application/json",
    )
    expected = {
        (sample["id"], role)
        for sample in plan["samples"]
        for role in REQUIRED_EVIDENCE_ROLES
    }
    supplied: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw in enumerate(submissions):
        row = _object(raw, f"submissions[{index}]")
        _only_keys(row, {"sample_id", "role", "path", "media_type", "producer"}, f"submissions[{index}]")
        sample_id = _identifier(row["sample_id"], f"submissions[{index}].sample_id")
        role = _string(row["role"], f"submissions[{index}].role")
        key = (sample_id, role)
        if key not in expected:
            raise EvidenceError(f"unexpected evidence submission for {sample_id}/{role}")
        if key in supplied:
            raise EvidenceError(f"duplicate evidence submission for {sample_id}/{role}")
        producer = normalize_external_producer(row["producer"], f"submissions[{index}].producer")
        required_producer = plan["sampling"]["external_producers"][role]
        if producer != required_producer:
            raise EvidenceError(f"producer metadata does not match the plan for role {role}")
        artifact_path = Path(row["path"])
        supplied[key] = {
            "sample_id": sample_id,
            "role": role,
            "binding": bind_external_artifact(
                artifact_path,
                project_root=project_root,
                artifact_id=f"{sample_id}-{role}",
                collection="derived",
                role=role,
                label=f"{sample_id} {role} evidence",
                media_type=_string(row["media_type"], f"submissions[{index}].media_type"),
                producer=producer,
            ),
        }
    missing = sorted(expected - set(supplied))
    if missing:
        formatted = ", ".join(f"{sample_id}/{role}" for sample_id, role in missing)
        raise EvidenceError(f"required evidence is missing: {formatted}")
    bundle = {
        "format_version": FORMAT_VERSION,
        "kind": BUNDLE_KIND,
        "plan": plan_record.to_dict(),
        "entries": [supplied[key] for key in sorted(supplied)],
    }
    _write_new_json(path, bundle, "evidence bundle")
    return bundle


def load_evidence_bundle(path: Path, *, project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reverify the bundle, its plan, all sources, and every evidence artifact."""

    row = _read_json_object(path, "evidence bundle")
    _only_keys(row, {"format_version", "kind", "plan", "entries"}, "evidence bundle")
    if row["format_version"] != FORMAT_VERSION or row["kind"] != BUNDLE_KIND:
        raise EvidenceError("evidence bundle must declare xar_promo_evidence_bundle format v1")
    plan_record = verify_source_record(row["plan"], project_root=project_root, context="evidence bundle plan")
    if plan_record.role != "evidence-plan":
        raise EvidenceError("evidence bundle plan record has the wrong role")
    plan_path = project_root.resolve() / Path(plan_record.path)
    plan = load_sampling_plan(plan_path, project_root=project_root)
    samples = {sample["id"]: sample for sample in plan["samples"]}
    expected = {(sample_id, role) for sample_id in samples for role in REQUIRED_EVIDENCE_ROLES}
    seen: set[tuple[str, str]] = set()
    normalized_entries: list[dict[str, Any]] = []
    for index, raw in enumerate(_array(row["entries"], "entries")):
        entry = _object(raw, f"entries[{index}]")
        _only_keys(entry, {"sample_id", "role", "binding"}, f"entries[{index}]")
        sample_id = _identifier(entry["sample_id"], f"entries[{index}].sample_id")
        role = _string(entry["role"], f"entries[{index}].role")
        key = (sample_id, role)
        if key not in expected:
            raise EvidenceError(f"unexpected evidence entry for {sample_id}/{role}")
        if key in seen:
            raise EvidenceError(f"duplicate evidence entry for {sample_id}/{role}")
        binding = verify_external_binding(
            entry["binding"], project_root=project_root, context=f"entries[{index}].binding"
        )
        artifact = binding["artifact"]
        if artifact["role"] != role:
            raise EvidenceError(f"evidence entry {sample_id}/{role} has a mismatched artifact role")
        if binding["producer"] != plan["sampling"]["external_producers"][role]:
            raise EvidenceError(f"evidence entry {sample_id}/{role} has unplanned producer metadata")
        seen.add(key)
        normalized_entries.append({"sample_id": sample_id, "role": role, "binding": binding})
    missing = sorted(expected - seen)
    if missing:
        formatted = ", ".join(f"{sample_id}/{role}" for sample_id, role in missing)
        raise EvidenceError(f"required evidence is missing: {formatted}")
    normalized = {
        "format_version": FORMAT_VERSION,
        "kind": BUNDLE_KIND,
        "plan": plan_record.to_dict(),
        "entries": sorted(normalized_entries, key=lambda item: (item["sample_id"], item["role"])),
    }
    if row != normalized:
        raise EvidenceError("evidence bundle is not in canonical deterministic order")
    return normalized, plan
