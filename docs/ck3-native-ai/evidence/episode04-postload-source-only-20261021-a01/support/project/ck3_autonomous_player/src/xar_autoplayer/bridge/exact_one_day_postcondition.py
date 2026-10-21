"""Pure exact-day contract for two actually observed CK3 1.20.0.4 policies."""
from __future__ import annotations


def exact_day_postcondition(step: object, before: object, after: object) -> dict[str, object]:
    """Validate top-level composite AND independent later native snapshot.

    `ck3_execute_step(life-advance-one-day)` returns progress_status rather
    than top-level accepted. Its internal primitive ACKs are not the business
    result. Never infer a day from any one ACK or retry an unknown result.
    """
    if not all(isinstance(row, dict) for row in (step, before, after)):
        raise ValueError("actual step and independent before/after snapshots required")
    start = before.get("date_raw")
    end = after.get("date_raw")
    if type(start) is not int or type(end) is not int or end != start + 24:
        raise ValueError("independent native date is not exactly one day")
    # Both literals have independent native evidence: R203 battle/contact and
    # R206 William noncombat speed 5. No arbitrary policy string is accepted.
    actual_policy = step.get("timeline_policy")
    allowed_policies = (
        "exact_one_day_unavoidable_contact",
        "exact_one_day_noncombat_native_speed_5",
    )
    if type(actual_policy) is not str or actual_policy not in allowed_policies:
        raise ValueError("unreviewed exact-day timeline policy")
    expected = {
        "step": "life-advance-one-day",
        "backend_id": "native-headless",
        "source": "native-composite",
        "progress_status": "postcondition",
        "starting_date_raw": start,
        "ending_date_raw": end,
        "elapsed_days": 1,
        "requested_horizon_days": 1,
        "paused": True,
    }
    for key, want in expected.items():
        got = step.get(key)
        if type(got) is not type(want) or got != want:
            raise ValueError("composite exact-day postcondition differs: " + key)
    if before.get("paused") is not True or after.get("paused") is not True:
        raise ValueError("independent paused native map frame absent")
    if before.get("episode_run_id") != after.get("episode_run_id"):
        raise ValueError("independent episode changed")
    if before.get("map_ready") is not True or after.get("map_ready") is not True:
        raise ValueError("independent native map not ready")
    clock = step.get("exact_day_native_clock")
    if not isinstance(clock, dict):
        raise ValueError("native exact-day clock readback absent")
    stopped = clock.get("stopped")
    if not isinstance(stopped, dict):
        raise ValueError("native exact-day stopped readback absent")
    pins = {"state": "triggered", "starting_date_raw": start,
            "target_date_raw": end, "trigger_date_raw": end,
            "last_observed_date_raw": end, "completed_daily_ticks": 1,
            "overshoot_days": 0, "pause_observed": True,
            "abnormal": False}
    for key, want in pins.items():
        got = stopped.get(key)
        if type(got) is not type(want) or got != want:
            raise ValueError("native stopped clock differs: " + key)
    if stopped.get("trigger_reasons") != ["date_deadline"]:
        raise ValueError("native day trigger was not exact date deadline")
    return {"exact_day": True, "starting_date_raw": start,
            "ending_date_raw": end, "elapsed_days": 1,
            "actual_timeline_policy": actual_policy,
            "evidence_scope": "composite_postcondition_plus_independent_snapshot",
            "first_take_historical_RED_relabelled": False}
