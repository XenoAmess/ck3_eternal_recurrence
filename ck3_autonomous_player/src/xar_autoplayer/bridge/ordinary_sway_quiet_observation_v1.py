"""Observe one retained Sway after an ordinary, completed army read.

The original war query and its following-turn consumers finish first. No new
Sway, pending reconciliation, world action, clock or replacement plan is possible
here. Other war phases, battles, retreats and mandatory contexts keep priority.
"""
from __future__ import annotations

from collections.abc import Mapping

from ..ordinary_sway_lifecycle_observation_v1 import READERS, observe_resolved_sway_lifecycle_v1
from ..ordinary_sway_schedule_v1 import plan_ordinary_sway_schedule_v1
from .ordinary_sway_service_v1 import INPUT, _finish, _inputs, project_ordinary_sway_input_v1
from .war_contract import QUERY_ARMY_STRENGTHS_STEP

SCHEMA = "ordinary-sway-quiet-observation-v1"


def _completed_query(planned, outcome):
    plan, source = planned.get("plan"), planned.get("planning_source_frame")
    result = outcome.get("result")
    return bool(
        isinstance(plan, Mapping) and plan.get("phase") == "native_war_army_strength_query"
        and plan.get("selected_step") == QUERY_ARMY_STRENGTHS_STEP
        and outcome.get("status") == "executed"
        and outcome.get("selected_step") == QUERY_ARMY_STRENGTHS_STEP
        and "ordinary_sway_optional" not in outcome
        and isinstance(result, Mapping) and isinstance(result.get("army_strengths"), list)
        and result.get("status") in {"available", "partial"}
        and isinstance(source, Mapping) and source.get("status") == "complete"
    )


def _quiet_same_actor(snapshot, source):
    played, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    frame = project_ordinary_sway_input_v1(snapshot, None)["snapshot"]
    context = frame.get("active_context")
    hint = snapshot.get("top_exclusive_modal_choice_hint")
    armies = snapshot.get("player_armies")
    return bool(
        snapshot.get("paused") is True and snapshot.get("map_ready") is True
        and snapshot.get("one_life_terminal_reason") is None
        and snapshot.get("episode_identity_pending") is False
        and isinstance(played, Mapping) and played.get("alive") is True
        and played.get("character_id") == source.get("actor_character_id")
        and snapshot.get("episode_run_id") == source.get("episode_run_id")
        and snapshot.get("date_raw") == source.get("date_raw")
        and isinstance(diagnostics, Mapping)
        and diagnostics.get("bridge_pid") == source.get("bridge_pid")
        and diagnostics.get("connection_generation") == source.get("connection_generation")
        and type(source.get("bridge_pid")) is int and source["bridge_pid"] > 0
        and type(source.get("connection_generation")) is int
        and isinstance(context, Mapping)
        and "active_event" in context and context["active_event"] is None
        and "pending_character_interaction" in context and context["pending_character_interaction"] is None
        and not (isinstance(hint, Mapping) and hint.get("status") == "present")
        and isinstance(armies, list)
        and all(isinstance(army, Mapping) and army.get("in_combat") is False
                and army.get("retreating") is False
                and army.get("gathering") is not True for army in armies)
    )


def observe_sway_after_quiet_query_v1(service, planned, outcome):
    """Best-effort post-query observation; retain the original action result on failure."""
    if not _completed_query(planned, outcome):
        return outcome
    if not any(getattr(service.driver, permission, False) is True for _, permission, _ in READERS):
        return outcome
    try:
        inputs = _inputs(service)
        if inputs is None:
            return outcome
        state_dir, state, ledger = inputs
        resolved = ledger.get("resolved")
        if (ledger.get("pending") is not None or not isinstance(resolved, Mapping)
                or resolved.get("status") != "applied"
                or resolved.get("postcondition_verified") is not True):
            return outcome
        staged = planned.get(INPUT)
        frame = staged.get("snapshot") if isinstance(staged, Mapping) else None
        if not isinstance(frame, Mapping):
            return outcome
        job = plan_ordinary_sway_schedule_v1(
            frame, selected_step=outcome["selected_step"], ledger=ledger, state=state,
            active_observation_only=True,
        )
        if job["job"] != "observe_applied":
            return outcome
        # No Native read is taken when there is no original applied instance.
        snapshot = service.snapshot(include_native_command_history=False)
        if not _quiet_same_actor(snapshot, planned["planning_source_frame"]):
            return outcome
        frame = project_ordinary_sway_input_v1(snapshot, None)["snapshot"]
        job = plan_ordinary_sway_schedule_v1(
            frame, selected_step=outcome["selected_step"], ledger=ledger, state=state,
            active_observation_only=True,
        )
        if job["job"] != "observe_applied":
            return outcome
        observation = observe_resolved_sway_lifecycle_v1(service, snapshot=frame)
        result = observation or {"status": "unavailable", "reason": "existing_observer_unready"}
        receipt = _finish(state_dir, job, frame,
                          "observed" if result.get("status") == "observed" else "unavailable", result)
        return {**outcome, "ordinary_sway_optional": {
            "schema": SCHEMA, **receipt, "after_completed_query": outcome["selected_step"],
            "schedule_window": "after_completed_ordinary_army_query",
            "original_selected_step_preserved": True, "submit_attempted": False,
            "request_retried": False, "new_game_days": 0,
            "following_consumption_deferred_to_later_ordinary_turn": True,
        }}
    except Exception as error:
        # The ordinary query already completed. Optional reads or state writes
        # must never hide that result and cause a caller to replay the turn.
        return {**outcome, "ordinary_sway_optional": {
            "schema": SCHEMA, "status": "unavailable",
            "schedule_window": "after_completed_ordinary_army_query",
            "reason": f"{type(error).__name__}: {error}",
            "original_selected_step_preserved": True, "submit_attempted": False,
            "request_retried": False, "new_game_days": 0,
        }}
