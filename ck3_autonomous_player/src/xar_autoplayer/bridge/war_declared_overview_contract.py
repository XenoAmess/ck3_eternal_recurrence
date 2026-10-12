"""Qualified fixed-window observations; UI closure is not a war acknowledgement."""

from __future__ import annotations

from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build

QUERY_STEP = "query-war-declared-overview-v1"
CLOSE_STEP = "close-war-declared-overview-v1"
QUERY_CAPABILITY = "game.command.query-war-declared-overview-v1"
CLOSE_CAPABILITY = "game.command.close-war-declared-overview-v1"
SCHEMA = "ck3-war-declared-overview-v1"
SOURCE_SCHEMA = "war-declared-overview-source-v1"
ATTEMPT_SCHEMA = "war-declared-overview-query-attempt-v1"
OWNER_RECEIPT_KEY = "war_declared_overview_owner_receipt"
_OWNER_RECEIPT_FIELDS = {
    "request_id", "ticket_sequence", "executor_started_sequence", "completed_sequence",
    "pump_epoch", "thread_id", "date_raw", "connection_generation",
}
_OBSERVATION_SOURCES = {"guarded_registered_top_level", "guarded_top_level_and_complete_owner_tree"}
LEASE_KEYS = {
    "queried_snapshot_id": "snapshot_id", "queried_revision": "revision",
    "queried_native_revision": "native_revision", "queried_date_raw": "date_raw",
    "queried_actor_character_id": "actor_character_id",
    "queried_connection_generation": "connection_generation", "queried_episode_run_id": "episode_run_id",
}
_BOOL_FIELDS = {
    "available", "accepted", "root_observed", "window_present", "effective_visible",
    "dispatch_attempted", "dispatch_invoked", "native_handled", "post_observed",
    "post_window_present", "post_effective_visible", "scope_unchanged", "closure_verified",
    "application_owner_thread_verified", "paused",
}
_FIELDS = _BOOL_FIELDS | {
    "schema", "operation", "window_name", "status", "unavailable_reason", "button_name",
    "played_character_id", "date_raw", "native_revision", "connection_generation",
    "pump_epoch", "thread_id", "game_version", "executable_sha256",
    "request_id", "ticket_sequence", "root_observation_source", "post_observation_source",
}


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"war overview {name} is outside its native integer range")
    return value


def normalize_war_declared_overview_owner_receipt_v1(value: object, *, request_id: str) -> dict[str, object]:
    if (type(request_id) is not str or not request_id or not isinstance(value, Mapping)
            or set(value) != _OWNER_RECEIPT_FIELDS or value["request_id"] != request_id):
        raise ValueError("war overview independent TOP owner receipt is malformed or stale")
    row = dict(value)
    for key in ("ticket_sequence", "executor_started_sequence", "completed_sequence", "pump_epoch", "connection_generation"):
        _integer(row[key], key, 1, (1 << 64) - 1)
    _integer(row["thread_id"], "thread_id", 1, (1 << 32) - 1)
    _integer(row["date_raw"], "date_raw", -(1 << 31), (1 << 31) - 1)
    if not row["ticket_sequence"] == row["executor_started_sequence"] == row["completed_sequence"]:
        raise ValueError("war overview owner ticket was not independently started and completed")
    return row


