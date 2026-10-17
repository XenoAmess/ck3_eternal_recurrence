"""Pause after one completed war-results callback crosses the UI scope.

This never retries the close or gives it UI credit.  The pending close remains
owned by the ordinary war-results transport until a new, paused owner query.
"""

from __future__ import annotations

from collections.abc import Mapping
import re


_REASON = re.compile(
    r"war_results_ui_scope_transition;begin_date_raw=(\d+);"
    r"end_date_raw=(\d+);begin_paused=true;end_paused=false;"
    r"owner_boundary_admitted=true\Z"
)


def _completed_transition(result: object) -> bool:
    if not isinstance(result, Mapping):
        return False
    reason = result.get("unavailable_reason")
    match = _REASON.fullmatch(reason) if isinstance(reason, str) else None
    top = result.get("native_command_result")
    request_id = result.get("native_request_id")
    receipt = top.get("war_results_window_owner_receipt") if isinstance(top, Mapping) else None
    return bool(
        match and int(match[1]) == int(match[2]) == result.get("queried_date_raw")
        and result.get("schema") == "ck3-war-results-window-v1"
        and result.get("operation") == "close"
        and result.get("step") == "close-war-results-window-v1"
        and result.get("status") == "verification_pending"
        and result.get("available") is False and result.get("accepted") is False
        and result.get("closure_verified") is False
        and result.get("scope_unchanged") is False
        and result.get("dismiss_stage") == "callback_returned"
        and result.get("dismiss_exception_code") == 0
        and result.get("dispatch_attempted") is True
        and result.get("dispatch_invoked") is True
        and result.get("native_handled") is True
        and result.get("post_observed") is True
        and result.get("application_owner_thread_verified") is True
        and isinstance(request_id, str) and request_id.startswith("war-overview-close-")
        and isinstance(top, Mapping) and top.get("ok") is True
        and top.get("request_id") == request_id
        and isinstance(receipt, Mapping) and receipt.get("request_id") == request_id
        and type(receipt.get("ticket_sequence")) is int
        and receipt.get("executor_started_sequence") == receipt["ticket_sequence"]
        and receipt.get("completed_sequence") == receipt["ticket_sequence"]
        and receipt.get("date_raw") == result.get("queried_date_raw")
        and receipt.get("connection_generation") == result.get("queried_connection_generation")
    )


def _frame(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, Mapping):
        return {}
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "actor_character_id": played.get("character_id") if isinstance(played, Mapping) else None,
        "episode_run_id": snapshot.get("episode_run_id"),
        "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None,
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None,
        "hello_pid": hello.get("pid") if isinstance(hello, Mapping) else None,
    }


def pause_after_war_results_scope_transition_v1(driver: object, result: object) -> dict[str, object] | None:
    """Return only pause/requery evidence; preserve the original close result."""
    if not _completed_transition(result):
        return None
    assert isinstance(result, Mapping)
    source = {
        "native_request_id": result["native_request_id"],
        "native_revision": result.get("queried_native_revision"),
        "date_raw": result.get("queried_date_raw"),
        "actor_character_id": result.get("queried_actor_character_id"),
        "episode_run_id": result.get("queried_episode_run_id"),
        "connection_generation": result.get("queried_connection_generation"),
    }
    evidence: dict[str, object] = {
        "schema": "xar.war-results-scope-transition-pause/v1",
        "status": "pause_unverified", "original_close": source,
        "close_replayed": False, "close_action_credit": False,
        "fresh_war_results_query_required": True,
        "pause_attempted": False, "pause_result": None,
    }
    reader = getattr(driver, "take_internal_semantic_snapshot", None)
    pause = getattr(driver, "execute_step", None)
    if not callable(reader) or not callable(pause):
        evidence["failure"] = "pause_or_semantic_reader_unavailable"
        return evidence
    try:
        before = _frame(reader())
        evidence["before_pause"] = before
        if before.get("paused") is False:
            evidence["pause_attempted"] = True
            evidence["pause_result"] = pause("pause-map", expected_revision=None)
        after = _frame(reader())
        evidence["after_pause"] = after
    except Exception as error:
        # Keep the exact original callback uncertainty visible to the caller.
        # A failed pause is never interpreted as a completed close.
        evidence["failure"] = f"{type(error).__name__}: {error}"[:512]
        return evidence
    same_owner = (
        type(after.get("bridge_pid")) is int and after["bridge_pid"] > 0
        and after.get("bridge_pid") == after.get("hello_pid")
        and after.get("actor_character_id") == source["actor_character_id"]
        and after.get("episode_run_id") == source["episode_run_id"]
        and after.get("connection_generation") == source["connection_generation"]
        and type(after.get("native_revision")) is int
        and after["native_revision"] >= source["native_revision"]
        and type(after.get("date_raw")) is int
        and after["date_raw"] >= source["date_raw"]
    )
    if after.get("paused") is True and after.get("map_ready") is True and same_owner:
        evidence["status"] = "paused_same_owner_requery_required"
    else:
        evidence["failure"] = "same_owner_paused_map_not_observed"
    return evidence
