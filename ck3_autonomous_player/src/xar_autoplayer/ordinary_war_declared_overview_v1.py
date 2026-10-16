"""Ordinary priority for the independently observed war overview window."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

QUERY_WAR_DECLARED_OVERVIEW_V1_STEP = "query-war-declared-overview-v1"
CLOSE_WAR_DECLARED_OVERVIEW_V1_STEP = "close-war-declared-overview-v1"
QUERY_WAR_DECLARED_OVERVIEW_V1_CAPABILITY = "game.command.query-war-declared-overview-v1"
CLOSE_WAR_DECLARED_OVERVIEW_V1_CAPABILITY = "game.command.close-war-declared-overview-v1"
WAR_DECLARED_OVERVIEW_V1_POLICY = "ordinary-war-declared-overview-v1"
WAR_DECLARED_OVERVIEW_V1_PUBLIC_KEYS = (
    "war_declared_overview_v1_observation",
    "war_declared_overview_v1_query_attempt",
    "war_declared_overview_v1_close_pending",
)


def _binding(snapshot: Mapping[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    return {
        "queried_snapshot_id": snapshot.get("snapshot_id"),
        "queried_revision": snapshot.get("revision"),
        "queried_native_revision": snapshot.get("native_revision"),
        "queried_date_raw": snapshot.get("date_raw"),
        "queried_actor_character_id": played.get("character_id") if isinstance(played, Mapping) else None,
        "queried_connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None,
        "queried_episode_run_id": snapshot.get("episode_run_id"),
    }


def _current(value: object, snapshot: Mapping[str, object], marker: str, schema: str) -> bool:
    return (isinstance(value, Mapping) and value.get(marker) == schema
            and all(key in value and value[key] == expected
                    and type(value[key]) is type(expected)
                    for key, expected in _binding(snapshot).items()))


def war_declared_overview_query_frame_v1(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    """Cadence identity excludes public projection revisions and snapshot IDs."""
    binding = _binding(snapshot)
    pending = snapshot.get(WAR_DECLARED_OVERVIEW_V1_PUBLIC_KEYS[2])
    original_close = pending.get("native_request_id") if isinstance(pending, Mapping) else None
    return tuple(binding[key] for key in (
        "queried_native_revision", "queried_date_raw", "queried_actor_character_id",
        "queried_connection_generation", "queried_episode_run_id")) + (original_close,)


def war_declared_overview_presence_v1(value: object) -> str:
    """Only the validated Native post-read can establish current visibility."""
    if not (isinstance(value, Mapping) and value.get("available") is True
            and value.get("post_observed") is True and value.get("scope_unchanged") is True):
        return "unknown"
    present = value.get("post_window_present")
    visible = value.get("post_effective_visible")
    if present is False and visible is False:
        return "absent"
    if present is True and visible is False:
        return "hidden"
    if present is True and visible is True:
        return "visible"
    return "unknown"


def plan_ordinary_war_declared_overview_v1(
    snapshot: object, *, action_steps: Iterable[str] = (),
    bridge_capabilities: Iterable[str] = (),
) -> dict[str, object] | None:
    """Choose one UI read/close before ordinary work; lifecycle is checked by caller."""
    if not isinstance(snapshot, Mapping):
        return None
    steps, caps = set(action_steps), set(bridge_capabilities)
    can_query = QUERY_WAR_DECLARED_OVERVIEW_V1_CAPABILITY in caps
    can_close = CLOSE_WAR_DECLARED_OVERVIEW_V1_CAPABILITY in caps
    observation = snapshot.get(WAR_DECLARED_OVERVIEW_V1_PUBLIC_KEYS[0])
    attempt = snapshot.get(WAR_DECLARED_OVERVIEW_V1_PUBLIC_KEYS[1])
    pending = snapshot.get(WAR_DECLARED_OVERVIEW_V1_PUBLIC_KEYS[2])
    if not (can_query or can_close or isinstance(pending, Mapping)):
        return None
    current_observation = _current(
        observation, snapshot, "sdk_validation_schema", "war-declared-overview-source-v1")
    current_attempt = _current(
        attempt, snapshot, "validation_schema", "war-declared-overview-query-attempt-v1")
    presence = war_declared_overview_presence_v1(observation) if current_observation else "unknown"
    # A fresh read can remove the UI blocker while an older close remains unconfirmed.
    if presence in ("absent", "hidden"):
        return None
    if (presence == "unknown" and current_attempt
            and attempt.get("status") == "failed"
            and not isinstance(pending, Mapping)):
        # A failed read has not proved a visible window.  Keep its exact-frame
        # negative attempt, then let ordinary planning run under its own
        # native action guards.  A changed frame makes this attempt stale and
        # schedules a new read; a known visible window never takes this path.
        return None
    selected = None
    reason = "war overview visibility is unknown"
    status = "blocked"
    if snapshot.get("map_ready") is not True:
        reason = "war overview requires a paused, ready frame"
    elif snapshot.get("paused") is not True:
        if snapshot.get("paused") is False and "pause-map" in steps:
            selected, reason, status = "pause-map", "pause the ready map before observing or closing the war overview", "ready"
        else:
            reason = "war overview requires a paused frame and pause-map is unavailable"
    elif presence == "visible" and isinstance(pending, Mapping):
        if not current_attempt and can_query and QUERY_WAR_DECLARED_OVERVIEW_V1_STEP in steps:
            selected, reason, status = QUERY_WAR_DECLARED_OVERVIEW_V1_STEP, "observe the pending close once without resubmitting it", "ready"
        else:
            reason, status = "the original war overview close is still pending; do not resubmit", "pending"
    elif presence == "visible" and can_close and CLOSE_WAR_DECLARED_OVERVIEW_V1_STEP in steps:
        selected, reason, status = CLOSE_WAR_DECLARED_OVERVIEW_V1_STEP, "dismiss the observed war overview before ordinary actions", "ready"
    elif presence == "visible":
        reason = "the native war overview close capability is unavailable"
    elif current_attempt:
        reason, status = "the current war overview read was already attempted; do not repeat it", "pending"
    elif can_query and QUERY_WAR_DECLARED_OVERVIEW_V1_STEP in steps:
        selected, reason, status = QUERY_WAR_DECLARED_OVERVIEW_V1_STEP, "observe the war overview once before ordinary actions", "ready"
    return {
        "policy": WAR_DECLARED_OVERVIEW_V1_POLICY,
        "phase": "war_declared_overview",
        "status": status, "selected_step": selected, "reason": reason,
        "pending_actions": [selected] if selected else [],
        "war_declared_overview": {
            "presence": presence, "close_pending": isinstance(pending, Mapping),
            "query_attempt_status": attempt.get("status") if isinstance(attempt, Mapping) else None,
            "close_action_credit": False,
        },
    }
