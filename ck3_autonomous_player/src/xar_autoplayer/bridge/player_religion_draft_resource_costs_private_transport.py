"""Read native draft base resource fees, without predicting an executed net cost."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12002, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-draft-resource-costs-v1"
DOMAIN_KEY = "player_religion_draft_resource_costs_v1"
SCHEMA = "ck3_12002_player_religion_draft_resource_costs_query_v1"
PERMISSION = "allow_private_player_religion_draft_resource_costs_query"
_KEYS = {
    "schema", "available", "window_present", "draft_observed", "failure", "capture_epoch",
    "date_raw", "played_character_id", "current_draft_window", "base_resource_cost_quote",
}
_WINDOW_KEYS = {
    "schema", "available", "unavailable_reason", "present", "visible", "draft_observed",
    "played_character_id", "source_rite_id", "date_raw", "capture_epoch",
}
_BASE_KEYS = {
    "schema", "scope", "quote_source", "game_version", "executable_sha256", "available",
    "base_resource_cost_vector_observed", "draft_kind", "raw_scale", "resource_slot_names",
    "native_base_fee_slots_raw", "actual_debit_observed", "post_action_net_resource_change_observed",
    "draft_quote",
}
_COST_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id", "source_rite_id", "editing_owned_current_rite",
    "piety_cost_raw", "piety_missing_signed_raw", "has_enough_piety", "raw_scale",
    "final_creation_legality_observed", "other_resource_costs_observed",
}


def _integer(value: object, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native draft resource integer is malformed: {field}")


def normalize_player_religion_draft_resource_costs_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep actual absence and the native CCost quote distinct from any debit."""
    if not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != SCHEMA:
        raise ValueError("native player draft resource costs schema is malformed")
    for key in ("available", "window_present", "draft_observed"):
        if type(value[key]) is not bool:
            raise ValueError(f"native draft resource status is malformed: {key}")
    _integer(value["capture_epoch"], 1, (1 << 64) - 1, "capture_epoch")
    _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1, "date_raw")
    _integer(value["played_character_id"], 0, 0xFFFFFFFF, "played_character_id")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or actor.get("character_id") != value["played_character_id"]
                or snapshot.get("date_raw") != value["date_raw"] or value["failure"] is not None):
            raise ValueError("native draft resource quote differs from its queried frame")
    elif not isinstance(value["failure"], str) or not value["failure"]:
        raise ValueError("unavailable native draft resource quote lost its reason")
    window = value["current_draft_window"]
    if (not isinstance(window, dict) or set(window) != _WINDOW_KEYS
            or window["schema"] != "ck3_12002_current_rite_creation_window_v1"
            or any(type(window[key]) is not bool for key in
                   ("available", "present", "visible", "draft_observed"))
            or window["present"] != value["window_present"]
            or window["draft_observed"] != value["draft_observed"]):
        raise ValueError("native resource quote lost its actual current window")
    if window["draft_observed"] and not (window["available"] and window["present"] and window["visible"]):
        raise ValueError("native resource quote has no actual visible draft")
    if window["available"] and any(window[key] != value[key] for key in
                                   ("capture_epoch", "date_raw", "played_character_id")):
        raise ValueError("native resource window differs from its owner frame")
    if not isinstance(window["unavailable_reason"], str):
        raise ValueError("native resource window lost its source reason")
    base = value["base_resource_cost_quote"]
    if (not isinstance(base, dict) or set(base) != _BASE_KEYS
            or base["schema"] != "ck3_12002_rite_creation_base_resource_costs_v1"
            or base["scope"] != "native_command_draft_base_fee_quote"
            or base["quote_source"] != "native_piety_getter_plus_exact_CCost_initialization"
            or base["raw_scale"] != 100000
            or base["resource_slot_names"] != ["gold", "prestige", "piety", None, None, None, None, None, None, None]
            or base["actual_debit_observed"] is not False
            or base["post_action_net_resource_change_observed"] is not False
            or type(base["available"]) is not bool
            or base["base_resource_cost_vector_observed"] != base["available"]):
        raise ValueError("native draft base resource quote scope is malformed")
    build = require_exact_native_build(base["game_version"], base["executable_sha256"])
    if build != CK3_12002 or build != private_native_build_identity(snapshot):
        raise ValueError("native draft base resource quote belongs to another build")
    cost = base["draft_quote"]
    if (not isinstance(cost, dict) or set(cost) != _COST_KEYS
            or cost["schema"] != "ck3_12002_rite_creation_costs_v1"
            or type(cost["available"]) is not bool
            or cost["raw_scale"] != 100000
            or cost["final_creation_legality_observed"] is not False
            or cost["other_resource_costs_observed"] is not False
            or require_exact_native_build(cost["game_version"], cost["executable_sha256"]) != build):
        raise ValueError("native draft base resource quote lost its piety getter quote")
    for key in ("piety_cost_raw", "piety_missing_signed_raw"):
        if cost[key] is not None:
            _integer(cost[key], -(1 << 63), (1 << 63) - 1, key)
    for key in ("editing_owned_current_rite", "has_enough_piety"):
        if cost[key] is not None and type(cost[key]) is not bool:
            raise ValueError(f"native draft piety quote bool is malformed: {key}")
    slots = base["native_base_fee_slots_raw"]
    if base["available"]:
        if (not value["available"] or not value["draft_observed"] or not cost["available"]
                or not isinstance(slots, list) or len(slots) != 10
                or base["draft_kind"] not in ("edit_owned_current_rite", "create_rite_or_faith")):
            raise ValueError("native base fee vector has no observed current draft")
        for raw in slots:
            _integer(raw, -(1 << 63), (1 << 63) - 1, "native_base_fee_slots_raw")
        if slots[2] != cost["piety_cost_raw"] or cost["unavailable_reason"] is not None:
            raise ValueError("native base fee vector differs from its piety getter quote")
    elif slots is not None or base["draft_kind"] is not None:
        raise ValueError("unavailable native base fee quote was filled")
    # Preserve the whole native quote, including signed piety missing and the
    # provider's ten slots. No script/event effects or final action are executed.
    return deepcopy(value)


def query_player_religion_draft_resource_costs_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-draft-resource-costs-v1",
        )
        if (build != CK3_12002 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native draft resource envelope differs from the queried build/frame")
        value = normalize_player_religion_draft_resource_costs_v1(
            result.get("player_religion_draft_resource_costs"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native draft resource envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
