"""Conditional full land rate from one current query and explicit refill usage.

This is24E51A0's current Province numeric branch, without monthly dispatch.
"""
from __future__ import annotations

from collections.abc import Mapping
from .army_current_land_supply_rate_contract import (
    normalize_current_land_supply_rate_inputs_v1, _integer,
)
from .army_current_land_resupply_contract import normalize_current_land_resupply_v1
from .army_current_province_supply_contributors_contract import (
    normalize_current_province_supply_contributors_v1,
)
from .army_monthly_loss_budget_projection import (
    _supply_component_product as _native_fixed_mul,
)

Q = 100000


def _wrap64(value: int) -> int:
    return (value + (1 << 63)) % (1 << 64) - (1 << 63)


def _trunc0(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def _native_fixed_div(value: int, divisor: int) -> tuple[int, str]:
    """24E6129..61CE, including zero DWORD quotient and signed abs/wrap semantics."""
    if divisor == 0:
        return 4294967295, "zero_divisor_positive_u32_max"
    if -0x53E2D6238DA3 <= value <= 0x53E2D6238DA3:
        return _trunc0(_wrap64(value * Q), divisor), "fast"
    if _wrap64(abs(divisor)) >= Q * Q:
        return _trunc0(value, _trunc0(divisor, Q)), "wide_divisor"
    quotient = _trunc0(value, Q)
    remainder = _wrap64(value - _wrap64(quotient * Q))
    whole = _wrap64(quotient * Q)
    qa = _trunc0(whole, divisor)
    ra = _wrap64(whole - qa * divisor)
    result = _wrap64(_wrap64(qa * Q)
                     + _trunc0(_wrap64(ra * Q), divisor)
                     + _trunc0(_wrap64(remainder * Q), divisor))
    return result, "decomposed"


def project_full_land_supply_rate_v1(
    same_query_strength: Mapping[str, object], *, selected_refill_usage_soldiers: int,
) -> dict[str, object]:
    """Change only explicit usage in the captured owner/Province/commander context.

    Caller supplies its selected-refill projection; no actual after stage is
    observed. Native limit and all raw rate/admission operands come from the
    same Strength row. Current total rate remains an independent observation.
    """
    if _integer(selected_refill_usage_soldiers, 32, "selected_refill_usage_soldiers") is None:
        raise ValueError("explicit selected-refill usage is required")
    result = {
        "source": "conditional_same_context_full_land_supply_rate",
        "status": "unavailable", "full_land_rate_ready": False,
        "selected_refill_usage_soldiers": selected_refill_usage_soldiers,
        "native_limit_soldiers": None, "conditional_full_land_rate_raw": None,
        "current_observed_total_rate_raw": same_query_strength.get("current_supply_change_monthly_raw"),
        "province_component_raw": None, "excess_loss_raw": None,
        "gain_component_raw": None, "local_component_before_adjustment_raw": None,
        "local_component_after_adjustment_raw": None, "commander_divisor_raw": None,
        "division_path": None, "scale": Q,
        "actual_after": False, "actual_post_stage_observed": False,
        "full_monthly_supply_change_ready": False, "missing_inputs": [],
    }
    inputs = normalize_current_land_supply_rate_inputs_v1(
        same_query_strength.get("current_land_supply_rate_inputs_v1"))
    gain = normalize_current_land_resupply_v1(same_query_strength.get("current_land_resupply_v1"))
    province = normalize_current_province_supply_contributors_v1(
        same_query_strength.get("current_province_supply_contributors_v1"))
    if same_query_strength.get("status") != "available":
        result["missing_inputs"].append("available_same_query_strength")
    for name, family in (("current_land_supply_rate_inputs_v1", inputs),
                         ("current_land_resupply_v1", gain)):
        if family is None or not family["current_observation_ready"]:
            result["missing_inputs"].append(name)
    if province is None or province["native_supply_limit_soldiers"] is None:
        result["missing_inputs"].append("current_province_native_limit")
    if result["missing_inputs"]:
        return result
    for field in ("province_id", "owner_character_id"):
        if inputs[field] != gain[field] or inputs[field] != province[field]:
            raise ValueError(f"same-query land rate {field} context differs")
    for field, row_field in (("subject_army_id", "army_id"), ("subject_carmy_id", "native_carmy_id")):
        if inputs[field] != province[field] or inputs[field] != same_query_strength.get(row_field):
            raise ValueError(f"same-query land rate {field} context differs")
    limit = province["native_supply_limit_soldiers"]
    p = inputs["province_component_raw"]
    loss, g = 0, 0
    if selected_refill_usage_soldiers > limit:
        candidate = _native_fixed_mul((selected_refill_usage_soldiers - limit) * Q,
                                      inputs["loaded_excess_slope_raw"])
        loss = (inputs["loaded_min_loss_raw"] if candidate < inputs["loaded_min_loss_raw"]
                else min(candidate, inputs["loaded_max_loss_raw"]))
    elif gain["native_resupply_eligible"]:
        g = gain["loaded_gain_raw"]
    local = _wrap64(p - loss)
    adjusted, divisor, path = local, None, "not_negative"
    if local < 0:
        divisor = max(inputs["loaded_divisor_floor_raw"],
                      _wrap64(Q + inputs["commander_modifier_1a9_raw"]))
        divided, path = _native_fixed_div(local, divisor)
        adjusted = max(divided, _wrap64(-inputs["loaded_max_loss_raw"]))
    result.update(status="available", full_land_rate_ready=True,
                  native_limit_soldiers=limit, conditional_full_land_rate_raw=_wrap64(g + adjusted),
                  province_component_raw=p, excess_loss_raw=loss, gain_component_raw=g,
                  local_component_before_adjustment_raw=local,
                  local_component_after_adjustment_raw=adjusted,
                  commander_divisor_raw=divisor, division_path=path)
    return result
