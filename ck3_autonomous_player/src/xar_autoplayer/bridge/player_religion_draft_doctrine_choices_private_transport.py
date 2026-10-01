"""Read final Doctrine choices from all actual current draft slot sources."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-draft-doctrine-choices-v1"
DOMAIN_KEY = "player_religion_draft_doctrine_choices_v1"
SCHEMA = "ck3_12002_current_draft_full_doctrine_choices_v1"
PERMISSION = "allow_private_player_religion_draft_doctrine_choices_query"
_KEYS = {
    "schema", "game_version", "executable_sha256", "scope", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id", "source_rite_id", "draft_observed",
    "doctrine_gates_complete", "slots",
}
_SLOT_KEYS = {"slot_index", "group_key", "selected_doctrine_key", "sources"}
_ROW_KEYS = {
    "source_index", "doctrine_key", "currently_selected", "duplicate_excluded", "passed_shown",
    "native_can_pick", "native_knows_doctrine", "native_has_prophet", "final_selectable",
}
_OPTIONAL_GATES = ("passed_shown", "native_can_pick", "native_knows_doctrine", "native_has_prophet")


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native draft Doctrine integer is malformed: {field}")


def normalize_player_religion_draft_doctrine_choices_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Copy actual final gates and preserve short-circuit nulls without recomputing."""
    if not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != SCHEMA:
        raise ValueError("native player draft Doctrine choices schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build != CK3_12002 or build != private_native_build_identity(snapshot):
        raise ValueError("native player draft Doctrine choices belongs to another build")
    if value["scope"] != "actual_current_draft_selected_slot_group_sources":
        raise ValueError("native draft Doctrine choices scope is malformed")
    for key in ("available", "draft_observed", "doctrine_gates_complete"):
        if type(value[key]) is not bool:
            raise ValueError(f"native draft Doctrine status is malformed: {key}")
    _integer(value["capture_epoch"], 1, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(value["played_character_id"], 0, 0xFFFFFFFF, "played_character_id")
    if value["source_rite_id"] is not None:
        _integer(value["source_rite_id"], 0, 0xFFFFFFFF, "source_rite_id")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or actor.get("character_id") != value["played_character_id"]
                or snapshot.get("date_raw") != value["date_raw"]
                or value["unavailable_reason"] is not None):
            raise ValueError("native draft Doctrine choices differs from its queried frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native draft Doctrine choices lost its reason")
    if value["doctrine_gates_complete"] and not (value["available"] and value["draft_observed"]):
        raise ValueError("native final Doctrine gates have no observed current draft")
    if not isinstance(value["slots"], list):
        raise ValueError("native final Doctrine choices lost its actual slots")
    for slot in value["slots"]:
        if not isinstance(slot, dict) or set(slot) != _SLOT_KEYS:
            raise ValueError("native final Doctrine slot schema is malformed")
        _integer(slot["slot_index"], 0, 0xFFFFFFFF, "slot_index")
        if (not isinstance(slot["group_key"], str)
                or not isinstance(slot["selected_doctrine_key"], str)
                or not isinstance(slot["sources"], list)):
            raise ValueError("native final Doctrine slot source identity is malformed")
        for row in slot["sources"]:
            if not isinstance(row, dict) or set(row) != _ROW_KEYS or not isinstance(row["doctrine_key"], str):
                raise ValueError("native final Doctrine source row is malformed")
            _integer(row["source_index"], 0, 0xFFFFFFFF, "source_index")
            for key in ("currently_selected", "duplicate_excluded", "final_selectable"):
                if type(row[key]) is not bool:
                    raise ValueError(f"native final Doctrine row bool is malformed: {key}")
            for key in _OPTIONAL_GATES:
                if row[key] is not None and type(row[key]) is not bool:
                    raise ValueError(f"native short-circuit Doctrine gate is malformed: {key}")
    # Optional gate nulls mean native short-circuit evaluation did not reach
    # that branch. They are neither false nor a missing final-selectable value.
    return deepcopy(value)


def query_player_religion_draft_doctrine_choices_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-draft-doctrine-choices-v1",
        )
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native final Doctrine envelope differs from the queried build/frame")
        value = normalize_player_religion_draft_doctrine_choices_v1(
            result.get("player_religion_draft_doctrine_choices"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native final Doctrine envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
