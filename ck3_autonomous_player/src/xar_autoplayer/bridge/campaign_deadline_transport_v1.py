"""Multi-day native date-only clock using the existing single sentinel slot.

Separate from exact_one_day: no new speed, battle or route qualification.
"""
from __future__ import annotations


def advance_campaign_deadline_v1(driver, starting: dict, *, target_date_raw: int, speed: int, actions: list) -> tuple[dict, dict]:
    from . import native_driver as n
    start = n._date_raw(starting, "campaign-deadline starting snapshot")
    if (starting.get("paused") is not True or type(target_date_raw) is not int
            or not 24 <= target_date_raw - start <= 45 * 24 or (target_date_raw - start) % 24):
        raise n.BridgeUnavailableError("campaign deadline requires a paused 1..45 whole-day slice")
    arm_step = f"{n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX}{start}-to-{target_date_raw}-speed-{speed}-mode-terminal-a-0"
    arm = None
    current = starting
    cancel = None
    cancel_submitted = False
    try:
        speed_step = f"set-speed-{speed}"
        result = driver._execute_composite_primitive(speed_step, current)
        actions.append({"step": speed_step, "result": result})
        current = driver._wait_for_life_advance_snapshot(driver.take_internal_semantic_snapshot(),
            lambda value: value.get("speed") == speed, timeout_seconds=driver.command_timeout_seconds)
        if current.get("speed") != speed:
            raise n.BridgeUnavailableError("campaign deadline did not observe the original policy speed")
        result = driver._execute_primitive_step(arm_step, expected_revision=None,
            required_capability=n._TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY, internal_semantic_snapshot=True)
        actions.append({"step": arm_step, "result": result})
        arm = n._normalize_tactical_daily_sentinel_status(result.get("tactical_daily_sentinel"))
        n._validate_tactical_daily_sentinel_arm(result, arm, arm_step=arm_step, starting_date_raw=start,
            target_date_raw=target_date_raw, speed=speed, mode="terminal_or_sentinel", watch_army_ids=(),
            sentinel_scope="campaign_date_deadline")
        current = driver._resume_life_advance(current, actions, native_stop_target_date_raw=target_date_raw)
        current = driver._wait_for_life_advance_snapshot(current,
            lambda value: value.get("paused") is True or n._life_advance_new_modal_hint(value, starting) is not None,
            timeout_seconds=driver.life_advance_timeout_seconds)
        if current.get("paused") is not True:
            current = driver._pause_life_advance(current, actions)
        if current.get("paused") is not True:
            raise n.BridgeUnavailableError("campaign native deadline did not stop the map")
        end = n._date_raw(current, "campaign-deadline ending snapshot")
        if not start <= end <= target_date_raw or (end - start) % 24:
            raise n.BridgeUnavailableError("campaign native deadline overshot or changed its native day clock")
        status_result = driver._execute_primitive_step(n._TACTICAL_DAILY_SENTINEL_STATUS_STEP,
            expected_revision=None, required_capability=n._TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY,
            internal_semantic_snapshot=True)
        actions.append({"step": n._TACTICAL_DAILY_SENTINEL_STATUS_STEP, "result": status_result})
        status = n._normalize_tactical_daily_sentinel_status(status_result.get("tactical_daily_sentinel"))
        if status.get("state") == "armed" and end < target_date_raw:
            # A real modal may pause before the daily callback, including zero
            # elapsed days. The same native generation must be cancelled.
            if not n._life_advance_progressed(current, starting):
                raise n.BridgeUnavailableError("campaign date-only clock stopped without a lawful observed boundary")
            if (status.get("generation") != arm["generation"]
                    or status.get("starting_date_raw") != start or status.get("target_date_raw") != target_date_raw
                    or status.get("speed") != speed or status.get("army_count") != 0):
                raise n.BridgeUnavailableError("campaign early-boundary sentinel identity changed")
            cancel_step = f"{n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX}{arm['generation']}"
            cancel_submitted = True
            cancel = driver._execute_primitive_step(cancel_step, expected_revision=None,
                required_capability=n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY, internal_semantic_snapshot=True)
            actions.append({"step": cancel_step, "result": cancel})
            if cancel.get("step") != cancel_step or cancel.get("accepted") is not True or cancel.get("status") != "canceled":
                raise n.BridgeUnavailableError("campaign early-boundary sentinel cancellation is unconfirmed")
            fresh = driver.take_internal_semantic_snapshot()
            if fresh.get("paused") is not True or fresh.get("date_raw") != end:
                raise n.BridgeUnavailableError("campaign early boundary changed after cancel")
            current = fresh
        else:
            n._validate_tactical_daily_sentinel_stop(status, arm_status=arm,
                starting_date_raw=start, target_date_raw=target_date_raw, ending_date_raw=end,
                elapsed_days=(end-start)//24, speed=speed, mode="terminal_or_sentinel", watch_army_ids=())
        return current, {"schema": "xar.ck3.campaign-native-date-clock/v1", "scope": "campaign_date_deadline",
                         "starting_date_raw": start, "target_date_raw": target_date_raw,
                         "armed": arm, "stopped": status, "early_boundary_cancel": cancel,
                         "exact_one_day_qualification_claimed": False}
    except Exception:
        try:
            driver._pause_life_advance(driver.take_internal_semantic_snapshot(), actions)
            if arm is not None and not cancel_submitted:
                driver._execute_primitive_step(f"{n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX}{arm['generation']}",
                    expected_revision=None, required_capability=n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY,
                    internal_semantic_snapshot=True)
        except Exception:
            pass
        raise
