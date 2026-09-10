"""Offline, content-addressed access to reviewed vanilla-event evidence.

The checked-in bundle is deliberately independent of a CK3 installation and
of the machine that captured the live observations.  Every payload is keyed by
the SHA-256 of its uncompressed bytes and is verified before it is exposed.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Final
import zlib

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, JsonValue


EVIDENCE_MANIFEST_SCHEMA: Final = (
    "xar.ck3.vanilla-event-portable-evidence-manifest"
)
EVIDENCE_INDEX_SCHEMA: Final = "xar.ck3.vanilla-event-evidence-index"
EVIDENCE_LIST_SCHEMA: Final = "xar.ck3.vanilla-event-evidence-list"
EVIDENCE_READ_SCHEMA: Final = "xar.ck3.vanilla-event-evidence-read"
EVIDENCE_SCHEMA_VERSION: Final = 1
MAX_EVIDENCE_READ_BYTES: Final = 64 * 1024

_BUNDLE_ROOT: Final = Path(__file__).with_name("portable_evidence")
_MANIFEST_PATH: Final = _BUNDLE_ROOT / "manifest_v1.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MEDIA_TYPES: Final = frozenset(
    {
        "application/json",
        "application/yaml; charset=utf-8",
        "image/png",
        "text/plain; charset=utf-8",
    }
)


class EvidenceBundleError(ValueError):
    """Raised internally when checked-in evidence fails its frozen contract."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_clone(value: object) -> JsonValue:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _media_type_for_path(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix == ".json":
        return "application/json"
    if suffix in {".yml", ".yaml"}:
        return "application/yaml; charset=utf-8"
    if suffix == ".png":
        return "image/png"
    if suffix in {".txt", ".gui", ".asset", ".info"}:
        return "text/plain; charset=utf-8"
    raise EvidenceBundleError(f"unsupported evidence media extension: {suffix}")


def _validate_payload_media_type(data: bytes, media_type: str) -> None:
    if media_type not in _MEDIA_TYPES:
        raise EvidenceBundleError("unsupported evidence media type")
    if media_type == "application/json":
        try:
            json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EvidenceBundleError("invalid JSON evidence payload") from exc
        return
    if media_type == "image/png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise EvidenceBundleError("invalid PNG evidence payload")
        return
    try:
        data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise EvidenceBundleError("evidence payload is not UTF-8 text") from exc


def _load_manifest(bundle_root: Path) -> dict[str, object]:
    manifest_path = bundle_root / "manifest_v1.json"
    try:
        raw = manifest_path.read_bytes()
    except OSError as exc:
        raise EvidenceBundleError("portable evidence manifest is unavailable") from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceBundleError("portable evidence manifest is invalid JSON") from exc
    if not isinstance(manifest, dict):
        raise EvidenceBundleError("portable evidence manifest must be an object")
    if set(manifest) != {
        "ck3_build",
        "ck3_exe_sha256",
        "compression",
        "evidence",
        "schema",
        "schema_version",
        "statistics",
    }:
        raise EvidenceBundleError("portable evidence manifest fields mismatch")
    if manifest.get("schema") != EVIDENCE_MANIFEST_SCHEMA:
        raise EvidenceBundleError("portable evidence manifest schema mismatch")
    if manifest.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise EvidenceBundleError("portable evidence manifest version mismatch")
    if manifest.get("ck3_build") != EXACT_CK3_BUILD:
        raise EvidenceBundleError("portable evidence CK3 build mismatch")
    if manifest.get("ck3_exe_sha256") != EXACT_CK3_EXE_SHA256:
        raise EvidenceBundleError("portable evidence executable hash mismatch")
    compression = manifest.get("compression")
    if compression != {
        "algorithm": "gzip",
        "filename": "",
        "mtime": 0,
    }:
        raise EvidenceBundleError("portable evidence compression contract mismatch")
    evidence = manifest.get("evidence")
    if not isinstance(evidence, list):
        raise EvidenceBundleError("portable evidence rows must be an array")
    return manifest


