"""Strict actual4 current custody of a retained full character ID."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build


_SCHEMA = "xar.ck3.prisoner-retained-target-state-12004-v1"
_FIELDS = {
    "schema", "build_version", "executable_sha256", "available",
    "unavailable_reason", "snapshot_revision", "date_raw",
    "actor_character_id", "target_character_id", "target_alive",
    "is_imprisoned", "jailer_character_id", "custody_state",
}


def normalize_prisoner_retained_target_state_12004(
    value: object, *, native_revision: int, date_raw: int,
    player_character_id: int, target_character_id: int,
) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ValueError("prisoner retained target state fields are malformed")
    if (value.get("schema") != _SCHEMA
            or require_exact_native_build(value.get("build_version"),
                                          value.get("executable_sha256")) != CK3_12004
            or type(value.get("available")) is not bool
            or not isinstance(value.get("unavailable_reason"), str)):
        raise ValueError("prisoner retained target state source identity is malformed")
    expected = {"snapshot_revision": native_revision, "date_raw": date_raw,
                "actor_character_id": player_character_id,
                "target_character_id": target_character_id}
    if any(type(raw) is not int or raw <= 0 or type(value.get(key)) is not int
           or value[key] != raw for key, raw in expected.items()):
        raise ValueError("prisoner retained target state differs from the current pair/frame")
    if not (0 < player_character_id < 0xFFFFFFFF
            and 0 < target_character_id < 0xFFFFFFFF
            and player_character_id != target_character_id):
        raise ValueError("prisoner retained target state requires distinct full character IDs")
    state = value["custody_state"]
    alive, imprisoned, jailer = (value["target_alive"], value["is_imprisoned"],
                                 value["jailer_character_id"])
    if not value["available"]:
        valid = (bool(value["unavailable_reason"]) and state == "unavailable"
                 and alive is None and imprisoned is None and jailer is None)
    elif value["unavailable_reason"]:
        valid = False
    elif state == "dead":
        valid = alive is False and imprisoned is None and jailer is None
    elif state == "free":
        valid = alive is True and imprisoned is False and jailer is None
    elif state in {"held_by_player", "held_by_other"}:
        valid = (alive is True and imprisoned is True and type(jailer) is int
                 and 0 < jailer < 0xFFFFFFFF
                 and (jailer == player_character_id) is (state == "held_by_player"))
    else:
        valid = False
    if not valid:
        raise ValueError("prisoner retained target custody fields are inconsistent")
    return copy.deepcopy(dict(value))
