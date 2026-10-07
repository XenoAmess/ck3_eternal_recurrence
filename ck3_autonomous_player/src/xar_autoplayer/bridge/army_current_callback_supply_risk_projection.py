"""Current-context supply risk at the source-closed 1.20.0.4 callback entrance.

Observed fields stay separate from the conditional one-entry result. No calendar,
earlier manager stage, writer or future context is executed or reconstructed.
"""
from __future__ import annotations

from collections.abc import Mapping

from .army_monthly_loss_budget_projection import (
    SCALE, _derive_supply_component, _i32, _i64, _integer, _trunc0,
)


def _stock_state(stock: object, inputs: Mapping[str, object]) -> dict[str, object]:
    state = {"ready": False, "stock_integer": None, "state_index": None,
             "base_fraction_raw": None, "missing_inputs": []}
    if not _integer(stock, 64):
        state["missing_inputs"].append("current_or_conditional_supply_raw")
        return state
    levels = inputs.get("loaded_supply_state_levels")
    if not isinstance(levels, list) or any(not _integer(value, 32) for value in levels):
        state["missing_inputs"].append("loaded_supply_state_levels")
        return state
    integer = _i32(_trunc0(stock, SCALE))
    index = next((i for i, level in enumerate(levels) if integer >= level), len(levels) - 1)
    state.update(stock_integer=integer, state_index=index)
    if index < 0:
        base = 0
    else:
        fractions = inputs.get("loaded_supply_state_fractions_raw")
        if not isinstance(fractions, list) or any(not _integer(value, 64) for value in fractions):
            state["missing_inputs"].append("loaded_supply_state_fractions_raw")
            return state
        base = fractions[index] if index < len(fractions) else 0
    state.update(ready=True, base_fraction_raw=base)
    return state


