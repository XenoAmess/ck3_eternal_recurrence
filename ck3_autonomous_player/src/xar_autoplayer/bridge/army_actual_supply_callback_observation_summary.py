"""Measured natural callback stock movement, never future attrition or soldier loss."""

from __future__ import annotations

from collections.abc import Mapping


def summarize_actual_supply_callback_observations_v1(
    army: Mapping[str, object], *, after_sequence: int = 0,
) -> dict[str, object]:
    """Select retained actual matching events without treating empty history as zero loss."""
    if type(after_sequence) is not int or after_sequence < 0:
        raise ValueError("after_sequence must be a nonnegative sequence fence")
    family = army.get("actual_supply_callback_observations_v1")
    base: dict[str, object] = {
        "source": "retained_actual_natural_supply_callback_snapshots",
        "after_sequence": after_sequence,
        "supply_scale": 100_000,
        "actual_physical_soldier_loss_observed": False,
        "updater_admission_observed": False,
        "future_supply_projected": False,
        "full_monthly_execution_observed": False,
    }
    if not isinstance(family, Mapping):
        return {**base, "status": "unavailable", "reason": "observer_leaf_absent",
                "actual_callback_observed": False, "matching_event_count": 0,
                "complete_supply_event_count": 0, "partial_supply_event_count": 0,
                "sum_observed_supply_delta_raw": None,
                "sum_observed_supply_drain_raw": None, "latest_event": None,
                "events": []}
    events = []
    for event in family["events"]:
        if event["sequence"] <= after_sequence:
            continue
        before, after = event["before"], event["after"]
        stock_before, stock_after = before["supply_raw"], after["supply_raw"]
        measured = (event["same_instance_after"]
                    and stock_before is not None and stock_after is not None)
        delta = stock_after - stock_before if measured else None
        events.append({
            "sequence": event["sequence"],
            "army_id": event["army_id"], "native_carmy_id": event["native_carmy_id"],
            "passed_date_raw64": event["passed_date_raw64"],
            "caller_return_rva": event["caller_return_rva"],
            "supply_before_raw": stock_before, "supply_after_raw": stock_after,
            "supply_delta_raw": delta,
            "supply_drain_raw": max(-delta, 0) if measured else None,
            "last_supply_update_date_before_raw64": before["last_supply_update_date_raw64"],
            "last_supply_update_date_after_raw64": after["last_supply_update_date_raw64"],
            "supply_updated_byte_before_raw": before["supply_updated_byte_raw"],
            "supply_updated_byte_after_raw": after["supply_updated_byte_raw"],
            "same_instance_after": event["same_instance_after"],
            "capture_failure_flags": event["capture_failure_flags"],
            "stock_change_observed": measured,
        })
    measured_events = [event for event in events if event["stock_change_observed"]]
    return {
        **base, "status": "available",
        "observer_installed": family["observer_installed"],
        "oldest_available_sequence": family["oldest_available_sequence"],
        "latest_sequence": family["latest_sequence"],
        "overwritten_events": family["overwritten_events"],
        "unattributed_capture_failures": family["unattributed_capture_failures"],
        "actual_callback_observed": bool(events),
        "matching_event_count": len(events),
        "complete_supply_event_count": len(measured_events),
        "partial_supply_event_count": len(events) - len(measured_events),
        "sum_observed_supply_delta_raw": (
            sum(event["supply_delta_raw"] for event in measured_events)
            if measured_events else None),
        "sum_observed_supply_drain_raw": (
            sum(event["supply_drain_raw"] for event in measured_events)
            if measured_events else None),
        "latest_event": events[-1] if events else None,
        "events": events,
    }