def _validate_reference(reference: object) -> dict[str, object]:
    if not isinstance(reference, dict) or set(reference) != {
        "caller_candidate_resolution",
        "event_definition_key",
        "logical_path",
        "origin",
        "provenance",
        "role",
        "source_column",
        "source_line",
    }:
        raise EvidenceBundleError("invalid evidence reference")
    for key in ("event_definition_key", "logical_path", "origin", "provenance", "role"):
        if not isinstance(reference[key], str) or not reference[key]:
            raise EvidenceBundleError(
                "evidence reference identity values must be non-empty strings"
            )
    origin = reference["origin"]
    if origin not in {"ck3_game", "runtime"}:
        raise EvidenceBundleError("invalid evidence reference origin")
    provenance = reference["provenance"]
    allowed_provenance = {
        "captured-observation-artifact",
        "generated-definition-index",
        "lexical-caller-candidate-not-proven-runtime-caller",
        "manually-reviewed-analysis-source",
    }
    if provenance not in allowed_provenance:
        raise EvidenceBundleError("invalid evidence reference provenance")
    logical = PurePosixPath(reference["logical_path"])
    if logical.is_absolute() or ".." in logical.parts:
        raise EvidenceBundleError("unsafe evidence logical path")
    line = reference["source_line"]
    column = reference["source_column"]
    resolution = reference["caller_candidate_resolution"]
    if line is not None and (not _is_plain_int(line) or line < 1):
        raise EvidenceBundleError("invalid evidence reference source line")
    if column is not None and (not _is_plain_int(column) or column < 1):
        raise EvidenceBundleError("invalid evidence reference source column")
    if resolution not in {
        None,
        "external-definition-file",
        "same-definition-file-only",
    }:
        raise EvidenceBundleError("invalid caller candidate resolution")
    shape = (reference["role"], line, column, resolution, origin)
    expected_shapes = {
        "generated-definition-index": (
            "event_definition",
            "positive",
            None,
            None,
            "ck3_game",
        ),
        "lexical-caller-candidate-not-proven-runtime-caller": (
            "caller_candidate",
            "positive",
            "positive",
            "resolution",
            "ck3_game",
        ),
        "manually-reviewed-analysis-source": (
            "analysis_source",
            None,
            None,
            None,
            "ck3_game",
        ),
    }
    if provenance == "captured-observation-artifact":
        if origin != "runtime" or any(
            value is not None for value in (line, column, resolution)
        ):
            raise EvidenceBundleError("invalid captured observation provenance shape")
    else:
        expected = expected_shapes[provenance]
        normalized_shape = (
            shape[0],
            "positive" if line is not None else None,
            "positive" if column is not None else None,
            "resolution" if resolution is not None else None,
            shape[4],
        )
        if normalized_shape != expected:
            raise EvidenceBundleError("invalid source provenance shape")
    return {key: reference[key] for key in sorted(reference)}


