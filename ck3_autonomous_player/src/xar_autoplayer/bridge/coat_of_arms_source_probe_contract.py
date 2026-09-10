"""Strict typed contract for probing CK3 coat-of-arms source text."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import re
from typing import Final


PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY: Final = (
    "game.command.probe-coat-of-arms-source-v1"
)
PROBE_COAT_OF_ARMS_SOURCE_V1_STEP: Final = (
    "probe-coat-of-arms-source-v1"
)
COAT_OF_ARMS_SOURCE_V1_MAX_BYTES: Final = 128 * 1024
COAT_OF_ARMS_SOURCE_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1"
)
COAT_OF_ARMS_SOURCE_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
COAT_OF_ARMS_SOURCE_V1_GAME_VERSION: Final = "1.19.0.6"
COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)

_RESULT_FIELDS: Final = {
    "schema",
    "schema_version",
    "step",
    "status",
    "detected",
    "designer_observed",
    "clipboard_written",
    "clipboard_readback_matched",
    "apply_requested",
    "paste_invoked",
    "applied",
    "candidate_index",
    "preview_coat_of_arms_handle",
    "active_coat_of_arms_index",
    "reason",
    "source_sha256",
    "source_bytes",
    "binding",
}
_GAMEPLAY_BINDING_FIELDS: Final = {
    "mode",
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "episode_run_id",
    "connection_generation",
    "bridge_pid",
}
_FRONTEND_SNAPSHOT_BINDING_FIELDS: Final = {
    "mode",
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "connection_generation",
    "bridge_pid",
}
_FRONTEND_BINDING_FIELDS: Final = {
    "mode",
    "revision",
    "connection_generation",
    "bridge_pid",
}
_NATIVE_RESULT_FIELDS: Final = {
    "step",
    "accepted",
    "status",
    "query_sequence",
    "snapshot_revision",
    "coat_of_arms_probe",
    "backend_id",
}
_NATIVE_PROBE_FIELDS: Final = {
    "schema",
    "schema_version",
    "status",
    "date_raw",
    "source_bytes",
    "designer_observed",
    "clipboard_written",
    "clipboard_readback_matched",
    "detected",
    "apply_requested",
    "paste_invoked",
    "applied",
    "candidate_index",
    "preview_coat_of_arms_handle",
    "active_coat_of_arms_index",
    "reason",
    "provenance",
}
_PROVENANCE_FIELDS: Final = {"backend_id"}
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class EncodedCoatOfArmsSourceV1:
    """One validated source and its exact native-wire representation."""

    source: str
    source_base64: str
    source_sha256: str
    source_bytes: int


def encode_coat_of_arms_source_v1(
    source: object,
) -> EncodedCoatOfArmsSourceV1:
    """Validate and canonicalize source for the Windows clipboard reader."""
    if not isinstance(source, str):
        raise ValueError("source must be a UTF-8 string")
    if not source:
        raise ValueError("source must not be empty")
    if "\0" in source:
        raise ValueError("source must not contain NUL")
    # CF_UNICODETEXT normalizes line endings to CRLF when CK3 reads the
    # clipboard back.  Bind the wire bytes and result hash to that canonical
    # Windows form so ordinary LF-only editor text still has exact read-back
    # identity instead of producing a false clipboard_readback_mismatch.
    source = source.replace("\r\n", "\n").replace("\r", "\n").replace(
        "\n", "\r\n"
    )
    try:
        encoded = source.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(
            "source must be ASCII because the vanilla reader rejects "
            "high-bit bytes"
        ) from error
    if len(encoded) > COAT_OF_ARMS_SOURCE_V1_MAX_BYTES:
        raise ValueError("source exceeds the 128 KiB limit")
    return EncodedCoatOfArmsSourceV1(
        source=source,
        source_base64=base64.b64encode(encoded).decode("ascii"),
        source_sha256=hashlib.sha256(encoded).hexdigest(),
        source_bytes=len(encoded),
    )


def validate_coat_of_arms_source_probe_apply(value: object) -> bool:
    """Require an explicit boolean for detect-only versus applying input."""
    if not isinstance(value, bool):
        raise ValueError("apply must be boolean")
    return value


def normalize_coat_of_arms_source_v1_binding(
    value: object,
) -> dict[str, object]:
    """Normalize the exact public/native revision binding for one probe."""
    if not isinstance(value, dict):
        raise ValueError("coat-of-arms probe binding must be an object")
    mode = value.get("mode")
    if mode == "frontend":
        binding = _exact_object(
            value,
            _FRONTEND_BINDING_FIELDS,
            "frontend coat-of-arms probe binding",
        )
        revision = _uint64(
            binding.get("revision"), "binding.revision", minimum=0
        )
        if revision != 0:
            raise ValueError("frontend coat-of-arms binding revision must be 0")
        return {
            "mode": "frontend",
            "revision": 0,
            "connection_generation": _uint64(
                binding.get("connection_generation"),
                "binding.connection_generation",
                minimum=1,
            ),
            "bridge_pid": _int(
                binding.get("bridge_pid"),
                "binding.bridge_pid",
                minimum=1,
                maximum=2**32 - 1,
            ),
        }
    if mode == "frontend_snapshot":
        binding = _exact_object(
            value,
            _FRONTEND_SNAPSHOT_BINDING_FIELDS,
            "frontend snapshot coat-of-arms probe binding",
        )
        return {
            "mode": "frontend_snapshot",
            "snapshot_id": _nonempty_string(
                binding.get("snapshot_id"), "binding.snapshot_id"
            ),
            "revision": _uint64(
                binding.get("revision"), "binding.revision", minimum=1
            ),
            "native_revision": _uint64(
                binding.get("native_revision"),
                "binding.native_revision",
                minimum=1,
            ),
            "date_raw": _int(
                binding.get("date_raw"),
                "binding.date_raw",
                minimum=-(2**63),
                maximum=2**63 - 1,
            ),
            "connection_generation": _uint64(
                binding.get("connection_generation"),
                "binding.connection_generation",
                minimum=1,
            ),
            "bridge_pid": _int(
                binding.get("bridge_pid"),
                "binding.bridge_pid",
                minimum=1,
                maximum=2**32 - 1,
            ),
        }
    if mode != "gameplay":
        raise ValueError("coat-of-arms probe binding mode is invalid")
    binding = _exact_object(
        value,
        _GAMEPLAY_BINDING_FIELDS,
        "gameplay coat-of-arms probe binding",
    )
    return {
        "mode": "gameplay",
        "snapshot_id": _nonempty_string(
            binding.get("snapshot_id"), "binding.snapshot_id"
        ),
        "revision": _uint64(
            binding.get("revision"), "binding.revision", minimum=1
        ),
        "native_revision": _uint64(
            binding.get("native_revision"),
            "binding.native_revision",
            minimum=1,
        ),
        "date_raw": _int(
            binding.get("date_raw"),
            "binding.date_raw",
            minimum=-(2**63),
            maximum=2**63 - 1,
        ),
        "episode_run_id": _nonempty_string(
            binding.get("episode_run_id"), "binding.episode_run_id"
        ),
        "connection_generation": _uint64(
            binding.get("connection_generation"),
            "binding.connection_generation",
            minimum=1,
        ),
        "bridge_pid": _int(
            binding.get("bridge_pid"),
            "binding.bridge_pid",
            minimum=1,
            maximum=2**32 - 1,
        ),
    }


def coat_of_arms_source_frontend_binding_from_capabilities(
    value: object,
) -> dict[str, object]:
    """Bind a frontend request to one connected exact-build native bridge."""

    candidates: list[dict[str, object]] = []

    def visit(row: object) -> None:
        if not isinstance(row, dict):
            return
        bridge_capabilities = row.get("bridge_capabilities")
        diagnostics = row.get("diagnostics")
        if (
            row.get("backend_id") == "native-headless"
            and row.get("mode") == "native-headless"
            and row.get("source") == "injected-dll-named-pipe"
            and row.get("visual_fallback") is False
            and row.get("snapshot") is False
            and isinstance(bridge_capabilities, list)
            and PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY
            in bridge_capabilities
            and isinstance(diagnostics, dict)
        ):
            candidates.append(
                _frontend_binding_from_native_diagnostics(diagnostics)
            )
        backends = row.get("backends")
        if isinstance(backends, list):
            for backend in backends:
                visit(backend)

    visit(value)
    unique = {
        (binding["bridge_pid"], binding["connection_generation"])
        for binding in candidates
    }
    if len(unique) != 1:
        raise ValueError(
            "frontend coat-of-arms probe requires one exact native bridge"
        )
    bridge_pid, connection_generation = unique.pop()
    return {
        "mode": "frontend",
        "revision": 0,
        "connection_generation": connection_generation,
        "bridge_pid": bridge_pid,
    }


def _frontend_binding_from_native_diagnostics(
    diagnostics: dict[str, object],
) -> dict[str, object]:
    hello = diagnostics.get("hello")
    if not isinstance(hello, dict):
        raise ValueError("frontend native bridge hello is unavailable")
    bridge_pid = diagnostics.get("bridge_pid")
    connection_generation = diagnostics.get("connection_generation")
    hello_capabilities = hello.get("capabilities")
    observed_sha256 = hello.get("expected_ck3_sha256")
    if not (
        diagnostics.get("connected") is True
        and diagnostics.get("semantic_state_available") is False
        and isinstance(bridge_pid, int)
        and not isinstance(bridge_pid, bool)
        and 1 <= bridge_pid <= 2**32 - 1
        and hello.get("pid") == bridge_pid
        and isinstance(connection_generation, int)
        and not isinstance(connection_generation, bool)
        and 1 <= connection_generation <= 2**64 - 1
        and hello.get("game_adapter_id")
        == COAT_OF_ARMS_SOURCE_V1_GAME_ADAPTER_ID
        and hello.get("game_adapter_status") == "ready"
        and hello.get("expected_ck3_version")
        == COAT_OF_ARMS_SOURCE_V1_GAME_VERSION
        and isinstance(observed_sha256, str)
        and observed_sha256.upper()
        == COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
        and hello.get("ck3_build_match") is True
        and isinstance(hello_capabilities, list)
        and PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY
        in hello_capabilities
    ):
        raise ValueError(
            "frontend native bridge is disconnected or not the exact build"
        )
    return {
        "mode": "frontend",
        "revision": 0,
        "connection_generation": connection_generation,
        "bridge_pid": bridge_pid,
    }


def normalize_native_coat_of_arms_source_v1_result(
    value: object,
    *,
    expected_source: EncodedCoatOfArmsSourceV1,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_apply: bool,
) -> dict[str, object]:
    """Validate the raw named-pipe result before Python adds its binding."""
    if not isinstance(expected_source, EncodedCoatOfArmsSourceV1):
        raise TypeError("expected_source must be encoded coat-of-arms source")
    native_revision = _uint64(
        expected_native_revision,
        "expected_native_revision",
        minimum=0,
    )
    date_raw = _int(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    apply = validate_coat_of_arms_source_probe_apply(expected_apply)
    result = _exact_object(
        value, _NATIVE_RESULT_FIELDS, "native coat-of-arms probe result"
    )
    observed_snapshot_revision = _uint64(
        result.get("snapshot_revision"),
        "snapshot_revision",
        minimum=0,
    )
    if (
        result.get("step") != PROBE_COAT_OF_ARMS_SOURCE_V1_STEP
        or result.get("accepted") is not True
        or result.get("backend_id") != "native-headless"
        or observed_snapshot_revision != native_revision
    ):
        raise ValueError("native coat-of-arms probe header is invalid")
    query_sequence = _uint64(
        result.get("query_sequence"), "query_sequence", minimum=1
    )
    probe = _exact_object(
        result.get("coat_of_arms_probe"),
        _NATIVE_PROBE_FIELDS,
        "native coat-of-arms probe",
    )
    observed_date_raw = _int(
        probe.get("date_raw"),
        "date_raw",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    if (
        probe.get("schema")
        != "xar.ck3.coat-of-arms-designer-probe.v1"
        or probe.get("schema_version") != 1
        or isinstance(probe.get("schema_version"), bool)
        or observed_date_raw != date_raw
        or probe.get("source_bytes") != expected_source.source_bytes
        or isinstance(probe.get("source_bytes"), bool)
    ):
        raise ValueError("native coat-of-arms probe payload header is invalid")
    provenance = _exact_object(
        probe.get("provenance"),
        _PROVENANCE_FIELDS,
        "native coat-of-arms probe provenance",
    )
    if provenance.get("backend_id") != COAT_OF_ARMS_SOURCE_V1_BACKEND_ID:
        raise ValueError("native coat-of-arms probe provenance is invalid")
    if probe.get("status") != result.get("status"):
        raise ValueError("native coat-of-arms status mirrors disagree")
    evidence = _normalize_evidence_fields(
        {
            **probe,
            # The native reader proves the byte count and exact clipboard
            # readback. Python binds the request bytes to their digest.
            "source_sha256": expected_source.source_sha256,
        },
        expected_source=expected_source,
        expected_apply=apply,
    )
    return {
        **evidence,
        "snapshot_revision": native_revision,
        "query_sequence": query_sequence,
    }


def normalize_coat_of_arms_source_v1_result(
    value: object,
    *,
    expected_source: EncodedCoatOfArmsSourceV1,
    expected_binding: dict[str, object],
    expected_apply: bool,
) -> dict[str, object]:
    """Validate one complete public MCP envelope and its exact source."""
    if not isinstance(expected_source, EncodedCoatOfArmsSourceV1):
        raise TypeError("expected_source must be encoded coat-of-arms source")
    apply = validate_coat_of_arms_source_probe_apply(expected_apply)
    binding = normalize_coat_of_arms_source_v1_binding(expected_binding)
    result = _exact_object(
        value, _RESULT_FIELDS, "coat-of-arms probe result"
    )
    if (
        result.get("schema") != "coat-of-arms-source-probe-v1"
        or result.get("schema_version") != 1
        or isinstance(result.get("schema_version"), bool)
        or result.get("step") != PROBE_COAT_OF_ARMS_SOURCE_V1_STEP
    ):
        raise ValueError("coat-of-arms probe header is invalid")
    evidence = _normalize_evidence_fields(
        result,
        expected_source=expected_source,
        expected_apply=apply,
    )
    observed_binding = normalize_coat_of_arms_source_v1_binding(
        result.get("binding")
    )
    if observed_binding != binding:
        raise ValueError("coat-of-arms probe revision binding changed")
    return {
        "schema": "coat-of-arms-source-probe-v1",
        "schema_version": 1,
        "step": PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
        **evidence,
        "binding": binding,
    }


def _normalize_evidence_fields(
    value: dict[str, object],
    *,
    expected_source: EncodedCoatOfArmsSourceV1,
    expected_apply: bool,
) -> dict[str, object]:
    status = value.get("status")
    if status not in {
        "applied",
        "detected",
        "not_detected",
        "apply_failed",
        "unavailable",
    }:
        raise ValueError("coat-of-arms probe status is invalid")
    detected = _bool(value.get("detected"), "detected")
    designer_observed = _bool(
        value.get("designer_observed"), "designer_observed"
    )
    clipboard_written = _bool(
        value.get("clipboard_written"), "clipboard_written"
    )
    clipboard_readback_matched = _bool(
        value.get("clipboard_readback_matched"),
        "clipboard_readback_matched",
    )
    apply_requested = _bool(
        value.get("apply_requested"), "apply_requested"
    )
    paste_invoked = _bool(value.get("paste_invoked"), "paste_invoked")
    applied = _bool(value.get("applied"), "applied")
    candidate_index = _uint32(
        value.get("candidate_index"), "candidate_index"
    )
    preview_handle = _uint32(
        value.get("preview_coat_of_arms_handle"),
        "preview_coat_of_arms_handle",
    )
    active_index = _uint32(
        value.get("active_coat_of_arms_index"),
        "active_coat_of_arms_index",
    )
    if apply_requested is not expected_apply:
        raise ValueError("coat-of-arms probe apply request changed")
    if clipboard_readback_matched and not clipboard_written:
        raise ValueError("clipboard readback requires a successful write")
    if detected and not designer_observed:
        raise ValueError("a detected coat of arms requires an observed designer")
    if detected and not (clipboard_written and clipboard_readback_matched):
        raise ValueError("detection requires exact clipboard readback")
    if paste_invoked and not (apply_requested and detected):
        raise ValueError("paste invocation requires a detected apply request")
    if applied and not paste_invoked:
        raise ValueError("an applied coat of arms requires paste invocation")
    if not apply_requested and (paste_invoked or applied):
        raise ValueError("detect-only probing cannot paste or apply")
    reason = value.get("reason")
    if status in {"applied", "detected"}:
        if reason is not None:
            raise ValueError("a successful coat-of-arms probe has no reason")
    else:
        reason = _bounded_reason(reason)
    if status == "applied":
        if not (detected and apply_requested and paste_invoked and applied):
            raise ValueError("applied coat-of-arms evidence is inconsistent")
    elif status == "detected":
        if not detected or apply_requested or paste_invoked or applied:
            raise ValueError("detect-only coat-of-arms evidence is inconsistent")
    elif status == "not_detected":
        if (
            detected
            or paste_invoked
            or applied
            or not designer_observed
            or not clipboard_written
            or not clipboard_readback_matched
            or reason != "engine_did_not_detect_coat_of_arms"
        ):
            raise ValueError("rejected coat-of-arms evidence is inconsistent")
    elif status == "apply_failed":
        if not (
            detected and apply_requested and paste_invoked and not applied
        ):
            raise ValueError("failed coat-of-arms apply evidence is inconsistent")
    elif detected or paste_invoked or applied:
        raise ValueError("unavailable coat-of-arms evidence is inconsistent")
    source_sha256 = value.get("source_sha256")
    source_bytes = value.get("source_bytes")
    if (
        not isinstance(source_sha256, str)
        or _SHA256.fullmatch(source_sha256) is None
        or source_sha256 != expected_source.source_sha256
        or source_bytes != expected_source.source_bytes
        or isinstance(source_bytes, bool)
    ):
        raise ValueError("coat-of-arms probe source identity changed")
    return {
        "status": status,
        "detected": detected,
        "designer_observed": designer_observed,
        "clipboard_written": clipboard_written,
        "clipboard_readback_matched": clipboard_readback_matched,
        "apply_requested": apply_requested,
        "paste_invoked": paste_invoked,
        "applied": applied,
        "candidate_index": candidate_index,
        "preview_coat_of_arms_handle": preview_handle,
        "active_coat_of_arms_index": active_index,
        "reason": reason,
        "source_sha256": expected_source.source_sha256,
        "source_bytes": expected_source.source_bytes,
    }


def _bounded_reason(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("an undetected coat of arms requires a reason")
    if any(ord(character) < 0x20 for character in value):
        raise ValueError("reason must not contain control characters")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("reason must be valid UTF-8") from error
    if len(encoded) > 1_024:
        raise ValueError("reason exceeds the 1024-byte limit")
    return value


def _exact_object(
    value: object, fields: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _uint64(value: object, name: str, *, minimum: int) -> int:
    return _int(value, name, minimum=minimum, maximum=2**64 - 1)


def _uint32(value: object, name: str) -> int:
    return _int(value, name, minimum=0, maximum=2**32 - 1)


def _int(
    value: object, name: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{name} must be an integer in [{minimum}, {maximum}]"
        )
    return value
