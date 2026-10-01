"""Read the player's four native hostility directions towards one full Rite ID."""

from __future__ import annotations

from collections.abc import Mapping

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


STEP = "query-player-religion-hostility-v1"
DOMAIN_KEY = "player_religion_hostility_v1"
SCHEMA = "ck3_12002_religion_hostility_v1"
PERMISSION = "allow_private_player_religion_hostility_query"
_REFERENCE_KEYS = (
    "actor_rite_id", "target_rite_id", "actor_faith_id", "target_faith_id",
    "actor_religion_id", "target_religion_id", "actor_main_rite_id", "target_main_rite_id",
)
_DIRECTION_KEYS = (
    "actor_rite_towards_target", "target_rite_towards_actor",
    "actor_faith_towards_target", "target_faith_towards_actor",
)
_RELATION_KEYS = ("same_faith", "same_religion")
_LEVEL_KEYS = ("righteous", "astray", "hostile", "evil")
_HOSTILITY_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id",
    *_REFERENCE_KEYS, *_DIRECTION_KEYS, *(key + "_key" for key in _DIRECTION_KEYS),
    *_RELATION_KEYS,
}


def normalize_player_religion_hostility_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep native directionality, generation bits, legal zero and typed nulls."""
    if not isinstance(value, dict) or set(value) != _HOSTILITY_KEYS or value["schema"] != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native player religion hostility schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion hostility belongs to another build")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or type(value["played_character_id"]) is not int):
        raise ValueError("native player religion hostility scalar fields are malformed")
    for key in _REFERENCE_KEYS:
        reference = value[key]
        if reference is not None and (type(reference) is not int or not 0 <= reference <= 0xFFFFFFFF):
            raise ValueError(f"native player religion hostility full reference is malformed: {key}")
    for key in _DIRECTION_KEYS:
        level, level_key = value[key], value[key + "_key"]
        if level is None:
            if level_key is not None:
                raise ValueError("native player religion hostility null level lost its native key")
        elif (type(level) is not int or not 0 <= level <= 3 or level_key != _LEVEL_KEYS[level]):
            raise ValueError("native player religion hostility direction level/key is malformed")
    for key in _RELATION_KEYS:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError("native player religion hostility relation is malformed")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None
                or any(value[key] is None for key in (*_REFERENCE_KEYS, *_DIRECTION_KEYS, *_RELATION_KEYS))):
            raise ValueError("native player religion hostility differs from its queried player frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player religion hostility lost its unavailable reason")
    # capture_epoch is the native owner-pump identity, not snapshot_revision.
    # Same Faith and same Religion are observed booleans, never inferred here.
    return dict(value)


def query_player_religion_hostility_private_v1(
    driver: object, *, expected_revision: int, target_rite_id: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if type(target_rite_id) is not int or not 0 <= target_rite_id <= 0xFFFFFFFF:
        raise ValueError("target_rite_id must be a full uint32 reference (zero is valid)")
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, request_fields={"target_rite_id": target_rite_id},
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-hostility-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player religion hostility envelope differs from the queried build/frame")
        value = normalize_player_religion_hostility_v1(
            result.get("player_religion_hostility"), snapshot=before,
        )
        if (result.get("status") != ("observed" if value["available"] else "unavailable")
                or (value["available"] and value["target_rite_id"] != target_rite_id)):
            raise ValueError("native player religion hostility envelope lost its source status/target")
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
