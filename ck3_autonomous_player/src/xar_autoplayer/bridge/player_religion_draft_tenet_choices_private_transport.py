"""Read final Tenet candidates from the actual current draft's native sources."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-draft-tenet-choices-v1"
DOMAIN_KEY = "player_religion_draft_tenet_choices_v1"
SCHEMA = "ck3_12002_current_draft_tenet_sources_v1"
PERMISSION = "allow_private_player_religion_draft_tenet_choices_query"
_KEYS = {
    "schema", "game_version", "executable_sha256", "scope", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id", "source_rite_id", "source_faith_id",
    "source_main_rite_id", "draft_observed", "tenet_gates_complete",
    "raw_category_exemption_present", "raw_category_exemption_key", "slots_share_source_predicate",
    "slots", "sources",
}
_SLOT_KEYS = {"slot_index", "selected_tenet_key"}
_ROW_KEYS = {
    "source_index", "tenet_key", "already_selected", "duplicate_excluded", "source_can_materialize",
    "filtered_out", "native_status_raw", "actor_faith_status_raw", "native_extra_knowledge",
    "native_has_prophet", "knowledge", "passed_shown", "passed_selectable_trigger",
    "native_can_pick", "final_selectable",
}
_ROW_BOOLS = _ROW_KEYS - {"source_index", "tenet_key", "native_status_raw", "actor_faith_status_raw"}


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native draft Tenet integer is malformed: {field}")


def normalize_player_religion_draft_tenet_choices_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve raw status, actual source filtering and the native final gate."""
    if not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native player draft Tenet choices schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(snapshot):
        raise ValueError("native player draft Tenet choices belongs to another build")
    if (value["scope"] != "actual_current_draft_all_tenet_sources_shared_slot_predicate"
            or value["slots_share_source_predicate"] is not True):
        raise ValueError("native draft Tenet source scope is malformed")
    for key in ("available", "draft_observed", "tenet_gates_complete", "raw_category_exemption_present"):
        if type(value[key]) is not bool:
            raise ValueError(f"native draft Tenet status is malformed: {key}")
    _integer(value["capture_epoch"], 1, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(value["played_character_id"], 0, 0xFFFFFFFF, "played_character_id")
    for key in ("source_rite_id", "source_faith_id", "source_main_rite_id"):
        if value[key] is not None:
            _integer(value[key], 0, 0xFFFFFFFF, key)
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or actor.get("character_id") != value["played_character_id"]
                or snapshot.get("date_raw") != value["date_raw"]
                or value["unavailable_reason"] is not None):
            raise ValueError("native draft Tenet choices differs from its queried frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native draft Tenet choices lost its reason")
    if value["tenet_gates_complete"] and not (value["available"] and value["draft_observed"]):
        raise ValueError("native final Tenet gates have no observed current draft")
    exemption = value["raw_category_exemption_key"]
    if ((exemption is not None and not isinstance(exemption, str))
            or value["raw_category_exemption_present"] != (exemption is not None)):
        raise ValueError("native current category exemption is malformed")
    if not isinstance(value["slots"], list) or not isinstance(value["sources"], list):
        raise ValueError("native final Tenet choices lost its actual slots/sources")
    for slot in value["slots"]:
        if (not isinstance(slot, dict) or set(slot) != _SLOT_KEYS
                or (slot["selected_tenet_key"] is not None
                    and not isinstance(slot["selected_tenet_key"], str))):
            raise ValueError("native final Tenet slot schema is malformed")
        _integer(slot["slot_index"], 0, 0xFFFFFFFF, "slot_index")
    for row in value["sources"]:
        if (not isinstance(row, dict) or set(row) != _ROW_KEYS
                or not isinstance(row["tenet_key"], str)):
            raise ValueError("native final Tenet source schema is malformed")
        _integer(row["source_index"], 0, 0xFFFFFFFF, "source_index")
        for key in ("native_status_raw", "actor_faith_status_raw"):
            _integer(row[key], 0, 255, key)
        for key in _ROW_BOOLS:
            if type(row[key]) is not bool:
                raise ValueError(f"native final Tenet gate is malformed: {key}")
    # The owning-thread provider evaluates the actual native filter/status/trigger
    # inputs. Python keeps its final result; it does not construct category items.
    return deepcopy(value)


def query_player_religion_draft_tenet_choices_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-draft-tenet-choices-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native final Tenet envelope differs from the queried build/frame")
        value = normalize_player_religion_draft_tenet_choices_v1(
            result.get("player_religion_draft_tenet_choices"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native final Tenet envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
