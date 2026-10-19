"""Pause after one completed war-results callback crosses the UI scope.

This never retries the close or gives it UI credit.  The pending close remains
owned by the ordinary war-results transport until a new, paused owner query.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from time import monotonic


_REASON = re.compile(
    r"war_results_ui_scope_transition;begin_date_raw=(\d+);"
    r"end_date_raw=(\d+);begin_paused=true;end_paused=false;"
    r"owner_boundary_admitted=true\Z"
)
_PAUSE_OBSERVATION_SECONDS = 1.5


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


def _observation_stop_reason(snapshot: object, source: Mapping[str, object],
                             baseline: Mapping[str, object]) -> str | None:
    """End a read-only wait on a paused map or an invalidated owner scope."""
    if not isinstance(snapshot, Mapping):
        return "snapshot_unavailable"
    current = _frame(snapshot)
    if (type(source.get("native_revision")) is not int
            or source["native_revision"] <= 0
            or type(source.get("date_raw")) is not int
            or type(source.get("actor_character_id")) is not int
            or source["actor_character_id"] <= 0
            or not isinstance(source.get("episode_run_id"), str) or not source["episode_run_id"]
            or type(source.get("connection_generation")) is not int
            or type(current.get("bridge_pid")) is not int or current["bridge_pid"] <= 0
            or current["bridge_pid"] != current.get("hello_pid")
            or current["bridge_pid"] != baseline.get("bridge_pid")
            or any(current.get(key) != source.get(key) for key in (
                "actor_character_id", "episode_run_id", "connection_generation"))):
        return "owner_scope_changed_or_unknown"
    if any(type(current.get(key)) is not int or type(baseline.get(key)) is not int
           or current[key] < baseline[key] for key in ("revision", "native_revision", "date_raw")):
        return "frame_regressed_or_unknown"
    if current["native_revision"] < source["native_revision"] or current["date_raw"] < source["date_raw"]:
        return "source_frame_regressed"
    if snapshot.get("map_ready") is not True:
        return "map_not_ready"
    played = snapshot.get("played_character")
    if (snapshot.get("one_life_terminal") is True or snapshot.get("one_life_terminal_reason") is not None
            or snapshot.get("episode_identity_pending") is True
            or isinstance(played, Mapping) and played.get("alive") is False):
        return "lifecycle_boundary"
    hint = snapshot.get("top_exclusive_modal_choice_hint")
    if (snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None
            or isinstance(hint, Mapping) and hint.get("status") == "present"):
        return "new_player_decision"
    return "paused" if snapshot.get("paused") is True else None


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
        "wait_attempted": False,
    }
    reader = getattr(driver, "take_internal_semantic_snapshot", None)
    pause = getattr(driver, "execute_step", None)
    if not callable(reader) or not callable(pause):
        evidence["failure"] = "pause_or_semantic_reader_unavailable"
        return evidence
    try:
        before_raw = reader()
        before = _frame(before_raw)
        evidence["before_pause"] = before
        before_reason = _observation_stop_reason(before_raw, source, before)
        # A new decision does not prevent the existing one safety pause. It
        # only prevents waiting past that boundary or doing any further work.
        if before_reason not in (None, "paused", "new_player_decision", "lifecycle_boundary"):
            evidence["observation_stop_reason"] = before_reason
            evidence["failure"] = "same_owner_paused_map_not_observed"
            return evidence
        if before.get("paused") is False:
            evidence["pause_attempted"] = True
            evidence["pause_result"] = pause("pause-map", expected_revision=None)
        after_raw = reader()
        after = _frame(after_raw)
        evidence["after_pause"] = after
        reason = _observation_stop_reason(after_raw, source, before)
        if after.get("paused") is True and reason in ("new_player_decision", "lifecycle_boundary"):
            # Preserve the existing immediate pause acknowledgement contract;
            # this status grants no decision handling or window-close credit.
            reason = "paused"
        if reason is None:
            # Observe the already submitted pause. This existing internal wait
            # reads semantic frames without another action or history export.
            waiter = getattr(driver, "_wait_for_life_advance_snapshot", None)
            if callable(waiter):
                evidence.update(wait_attempted=True, wait_budget_seconds=_PAUSE_OBSERVATION_SECONDS,
                                immediate_after_pause=dict(after), observed_frame_count=0)
                baseline = after
                started = monotonic()

                def stop(current: object) -> bool:
                    nonlocal reason
                    evidence["observed_frame_count"] += 1
                    reason = _observation_stop_reason(current, source, baseline)
                    return reason is not None

                try:
                    after_raw = waiter(after_raw, stop, timeout_seconds=_PAUSE_OBSERVATION_SECONDS)
                finally:
                    evidence["wait_elapsed_seconds"] = max(0.0, monotonic() - started)
                after = _frame(after_raw)
                evidence["after_pause"] = after
                reason = _observation_stop_reason(after_raw, source, baseline) or "timeout"
            else:
                reason = "internal_pause_observer_unavailable"
        evidence["observation_stop_reason"] = reason
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
    if reason == "paused" and after.get("paused") is True and after.get("map_ready") is True and same_owner:
        evidence["status"] = "paused_same_owner_requery_required"
    else:
        evidence["failure"] = "same_owner_paused_map_not_observed"
    return evidence
