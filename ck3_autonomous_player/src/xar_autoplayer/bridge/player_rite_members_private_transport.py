"""Read actual current-player Faith characters, Rite characters and Rite counties."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-rite-members-v1"
DOMAIN_KEY = "player_rite_members_v1"
SCHEMA = "ck3_12002_rite_organization_members_v1"
PERMISSION = "allow_private_player_rite_members_query"
_KEYS = {
    "schema", "game_version", "executable_sha256", "scope", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "rite_id", "faith_id", "religion_id", "faith_character_ids",
    "rite_character_ids", "county_title_ids",
}
_LIST_KEYS = ("faith_character_ids", "rite_character_ids", "county_title_ids")


def _reference(value: object, key: str) -> None:
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"native Rite member full reference is malformed: {key}")


def normalize_player_rite_members_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve full native lists, their distinct scope and known-empty/unavailable."""
    if (not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != private_native_schema(SCHEMA, snapshot)
            or value["scope"] != "current_player_rite_and_its_faith"):
        raise ValueError("native player Rite members schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native player Rite members belong to another build")
    if (type(value["available"]) is not bool or type(value["capture_epoch"]) is not int
            or not 0 <= value["capture_epoch"] < (1 << 64)):
        raise ValueError("native player Rite members availability/epoch are malformed")
    for key in ("date_raw", "played_character_id"):
        if type(value[key]) is not int or not -(1 << 31) <= value[key] < (1 << 31):
            raise ValueError(f"native player Rite members signed field is malformed: {key}")
    for key in ("rite_id", "faith_id", "religion_id"):
        if value[key] is not None:
            _reference(value[key], key)
    for key in _LIST_KEYS:
        if not isinstance(value[key], list):
            raise ValueError(f"native Rite member list is malformed: {key}")
        for member in value[key]:
            _reference(member, key)
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None or value["capture_epoch"] == 0):
            raise ValueError("native player Rite members differ from their queried player frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player Rite members lost their unavailable reason")
    # Lists retain their source order and full generation bits. Failed empty
    # output is not turned into known zero membership or cache count equality.
    return deepcopy(value)


def query_player_rite_members_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-rite-members-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player Rite members envelope differs from the queried build/frame")
        value = normalize_player_rite_members_v1(result.get("player_rite_members"), snapshot=before)
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native player Rite members envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
