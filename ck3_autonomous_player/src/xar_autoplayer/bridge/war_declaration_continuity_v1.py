"""Retain one actual declaration request and observe its bounded postcondition.

The current active-war projection has no CB identity. This module records that
limit explicitly and never promotes an ACK or a changed war count to success.
"""

from __future__ import annotations

from copy import deepcopy
import json
from collections.abc import Mapping
from functools import wraps

from .declaration_contract import normalize_declarable_wars
from ..environment import write_json_atomic

KEY = "war_declaration_continuity_v1"
SCHEMA = "war-declaration-continuity-v1"
TERMINAL = {"war_started", "native_rejected", "not_submitted"}
MAX_RECORD_BYTES = 32768


def _locked(operation):
    @wraps(operation)
    def call(driver, *args, **kwargs):
        with driver._driver_state_lock:
            return operation(driver, *args, **kwargs)
    return call


def _id(value):
    return type(value) is int and 0 < value <= 2**31 - 1


def _war_id(value):
    return type(value) is int and 0 <= value <= 2**31 - 1


def _path(driver):
    return (driver._native_driver_state_path().parent / "war-declaration-continuity-v1.json"
            if driver.state_dir is not None else None)


def _record(driver):
    if getattr(driver, "_war_declaration_continuity_loaded_v1", False):
        return getattr(driver, "_war_declaration_continuity_v1", None)
    path = _path(driver)
    value = None
    if path is not None and path.exists():
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("declaration continuity record exceeds its bound")
        value = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(value, dict) or value.get("schema") != SCHEMA
                or not isinstance(value.get("request_id"), str)
                or not value["request_id"] or not isinstance(value.get("before_war_ids"), list)
                or not isinstance(value.get("owner"), dict)):
            raise ValueError("declaration continuity record is malformed")
        normalize_declarable_wars([value.get("declaration")])
        # A new SDK has no waiter for an old request. Only the original ID may
        # be collected; resetting this local latch never authorizes resending.
        value["in_flight"] = False
    driver._war_declaration_continuity_v1 = value
    driver._war_declaration_continuity_loaded_v1 = True
    return value


def _store(driver, value):
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RECORD_BYTES:
        raise ValueError("declaration continuity record exceeds its bound")
    path = _path(driver)
    if path is not None:
        write_json_atomic(path, value)
    driver._war_declaration_continuity_v1 = deepcopy(value)
    driver._war_declaration_continuity_loaded_v1 = True


def _owner(snapshot):
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    return {
        "actor_character_id": played.get("character_id") if isinstance(played, Mapping) else None,
        "episode_run_id": snapshot.get("episode_run_id"),
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None,
        "hello_pid": hello.get("pid") if isinstance(hello, Mapping) else None,
        "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None,
    }


