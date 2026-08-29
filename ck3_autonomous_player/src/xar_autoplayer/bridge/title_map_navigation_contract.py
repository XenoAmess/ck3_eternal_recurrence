"""Strict typed contract for centering CK3 on one landed-title stable key."""

from __future__ import annotations

import copy
import math
import re
import struct
from typing import Final


CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY: Final = (
    "game.command.center-map-on-landed-title-v1"
)
CENTER_MAP_ON_LANDED_TITLE_V1_STEP: Final = (
    "center-map-on-landed-title-v1"
)
TITLE_MAP_NAVIGATION_V1_GAME_VERSION: Final = "1.19.0.6"
TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
TITLE_MAP_NAVIGATION_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-title-map-navigation-v1"
)
TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE: Final = (
    "exact-build-native-camera-settled-v1"
)

TITLE_MAP_NAVIGATION_V1_REJECTION_CODES: Final = frozenset(
    {
        "unsupported_build",
        "requires_owning_thread",
        "requires_paused",
        "map_not_ready",
        "title_key_not_found",
        "title_generation_mismatch",
        "title_not_centerable",
        "camera_state_unavailable",
        "state_changed",
        "submission_failed",
        "internal_error",
    }
)

_LANDED_TITLE_KEY = re.compile(r"[ekdcb]_[a-z0-9][a-z0-9_]*")
_RESULT_FIELDS = {
    "schema_version",
    "step",
    "accepted",
    "status",
    "title",
    "binding",
    "native_action_ack",
    "camera_center",
    "source",
}
_TITLE_FIELDS = {
    "key",
    "title_id",
    "tier_raw",
    "tier_key",
    "anchor_kind",
    "capital_province_id",
    "bounds_extent",
    "map_x_adjustment",
}
_NATIVE_BINDING_FIELDS = {
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
}
_PUBLIC_BINDING_FIELDS = {
    *_NATIVE_BINDING_FIELDS,
    "episode_run_id",
    "connection_generation",
}
_NATIVE_ACTION_ACK_FIELDS = {"sequence", "status"}
_CAMERA_CENTER_FIELDS = {
    "status",
    "postcondition_verified",
    "expected_position_xyz",
    "current_state",
    "target_state",
    "zoom_index",
    "expected_zoom_value",
    "settled",
    "target_write_blocked",
    "completion_predicate",
}
_SOURCE_FIELDS = {
    "game_version",
    "executable_sha256",
    "backend_id",
}
_TIER_KEYS = {
    1: "barony",
    2: "county",
    3: "duchy",
    4: "kingdom",
    5: "empire",
    6: "hegemony",
}
_FLOAT32_MAX: Final = 3.4028234663852886e38


