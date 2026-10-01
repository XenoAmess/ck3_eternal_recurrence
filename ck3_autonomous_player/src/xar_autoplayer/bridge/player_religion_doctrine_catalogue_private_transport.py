"""Read all loaded native Doctrine definitions without selecting a doctrine."""

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
from .version_identity import CK3_12002, CK3_12003, require_exact_native_backend


STEP = "query-player-religion-doctrine-catalogue-v1"
DOMAIN_KEY = "player_religion_doctrine_catalogue_v1"
SCHEMA = "ck3_12002_loaded_doctrine_catalogue_v1"
PERMISSION = "allow_private_player_religion_doctrine_catalogue_query"
_CATALOGUE_KEYS = {
    "schema", "available", "unavailable_reason", "catalogue_complete", "source",
    "capture_epoch", "date_raw", "played_character_id", "rows",
}
_SOURCE = "loaded_doctrine_registry"


def normalize_player_religion_doctrine_catalogue_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep a complete loaded registry separate from a typed failed read."""
    if (not isinstance(value, dict) or set(value) != _CATALOGUE_KEYS
            or value.get("schema") != private_native_schema(SCHEMA, snapshot)):
        raise ValueError("native player doctrine catalogue schema is malformed")
    # The actual catalogue DTO has no build fields; its command-result envelope
    # supplies the exact build, checked by the query before normalization.
    if private_native_build_identity(snapshot) not in (CK3_12002, CK3_12003):
        raise ValueError("native player doctrine catalogue belongs to another build")
    if (type(value["available"]) is not bool
            or type(value["catalogue_complete"]) is not bool
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int or type(value["played_character_id"]) is not int
            or value["source"] != _SOURCE or not isinstance(value["rows"], list)):
        raise ValueError("native player doctrine catalogue scalar fields are malformed")
    reason = value["unavailable_reason"]
    if ((value["available"] and (reason is not None or value["catalogue_complete"] is not True))
            or (not value["available"] and (not isinstance(reason, str) or not reason
                                          or value["catalogue_complete"] is not False))):
        raise ValueError("native player doctrine catalogue lost its availability/completeness")
    for row in value["rows"]:
        if (not isinstance(row, Mapping) or set(row) != {"doctrine_key", "group_key", "source"}
                or not isinstance(row.get("doctrine_key"), str)
                or not isinstance(row.get("group_key"), str) or row.get("source") != _SOURCE):
            raise ValueError("native player doctrine catalogue row is malformed")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")):
            raise ValueError("native player doctrine catalogue differs from its queried player frame")
    # catalogue_complete means all loaded definitions, never final legal choices.
    # capture_epoch remains the actual owner pump epoch, not snapshot_revision.
    return deepcopy(value)


def query_player_religion_doctrine_catalogue_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-doctrine-catalogue-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native doctrine catalogue envelope differs from the queried build/frame")
        value = normalize_player_religion_doctrine_catalogue_v1(
            result.get("player_religion_doctrine_catalogue"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native doctrine catalogue envelope lost its source status")
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
