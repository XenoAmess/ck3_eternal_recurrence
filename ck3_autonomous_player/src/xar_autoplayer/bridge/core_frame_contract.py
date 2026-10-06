"""Exact 1.20.0.4 core prefix, independently readable before a full Snapshot."""
from __future__ import annotations

from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build


CORE_FRAME_V1_STEP = "query-core-frame-v1"
CORE_FRAME_V1_CAPABILITY = "game.query.core-frame.v1"
CORE_FRAME_V1_SCHEMA = "ck3_12004_core_frame_v1"
CORE_FRAME_V1_ADAPTER_ID = "ck3-1.20.0.4-msvc-x64"
CORE_FRAME_V1_BACKEND = "ck3-1.20.0.4-native-headless-main-thread"
CORE_FRAME_V1_EXCLUDED_FAMILIES = ["treasury", "domain", "military", "campaign"]
_PREFIX_FIELDS = {
    "date_raw", "speed", "paused", "local_player_id", "map_ready",
    "has_played_character", "played_character_id", "played_character_alive",
}
_RESULT_FIELDS = _PREFIX_FIELDS | {
    "schema", "game_version", "executable_sha256", "adapter_id", "backend",
    "status", "complete_snapshot", "core_available", "application_main_observed",
    "unavailable_reason", "excluded_snapshot_families",
}


def require_core_frame_hello_v1(hello: object) -> None:
    if not isinstance(hello, Mapping):
        raise ValueError("core frame requires the connected native hello")
    build = require_exact_native_build(
        hello.get("expected_ck3_version", hello.get("game_version")),
        hello.get("expected_ck3_sha256", hello.get("executable_sha256")),
    )
    if build != CK3_12004 or hello.get("game_adapter_status") != "ready":
        raise ValueError("core frame requires the ready exact 1.20.0.4 adapter")
    if CORE_FRAME_V1_CAPABILITY not in hello.get("capabilities", []):
        raise ValueError("native hello does not advertise the core-frame query")


def normalize_core_frame_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _RESULT_FIELDS:
        raise ValueError("core frame must contain the exact named prefix fields")
    if value["schema"] != CORE_FRAME_V1_SCHEMA:
        raise ValueError("core frame schema is not ck3_12004_core_frame_v1")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build != CK3_12004:
        raise ValueError("core frame does not identify the frozen 1.20.0.4 build")
    if (value["adapter_id"] != CORE_FRAME_V1_ADAPTER_ID
            or value["backend"] != CORE_FRAME_V1_BACKEND):
        raise ValueError("core frame does not identify the .4 app-main reader")
    if value["complete_snapshot"] is not False:
        raise ValueError("core frame must remain a partial observation")
    for name in ("core_available", "application_main_observed"):
        if type(value[name]) is not bool:
            raise ValueError(f"core frame {name} must be a boolean")
    if value["excluded_snapshot_families"] != CORE_FRAME_V1_EXCLUDED_FAMILIES:
        raise ValueError("core frame must name its excluded Snapshot families")
    if value["core_available"] is False:
        if (value["status"] != "unavailable"
                or not isinstance(value["unavailable_reason"], str)
                or not value["unavailable_reason"]
                or any(value[name] is not None for name in _PREFIX_FIELDS)):
            raise ValueError("unavailable core frame must carry reason and null prefix")
    else:
        if (value["status"] != "partial" or value["unavailable_reason"] is not None
                or value["application_main_observed"] is not True):
            raise ValueError("available core frame must be an observed partial prefix")
        for name in ("paused", "map_ready", "has_played_character", "played_character_alive"):
            if type(value[name]) is not bool:
                raise ValueError(f"core frame {name} must be a boolean")
        if type(value["date_raw"]) is not int or not -(2**31) <= value["date_raw"] < 2**31:
            raise ValueError("core frame date_raw must retain its native int32 value")
        if type(value["speed"]) is not int or not 1 <= value["speed"] <= 5:
            raise ValueError("core frame speed must use public levels 1 through 5")
        for name in ("local_player_id", "played_character_id"):
            if type(value[name]) is not int or not -(2**31) <= value[name] < 2**31:
                raise ValueError(f"core frame {name} must retain its native int32 identity")
        if value["has_played_character"]:
            if value["played_character_id"] == -1:
                raise ValueError("core frame played character lacks a full native ID")
        elif value["played_character_id"] != -1 or value["played_character_alive"]:
            raise ValueError("absent played character must retain the native sentinel")
    return {
        **value,
        "executable_sha256": build.executable_sha256,
        "excluded_snapshot_families": list(CORE_FRAME_V1_EXCLUDED_FAMILIES),
    }
