"""Default-off same-frame native read for one requested feast guest ID.

Native filtered membership, join and arrival are pre-invitation observations.
They never authorize a feast Start.
"""

from __future__ import annotations

import re
import uuid
from typing import cast

from .activity_feast_stage5_start_private_transport import _same_frame, _source_snapshot
from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-activity-feast-stage5-guest-target-v1-private"
SCHEMA = "activity-feast-stage5-guest-target-private-v1"
_FINGERPRINT = re.compile(r"0x[0-9a-f]{16}\Z")
_KEYS = {
    "schema", "snapshot_revision", "date_raw", "actor_character_id",
    "activity_key", "planning_stage", "status", "target_status",
    "target_character_id", "selected_status", "start_gate_status",
    "normal_refresh_sequence", "source_fingerprint", "active_rule_count",
    "filtered_group_count", "selected_row_count", "native_filtered_member",
    "selected_member", "planner_join_raw", "travel_days", "arrival_raw",
    "planned_start_raw", "positive_join", "timely_arrival", "final_can_start",
    "authored_rule_membership", "native_guest_route_qualified", "read_only",
    "advertised",
}
_VALUES = (
    "normal_refresh_sequence", "source_fingerprint", "active_rule_count",
    "filtered_group_count", "selected_row_count", "native_filtered_member",
    "selected_member", "planner_join_raw", "travel_days", "arrival_raw",
    "planned_start_raw", "positive_join", "timely_arrival", "final_can_start",
)
_UNAVAILABLE = {
    "observed", "target_not_filtered",  # independent selected/CanStart binding can fail
    "exact_build_rejected", "frame_changed", "planner_unavailable",
    "no_normal_refresh", "candidate_source_unavailable",
    "native_evaluation_failed", "arrival_unavailable",
    "configuration_changed",
}


def _i32(value: object) -> bool:
    return type(value) is int and -(2**31) <= value < 2**31


def _i64(value: object) -> bool:
    return type(value) is int and -(2**63) <= value < 2**63


def parse_activity_feast_guest_target_private_v1(
    payload: object, *, native_revision: int, date_raw: int, actor_id: int,
    target_character_id: int, envelope_status: str,
) -> dict[str, object]:
    """Treat absent filtered member, poor join, and unavailable as distinct."""
    if (not isinstance(payload, dict) or set(payload) != _KEYS
            or payload["schema"] != SCHEMA
            or type(payload["snapshot_revision"]) is not int
            or payload["snapshot_revision"] != native_revision
            or type(payload["date_raw"]) is not int
            or payload["date_raw"] != date_raw
            or type(payload["actor_character_id"]) is not int
            or payload["actor_character_id"] != actor_id
            or type(payload["target_character_id"]) is not int
            or payload["target_character_id"] != target_character_id
            or payload["activity_key"] != "activity_feast"
            or type(payload["planning_stage"]) is not int
            or payload["planning_stage"] != 5
            or payload["authored_rule_membership"] is not None
            or payload["native_guest_route_qualified"] is not False
            or payload["read_only"] is not True
            or payload["advertised"] is not False):
        raise BridgeUnavailableError("private feast target payload malformed")
    if payload["status"] == "unavailable":
        if (envelope_status != "unavailable"
                or payload["target_status"] not in _UNAVAILABLE
                or any(payload[key] is not None for key in _VALUES)):
            raise BridgeUnavailableError("private feast target unavailable data malformed")
        return dict(payload)
    if (payload["status"] != "observed" or envelope_status != "available"
            or payload["target_status"] not in {"observed", "target_not_filtered"}
            or payload["selected_status"] != "observed"
            or payload["start_gate_status"] != "observed"
            or type(payload["normal_refresh_sequence"]) is not int
            or payload["normal_refresh_sequence"] <= 0
            or not isinstance(payload["source_fingerprint"], str)
            or _FINGERPRINT.fullmatch(payload["source_fingerprint"]) is None
            or any(type(payload[key]) is not int or not 0 <= payload[key] <= 4096
                   for key in ("active_rule_count", "filtered_group_count",
                               "selected_row_count"))
            or type(payload["selected_member"]) is not bool
            or type(payload["final_can_start"]) is not bool):
        raise BridgeUnavailableError("private feast target observed data malformed")
    if payload["target_status"] == "target_not_filtered":
        if (payload["native_filtered_member"] is not False
                or any(payload[key] is not None for key in (
                    "planner_join_raw", "travel_days", "arrival_raw",
                    "planned_start_raw", "positive_join", "timely_arrival"))):
            raise BridgeUnavailableError("private feast target absence malformed")
    elif (payload["native_filtered_member"] is not True
          or not _i64(payload["planner_join_raw"])
          or not _i32(payload["travel_days"])
          or not _i32(payload["arrival_raw"])
          or not _i32(payload["planned_start_raw"])
          or type(payload["positive_join"]) is not bool
          or payload["positive_join"] != (payload["planner_join_raw"] > 0)
          or type(payload["timely_arrival"]) is not bool
          or payload["timely_arrival"] != (
              payload["arrival_raw"] <= payload["planned_start_raw"])):
        raise BridgeUnavailableError("private feast target native value malformed")
    return dict(payload)


def query_activity_feast_guest_target_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_guest_target_query", False) is not True:
        raise UnsupportedStepError("private feast target query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if (type(target_character_id) is not int
            or not 0 < target_character_id <= 0x7FFFFFFF):
        raise ValueError("target_character_id must be a positive full int32 ID")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast target revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    if target_character_id == actor_id:
        raise ValueError("target guest cannot be the played host")
    request_id = "activity-feast-guest-target-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "expected_planning_stage": 5,
        "expected_activity_key": "activity_feast",
        "target_character_id": target_character_id,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast target result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast target native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_guest_target", "backend_id"}
            or envelope["step"] != STEP
            or envelope["accepted"] is not True
            or envelope["status"] not in {"available", "unavailable"}
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast target envelope malformed")
    result = parse_activity_feast_guest_target_private_v1(
        envelope["activity_feast_guest_target"],
        native_revision=cast(int, before["native_revision"]),
        date_raw=cast(int, before["date_raw"]), actor_id=actor_id,
        target_character_id=target_character_id,
        envelope_status=envelope["status"],
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast target crossed paused frame")
    return {**result, **provenance, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}