def _validated_entries(
    bundle_root: Path,
    *,
    verify_payloads: bool,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    manifest = _load_manifest(bundle_root)
    entries: dict[str, dict[str, object]] = {}
    prior_id: str | None = None
    reference_count = 0
    source_count = 0
    observation_count = 0
    provenance_counts = {
        "generated-definition-index": 0,
        "lexical-caller-candidate-not-proven-runtime-caller": 0,
        "manually-reviewed-analysis-source": 0,
        "captured-observation-artifact": 0,
    }
    for raw_entry in manifest["evidence"]:  # type: ignore[index]
        if not isinstance(raw_entry, dict):
            raise EvidenceBundleError("portable evidence row must be an object")
        required = {
            "blob_bytes",
            "blob_path",
            "blob_sha256",
            "bytes",
            "evidence_id",
            "kind",
            "media_type",
            "references",
            "sha256",
        }
        if set(raw_entry) != required:
            raise EvidenceBundleError("portable evidence row fields mismatch")
        evidence_id = raw_entry["evidence_id"]
        digest = raw_entry["sha256"]
        if (
            not isinstance(evidence_id, str)
            or _SHA256.fullmatch(evidence_id) is None
            or digest != evidence_id
        ):
            raise EvidenceBundleError("portable evidence id/hash mismatch")
        if prior_id is not None and evidence_id <= prior_id:
            raise EvidenceBundleError("portable evidence rows are not strictly sorted")
        prior_id = evidence_id
        if evidence_id in entries:
            raise EvidenceBundleError("duplicate portable evidence id")
        kind = raw_entry["kind"]
        if kind not in {"source_definition", "observation_artifact"}:
            raise EvidenceBundleError("invalid portable evidence kind")
        media_type = raw_entry["media_type"]
        if not isinstance(media_type, str) or media_type not in _MEDIA_TYPES:
            raise EvidenceBundleError("invalid portable evidence media type")
        size = raw_entry["bytes"]
        blob_size = raw_entry["blob_bytes"]
        blob_digest = raw_entry["blob_sha256"]
        if (
            not _is_plain_int(size)
            or size < 0
            or not _is_plain_int(blob_size)
            or blob_size <= 0
            or not isinstance(blob_digest, str)
            or _SHA256.fullmatch(blob_digest) is None
        ):
            raise EvidenceBundleError("invalid portable evidence sizes or blob hash")
        expected_blob = f"blobs/{evidence_id}.gz"
        if raw_entry["blob_path"] != expected_blob:
            raise EvidenceBundleError("portable evidence blob path mismatch")
        raw_references = raw_entry["references"]
        if not isinstance(raw_references, list) or not raw_references:
            raise EvidenceBundleError("portable evidence must have references")
        references = [_validate_reference(item) for item in raw_references]
        canonical_refs = sorted(
            references,
            key=lambda item: (
                item["event_definition_key"],
                item["origin"],
                item["provenance"],
                item["role"],
                item["logical_path"],
                item["source_line"] if item["source_line"] is not None else 0,
                item["source_column"] if item["source_column"] is not None else 0,
            ),
        )
        if references != canonical_refs or len(
            {tuple(item.items()) for item in references}
        ) != len(references):
            raise EvidenceBundleError("portable evidence references are not canonical")
        expected_origin = "ck3_game" if kind == "source_definition" else "runtime"
        for reference in references:
            if reference["origin"] != expected_origin:
                raise EvidenceBundleError("portable evidence kind/origin mismatch")
            if _media_type_for_path(reference["logical_path"]) != media_type:
                raise EvidenceBundleError("portable evidence path/media type mismatch")
            provenance_counts[str(reference["provenance"])] += 1
        reference_count += len(references)
        if kind == "source_definition":
            source_count += 1
        else:
            observation_count += 1
        entry = dict(raw_entry)
        entry["references"] = references
        entries[evidence_id] = entry
        if verify_payloads:
            _verified_payload(bundle_root, entry)

    stats = manifest.get("statistics")
    expected_stats = {
        "evidence": len(entries),
        "generated_definition_references": provenance_counts[
            "generated-definition-index"
        ],
        "lexical_caller_candidate_references": provenance_counts[
            "lexical-caller-candidate-not-proven-runtime-caller"
        ],
        "manually_reviewed_analysis_source_references": provenance_counts[
            "manually-reviewed-analysis-source"
        ],
        "observation_artifacts": observation_count,
        "observation_artifact_references": provenance_counts[
            "captured-observation-artifact"
        ],
        "references": reference_count,
        "source_definitions": source_count,
    }
    if stats != expected_stats:
        raise EvidenceBundleError("portable evidence statistics mismatch")

    blob_root = bundle_root / "blobs"
    try:
        actual_blobs = {
            path.name for path in blob_root.iterdir() if path.is_file()
        }
    except OSError as exc:
        raise EvidenceBundleError("portable evidence blob directory is unavailable") from exc
    expected_blobs = {f"{evidence_id}.gz" for evidence_id in entries}
    if actual_blobs != expected_blobs:
        raise EvidenceBundleError("portable evidence blob set mismatch")
    return manifest, entries


def _verified_payload(bundle_root: Path, entry: dict[str, object]) -> bytes:
    evidence_id = entry["evidence_id"]
    assert isinstance(evidence_id, str)
    blob_path = bundle_root / "blobs" / f"{evidence_id}.gz"
    try:
        blob = blob_path.read_bytes()
    except OSError as exc:
        raise EvidenceBundleError("portable evidence blob is unavailable") from exc
    if len(blob) != entry["blob_bytes"] or _sha256(blob) != entry["blob_sha256"]:
        raise EvidenceBundleError("portable evidence compressed blob mismatch")
    if len(blob) < 10 or blob[:3] != b"\x1f\x8b\x08":
        raise EvidenceBundleError("portable evidence is not gzip")
    if blob[3] != 0 or blob[4:8] != b"\x00\x00\x00\x00":
        raise EvidenceBundleError("portable evidence gzip header is nondeterministic")
    decompressor = zlib.decompressobj(wbits=31)
    try:
        data = decompressor.decompress(blob) + decompressor.flush()
    except zlib.error as exc:
        raise EvidenceBundleError("portable evidence gzip stream is invalid") from exc
    if not decompressor.eof or decompressor.unused_data or decompressor.unconsumed_tail:
        raise EvidenceBundleError("portable evidence gzip stream has trailing data")
    if len(data) != entry["bytes"] or _sha256(data) != evidence_id:
        raise EvidenceBundleError("portable evidence payload hash/size mismatch")
    media_type = entry["media_type"]
    assert isinstance(media_type, str)
    _validate_payload_media_type(data, media_type)
    return data


def validate_portable_evidence_bundle_v1(
    bundle_root: str | Path | None = None,
) -> dict[str, JsonValue]:
    """Validate every checked-in blob without consulting external source paths."""
    root = Path(bundle_root) if bundle_root is not None else _BUNDLE_ROOT
    manifest, entries = _validated_entries(root, verify_payloads=True)
    return {
        "schema": EVIDENCE_MANIFEST_SCHEMA,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": "available",
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "statistics": _json_clone(manifest["statistics"]),
        "manifest_sha256": _sha256((root / "manifest_v1.json").read_bytes()),
        "validated_evidence": len(entries),
        "unavailable_reason": None,
    }


def _index_response(
    *,
    status: str,
    event_definition_key: object,
    kind: object,
    evidence: object,
    unavailable_reason: str | None,
) -> dict[str, JsonValue]:
    return {
        "schema": EVIDENCE_INDEX_SCHEMA,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": status,
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "event_definition_key": (
            event_definition_key if isinstance(event_definition_key, str) else None
        ),
        "kind": (
            kind
            if kind in {"source_definition", "observation_artifact"}
            else None
        ),
        "evidence": _json_clone(evidence),
        "unavailable_reason": unavailable_reason,
    }


def query_vanilla_event_evidence_index_v1(
    event_definition_key: str | None = None,
    *,
    kind: str | None = None,
    ck3_build: str = EXACT_CK3_BUILD,
    bundle_root: str | Path | None = None,
) -> dict[str, JsonValue]:
    """List frozen evidence, optionally restricted to one event and/or kind."""
    if ck3_build != EXACT_CK3_BUILD:
        return _index_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            evidence=[],
            unavailable_reason="unsupported_ck3_build",
        )
    if event_definition_key is not None and (
        not isinstance(event_definition_key, str) or not event_definition_key.strip()
    ):
        return _index_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            evidence=[],
            unavailable_reason="invalid_event_definition_key",
        )
    if kind not in {None, "source_definition", "observation_artifact"}:
        return _index_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            evidence=[],
            unavailable_reason="invalid_evidence_kind",
        )
    root = Path(bundle_root) if bundle_root is not None else _BUNDLE_ROOT
    try:
        _, entries = _validated_entries(root, verify_payloads=False)
    except EvidenceBundleError:
        return _index_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            evidence=[],
            unavailable_reason="bundle_integrity_error",
        )
    result: list[dict[str, object]] = []
    event_seen = False
    for evidence_id, entry in entries.items():
        references = entry["references"]
        assert isinstance(references, list)
        if event_definition_key is not None:
            selected_references = [
                reference
                for reference in references
                if reference["event_definition_key"] == event_definition_key
            ]
            if selected_references:
                event_seen = True
            if not selected_references:
                continue
        else:
            selected_references = references
        if kind is not None and entry["kind"] != kind:
            continue
        result.append(
            {
                "bytes": entry["bytes"],
                "evidence_id": evidence_id,
                "kind": entry["kind"],
                "media_type": entry["media_type"],
                "references": selected_references,
                "sha256": entry["sha256"],
            }
        )
    if event_definition_key is not None and not event_seen:
        return _index_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            evidence=[],
            unavailable_reason="event_definition_key_not_indexed",
        )
    return _index_response(
        status="available",
        event_definition_key=event_definition_key,
        kind=kind,
        evidence=result,
        unavailable_reason=None,
    )


