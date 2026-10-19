"""Run-scoped campaign clock caps; no native query or gameplay policy change."""
from __future__ import annotations

from bisect import bisect_right

from ..campaign_score_cadence_v1 import CALENDAR_PROFILE, date_to_raw, month_boundaries


def configure_v1(driver, *, campaign_id: str, start_date: str, start_date_raw: int, months: int = 360) -> dict:
    if (not isinstance(campaign_id, str) or not campaign_id
            or type(start_date_raw) is not int or date_to_raw(start_date) != start_date_raw):
        raise ValueError("campaign deadline requires its explicit actual founding date/raw identity")
    rows = month_boundaries(start_date, months)
    config = {"schema": "xar.ck3.campaign-clock-deadline/v1", "campaign_id": campaign_id,
              "calendar_profile": CALENDAR_PROFILE, "start_date": start_date,
              "start_date_raw": start_date_raw, "months": months,
              "endpoint_date_raw": rows[-1][1], "boundary_raws": tuple(row[1] for row in rows)}
    previous = getattr(driver, "_campaign_clock_deadline_v1", None)
    if previous is not None and previous != config:
        raise ValueError("a live driver cannot replace its founding campaign deadline")
    driver._campaign_clock_deadline_v1 = config
    return {key: value for key, value in config.items() if key != "boundary_raws"}


def deadline_v1(driver, starting: dict, proposed_target_raw: int) -> dict | None:
    config = getattr(driver, "_campaign_clock_deadline_v1", None)
    if config is None:
        return None
    current = starting.get("date_raw")
    if (type(current) is not int or current < config["start_date_raw"]
            or (current - config["start_date_raw"]) % 24 != 0
            or type(proposed_target_raw) is not int or proposed_target_raw <= current
            or (proposed_target_raw - current) % 24 != 0):
        raise ValueError("campaign clock cap lacks its actual whole-day starting frame")
    endpoint = config["endpoint_date_raw"]
    boundary = endpoint if current >= endpoint else config["boundary_raws"][bisect_right(config["boundary_raws"], current)]
    return {"schema": config["schema"], "campaign_id": config["campaign_id"],
            "calendar_profile": config["calendar_profile"], "starting_date_raw": current,
            "requested_target_date_raw": proposed_target_raw, "boundary_date_raw": boundary,
            "endpoint_date_raw": endpoint, "target_date_raw": min(proposed_target_raw, boundary),
            "status": "endpoint_reached" if current == endpoint else "endpoint_overshot" if current > endpoint else "advance",
            "policy_choices_changed": False}


def cap_plan_v1(driver, planned: dict) -> dict:
    """Shared PLAN/AUTO normalization before display and command dispatch."""
    if getattr(driver, "_campaign_clock_deadline_v1", None) is None:
        return planned
    from .war_contract import (
        BATTLE_DECISION_EPOCH_ADVANCE_STEP, BATTLE_TERMINAL_CRUISE_STEP,
        battle_decision_epoch_advance_step, committed_route_sentinel_advance_step,
        parse_battle_decision_epoch_advance_step, parse_committed_route_sentinel_advance_step,
        parse_committed_route_sentinel_advance_speed, parse_war_objective_hold_sentinel_advance_step,
        parse_war_objective_hold_sentinel_advance_speed, war_objective_hold_sentinel_advance_step,
    )
    from .route_contact_window_contract import parse_advance_route_contact_window_step, advance_route_contact_window_step
    plan = planned.get("plan")
    frame = planned.get("planning_source_frame")
    if not isinstance(plan, dict) or not isinstance(frame, dict):
        return planned
    step = plan.get("selected_step")
    prior = plan.get("campaign_deadline_v1")
    if (isinstance(prior, dict) and prior.get("campaign_id") == driver._campaign_clock_deadline_v1["campaign_id"]
            and prior.get("starting_date_raw") == frame.get("date_raw") and prior.get("effective_step") == step):
        return planned
    battle = parse_battle_decision_epoch_advance_step(step)
    route = parse_committed_route_sentinel_advance_step(step)
    hold = parse_war_objective_hold_sentinel_advance_step(step)
    window = parse_advance_route_contact_window_step(step)
    generic = step in {"life-advance", "life-advance-one-day", BATTLE_DECISION_EPOCH_ADVANCE_STEP, BATTLE_TERMINAL_CRUISE_STEP}
    if not (generic or battle is not None or route is not None or hold is not None or window is not None):
        return planned
    current = frame["date_raw"]
    requested = battle if battle is not None else route[2] if route else hold[3] if hold else current + window[3] * 24 if window else current + (45 if step in {BATTLE_DECISION_EPOCH_ADVANCE_STEP, BATTLE_TERMINAL_CRUISE_STEP} else 1) * 24
    cap = deadline_v1(driver, frame, requested)
    target = cap["target_date_raw"]
    updated = dict(plan)
    if cap["status"] != "advance":
        updated.update(selected_step=None, phase="campaign_score_endpoint_reached",
                       reason="the fixed campaign endpoint is already observed; no further clock advance")
    elif battle is not None:
        updated["selected_step"] = battle_decision_epoch_advance_step(target)
    elif route is not None:
        updated["selected_step"] = committed_route_sentinel_advance_step(route[0], route[1], target,
            timeline_speed=parse_committed_route_sentinel_advance_speed(step))
    elif hold is not None:
        updated["selected_step"] = war_objective_hold_sentinel_advance_step(*hold[:3], target,
            timeline_speed=parse_war_objective_hold_sentinel_advance_speed(step))
    elif window is not None:
        days = (target - current) // 24
        updated["selected_step"] = ("life-advance-one-day" if days == 1 else
            advance_route_contact_window_step(*window[:3], horizon_days=days))
    if target != requested:
        for key in ("absolute_target_date_raw", "target_date_raw"):
            if key in updated:
                updated[key] = target
    metadata = {**cap, "requested_step": step, "effective_step": updated.get("selected_step"),
                "maximum_target_date_raw": cap["boundary_date_raw"]}
    if step == "life-advance":
        # Its horizon is selected from the full paused frame in the Driver;
        # this public plan declares the maximum rather than inventing it.
        metadata.update(requested_target_date_raw=None, target_date_raw=None)
    updated["campaign_deadline_v1"] = metadata
    return {**planned, "plan": updated}


def endpoint_result_v1(starting: dict, result_step: str, cap: dict) -> dict:
    """No resume at the endpoint; nested Close receives an honest zero-day result."""
    raw = starting["date_raw"]
    return {"step": result_step, "backend_id": "native-headless", "source": "native-composite",
            "starting_date": {"date_raw": raw}, "ending_date": {"date_raw": raw},
            "starting_date_raw": raw, "ending_date_raw": raw, "elapsed_days": 0,
            "requested_horizon_days": 0, "progress_status": "campaign_endpoint_reached",
            "paused": starting.get("paused") is True, "actions": [],
            "snapshot_id": starting.get("snapshot_id"), "revision": starting.get("revision"),
            "campaign_deadline_v1": cap, "calendar_progress_verified": False,
            "business_success_inferred": False}
