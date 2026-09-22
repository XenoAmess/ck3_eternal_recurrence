"""Unadvertised exact-build CE1 recovered-county list and modifier readback."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import _binding


STEP = "query-player-epidemic-recovery-v1"
TITLE_STEP_PREFIX = STEP + "-title-"
LIST_KEY = "formerly_infected_counties"
DURATION = {"status": "unavailable", "value": None,
            "unavailable_reason": "duration_abi_not_verified"}


def query_player_epidemic_recovery_private_v1(
    driver: object, *, expected_revision: int, requested_title_id: int = 0,
    expected_event_instance_id: int | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_epidemic_recovery_query", False) is not True:
        raise UnsupportedStepError("private epidemic recovery query is disabled")
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision <= 0:
        raise ValueError("expected_revision must be a positive integer")
    if isinstance(requested_title_id, bool) or not isinstance(requested_title_id, int) or not 0 <= requested_title_id <= 2**31 - 1:
        raise ValueError("requested_title_id must be zero or a full positive LandedTitleID")
    if requested_title_id == 0 and (isinstance(expected_event_instance_id, bool) or not isinstance(expected_event_instance_id, int) or expected_event_instance_id <= 0):
        raise ValueError("list mode requires a positive expected event instance")
    if requested_title_id > 0 and expected_event_instance_id is not None:
        raise ValueError("explicit title mode must use the frozen pre-action title ID")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    played = before.get("played_character")
    event = before.get("active_event")
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
        or (requested_title_id == 0 and (
            not isinstance(event, Mapping)
            or event.get("instance_id") != expected_event_instance_id
        ))
    ):
        raise BridgeUnavailableError("epidemic recovery query requires one living played character on a paused map frame")
    step = STEP if requested_title_id == 0 else TITLE_STEP_PREFIX + str(requested_title_id)
    request_id = "epidemic-recovery-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if not isinstance(frame, dict) or frame.get("type") != "command_result" or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id or frame.get("ok") is not True:
        raise BridgeUnavailableError("epidemic recovery private query returned RED or timed out")
    envelope = frame.get("result")
    if not isinstance(envelope, dict) or set(envelope) != {
        "step", "accepted", "status", "query_sequence", "observation_revision",
        "snapshot_revision", "player_epidemic_recovery", "private_build",
        "read_only", "advertised", "backend_id",
    } or envelope.get("step") != step or envelope.get("accepted") is not True or envelope.get("snapshot_revision") != native_revision or envelope.get("private_build") is not True or envelope.get("read_only") is not True or envelope.get("advertised") is not False or envelope.get("backend_id") != "native-headless" or isinstance(envelope.get("query_sequence"), bool) or not isinstance(envelope.get("query_sequence"), int) or envelope["query_sequence"] <= 0 or isinstance(envelope.get("observation_revision"), bool) or not isinstance(envelope.get("observation_revision"), int) or envelope["observation_revision"] <= 0:
        raise BridgeUnavailableError("epidemic recovery private envelope is malformed")
    value = envelope.get("player_epidemic_recovery")
    if not isinstance(value, dict) or set(value) != {
        "schema", "schema_version", "snapshot_revision", "date_raw",
        "played_character_id", "list_key", "requested_title_id", "status",
        "counties", "remaining_days", "unavailable_reason",
    } or value.get("schema") != "player-epidemic-recovery-v1" or value.get("schema_version") != 1 or value.get("snapshot_revision") != native_revision or value.get("date_raw") != date_raw or value.get("played_character_id") != played["character_id"] or value.get("list_key") != LIST_KEY or value.get("requested_title_id") != requested_title_id or envelope.get("status") != value.get("status") or value.get("remaining_days") != DURATION:
        raise BridgeUnavailableError("epidemic recovery private payload is malformed")
    if value["status"] == "available":
        counties = value["counties"]
        if not isinstance(counties, list) or value["unavailable_reason"] is not None or (requested_title_id > 0 and len(counties) != 1):
            raise BridgeUnavailableError("epidemic recovery counties are malformed")
        seen: set[int] = set()
        for county in counties:
            if not isinstance(county, dict) or set(county) != {"landed_title_id", "minor_present", "tiny_present"} or isinstance(county.get("landed_title_id"), bool) or not isinstance(county.get("landed_title_id"), int) or county["landed_title_id"] <= 0 or county["landed_title_id"] in seen or not isinstance(county.get("minor_present"), bool) or not isinstance(county.get("tiny_present"), bool):
                raise BridgeUnavailableError("epidemic recovery county row is malformed")
            seen.add(county["landed_title_id"])
        if requested_title_id > 0 and counties[0]["landed_title_id"] != requested_title_id:
            raise BridgeUnavailableError("epidemic recovery title identity drifted")
    elif value["status"] == "unavailable":
        if value["counties"] is not None or not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
            raise BridgeUnavailableError("epidemic recovery unavailability is malformed")
    else:
        raise BridgeUnavailableError("epidemic recovery status is malformed")
    if _binding(driver.take_snapshot()) != _binding(before):
        raise BridgeUnavailableError("epidemic recovery query crossed its paused frame")
    return {**envelope, "queried_snapshot_id": before.get("snapshot_id"),
            "queried_revision": before.get("revision"),
            "queried_native_revision": native_revision,
            "queried_event_instance_id": expected_event_instance_id}