def _list_response(
    *,
    status: str,
    event_definition_key: object,
    kind: object,
    after_evidence_id: object,
    limit: object,
    dataset_sha256: str | None,
    total_matches: int,
    evidence: object,
    next_after_evidence_id: str | None,
    unavailable_reason: str | None,
    invalid_parameter: str | None,
) -> dict[str, JsonValue]:
    return {
        "schema": EVIDENCE_LIST_SCHEMA,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": status,
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "event_definition_key": (
            event_definition_key
            if isinstance(event_definition_key, str)
            else None
        ),
        "kind": (
            kind
            if kind in {"source_definition", "observation_artifact"}
            else None
        ),
        "after_evidence_id": (
            after_evidence_id
            if isinstance(after_evidence_id, str)
            and _SHA256.fullmatch(after_evidence_id) is not None
            else None
        ),
        "limit": limit if _is_plain_int(limit) and 1 <= limit <= 100 else None,
        "dataset_sha256": dataset_sha256,
        "total_matches": total_matches,
        "evidence": _json_clone(evidence),
        "next_after_evidence_id": next_after_evidence_id,
        "unavailable_reason": unavailable_reason,
        "invalid_parameter": invalid_parameter,
    }


def list_vanilla_event_evidence_v1(
    event_definition_key: object = None,
    *,
    kind: object = None,
    after_evidence_id: object = None,
    limit: object = 50,
    ck3_build: object = EXACT_CK3_BUILD,
    bundle_root: str | Path | None = None,
) -> dict[str, JsonValue]:
    """List portable evidence through a stable content-hash cursor.

    Only logical, repository-relative provenance is returned.  Blob paths and
    the machine-local bundle root are deliberately absent from this response.
    The dataset identity is the SHA-256 of the checked-in manifest bytes.
    """
    invalid_parameter: str | None = None
    unavailable_reason: str | None = None
    if not isinstance(ck3_build, str) or ck3_build != EXACT_CK3_BUILD:
        unavailable_reason = "unsupported_ck3_build"
        invalid_parameter = "ck3_build"
    elif event_definition_key is not None and (
        not isinstance(event_definition_key, str)
        or not event_definition_key.strip()
    ):
        unavailable_reason = "invalid_event_definition_key"
        invalid_parameter = "event_definition_key"
    elif kind not in {None, "source_definition", "observation_artifact"}:
        unavailable_reason = "invalid_evidence_kind"
        invalid_parameter = "kind"
    elif (
        after_evidence_id is not None
        and (
            not isinstance(after_evidence_id, str)
            or _SHA256.fullmatch(after_evidence_id) is None
        )
    ):
        unavailable_reason = "invalid_cursor"
        invalid_parameter = "after_evidence_id"
    elif not _is_plain_int(limit) or not 1 <= limit <= 100:
        unavailable_reason = "invalid_limit"
        invalid_parameter = "limit"
    if unavailable_reason is not None:
        return _list_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            after_evidence_id=after_evidence_id,
            limit=limit,
            dataset_sha256=None,
            total_matches=0,
            evidence=[],
            next_after_evidence_id=None,
            unavailable_reason=unavailable_reason,
            invalid_parameter=invalid_parameter,
        )

    root = Path(bundle_root) if bundle_root is not None else _BUNDLE_ROOT
    try:
        _, entries = _validated_entries(root, verify_payloads=False)
        manifest_sha256 = _sha256((root / "manifest_v1.json").read_bytes()).upper()
    except (EvidenceBundleError, OSError):
        return _list_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            after_evidence_id=after_evidence_id,
            limit=limit,
            dataset_sha256=None,
            total_matches=0,
            evidence=[],
            next_after_evidence_id=None,
            unavailable_reason="bundle_integrity_error",
            invalid_parameter=None,
        )
    if after_evidence_id is not None and after_evidence_id not in entries:
        return _list_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            after_evidence_id=after_evidence_id,
            limit=limit,
            dataset_sha256=None,
            total_matches=0,
            evidence=[],
            next_after_evidence_id=None,
            unavailable_reason="invalid_cursor",
            invalid_parameter="after_evidence_id",
        )

    rows: list[dict[str, object]] = []
    event_seen = False
    for evidence_id, entry in entries.items():
        references = entry["references"]
        assert isinstance(references, list)
        if event_definition_key is not None:
            selected_references = [
                reference
                for reference in references
                if reference["event_definition_key"] == event_definition_key
            ]
            if selected_references:
                event_seen = True
            if not selected_references:
                continue
        else:
            selected_references = references
        if kind is not None and entry["kind"] != kind:
            continue
        rows.append(
            {
                "bytes": entry["bytes"],
                "evidence_id": evidence_id,
                "kind": entry["kind"],
                "media_type": entry["media_type"],
                "references": selected_references,
                "sha256": entry["sha256"],
            }
        )
    if event_definition_key is not None and not event_seen:
        return _list_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            kind=kind,
            after_evidence_id=after_evidence_id,
            limit=limit,
            dataset_sha256=None,
            total_matches=0,
            evidence=[],
            next_after_evidence_id=None,
            unavailable_reason="event_definition_key_not_indexed",
            invalid_parameter="event_definition_key",
        )

    assert _is_plain_int(limit)
    page_candidates = (
        rows
        if after_evidence_id is None
        else [row for row in rows if row["evidence_id"] > after_evidence_id]
    )
    page = page_candidates[:limit]
    next_after_evidence_id = (
        str(page[-1]["evidence_id"])
        if len(page_candidates) > limit and page
        else None
    )
    return _list_response(
        status="available",
        event_definition_key=event_definition_key,
        kind=kind,
        after_evidence_id=after_evidence_id,
        limit=limit,
        dataset_sha256=manifest_sha256,
        total_matches=len(rows),
        evidence=page,
        next_after_evidence_id=next_after_evidence_id,
        unavailable_reason=None,
        invalid_parameter=None,
    )


