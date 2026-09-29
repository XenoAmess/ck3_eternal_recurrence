"""Narrow, source-backed Stage 5 value and budget gate for a generic feast.

This does not submit Start.  Rewards below are conditional on a successfully
completed feast; the caller must supply same-frame native legality, configured
costs, balances, existing commitments and a credible guest route.
"""

from __future__ import annotations

from collections.abc import Sequence


RESOURCE_KEYS = ("gold", "treasury", "piety", "barter_goods")
SCALE = 100_000


def assess_feast_stage5_start(
    *,
    activity_key: str,
    selected_option_key: str,
    planning_stage: int,
    final_can_start: bool | None,
    configured_cost_raw: Sequence[int | None],
    balance_available: Sequence[bool],
    balance_raw: Sequence[int],
    reserved_raw: Sequence[int],
    expected_nonhost_guest_count: int | None,
    peaceful_spend_allowed: bool | None,
    gold_floor_raw: int | None,
    active_war_count: int | None,
    war_cash_reserve_raw: int | None,
) -> dict[str, object]:
    """Assess only the fully configured generic feast and return one decision.

    ``reserved_raw`` counts already committed resources once.  ``gold_floor``
    is an independent peaceful cash floor, and ``war_cash_reserve`` is a
    separately assessed claim while a war is active.  Neither unknown is zero.
    ``expected_nonhost_guest_count`` is a caller-observed credible invite or
    attendance route, not a guarantee that those guests arrive.
    """
    costs = _cost_vector(configured_cost_raw)
    balances = _vector(balance_raw, "balance_raw")
    reserved = _vector(reserved_raw, "reserved_raw")
    available = _availability(balance_available)
    for name, value in (
        ("gold_floor_raw", gold_floor_raw),
        ("active_war_count", active_war_count),
        ("war_cash_reserve_raw", war_cash_reserve_raw),
        ("expected_nonhost_guest_count", expected_nonhost_guest_count),
    ):
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"{name} must be a nonnegative integer or None")
    if final_can_start is not None and type(final_can_start) is not bool:
        raise ValueError("final_can_start must be a native boolean or None")
    if peaceful_spend_allowed is not None and type(peaceful_spend_allowed) is not bool:
        raise ValueError("peaceful_spend_allowed must be a boolean or None")

    def result(
        reason: str, *, start: bool = False, missing_input: bool = False
    ) -> dict[str, object]:
        value_supported = (
            activity_key == "activity_feast"
            and selected_option_key == "feast_type_generic"
            and expected_nonhost_guest_count is not None
            and expected_nonhost_guest_count > 0
        )
        submit_reserve = list(reserved)
        if start and costs[0]:
            # These were required above before Start can be returned.
            if gold_floor_raw is None or active_war_count is None:
                raise RuntimeError("Start without observed Gold reserve")
            submit_reserve[0] += gold_floor_raw
            if active_war_count:
                if war_cash_reserve_raw is None:
                    raise RuntimeError("Start without observed war cash reserve")
                submit_reserve[0] += war_cash_reserve_raw
        return {
            "policy": "g2-feast-stage5-value-policy-v1",
            "decision": "start" if start else "hold",
            "status": "ready" if start else (
                "missing_input" if missing_input else "not_actionable"
            ),
            "reason": reason,
            "positive_value_supported": value_supported,
            "benefit_if_successful": (
                "scripted_prestige_and_reveler_progress_or_xp"
                if value_supported else None
            ),
            "resource_keys": list(RESOURCE_KEYS),
            "scale": SCALE,
            "configured_cost_raw": list(costs),
            "resource_commitment_raw": [int(cost) for cost in costs] if start else None,
            "submit_reserve_raw": submit_reserve if start else None,
        }

    if activity_key != "activity_feast" or selected_option_key != "feast_type_generic":
        return result("unsupported_activity_or_type")
    if planning_stage != 5:
        return result("not_final_planning_stage")
    if final_can_start is None:
        return result("native_final_start_unavailable", missing_input=True)
    if final_can_start is not True:
        return result("native_final_start_unavailable")
    if expected_nonhost_guest_count is None:
        return result("guest_route_unproven", missing_input=True)
    if expected_nonhost_guest_count == 0:
        return result("guest_route_unproven")
    if any(cost is None for cost in costs):
        return result("configured_cost_unobserved", missing_input=True)
    if peaceful_spend_allowed is None:
        return result("peaceful_spend_unapproved", missing_input=True)
    if peaceful_spend_allowed is not True:
        return result("peaceful_spend_unapproved")

    for index, cost in enumerate(costs):
        if cost == 0:
            continue
        if not available[index]:
            return result(f"{RESOURCE_KEYS[index]}_balance_unobserved", missing_input=True)
        needed = cost + reserved[index]
        if index == 0:
            if gold_floor_raw is None or active_war_count is None:
                return result("gold_reserve_unobserved", missing_input=True)
            needed += gold_floor_raw
            if active_war_count:
                if war_cash_reserve_raw is None:
                    return result("war_cash_reserve_unobserved", missing_input=True)
                needed += war_cash_reserve_raw
        if needed > balances[index]:
            return result(f"{RESOURCE_KEYS[index]}_budget_exceeded")
    return result("positive_feast_within_observed_budget", start=True)


def _cost_vector(value: Sequence[int | None]) -> tuple[int | None, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != len(RESOURCE_KEYS):
        raise ValueError("configured_cost_raw must have four named resources")
    if any(item is not None and (type(item) is not int or item < 0) for item in value):
        raise ValueError("configured_cost_raw must contain nonnegative values or None")
    return tuple(value)


def _vector(value: Sequence[int], name: str) -> tuple[int, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != len(RESOURCE_KEYS):
        raise ValueError(f"{name} must have four named resources")
    if any(type(item) is not int or item < 0 for item in value):
        raise ValueError(f"{name} must contain nonnegative integers")
    return tuple(value)


def _availability(value: Sequence[bool]) -> tuple[bool, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != len(RESOURCE_KEYS):
        raise ValueError("balance_available must have four named resources")
    if any(type(item) is not bool for item in value):
        raise ValueError("balance_available must contain booleans")
    return tuple(value)
