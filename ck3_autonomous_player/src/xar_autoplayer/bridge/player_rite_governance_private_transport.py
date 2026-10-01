"""Read native player Rite governance while retaining each component's status."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

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


STEP = "query-player-rite-governance-v1"
DOMAIN_KEY = "player_rite_governance_v1"
SCHEMA = "ck3_12002_player_rite_governance_v1"
PERMISSION = "allow_private_player_rite_governance_query"
_COMMON_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
}
_TOP_KEYS = {
    "schema", "available", "frame_available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id", "observed_components",
    "all_components_available", "state_rite", "heads", "organization",
}
_STATE_REFERENCES = (
    "actor_rite_id", "actor_faith_id", "actor_faith_main_rite_id",
    "top_liege_character_id",
)
_HEAD_REFERENCES = (
    "actor_rite_id", "faith_id", "faith_main_rite_id",
    "actor_rite_head_character_id", "faith_main_rite_head_character_id",
    "faith_religious_head_title_id", "faith_religious_head_holder_character_id",
)
_TITLE_KEYS = {"title_id", "state_rite_id", "state_faith_id"}


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native Rite governance integer is malformed: {field}")


def _nullable_integer(value: object, low: int, high: int, field: str) -> None:
    if value is not None:
        _integer(value, low, high, field)


def _component(
    value: object, *, schema: str, fields: set[str], snapshot: Mapping[str, object],
    epoch: int, unsigned_actor: bool = False,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _COMMON_KEYS | fields or value["schema"] != schema:
        raise ValueError(f"native Rite governance component schema is malformed: {schema}")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build != CK3_12002 or build != private_native_build_identity(snapshot):
        raise ValueError("native Rite governance component belongs to another build")
    if type(value["available"]) is not bool:
        raise ValueError("native Rite governance component availability is malformed")
    _integer(value["capture_epoch"], 0, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(value["played_character_id"], 0 if unsigned_actor else -(1 << 31),
             0xFFFFFFFF if unsigned_actor else (1 << 31) - 1, "played_character_id")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["capture_epoch"] != epoch
                or value["unavailable_reason"] is not None):
            raise ValueError("native Rite governance component differs from the queried frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native Rite governance component lost its unavailable reason")
    # Failed components retain their own native frame defaults and any partial
    # fields; another component's success does not rewrite them.
    return value


def normalize_player_rite_governance_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve native full references, legal absence, zero counts and partial reads."""
    if not isinstance(value, dict) or set(value) != _TOP_KEYS or value["schema"] != SCHEMA:
        raise ValueError("native player Rite governance schema is malformed")
    if (type(value["available"]) is not bool
            or type(value["frame_available"]) is not bool
            or type(value["all_components_available"]) is not bool
            or not isinstance(value["unavailable_reason"], str)
            or not value["unavailable_reason"]):
        raise ValueError("native player Rite governance status is malformed")
    _integer(value["capture_epoch"], 0, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(value["played_character_id"], -(1 << 31), (1 << 31) - 1, "played_character_id")
    _integer(value["observed_components"], 0, 3, "observed_components")
    if value["frame_available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["capture_epoch"] == 0):
            raise ValueError("native player Rite governance differs from its queried player frame")
    state = _component(
        value["state_rite"], schema="ck3_12002_religion_state_rite_v1",
        fields=set(_STATE_REFERENCES) | {"player_primary_title", "realm_primary_title"},
        snapshot=snapshot, epoch=value["capture_epoch"], unsigned_actor=True,
    )
    for key in _STATE_REFERENCES:
        _nullable_integer(state[key], 0, 0xFFFFFFFF, key)
    for key in ("player_primary_title", "realm_primary_title"):
        title = state[key]
        if not isinstance(title, dict) or set(title) != _TITLE_KEYS:
            raise ValueError(f"native player Rite governance title is malformed: {key}")
        for field in _TITLE_KEYS:
            _nullable_integer(title[field], 0, 0xFFFFFFFF, field)
    heads = _component(
        value["heads"], schema="ck3_12002_religion_rite_heads_v1",
        fields=set(_HEAD_REFERENCES), snapshot=snapshot, epoch=value["capture_epoch"],
    )
    for key in _HEAD_REFERENCES:
        _nullable_integer(heads[key], 0, 0xFFFFFFFF, key)
    organization = _component(
        value["organization"], schema="ck3_12002_rite_organization_counts_v1",
        fields={"scope", "values", "rite_id", "county_count", "character_follower_count"},
        snapshot=snapshot, epoch=value["capture_epoch"],
    )
    if (organization["scope"] != "current_player_rite"
            or organization["values"] != "native_cached_counts"):
        raise ValueError("native Rite organization count scope is malformed")
    _nullable_integer(organization["rite_id"], 0, 0xFFFFFFFF, "rite_id")
    for key in ("county_count", "character_follower_count"):
        _nullable_integer(organization[key], -(1 << 31), (1 << 31) - 1, key)
    observed = sum(component["available"] for component in (state, heads, organization))
    if (value["observed_components"] != observed
            or value["available"] != bool(observed)
            or value["all_components_available"] != (observed == 3)
            or (observed > 0 and not value["frame_available"])):
        raise ValueError("native Rite governance aggregate lost its component status")
    # capture_epoch is the native owner-pump identity, not snapshot_revision.
    return deepcopy(value)


def query_player_rite_governance_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-rite-governance-v1",
        )
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player Rite governance envelope differs from the queried build/frame")
        value = normalize_player_rite_governance_v1(
            result.get("player_rite_governance"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native player Rite governance envelope lost its source status")
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
