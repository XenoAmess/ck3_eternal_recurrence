"""Default-off, same-frame read of the native feast guest route proof.

Selected rows and the pre-invitation candidate are different native sources.
Neither source qualifies the guest route or authorizes an activity action.
"""

from __future__ import annotations

import re
import uuid
from typing import cast

from .activity_feast_stage5_start_private_transport import _same_frame, _source_snapshot
from .driver import BridgeUnavailableError, UnsupportedStepError


STEP = "query-activity-feast-stage5-guest-route-proof-v1-private"
SCHEMA = "activity-feast-stage5-guest-route-proof-private-v1"
_FINGERPRINT = re.compile(r"0x[0-9a-f]{16}\Z")
_KEYS = {
    "schema", "snapshot_revision", "date_raw", "actor_character_id",
    "activity_key", "planning_stage", "status", "candidate_status",
    "selected_status", "start_gate_status", "normal_refresh_sequence",
    "source_fingerprint", "active_rule_count", "filtered_group_count",
    "selected_row_count", "selected_nonhost_count", "selected_nonhost_rows",
    "positive_join_count", "timely_positive_join_count", "final_can_start",
    "pre_invitation_candidate", "candidate_selected_membership",
    "authored_rule_membership", "native_guest_route_qualified", "read_only",
    "advertised",
}
_COUNTS = (
    "active_rule_count", "filtered_group_count", "selected_row_count",
    "selected_nonhost_count", "positive_join_count", "timely_positive_join_count",
)
_CANDIDATE_STATUSES = {
    "observed", "no_qualified_candidate", "exact_build_rejected",
    "frame_changed", "planner_unavailable", "no_normal_refresh",
    "candidate_source_unavailable", "native_evaluation_failed",
    "arrival_unavailable", "configuration_changed",
}
_SELECTED_STATUSES = {
    "observed", "exact_build_rejected", "frame_changed", "planner_unavailable",
    "planner_diagnostic_unavailable", "planner_absent", "not_stage_five",
    "widget_detached", "widget_hidden", "host_view_type_mismatch",
    "no_normal_refresh", "configuration_changed", "guest_source_unavailable",
    "native_evaluation_failed", "cache_disagreed", "arrival_source_unavailable",
    "arrival_evaluation_failed",
}
_START_STATUSES = {
    "observed", "exact_build_rejected", "callback_missing", "planner_unavailable",
    "not_stage5", "selected_type_mismatch", "native_identity_mismatch",
    "native_evaluation_failed", "frame_changed",
}


def _uint(value: object, maximum: int = 2**64 - 1) -> bool:
    return type(value) is int and 0 <= value <= maximum


def _i32(value: object) -> bool:
    return type(value) is int and -(2**31) <= value < 2**31


def _i64(value: object) -> bool:
    return type(value) is int and -(2**63) <= value < 2**63


