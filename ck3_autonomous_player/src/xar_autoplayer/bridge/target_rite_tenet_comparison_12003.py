"""Preserve an independently sampled explicit-Rite/named-Tenet comparison."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12003, require_exact_native_build


SCHEMA = "ck3_12003_target_rite_tenet_comparison_v1"
SIBLING_KEY = "target_rite_tenet_comparison"
_KEYS = {
    "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
    "date_raw", "played_character_id", "requested_target_rite_id", "tenet_key",
    "actor_rite", "target_rite", "same_rite", "same_faith",
    "named_comparison_ready", "status_values",
}
_SCOPE_KEYS = {
    "rite_id", "faith_id", "faith_main_rite_id", "current_is_main",
    "core_tenets_complete", "core_tenet_keys", "faith_main_core_tenets_complete",
    "faith_main_core_tenet_keys", "named_tenet_core_member",
    "named_tenet_faith_main_core_member", "named_tenet_status",
}
_STATUS_VALUES = {"unknown": 0, "known": 1, "prohibited": 2, "permitted": 3, "core": 4}
_UNAVAILABLE_REASONS = {
    "bindings_unavailable", "played_character_unavailable", "frame_not_paused",
    "actor_rite_unavailable", "target_rite_unavailable", "actor_faith_unavailable",
    "target_faith_unavailable", "actor_main_rite_unavailable",
    "target_main_rite_unavailable", "actor_core_tenets_unavailable",
    "actor_main_core_tenets_unavailable", "target_core_tenets_unavailable",
    "target_main_core_tenets_unavailable", "tenet_database_unavailable",
    "tenet_definitions_unavailable", "tenet_definition_key_unavailable",
    "tenet_definition_unavailable", "actor_tenet_state_unavailable",
    "target_tenet_state_unavailable", "state_changed", "tenet_native_read_unavailable",
}


def _full_reference(value: object) -> bool:
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def _core_keys(value: object) -> bool:
    return type(value) is list and all(type(key) is str and bool(key) for key in value)


def _scope(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or set(value) != _SCOPE_KEYS:
        raise ValueError("native target Rite Tenet comparison scope is malformed")
    if (not all(_full_reference(value[key]) for key in (
                "rite_id", "faith_id", "faith_main_rite_id"))
            or type(value["current_is_main"]) is not bool
            or value["current_is_main"] != (value["rite_id"] == value["faith_main_rite_id"])
            or value["core_tenets_complete"] is not True
            or value["faith_main_core_tenets_complete"] is not True
            or not _core_keys(value["core_tenet_keys"])
            or not _core_keys(value["faith_main_core_tenet_keys"])
            or type(value["named_tenet_core_member"]) is not bool
            or type(value["named_tenet_faith_main_core_member"]) is not bool
            or type(value["named_tenet_status"]) is not int
            or not 0 <= value["named_tenet_status"] <= 4):
        raise ValueError("native target Rite Tenet comparison scope fields are malformed")
    # Native membership is a literal pointer observation. Native status is a
    # separate getter result; neither is reconstructed from the other.
    return value


def normalize_target_rite_tenet_comparison_12003(
    value: object, *, snapshot: Mapping[str, object],
    tenet_rows: Mapping[str, object], target_rite_id: int, tenet_key: str,
) -> dict[str, object]:
    """Bind the sibling to its owner frame and request without changing sources."""
    if (not _full_reference(target_rite_id)
            or type(tenet_key) is not str or not tenet_key
            or len(tenet_key.encode("utf-8")) > 128):
        raise ValueError("target_rite_id and tenet_key must identify the requested comparison")
    if (not isinstance(value, dict) or set(value) != _KEYS
            or value["schema"] != SCHEMA or value["read_only"] is not True):
        raise ValueError("native target Rite Tenet comparison schema is malformed")
    if (require_exact_native_build(
            tenet_rows.get("game_version"), tenet_rows.get("executable_sha256"),
        ) != CK3_12003 or private_native_build_identity(snapshot) != CK3_12003):
        raise ValueError("native target Rite Tenet comparison belongs to another build")
    if (type(value["available"]) is not bool
            or type(value["named_comparison_ready"]) is not bool
            or value["named_comparison_ready"] != value["available"]
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or not -0x80000000 <= value["date_raw"] <= 0x7FFFFFFF
            or not _full_reference(value["played_character_id"])
            or not _full_reference(value["requested_target_rite_id"])
            or type(value["tenet_key"]) is not str or not value["tenet_key"]):
        raise ValueError("native target Rite Tenet comparison scalar fields are malformed")
    states = value["status_values"]
    if (not isinstance(states, Mapping) or states != _STATUS_VALUES
            or any(type(state) is not int for state in states.values())):
        raise ValueError("native target Rite Tenet comparison lost its native status values")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or not _full_reference(actor.get("character_id"))
            or type(snapshot.get("date_raw")) is not int
            or type(tenet_rows.get("capture_epoch")) is not int
            or type(tenet_rows.get("date_raw")) is not int
            or not _full_reference(tenet_rows.get("played_character_id"))
            or value["played_character_id"] != actor["character_id"]
            or value["played_character_id"] != tenet_rows["played_character_id"]
            or value["date_raw"] != snapshot["date_raw"]
            or value["date_raw"] != tenet_rows["date_raw"]
            or value["capture_epoch"] != tenet_rows["capture_epoch"]
            or value["requested_target_rite_id"] != target_rite_id
            or value["tenet_key"] != tenet_key):
        raise ValueError("native target Rite Tenet comparison differs from its queried frame/request")
    if value["available"]:
        actor_rite = _scope(value["actor_rite"])
        target_rite = _scope(value["target_rite"])
        if (value["unavailable_reason"] is not None
                or target_rite["rite_id"] != target_rite_id
                or type(value["same_rite"]) is not bool
                or value["same_rite"] != (actor_rite["rite_id"] == target_rite["rite_id"])
                or type(value["same_faith"]) is not bool
                or value["same_faith"] != (actor_rite["faith_id"] == target_rite["faith_id"])):
            raise ValueError("native target Rite Tenet comparison readiness is malformed")
        current = tenet_rows.get("current_rite")
        main = tenet_rows.get("faith_main_rite")
        if ((current is not None and (
                    not isinstance(current, Mapping)
                    or actor_rite["rite_id"] != current.get("rite_id")))
                or (main is not None and (
                    not isinstance(main, Mapping)
                    or actor_rite["faith_main_rite_id"] != main.get("rite_id")))
                or (tenet_rows.get("faith_id") is not None
                    and actor_rite["faith_id"] != tenet_rows["faith_id"])):
            raise ValueError("native target Rite Tenet comparison differs from its actor Rite sources")
    elif (type(value["unavailable_reason"]) is not str
            or value["unavailable_reason"] not in _UNAVAILABLE_REASONS
            or any(value[key] is not None for key in (
                "actor_rite", "target_rite", "same_rite", "same_faith"))):
        raise ValueError("native target Rite Tenet comparison lost its typed unavailable observation")
    # Keep each Core collection in its own native order, including duplicates.
    # A failed sibling does not change the independent existing Tenet DTO.
    return deepcopy(value)
