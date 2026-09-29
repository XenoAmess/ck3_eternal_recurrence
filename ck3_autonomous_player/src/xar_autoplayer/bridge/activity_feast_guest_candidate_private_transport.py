"""Default-off, paused native read of one filtered feast guest candidate.

The native filter precedes invitation.  Its candidate is not final invite
legality, acceptance, attendance, or permission to Start the feast.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from typing import cast

from .activity_feast_stage5_start_private_transport import (
    _same_frame, _source_snapshot,
)
from .driver import BridgeUnavailableError, UnsupportedStepError


STEP = "query-activity-feast-guest-candidate-v1"
SCHEMA = "activity-feast-guest-candidate-private-read-v1"
_FINGERPRINT = re.compile(r"0x[0-9a-f]{16}\Z")
_UNAVAILABLE = frozenset({
    "exact_build_rejected", "frame_changed", "planner_unavailable",
    "no_normal_refresh", "candidate_source_unavailable",
    "native_evaluation_failed", "arrival_unavailable",
    "configuration_changed",
})


def _i32(value: object) -> bool:
    return type(value) is int and -(2**31) <= value < 2**31


def _i64(value: object) -> bool:
    return type(value) is int and -(2**63) <= value < 2**63


def parse_activity_feast_guest_candidate_private_v1(
    payload: object, *, native_revision: int, date_raw: int, actor_id: int,
    envelope_status: str,
) -> dict[str, object]:
    """Keep a complete native empty set distinct from an unavailable read."""
    if (not isinstance(payload, dict)
            or set(payload) != {
                "schema", "snapshot_revision", "date_raw", "actor_character_id",
                "activity_key", "planning_stage", "status",
                "normal_refresh_sequence", "source_fingerprint",
                "native_filtered_pre_invitation", "candidate",
                "read_only", "raw_pointer_fields_persisted",
            }
            or payload["schema"] != SCHEMA
            or type(payload["snapshot_revision"]) is not int
            or payload["snapshot_revision"] != native_revision
            or type(payload["date_raw"]) is not int
            or payload["date_raw"] != date_raw
            or type(payload["actor_character_id"]) is not int
            or payload["actor_character_id"] != actor_id
            or payload["activity_key"] != "activity_feast"
            or type(payload["planning_stage"]) is not int
            or payload["planning_stage"] != 5
            or payload["read_only"] is not True
            or payload["raw_pointer_fields_persisted"] is not False
            or not isinstance(payload["status"], str)):
        raise BridgeUnavailableError("private feast guest candidate payload malformed")
    status = payload["status"]
    if status in {"observed", "no_qualified_candidate"}:
        if (envelope_status != "available"
                or type(payload["normal_refresh_sequence"]) is not int
                or payload["normal_refresh_sequence"] <= 0
                or not isinstance(payload["source_fingerprint"], str)
                or _FINGERPRINT.fullmatch(payload["source_fingerprint"]) is None):
            raise BridgeUnavailableError("private feast guest candidate source malformed")
        if status == "observed":
            candidate = payload["candidate"]
            if (payload["native_filtered_pre_invitation"] is not True
                    or not isinstance(candidate, dict)
                    or set(candidate) != {
                        "character_id", "planner_join_raw", "travel_days",
                        "arrival_raw", "planned_start_raw",
                    }
                    or type(candidate["character_id"]) is not int
                    or not 0 < candidate["character_id"] <= 0xFFFFFFFF
                    or not _i64(candidate["planner_join_raw"])
                    or candidate["planner_join_raw"] <= 0
                    or not _i32(candidate["travel_days"])
                    or not _i32(candidate["arrival_raw"])
                    or not _i32(candidate["planned_start_raw"])
                    or candidate["arrival_raw"] > candidate["planned_start_raw"]):
                raise BridgeUnavailableError("private feast guest candidate row malformed")
            return {**payload, "candidate": dict(candidate)}
        if (payload["native_filtered_pre_invitation"] is not False
                or payload["candidate"] is not None):
            raise BridgeUnavailableError("private feast guest empty result malformed")
    elif status in _UNAVAILABLE:
        if (envelope_status != "unavailable"
                or payload["normal_refresh_sequence"] is not None
                or payload["source_fingerprint"] is not None
                or payload["native_filtered_pre_invitation"] is not None
                or payload["candidate"] is not None):
            raise BridgeUnavailableError("private feast guest unavailable result malformed")
    else:
        raise BridgeUnavailableError("private feast guest candidate status unknown")
    return dict(payload)


def query_activity_feast_guest_candidate_private_v1(
    driver: object, *, expected_revision: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_guest_candidate_query", False) is not True:
        raise UnsupportedStepError("private feast guest candidate query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast guest candidate revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    request_id = "activity-feast-guest-candidate-" + uuid.uuid4().hex
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
        raise BridgeUnavailableError("private feast guest candidate result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast guest candidate native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_guest_candidate", "backend_id",
            }
            or envelope["step"] != STEP
            or envelope["accepted"] is not True
            or envelope["status"] not in {"available", "unavailable"}
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast guest candidate envelope malformed")
    payload = parse_activity_feast_guest_candidate_private_v1(
        envelope["activity_feast_guest_candidate"],
        native_revision=cast(int, before["native_revision"]),
        date_raw=cast(int, before["date_raw"]), actor_id=actor_id,
        envelope_status=envelope["status"],
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast guest candidate crossed paused frame")
    return {**payload, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}