def validate_landed_title_key(value: object) -> str:
    """Accept only a canonical, byte-bounded landed-title stable key."""
    if not isinstance(value, str) or not value:
        raise ValueError("title_key must be a non-empty string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("title_key must be valid UTF-8") from error
    if len(encoded) > 1_024:
        raise ValueError("title_key exceeds the 1024-byte stable-key limit")
    if _LANDED_TITLE_KEY.fullmatch(value) is None:
        raise ValueError("title_key must be a canonical landed-title stable key")
    return value


def normalize_native_title_map_navigation_v1_result(
    value: object,
    *,
    expected_title_key: str,
    expected_snapshot_id: str,
    expected_native_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    """Validate the raw named-pipe result before adding Python-only binding."""
    key = validate_landed_title_key(expected_title_key)
    expected_binding = {
        "snapshot_id": _nonempty_string(
            expected_snapshot_id, "expected_snapshot_id"
        ),
        "revision": _positive_uint64(
            expected_native_revision, "expected_native_revision"
        ),
        "native_revision": _positive_uint64(
            expected_native_revision, "expected_native_revision"
        ),
        "date_raw": _signed_int64(expected_date_raw, "expected_date_raw"),
    }
    if not isinstance(value, dict) or set(value) != _RESULT_FIELDS | {
        "backend_id"
    }:
        raise ValueError("native title-map result has a malformed envelope")
    if value.get("backend_id") != "native-headless":
        raise ValueError("native title-map transport backend is invalid")
    payload = {key_name: value[key_name] for key_name in _RESULT_FIELDS}
    return _normalize_result(
        payload,
        expected_title_key=key,
        expected_binding=expected_binding,
        binding_fields=_NATIVE_BINDING_FIELDS,
    )


def normalize_title_map_navigation_v1_result(
    value: object,
    *,
    expected_title_key: str,
    expected_binding: dict[str, object],
) -> dict[str, object]:
    """Validate the complete public MCP result and its session binding."""
    key = validate_landed_title_key(expected_title_key)
    binding = normalize_title_map_navigation_v1_binding(expected_binding)
    return _normalize_result(
        value,
        expected_title_key=key,
        expected_binding=binding,
        binding_fields=_PUBLIC_BINDING_FIELDS,
    )


def normalize_title_map_navigation_v1_binding(
    value: object,
) -> dict[str, object]:
    """Normalize the six fields that bind one presentation-only command."""
    binding = _exact_object(
        value, _PUBLIC_BINDING_FIELDS, "title-map binding"
    )
    snapshot_id = _nonempty_string(
        binding.get("snapshot_id"), "binding.snapshot_id"
    )
    episode_run_id = _nonempty_string(
        binding.get("episode_run_id"), "binding.episode_run_id"
    )
    return {
        "snapshot_id": snapshot_id,
        "revision": _non_negative_uint64(
            binding.get("revision"), "binding.revision"
        ),
        "native_revision": _positive_uint64(
            binding.get("native_revision"), "binding.native_revision"
        ),
        "date_raw": _signed_int64(
            binding.get("date_raw"), "binding.date_raw"
        ),
        "episode_run_id": episode_run_id,
        "connection_generation": _positive_uint64(
            binding.get("connection_generation"),
            "binding.connection_generation",
        ),
    }


def _normalize_result(
    value: object,
    *,
    expected_title_key: str,
    expected_binding: dict[str, object],
    binding_fields: set[str],
) -> dict[str, object]:
    result = _exact_object(value, _RESULT_FIELDS, "title-map result")
    if (
        result.get("schema_version") != 1
        or result.get("step") != CENTER_MAP_ON_LANDED_TITLE_V1_STEP
        or result.get("accepted") is not True
    ):
        raise ValueError("title-map result header is invalid")
    status = result.get("status")
    if status not in {"centered", "already_centered"}:
        raise ValueError("title-map result status is invalid")

    title = _exact_object(result.get("title"), _TITLE_FIELDS, "title")
    key = validate_landed_title_key(title.get("key"))
    if key != expected_title_key:
        raise ValueError("title-map result resolved another stable key")
    title_id = _positive_int32(title.get("title_id"), "title.title_id")
    tier_raw = _int(
        title.get("tier_raw"), "title.tier_raw", minimum=1, maximum=6
    )
    if title.get("tier_key") != _TIER_KEYS[tier_raw]:
        raise ValueError("title-map result tier pair is invalid")
    if title.get("anchor_kind") != "title_bounds_center":
        raise ValueError("title-map result anchor kind is invalid")
    capital_province_id = _optional_positive_int32(
        title.get("capital_province_id"), "title.capital_province_id"
    )
    bounds_extent = _signed_int32_vector(
        title.get("bounds_extent"), 4, "title.bounds_extent"
    )
    map_x_adjustment = _signed_int32(
        title.get("map_x_adjustment"), "title.map_x_adjustment"
    )
    min_x, min_z, max_x, max_z = bounds_extent
    if min_x > max_x or min_z > max_z:
        raise ValueError("title-map result bounds extent is inverted")

    binding = _exact_object(
        result.get("binding"), binding_fields, "title-map binding"
    )
    if any(binding.get(field) != expected for field, expected in expected_binding.items()):
        raise ValueError("title-map result binding changed")

    action_ack = _exact_object(
        result.get("native_action_ack"),
        _NATIVE_ACTION_ACK_FIELDS,
        "native_action_ack",
    )
    sequence = action_ack.get("sequence")
    if status == "centered":
        if (
            action_ack.get("status") != "dispatched"
            or _optional_positive_uint64(sequence, "native_action_ack.sequence")
            is None
        ):
            raise ValueError("centered title-map result lacks dispatch ACK")
    elif action_ack.get("status") != "not_needed" or sequence is not None:
        raise ValueError("already-centered title-map result invented a dispatch")

    camera = _exact_object(
        result.get("camera_center"),
        _CAMERA_CENTER_FIELDS,
        "camera_center",
    )
    expected_position = _finite_f32_vector(
        camera.get("expected_position_xyz"),
        3,
        "camera_center.expected_position_xyz",
    )
    current_state = _finite_f32_vector(
        camera.get("current_state"),
        6,
        "camera_center.current_state",
    )
    target_state = _finite_f32_vector(
        camera.get("target_state"),
        6,
        "camera_center.target_state",
    )
    zoom_index = _non_negative_int32(
        camera.get("zoom_index"), "camera_center.zoom_index"
    )
    expected_zoom_value = _finite_f32_number(
        camera.get("expected_zoom_value"),
        "camera_center.expected_zoom_value",
    )
    bounds_center = _native_title_bounds_center(
        bounds_extent, map_x_adjustment
    )
    if (
        camera.get("status") != status
        or camera.get("postcondition_verified") is not True
        or camera.get("settled") is not True
        or camera.get("target_write_blocked") is not False
        or not _same_f32_vector(current_state, target_state)
        or not _same_f32_vector(target_state[:3], expected_position)
        or not _same_f32_vector(expected_position, bounds_center)
        or not _same_f32_vector(
            [current_state[3], target_state[3]],
            [expected_zoom_value, expected_zoom_value],
        )
        or camera.get("completion_predicate")
        != TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE
    ):
        raise ValueError("title-map camera postcondition is invalid")
    source = _exact_object(result.get("source"), _SOURCE_FIELDS, "source")
    if (
        source.get("game_version") != TITLE_MAP_NAVIGATION_V1_GAME_VERSION
        or not isinstance(source.get("executable_sha256"), str)
        or str(source["executable_sha256"]).upper()
        != TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
        or source.get("backend_id") != TITLE_MAP_NAVIGATION_V1_BACKEND_ID
    ):
        raise ValueError("title-map source does not match the frozen exact build")

    normalized_title = {
        **title,
        "key": key,
        "title_id": title_id,
        "tier_raw": tier_raw,
        "tier_key": _TIER_KEYS[tier_raw],
        "anchor_kind": "title_bounds_center",
        "capital_province_id": capital_province_id,
        "bounds_extent": bounds_extent,
        "map_x_adjustment": map_x_adjustment,
    }
    normalized_source = {
        **source,
        "executable_sha256": TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
    }
    return {
        **copy.deepcopy(result),
        "title": normalized_title,
        "binding": copy.deepcopy(expected_binding),
        "native_action_ack": {
            "sequence": sequence,
            "status": action_ack["status"],
        },
        "camera_center": {
            **camera,
            "expected_position_xyz": expected_position,
            "current_state": current_state,
            "target_state": target_state,
            "zoom_index": zoom_index,
            "expected_zoom_value": expected_zoom_value,
        },
        "source": normalized_source,
    }


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


def _int(
    value: object, name: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _positive_int32(value: object, name: str) -> int:
    return _int(value, name, minimum=1, maximum=2**31 - 1)


def _non_negative_int32(value: object, name: str) -> int:
    return _int(value, name, minimum=0, maximum=2**31 - 1)


def _signed_int32(value: object, name: str) -> int:
    return _int(value, name, minimum=-(2**31), maximum=2**31 - 1)


def _optional_positive_int32(value: object, name: str) -> int | None:
    return None if value is None else _positive_int32(value, name)


def _non_negative_uint64(value: object, name: str) -> int:
    return _int(value, name, minimum=0, maximum=2**64 - 1)


def _positive_uint64(value: object, name: str) -> int:
    return _int(value, name, minimum=1, maximum=2**64 - 1)


def _optional_positive_uint64(value: object, name: str) -> int | None:
    return None if value is None else _positive_uint64(value, name)


def _finite_f32_vector(
    value: object, size: int, name: str
) -> list[float]:
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{name} must be an array of {size} finite f32 numbers")
    normalized: list[float] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{name}[{index}] must be a finite f32 number")
        number = float(item)
        if not math.isfinite(number) or abs(number) > _FLOAT32_MAX:
            raise ValueError(f"{name}[{index}] must be a finite f32 number")
        try:
            rounded = struct.unpack("<f", struct.pack("<f", number))[0]
        except (OverflowError, struct.error) as error:
            raise ValueError(
                f"{name}[{index}] must be a finite f32 number"
            ) from error
        if not math.isfinite(rounded):
            raise ValueError(f"{name}[{index}] must be a finite f32 number")
        normalized.append(rounded)
    return normalized


def _finite_f32_number(value: object, name: str) -> float:
    return _finite_f32_vector([value], 1, name)[0]


def _signed_int32_vector(
    value: object, size: int, name: str
) -> list[int]:
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{name} must be an array of {size} signed int32 values")
    return [
        _signed_int32(item, f"{name}[{index}]")
        for index, item in enumerate(value)
    ]


def _wrapped_int32(value: int) -> int:
    unsigned = value & 0xFFFF_FFFF
    return unsigned - 2**32 if unsigned >= 2**31 else unsigned


def _native_signed_midpoint(left: int, right: int) -> int:
    total = _wrapped_int32(left + right)
    biased = _wrapped_int32(total - (total >> 31))
    return biased >> 1


def _native_title_bounds_center(
    bounds_extent: list[int], map_x_adjustment: int
) -> list[float]:
    min_x, min_z, max_x, max_z = bounds_extent
    center_x = _native_signed_midpoint(min_x, max_x)
    center_z = _native_signed_midpoint(min_z, max_z)
    adjusted_x = _wrapped_int32(center_x - map_x_adjustment)
    return [
        struct.unpack("<f", struct.pack("<f", adjusted_x))[0],
        0.0,
        struct.unpack("<f", struct.pack("<f", center_z))[0],
    ]


def _same_f32_vector(left: list[float], right: list[float]) -> bool:
    return len(left) == len(right) and all(
        struct.pack("<f", left_item) == struct.pack("<f", right_item)
        for left_item, right_item in zip(left, right)
    )


def _signed_int64(value: object, name: str) -> int:
    return _int(value, name, minimum=-(2**63), maximum=2**63 - 1)