def normalize_war_declared_overview_v1(
    value: object, *, operation: str, binding: Mapping[str, object], native_generation: int,
    owner_receipt: Mapping[str, object],
) -> dict[str, object]:
    """Validate only the actual Native leaf, against independent before sources."""
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ValueError("war overview Native leaf shape is malformed")
    owner_receipt = normalize_war_declared_overview_owner_receipt_v1(
        owner_receipt, request_id=owner_receipt.get("request_id") if isinstance(owner_receipt, Mapping) else None,
    )
    row = dict(value)
    if (operation not in {"query", "close"} or row["operation"] != operation
            or row["schema"] != SCHEMA or row["window_name"] != "war_declared_overview"):
        raise ValueError("war overview fixed operation/window differs")
    if require_exact_native_build(row["game_version"], row["executable_sha256"]) != CK3_12004:
        raise ValueError("war overview observation belongs to another build")
    for key in _BOOL_FIELDS:
        if type(row[key]) is not bool:
            raise ValueError(f"war overview {key} must be an actual boolean")
    for key in ("status", "unavailable_reason", "button_name", "request_id", "root_observation_source", "post_observation_source"):
        if type(row[key]) is not str:
            raise ValueError(f"war overview {key} must be native text")
    if row["button_name"] not in {"", "dismiss", "button_close"}:
        raise ValueError("war overview close button is outside the fixed candidates")
    _integer(row["played_character_id"], "played_character_id", -(1 << 31), (1 << 31) - 1)
    _integer(row["date_raw"], "date_raw", -(1 << 31), (1 << 31) - 1)
    for key in ("native_revision", "connection_generation", "pump_epoch", "ticket_sequence"):
        _integer(row[key], key, 0, (1 << 64) - 1)
    _integer(row["thread_id"], "thread_id", 0, (1 << 32) - 1)
    if row["native_revision"] != binding["native_revision"] or row["connection_generation"] != native_generation:
        raise ValueError("war overview native revision/generation differs from its actual lease")
    for key in ("request_id", "ticket_sequence", "pump_epoch", "thread_id", "date_raw", "connection_generation"):
        if row[key] != owner_receipt[key]:
            raise ValueError("war overview leaf differs from its independently captured TOP owner receipt")
    for flag, source in (("root_observed", "root_observation_source"), ("post_observed", "post_observation_source")):
        if row[source] not in _OBSERVATION_SOURCES | {""} or row[flag] and row[source] not in _OBSERVATION_SOURCES:
            raise ValueError("war overview lookup lacks its actual qualified observation source")
    for flag, present, source in (("root_observed", "window_present", "root_observation_source"),
                                  ("post_observed", "post_window_present", "post_observation_source")):
        if row[flag] and not row[present] and row[source] != "guarded_top_level_and_complete_owner_tree":
            raise ValueError("war overview absence lacks the complete owner-tree negative observation")
    if row["root_observed"] or row["available"] or row["dispatch_attempted"]:
        if (row["played_character_id"] != binding["actor_character_id"]
                or row["date_raw"] != binding["date_raw"] or row["paused"] is not True):
            raise ValueError("war overview played actor/date/pause differs from its actual lease")
    if row["effective_visible"] and not row["window_present"]:
        raise ValueError("war overview visibility lacks a window")
    if row["post_effective_visible"] and not row["post_window_present"]:
        raise ValueError("war overview post visibility lacks a window")
    if row["native_handled"] and not row["dispatch_invoked"]:
        raise ValueError("war overview native handling lacks an invocation")
    if row["dispatch_invoked"] and not row["dispatch_attempted"]:
        raise ValueError("war overview invocation lacks an attempted dispatch")
    if row["dispatch_attempted"] and (
        operation != "close" or not row["root_observed"] or not row["application_owner_thread_verified"]
        or not row["window_present"] or not row["effective_visible"] or not row["button_name"]
    ):
        raise ValueError("war overview dispatch lacks the qualified visible fixed target")
    if row["available"]:
        if (not all(row[key] for key in ("root_observed", "post_observed", "scope_unchanged",
                                        "application_owner_thread_verified"))
                or not row["pump_epoch"] or not row["thread_id"] or row["unavailable_reason"]):
            raise ValueError("war overview availability lacks actual owner/post observation")
        if operation == "query":
            status = "absent" if not row["window_present"] else "visible" if row["effective_visible"] else "hidden"
            if (row["status"] != status or not row["accepted"] or row["dispatch_attempted"]
                    or row["dispatch_invoked"] or row["native_handled"] or row["closure_verified"]
                    or row["button_name"] or row["post_window_present"] != row["window_present"]
                    or row["post_effective_visible"] != row["effective_visible"]):
                raise ValueError("war overview query differs from its stable independent reads")
        elif row["status"] == "closed_verified":
            if (not all(row[key] for key in ("accepted", "closure_verified", "dispatch_attempted", "dispatch_invoked"))
                    or row["post_window_present"] and row["post_effective_visible"]):
                raise ValueError("war overview close is not post verified")
        else:
            status = "already_absent" if not row["window_present"] else "already_hidden"
            if (row["status"] != status or row["effective_visible"] or row["accepted"]
                    or row["closure_verified"] or row["dispatch_attempted"] or row["dispatch_invoked"]
                    or row["native_handled"] or row["button_name"]
                    or row["post_window_present"] != row["window_present"]
                    or row["post_effective_visible"] != row["effective_visible"]):
                raise ValueError("war overview no-op must retain its actual non-dispatch observation")
    else:
        expected_status = "verification_pending" if row["dispatch_attempted"] else "unavailable"
        if (row["status"] != expected_status or row["accepted"] or row["closure_verified"]
                or not row["unavailable_reason"].strip() or operation == "query" and row["dispatch_attempted"]):
            raise ValueError("war overview unavailable/pending result overclaims an outcome")
    return row
