"""Typed sentinel actor boundary; no Continue, Close, SAVE or runtime IO.

The ordinary owner retains the original response and pairs fresh after-metrics
before its existing succession transaction. This leaf only classifies evidence.
"""
from __future__ import annotations

def require(condition, message):
    if not condition:
        raise ValueError("ordinary succession handoff denied: " + message)


def classify_natural_boundary(body, *, current_frame, goal_anchor, game_pid):
    """Observe a typed sentinel natural terminal before ordinary war classifiers.

    This grants zero business credit and no movement/war safety qualification.
    The following metrics and fresh semantic/reconciliation remain mandatory.
    """
    plan = body.get("plan") if isinstance(body, dict) else None
    inner = body.get("result") if isinstance(body, dict) else None
    if not (isinstance(inner, dict)
            and inner.get("source") == "native-tactical-daily-sentinel-composite"
            and inner.get("one_life_terminal") is True
            and inner.get("one_life_terminal_reason") == "played_character_changed"):
        return None
    from xar_autoplayer.bridge.native_driver import (
        _validate_tactical_daily_sentinel_stop,
        _validate_tactical_daily_sentinel_decision_boundary,
    )
    from xar_autoplayer.bridge.route_contact_window_contract import (
        parse_advance_route_contact_window_step,
    )
    from xar_autoplayer.bridge.war_contract import (
        parse_battle_decision_epoch_advance_step,
        parse_committed_route_sentinel_advance_step,
        parse_committed_route_sentinel_advance_speed,
        parse_war_objective_hold_sentinel_advance_step,
        parse_war_objective_hold_sentinel_advance_speed,
    )
    step = body.get("selected_step")
    require(isinstance(plan, dict) and body.get("status") == "executed"
            and plan.get("selected_step") == inner.get("step") == step
            and inner.get("backend_id") == "native-headless"
            and inner.get("progress_status") == "postcondition"
            and inner.get("paused") is True
            and inner.get("managed_failure_cleanup") == {"attempted": False, "error": None}
            and isinstance(current_frame, dict) and isinstance(goal_anchor, dict),
            "natural sentinel does not have its executed typed boundary")
    start, end, target = (inner.get(k) for k in (
        "starting_date_raw", "ending_date_raw", "target_date_raw"))
    days, horizon, speed = (inner.get(k) for k in (
        "elapsed_days", "requested_horizon_days", "timeline_speed"))
    predecessor = goal_anchor.get("current_character_id")
    successor = inner.get("played_character_id")
    require(all(type(v) is int for v in (start, end, target, days, horizon, speed))
            and start == current_frame["date_raw"] and 0 <= days <= horizon <= 45
            and horizon > 0 and end - start == days * 24
            and target - start == horizon * 24 and end <= target
            and inner.get("starting_date") == {"date_raw": start}
            and inner.get("ending_date") == {"date_raw": end}
            and type(predecessor) is int and predecessor > 0
            and type(successor) is int and successor > 0 and successor != predecessor
            and inner.get("episode_character_id") == predecessor
            and inner.get("episode_run_id") == current_frame["episode_run_id"]
            and inner.get("played_character_alive") is True
            and inner.get("bridge_pid") == game_pid
            and type(inner.get("connection_generation")) is int
            and inner["connection_generation"] > 0
            and type(inner.get("revision")) is int and inner["revision"] >= 0
            and type(inner.get("native_revision")) is int and inner["native_revision"] > 0
            and inner.get("snapshot_id") == f"native:{inner['native_revision']}",
            "natural sentinel identity/date/goal binding differs")
    scope, mode = inner.get("sentinel_scope"), inner.get("sentinel_mode")
    if scope == "route_contact_window":
        parsed = parse_advance_route_contact_window_step(step)
        require(parsed is not None and parsed[3] == horizon and horizon <= 30
                and mode == "terminal_or_sentinel" and 1 <= speed <= 5,
                "route-window natural boundary has noncanonical terms")
    elif scope == "committed_route":
        parsed = parse_committed_route_sentinel_advance_step(step)
        require(parsed is not None and parsed[2] == target
                and parse_committed_route_sentinel_advance_speed(step) == speed == 3
                and mode == "decision_epoch", "committed natural boundary terms differ")
    elif scope == "active_battle":
        require(parse_battle_decision_epoch_advance_step(step) == target
                and speed == 3 and mode == "decision_epoch",
                "battle natural boundary terms differ")
    elif scope == "stationary_objective_hold":
        parsed = parse_war_objective_hold_sentinel_advance_step(step)
        require(parsed is not None and parsed[3] == target
                and parse_war_objective_hold_sentinel_advance_speed(step) == speed
                and (speed == 3 or (speed in (4, 5)
                    and plan.get("research_high_speed_ab") is True
                    and plan.get("timeline_speed") == speed
                    and plan.get("sentinel_scope") == scope
                    and plan.get("sentinel_mode") == mode
                    and plan.get("timeline_policy") == f"war_stationary_objective_hold_speed_{speed}"
                    and plan.get("absolute_target_date_raw") == target))
                and mode == "decision_epoch", "objective-hold natural boundary terms differ")
    else:
        raise ValueError("natural boundary is outside the existing sentinel families")
    require(inner.get("timeline_policy") == mode, "sentinel policy/mode differs")
    watch, arm, status = (inner.get(k) for k in (
        "watch_army_ids", "armed_tactical_daily_sentinel", "tactical_daily_sentinel"))
    allow_empty_watch = scope == "stationary_objective_hold" and parsed[1] == 0
    require(isinstance(watch, list) and (watch or allow_empty_watch)
            and all(type(v) is int and v > 0 for v in watch)
            and isinstance(arm, dict) and isinstance(status, dict)
            and type(arm.get("generation")) is int and arm["generation"] > 0,
            "original native arm/status identity unavailable")
    boundary = inner.get("player_decision_boundary")
    terms = dict(arm_status=arm, starting_date_raw=start, target_date_raw=target,
                 ending_date_raw=end, elapsed_days=days, speed=speed, mode=mode,
                 watch_army_ids=tuple(watch))
    if isinstance(boundary, dict):
        require(inner.get("stop_kind") == "player_decision",
                "typed player-decision stop identity differs")
        _validate_tactical_daily_sentinel_decision_boundary(
            status, **terms, player_decision_boundary=boundary,
            player_decision_boundary_cancel=inner.get("player_decision_boundary_cancel"))
    else:
        require(inner.get("stop_kind") == "terminal" and inner.get("terminal_reached") is True
                and status.get("terminal_observed") is True
                and inner.get("player_decision_boundary_cancel") is None,
                "natural terminal stop was not independently observed")
        _validate_tactical_daily_sentinel_stop(status, **terms)
    actions = inner.get("actions")
    require(isinstance(actions, list) and actions
            and all(isinstance(a, dict) and isinstance(a.get("result"), dict)
                    and a["result"].get("accepted") is True for a in actions),
            "original native clock actions are not all accepted")
    return {"schema": "g2.queue.ordinary-result-credit/v1",
            "selected_step": step, "category": "natural_succession_boundary_observed",
            "natural_succession_boundary_observed": True,
            "natural_boundary_end": {
                "date_raw": end, "actor_character_id": successor,
                "episode_run_id": inner["episode_run_id"],
                "native_revision": inner["native_revision"]},
            "actual_date_delta_raw": end - start, "actual_elapsed_days": days,
            "submitted_pending": False, "primitive_accepted": False,
            "business_success_inferred": False, "business_cycle_credit": 0,
            "paired_after_metrics_still_required": True,
            "replay_allowed": False}

