"""Conditional current-Province LAND updater followed by its supply loss getter.

The source-closed Land rate uses original captured usage and loaded inputs.
Refill/target contexts remain separate, and captured capacity is held explicitly.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_current_province_supply_contributors_contract import normalize_current_province_supply_contributors_v1
from .army_full_land_supply_rate_projection import project_full_land_supply_rate_v1
from .army_monthly_loss_budget_projection import _i64, _integer
from .army_next_fleet_supply_budget_projection import _project_source_next_fleet_supply_budget_at_stock_v1
from .army_next_updater_write_projection import project_source_derived_next_updater_writes_v1


CONDITION = (
    "one source-ordered LAND supply callback for this CURRENT captured receiver at "
    "source-derived next passedDate and the same next GLOBAL GameState low32 date, "
    "with current Province/owner/commander, native usage/limit, captured capacity "
    "and all non-date rate/budget inputs unchanged after earlier Unit stages"
)


def project_source_derived_next_land_stock_supply_budget_v1(
    same_query_strength: Mapping[str, object],
) -> dict[str, object]:
    """Join original current-Province rate operands to conditional poststock."""
    row = same_query_strength
    writes = project_source_derived_next_updater_writes_v1(row)
    future = writes["source_next_date"]
    next_low = future.get("source_derived_next_date_raw_i32") if future else None
    admission = writes["next_admission"]
    admitted = admission["admitted"]
    stock, capacity = row.get("current_supply_raw"), row.get("current_supply_capacity_raw")
    raw_inputs = row.get("monthly_loss_budget_inputs_v1")
    inputs = raw_inputs if isinstance(raw_inputs, Mapping) else {}
    raw_losses = row.get("loss_application_inputs_v1")
    losses = raw_losses if isinstance(raw_losses, Mapping) else {}
    rate_stage: dict[str, object] = {
        "would_evaluate": admitted, "ready": False, "raw": None, "basis": None,
        "usage_basis": "captured_current_native_usage_unchanged",
        "native_usage_soldiers": None, "native_limit_soldiers": None,
        "conditional_refill_usage_used": False, "captured_target_context_used": False,
        "native_day_index_used": False, "full_land_rate_projection": None,
        "missing_inputs": [],
    }
    stock_stage: dict[str, object] = {
        "ready": False, "raw": None, "signed64_add_raw": None, "clamp_branch": None,
        "capacity_basis": "captured_current_capacity_unchanged",
        "actual_future_capacity_observed": False, "missing_inputs": [],
    }
    budget_stage: dict[str, object] = {
        "would_call": admitted, "call_predicate_ready": admission["ready"],
        "global_date_raw_i32": next_low, "fleet_date_predicate_ready": False,
        "suppression": None, "stock_basis": "conditional_post_updater_stock",
        "stock_raw": None, "state_index": None, "base_fraction_raw": None,
        "effective_fraction_raw": None, "ready": False, "soldiers": None,
        "missing_inputs": [],
    }
    result: dict[str, object] = {
        "schema_version": 1,
        "source": "same_input_conditional_source_derived_next_land_stock_supply_budget",
        "status": "unavailable", "ready": False, "missing_inputs": [],
        "army_id": row.get("army_id"), "native_carmy_id": row.get("native_carmy_id"),
        "condition": CONDITION, "callback_entry_is_conditional": True,
        "observed_current_stock_raw": stock,
        "observed_current_rate_raw": row.get("current_supply_change_monthly_raw"),
        "observed_current_capacity_raw": capacity,
        "observed_current_native_fleet_supply_loss_suppressed": inputs.get("native_fleet_supply_loss_suppressed"),
        "observed_current_budget_soldiers": losses.get("current_supply_loss_budget"),
        "source_next_date": deepcopy(future), "next_admission": deepcopy(admission),
        "conditional_pre_rate_writes": deepcopy(writes["conditional_writes"]),
        "ordered_pre_rate_writes_ready": writes["ready"],
        "conditional_rate": rate_stage, "conditional_post_updater_stock": stock_stage,
        "conditional_budget_getter": budget_stage,
        "earlier_stage_effects_reconstructed": False,
        "actual_future_date_stage_observed": False,
        "actual_future_callback_observed": False,
        "actual_future_rate_getter_observed": False,
        "actual_future_stock_observed": False,
        "actual_future_supply_budget_observed": False,
        "actual_physical_loss_observed": False,
        "future_stock_or_strength_ready": False,
        "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
    }
    missing = list(writes["missing_inputs"])
    if admitted is False:
        rate_stage["basis"] = "not_called_rejected_updater"
        if _integer(stock, 64):
            stock_stage.update(ready=True, raw=stock, clamp_branch="captured_stock_retained_rejected_updater")
        else:
            stock_stage["missing_inputs"].append("current_supply_raw")
        budget_stage.update(stock_basis="getter_not_called_rejected_updater", ready=True, soldiers=0)
    elif admitted is True:
        province = normalize_current_province_supply_contributors_v1(
            row.get("current_province_supply_contributors_v1"))
        if province is None:
            rate_stage["missing_inputs"].append("current_province_supply_contributors_v1")
        else:
            usage = province["native_supply_usage_soldiers"]
            rate_stage.update(native_usage_soldiers=usage,
                              native_limit_soldiers=province["native_supply_limit_soldiers"])
            if province["current_usage_ready"] is not True or not _integer(usage, 32):
                rate_stage["missing_inputs"].append("current_province_supply_contributors_v1.current_native_usage")
            else:
                # The kernel's selected_refill argument name is legacy. This
                # explicit value is ORIGINAL native usage; no refill is projected.
                rate = project_full_land_supply_rate_v1(row, selected_refill_usage_soldiers=usage)
                rate_stage["full_land_rate_projection"] = deepcopy(rate)
                rate_stage["missing_inputs"].extend(rate["missing_inputs"])
                if rate["full_land_rate_ready"]:
                    rate_stage.update(ready=True, raw=rate["conditional_full_land_rate_raw"],
                                      basis="same_query_land_numeric_kernel_at_captured_native_usage")
        if rate_stage["ready"]:
            if _integer(stock, 64):
                changed = _i64(stock + rate_stage["raw"])
                stock_stage["signed64_add_raw"] = changed
                if changed < 0:
                    stock_stage.update(ready=True, raw=0, clamp_branch="negative_wrapped_add_to_zero")
                elif _integer(capacity, 64):
                    stock_stage.update(ready=True, raw=min(changed, capacity), clamp_branch="min_changed_captured_capacity")
                else:
                    stock_stage["missing_inputs"].append("current_supply_capacity_raw")
            else:
                stock_stage["missing_inputs"].append("current_supply_raw")
        budget = _project_source_next_fleet_supply_budget_at_stock_v1(
            row, stock_stage["raw"], stock_basis="conditional_post_updater_stock",
            post_updater_stock_used=True, stock_input_name="conditional_post_updater_stock_raw")
        budget_stage.update(
            fleet_date_predicate_ready=budget["fleet_date_predicate_ready"],
            suppression=budget["conditional_native_fleet_supply_loss_suppressed"],
            stock_raw=stock_stage["raw"], state_index=budget["held_stock_state_index"],
            base_fraction_raw=budget["supply_base_fraction_raw"],
            effective_fraction_raw=budget["supply_effective_fraction_raw"],
            ready=budget["conditional_supply_budget_ready"],
            soldiers=budget["conditional_supply_budget_soldiers"],
            missing_inputs=list(budget["missing_inputs"]))
    for stage in (rate_stage, stock_stage, budget_stage):
        missing.extend(stage["missing_inputs"])
    ready = (writes["ready"] and admission["ready"] and stock_stage["ready"]
             and budget_stage["ready"] and (admitted is False or rate_stage["ready"]))
    result.update(ready=bool(ready), status="available" if ready else (
        "partial" if row.get("status") == "available" else "unavailable"),
        missing_inputs=list(dict.fromkeys(missing)))
    return result
