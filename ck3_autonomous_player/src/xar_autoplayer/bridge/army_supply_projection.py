"""Pure supply diagnosis for a frozen native rate and current capacity.

One event is one successful 1.20.0.3 supply-rate application, not a day or
calendar month. The stock-state table is the installed stock-data scenario;
the model does not predict the final native attrition getter or casualties.
"""

from typing import Any

SCALE = 100000
STOCK_SUPPLY_LEVELS = (60, 10, 0)
STOCK_BASE_ATTRITION_RAW = (0, 0, 5000)


def _stock_state(stock_raw: int) -> dict[str, int]:
    units = abs(stock_raw) // SCALE
    if stock_raw < 0:
        units = -units
    index = len(STOCK_SUPPLY_LEVELS) - 1
    for candidate, threshold in enumerate(STOCK_SUPPLY_LEVELS):
        if units >= threshold:
            index = candidate
            break
    return {
        "stock_integer_supplies": units,
        "stock_data_state_index": index,
        "stock_data_base_attrition_raw": STOCK_BASE_ATTRITION_RAW[index],
    }


def diagnose_frozen_supply(
    *,
    stock_raw: int,
    capacity_raw: int,
    monthly_change_raw: int,
    observed_current_attrition_raw: int | None = None,
    loss_application_inputs_v1: dict[str, Any] | None = None,
    army_update_clock_v1: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return conditional stock milestones without a calendar conversion.

    Raw fields use Q100000. Native stock and capacity are caller-provided
    observations. Each hypothetical successful update applies this same
    signed rate once and clamps to the same capacity. Current attrition is
    retained as an independent observation, never derived from the rate.
    Optional inputs and clock are the normalized readonly native query outputs.
    Loss budgets are preserved as observations, not recomputed from the UI
    attrition fraction or converted into future net soldier changes.
    """
    first_stock = max(0, min(capacity_raw, stock_raw + monthly_change_raw))

    def events_until_at_most(maximum_raw: int) -> int | None:
        if stock_raw <= maximum_raw:
            return 0
        if first_stock <= maximum_raw:
            return 1
        if monthly_change_raw >= 0:
            return None
        decline = -monthly_change_raw
        remaining = first_stock - maximum_raw
        return 1 + (remaining + decline - 1) // decline

    def stock_after(events: int) -> int:
        if events == 0:
            return stock_raw
        return max(0, min(capacity_raw, first_stock + (events - 1) * monthly_change_raw))

    milestones: dict[str, dict[str, int | None]] = {}
    for name, maximum_raw in (
        ("below_60_supplies", 60 * SCALE - 1),
        ("below_10_supplies", 10 * SCALE - 1),
        ("zero_supplies", 0),
    ):
        events = events_until_at_most(maximum_raw)
        entry: dict[str, int | None] = {"successful_update_events": events, "stock_raw": None}
        if events is not None:
            projected_stock = stock_after(events)
            entry["stock_raw"] = projected_stock
            entry.update(_stock_state(projected_stock))
        milestones[name] = entry

    result = {
        "model": "frozen native successful-update recurrence",
        "scale": SCALE,
        "stock_raw": stock_raw,
        "capacity_raw": capacity_raw,
        "frozen_monthly_change_raw": monthly_change_raw,
        "stock_after_one_successful_update_raw": first_stock,
        "stock_data_state": _stock_state(stock_raw),
        "state_table_basis": "installed stock data; runtime loaded vectors not observed by this model",
        "milestones": milestones,
        "observed_current_attrition_raw": observed_current_attrition_raw,
        "projected_final_native_attrition_raw": None,
        "projected_casualties": None,
        "elapsed_days": None,
        "depletion_date_raw": None,
        "clock_basis": "actual upstream cadence/grace inputs are not mapped; no conversion from events to days",
    }
    if loss_application_inputs_v1 is not None:
        result["loss_application_inputs_v1"] = dict(loss_application_inputs_v1)
    if army_update_clock_v1 is not None:
        result["army_update_clock_v1"] = dict(army_update_clock_v1)
        result["clock_basis"] = "observed native army update clock; no conversion into future net losses"
    return result
