"""Strict typed contract for exporting CK3's current designer source."""

from __future__ import annotations

import hashlib
import re
from typing import Final

from .coat_of_arms_source_probe_contract import (
    COAT_OF_ARMS_SOURCE_V1_MAX_BYTES,
    normalize_coat_of_arms_source_v1_binding,
)


EXPORT_COAT_OF_ARMS_SOURCE_V1_CAPABILITY: Final = (
    "game.command.export-coat-of-arms-source-v1"
)
EXPORT_COAT_OF_ARMS_SOURCE_V1_STEP: Final = "export-coat-of-arms-source-v1"
EXPORT_COAT_OF_ARMS_SOURCE_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-coat-of-arms-designer-export-v1"
)

_NATIVE_RESULT_FIELDS: Final = {
    "step",
    "accepted",
    "status",
    "query_sequence",
    "snapshot_revision",
    "coat_of_arms_export",
    "backend_id",
}
_NATIVE_EXPORT_FIELDS: Final = {
    "schema",
    "schema_version",
    "status",
    "date_raw",
    "source_bytes",
    "designer_observed",
    "copy_invoked",
    "clipboard_read",
    "source",
    "reason",
    "provenance",
}
_PUBLIC_FIELDS: Final = {
    "schema",
    "schema_version",
    "step",
    "status",
    "designer_observed",
    "copy_invoked",
    "clipboard_read",
    "source",
    "source_sha256",
    "source_bytes",
    "reason",
    "binding",
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _exact(value: object, fields: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _uint64(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**64 - 1:
        raise ValueError(f"{label} must be uint64")
    return value


def _int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not -(2**31) <= value <= 2**31 - 1:
        raise ValueError(f"{label} must be int32")
    return value


def _source_identity(source: object) -> tuple[str, str, int]:
    if not isinstance(source, str) or not source or "\0" in source:
        raise ValueError("exported source must be a non-empty string without NUL")
    try:
        encoded = source.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("exported source must be ASCII") from error
    if len(encoded) > COAT_OF_ARMS_SOURCE_V1_MAX_BYTES:
        raise ValueError("exported source exceeds the 128 KiB limit")
    return source, hashlib.sha256(encoded).hexdigest(), len(encoded)


def normalize_native_coat_of_arms_source_export_v1_result(
    value: object,
    *,
    expected_native_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    """Validate the exact native named-pipe export envelope."""

    result = _exact(value, _NATIVE_RESULT_FIELDS, "native coat-of-arms export")
    if result.get("step") != EXPORT_COAT_OF_ARMS_SOURCE_V1_STEP or result.get("accepted") is not True:
        raise ValueError("native coat-of-arms export identity is invalid")
    status = result.get("status")
    if status not in {"exported", "unavailable"}:
        raise ValueError("native coat-of-arms export status is invalid")
    _uint64(result.get("query_sequence"), "query_sequence")
    if _uint64(result.get("snapshot_revision"), "snapshot_revision") != expected_native_revision:
        raise ValueError("native coat-of-arms export revision changed")
    if result.get("backend_id") != "native-headless":
        raise ValueError("native coat-of-arms export backend is invalid")

    export = _exact(result.get("coat_of_arms_export"), _NATIVE_EXPORT_FIELDS, "native coat-of-arms export payload")
    if export.get("schema") != "xar.ck3.coat-of-arms-designer-export.v1" or export.get("schema_version") != 1 or export.get("status") != status:
        raise ValueError("native coat-of-arms export schema is invalid")
    if _int32(export.get("date_raw"), "date_raw") != expected_date_raw:
        raise ValueError("native coat-of-arms export date changed")
    for field in ("designer_observed", "copy_invoked", "clipboard_read"):
        if not isinstance(export.get(field), bool):
            raise ValueError(f"native coat-of-arms export {field} must be boolean")
    provenance = _exact(export.get("provenance"), {"backend_id"}, "native coat-of-arms export provenance")
    if provenance.get("backend_id") != EXPORT_COAT_OF_ARMS_SOURCE_V1_BACKEND_ID:
        raise ValueError("native coat-of-arms export provenance is invalid")

    if status == "exported":
        source, source_sha256, source_bytes = _source_identity(export.get("source"))
        if not (export.get("designer_observed") is True and export.get("copy_invoked") is True and export.get("clipboard_read") is True):
            raise ValueError("exported coat-of-arms source lacks successful native postconditions")
        if export.get("source_bytes") != source_bytes or isinstance(export.get("source_bytes"), bool):
            raise ValueError("exported coat-of-arms source byte count changed")
        if export.get("reason") is not None:
            raise ValueError("successful coat-of-arms export must not have a reason")
    else:
        if export.get("source") is not None or export.get("source_bytes") != 0:
            raise ValueError("unavailable coat-of-arms export must not expose source")
        reason = export.get("reason")
        if not isinstance(reason, str) or not reason:
            raise ValueError("unavailable coat-of-arms export must explain why")
        source = None
        source_sha256 = None
        source_bytes = 0

    return {
        "status": status,
        "designer_observed": export["designer_observed"],
        "copy_invoked": export["copy_invoked"],
        "clipboard_read": export["clipboard_read"],
        "source": source,
        "source_sha256": source_sha256,
        "source_bytes": source_bytes,
        "reason": export["reason"],
    }


def normalize_coat_of_arms_source_export_v1_result(
    value: object,
    *,
    expected_binding: object,
) -> dict[str, object]:
    """Validate and normalize the public MCP export result."""

    result = _exact(value, _PUBLIC_FIELDS, "coat-of-arms source export")
    binding = normalize_coat_of_arms_source_v1_binding(expected_binding)
    if result.get("schema") != "coat-of-arms-source-export-v1" or result.get("schema_version") != 1 or result.get("step") != EXPORT_COAT_OF_ARMS_SOURCE_V1_STEP:
        raise ValueError("coat-of-arms source export schema is invalid")
    if normalize_coat_of_arms_source_v1_binding(result.get("binding")) != binding:
        raise ValueError("coat-of-arms source export binding changed")
    status = result.get("status")
    if status not in {"exported", "unavailable"}:
        raise ValueError("coat-of-arms source export status is invalid")
    for field in ("designer_observed", "copy_invoked", "clipboard_read"):
        if not isinstance(result.get(field), bool):
            raise ValueError(f"coat-of-arms source export {field} must be boolean")
    if status == "exported":
        source, source_sha256, source_bytes = _source_identity(result.get("source"))
        if result.get("source_sha256") != source_sha256 or not _SHA256.fullmatch(str(result.get("source_sha256"))):
            raise ValueError("coat-of-arms source export hash changed")
        if result.get("source_bytes") != source_bytes or result.get("reason") is not None:
            raise ValueError("coat-of-arms source export success envelope is inconsistent")
        if not all(result.get(field) is True for field in ("designer_observed", "copy_invoked", "clipboard_read")):
            raise ValueError("coat-of-arms source export postconditions are incomplete")
    else:
        if result.get("source") is not None or result.get("source_sha256") is not None or result.get("source_bytes") != 0:
            raise ValueError("unavailable coat-of-arms source export exposed source")
        if not isinstance(result.get("reason"), str) or not result.get("reason"):
            raise ValueError("unavailable coat-of-arms source export lacks a reason")
    return dict(result)
