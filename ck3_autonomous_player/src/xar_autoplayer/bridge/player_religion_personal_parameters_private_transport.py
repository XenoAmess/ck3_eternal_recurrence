"""Read the played character's complete personal Tenet boolean parameters."""

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


STEP = "query-player-religion-personal-parameters-v1"
DOMAIN_KEY = "player_religion_personal_parameters_v1"
SCHEMA = "ck3_12002_character_personal_parameters_v1"
PERMISSION = "allow_private_player_religion_personal_parameters_query"
_PARAMETER_KEYS = {
    "schema", "game_version", "executable_sha256", "source", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "has_character_extension", "supported_keys_complete", "personal_parameters_complete",
    "personal_tenet_keys", "parameters",
}


def normalize_player_religion_personal_parameters_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve true, known missing false, legal absence and native read failures."""
    if (not isinstance(value, dict) or set(value) != _PARAMETER_KEYS
            or value.get("schema") != private_native_schema(SCHEMA, snapshot)
            or value.get("source") != "character_personal_tenets"):
        raise ValueError("native player religion personal parameters schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion personal parameters belongs to another build")
    if (any(type(value[key]) is not bool for key in (
                "available", "has_character_extension", "supported_keys_complete",
                "personal_parameters_complete"))
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or type(value["played_character_id"]) is not int
            or not 0 <= value["played_character_id"] <= 0xFFFFFFFF
            or value["supported_keys_complete"] != value["available"]
            or value["personal_parameters_complete"] != value["available"]):
        raise ValueError("native player religion personal parameters scalars are malformed")
    tenets = value["personal_tenet_keys"]
    parameters = value["parameters"]
    if (not isinstance(tenets, list)
            or any(not isinstance(key, str) or not key for key in tenets)
            or not isinstance(parameters, list)):
        raise ValueError("native player religion personal parameter collections are malformed")
    for row in parameters:
        if (not isinstance(row, Mapping) or set(row) != {"key", "value"}
                or not isinstance(row.get("key"), str) or not row["key"]
                or type(row.get("value")) is not bool):
            raise ValueError("native player religion personal parameter row is malformed")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None):
            raise ValueError("native player religion personal parameters differs from its queried player frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player religion personal parameters lost its unavailable reason")
    # The producer's supported registry is authoritative; do not filter false,
    # infer unlisted keys, or merge these rows with Rite boolean parameters.
    return deepcopy(value)


def query_player_religion_personal_parameters_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-personal-parameters-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player religion personal parameters envelope differs from the queried build/frame")
        value = normalize_player_religion_personal_parameters_v1(
            result.get("player_religion_personal_parameters"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native player religion personal parameters envelope lost its source status")
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
