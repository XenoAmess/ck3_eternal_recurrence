"""Read current/main Rite and personal Tenets with native effective states."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import (
    private_native_schema,
    private_native_build_identity, private_native_provenance,
)
from .version_identity import (
    CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build,
)
from .target_rite_tenet_comparison_12003 import (
    normalize_target_rite_tenet_comparison_12003,
)


STEP = "query-player-religion-tenets-v1"
DOMAIN_KEY = "player_religion_tenets_v1"
SCHEMA = "ck3_12002_tenet_rows_v1"
PERMISSION = "allow_private_player_religion_tenets_query"
_TENET_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "faith_id", "current_rite", "faith_main_rite", "personal_tenets_complete",
    "personal_tenets", "effective_tenet_states", "status_values",
}
_STATUS_VALUES = {"unknown": 0, "known": 1, "prohibited": 2, "permitted": 3, "core": 4}


def _full_reference(value: object) -> bool:
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def _tenet_rows(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("native player religion Tenet rows are malformed")
    for row in value:
        if (not isinstance(row, Mapping) or set(row) != {"key", "current_rite_status"}
                or not isinstance(row.get("key"), str)):
            raise ValueError("native player religion Tenet entry is malformed")
        status = row["current_rite_status"]
        if status is not None and (type(status) is not int or not 0 <= status <= 4):
            raise ValueError("native player religion Tenet state is malformed")


def _rite_tenets(value: object) -> None:
    if value is None:
        return
    if (not isinstance(value, Mapping) or set(value) != {"rite_id", "core_tenets"}
            or not _full_reference(value.get("rite_id"))):
        raise ValueError("native player religion Tenet Rite scope is malformed")
    _tenet_rows(value["core_tenets"])


def normalize_player_religion_tenets_v1(
    value: object, *, snapshot: Mapping[str, object],
    target_rite_id: int | None = None, tenet_key: str | None = None,
) -> dict[str, object]:
    """Preserve source collections, zero states, absent Rite and native failure."""
    expected_keys = _TENET_KEYS | ({"target_rite_tenet_comparison"} if target_rite_id is not None else set())
    if not isinstance(value, dict) or set(value) != expected_keys or value.get("schema") != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native player religion Tenets schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion Tenets belongs to another build")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or not _full_reference(value["played_character_id"])
            or (value["faith_id"] is not None and not _full_reference(value["faith_id"]))
            or type(value["personal_tenets_complete"]) is not bool
            or value["personal_tenets_complete"] != value["available"]):
        raise ValueError("native player religion Tenets scalar fields are malformed")
    states = value["status_values"]
    if (not isinstance(states, Mapping) or states != _STATUS_VALUES
            or any(type(state) is not int for state in states.values())):
        raise ValueError("native player religion Tenets lost its native status values")
    _rite_tenets(value["current_rite"])
    _rite_tenets(value["faith_main_rite"])
    _tenet_rows(value["personal_tenets"])
    _tenet_rows(value["effective_tenet_states"])
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None):
            raise ValueError("native player religion Tenets differs from its queried player frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player religion Tenets lost its unavailable reason")
    # Owner-pump epoch, legal zero references/states and source nulls stay native.
    result = deepcopy(value)
    if target_rite_id is not None:
        if tenet_key is None:
            raise ValueError("native player religion comparison request lost its Tenet key")
        result["target_rite_tenet_comparison"] = normalize_target_rite_tenet_comparison_12003(
            value["target_rite_tenet_comparison"], snapshot=snapshot, tenet_rows=value,
            target_rite_id=target_rite_id, tenet_key=tenet_key,
        )
    return result


def _comparison_request_fields(
    target_rite_id: int | None, tenet_key: str | None,
) -> dict[str, object]:
    if (target_rite_id is None) != (tenet_key is None):
        raise ValueError("target_rite_id and tenet_key must be provided together")
    if target_rite_id is None:
        return {}
    if (not _full_reference(target_rite_id) or not isinstance(tenet_key, str)
            or not tenet_key or len(tenet_key.encode("utf-8")) > 128):
        raise ValueError("target Rite and named Tenet comparison request is malformed")
    return {"target_rite_id": target_rite_id, "tenet_key": tenet_key}


def query_player_religion_tenets_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
    target_rite_id: int | None = None, tenet_key: str | None = None,
) -> dict[str, object]:
    try:
        request_fields = _comparison_request_fields(target_rite_id, tenet_key)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
        request_fields=request_fields,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-tenets-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player religion Tenets envelope differs from the queried build/frame")
        value = normalize_player_religion_tenets_v1(
            result.get("player_religion_tenets"), snapshot=before,
            target_rite_id=target_rite_id, tenet_key=tenet_key,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native player religion Tenets envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
