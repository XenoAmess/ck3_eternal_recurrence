"""Default-off paused native reads for feast Start and its independent poststate."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import cast

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


INPUT_STEP = "query-activity-feast-stage5-start-inputs-v1-private"
POST_STEP = "query-activity-feast-hosted-post-v1-private"
START_STEP = "start-activity-feast-stage5-v1-private"
INPUT_SCHEMA = "activity-feast-stage5-start-inputs-private-v1"
POST_SCHEMA = "activity-feast-hosted-post-private-read-v1"
RESOURCE_KEYS = ("gold", "treasury", "piety", "barter_goods")
_MAX_I64 = 2**63 - 1
_MIN_I64 = -(2**63)


def _positive(value: object, maximum: int = 2**64 - 1) -> bool:
    return type(value) is int and 0 < value <= maximum


def _signed(value: object) -> bool:
    return type(value) is int and _MIN_I64 <= value <= _MAX_I64


def _source_snapshot(driver: object) -> dict[str, object]:
    snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (
        type(snapshot.get("revision")) is not int
        or not _positive(snapshot["revision"])
        or not _positive(snapshot.get("native_revision"))
        or type(snapshot.get("date_raw")) is not int
        or snapshot["date_raw"] < 0
        or snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(snapshot.get("snapshot_id"), str)
        or not snapshot["snapshot_id"]
        or not isinstance(actor, Mapping)
        or actor.get("alive") is not True
        or not _positive(actor.get("character_id"), 2**32 - 1)
    ):
        raise BridgeUnavailableError("private feast Start read needs a living paused actor")
    return snapshot


def _same_frame(before: Mapping[str, object], after: Mapping[str, object]) -> bool:
    return bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and after.get("paused") is True
        and after.get("map_ready") is True
        and after.get("played_character") == before.get("played_character")
    )


def _balances(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict) or set(value) != set(RESOURCE_KEYS):
        raise BridgeUnavailableError("private feast balances malformed")
    copied: dict[str, dict[str, object]] = {}
    for key in RESOURCE_KEYS:
        row = value[key]
        if (
            not isinstance(row, dict)
            or set(row) != {"available", "raw"}
            or type(row["available"]) is not bool
            or (row["available"] is True and not _signed(row["raw"]))
            or (row["available"] is False and row["raw"] is not None)
        ):
            raise BridgeUnavailableError("private feast balance row malformed")
        copied[key] = dict(row)
    return copied


def _hosted(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) > 64:
        raise BridgeUnavailableError("private feast hosted identities malformed")
    copied: list[dict[str, object]] = []
    seen: set[int] = set()
    identity_fields = {"activity_id", "host_character_id", "activity_type_key"}
    terminal_fields = {
        "terminal_flags_observed", "native_completed", "native_invalidated",
    }
    for row in value:
        if (
            not isinstance(row, dict)
            or set(row) not in (identity_fields, identity_fields | terminal_fields)
            or not _positive(row["activity_id"], 2**32 - 1)
            or not _positive(row["host_character_id"], 2**32 - 1)
            or not isinstance(row["activity_type_key"], str)
            or not row["activity_type_key"]
            or len(row["activity_type_key"]) > 63
            or row["activity_id"] in seen
        ):
            raise BridgeUnavailableError("private feast hosted identity malformed")
        if terminal_fields <= set(row) and (
            row["terminal_flags_observed"] is not True
            or type(row["native_completed"]) is not bool
            or type(row["native_invalidated"]) is not bool
        ):
            raise BridgeUnavailableError("private feast hosted terminal flags malformed")
        seen.add(row["activity_id"])
        copied.append(dict(row))
    return copied


def _parse_payload(
    value: object, *, step: str, native_revision: int,
    date_raw: int, actor_id: int,
) -> dict[str, object]:
    common = {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "balances", "hosted_activities", "read_only", "advertised",
    }
    input_fields = {
        "activity_key", "selected_option_key", "planning_stage", "scale",
        "normal_refresh_sequence", "final_can_start", "resources",
        "native_guest_route_qualified", "guest_join_status",
        "selected_nonhost_count", "positive_join_count",
        "timely_positive_join_count", "arrival_time_observed",
    }
    if (not isinstance(value, dict)
            or set(value) != common | (input_fields if step == INPUT_STEP else set())
            or value["schema"] != (INPUT_SCHEMA if step == INPUT_STEP else POST_SCHEMA)
            or type(value["snapshot_revision"]) is not int
            or value["snapshot_revision"] != native_revision
            or type(value["date_raw"]) is not int
            or value["date_raw"] != date_raw
            or type(value["actor_character_id"]) is not int
            or value["actor_character_id"] != actor_id
            or value["read_only"] is not True
            or value["advertised"] is not False):
        raise BridgeUnavailableError("private feast Start payload malformed")
    balances = _balances(value["balances"])
    hosted = _hosted(value["hosted_activities"])
    result = {**value, "balances": balances, "hosted_activities": hosted}
    if step == INPUT_STEP:
        resources = value["resources"]
        if not isinstance(resources, dict) or set(resources) != set(RESOURCE_KEYS):
            raise BridgeUnavailableError("private feast Start costs malformed")
        copied_resources: dict[str, dict[str, object]] = {}
        for key in RESOURCE_KEYS:
            row = resources[key]
            if (
                not isinstance(row, dict)
                or set(row) != {"resource_index", "configured_cost_raw"}
                or type(row["resource_index"]) is not int
                or not 0 <= row["resource_index"] < 10
                or not _signed(row["configured_cost_raw"])
            ):
                raise BridgeUnavailableError("private feast Start cost row malformed")
            copied_resources[key] = dict(row)
        if (
            value["activity_key"] != "activity_feast"
            or value["selected_option_key"] != "feast_type_generic"
            or type(value["planning_stage"]) is not int
            or value["planning_stage"] != 5
            or type(value["scale"]) is not int
            or value["scale"] != 100000
            or not _positive(value["normal_refresh_sequence"])
            or type(value["final_can_start"]) is not bool
            or type(value["native_guest_route_qualified"]) is not bool
            or not isinstance(value["guest_join_status"], str)
            or value["guest_join_status"] not in {
                "observed", "exact_build_rejected", "frame_changed",
                "planner_unavailable", "planner_diagnostic_unavailable",
                "planner_absent", "not_stage_five", "widget_detached",
                "widget_hidden", "host_view_type_mismatch",
                "no_normal_refresh",
                "configuration_changed", "guest_source_unavailable",
                "native_evaluation_failed", "cache_disagreed",
                "arrival_source_unavailable", "arrival_evaluation_failed",
            }
            or type(value["arrival_time_observed"]) is not bool
        ):
            raise BridgeUnavailableError("private feast Start inputs malformed")
        counts = [value[key] for key in (
            "selected_nonhost_count", "positive_join_count",
            "timely_positive_join_count",
        )]
        if value["guest_join_status"] == "observed":
            if (any(type(count) is not int or not 0 <= count <= 128
                    for count in counts)
                    or not counts[2] <= counts[1] <= counts[0]
                    or value["arrival_time_observed"] is not True):
                raise BridgeUnavailableError("private feast guest counts malformed")
        elif (any(count is not None for count in counts)
              or value["arrival_time_observed"] is not False):
            raise BridgeUnavailableError("private feast unavailable guest must remain unknown")
        result["resources"] = copied_resources
    return result


def _query(driver: object, *, step: str, expected_revision: int,
           timeout_seconds: float) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_stage5_start_query", False) is not True:
        raise UnsupportedStepError("private feast Start query is disabled")
    if not _positive(expected_revision):
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast Start query revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    request_id = "activity-feast-start-read-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
    }
    if step == INPUT_STEP:
        request.update({
            "expected_activity_key": "activity_feast",
            "expected_option_key": "feast_type_generic",
            "expected_planning_stage": 5,
        })
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast Start command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast Start native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    key = ("activity_feast_stage5_start_inputs" if step == INPUT_STEP
           else "activity_feast_hosted_post")
    if (not isinstance(envelope, dict) or set(envelope) != {
        "step", "accepted", "status", "private_build", "read_only",
        "advertised", key, "backend_id",
    } or envelope["step"] != step or envelope["accepted"] is not True
            or envelope["status"] != "available"
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast Start envelope malformed")
    payload = _parse_payload(
        envelope[key], step=step,
        native_revision=cast(int, before["native_revision"]),
        date_raw=cast(int, before["date_raw"]), actor_id=actor_id,
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast Start query crossed paused frame")
    return {
        **payload, **provenance, "queried_snapshot_id": before["snapshot_id"],
        "queried_revision": before["revision"],
        "queried_native_revision": before["native_revision"],
        "post_snapshot_id": after["snapshot_id"],
    }


def query_activity_feast_stage5_start_inputs_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    return _query(driver, step=INPUT_STEP, expected_revision=expected_revision,
                  timeout_seconds=timeout_seconds)


def query_activity_feast_hosted_post_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    return _query(driver, step=POST_STEP, expected_revision=expected_revision,
                  timeout_seconds=timeout_seconds)


def submit_activity_feast_stage5_start_private_v1(
    driver: object, *, inputs: Mapping[str, object],
    reserve_raw: Mapping[str, int], timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Submit once after a separately persisted intent; pending is not success."""
    if getattr(driver, "allow_private_activity_feast_stage5_start_action", False) is not True:
        raise UnsupportedStepError("private feast Start action is disabled")
    if (inputs.get("schema") != INPUT_SCHEMA
            or inputs.get("native_guest_route_qualified") is not True
            or inputs.get("final_can_start") is not True
            or not isinstance(reserve_raw, Mapping)
            or set(reserve_raw) != set(RESOURCE_KEYS)
            or any(type(reserve_raw[key]) is not int or not 0 <= reserve_raw[key] <= _MAX_I64
                   for key in RESOURCE_KEYS)):
        raise BridgeUnavailableError("private feast Start lacks qualified inputs")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    actor_id = cast(int, before["played_character"]["character_id"])
    if any((inputs.get(key) != expected) for key, expected in (
        ("queried_snapshot_id", before["snapshot_id"]),
        ("queried_revision", before["revision"]),
        ("snapshot_revision", before["native_revision"]),
        ("date_raw", before["date_raw"]),
        ("actor_character_id", actor_id),
    )):
        raise BridgeUnavailableError("private feast Start inputs crossed paused frame")
    request_id = "activity-feast-start-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": START_STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "expected_activity_key": "activity_feast",
        "expected_option_key": "feast_type_generic",
        "expected_planning_stage": 5,
        "policy_positive": True,
        "previous_submit_pending": False,
        **{f"reserve_{key}_raw": reserve_raw[key] for key in RESOURCE_KEYS},
    }
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast Start command_result unavailable")
    envelope = frame.get("result")
    if frame.get("ok") is not True:
        reason = (envelope.get("activity_feast_stage5_start", {}).get("failure")
                  if isinstance(envelope, dict) else frame.get("error"))
        raise BridgeUnavailableError("private feast Start native RED: " + str(reason))
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_stage5_start", "backend_id",
            }
            or envelope["step"] != START_STEP
            or envelope["accepted"] is not True
            or envelope["status"] != "pending"
            or envelope["private_build"] is not True
            or envelope["read_only"] is not False
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast Start pending envelope malformed")
    action = envelope["activity_feast_stage5_start"]
    if (not isinstance(action, dict)
            or action.get("schema") != "activity-feast-stage5-start-private-action-v1"
            or action.get("submitted") is not True
            or action.get("native_status") != "submitted_pending"
            or not isinstance(action.get("precondition"), dict)):
        raise BridgeUnavailableError("private feast Start ACK lacks native pending")
    # A changed snapshot is expected only after the native action.  The caller
    # performs an independent hosted/resource post read before any success.
    return {**provenance, "request_id": request_id, "native_status": "submitted_pending",
            "ack": dict(action), "source_snapshot_id": before["snapshot_id"]}
