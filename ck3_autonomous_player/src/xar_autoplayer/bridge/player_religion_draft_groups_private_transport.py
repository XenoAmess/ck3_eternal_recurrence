"""Read actual draft group sources and the current materialized Tenet gates."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-draft-groups-v1"
DOMAIN_KEY = "player_religion_draft_groups_v1"
SCHEMA = "ck3_12002_current_draft_group_model_v1"
PERMISSION = "allow_private_player_religion_draft_groups_query"
_KEYS = {
    "schema", "executable_sha256", "available", "unavailable_reason", "capture_epoch",
    "date_raw", "played_character_id", "founder_character_id", "source_rite_id",
    "draft_observed", "category_materialized", "current_category_slot", "current_group_key",
    "current_selected_definition_key", "all_group_materialized_choices_complete",
    "group_source_scope", "current_tenet_scope", "current_tenet_gate_complete",
    "current_doctrine_cache_count", "current_tenet_source_count", "current_tenet_group_count",
    "selected_slots", "current_tenet_choices",
}
_SLOT_KEYS = {"selected_array_index", "selected_definition_key", "group_key", "group_source_definition_keys"}
_TENET_KEYS = {"tenet_key", "popup_group_index", "popup_item_index", "native_pick_source", "final_can_pick"}


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native draft group integer is malformed: {field}")


def normalize_player_religion_draft_groups_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep definition sources distinct from actual current popup final choices."""
    if not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native player religion draft groups schema is malformed")
    build = require_exact_native_build(private_native_build_identity(snapshot).game_version, value["executable_sha256"])
    if build != private_native_build_identity(snapshot):
        raise ValueError("native player religion draft groups belongs to another build")
    for key in ("available", "draft_observed", "category_materialized", "current_tenet_gate_complete"):
        if type(value[key]) is not bool:
            raise ValueError(f"native draft group availability is malformed: {key}")
    if (value["all_group_materialized_choices_complete"] is not False
            or value["group_source_scope"] != "actual_selected_slot_group_definition_sources"
            or value["current_tenet_scope"] != "current_materialized_category_status_groups"):
        raise ValueError("native draft group source/current-popup scope is malformed")
    _integer(value["capture_epoch"], 1, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    for key in ("played_character_id", "founder_character_id"):
        _integer(value[key], 0, 0xFFFFFFFF, key)
    if value["source_rite_id"] is not None:
        _integer(value["source_rite_id"], 0, 0xFFFFFFFF, "source_rite_id")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or actor.get("character_id") != value["played_character_id"]
                or snapshot.get("date_raw") != value["date_raw"]
                or value["unavailable_reason"] is not None):
            raise ValueError("native draft group model differs from its queried frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native draft group model lost its reason")
    if value["draft_observed"] and (not value["available"]
            or value["founder_character_id"] != value["played_character_id"]):
        raise ValueError("native draft group model lost its actual founder")
    _integer(value["current_category_slot"], -1, (1 << 31) - 1, "current_category_slot")
    for key in ("current_group_key", "current_selected_definition_key"):
        if value[key] is not None and not isinstance(value[key], str):
            raise ValueError(f"native current draft group key is malformed: {key}")
    for key in ("current_doctrine_cache_count", "current_tenet_source_count", "current_tenet_group_count"):
        _integer(value[key], 0, 0xFFFFFFFF, key)
    slots = value["selected_slots"]
    choices = value["current_tenet_choices"]
    if not isinstance(slots, list) or not isinstance(choices, list):
        raise ValueError("native draft group model lost its source/current-popup lists")
    for row in slots:
        if not isinstance(row, dict) or set(row) != _SLOT_KEYS:
            raise ValueError("native draft selected slot schema is malformed")
        _integer(row["selected_array_index"], 0, 0xFFFFFFFF, "selected_array_index")
        if (not isinstance(row["selected_definition_key"], str)
                or not isinstance(row["group_key"], str)
                or not isinstance(row["group_source_definition_keys"], list)
                or any(not isinstance(key, str) for key in row["group_source_definition_keys"])):
            raise ValueError("native draft selected slot definition sources are malformed")
    for row in choices:
        if not isinstance(row, dict) or set(row) != _TENET_KEYS or not isinstance(row["tenet_key"], str):
            raise ValueError("native current materialized Tenet schema is malformed")
        for key in ("popup_group_index", "popup_item_index"):
            _integer(row[key], 0, 0xFFFFFFFF, key)
        _integer(row["native_pick_source"], 0, 255, "native_pick_source")
        if type(row["final_can_pick"]) is not bool:
            raise ValueError("native current materialized Tenet lost its final gate")
    if value["category_materialized"]:
        if (not value["draft_observed"] or value["current_category_slot"] < 0
                or value["current_group_key"] is None
                or value["current_selected_definition_key"] is None):
            raise ValueError("native current materialized category lost its actual identity")
    elif value["current_tenet_gate_complete"] or choices:
        raise ValueError("native Tenet final choices have no current materialized category")
    # Unavailable or absent models retain their native empty lists and scalar
    # defaults. These arrays are never promoted to observed all-group choices.
    return deepcopy(value)


def query_player_religion_draft_groups_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-draft-groups-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native draft group envelope differs from the queried build/frame")
        value = normalize_player_religion_draft_groups_v1(
            result.get("player_religion_draft_groups"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native draft group envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