def portable_event_keys_v1(
    bundle_root: str | Path | None = None,
) -> frozenset[str]:
    """Return event keys represented by the validated portable manifest."""
    root = Path(bundle_root) if bundle_root is not None else _BUNDLE_ROOT
    _, entries = _validated_entries(root, verify_payloads=False)
    return frozenset(
        reference["event_definition_key"]
        for entry in entries.values()
        for reference in entry["references"]  # type: ignore[union-attr]
    )


def _read_response(
    *,
    status: str,
    evidence_id: object,
    entry: dict[str, object] | None,
    offset: object,
    content: bytes | None,
    eof: bool | None,
    unavailable_reason: str | None,
) -> dict[str, JsonValue]:
    return {
        "schema": EVIDENCE_READ_SCHEMA,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": status,
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "evidence_id": evidence_id if isinstance(evidence_id, str) else None,
        "sha256": entry["sha256"] if entry is not None else None,
        "kind": entry["kind"] if entry is not None else None,
        "media_type": entry["media_type"] if entry is not None else None,
        "historical_artifact_may_contain_nonportable_locators": (
            entry["kind"] == "observation_artifact"
            if entry is not None
            else None
        ),
        "offset": offset if _is_plain_int(offset) and offset >= 0 else None,
        "content_bytes": len(content) if content is not None else None,
        "total_bytes": entry["bytes"] if entry is not None else None,
        "content_base64": (
            base64.b64encode(content).decode("ascii") if content is not None else None
        ),
        "eof": eof,
        "unavailable_reason": unavailable_reason,
    }


