"""Read numeric Rite caches and the separate native Faith final threshold."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-numeric-special-parameters-v1"
DOMAIN_KEY = "player_religion_numeric_special_parameters_v1"
PERMISSION = "allow_private_player_religion_numeric_special_parameters_query"
SCHEMA = "ck3_12002_rite_numeric_special_parameters_v1"
FINAL_SCHEMA = "ck3_12002_faith_numeric_final_v1"
_BASE_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id",
}
_PARAMETERS = {
    "minimum_fervor": (1, "fervor_points"),
    "fervor_per_holy_site": (100000, "yearly_fervor_per_controlled_holy_site"),
    "bonus_fervor_gain": (100000, "yearly_fervor_gain_bonus"),
    "bonus_heresy_protection": (1, "heresy_protection_count_bonus"),
    "heresy_threshold": (100000, "fervor_threshold_adjustment"),
}


def _reference(value: object) -> bool:
    return value is None or (type(value) is int and 0 <= value <= 0xFFFFFFFF)


def _signed_raw(value: object) -> bool:
    return type(value) is int and -(1 << 63) <= value < (1 << 63)


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _native_frame(value: Mapping[str, object], *, snapshot: Mapping[str, object]) -> None:
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot):
        raise ValueError("native religion numeric observation belongs to another build")
    if (type(value.get("available")) is not bool
            or type(value.get("capture_epoch")) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value.get("date_raw")) is not int
            or type(value.get("played_character_id")) is not int):
        raise ValueError("native religion numeric observation scalar fields are malformed")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (value.get("unavailable_reason") is not None or not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")):
            raise ValueError("native religion numeric observation differs from the queried player frame")
    elif not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
        raise ValueError("native religion numeric observation lost its typed failure")


def _numeric_scope(value: object) -> None:
    if value is None:
        return
    if (not isinstance(value, Mapping)
            or set(value) != {"rite_id", "observed_special_parameters_complete", "parameters"}
            or not _reference(value.get("rite_id"))
            or value.get("observed_special_parameters_complete") is not True
            or not isinstance(value.get("parameters"), list)
            or len(value["parameters"]) != len(_PARAMETERS)):
        raise ValueError("native numeric special cache scope is malformed")
    seen = set()
    for row in value["parameters"]:
        if not isinstance(row, Mapping) or set(row) != {"key", "raw", "scale", "value", "state", "unit"}:
            raise ValueError("native numeric special cache entry is malformed")
        key = row.get("key")
        if not isinstance(key, str) or key not in _PARAMETERS or key in seen or not _signed_raw(row.get("raw")):
            raise ValueError("native numeric special cache key/raw is malformed")
        seen.add(key)
        scale, unit = _PARAMETERS[key]
        if type(row.get("scale")) is not int or row["scale"] != scale or row.get("unit") != unit:
            raise ValueError("native numeric special cache unit/scale changed")
        unset = key == "minimum_fervor" and row["raw"] == -1
        if ((unset and (row.get("state") != "unset" or row.get("value") is not None))
                or (not unset and (row.get("state") != "value" or not _number(row.get("value"))))):
            raise ValueError("native numeric special cache lost its unset/value distinction")


def normalize_player_religion_numeric_special_parameters_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    keys = _BASE_KEYS | {
        "faith_id", "faith_numeric_consumer_source", "authored_presence_provenance_observed",
        "supported_key_count", "current_rite", "faith_main_rite",
    }
    if not isinstance(value, dict) or set(value) != keys or value.get("schema") != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native numeric special cache schema is malformed")
    _native_frame(value, snapshot=snapshot)
    if (not _reference(value["faith_id"])
            or value["faith_numeric_consumer_source"] != "faith_main_rite"
            or value["authored_presence_provenance_observed"] is not False
            or type(value["supported_key_count"]) is not int or value["supported_key_count"] != 5):
        raise ValueError("native numeric special cache provenance is malformed")
    _numeric_scope(value["current_rite"])
    _numeric_scope(value["faith_main_rite"])
    return deepcopy(value)


def normalize_faith_numeric_final_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    keys = _BASE_KEYS | {
        "current_rite_id", "faith_id", "main_rite_id", "value_state",
        "main_rite_adjustment_raw", "native_define_raw", "final_heresy_threshold_raw",
        "final_heresy_threshold", "scale", "unit", "source", "native_getter_rva", "native_define_rva",
    }
    if not isinstance(value, dict) or set(value) != keys or value.get("schema") != private_native_schema(FINAL_SCHEMA, snapshot):
        raise ValueError("native Faith final numeric schema is malformed")
    _native_frame(value, snapshot=snapshot)
    if (any(not _reference(value[key]) for key in ("current_rite_id", "faith_id", "main_rite_id"))
            or type(value["scale"]) is not int or value["scale"] != 100000
            or value["unit"] != "fervor_points" or value["source"] != "faith_main_rite"
            or not isinstance(value["native_getter_rva"], str)
            or not isinstance(value["native_define_rva"], str)):
        raise ValueError("native Faith final numeric provenance is malformed")
    state = value["value_state"]
    raw_keys = ("main_rite_adjustment_raw", "native_define_raw", "final_heresy_threshold_raw")
    if value["available"] and state == "value":
        if any(not _signed_raw(value[key]) for key in raw_keys) or not _number(value["final_heresy_threshold"]):
            raise ValueError("native Faith final threshold values are malformed")
    elif ((value["available"] and state in {"legal_absent_faith", "legal_absent_main_rite"})
          or (not value["available"] and state == "unavailable")):
        if any(value[key] is not None for key in (*raw_keys, "final_heresy_threshold")):
            raise ValueError("native Faith final threshold lost its absent/unavailable values")
    else:
        raise ValueError("native Faith final numeric value state is malformed")
    # Native final results are preserved. No cache adjustment, define or sum is
    # evaluated here as a substitute for the native getter.
    return deepcopy(value)


def query_player_religion_numeric_special_parameters_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-numeric-special-parameters-v1",
        )
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native numeric observation envelope differs from the queried build/frame")
        primary = normalize_player_religion_numeric_special_parameters_v1(
            result.get("player_religion_numeric_special_parameters"), snapshot=before,
        )
        final = normalize_faith_numeric_final_v1(result.get("faith_numeric_final"), snapshot=before)
        if result.get("status") != ("observed" if primary["available"] else "unavailable"):
            raise ValueError("native numeric observation envelope lost its primary source status")
        if primary["available"] and final["available"]:
            if (primary["capture_epoch"] != final["capture_epoch"]
                    or primary["faith_id"] != final["faith_id"]
                    or (primary["current_rite"] is not None
                        and primary["current_rite"]["rite_id"] != final["current_rite_id"])
                    or (primary["faith_main_rite"] is not None
                        and primary["faith_main_rite"]["rite_id"] != final["main_rite_id"])):
                raise ValueError("native numeric cache and final getter observed different source scopes")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **primary, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "faith_numeric_final": final,
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
