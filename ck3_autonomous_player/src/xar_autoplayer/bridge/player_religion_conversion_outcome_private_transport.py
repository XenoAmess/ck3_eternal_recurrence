"""Read independent current conversion-related facts, never action causality."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .player_religion_context_private_transport import normalize_player_religion_context_v1
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-conversion-outcome-v1"
DOMAIN_KEY = "player_religion_conversion_outcome_v1"
SCHEMA = "ck3_12002_religion_conversion_outcome_v1"
PERMISSION = "allow_private_player_religion_conversion_outcome_query"
_COMMON = {"schema", "available", "unavailable_reason", "capture_epoch", "date_raw", "played_character_id"}
_BUILD = {"game_version", "executable_sha256", "read_only"}
_TOP = _COMMON | _BUILD | {"target_rite_id", "target_reached", "target_reached_is_identity_only",
                          "conversion_causality_inferred", "actor", "state"}
_RESOURCES = {"piety_raw", "gold_raw", "prestige_raw"}
_ACTOR = _COMMON | _BUILD | _RESOURCES | {"current_religion", "raw_scale", "conversion_causality_inferred"}
_STATE_RAW = {"knowledge_level_raw", "spiritual_fulfillment_raw", "baseline_spiritual_fulfillment_raw"}
_FLAGS = {"faith_conversion_recently_converted", "conversion_memory_recently_created", "recent_convert"}
_STATE = _COMMON | _STATE_RAW | _FLAGS | {"requested_target_rite_id", "target_rite_id", "raw_scale",
                                        "flag_expiry_unit", "is_conversion_gain"}
_FLAG_FIELDS = {"key_registered", "present", "timed", "expiry_counter_raw", "current_counter_raw", "remaining_updates"}


def _integer(value: object, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < (1 << (bits - 1))


def _target(value: object) -> int:
    if type(value) is not int or not 0 <= value < 0xFFFFFFFF:
        raise ValueError("target_rite_id must be a full uint32 reference below the absent sentinel")
    return value


def _source(value: object, schema: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys or value["schema"] != schema:
        raise ValueError("native conversion outcome schema is malformed")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int or type(value["played_character_id"]) is not int
            or value["available"] and value["unavailable_reason"] is not None
            or not value["available"] and (not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"])):
        raise ValueError("native conversion outcome source status is malformed")
    return value


def _build(value: Mapping[str, object], snapshot: Mapping[str, object]) -> None:
    observed = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if observed not in (CK3_12002, CK3_12003, CK3_12004) or observed != private_native_build_identity(snapshot) or value["read_only"] is not True:
        raise ValueError("native conversion outcome belongs to another connected build")


def normalize_player_religion_conversion_outcome_v1(
    value: object, *, snapshot: Mapping[str, object], target_rite_id: object,
) -> dict[str, object]:
    target = _target(target_rite_id)
    top = _source(value, private_native_schema(SCHEMA, snapshot), _TOP)
    _build(top, snapshot)
    actor = _source(top["actor"], private_native_schema("ck3_12002_conversion_outcome_actor_v1", snapshot), _ACTOR)
    _build(actor, snapshot)
    state = _source(top["state"], private_native_schema("ck3_12002_religion_conversion_outcome_state_v1", snapshot), _STATE)
    context = normalize_player_religion_context_v1(actor["current_religion"], snapshot=snapshot)
    if (top["target_rite_id"] != target or state["requested_target_rite_id"] != target
            or state["target_rite_id"] is not None and state["target_rite_id"] != target
            or top["target_reached"] is not None and type(top["target_reached"]) is not bool
            or top["target_reached_is_identity_only"] is not True
            or top["conversion_causality_inferred"] is not False
            or actor["conversion_causality_inferred"] is not False
            or state["flag_expiry_unit"] != "native_flag_updates" or state["is_conversion_gain"] is not False
            or any(type(child["raw_scale"]) is not int or child["raw_scale"] != 100000 for child in (actor, state))
            or any(actor[key] is not None and not _integer(actor[key], 64) for key in _RESOURCES)
            or any(state[key] is not None and not _integer(state[key], 64) for key in _STATE_RAW)):
        raise ValueError("native conversion outcome target/resource fields are malformed")
    for key in _FLAGS:
        flag = state[key]
        if (not isinstance(flag, dict) or set(flag) != _FLAG_FIELDS
                or any(flag[field] is not None and type(flag[field]) is not bool for field in ("key_registered", "present", "timed"))
                or any(flag[field] is not None and not _integer(flag[field], 32) for field in ("expiry_counter_raw", "current_counter_raw"))
                or flag["remaining_updates"] is not None and not _integer(flag["remaining_updates"], 64)):
            raise ValueError("native conversion outcome flag observation is malformed")
    for child in (actor, state, context):
        if child["available"]:
            played = snapshot.get("played_character")
            if (not isinstance(played, Mapping) or top["played_character_id"] != played.get("character_id")
                    or top["date_raw"] != snapshot.get("date_raw")
                    or any(child[key] != top[key] for key in ("capture_epoch", "date_raw", "played_character_id"))):
                raise ValueError("native conversion outcome crossed its queried player frame")
    if actor["available"] and (not context["available"] or any(actor[key] is None for key in _RESOURCES)):
        raise ValueError("available native conversion outcome actor lacks actual facts")
    if state["available"] and (state["target_rite_id"] != target or any(state[key] is None for key in _STATE_RAW)
            or any(state[key][field] is None for key in _FLAGS for field in ("key_registered", "present"))):
        raise ValueError("available native conversion outcome state lacks actual facts")
    if top["available"] and (not actor["available"] or not state["available"]):
        raise ValueError("available native conversion outcome lacks a source component")
    # A state failure can coexist with an independently observed identity bool.
    # Nulls, sentinel counters and legal absent flags are preserved unchanged.
    return deepcopy(top)


def query_player_religion_conversion_outcome_private_v1(
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
                                           result.get("backend_id"), suffix="player-religion-conversion-outcome-v1")
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native conversion outcome envelope differs from its queried build/frame")
        outcome = normalize_player_religion_conversion_outcome_v1(
            result.get("player_religion_conversion_outcome"), snapshot=before, target_rite_id=target,
        )
        if result.get("status") != ("observed" if outcome["available"] else "unavailable"):
            raise ValueError("native conversion outcome envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**outcome, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
            "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
            "status": result["status"], "advertised": False}
