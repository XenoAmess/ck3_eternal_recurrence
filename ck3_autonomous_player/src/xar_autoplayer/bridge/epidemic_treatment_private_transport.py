"""Unadvertised exact-build, fixed-key CE1 treatment presence readback."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import _binding


STEP = "query-player-epidemic-treatment-presence-v1"
KEY = "ce1_unorthodox_epidemic_treatment"


def query_player_epidemic_treatment_presence_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0
) -> dict[str, object]:
    if getattr(driver, "allow_private_epidemic_treatment_presence_query", False) is not True:
        raise UnsupportedStepError("private epidemic treatment query is disabled")
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision <= 0:
        raise ValueError("expected_revision must be a positive integer")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    played = before.get("played_character")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or native_revision <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not -(2**31) <= date_raw <= 2**31 - 1
        or not isinstance(played, Mapping)
        or played.get("alive") is not True
        or isinstance(played.get("character_id"), bool)
        or not isinstance(played.get("character_id"), int)
        or played["character_id"] <= 0
    ):
        raise BridgeUnavailableError("epidemic treatment query requires one living played character on a paused map frame")
    request_id = "epidemic-treatment-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if not isinstance(frame, dict) or frame.get("type") != "command_result" or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id or frame.get("ok") is not True:
        raise BridgeUnavailableError("epidemic treatment private query returned RED or timed out")
    envelope = frame.get("result")
    if not isinstance(envelope, dict) or set(envelope) != {
        "step", "accepted", "status", "query_sequence", "observation_revision",
        "snapshot_revision", "player_epidemic_treatment_presence", "private_build",
        "read_only", "advertised", "backend_id",
    } or envelope.get("step") != STEP or envelope.get("accepted") is not True or envelope.get("snapshot_revision") != native_revision or envelope.get("private_build") is not True or envelope.get("read_only") is not True or envelope.get("advertised") is not False or envelope.get("backend_id") != "native-headless" or isinstance(envelope.get("query_sequence"), bool) or not isinstance(envelope.get("query_sequence"), int) or envelope["query_sequence"] <= 0 or isinstance(envelope.get("observation_revision"), bool) or not isinstance(envelope.get("observation_revision"), int) or envelope["observation_revision"] <= 0:
        raise BridgeUnavailableError("epidemic treatment private envelope is malformed")
    value = envelope.get("player_epidemic_treatment_presence")
    if not isinstance(value, dict) or set(value) != {
        "schema", "schema_version", "modifier_key", "snapshot_revision",
        "date_raw", "played_character_id", "status", "present",
        "remaining_days", "unavailable_reason",
    } or value.get("schema") != "player-epidemic-treatment-presence-v1" or value.get("schema_version") != 1 or value.get("modifier_key") != KEY or value.get("snapshot_revision") != native_revision or value.get("date_raw") != date_raw or value.get("played_character_id") != played["character_id"] or envelope.get("status") != value.get("status"):
        raise BridgeUnavailableError("epidemic treatment private payload is malformed")
    duration = value.get("remaining_days")
    if duration != {"status": "unavailable", "value": None, "unavailable_reason": "duration_abi_not_verified"}:
        raise BridgeUnavailableError("epidemic treatment duration contract changed")
    if value["status"] == "available":
        if not isinstance(value["present"], bool) or value["unavailable_reason"] is not None:
            raise BridgeUnavailableError("epidemic treatment presence is malformed")
    elif value["status"] == "unavailable":
        if value["present"] is not None or not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
            raise BridgeUnavailableError("epidemic treatment unavailability is malformed")
    else:
        raise BridgeUnavailableError("epidemic treatment status is malformed")
    if _binding(driver.take_snapshot()) != _binding(before):
        raise BridgeUnavailableError("epidemic treatment query crossed its paused frame")
    return {**envelope, "queried_snapshot_id": before.get("snapshot_id"),
            "queried_revision": before.get("revision"),
            "queried_native_revision": native_revision}
