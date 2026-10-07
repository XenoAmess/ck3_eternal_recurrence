"""Source-next GLOBAL clock for the captured-stock supply budget getter.

This is a direct 24E32C0 numerical evaluation. It performs no stock updater,
physical loss, earlier-stage reconstruction or future observation.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_current_fleet_supply_tick_inputs_contract import normalize_current_fleet_supply_tick_inputs_v1
from .army_source_derived_next_daily_supply_frame_contract import normalize_source_derived_next_daily_supply_frame_inputs_v1
from .army_monthly_loss_budget_projection import _derive_supply_component


def _integer(value: object, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < (1 << (bits - 1))


def project_source_derived_next_fleet_supply_budget_v1(
    same_query_strength: Mapping[str, object],
) -> dict[str, object]:
    """Recompute signed Fleet suppression, then reuse the held-stock evaluator."""
    row = same_query_strength
    family = normalize_current_fleet_supply_tick_inputs_v1(row.get("current_fleet_supply_tick_inputs_v1"))
    future = normalize_source_derived_next_daily_supply_frame_inputs_v1(
        row.get("source_derived_next_daily_supply_frame_inputs_v1"),
        expected_army_id=row.get("army_id"), expected_carmy_id=row.get("native_carmy_id"))
    inputs = row.get("monthly_loss_budget_inputs_v1")
    inputs = inputs if isinstance(inputs, Mapping) else {}
    losses = row.get("loss_application_inputs_v1")
    losses = losses if isinstance(losses, Mapping) else {}
    stock = row.get("current_supply_raw")
    next_date = future.get("source_derived_next_date_raw_i32") if future else None
    bare_fleet = family.get("native_fleet_branch_applicable") if family else None
    fleet_day = family.get("fleet_day_raw") if family else None
    sentinel = family.get("loaded_fleet_day_sentinel_raw") if family else None
    result: dict[str, object] = {
        "schema_version": 1,
        "source": "same_input_conditional_source_derived_next_fleet_supply_budget",
        "status": "unavailable", "ready": False, "missing_inputs": [],
        "army_id": row.get("army_id"), "native_carmy_id": row.get("native_carmy_id"),
        "condition": "one direct 24E32C0 getter evaluation with source-derived next GLOBAL GameState low32 date and CURRENT captured stock/Fleet/commander/eligible-current inputs unchanged",
        "stock_basis": "captured_current_stock_unchanged",
        "post_updater_stock_used": False,
        "held_current_supply_stock_raw": stock,
        "observed_current_native_fleet_supply_loss_suppressed": inputs.get("native_fleet_supply_loss_suppressed"),
        "observed_current_supply_loss_budget_soldiers": losses.get("current_supply_loss_budget"),
        "source_next_global_clock": deepcopy(future),
        "source_next_global_date_raw_i32": next_date,
        "source_next_global_date_ready": _integer(next_date, 32),
        "native_fleet_branch_applicable": bare_fleet,
        "fleet_day_raw_i32": fleet_day, "loaded_fleet_day_sentinel_raw_i32": sentinel,
        "fleet_date_predicate_ready": False,
        "conditional_native_fleet_supply_loss_suppressed": None,
        "fleet_date_comparison": "signed_int32_strict_greater_than_global_date",
        "global_date_operand_used": False,
        "held_stock_state_index": None, "supply_base_fraction_raw": None,
        "supply_effective_fraction_raw": None,
        "conditional_supply_budget_ready": False,
        "conditional_supply_budget_soldiers": None,
        "earlier_stage_effects_reconstructed": False,
        "actual_future_date_stage_observed": False,
        "actual_future_callback_observed": False,
        "actual_future_supply_budget_observed": False,
        "future_supply_eligibility_ready": False,
        "future_stock_or_strength_ready": False,
        "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
    if row.get("status") != "available" or type(row.get("native_carmy_id")) is not int:
        result["missing_inputs"].append("available_typed_army_row")
        return result
    if family is None:
        result["missing_inputs"].append("current_fleet_supply_tick_inputs_v1")
        return result
    for key, row_key in (("subject_army_id", "army_id"), ("subject_carmy_id", "native_carmy_id")):
        if family[key] is not None and family[key] != row.get(row_key):
            raise ValueError(f"same-query next supply budget {key} differs")
    if type(bare_fleet) is not bool:
        result["missing_inputs"].append("current_fleet_supply_tick_inputs_v1.native_fleet_branch_applicable")
        return result
    if bare_fleet is False:
        suppressed = False
    else:
        absent = [key for key, value in (("fleet_day_raw", fleet_day),
                                         ("loaded_fleet_day_sentinel_raw", sentinel))
                  if not _integer(value, 32)]
        if absent:
            result["missing_inputs"].extend("current_fleet_supply_tick_inputs_v1." + key for key in absent)
            return result
        if fleet_day == sentinel:
            suppressed = False
        elif not _integer(next_date, 32):
            result["missing_inputs"].append("source_derived_next_daily_supply_frame_inputs_v1.source_derived_next_date_raw_i32")
            return result
        else:
            result["global_date_operand_used"] = True
            suppressed = fleet_day > next_date
    result.update(fleet_date_predicate_ready=True,
                  conditional_native_fleet_supply_loss_suppressed=suppressed)
    if suppressed:
        result.update(status="available", ready=True, conditional_supply_budget_ready=True,
                      conditional_supply_budget_soldiers=0)
        return result
    if not _integer(stock, 64):
        result.update(status="partial", missing_inputs=["current_supply_raw"])
        return result
    # The reused evaluator's argument name is legacy. Its seed is explicitly the
    # captured CURRENT stock here; no post-updater stock is constructed or tagged.
    kernel: dict[str, object] = {
        "conditional_post_supply_raw": stock, "missing_inputs": [],
        "supply_state_index": None, "supply_base_fraction_raw": None,
        "supply_effective_fraction_raw": None,
        "supply_budget_soldiers": None, "supply_budget_ready": False,
    }
    _derive_supply_component(kernel, inputs, losses)
    result.update(
        held_stock_state_index=kernel["supply_state_index"],
        supply_base_fraction_raw=kernel["supply_base_fraction_raw"],
        supply_effective_fraction_raw=kernel["supply_effective_fraction_raw"],
        conditional_supply_budget_ready=kernel["supply_budget_ready"],
        conditional_supply_budget_soldiers=kernel["supply_budget_soldiers"],
        ready=kernel["supply_budget_ready"],
        status="available" if kernel["supply_budget_ready"] else "partial",
        missing_inputs=list(dict.fromkeys(kernel["missing_inputs"])),
    )
    return result