def parse_activity_feast_guest_route_proof_private_v1(
    payload: object, *, native_revision: int, date_raw: int, actor_id: int,
    envelope_status: str,
) -> dict[str, object]:
    if (not isinstance(payload, dict) or set(payload) != _KEYS
            or payload["schema"] != SCHEMA
            or payload["snapshot_revision"] != native_revision
            or type(payload["snapshot_revision"]) is not int
            or payload["date_raw"] != date_raw
            or type(payload["date_raw"]) is not int
            or payload["actor_character_id"] != actor_id
            or type(payload["actor_character_id"]) is not int
            or payload["activity_key"] != "activity_feast"
            or type(payload["planning_stage"]) is not int
            or payload["planning_stage"] != 5
            or payload["candidate_status"] not in _CANDIDATE_STATUSES
            or payload["selected_status"] not in _SELECTED_STATUSES
            or payload["start_gate_status"] not in _START_STATUSES
            or payload["native_guest_route_qualified"] is not False
            or payload["authored_rule_membership"] is not None
            or payload["read_only"] is not True
            or payload["advertised"] is not False):
        raise BridgeUnavailableError("private feast guest route proof malformed")
    if payload["status"] == "unavailable":
        if (envelope_status != "unavailable"
                or any(payload[key] is not None for key in (
                    "normal_refresh_sequence", "source_fingerprint", *_COUNTS,
                    "selected_nonhost_rows", "final_can_start",
                    "pre_invitation_candidate", "candidate_selected_membership"))):
            raise BridgeUnavailableError("private feast guest route unavailable data malformed")
        return dict(payload)
    if payload["status"] != "observed" or envelope_status != "available":
        raise BridgeUnavailableError("private feast guest route status malformed")
    if (payload["candidate_status"] not in {"observed", "no_qualified_candidate"}
            or payload["selected_status"] != "observed"
            or payload["start_gate_status"] != "observed"
            or not _uint(payload["normal_refresh_sequence"])
            or payload["normal_refresh_sequence"] == 0
            or not isinstance(payload["source_fingerprint"], str)
            or _FINGERPRINT.fullmatch(payload["source_fingerprint"]) is None
            or any(not _uint(payload[key], 4096) for key in _COUNTS)
            or not isinstance(payload["selected_nonhost_rows"], list)
            or len(payload["selected_nonhost_rows"]) != payload["selected_nonhost_count"]
            or payload["selected_nonhost_count"] > 128
            or payload["timely_positive_join_count"] > payload["positive_join_count"]
            or payload["positive_join_count"] > payload["selected_nonhost_count"]
            or type(payload["final_can_start"]) is not bool):
        raise BridgeUnavailableError("private feast guest route observed data malformed")
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    for row in payload["selected_nonhost_rows"]:
        if (not isinstance(row, dict) or set(row) != {
                "character_id", "planner_join_raw", "positive_join",
                "predicted_arrival_raw", "travel_days", "late"}
                or not _uint(row["character_id"], 0xFFFFFFFF)
                or row["character_id"] == 0 or row["character_id"] in seen
                or not _i64(row["planner_join_raw"])
                or type(row["positive_join"]) is not bool
                or row["positive_join"] != (row["planner_join_raw"] > 0)
                or not _i32(row["predicted_arrival_raw"])
                or not _i32(row["travel_days"])
                or type(row["late"]) is not bool):
            raise BridgeUnavailableError("private feast guest route selected row malformed")
        seen.add(row["character_id"])
        rows.append(dict(row))
    if sum(row["positive_join"] for row in rows) != payload["positive_join_count"]:
        raise BridgeUnavailableError("private feast guest route positive count malformed")
    candidate = payload["pre_invitation_candidate"]
    if payload["candidate_status"] == "observed":
        if (not isinstance(candidate, dict) or set(candidate) != {
                "character_id", "planner_join_raw", "travel_days",
                "arrival_raw", "planned_start_raw"}
                or not _uint(candidate["character_id"], 0xFFFFFFFF)
                or candidate["character_id"] == 0
                or not _i64(candidate["planner_join_raw"])
                or candidate["planner_join_raw"] <= 0
                or not _i32(candidate["travel_days"])
                or not _i32(candidate["arrival_raw"])
                or not _i32(candidate["planned_start_raw"])
                or payload["candidate_selected_membership"] is not False
                or candidate["character_id"] in seen):
            raise BridgeUnavailableError("private feast guest route candidate malformed")
    elif candidate is not None or payload["candidate_selected_membership"] is not None:
        raise BridgeUnavailableError("private feast guest route empty candidate malformed")
    return {**payload, "selected_nonhost_rows": rows,
            "pre_invitation_candidate": dict(candidate) if candidate else None}


def query_activity_feast_guest_route_proof_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_guest_route_proof_query", False) is not True:
        raise UnsupportedStepError("private feast guest route proof query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast guest route proof revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    request_id = "activity-feast-guest-route-proof-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "expected_planning_stage": 5,
        "expected_activity_key": "activity_feast",
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast guest route proof result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast guest route proof native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_guest_route_proof", "backend_id"}
            or envelope["step"] != STEP
            or envelope["accepted"] is not True
            or envelope["status"] not in {"available", "unavailable"}
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast guest route proof envelope malformed")
    payload = parse_activity_feast_guest_route_proof_private_v1(
        envelope["activity_feast_guest_route_proof"],
        native_revision=cast(int, before["native_revision"]),
        date_raw=cast(int, before["date_raw"]), actor_id=actor_id,
        envelope_status=envelope["status"],
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast guest route proof crossed paused frame")
    return {**payload, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}
