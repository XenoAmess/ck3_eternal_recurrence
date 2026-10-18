"""Observe one retained Sway after an ordinary, completed military read.

The original war query and its following-turn consumers finish first. No new
Sway, pending reconciliation, world action, clock or replacement plan is possible
here. Other war phases, battles, retreats and mandatory contexts keep priority.
"""
from __future__ import annotations

from collections.abc import Mapping

from ..ordinary_sway_lifecycle_observation_v1 import READERS, observe_resolved_sway_lifecycle_v1
from ..ordinary_sway_schedule_v1 import plan_ordinary_sway_schedule_v1
from ..m5_observed_opportunity_selector import observed_frame
from .driver import BridgeUnavailableError
from .ordinary_sway_service_v1 import INPUT, STEP as START_STEP, _finish, _inputs, project_ordinary_sway_input_v1
from .player_mercenary_context import STEP as MARKET_QUERY, normalize_player_mercenary_context_v1
from .war_contract import QUERY_ARMY_STRENGTHS_STEP
from ..sway_formal_consumer import _resolved_instance_identity

SCHEMA = "ordinary-sway-quiet-observation-v1"


def _completed_query(planned, outcome):
    plan, source = planned.get("plan"), planned.get("planning_source_frame")
    result = outcome.get("result")
    if not (
        isinstance(plan, Mapping) and outcome.get("status") == "executed"
        and plan.get("selected_step") == outcome.get("selected_step")
        and "ordinary_sway_optional" not in outcome
        and isinstance(result, Mapping)
        and isinstance(source, Mapping) and source.get("status") == "complete"
    ):
        return None
    if (plan.get("phase") == "native_war_army_strength_query"
            and outcome.get("selected_step") == QUERY_ARMY_STRENGTHS_STEP
            and isinstance(result.get("army_strengths"), list)
            and result.get("status") in {"available", "partial"}):
        return "after_completed_ordinary_army_query"
    if (plan.get("phase") == "native_war_mercenary_query"
            and outcome.get("selected_step") == MARKET_QUERY
            and result.get("step") == MARKET_QUERY
            and result.get("accepted") is True and result.get("read_only") is True
            and result.get("status") == "completed"
            and type(result.get("query_sequence")) is int and result["query_sequence"] > 0
            and isinstance(result.get("mercenary_query_source_frame_v1"), Mapping)):
        return "after_completed_ordinary_mercenary_query"
    return None


def _market_query_matches(snapshot, result):
    """Use the same complete market frame/DTO checks as its ordinary consumer."""
    try:
        frame = observed_frame(snapshot)
        if (result["mercenary_query_source_frame_v1"] != frame
                or result.get("snapshot_revision") != frame["native_revision"]
                or result.get("date_raw") != frame["date_raw"]):
            return False
        normalize_player_mercenary_context_v1(result.get("player_mercenary_context"), snapshot=snapshot)
    except (ValueError, BridgeUnavailableError):
        return False
    return True


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


def _observe_applied_after_turn(service, planned, outcome, *, window, receipt_key,
                                expected_start_identity=None, verified_hold_snapshot=None):
    """Best-effort read after original following consumers; never replay the turn."""
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
        if expected_start_identity is not None and _start_identity(resolved) != expected_start_identity:
            return outcome
        staged = planned.get(INPUT)
        frame = (project_ordinary_sway_input_v1(verified_hold_snapshot, None)["snapshot"]
                 if verified_hold_snapshot is not None
                 else staged.get("snapshot") if isinstance(staged, Mapping) else None)
        if not isinstance(frame, Mapping):
            return outcome
        job = plan_ordinary_sway_schedule_v1(
            frame, selected_step=outcome["selected_step"], ledger=ledger, state=state,
            active_observation_only=True,
        )
        if job["job"] != "observe_applied":
            return outcome
        # No Native read is taken when there is no original applied instance.
        snapshot = (verified_hold_snapshot if verified_hold_snapshot is not None
                    else service.snapshot(include_native_command_history=False))
        if verified_hold_snapshot is None and not _quiet_same_actor(snapshot, planned["planning_source_frame"]):
            return outcome
        if outcome["selected_step"] == MARKET_QUERY and not _market_query_matches(snapshot, outcome["result"]):
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
        after_key = ("after_completed_query" if receipt_key == "ordinary_sway_optional"
                     else "after_verified_hold" if verified_hold_snapshot is not None else "after_completed_start")
        return {**outcome, receipt_key: {
            "schema": SCHEMA, **receipt, after_key: outcome["selected_step"],
            "schedule_window": window,
            "original_selected_step_preserved": True, "submit_attempted": False,
            "request_retried": False, "new_game_days": 0,
            "following_consumption_deferred_to_later_ordinary_turn": True,
        }}
    except Exception as error:
        # The ordinary query already completed. Optional reads or state writes
        # must never hide that result and cause a caller to replay the turn.
        return {**outcome, receipt_key: {
            "schema": SCHEMA, "status": "unavailable",
            "schedule_window": window,
            "reason": f"{type(error).__name__}: {error}",
            "original_selected_step_preserved": True, "submit_attempted": False,
            "request_retried": False, "new_game_days": 0,
        }}


def observe_sway_after_quiet_query_v1(service, planned, outcome):
    """Retain the original army/market result, including on optional failure."""
    window = _completed_query(planned, outcome)
    if window is None:
        return outcome
    return _observe_applied_after_turn(service, planned, outcome, window=window,
                                      receipt_key="ordinary_sway_optional")


def _start_identity(value):
    if (not isinstance(value, Mapping) or value.get("status") != "applied"
            or value.get("postcondition_verified") is not True):
        return None
    try:
        instance = _resolved_instance_identity(value)
    except Exception:
        return None
    if not isinstance(instance, Mapping):
        return None
    identity = (value.get("action_id"), value.get("actor_character_id"), value.get("target_character_id"),
                instance.get("scheme_instance_id"), instance.get("scheme_instance_generation"))
    if (not isinstance(identity[0], str) or not identity[0]
            or any(type(item) is not int or item <= 0 for item in identity[1:])):
        return None
    return identity


def observe_sway_after_applied_start_v1(service, planned, outcome):
    """Capture an early named baseline after the independently applied ordinary Start."""
    plan, receipt = planned.get("plan"), outcome.get("ordinary_sway_optional")
    source = planned.get("planning_source_frame")
    result = outcome.get("result")
    if (not isinstance(plan, Mapping) or plan.get("selected_step") != START_STEP
            or outcome.get("selected_step") != START_STEP or outcome.get("status") != "executed"
            or "ordinary_sway_post_start_observation" in outcome
            or not isinstance(receipt, Mapping) or receipt.get("job") != "query_selected_target"
            or receipt.get("outcome") != "applied"
            or not isinstance(source, Mapping) or source.get("status") != "complete"
            or getattr(service.driver, "allow_private_active_scheme_sway_completion_query", False) is not True
            or getattr(service.driver, "allow_private_active_scheme_sway_outcome_opinion_query", False) is not True):
        return outcome
    identity = _start_identity(result)
    job = plan.get("ordinary_sway_job_v1")
    if (identity is None or _start_identity(receipt.get("result")) != identity
            or not isinstance(job, Mapping) or job.get("job") != "query_selected_target"
            or job.get("target_character_id") != identity[2]):
        return outcome
    return _observe_applied_after_turn(service, planned, outcome,
        window="after_completed_ordinary_sway_start", receipt_key="ordinary_sway_post_start_observation",
        expected_start_identity=identity)
