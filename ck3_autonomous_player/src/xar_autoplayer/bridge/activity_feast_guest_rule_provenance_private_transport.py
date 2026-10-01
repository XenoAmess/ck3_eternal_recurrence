"""Default-off paused read of one authored feast rule's candidate membership.

The native source is a passive capture of a natural Stage-5 refresh. Membership
does not submit a rule toggle, invite a guest, or authorize feast Start.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import cast

from .activity_feast_stage5_start_private_transport import _same_frame, _source_snapshot
from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-activity-feast-guest-rule-provenance-v1"
SCHEMA = "activity-feast-guest-rule-provenance-private-v1"
_UNAVAILABLE = frozenset({
    "exact_build_rejected", "no_normal_refresh", "frame_changed",
    "planner_unavailable", "rule_unavailable", "ambiguous_rule",
    "capture_overflow", "native_read_failed",
})


def _positive(value: object, maximum: int = 0xFFFFFFFF) -> bool:
    return type(value) is int and 0 < value <= maximum


def _rule_key(value: object) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= 96
            and value.startswith("activity_invite_rule_")
            and len(value) > len("activity_invite_rule_")
            and all(ch in "abcdefghijklmnopqrstuvwxyz0123456789_" for ch in value))


def parse_activity_feast_guest_rule_provenance_private_v1(
    payload: object, *, expected_revision: int, expected_date_raw: int,
    expected_actor_id: int, authored_rule_key: str, candidate_character_id: int,
    envelope_status: str,
) -> dict[str, object]:
    if (not isinstance(payload, dict)
            or set(payload) != {
                "schema", "snapshot_revision", "date_raw", "actor_character_id",
                "activity_key", "planning_stage", "authored_rule_key",
                "rule_status", "status", "candidate_character_id", "rule_active",
                "native_key_hash", "normal_refresh_sequence",
                "raw_rule_character_count", "filtered_rule_character_count",
                "candidate_membership", "filtered_rule_character_ids",
            }
            or payload["schema"] != SCHEMA
            or type(payload["snapshot_revision"]) is not int
            or payload["snapshot_revision"] != expected_revision
            or type(payload["date_raw"]) is not int
            or payload["date_raw"] != expected_date_raw
            or type(payload["actor_character_id"]) is not int
            or payload["actor_character_id"] != expected_actor_id
            or payload["activity_key"] != "activity_feast"
            or type(payload["planning_stage"]) is not int
            or payload["planning_stage"] != 5
            or payload["authored_rule_key"] != authored_rule_key
            or type(payload["candidate_character_id"]) is not int
            or payload["candidate_character_id"] != candidate_character_id):
        raise BridgeUnavailableError("private feast rule provenance payload malformed")
    status = payload["status"]
    if status == "observed":
        ids = payload["filtered_rule_character_ids"]
        if (envelope_status != "available"
                or payload["rule_status"] != "observed_active"
                or payload["rule_active"] is not True
                or type(payload["native_key_hash"]) is not int
                or not 0 <= payload["native_key_hash"] <= 0xFFFFFFFF
                or not _positive(payload["normal_refresh_sequence"], 2**64 - 1)
                or type(payload["raw_rule_character_count"]) is not int
                or type(payload["filtered_rule_character_count"]) is not int
                or not 0 <= payload["filtered_rule_character_count"] <= payload["raw_rule_character_count"] <= 4096
                or not isinstance(ids, list)
                or len(ids) != payload["filtered_rule_character_count"]
                or any(not _positive(item) for item in ids)
                or type(payload["candidate_membership"]) is not bool
                or payload["candidate_membership"] is not (candidate_character_id in ids)):
            raise BridgeUnavailableError("private feast rule provenance observed data malformed")
        return {**payload, "filtered_rule_character_ids": list(ids)}
    if status not in _UNAVAILABLE or envelope_status != "unavailable":
        raise BridgeUnavailableError("private feast rule provenance status malformed")
    if (payload["rule_status"] not in {
            "observed_active", "observed_inactive", "exact_build_rejected",
            "frame_changed", "planner_unavailable", "window_unbound",
            "rule_unavailable", "ambiguous_rule", "native_read_failed",
            "native_action_failed", "postcondition_failed"}
            or (payload["rule_active"] is not True
                and payload["rule_active"] is not False
                and payload["rule_active"] is not None)
            or any(payload[key] is not None for key in (
                "native_key_hash", "normal_refresh_sequence",
                "raw_rule_character_count", "filtered_rule_character_count",
                "candidate_membership", "filtered_rule_character_ids"))):
        raise BridgeUnavailableError("private feast rule provenance unavailable data malformed")
    return dict(payload)


def query_activity_feast_guest_rule_provenance_private_v1(
    driver: object, *, expected_revision: int, authored_rule_key: str,
    candidate_character_id: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_guest_rule_provenance_query", False) is not True:
        raise UnsupportedStepError("private feast rule provenance query is disabled")
    if not _rule_key(authored_rule_key):
        raise ValueError("authored_rule_key must be a bounded feast invitation rule")
    if not _positive(candidate_character_id):
        raise ValueError("candidate_character_id must be a full positive CharacterID")
    if not _positive(expected_revision) or type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("private feast rule provenance frame or timeout invalid")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast rule provenance revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    request_id = "activity-feast-guest-rule-provenance-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "expected_planning_stage": 5,
        "expected_activity_key": "activity_feast",
        "authored_rule_key": authored_rule_key,
        "candidate_character_id": candidate_character_id,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast rule provenance result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast rule provenance native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_guest_rule_provenance", "backend_id",
            }
            or envelope["step"] != STEP or envelope["accepted"] is not True
            or envelope["status"] not in {"available", "unavailable"}
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast rule provenance envelope malformed")
    result = parse_activity_feast_guest_rule_provenance_private_v1(
        envelope["activity_feast_guest_rule_provenance"],
        expected_revision=cast(int, before["native_revision"]),
        expected_date_raw=cast(int, before["date_raw"]),
        expected_actor_id=actor_id, authored_rule_key=authored_rule_key,
        candidate_character_id=candidate_character_id,
        envelope_status=envelope["status"],
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast rule provenance crossed paused frame")
    return {**result, **provenance, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}
