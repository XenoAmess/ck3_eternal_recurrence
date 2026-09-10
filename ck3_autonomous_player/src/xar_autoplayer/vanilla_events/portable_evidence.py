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


def _validate_reference(reference: object) -> dict[str, str]:
    if not isinstance(reference, dict) or set(reference) != {
        "event_definition_key",
        "logical_path",
        "origin",
        "role",
    }:
        raise EvidenceBundleError("invalid evidence reference")
    if not all(isinstance(value, str) and value for value in reference.values()):
        raise EvidenceBundleError("evidence reference values must be non-empty strings")
    origin = reference["origin"]
    if origin not in {"ck3_game", "runtime"}:
        raise EvidenceBundleError("invalid evidence reference origin")
    logical = PurePosixPath(reference["logical_path"])
    if logical.is_absolute() or ".." in logical.parts:
        raise EvidenceBundleError("unsafe evidence logical path")
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
                item["role"],
                item["logical_path"],
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
        "observation_artifacts": observation_count,
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
        "kind": kind if isinstance(kind, str) else None,
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
    "EVIDENCE_MANIFEST_SCHEMA",
    "EVIDENCE_READ_SCHEMA",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceBundleError",
    "MAX_EVIDENCE_READ_BYTES",
    "query_vanilla_event_evidence_index_v1",
    "read_vanilla_event_evidence_v1",
    "validate_portable_evidence_bundle_v1",
]