def project_current_callback_supply_risk_v1(army: Mapping[str, object]) -> dict[str, object]:
    """Use captured current inputs if one 24E3410 entry receives that same frame.

    This supply-only seam has its own readiness. A known rejected callback or
    suppressed/zero component needs no unused rate, table or eligible count.
    Selected bucket repeats are observations, not repeated copies of one budget.
    """
    raw_inputs = army.get("monthly_loss_budget_inputs_v1")
    inputs = raw_inputs if isinstance(raw_inputs, Mapping) else {}
    raw_losses = army.get("loss_application_inputs_v1")
    losses = raw_losses if isinstance(raw_losses, Mapping) else {}
    raw_clock = army.get("army_update_clock_v1")
    clock = raw_clock if isinstance(raw_clock, Mapping) else {}
    raw_dispatch = army.get("current_daily_supply_dispatch_inputs_v1")
    dispatch = raw_dispatch if isinstance(raw_dispatch, Mapping) else {}
    stock = army.get("current_supply_raw")
    current_state = _stock_state(stock, inputs)
    dispatch_ready = dispatch.get("ready") is True
    occurrences = dispatch.get("subject_dispatch_occurrence_count") if dispatch_ready else None
    result = {
        "schema_version": 1,
        "source": "same_input_conditional_current_supply_callback_risk",
        "source_contract_game_version": "1.20.0.4",
        "input_basis": "captured_current_context_before_one_native_supply_callback_entry",
        "status": "unavailable", "ready": False,
        "current_context_callback_values_ready": False,
        "scale": SCALE,
        "observed_current_supply_raw": stock,
        "observed_current_supply_capacity_raw": army.get("current_supply_capacity_raw"),
        "observed_current_supply_change_monthly_raw": army.get("current_supply_change_monthly_raw"),
        "observed_current_attrition_fraction_raw": army.get("current_attrition_fraction_raw"),
        "observed_current_supply_loss_budget_soldiers": losses.get("current_supply_loss_budget"),
        "observed_current_stock_state": current_state,
        "observed_current_date_raw": clock.get("current_date_raw"),
        "observed_last_supply_update_date_raw64": clock.get("last_supply_update_date_storage_raw64"),
        "observed_selected_bucket_ready": dispatch_ready,
        "observed_selected_bucket_phase": dispatch.get("selected_bucket_phase") if dispatch_ready else None,
        "observed_subject_callback_occurrences": occurrences,
        "observed_subject_callback_positions": list(dispatch.get("subject_occurrence_indices", [])) if dispatch_ready else None,
        "observed_current_day_callback_selected": occurrences > 0 if type(occurrences) is int else None,
        "admission_ready": False, "conditional_callback_admitted": None,
        "admission_witnesses": [], "admission_rejection": None,
        "conditional_post_stock_ready": False, "conditional_post_stock_raw": None,
        "conditional_post_stock_state": None,
        "conditional_supply_effective_fraction_raw": None,
        "conditional_supply_budget_ready": False, "conditional_supply_budget_soldiers": None,
        "conditional_positive_supply_budget": None,
        "conditional_enters_positive_supply_base_state": None,
        "missing_inputs": [],
        "actual_callback_observed": False, "actual_supply_update_observed": False,
        "actual_loss": False, "actual_post_stage_supply_raw": None,
        "actual_post_stage_current": None, "earlier_stage_outputs_reconstructed": False,
        "future_callback_selection_ready": False, "future_date_or_day_derived": False,
        "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
    }
    missing = result["missing_inputs"]
    if army.get("status") != "available":
        missing.append("available_same_query_army_strength")
        return result

    def admit() -> bool | None:
        for key, bits, passes in (
            ("unit_native_170_raw", 32, lambda value: value != 3),
            ("native_unit_in_combat", None, lambda value: not value),
            ("native_unit_gathering", None, lambda value: not value),
            ("army_gathering_count_raw", 32, lambda value: value == 0),
        ):
            value = inputs.get(key)
            valid = type(value) is bool if bits is None else _integer(value, bits)
            passed = passes(value) if valid else None
            result["admission_witnesses"].append({"input": key, "value": value, "passed": passed})
            if not valid:
                missing.append(key)
                return None
            if not passed:
                result["admission_rejection"] = key
                return False
        keys = ("current_date_raw", "grace_anchor_date_raw", "loaded_grace_days")
        absent = [key for key in keys if not _integer(clock.get(key), 32)]
        if absent:
            missing.extend(absent)
            return None
        elapsed = _i32(clock["current_date_raw"] - clock["grace_anchor_date_raw"])
        days = _trunc0(elapsed, 24)
        passed = days > clock["loaded_grace_days"]
        result["admission_witnesses"].append({
            "input": "native_grace_strict_greater", "elapsed_date_raw": elapsed,
            "elapsed_days": days, "loaded_grace_days": clock["loaded_grace_days"], "passed": passed})
        if not passed:
            result["admission_rejection"] = "native_grace_strict_greater"
        return passed

    admitted = admit()
    result.update(admission_ready=admitted is not None, conditional_callback_admitted=admitted)
    if admitted is False:
        if _integer(stock, 64):
            result.update(conditional_post_stock_ready=True, conditional_post_stock_raw=stock)
        else:
            missing.append("current_supply_raw")
        result.update(conditional_supply_budget_ready=True, conditional_supply_budget_soldiers=0)
    elif admitted is True:
        rate = army.get("current_supply_change_monthly_raw")
        capacity = army.get("current_supply_capacity_raw")
        if _integer(stock, 64) and _integer(rate, 64):
            changed = _i64(stock + rate)
            if changed < 0:
                result.update(conditional_post_stock_ready=True, conditional_post_stock_raw=0)
            elif _integer(capacity, 64):
                result.update(conditional_post_stock_ready=True, conditional_post_stock_raw=min(changed, capacity))
            else:
                missing.append("current_supply_capacity_raw")
        else:
            missing.extend(key for key, value in (
                ("current_supply_raw", stock), ("current_supply_change_monthly_raw", rate)
            ) if not _integer(value, 64))
        suppressed = inputs.get("native_fleet_supply_loss_suppressed")
        if suppressed is True:
            result.update(conditional_supply_budget_ready=True, conditional_supply_budget_soldiers=0)
        elif suppressed is not False:
            missing.append("native_fleet_supply_loss_suppressed")
        elif result["conditional_post_stock_ready"]:
            derived = {"conditional_post_supply_raw": result["conditional_post_stock_raw"],
                       "missing_inputs": [], "supply_budget_ready": False,
                       "supply_budget_soldiers": None, "supply_effective_fraction_raw": None}
            _derive_supply_component(derived, inputs, losses)
            missing.extend(derived["missing_inputs"])
            result.update(conditional_supply_budget_ready=derived["supply_budget_ready"],
                          conditional_supply_budget_soldiers=derived["supply_budget_soldiers"],
                          conditional_supply_effective_fraction_raw=derived["supply_effective_fraction_raw"])
    if result["conditional_post_stock_ready"]:
        post_state = _stock_state(result["conditional_post_stock_raw"], inputs)
        result["conditional_post_stock_state"] = post_state
        if current_state["ready"] and post_state["ready"]:
            result["conditional_enters_positive_supply_base_state"] = (
                current_state["base_fraction_raw"] <= 0 < post_state["base_fraction_raw"])
    if result["conditional_supply_budget_ready"]:
        result["conditional_positive_supply_budget"] = result["conditional_supply_budget_soldiers"] > 0
    ready = (result["admission_ready"] and result["conditional_post_stock_ready"]
             and result["conditional_supply_budget_ready"])
    result.update(ready=ready, current_context_callback_values_ready=ready,
                  status="available" if ready else "partial" if (
                      result["admission_ready"] or current_state["ready"] or _integer(stock, 64)
                  ) else "unavailable", missing_inputs=list(dict.fromkeys(missing)))
    return result
