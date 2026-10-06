"""Read the player's native target Rite conversion verdict and paid quote."""

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
    CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build,
)


STEP = "query-player-religion-conversion-terms-v1"
DOMAIN_KEY = "player_religion_conversion_terms_v1"
SCHEMA = "ck3_12002_religion_conversion_terms_v1"
PERMISSION = "allow_private_player_religion_conversion_terms_query"
_COMMON_KEYS = {
    "schema", "available", "unavailable_reason", "capture_epoch",
    "date_raw", "played_character_id", "target_rite_id",
}
_BUILD_KEYS = {"game_version", "executable_sha256", "read_only"}
_TERMS_KEYS = _COMMON_KEYS | _BUILD_KEYS | {
    "can_convert", "native_blocker_text_available", "final_gate", "cost",
}
_GATE_KEYS = _COMMON_KEYS | _BUILD_KEYS | {
    "current_rite_id", "current_faith_id", "target_faith_id", "same_faith",
    "different_from_current_rite", "validator_without_payment", "validator_with_payment",
}
_COST_KEYS = _COMMON_KEYS | {
    "target_faith_id", "same_faith", "charge_piety", "piety_points",
    "piety_cost_raw", "actor_piety_raw", "can_afford_piety", "raw_scale",
    "final_conversion_legality_observed",
}


def _integer(value: object, lower: int, upper: int) -> bool:
    return type(value) is int and lower <= value <= upper


def _full_rite_id(value: object) -> int:
    if not _integer(value, 0, 0xFFFFFFFF):
        raise ValueError("target_rite_id must be a full unsigned 32-bit reference")
    return value


def _common(value: object, schema: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys or value["schema"] != schema:
        raise ValueError(f"native conversion schema is malformed: {schema}")
    if (type(value["available"]) is not bool
            or not _integer(value["capture_epoch"], 0, 0xFFFFFFFFFFFFFFFF)
            or not _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1)
            or not _integer(value["played_character_id"], -(1 << 31), (1 << 31) - 1)
            or not _integer(value["target_rite_id"], 0, 0xFFFFFFFF)):
        raise ValueError(f"native conversion scalar fields are malformed: {schema}")
    reason = value["unavailable_reason"]
    if ((value["available"] and reason is not None)
            or (not value["available"] and (not isinstance(reason, str) or not reason))):
        raise ValueError(f"native conversion source reason is malformed: {schema}")
    return value


def _build(value: Mapping[str, object], snapshot: Mapping[str, object]) -> None:
    observed = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if (observed not in (CK3_12002, CK3_12003, CK3_12004) or observed != private_native_build_identity(snapshot)
            or value["read_only"] is not True):
        raise ValueError("native conversion terms belong to another connected build")


def normalize_player_religion_conversion_terms_v1(
    value: object, *, snapshot: Mapping[str, object], target_rite_id: object,
) -> dict[str, object]:
    """Preserve the native verdict, quoted costs and unavailable sub-read values."""
    target = _full_rite_id(target_rite_id)
    terms = _common(value, private_native_schema(SCHEMA, snapshot), _TERMS_KEYS)
    _build(terms, snapshot)
    if (terms["capture_epoch"] == 0 or terms["target_rite_id"] != target
            or terms["native_blocker_text_available"] is not False
            or (terms["can_convert"] is not None and type(terms["can_convert"]) is not bool)):
        raise ValueError("native conversion terms target or verdict is malformed")

    gate = _common(terms["final_gate"], private_native_schema("ck3_12002_religion_conversion_rite_preview_v1", snapshot), _GATE_KEYS)
    _build(gate, snapshot)
    if (gate["target_rite_id"] != target
            or gate["capture_epoch"] != terms["capture_epoch"]
            or any(not _integer(gate[key], 0, 0xFFFFFFFF) for key in (
                "current_rite_id", "current_faith_id", "target_faith_id"))
            or any(type(gate[key]) is not bool for key in (
                "same_faith", "different_from_current_rite"))
            or any(gate[key] is not None and type(gate[key]) is not bool for key in (
                "validator_without_payment", "validator_with_payment"))):
        raise ValueError("native conversion final gate is malformed")

    cost = _common(terms["cost"], private_native_schema("ck3_12002_religion_conversion_cost_v1", snapshot), _COST_KEYS)
    if (cost["target_faith_id"] is not None and not _integer(cost["target_faith_id"], 0, 0xFFFFFFFF)
            or any(cost[key] is not None and type(cost[key]) is not bool for key in (
                "same_faith", "can_afford_piety"))
            or cost["charge_piety"] is not True
            or cost["raw_scale"] != 100000 or type(cost["raw_scale"]) is not int
            or cost["final_conversion_legality_observed"] is not False
            or (cost["piety_points"] is not None and not _integer(cost["piety_points"], -(1 << 31), (1 << 31) - 1))
            or any(cost[key] is not None and not _integer(cost[key], -(1 << 63), (1 << 63) - 1) for key in (
                "piety_cost_raw", "actor_piety_raw"))):
        raise ValueError("native conversion paid quote is malformed")

    actor = snapshot.get("played_character")
    if gate["available"] or terms["available"]:
        if (not isinstance(actor, Mapping)
                or terms["played_character_id"] != actor.get("character_id")
                or terms["date_raw"] != snapshot.get("date_raw")
                or gate["played_character_id"] != terms["played_character_id"]
                or gate["date_raw"] != terms["date_raw"]):
            raise ValueError("native conversion terms differ from the queried player frame")
    if gate["available"] and any(type(gate[key]) is not bool for key in (
            "validator_without_payment", "validator_with_payment")):
        raise ValueError("available native conversion final gate lacks a verdict")
    if cost["available"]:
        if (cost["capture_epoch"] != terms["capture_epoch"]
                or cost["date_raw"] != terms["date_raw"]
                or cost["played_character_id"] != terms["played_character_id"]
                or cost["target_rite_id"] != target
                or any(cost[key] is None for key in (
                    "target_faith_id", "same_faith", "piety_points",
                    "piety_cost_raw", "actor_piety_raw", "can_afford_piety"))):
            raise ValueError("available native conversion quote lacks its player/target frame")
    if (terms["available"] and (not gate["available"] or not cost["available"]
                                or type(terms["can_convert"]) is not bool)
            or not terms["available"] and terms["can_convert"] is not None):
        raise ValueError("native conversion terms lost their source availability")
    return deepcopy(terms)


def query_player_religion_conversion_terms_private_v1(
    driver: object, *, expected_revision: int, target_rite_id: object,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    target = _full_rite_id(target_rite_id)
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, request_fields={"target_rite_id": target},
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-conversion-terms-v1",
        )
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native conversion envelope differs from its queried build/frame")
        terms = normalize_player_religion_conversion_terms_v1(
            result.get("player_religion_conversion_terms"), snapshot=before,
            target_rite_id=target,
        )
        if result.get("status") != ("observed" if terms["available"] else "unavailable"):
            raise ValueError("native conversion envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **terms, **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "advertised": False,
    }
