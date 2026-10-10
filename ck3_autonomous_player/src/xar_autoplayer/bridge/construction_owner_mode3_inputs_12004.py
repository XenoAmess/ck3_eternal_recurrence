"""Independent copied current-frame inputs for the actual4 income mode3 path.

Conditional aggregates are source software projections. These inputs neither
attribute income to one building nor change the construction selector.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .version_identity import CK3_12004, NativeBuildIdentity

FIELD_NAME = "native_mode3_inputs"
SCHEMA = "xar.ck3.construction-owner-mode3-inputs-12004-v1"
_MODEL_FAILURES = {
    "none", "exact_build", "application_main", "paused_frame", "player_identity",
    "held_title_source", "holding_province_identity", "definition_source", "frame_changed",
}
_INPUT_FLAGS = {
    "inputs_observed", "all_reached_inputs_observed", "observed_native_producer_call",
    "per_building_attribution", "realized_holder_net",
}
_UNPROVEN = {"observed_native_producer_call", "per_building_attribution", "realized_holder_net"}
_RAW_Q64 = {
    "loaded_publisher_718_raw", "loaded_key_3f_raw", "factor_before_context",
    "context_factor_raw", "owner_factor_raw", "conditional_aggregate_raw",
}
_KEYS_U16 = {"selected_a3_or_a4_key", "selected_a6_or_a7_key", "context_dynamic_key"}
_SIGNED_EAX = {"child_28be0b0_signed_eax", "child_28b9300_signed_eax"}
_INPUT_FIELDS = {
    *_INPUT_FLAGS, *_RAW_Q64, *_KEYS_U16, *_SIGNED_EAX,
    "unavailable_input", "snapshot_revision", "province_id", "context_predicate_2c25010", "components",
}


def _object(value: object, path: str, fields: set[str]) -> Mapping:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ValueError(path + " requires exactly its native copied fields")
    return value


def _int(value: object, path: str, bits: int, *, unsigned: bool = False,
         nullable: bool = False) -> int | None:
    if nullable and value is None:
        return None
    minimum, maximum = (0, 2**bits - 1) if unsigned else (-(2**(bits - 1)), 2**(bits - 1) - 1)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(path + f" must retain a native {'unsigned' if unsigned else 'signed'}{bits} integer")
    return value


def _bool(value: object, path: str, *, nullable: bool = False) -> bool | None:
    if nullable and value is None:
        return None
    if type(value) is not bool:
        raise ValueError(path + " must retain a native boolean")
    return value


def _text(value: object, path: str) -> str:
    if type(value) is not str:
        raise ValueError(path + " must retain its native source/failure text")
    return value


def _inputs(value: object, path: str, *, revision: int, province_id: int) -> dict:
    raw = _object(value, path, _INPUT_FIELDS)
    result = {
        "snapshot_revision": _int(raw["snapshot_revision"], path + ".snapshot_revision", 64, unsigned=True, nullable=True),
        "province_id": _int(raw["province_id"], path + ".province_id", 32, nullable=True),
        "unavailable_input": _text(raw["unavailable_input"], path + ".unavailable_input"),
        "context_predicate_2c25010": _bool(raw["context_predicate_2c25010"], path + ".context_predicate_2c25010", nullable=True),
    }
    if (result["snapshot_revision"] not in (None, revision)
            or result["province_id"] not in (None, province_id)):
        raise ValueError(path + " differs from its copied current frame or holding")
    for field in _INPUT_FLAGS:
        result[field] = _bool(raw[field], path + "." + field)
        if field in _UNPROVEN and result[field]:
            raise ValueError(path + " cannot grant a native producer invocation, building attribution or realized net")
    for field in _RAW_Q64:
        result[field] = _int(raw[field], path + "." + field, 64, nullable=True)
    for field in _KEYS_U16:
        result[field] = _int(raw[field], path + "." + field, 16, unsigned=True, nullable=True)
    for field in _SIGNED_EAX:
        result[field] = _int(raw[field], path + "." + field, 32, nullable=True)
    components = raw["components"]
    if not isinstance(components, list):
        raise ValueError(path + ".components must retain native component order")
    result["components"] = []
    for index, value in enumerate(components):
        location = f"{path}.components[{index}]"
        component = _object(value, location, {"call_rva", "key_u16", "reached", "raw_q64", "unavailable_input"})
        result["components"].append({
            "call_rva": _int(component["call_rva"], location + ".call_rva", 32, unsigned=True),
            "key_u16": _int(component["key_u16"], location + ".key_u16", 16, unsigned=True),
            "reached": _bool(component["reached"], location + ".reached"),
            "raw_q64": _int(component["raw_q64"], location + ".raw_q64", 64, nullable=True),
            "unavailable_input": _text(component["unavailable_input"], location + ".unavailable_input"),
        })
    return result


def normalize_construction_owner_mode3_inputs_12004(
        value: object, *, source_frame: Mapping, world: Mapping,
        build: NativeBuildIdentity) -> dict | None:
    """Strictly bind the optional packet to the existing material query frame."""
    if value is None:
        return None
    raw = _object(value, FIELD_NAME, {
        "schema", "source_executable_sha256", "current_frame_observed", "failure",
        "snapshot_revision", "date_raw", "player_character_id", "holdings",
    })
    if (build != CK3_12004 or raw["schema"] != SCHEMA
            or raw["source_executable_sha256"] != CK3_12004.executable_sha256):
        raise ValueError(FIELD_NAME + " requires its exact actual4 source identity")
    result = {
        "schema": SCHEMA, "source_executable_sha256": CK3_12004.executable_sha256,
        "current_frame_observed": _bool(raw["current_frame_observed"], FIELD_NAME + ".current_frame_observed"),
        "failure": _text(raw["failure"], FIELD_NAME + ".failure"),
        "snapshot_revision": _int(raw["snapshot_revision"], FIELD_NAME + ".snapshot_revision", 64, unsigned=True, nullable=True),
        "date_raw": _int(raw["date_raw"], FIELD_NAME + ".date_raw", 32, nullable=True),
        "player_character_id": _int(raw["player_character_id"], FIELD_NAME + ".player_character_id", 32, nullable=True),
    }
    holdings = raw["holdings"]
    if result["failure"] not in _MODEL_FAILURES:
        raise ValueError(FIELD_NAME + ".failure differs from the native model failure enum")
    if not isinstance(holdings, list):
        raise ValueError(FIELD_NAME + ".holdings must retain the held source order")
    if not result["current_frame_observed"]:
        if holdings or any(result[field] is not None for field in (
                "snapshot_revision", "date_raw", "player_character_id")):
            raise ValueError(FIELD_NAME + " unobserved frame must retain null metadata and no holdings")
        return {**result, "holdings": []}
    for field, frame_field in (("snapshot_revision", "native_revision"), ("date_raw", "date_raw"),
                               ("player_character_id", "actor_character_id")):
        if result[field] is None or result[field] != source_frame.get(frame_field):
            raise ValueError(FIELD_NAME + "." + field + " differs from this material source frame")
    if (result["snapshot_revision"] != world.get("snapshot_revision")
            or result["date_raw"] != world.get("date_raw")
            or result["player_character_id"] != world.get("player_character_id")):
        raise ValueError(FIELD_NAME + " differs from this native world observation")
    world_rows = world.get("active_constructions")
    if not isinstance(world_rows, list):
        raise ValueError(FIELD_NAME + " lacks this query's held province identities")
    identities = [(row.get("barony_title_id"), row.get("province_id"))
                  for row in world_rows if isinstance(row, Mapping)]
    copied, seen = [], set()
    for index, value in enumerate(holdings):
        path = f"{FIELD_NAME}.holdings[{index}]"
        row = _object(value, path, {"barony_title_id", "province_id", "inputs"})
        title = _int(row["barony_title_id"], path + ".barony_title_id", 32)
        province = _int(row["province_id"], path + ".province_id", 32)
        identity = title, province
        if identity in seen or identities.count(identity) != 1:
            raise ValueError(path + " lacks one exact held title/province in this query")
        seen.add(identity)
        copied.append({"barony_title_id": title, "province_id": province,
                       "inputs": _inputs(row["inputs"], path + ".inputs",
                                         revision=result["snapshot_revision"], province_id=province)})
    return {**result, "holdings": copied}


def _holding_status(inputs: Mapping) -> tuple[str, str | None]:
    if inputs["snapshot_revision"] is None or inputs["province_id"] is None:
        return "partial", inputs["unavailable_input"] or "mode3_holding_frame_metadata_unavailable"
    if (inputs["inputs_observed"] and inputs["all_reached_inputs_observed"]
            and inputs["conditional_aggregate_raw"] is not None):
        return "conditional_projection_available", None
    return "partial", inputs["unavailable_input"] or "reached_mode3_source_inputs_unavailable"


def normalize_mode3_world_observation_12004(
        world: Mapping, *, source_frame: Mapping, build: NativeBuildIdentity) -> tuple[dict, dict]:
    """Keep new-source validation independent from ordinary construction."""
    copied = dict(world)
    if FIELD_NAME not in world:
        return copied, {}
    try:
        packet = normalize_construction_owner_mode3_inputs_12004(
            world[FIELD_NAME], source_frame=source_frame, world=world, build=build)
    except ValueError as error:
        return copied, {"native_mode3_inputs_status": "source_red", "native_mode3_inputs_reason": str(error)}
    copied[FIELD_NAME] = packet
    if packet is None:
        status, reason = "observation_unavailable", "native_mode3_inputs_explicitly_null"
    elif not packet["current_frame_observed"]:
        status, reason = "observation_unavailable", packet["failure"]
    else:
        statuses = [_holding_status(row["inputs"]) for row in packet["holdings"]]
        status = ("conditional_projection_available" if statuses and all(
            item[0] == "conditional_projection_available" for item in statuses) else "partial")
        reason = next((item[1] for item in statuses if item[1] is not None),
                      None if statuses else "no_held_mode3_inputs")
    return copied, {"native_mode3_inputs_status": status, "native_mode3_inputs_reason": reason}


def mode3_province_observation_12004(source: Mapping, *, barony_title_id: int, province_id: int) -> dict:
    """Select raw copied inputs from this already-read query; issue no query."""
    world = source["world"]
    if FIELD_NAME not in world:
        return {}
    status, reason = source["native_mode3_inputs_status"], source["native_mode3_inputs_reason"]
    packet = world[FIELD_NAME]
    observation = {
        "status": status, "reason": reason, "inputs": None,
        "barony_title_id": barony_title_id, "province_id": province_id,
        "source_frame": deepcopy(source["source_frame"]),
        "observed_native_producer_call": False, "per_building_attribution": False,
        "realized_holder_net": False, "conditional_aggregate_kind": "source_software_projection",
    }
    if status != "source_red" and packet is not None:
        observation.update(schema=packet["schema"], source_executable_sha256=packet["source_executable_sha256"])
    if status == "source_red" or packet is None or not packet["current_frame_observed"]:
        return {FIELD_NAME: observation}
    rows = [row for row in packet["holdings"] if row["barony_title_id"] == barony_title_id
            and row["province_id"] == province_id]
    if len(rows) != 1:
        observation.update(status="observation_unavailable", reason="mode3_holding_missing_or_duplicate")
    else:
        inputs = rows[0]["inputs"]
        status, reason = _holding_status(inputs)
        observation.update(status=status, reason=reason, inputs=deepcopy(inputs))
    return {FIELD_NAME: observation}