@_locked
def prepare_declaration_attempt_v1(driver, snapshot, declaration, request_id):
    """Durably arm uncertainty before sending the original request."""
    previous = _record(driver)
    if isinstance(previous, Mapping) and previous.get("status") not in TERMINAL:
        raise ValueError("original declaration remains unresolved; no second submission")
    selected = normalize_declarable_wars([dict(declaration)])[0]
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or len(wars) > 256:
        raise ValueError("bounded actual before-war inventory required")
    ids = [row.get("war_id") for row in wars if isinstance(row, Mapping)]
    if len(ids) != len(wars) or any(not _war_id(item) for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("actual before-war IDs are malformed")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("original native request identity required")
    roles = None
    envelope = driver.get_current_prewar_force_coalition_coverage_v2(selected["declaration_id"], snapshot)
    value = envelope.get("prewar_force_coalition_coverage_v2") if isinstance(envelope, Mapping) else None
    observed_roles = value.get("final_cb_roles") if isinstance(value, Mapping) else None
    if (isinstance(observed_roles, Mapping) and observed_roles.get("available") is True
            and observed_roles.get("source") == "finalized_selected_cb_context"
            and _id(observed_roles.get("primary_attacker_character_id"))
            and _id(observed_roles.get("primary_defender_character_id"))):
        roles = {key: observed_roles[key] for key in (
            "primary_attacker_character_id", "primary_defender_character_id", "source")}
    owner = _owner(snapshot)
    if (not _id(owner["actor_character_id"]) or not _id(owner["bridge_pid"])
            or owner["bridge_pid"] != owner["hello_pid"]
            or type(owner["connection_generation"]) is not int
            or owner["connection_generation"] < 1):
        raise ValueError("actual declaration actor/process/connection required")
    pending = {
        "schema": SCHEMA, "request_id": request_id,
        "declaration": selected, "before_war_ids": ids, "final_cb_roles": roles,
        "owner": owner, "submitted_snapshot_id": snapshot.get("snapshot_id"),
        "submitted_revision": snapshot.get("revision"),
        "submitted_native_revision": snapshot.get("native_revision"),
        "submitted_date_raw": snapshot.get("date_raw"),
        "status": "submission_unknown", "native_response": "unknown",
        "in_flight": True,
        "request_retried": False, "war_id": None,
        "postcondition_verified": False, "casus_belli_identity_observed": False,
        "postcondition_scope": "unique_new_primary_attacker_opponent_and_target_titles",
        "reason": "original_request_not_yet_observed",
    }
    _store(driver, pending)
    return deepcopy(pending)


@_locked
def mark_declaration_response_v1(driver, *, accepted=None, not_submitted=False):
    pending = deepcopy(_record(driver))
    if not isinstance(pending, dict):
        raise ValueError("original declaration continuity record required")
    pending["in_flight"] = False
    if not_submitted:
        pending.update(status="not_submitted", reason="primitive_rejected_before_send")
    elif accepted is False:
        pending.update(status="native_rejected", native_response="rejected", reason="original_native_request_refused")
    elif accepted is True:
        pending.update(status="declaration_submitted", native_response="accepted", reason="awaiting_unique_actual_war")
    _store(driver, pending)


@_locked
def observe_declaration_attempt_v1(driver, snapshot):
    """Read/collect the original request only; this function never sends."""
    pending = deepcopy(_record(driver))
    if not isinstance(pending, dict):
        return None
    if pending.get("status") in TERMINAL:
        return pending
    if _owner(snapshot) != pending["owner"]:
        return {**pending, "reason": "actual_process_connection_or_episode_changed"}
    if pending.get("native_response") == "unknown" and pending.get("in_flight") is not True:
        frame = driver.state.wait_for_command_result(pending["request_id"], 0.0)
        if frame is not None:
            valid = (isinstance(frame, Mapping) and frame.get("type") == "command_result"
                     and frame.get("protocol_version") == 1
                     and frame.get("request_id") == pending["request_id"])
            result = frame.get("result") if valid else None
            if valid and frame.get("ok") is False and isinstance(frame.get("error"), str):
                pending.update(status="native_rejected", native_response="rejected", reason="original_native_request_refused")
            elif (valid and frame.get("ok") is True and isinstance(result, Mapping)
                  and result.get("step") == "declare-war-" + pending["declaration"]["declaration_id"]
                  and result.get("accepted") is True):
                pending.update(status="declaration_submitted", native_response="accepted")
            else:
                pending["reason"] = "original_native_response_malformed"
    roles = pending.get("final_cb_roles")
    titles = pending["declaration"]["target_title_ids"]
    fresh = (type(snapshot.get("native_revision")) is int
             and type(pending.get("submitted_native_revision")) is int
             and snapshot["native_revision"] > pending["submitted_native_revision"])
    wars = snapshot.get("active_wars")
    can_match = (fresh and snapshot.get("paused") is True and snapshot.get("map_ready") is True
                 and isinstance(wars, list) and len(wars) <= 256
                 and isinstance(roles, Mapping) and titles
                 and pending["owner"]["actor_character_id"] == roles["primary_attacker_character_id"])
    matches = []
    if can_match:
        matches = [row["war_id"] for row in wars if isinstance(row, Mapping)
            and _war_id(row.get("war_id")) and row["war_id"] not in pending["before_war_ids"]
            and row.get("player_side") == "attacker"
            and row.get("player_is_primary_war_leader") is True
            and row.get("primary_opponent_character_id") == roles["primary_defender_character_id"]
            and row.get("targeted_title_ids") == titles]
    if len(matches) == 1 and pending.get("native_response") == "accepted":
        pending.update(status="war_started", war_id=matches[0], postcondition_verified=True,
                       observed_snapshot_id=snapshot.get("snapshot_id"),
                       observed_native_revision=snapshot.get("native_revision"),
                       reason="unique_new_war_matches_actual_published_identity")
    elif pending.get("status") not in TERMINAL:
        pending["reason"] = ("ambiguous_new_wars" if len(matches) > 1 else
                             "awaiting_unique_actual_war" if can_match else
                             "actual_role_title_or_fresh_frame_identity_unavailable")
    if pending != _record(driver):
        _store(driver, pending)
    return pending
