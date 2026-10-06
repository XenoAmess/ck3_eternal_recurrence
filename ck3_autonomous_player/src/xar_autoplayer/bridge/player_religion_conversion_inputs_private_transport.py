"""Read native conversion inputs, predicted base fulfillment and optional fervor."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .player_conversion_fervor_inputs import normalize_player_conversion_fervor_inputs_v1
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-conversion-inputs-v1"
DOMAIN_KEY = "player_religion_conversion_inputs_v1"
SCHEMA = "ck3_12002_religion_conversion_inputs_v1"
PERMISSION = "allow_private_player_religion_conversion_inputs_query"
_COMMON = {"schema", "available", "unavailable_reason", "capture_epoch", "date_raw", "played_character_id"}
_TOP = _COMMON | {"target_rite_id", "conversion_gates", "predicted_base_fulfillment"}
_REFERENCES = {"target_rite_id", "actor_faith_id", "target_faith_id", "actor_religion_id",
               "target_religion_id", "realm_state_rite_id", "realm_state_faith_id"}
_BOOLEANS = {"recently_converted", "recent_flag_key_registered", "same_faith", "same_religion",
             "state_rite_target_match", "state_faith_target_match"}
_GATES = _COMMON | _REFERENCES | _BOOLEANS | {"requested_target_rite_id", "knowledge_level_raw", "raw_scale"}
_BASES = {"current_rite_base_raw", "target_rite_base_raw", "expected_base_change_raw"}
_NOT_OBSERVED = {"is_current_fulfillment", "is_observed_conversion_gain", "is_final_ai_desire"}
_PREDICTION = _COMMON | _BASES | _NOT_OBSERVED | {
    "game_version", "executable_sha256", "read_only", "current_rite_id", "target_rite_id", "raw_scale",
}


def _reference(value: object, *, nullable: bool = False) -> bool:
    return (nullable and value is None) or type(value) is int and 0 <= value <= 0xFFFFFFFF


def _target(value: object) -> int:
    if not _reference(value):
        raise ValueError("target_rite_id must be a full unsigned 32-bit reference")
    return value


def _source(value: object, schema: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys or value["schema"] != schema:
        raise ValueError("native conversion inputs schema is malformed")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int or type(value["played_character_id"]) is not int
            or value["available"] and value["unavailable_reason"] is not None
            or not value["available"] and (not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"])):
        raise ValueError("native conversion inputs source status is malformed")
    return value


def normalize_player_religion_conversion_inputs_v1(
    value: object, *, snapshot: Mapping[str, object], target_rite_id: object,
) -> dict[str, object]:
    target = _target(target_rite_id)
    top_keys = _TOP | ({"conversion_fervor"} if isinstance(value, dict) and "conversion_fervor" in value else set())
    top = _source(value, private_native_schema(SCHEMA, snapshot), top_keys)
    gates = _source(top["conversion_gates"], private_native_schema("ck3_12002_religion_conversion_gates_v1", snapshot), _GATES)
    prediction = _source(top["predicted_base_fulfillment"], private_native_schema("ck3_12002_expected_rite_base_fulfillment_v1", snapshot), _PREDICTION)
    build = require_exact_native_build(prediction["game_version"], prediction["executable_sha256"])
    if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot)
            or prediction["read_only"] is not True or top["target_rite_id"] != target
            or gates["requested_target_rite_id"] != target
            or prediction["target_rite_id"] != target):
        raise ValueError("native conversion inputs differ from the connected build/target")
    if (any(not _reference(gates[key], nullable=True) for key in _REFERENCES)
            or any(gates[key] is not None and type(gates[key]) is not bool for key in _BOOLEANS)
            or not _reference(prediction["current_rite_id"])
            or any(prediction[key] is not False for key in _NOT_OBSERVED)
            or any(type(child["raw_scale"]) is not int or child["raw_scale"] != 100000 for child in (gates, prediction))
            or gates["knowledge_level_raw"] is not None and (type(gates["knowledge_level_raw"]) is not int
                or not -(1 << 63) <= gates["knowledge_level_raw"] < (1 << 63))
            or any(prediction[key] is not None and (type(prediction[key]) is not int
                or not -(1 << 63) <= prediction[key] < (1 << 63)) for key in _BASES)):
        raise ValueError("native conversion input scalar fields are malformed")
    for child in (gates, prediction):
        if child["available"]:
            actor = snapshot.get("played_character")
            if (not isinstance(actor, Mapping) or top["played_character_id"] != actor.get("character_id")
                    or top["date_raw"] != snapshot.get("date_raw")
                    or any(child[key] != top[key] for key in ("capture_epoch", "date_raw", "played_character_id"))):
                raise ValueError("native conversion inputs crossed their queried player frame")
    if gates["available"] and (gates["target_rite_id"] != target
            or any(gates[key] is None for key in (_BOOLEANS | {"knowledge_level_raw"}))):
        raise ValueError("available native conversion gates lost their actual inputs")
    if prediction["available"] and any(prediction[key] is None for key in _BASES):
        raise ValueError("available native conversion base prediction lacks its raw values")
    if top["available"] and (not gates["available"] or not prediction["available"]):
        raise ValueError("available native conversion inputs lack a source component")
    if "conversion_fervor" in top:
        normalize_player_conversion_fervor_inputs_v1(
            top["conversion_fervor"], conversion_inputs=top, snapshot=snapshot,
        )
    return deepcopy(top)


def query_player_religion_conversion_inputs_private_v1(
    driver: object, *, expected_revision: int, target_rite_id: object,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    target = _target(target_rite_id)
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"target_rite_id": target}, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(result.get("game_version"), result.get("executable_sha256"),
                                           result.get("backend_id"), suffix="player-religion-conversion-inputs-v1")
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native conversion inputs envelope differs from its queried build/frame")
        inputs = normalize_player_religion_conversion_inputs_v1(
            result.get("player_religion_conversion_inputs"), snapshot=before, target_rite_id=target,
        )
        if result.get("status") != ("observed" if inputs["available"] else "unavailable"):
            raise ValueError("native conversion inputs envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**inputs, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
            "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
            "status": result["status"], "read_only": True, "advertised": False}
