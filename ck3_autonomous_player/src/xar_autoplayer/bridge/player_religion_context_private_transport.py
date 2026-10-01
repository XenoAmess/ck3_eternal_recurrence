"""Read the current player's native Rite/Faith/Religion context; no action."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import (
    private_native_build_identity, private_native_provenance,
)
from .version_identity import (
    CK3_12002, require_exact_native_backend, require_exact_native_build,
)


STEP = "query-player-religion-context-v1"
DOMAIN_KEY = "player_religion_context_v1"
SCHEMA = "ck3_12002_religion_context_v1"
PERMISSION = "allow_private_player_religion_context_query"
_CONTEXT_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "rite_id", "faith_id", "religion_id", "faith_main_rite_id",
    "faith_key", "religion_key", "faith_fervor_raw",
    "spiritual_fulfillment_raw", "raw_scale",
}
_REFERENCE_KEYS = ("rite_id", "faith_id", "religion_id", "faith_main_rite_id")
_TAG_KEYS = ("faith_key", "religion_key")
_RESOURCE_KEYS = ("faith_fervor_raw", "spiritual_fulfillment_raw")


def normalize_player_religion_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve native nulls, full references, strings and signed raw resources."""
    if not isinstance(value, dict) or set(value) != _CONTEXT_KEYS or value["schema"] != SCHEMA:
        raise ValueError("native player religion context schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build != CK3_12002 or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion context belongs to another build")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or type(value["played_character_id"]) is not int
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000):
        raise ValueError("native player religion context scalar fields are malformed")
    for key in _REFERENCE_KEYS:
        reference = value[key]
        if reference is not None and (type(reference) is not int or not 0 <= reference <= 0xFFFFFFFF):
            raise ValueError(f"native player religion context full reference is malformed: {key}")
    for key in _TAG_KEYS:
        if value[key] is not None and not isinstance(value[key], str):
            raise ValueError(f"native player religion context tag is malformed: {key}")
    for key in _RESOURCE_KEYS:
        resource = value[key]
        if resource is not None and (type(resource) is not int or not -(1 << 63) <= resource < (1 << 63)):
            raise ValueError(f"native player religion context signed resource is malformed: {key}")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None
                or value["spiritual_fulfillment_raw"] is None):
            raise ValueError("native player religion context differs from its queried player frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player religion context lost its unavailable reason")
    # The provider's capture epoch is an owner-pump identity, not the bridge
    # snapshot revision. Neither it nor zero/native-null values are rewritten.
    return dict(value)


def query_player_religion_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-context-v1",
        )
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player religion context envelope differs from the queried build/frame")
        value = normalize_player_religion_context_v1(
            result.get("player_religion_context"), snapshot=before,
        )
        expected_status = "observed" if value["available"] else "unavailable"
        if result.get("status") != expected_status:
            raise ValueError("native player religion context envelope lost its source status")
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
