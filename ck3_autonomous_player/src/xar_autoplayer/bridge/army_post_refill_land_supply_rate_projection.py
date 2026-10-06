"""Compose qualified current Province refill usage and full land rate kernels."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from .army_current_province_supply_usage_projection import (
    project_conditional_current_province_supply_usage,
)
from .army_full_land_supply_rate_projection import project_full_land_supply_rate_v1


def project_conditional_post_refill_land_supply_rate(
    same_query_strength: Mapping[str, object],
) -> dict[str, object]:
    """Retain one observed context, one physical refill and ordered contributions.

    The selected refill usage is a conditional value, never an after-stage
    observation. Unknown usage must not be replaced by current usage or zero.
    """
    usage = project_conditional_current_province_supply_usage(same_query_strength)
    full_rate = None
    if usage["conditional_usage_ready"]:
        full_rate = project_full_land_supply_rate_v1(
            same_query_strength,
            selected_refill_usage_soldiers=usage["conditional_supply_usage_soldiers"],
        )
    ready = full_rate is not None and full_rate["full_land_rate_ready"]
    observed_rate = same_query_strength.get("current_supply_change_monthly_raw")
    gain = same_query_strength.get("current_land_resupply_v1")
    raw_inputs = same_query_strength.get("current_land_supply_rate_inputs_v1")
    any_ready = (usage["conditional_usage_ready"] or usage["current_usage_ready"]
                 or type(observed_rate) is int
                 or isinstance(gain, Mapping) and gain["current_observation_ready"]
                 or isinstance(raw_inputs, Mapping) and raw_inputs["current_observation_ready"])
    missing = []
    if not usage["conditional_usage_ready"]:
        missing.append({"stage": "selected_refill_province_usage", "inputs": usage["missing_inputs"]})
    elif not ready:
        missing.append({"stage": "full_land_rate", "inputs": full_rate["missing_inputs"]})
    return {
        "projection_kind": "conditional_post_refill_current_province_full_land_supply_rate",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "one_same_query_Strength_row; observed_owner_Province_commander_roster; "
                       "one_explicit_core_refill_per_observed_persistent_cache",
        "army_id": same_query_strength.get("army_id"),
        "native_carmy_id": same_query_strength.get("native_carmy_id"),
        "status": "available" if ready else "partial" if any_ready else "unavailable",
        "conditional_usage_ready": usage["conditional_usage_ready"],
        "conditional_supply_usage_soldiers": usage["conditional_supply_usage_soldiers"],
        "conditional_full_land_rate_ready": bool(ready),
        "conditional_post_refill_supply_rate_raw": (
            full_rate["conditional_full_land_rate_raw"] if ready else None),
        "current_observed_total_rate_raw": observed_rate,
        "current_resupply_inputs_v1": dict(gain) if isinstance(gain, Mapping) else None,
        "current_land_rate_inputs_v1": dict(raw_inputs) if isinstance(raw_inputs, Mapping) else None,
        "same_input_conditional_province_supply_usage_v1": usage,
        "same_input_conditional_full_land_supply_rate_v1": full_rate,
        "scale": 100000, "soldiers_scale": 1,
        "actual_after": False, "actual_replenishment": False,
        "actual_post_stage_observed": False, "full_monthly_supply_change_ready": False,
        "missing_inputs": missing,
    }


def project_observed_post_refill_land_supply_rates_v1(
    same_query_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [project_conditional_post_refill_land_supply_rate(row) for row in same_query_rows]
