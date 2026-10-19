"""Optional diagnostics from a future camera provider; no Game/OS I/O.

Legacy status7 remains ambiguous without this exact extension. This decoder
does not repair old records, select a camera, retry a request, or grant coverage.
The caller copies base Result and tail under ONE existing result_sequence check.
"""
from __future__ import annotations

import ctypes
import math
import struct
from collections.abc import Mapping

DIAGNOSTICS_OFFSET = 0x18000
DIAGNOSTICS_BYTES = 168
DIAGNOSTICS_MAGIC = 0x44434158
MAPPING_BYTES = 131072
MAPPING_MAGIC = 0x43524158
LEGACY_RESULT_REGION_END = 65832  # v1: Result offset192 + sizeof(Result)65640
REASONS = {1: "current_read_failed", 2: "target_read_failed",
           3: "current_nonfinite", 4: "target_changed"}


class CameraSettleDiagnosticsV1(ctypes.LittleEndianStructure):
    _fields_ = [
        ("magic", ctypes.c_uint32), ("version", ctypes.c_uint32),
        ("byte_size", ctypes.c_uint32), ("request_sequence", ctypes.c_uint32),
        ("legacy_status", ctypes.c_uint32), ("reason", ctypes.c_uint32),
        ("provider_pid", ctypes.c_uint32), ("actor", ctypes.c_int32),
        ("submit_date_raw", ctypes.c_int32), ("request_date_raw", ctypes.c_int32),
        ("request_mode", ctypes.c_uint32), ("observation_flags", ctypes.c_uint32),
        ("target_difference_mask", ctypes.c_uint32), ("county_count", ctypes.c_uint32),
        ("client_width", ctypes.c_uint32), ("client_height", ctypes.c_uint32),
        ("zoom_index", ctypes.c_int32), ("bounds", ctypes.c_int32 * 4),
        ("expected_target", ctypes.c_float * 6), ("observed_current", ctypes.c_float * 6),
        ("observed_target", ctypes.c_float * 6), ("reserved", ctypes.c_uint32),
        ("observation_uptime_ms", ctypes.c_uint64),
    ]


assert ctypes.sizeof(CameraSettleDiagnosticsV1) == DIAGNOSTICS_BYTES
assert CameraSettleDiagnosticsV1.expected_target.offset == 84
assert CameraSettleDiagnosticsV1.observed_current.offset == 108
assert CameraSettleDiagnosticsV1.observed_target.offset == 132
assert CameraSettleDiagnosticsV1.observation_uptime_ms.offset == 160
assert DIAGNOSTICS_OFFSET + DIAGNOSTICS_BYTES <= MAPPING_BYTES


def _unknown(reason: str) -> dict:
    return {"schema": "xar.ck3.camera-settle-diagnostics/v1",
            "available": False, "reason": reason}


def _finite(values) -> bool:
    return all(math.isfinite(value) for value in values)


def _values(values, known: bool):
    # JSON-safe; raw float bits below retain a read NaN/Inf without fake zero.
    return [float(value) if math.isfinite(value) else None for value in values] if known else None


def _bits(raw: bytes, field: str, known: bool):
    return list(struct.unpack_from("<6I", raw, getattr(CameraSettleDiagnosticsV1, field).offset)) if known else None


