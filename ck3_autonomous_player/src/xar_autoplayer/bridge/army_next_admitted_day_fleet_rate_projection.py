"""Candidate conditional fleet scalar after replacing only low32 date with +24U.

Current bucket/grace/updater admission, preparation and actual next callback
remain separate. This module has not been executed or qualified.
"""
from __future__ import annotations

from collections.abc import Mapping
from .army_current_fleet_supply_tick_inputs_contract import normalize_current_fleet_supply_tick_inputs_v1
from .army_full_land_supply_rate_projection import _native_fixed_div, _wrap64


def project_next_admitted_day_fleet_rate_v1(same_query_strength: Mapping[str, object]) -> dict[str, object]:
    result = {
        "source": "conditional_same_context_next_admitted_day_fleet_rate",
        "status": "unavailable", "conditional_fleet_rate_ready": False,
        "current_native_date_low32": None, "conditional_next_date_low32": None,
        "conditional_full_fleet_rate_raw": None, "fleet_date_admitted": None,
        "branch": None, "division_path": None, "commander_divisor_raw": None,
        "current_observed_total_rate_raw": same_query_strength.get("current_supply_change_monthly_raw"),
        "scale": 100000, "actual_next_callback_ready": False,
        "actual_after": False, "actual_post_stage_observed": False,
        "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
        "fixed_context": ["same Fleet association", "same Province/terrain", "same commander/fallback",
                          "same loaded slots/modifier context"],
        "missing_inputs": [],
    }
    family = normalize_current_fleet_supply_tick_inputs_v1(
        same_query_strength.get("current_fleet_supply_tick_inputs_v1"))
    if same_query_strength.get("status") != "available":
        result["missing_inputs"].append("available_same_query_strength")
        return result
    if family is None:
        result["missing_inputs"].append("current_fleet_supply_tick_inputs_v1")
        return result
    for field, row_field in (("subject_army_id", "army_id"), ("subject_carmy_id", "native_carmy_id")):
        if family[field] is not None and family[field] != same_query_strength.get(row_field):
            raise ValueError(f"same-query fleet rate {field} context differs")
    if family["native_fleet_branch_applicable"] is False:
        result.update(status="not_fleet", branch="native_not_fleet")
        return result

    def need(*keys: str) -> bool:
        missing = [key for key in keys if family[key] is None]
        result["missing_inputs"].extend(missing)
        return not missing

    def ready(raw: int, branch: str) -> dict[str, object]:
        result.update(status="available", conditional_fleet_rate_ready=True,
                      conditional_full_fleet_rate_raw=raw, branch=branch)
        return result

    if not need("native_fleet_branch_applicable", "current_native_date_low32",
                "fleet_day_raw", "loaded_fleet_day_sentinel_raw"):
        return result
    current = family["current_native_date_low32"]
    next_date = ((current + 24 + (1 << 31)) % (1 << 32)) - (1 << 31)
    result.update(current_native_date_low32=current, conditional_next_date_low32=next_date)
    admitted = (family["fleet_day_raw"] == family["loaded_fleet_day_sentinel_raw"]
                or family["fleet_day_raw"] <= next_date)
    result["fleet_date_admitted"] = admitted
    if not admitted:
        return ready(0, "future_fleet_date")
    if not need("terrain_magic_38_raw"):
        return result
    if family["terrain_magic_38_raw"] != 0x4744624F:
        return ready(0, "terrain_not_gdbo")
    if not need("terrain_modifier_772_id", "terrain_modifier_772_raw"):
        return result
    if family["terrain_modifier_772_raw"] > 0:
        return ready(0, "positive_terrain772_modifier")
    if not need("loaded_fleet_loss_raw"):
        return result
    component = _wrap64(-family["loaded_fleet_loss_raw"])
    if component >= 0:
        result["division_path"] = "not_negative"
        return ready(component, "nonnegative_base_component")
    if not need("commander_modifier_1a9_raw", "loaded_divisor_floor_raw", "loaded_max_loss_raw"):
        return result
    divisor = max(family["loaded_divisor_floor_raw"], _wrap64(100000 + family["commander_modifier_1a9_raw"]))
    if divisor == 0:
        divided, path = 4294967295, "fleet_zero_divisor_positive_u32_max"
    else:
        divided, path = _native_fixed_div(component, divisor)
    result.update(commander_divisor_raw=divisor, division_path=path)
    return ready(max(divided, _wrap64(-family["loaded_max_loss_raw"])), "negative_base_adjusted")
