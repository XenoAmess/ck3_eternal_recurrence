"""Default-off read of one paused exact-build activity planner diagnostic."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-activity-planner-diag-v1-private"
SCHEMA = "activity-planner-diag-private-read-v1"


def _valid_payload(value: object, *, revision: int, date_raw: int,
                   actor_id: int) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "planner_status", "planner_present", "widget_attached",
        "widget_visible", "planning_stage", "host_view_activity_key_source",
        "host_view_activity_key", "configured_cost_state",
        "final_can_start_state", "raw_pointer_fields_persisted",
    }:
        return False
    if (value["schema"] != SCHEMA or value["snapshot_revision"] != revision
            or value["date_raw"] != date_raw
            or value["actor_character_id"] != actor_id
            or value["planner_status"] not in {"observed", "planner_absent"}
            or type(value["planner_present"]) is not bool
            or type(value["widget_attached"]) is not bool
            or type(value["widget_visible"]) is not bool
            or value["host_view_activity_key_source"] != "host_view_current_type"
            or value["configured_cost_state"] != "unknown"
            or value["final_can_start_state"] != "unknown"
            or value["raw_pointer_fields_persisted"] is not False):
        return False
    key = value["host_view_activity_key"]
    if key is not None and (not isinstance(key, str) or not key
                            or len(key) > 95
                            or any(not (character.isascii() and (
                                character.islower() or character.isdigit()
                                or character == "_")) for character in key)):
        return False
    if value["planner_status"] == "planner_absent":
        return (value["planner_present"] is False
                and value["widget_attached"] is False
                and value["widget_visible"] is False
                and value["planning_stage"] is None and key is None)
    return (value["planner_present"] is True
            and type(value["planning_stage"]) is int
            and 0 <= value["planning_stage"] <= 5
            and (value["widget_attached"] or not value["widget_visible"]))


def query_activity_planner_diag_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_planner_diag_query", False) is not True:
        raise UnsupportedStepError("private activity planner diagnostic is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    provenance = private_native_provenance(before)
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision
            or before.get("paused") is not True
            or before.get("map_ready") is not True
            or not isinstance(actor, Mapping)
            or actor.get("alive") is not True
            or type(actor.get("character_id")) is not int
            or actor["character_id"] <= 0
            or type(native_revision) is not int or native_revision <= 0
            or type(before.get("date_raw")) is not int):
        raise BridgeUnavailableError(
            "private activity planner read requires a living paused actor")
    request_id = "activity-planner-read-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private activity planner command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "private activity planner native RED: " + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict) or set(envelope) != {
        "step", "accepted", "status", "private_build", "read_only",
        "advertised", "activity_planner_diag", "backend_id",
    } or envelope.get("step") != STEP or envelope.get("accepted") is not True
            or envelope.get("status") != "available"
            or envelope.get("private_build") is not True
            or envelope.get("read_only") is not True
            or envelope.get("advertised") is not False
            or envelope.get("backend_id") != "native-headless"
            or not _valid_payload(envelope.get("activity_planner_diag"),
                                  revision=native_revision,
                                  date_raw=before["date_raw"],
                                  actor_id=actor["character_id"])):
        raise BridgeUnavailableError("private activity planner native payload malformed")
    after = driver.take_snapshot()
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"]
            or after.get("played_character") != actor):
        raise BridgeUnavailableError(
            "private activity planner read crossed the paused actor/date frame")
    return {
        **envelope["activity_planner_diag"],
        **provenance,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "post_snapshot_id": after.get("snapshot_id"),
    }