def decode_camera_settle_diagnostics_v1(
    raw: bytes, *, result: Mapping, mapping_identity: tuple,
    result_region_end: int, request_binding: Mapping | None,
) -> dict:
    """Fail closed only this optional observation; do not fail legacy camera work."""
    if (not isinstance(mapping_identity, tuple)
            or mapping_identity[:2] != (MAPPING_MAGIC, 1)
            or len(mapping_identity) != 3
            or type(mapping_identity[2]) is not int or mapping_identity[2] <= 0
            or type(result_region_end) is not int
            or result_region_end != LEGACY_RESULT_REGION_END
            or result_region_end > DIAGNOSTICS_OFFSET
            or len(raw) != DIAGNOSTICS_BYTES):
        return _unknown("mapping_layout_or_identity_mismatch")
    diag = CameraSettleDiagnosticsV1.from_buffer_copy(raw)
    if diag.magic == 0:
        return _unknown("legacy_or_absent_extension")
    if (diag.magic != DIAGNOSTICS_MAGIC or diag.version != 1
            or diag.byte_size != DIAGNOSTICS_BYTES or diag.reserved
            or diag.legacy_status != 7 or diag.reason not in REASONS):
        return _unknown("diagnostic_layout_or_status_mismatch")
    if (diag.provider_pid != mapping_identity[2] or diag.actor <= 0
            or result.get("status") != "target_changed"
            or result.get("request_sequence") != diag.request_sequence
            or diag.request_sequence <= 0 or diag.request_sequence & 1
            or result.get("actor_character_id") != diag.actor
            or result.get("date_raw") != diag.submit_date_raw):
        return _unknown("result_binding_mismatch")
    binding = request_binding
    if not isinstance(binding, Mapping):
        return _unknown("request_context_not_observed")
    frame = binding.get("source_frame")
    if (not isinstance(frame, Mapping)
            or binding.get("request_sequence") != diag.request_sequence
            or frame.get("bridge_pid") != diag.provider_pid
            or frame.get("actor_character_id") != diag.actor
            or frame.get("date_raw") != diag.request_date_raw
            or type(frame.get("connection_generation")) is not int
            or frame["connection_generation"] <= 0
            or not isinstance(frame.get("episode_run_id"), str)
            or not 0 < len(frame["episode_run_id"]) <= 256
            or diag.submit_date_raw < diag.request_date_raw
            or diag.submit_date_raw - diag.request_date_raw > 7 * 24):
        return _unknown("request_context_binding_mismatch")
    if (diag.request_mode not in (1, 2) or not 0 <= diag.county_count <= 16384
            or diag.client_width < 320 or diag.client_height < 240
            or diag.zoom_index < 0
            or result.get("county_count") != diag.county_count
            or result.get("client_size") != [diag.client_width, diag.client_height]
            or result.get("zoom_index") != diag.zoom_index
            or result.get("bounds") != list(diag.bounds)
            or result.get("target") != list(diag.expected_target)
            or diag.bounds[0] > diag.bounds[2] or diag.bounds[1] > diag.bounds[3]
            or not _finite(diag.expected_target)):
        return _unknown("submitted_geometry_binding_mismatch")
    flags = diag.observation_flags
    current_read, target_read = bool(flags & 1), bool(flags & 2)
    if (flags & ~15 or (target_read and not current_read)
            or bool(flags & 4) != (current_read and _finite(diag.observed_current))
            or bool(flags & 8) != (target_read and _finite(diag.observed_target))):
        return _unknown("observation_flags_mismatch")
    if not current_read:
        reason, differences = 1, 0
    elif not target_read:
        reason, differences = 2, 0
    elif not _finite(diag.observed_current):
        reason, differences = 3, 0
    else:
        differences = sum(1 << index for index, (seen, expected) in enumerate(
            zip(diag.observed_target, diag.expected_target)) if seen != expected)
        reason = 4 if differences else 0
    if reason != diag.reason or differences != diag.target_difference_mask:
        return _unknown("failure_reason_or_difference_mismatch")
    return {
        "schema": "xar.ck3.camera-settle-diagnostics/v1", "available": True,
        "reason": REASONS[reason], "legacy_status": "target_changed",
        "request_sequence": diag.request_sequence,
        "provider": {"channel": "native-camera-presentation-v1",
                     "pid": diag.provider_pid, "mapping_version": 1,
                     "native_epoch": None, "game_creation_filetime": None},
        "request_source_frame": {key: frame[key] for key in (
            "actor_character_id", "date_raw", "bridge_pid",
            "connection_generation", "episode_run_id")},
        "submit_snapshot_date_raw": diag.submit_date_raw,
        "observation_uptime_ms": diag.observation_uptime_ms,
        "observation_game_frame": None,
        "current_read_success": current_read, "target_read_success": target_read,
        "current_finite": bool(flags & 4) if current_read else None,
        "target_finite": bool(flags & 8) if target_read else None,
        "observed_current": _values(diag.observed_current, current_read),
        "observed_current_float_bits": _bits(raw, "observed_current", current_read),
        "observed_target": _values(diag.observed_target, target_read),
        "observed_target_float_bits": _bits(raw, "observed_target", target_read),
        "target_difference_mask": differences,
        "submitted_geometry": {"county_count": diag.county_count,
            "client_size": [diag.client_width, diag.client_height],
            "bounds": list(diag.bounds), "zoom_index": diag.zoom_index,
            "expected_target": list(diag.expected_target), "request_mode": diag.request_mode},
        "same_frame_with_gameplay_claim": False,
        "camera_postcondition_verified": False, "coverage_verified": False,
    }

