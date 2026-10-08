"""Default-off exact .4 actor cached-succession observation without business credit."""
from __future__ import annotations

from copy import deepcopy
import math
import uuid

from .confucian_readonly_private_v1 import (
    ENVELOPE_KEYS, PUBLIC_KEYS, _common_payload, exact, full_id, integer, reason,
    query_binding as _shared_query_binding,
    same_query_frame as _shared_same_query_frame,
)
from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12004, require_exact_native_build

PERMISSION = "allow_private_actor_cached_succession_queries"
STEP = "query-actor-cached-succession-v1"
DOMAIN_KEY = "actor_cached_succession_v1"
BACKEND_ID = "ck3-1.20.0.4-native-actor-cached-succession-v1"
NATIVE_SCHEMA = "ck3-1.20.0.4-actor-cached-succession-v1"
NESTED_KEY = "actor_cached_succession"
PUBLIC_SCHEMA = "ck3-actor-cached-succession-public-v1"
OPERATION = "actor_cached_succession"
PAYLOAD_KEYS = {
    "schema", "read_only", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "played_character_full_id", "roster_complete", "native_count",
    "complete_cached_successor_ids", "native_data_pointer", "land_state_pointer",
}


def _exact_build(value):
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build != CK3_12004:
        raise ValueError("actor cached-succession query requires the exact .4 native build")
    return build


def query_binding(snapshot, expected_revision):
    binding = _shared_query_binding(snapshot, expected_revision)
    if private_native_build_identity(snapshot) != CK3_12004:
        raise ValueError("actor cached-succession query requires its current exact .4 actor/frame")
    return binding


def same_query_frame(before, after, binding):
    try:
        later = query_binding(after, binding["revision"])
    except (ValueError, TypeError, AttributeError):
        return False
    return later == binding and _shared_same_query_frame(before, after, binding)


def normalize_cached_succession(value, binding):
    exact(value, PAYLOAD_KEYS, "actor cached-succession native payload")
    _exact_build(value)
    _common_payload(value, NATIVE_SCHEMA, binding)
    if value["read_only"] is not True or type(value["roster_complete"]) is not bool:
        raise ValueError("actor cached succession requires actual readonly/completeness")
    if full_id(value["played_character_full_id"], "played full identity") != (
            binding["played_character_id"] & 0xFFFFFFFF):
        raise ValueError("played full identity differs from its actual bound actor")
    if value["roster_complete"] is not value["available"]:
        raise ValueError("cached successor completeness differs from actual availability")
    reason(value["unavailable_reason"], not value["available"], "actor cached succession")
    if not value["available"]:
        if any(value[name] is not None for name in (
                "native_count", "complete_cached_successor_ids",
                "native_data_pointer", "land_state_pointer")):
            raise ValueError("unavailable cached succession must preserve null roster/pointers")
        return deepcopy(value)
    count = integer(value["native_count"], 0, 2**31-1, "native cached successor count")
    identities = value["complete_cached_successor_ids"]
    if type(identities) is not list or len(identities) != count:
        raise ValueError("cached successors require their complete original-order array/count")
    for identity in identities:
        full_id(identity, "cached successor full identity")
    integer(value["land_state_pointer"], 1, 2**64-1, "actual LandState pointer")
    pointer = integer(value["native_data_pointer"], 0, 2**64-1, "actual cached successor data pointer")
    if pointer == 0 and count != 0:
        raise ValueError("null cached successor data pointer is legal only for an empty cache")
    return deepcopy(value)


def project_native_query(raw, binding, expected_build=None):
    exact(raw, ENVELOPE_KEYS | {NESTED_KEY}, "native actor cached-succession envelope")
    build = _exact_build(raw)
    if expected_build is not None and build != expected_build:
        raise ValueError("cached-succession envelope differs from its connected build")
    expected = {
        "step": STEP, "accepted": True, "private_build": True, "read_only": True,
        "advertised": False, "game_version": build.game_version, "domain_key": DOMAIN_KEY,
        "backend_id": BACKEND_ID, "snapshot_revision": binding["native_revision"],
        "date_raw": binding["date_raw"],
    }
    if any(type(raw[name]) is not type(wanted) or raw[name] != wanted
           for name, wanted in expected.items()):
        raise ValueError("cached-succession envelope differs from its actual operation/frame")
    value = normalize_cached_succession(raw[NESTED_KEY], binding)
    if raw["status"] != ("observed" if value["available"] else "unavailable"):
        raise ValueError("cached-succession envelope availability differs")
    return {
        "schema": PUBLIC_SCHEMA, "operation": OPERATION, "native_result": deepcopy(raw),
        "queried_snapshot_id": binding["snapshot_id"], "queried_revision": binding["revision"],
        "queried_native_revision": binding["native_revision"], "date_raw": binding["date_raw"],
        "game_pid": binding["game_pid"], "connection_generation": binding["connection_generation"],
        "player_character_id": binding["played_character_id"],
        "business_postcondition_verified": False, "full_product_acceptance_credit": False,
    }


def normalize_public_query(raw, binding):
    exact(raw, PUBLIC_KEYS, "public actor cached-succession result")
    projected = project_native_query(raw["native_result"], binding, CK3_12004)
    if any(type(raw[name]) is not type(wanted) or raw[name] != wanted
           for name, wanted in projected.items()):
        raise ValueError("public cached-succession binding or credit changed")
    return deepcopy(raw)


def encode_query_request(binding, request_id):
    if type(request_id) is not str or not request_id:
        raise ValueError("actual cached-succession request identity required")
    return {
        "type": "execute_step", "protocol_version": 1, "request_id": request_id, "step": STEP,
        "expected_snapshot_revision": integer(
            binding["native_revision"], 1, 2**64-1, "native_revision"),
    }


def query_actor_cached_succession_private_v1(driver, *, expected_revision, timeout_seconds=10.0):
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError("private actor cached-succession query is disabled")
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 60):
        raise ValueError("bounded positive cached-succession query timeout required")
    before = driver.take_snapshot()
    try:
        binding = query_binding(before, expected_revision)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    request_id = "actor-cached-succession-" + uuid.uuid4().hex
    driver.endpoint.send(encode_query_request(binding, request_id))
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (type(frame) is not dict or frame.get("type") != "command_result"
            or type(frame.get("protocol_version")) is not int or frame["protocol_version"] != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("cached-succession command_result unresolved; no automatic retry")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("cached-succession native error: " + str(frame.get("error", "unknown")))
    after = driver.take_snapshot()
    if not same_query_frame(before, after, binding):
        raise BridgeUnavailableError("cached-succession query crossed its actual paused owner/frame")
    try:
        return project_native_query(frame.get("result"), binding, private_native_build_identity(before))
    except ValueError as error:
        raise BridgeUnavailableError("malformed native cached-succession read: " + str(error)) from error