def read_vanilla_event_evidence_v1(
    evidence_id: str,
    *,
    offset: int = 0,
    max_bytes: int = MAX_EVIDENCE_READ_BYTES,
    ck3_build: str = EXACT_CK3_BUILD,
    bundle_root: str | Path | None = None,
) -> dict[str, JsonValue]:
    """Read one verified evidence payload in a bounded, JSON-safe chunk."""
    if ck3_build != EXACT_CK3_BUILD:
        return _read_response(
            status="unavailable",
            evidence_id=evidence_id,
            entry=None,
            offset=offset,
            content=None,
            eof=None,
            unavailable_reason="unsupported_ck3_build",
        )
    if not isinstance(evidence_id, str) or _SHA256.fullmatch(evidence_id) is None:
        return _read_response(
            status="unavailable",
            evidence_id=evidence_id,
            entry=None,
            offset=offset,
            content=None,
            eof=None,
            unavailable_reason="invalid_evidence_id",
        )
    if not _is_plain_int(offset) or offset < 0:
        return _read_response(
            status="unavailable",
            evidence_id=evidence_id,
            entry=None,
            offset=offset,
            content=None,
            eof=None,
            unavailable_reason="invalid_offset",
        )
    if (
        not _is_plain_int(max_bytes)
        or max_bytes <= 0
        or max_bytes > MAX_EVIDENCE_READ_BYTES
    ):
        return _read_response(
            status="unavailable",
            evidence_id=evidence_id,
            entry=None,
            offset=offset,
            content=None,
            eof=None,
            unavailable_reason="invalid_max_bytes",
        )
    root = Path(bundle_root) if bundle_root is not None else _BUNDLE_ROOT
    try:
        _, entries = _validated_entries(root, verify_payloads=False)
        entry = entries.get(evidence_id)
        if entry is None:
            return _read_response(
                status="unavailable",
                evidence_id=evidence_id,
                entry=None,
                offset=offset,
                content=None,
                eof=None,
                unavailable_reason="evidence_id_not_indexed",
            )
        payload = _verified_payload(root, entry)
    except EvidenceBundleError:
        return _read_response(
            status="unavailable",
            evidence_id=evidence_id,
            entry=None,
            offset=offset,
            content=None,
            eof=None,
            unavailable_reason="bundle_integrity_error",
        )
    if offset > len(payload):
        return _read_response(
            status="unavailable",
            evidence_id=evidence_id,
            entry=entry,
            offset=offset,
            content=None,
            eof=None,
            unavailable_reason="offset_out_of_range",
        )
    content = payload[offset : offset + max_bytes]
    return _read_response(
        status="available",
        evidence_id=evidence_id,
        entry=entry,
        offset=offset,
        content=content,
        eof=offset + len(content) >= len(payload),
        unavailable_reason=None,
    )


__all__ = [
    "EVIDENCE_INDEX_SCHEMA",
    "EVIDENCE_LIST_SCHEMA",
    "EVIDENCE_MANIFEST_SCHEMA",
    "EVIDENCE_READ_SCHEMA",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceBundleError",
    "MAX_EVIDENCE_READ_BYTES",
    "list_vanilla_event_evidence_v1",
    "portable_event_keys_v1",
    "query_vanilla_event_evidence_index_v1",
    "read_vanilla_event_evidence_v1",
    "validate_portable_evidence_bundle_v1",
]
