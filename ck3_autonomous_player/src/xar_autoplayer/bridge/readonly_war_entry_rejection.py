"""Bound one failed native war-entry read without treating it as a game action."""

from __future__ import annotations

import copy
import json

from .war_entry_contract import parse_query_war_entry_assessments_step


_ERROR = "application-main typed query failed or its snapshot changed"
_COOLDOWN_DATE_RAW = 7 * 24
_TYPED_FAILURE = {
    "executor_enter": True,
    "executor_exception": {"code": 0, "image": "none", "rva": None},
    "executor_finish": True,
    "executor_typed_result": False,
    "final_equal": None,
    "final_read": None,
    "frame_stable": True,
    "query_type": "war_entry",
    "stage": "typed_result",
    "typed_result": False,
    "wait_completed": True,
    "wait_result": "completed",
}


def returned_readonly_war_entry_typed_rejection_v1(error, selected_step, planned):
    """Require the exact terminal native read failure and its request binding."""
    from .native_driver import _NativeCommandRejectedError

    targets = parse_query_war_entry_assessments_step(selected_step)
    if not isinstance(error, _NativeCommandRejectedError) or targets is None:
        return None
    source = planned.get("planning_source_frame") if isinstance(planned, dict) else None
    plan = planned.get("plan") if isinstance(planned, dict) else None
    request = error.native_request_frame
    response = error.native_command_result_frame
    request_id = error.native_request_id
    typed = response.get("typed_query_failure_v1") if isinstance(response, dict) else None
    if (not isinstance(source, dict) or source.get("status") != "complete"
            or not isinstance(plan, dict) or plan.get("selected_step") != selected_step
            or planned.get("snapshot_id") != source.get("snapshot_id")
            or planned.get("revision") != source.get("revision")
            or type(source.get("native_revision")) is not int or source["native_revision"] <= 0
            or type(source.get("date_raw")) is not int
            or type(source.get("actor_character_id")) is not int or source["actor_character_id"] <= 0
            or not isinstance(source.get("episode_run_id"), str) or not source["episode_run_id"]
            or type(source.get("connection_generation")) is not int
            or type(source.get("bridge_pid")) is not int or source["bridge_pid"] <= 0
            or not isinstance(request_id, str) or not request_id
            or not isinstance(request, dict) or not isinstance(response, dict)
            or request.get("type") != "execute_step" or request.get("protocol_version") != 1
            or request.get("request_id") != request_id or request.get("step") != selected_step
            or request.get("expected_revision") != source["native_revision"]
            or response.get("type") != "command_result" or response.get("protocol_version") != 1
            or response.get("request_id") != request_id or response.get("ok") is not False
            or response.get("error") != _ERROR or typed != _TYPED_FAILURE
            or error.native_error != _ERROR + "; typed_query_failure_v1="
            + json.dumps(_TYPED_FAILURE, sort_keys=True, separators=(",", ":"))):
        return None
    target = targets[0]
    return {
        "status": "readonly_rejected", "selected_step": selected_step,
        "plan": copy.deepcopy(plan),
        "snapshot_id": source["snapshot_id"], "revision": source["revision"],
        "result": {
            "schema": "xar.readonly-war-entry-typed-rejection.v1",
            "step": selected_step, "status": "rejected_no_business_submission",
            "accepted": False, "read_only": True, "request_sent": True,
            "business_submission": False, "terminal_native_rejection": True,
            "replan_required": True, "fresh_snapshot_required": True,
            "replay_allowed": False,
            "native_rejection": {
                "native_request_id": request_id, "native_step": selected_step,
                "expected_native_revision": source["native_revision"],
                "native_error": _ERROR,
                "typed_query_failure_v1": copy.deepcopy(_TYPED_FAILURE),
            },
            "source_frame": copy.deepcopy(source),
            "target_character_id": target,
            "cooldown_until_date_raw": source["date_raw"] + _COOLDOWN_DATE_RAW,
        },
    }


def observe_readonly_war_entry_rejection_v1(service, rejection):
    """Read the current semantic frame; never resend the failed query."""
    from .driver import BridgeUnavailableError

    reader = getattr(service.driver, "take_internal_semantic_snapshot", None)
    if not callable(reader):
        raise BridgeUnavailableError("war-entry rejection requires a semantic reader")
    fresh = reader()
    source = rejection["result"]["source_frame"]
    played = fresh.get("played_character") if isinstance(fresh, dict) else None
    diagnostics = fresh.get("diagnostics") if isinstance(fresh, dict) else None
    verified = bool(
        isinstance(fresh, dict) and fresh.get("paused") is True
        and fresh.get("map_ready") is True and isinstance(played, dict)
        and played.get("alive") is True
        and played.get("character_id") == source["actor_character_id"]
        and fresh.get("episode_run_id") == source["episode_run_id"]
        and isinstance(diagnostics, dict)
        and diagnostics.get("bridge_pid") == source["bridge_pid"]
        and diagnostics.get("connection_generation") == source["connection_generation"]
        and type(fresh.get("date_raw")) is int and fresh["date_raw"] >= source["date_raw"]
        and type(fresh.get("revision")) is int and fresh["revision"] >= source["revision"]
        and type(fresh.get("native_revision")) is int
        and fresh["native_revision"] >= source["native_revision"]
        and fresh.get("snapshot_id") == "native:" + str(fresh["native_revision"])
    )
    observed = copy.deepcopy(rejection)
    observed["result"].update(
        fresh_snapshot_verified=verified, replan_deferred=not verified,
        fresh_frame=({key: fresh.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw", "paused",
            "map_ready", "episode_run_id",
        )} | {
            "actor_character_id": played.get("character_id") if isinstance(played, dict) else None,
            "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, dict) else None,
            "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None,
        } if isinstance(fresh, dict) else None),
    )
    service._readonly_war_entry_rejection_refresh = None if verified else rejection
    if verified:
        failures = list(getattr(service, "_readonly_war_entry_failures", []))
        failures.append({
            "target_character_id": rejection["result"]["target_character_id"],
            "source_frame": copy.deepcopy(source),
            "cooldown_until_date_raw": rejection["result"]["cooldown_until_date_raw"],
        })
        service._readonly_war_entry_failures = failures[-16:]
    return observed


def suppressed_war_entry_read_steps_v1(snapshot, failures):
    """Skip only a failed target for seven game days in this Game/episode."""
    from .war_entry_contract import query_war_entry_assessments_step

    if not isinstance(snapshot, dict) or not isinstance(failures, list):
        return set()
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(played, dict) or not isinstance(diagnostics, dict):
        return set()
    now = snapshot.get("date_raw")
    if type(now) is not int:
        return set()
    suppressed = set()
    for row in failures[-16:]:
        if not isinstance(row, dict) or not isinstance(row.get("source_frame"), dict):
            continue
        source = row["source_frame"]
        target = row.get("target_character_id")
        if (type(target) is not int or target <= 0
                or played.get("character_id") != source.get("actor_character_id")
                or snapshot.get("episode_run_id") != source.get("episode_run_id")
                or diagnostics.get("bridge_pid") != source.get("bridge_pid")
                or diagnostics.get("connection_generation") != source.get("connection_generation")
                or not source.get("date_raw") <= now < row.get("cooldown_until_date_raw", 0)):
            continue
        suppressed.add(query_war_entry_assessments_step([target]))
    return suppressed
