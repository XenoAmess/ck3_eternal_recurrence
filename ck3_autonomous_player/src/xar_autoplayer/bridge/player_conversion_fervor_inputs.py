"""Normalize the independent same-frame native conversion fervor inputs."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12003, require_exact_native_build


SCHEMA = "ck3_12003_conversion_fervor_inputs_v1"
_KEYS = {
    "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
    "date_raw", "played_character_id", "requested_target_rite_id",
    "actor_faith_id", "target_faith_id", "actor_fervor_raw", "target_fervor_raw",
    "raw_scale", "unit", "is_final_conversion_cost", "is_final_conversion_desire",
}
_FRAME = ("capture_epoch", "date_raw", "played_character_id")
_FAITH_IDS = ("actor_faith_id", "target_faith_id")
_RAWS = ("actor_fervor_raw", "target_fervor_raw")


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def normalize_player_conversion_fervor_inputs_v1(
    value: object, *, conversion_inputs: Mapping[str, object],
    snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep observed zero/full Faith IDs; never modify the existing verdicts."""
    if not isinstance(value, dict) or set(value) != _KEYS or value["schema"] != SCHEMA:
        raise ValueError("native conversion fervor inputs schema is malformed")
    if (value["read_only"] is not True or type(value["available"]) is not bool
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or value["unit"] != "fervor_points"
            or value["is_final_conversion_cost"] is not False
            or value["is_final_conversion_desire"] is not False):
        raise ValueError("native conversion fervor inputs status/units are malformed")
    reason = value["unavailable_reason"]
    if (value["available"] and reason is not None) or (
            not value["available"] and (not isinstance(reason, str) or not reason)):
        raise ValueError("native conversion fervor inputs lost their source reason")

    if not isinstance(conversion_inputs, Mapping) or (
            conversion_inputs.get("schema") != "ck3_12003_religion_conversion_inputs_v1"):
        raise ValueError("native conversion fervor inputs lack their .3 owning query")
    prediction = conversion_inputs.get("predicted_base_fulfillment")
    gates = conversion_inputs.get("conversion_gates")
    if (not isinstance(prediction, Mapping) or not isinstance(gates, Mapping)
            or prediction.get("schema") != "ck3_12003_expected_rite_base_fulfillment_v1"
            or gates.get("schema") != "ck3_12003_religion_conversion_gates_v1"):
        raise ValueError("native conversion fervor inputs lack their existing source components")
    build = require_exact_native_build(
        prediction.get("game_version"), prediction.get("executable_sha256"),
    )
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native conversion fervor inputs belong to another exact build")

    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or not _integer(value["capture_epoch"], 1, (1 << 64) - 1)
            or not _integer(value["date_raw"], -(1 << 31), (1 << 31) - 1)
            or not _integer(value["played_character_id"], 0, 0xFFFFFFFF)
            or not _integer(value["requested_target_rite_id"], 0, 0xFFFFFFFF)
            or not _integer(actor.get("character_id"), 0, 0xFFFFFFFF)
            or not _integer(snapshot.get("date_raw"), -(1 << 31), (1 << 31) - 1)
            or value["played_character_id"] != actor["character_id"]
            or value["date_raw"] != snapshot["date_raw"]
            or any(type(conversion_inputs.get(key)) is not int
                   or value[key] != conversion_inputs[key] for key in _FRAME)
            or type(conversion_inputs.get("target_rite_id")) is not int
            or value["requested_target_rite_id"] != conversion_inputs["target_rite_id"]
            or type(gates.get("requested_target_rite_id")) is not int
            or value["requested_target_rite_id"] != gates["requested_target_rite_id"]
            or type(prediction.get("target_rite_id")) is not int
            or value["requested_target_rite_id"] != prediction["target_rite_id"]):
        raise ValueError("native conversion fervor inputs crossed their queried player frame/target")
    # A failed older component may retain only some identities. Join its actual
    # source frame whenever observed; its availability is not a new fervor gate.
    for child in (gates, prediction):
        if child.get("available") is True and any(
                type(child.get(key)) is not int or child[key] != value[key] for key in _FRAME):
            raise ValueError("native conversion fervor inputs differ from an observed source frame")

    for key in _FAITH_IDS:
        observed = value[key]
        if observed is not None and not _integer(observed, 0, 0xFFFFFFFE):
            raise ValueError("native conversion fervor inputs contain a malformed full Faith ID")
        gate_id = gates.get(key)
        if observed is not None and gate_id is not None and (
                not _integer(gate_id, 0, 0xFFFFFFFE) or observed != gate_id):
            raise ValueError("native conversion fervor inputs differ from an observed gate Faith ID")
    if (all(value[key] is not None for key in _FAITH_IDS)
            and type(gates.get("same_faith")) is bool
            and gates["same_faith"] != (value["actor_faith_id"] == value["target_faith_id"])):
        raise ValueError("native conversion fervor inputs differ from the observed same-Faith gate")

    if value["available"]:
        if (any(value[key] is None for key in _FAITH_IDS)
                or any(not _integer(value[key], -(1 << 63), (1 << 63) - 1) for key in _RAWS)):
            raise ValueError("available native conversion fervor inputs lack their actual IDs/raw values")
    elif any(value[key] is not None for key in _RAWS):
        raise ValueError("unavailable native conversion fervor inputs contain unsampled raw values")
    return deepcopy(value)
