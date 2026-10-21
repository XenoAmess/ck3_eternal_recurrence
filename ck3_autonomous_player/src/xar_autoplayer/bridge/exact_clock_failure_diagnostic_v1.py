"""Bounded projection of evidence already held by one failed exact-day call.

No I/O, Native query, state change, retry decision or success credit.
"""
from __future__ import annotations

import json
from .exact_clock_wait_progress_v1 import project_wait_progress_v1
from .cached_native_clock_summary_v1 import parse_cached_native_clock_summary_v1

SCHEMA = "xar.exact-day-clock-failure.v2"
MESSAGE = "exact-day native clock did not stop the map"
MAX_BYTES = 8192
_CACHED_MAX_BYTES = 16384
_FRAME = ("date_raw", "native_revision", "revision", "snapshot_id", "speed",
          "paused", "player_character_id", "episode_character_id", "episode_id",
          "alive", "map_ready", "monotonic_ms")
_STATUS = ("state", "generation", "starting_date_raw", "target_date_raw",
           "last_observed_date_raw", "trigger_date_raw", "speed", "mode",
           "army_count", "combat_count", "completed_daily_ticks",
           "intermediate_pause_count", "trigger_flags", "signed_date_delta_from_target_raw",
           "overshoot_days", "pause_wrapper_called", "pause_observed", "terminal_observed", "abnormal")
_ACK = ("step", "accepted", "status", "request_id", "native_request_id")
_DIAGNOSTIC = ("schema", "is_error", "credit", "never_replay", "original_error_type",
    "original_error", "starting_date_raw", "target_date_raw", "requested_speed",
    "normal_status_query_attempted", "stop_validation_attempted", "stopped_status",
    "stop_credit", "armed_reply", "starting_frame", "last_wait_frame",
    "cleanup_before_pause_frame", "before_cleanup_actions", "cleanup_actions", "truncated", "wait_progress")


def _map(value):
    return value if type(value) is dict else {}


def _scalar(value):
    if value is None or type(value) is bool:
        return value
    if type(value) is int and -(1 << 63) <= value < (1 << 64):
        return value
    if type(value) is str:
        return value[:192]
    return None


def _fields(value, keys):
    value = _map(value)
    return {key: _scalar(value.get(key)) for key in keys}


def _frame(value):
    if type(value) is not dict:
        return None
    result = _fields(value, _FRAME)
    diagnostics = _map(value.get("diagnostics"))
    result["connection"] = _fields(diagnostics, ("connection_generation", "bridge_pid"))
    heartbeat = _map(diagnostics.get("last_heartbeat"))
    result["cached_heartbeat"] = _fields(heartbeat, ("sequence", "monotonic_ms", "pid"))
    result["cached_owner"] = _fields(heartbeat.get("main_thread_query_mailbox_v1"),
        ("pump_epochs", "owner_verified_pump_epochs", "date_raw", "paused", "failure"))
    result["cached_observer"] = _fields(heartbeat.get("snapshot_observer_12002"),
        ("started_ms", "completed_ms", "read_in_progress", "last_read_available"))
    return result


def _actions(actions, start, end):
    # Index only this invocation. Never copy an outer horizon's prior actions.
    result = []
    for index in range(start, min(end, start + 4)):
        action = _map(actions[index])
        ack = _map(action.get("result"))
        ack_fields = _fields(ack, _ACK)
        ack_fields["accepted"] = ack.get("accepted") if type(ack.get("accepted")) is bool else None
        result.append({"step": _scalar(action.get("step")),
                       "error": _scalar(action.get("error")),
                       "result_observed": type(action.get("result")) is dict,
                       "ack": ack_fields})
    return {"rows": result, "omitted_count": max(0, end - start - len(result))}


def build_exact_clock_failure_v1(*, original_error, starting_date_raw, target_date_raw,
        speed, arm_status, starting, last_frame, cleanup_before_frame,
        actions, action_start, cleanup_start, wait_progress=None):
    """Only called for the local pre-status-query map-not-paused error.

    Arm fields describe the earlier Arm reply, never a later stop observation.
    Cleanup frame was acquired BEFORE cleanup pause/cancel. ACK fields are only
    copied from returned action results; a missing field remains null.
    """
    diagnostic = {
        "schema": SCHEMA, "is_error": True, "credit": 0, "never_replay": True,
        "original_error_type": type(original_error).__name__,
        "original_error": MESSAGE, "starting_date_raw": starting_date_raw,
        "target_date_raw": target_date_raw, "requested_speed": speed,
        "normal_status_query_attempted": False, "stop_validation_attempted": False,
        "stopped_status": None, "stop_credit": False,
        "armed_reply": None if arm_status is None else _fields(arm_status, _STATUS),
        "starting_frame": _frame(starting), "last_wait_frame": _frame(last_frame),
        "cleanup_before_pause_frame": _frame(cleanup_before_frame),
        "before_cleanup_actions": _actions(actions, action_start, cleanup_start),
        "cleanup_actions": _actions(actions, cleanup_start, len(actions)),
        "truncated": False, "wait_progress": project_wait_progress_v1(wait_progress),
    }
    # A fixed allowlist and small integer/string caps bound allocation. If the
    # optional frames/actions exceed 8KiB, retain the core failure and Arm only.
    if len(_encode(diagnostic)) > MAX_BYTES:
        for key in ("starting_frame", "last_wait_frame", "cleanup_before_pause_frame",
                    "before_cleanup_actions", "cleanup_actions"):
            diagnostic[key] = None
        diagnostic["truncated"] = True
    if len(_encode(diagnostic)) > MAX_BYTES:
        diagnostic["armed_reply"] = None
    return diagnostic


def _encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def exact_clock_failure_diagnostic_v1(error: object) -> dict[str, object] | None:
    """Validate and isolate this typed exception for the existing MCP error path."""
    from .driver import StepPostconditionError

    if (not isinstance(error, StepPostconditionError)
            or error.primitive_step != "life-advance-one-day"):
        return None
    value: object = getattr(error, "step_result", None)
    if (type(value) is not dict or set(value) not in (set(_DIAGNOSTIC), set(_DIAGNOSTIC) | {"cached_native_clock_summary_v1"})
            or value.get("schema") != SCHEMA
            or value.get("is_error") is not True or value.get("never_replay") is not True
            or type(value.get("credit")) is not int or value["credit"] != 0
            or value.get("stop_credit") is not False
            or value.get("normal_status_query_attempted") is not False
            or value.get("stop_validation_attempted") is not False
            or value.get("stopped_status") is not None
            or value.get("original_error") != MESSAGE or str(error) != MESSAGE):
        return None
    try:
        result: dict[str, object] = {key: value[key] for key in _DIAGNOSTIC}
        result["wait_progress"] = project_wait_progress_v1(value["wait_progress"])
        if len(_encode(result)) > MAX_BYTES:
            return None
        if "cached_native_clock_summary_v1" in value:
            cached_summary = parse_cached_native_clock_summary_v1(value["cached_native_clock_summary_v1"])
            if cached_summary is None:
                return None
            result["cached_native_clock_summary_v1"] = cached_summary
        encoded = _encode(result)
        limit = _CACHED_MAX_BYTES if "cached_native_clock_summary_v1" in result else MAX_BYTES
        if len(encoded) > limit:
            return None
        isolated: object = json.loads(encoded)
        if not isinstance(isolated, dict):
            return None
        projected: dict[str, object] = {}
        for key, item in isolated.items():
            if not isinstance(key, str):
                return None
            projected[key] = item
        return projected
    except (TypeError, ValueError, RecursionError):
        return None
