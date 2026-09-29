"""Default-off, same-frame private feast guest-category query and action."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import cast

from .activity_feast_stage5_start_private_transport import _same_frame, _source_snapshot
from .driver import BridgeUnavailableError, UnsupportedStepError


QUERY_STEP = "query-activity-feast-guest-rule-v1"
ACTIVATE_STEP = "activate-activity-feast-guest-rule-v1"
SCHEMA = "activity-feast-guest-rule-private-v1"
_UNAVAILABLE = frozenset({
    "exact_build_rejected", "frame_changed", "planner_unavailable",
    "window_unbound", "rule_unavailable", "ambiguous_rule",
    "native_read_failed", "native_action_failed", "postcondition_failed",
})
_COUNT_KEYS = ("ordered_rule_count", "active_rule_count",
               "filtered_group_count", "filtered_character_count")


def _positive(value: object, maximum: int = 2**64 - 1) -> bool:
    return type(value) is int and 0 < value <= maximum


def _key(value: object) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= 96
            and value.startswith("activity_invite_rule_")
            and all(ch.isascii() and (ch.isalnum() or ch == "_") for ch in value))


def _parse(payload: object, *, step: str, envelope_status: str,
           native_revision: int, date_raw: int, actor_id: int) -> dict[str, object]:
    if (not isinstance(payload, dict)
            or set(payload) != {
                "schema", "snapshot_revision", "date_raw", "actor_character_id",
                "activity_key", "planning_stage", "status", "invoked", "active",
                "native_key_hash", *_COUNT_KEYS,
            }
            or payload["schema"] != SCHEMA
            or payload["snapshot_revision"] != native_revision
            or type(payload["snapshot_revision"]) is not int
            or payload["date_raw"] != date_raw
            or type(payload["date_raw"]) is not int
            or payload["actor_character_id"] != actor_id
            or type(payload["actor_character_id"]) is not int
            or payload["activity_key"] != "activity_feast"
            or payload["planning_stage"] != 5
            or type(payload["planning_stage"]) is not int
            or type(payload["invoked"]) is not bool):
        raise BridgeUnavailableError("private feast guest rule payload malformed")
    status = payload["status"]
    expected = {
        (QUERY_STEP, "observed_inactive"): "available",
        (QUERY_STEP, "observed_active"): "available",
        (ACTIVATE_STEP, "observed_active"): "already_active",
        (ACTIVATE_STEP, "activated"): "activated",
    }.get((step, status))
    if status in _UNAVAILABLE:
        expected = "unavailable"
    if expected is None or envelope_status != expected:
        raise BridgeUnavailableError("private feast guest rule status malformed")
    observed = status in {"observed_inactive", "observed_active", "activated"}
    if observed:
        if (type(payload["active"]) is not bool
                or type(payload["native_key_hash"]) is not int
                or not 0 <= payload["native_key_hash"] <= 2**64 - 1
                or any(type(payload[key]) is not int or payload[key] < 0
                       for key in _COUNT_KEYS)):
            raise BridgeUnavailableError("private feast guest rule observed counts malformed")
    elif (payload["active"] is not None or payload["native_key_hash"] is not None
          or any(payload[key] is not None for key in _COUNT_KEYS)):
        raise BridgeUnavailableError("private feast guest rule unavailable must remain unknown")
    if status == "activated":
        if payload["invoked"] is not True or payload["active"] is not True:
            raise BridgeUnavailableError("private feast guest rule activation lacks poststate")
    elif status == "observed_active":
        if payload["invoked"] is not False or payload["active"] is not True:
            raise BridgeUnavailableError("private feast guest rule active read malformed")
    elif status == "observed_inactive":
        if payload["invoked"] is not False or payload["active"] is not False:
            raise BridgeUnavailableError("private feast guest rule inactive read malformed")
    elif step == QUERY_STEP and payload["invoked"] is not False:
        raise BridgeUnavailableError("private feast guest rule read unexpectedly invoked")
    return dict(payload)


def _execute(driver: object, *, step: str, authored_rule_key: str,
             expected_revision: int, timeout_seconds: float,
             policy_approved: bool = False) -> dict[str, object]:
    flag = ("allow_private_activity_feast_guest_rule_query" if step == QUERY_STEP
            else "allow_private_activity_feast_guest_rule_action")
    if getattr(driver, flag, False) is not True:
        raise UnsupportedStepError("private feast guest rule route is disabled")
    if not _key(authored_rule_key):
        raise ValueError("authored_rule_key must be a bounded feast invitation rule")
    if not _positive(expected_revision) or type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("private feast guest rule frame or timeout invalid")
    if step == ACTIVATE_STEP and policy_approved is not True:
        raise ValueError("private feast guest rule action needs approved policy")
    before = _source_snapshot(driver)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast guest rule revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    request_id = "activity-feast-guest-rule-" + uuid.uuid4().hex
    request: dict[str, object] = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "expected_planning_stage": 5,
        "expected_activity_key": "activity_feast",
        "authored_rule_key": authored_rule_key,
    }
    if step == ACTIVATE_STEP:
        request["policy_approved"] = True
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast guest rule result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast guest rule native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_guest_rule", "backend_id",
            }
            or envelope["step"] != step or envelope["accepted"] is not True
            or envelope["status"] not in {
                "available", "activated", "already_active", "unavailable"}
            or envelope["private_build"] is not True
            or envelope["read_only"] is not (step == QUERY_STEP)
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast guest rule envelope malformed")
    payload = _parse(envelope["activity_feast_guest_rule"], step=step,
                     envelope_status=envelope["status"],
                     native_revision=cast(int, before["native_revision"]),
                     date_raw=cast(int, before["date_raw"]), actor_id=actor_id)
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast guest rule crossed paused frame")
    return {**payload, "authored_rule_key": authored_rule_key,
            "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}


def query_activity_feast_guest_rule_private_v1(
    driver: object, *, authored_rule_key: str, expected_revision: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    return _execute(driver, step=QUERY_STEP, authored_rule_key=authored_rule_key,
                    expected_revision=expected_revision, timeout_seconds=timeout_seconds)


def activate_activity_feast_guest_rule_private_v1(
    driver: object, *, authored_rule_key: str, expected_revision: int,
    policy_approved: bool, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    return _execute(driver, step=ACTIVATE_STEP, authored_rule_key=authored_rule_key,
                    expected_revision=expected_revision, timeout_seconds=timeout_seconds,
                    policy_approved=policy_approved)
