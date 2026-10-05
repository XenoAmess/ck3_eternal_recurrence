"""Conditional 1.20.0.3 caller budgets from one readonly army query.

24E3430 constructs supply from post-24E4D10 stock, then independently rounds
siege and raid against the original current. No updater or writer is called;
the current readonly supply budget and actual-stage boundary stay unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from ..simulation.battle_trait_numeric_inputs_12003 import (
    native_wrap32_12003 as _i32,
    native_wrap64_12003 as _i64,
)
from .army_loss_sequence_replay import project_conditional_army_loss_sequence

SCALE = 100_000


def _integer(value: object, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < 1 << (bits - 1)


def _trunc0(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // denominator
    return -quotient if numerator < 0 else quotient


def _supply_component_product(base: int, multiplier: int) -> int:
    """24E50D7..5151: its decomposed path divides the HIGH operand.

    The battle-trait helper divides the low operand and is therefore not the
    same overflow contract. Keep this source-bound A0 implementation local.
    """
    bound = 3_037_000_499
    mask = (1 << 64) - 1
    if all(((operand + bound) & mask) <= bound * 2 for operand in (base, multiplier)):
        return _trunc0(_i64(base * multiplier), SCALE)
    low, high = sorted((base, multiplier))
    quotient = _trunc0(high, SCALE)
    remainder = _i64(high - _i64(quotient * SCALE))
    return _i64(_i64(quotient * low) + _trunc0(_i64(remainder * low), SCALE))


def _whole_budget(count: int, fraction: int) -> int:
    quotient = _trunc0(_i64(count * fraction), SCALE)
    return min(count, _i32(quotient))


def construct_conditional_monthly_loss_budgets(
    army_strength: Mapping[str, object],
) -> dict[str, object]:
    """Derive pre-write caller operands, with branch-specific readiness.

    Known rejection, fleet suppression and zero component need no later
    component/count operands. Independent siege/raid retain their results
    when supply inputs are missing. A ready budget can feed a copied loss
    subsystem frame; neither that frame nor its outcome is an observation.
    """
    result: dict[str, object] = {
        "projection_kind": "conditional_post_updater_monthly_loss_budgets",
        "source_contract_game_version": "1.20.0.3",
        "input_basis": "one_query_current_native_inputs_conditional_caller_entry",
        "status": "unavailable", "conditional_budgets_ready": False,
        "actual_loss": False, "actual_post_stage_current": None,
        "full_monthly_applied_loss_ready": False,
        "fraction_scale": SCALE, "soldier_scale": 1,
        "current_readonly_supply_loss_budget": None,
        "supply_updater_admitted": None, "admission_ready": False,
        "admission_witnesses": [], "admission_rejection": None,
        "conditional_post_supply_raw": None, "post_supply_ready": False,
        "supply_state_index": None, "supply_base_fraction_raw": None,
        "supply_effective_fraction_raw": None,
        "supply_budget_soldiers": None, "supply_budget_ready": False,
        "siege_budget_soldiers": None, "siege_budget_ready": False,
        "raid_budget_soldiers": None, "raid_budget_ready": False,
        "combined_siege_raid_budget_soldiers": None,
        "same_input_conditional_loss_sequence_v1": None,
        "missing_inputs": [],
    }
    if army_strength.get("status") != "available":
        return {**result, "missing_inputs": ["available_same_query_army_strength"]}
    inputs = army_strength.get("monthly_loss_budget_inputs_v1")
    inputs = inputs if isinstance(inputs, Mapping) else {}
    losses = army_strength.get("loss_application_inputs_v1")
    losses = losses if isinstance(losses, Mapping) else {}
    clock = army_strength.get("army_update_clock_v1")
    clock = clock if isinstance(clock, Mapping) else {}
    result["current_readonly_supply_loss_budget"] = losses.get("current_supply_loss_budget")
    missing: list[str] = result["missing_inputs"]

    # All-current count is the pre-write count for BOTH independently rounded
    # budgets. Neither tier nor native supply eligibility filters this count.
    for prefix in ("siege", "raid"):
        active = losses.get(f"{prefix}_active")
        if active is False:
            result[f"{prefix}_budget_soldiers"] = 0
            result[f"{prefix}_budget_ready"] = True
        elif active is True:
            count, rate = losses.get("whole_soldiers"), losses.get(f"{prefix}_rate_raw")
            absent = [key for key, value, bits in (
                ("whole_soldiers", count, 32), (f"{prefix}_rate_raw", rate, 64)
            ) if not _integer(value, bits)]
            if absent:
                missing.extend(absent)
            else:
                result[f"{prefix}_budget_soldiers"] = _whole_budget(count, min(SCALE, max(0, rate)))
                result[f"{prefix}_budget_ready"] = True
        else:
            missing.append(f"{prefix}_active")
    if result["siege_budget_ready"] and result["raid_budget_ready"]:
        result["combined_siege_raid_budget_soldiers"] = _i32(
            result["siege_budget_soldiers"] + result["raid_budget_soldiers"])

    def admission() -> bool | None:
        gates = (
            ("unit_native_170_raw", 32, lambda value: value != 3),
            ("native_unit_in_combat", None, lambda value: not value),
            ("native_unit_gathering", None, lambda value: not value),
            ("army_gathering_count_raw", 32, lambda value: value == 0),
        )
        for key, bits, passes in gates:
            value = inputs.get(key)
            valid = type(value) is bool if bits is None else _integer(value, bits)
            witness = {"input": key, "value": value, "passed": passes(value) if valid else None}
            result["admission_witnesses"].append(witness)
            if not valid:
                missing.append(key)
                return None
            if not witness["passed"]:
                result["admission_rejection"] = key
                return False
        names = ("current_date_raw", "grace_anchor_date_raw", "loaded_grace_days")
        if any(not _integer(clock.get(key), 32) for key in names):
            missing.extend(key for key in names if not _integer(clock.get(key), 32))
            return None
        elapsed = _i32(clock["current_date_raw"] - clock["grace_anchor_date_raw"])
        days = _trunc0(elapsed, 24)
        passed = days > clock["loaded_grace_days"]
        result["admission_witnesses"].append({
            "input": "native_grace_strict_greater", "elapsed_date_raw": elapsed,
            "elapsed_days": days, "loaded_grace_days": clock["loaded_grace_days"],
            "passed": passed,
        })
        if not passed:
            result["admission_rejection"] = "native_grace_strict_greater"
        return passed

    admitted = admission()
    result.update(supply_updater_admitted=admitted, admission_ready=admitted is not None)
    stock = army_strength.get("current_supply_raw")
    if admitted is False:
        if _integer(stock, 64):
            result.update(conditional_post_supply_raw=stock, post_supply_ready=True)
        result.update(supply_budget_soldiers=0, supply_budget_ready=True)
    elif admitted is True:
        rate = army_strength.get("current_supply_change_monthly_raw")
        capacity = army_strength.get("current_supply_capacity_raw")
        if _integer(stock, 64) and _integer(rate, 64):
            changed = _i64(stock + rate)
            if changed < 0:
                result.update(conditional_post_supply_raw=0, post_supply_ready=True)
            elif _integer(capacity, 64):
                result.update(conditional_post_supply_raw=min(changed, capacity), post_supply_ready=True)
            else:
                missing.append("current_supply_capacity_raw")
        else:
            missing.extend(key for key, value in (
                ("current_supply_raw", stock), ("current_supply_change_monthly_raw", rate)
            ) if not _integer(value, 64))
        suppressed = inputs.get("native_fleet_supply_loss_suppressed")
        if suppressed is True:
            result.update(supply_budget_soldiers=0, supply_budget_ready=True)
        elif suppressed is not False:
            missing.append("native_fleet_supply_loss_suppressed")
        elif result["post_supply_ready"]:
            _derive_supply_component(result, inputs, losses)

    result["missing_inputs"] = list(dict.fromkeys(missing))
    ready = all(result[f"{prefix}_budget_ready"] for prefix in ("supply", "siege", "raid"))
    result["conditional_budgets_ready"] = ready
    result["status"] = "available" if ready else (
        "partial" if any(result[f"{prefix}_budget_ready"] for prefix in ("supply", "siege", "raid"))
        or result["admission_ready"] else "unavailable")
    if ready:
        state = deepcopy(dict(army_strength))
        state["loss_application_inputs_v1"] = {
            **losses, "status": "available",
            "current_supply_loss_budget": result["supply_budget_soldiers"],
            "siege_loss_budget": result["siege_budget_soldiers"],
            "raid_loss_budget": result["raid_budget_soldiers"],
        }
        sequence = project_conditional_army_loss_sequence(state)
        sequence["input_basis"] = "derived_budget_and_loss_subsystem"
        result["same_input_conditional_loss_sequence_v1"] = sequence
    return result


def _derive_supply_component(
    result: dict[str, object], inputs: Mapping[str, object], losses: Mapping[str, object],
) -> None:
    missing = result["missing_inputs"]
    levels = inputs.get("loaded_supply_state_levels")
    if not isinstance(levels, list) or any(not _integer(value, 32) for value in levels):
        missing.append("loaded_supply_state_levels")
        return
    stock_integer = _i32(_trunc0(result["conditional_post_supply_raw"], SCALE))
    index = next((index for index, level in enumerate(levels) if stock_integer >= level), len(levels) - 1)
    result["supply_state_index"] = index
    if index < 0:
        base = 0
    else:
        fractions = inputs.get("loaded_supply_state_fractions_raw")
        if not isinstance(fractions, list) or any(not _integer(value, 64) for value in fractions):
            missing.append("loaded_supply_state_fractions_raw")
            return
        base = fractions[index] if index < len(fractions) else 0
    result["supply_base_fraction_raw"] = base
    if base == 0:
        component = 0
    elif inputs.get("commander_valid") is False:
        component = base  #24E517E does not clamp the absent/invalid branch.
    elif inputs.get("commander_valid") is True:
        modifier = inputs.get("commander_supply_modifier_raw")
        if not _integer(modifier, 64):
            missing.append("commander_supply_modifier_raw")
            return
        component = min(SCALE, max(0, _supply_component_product(base, _i64(SCALE + modifier))))
    else:
        missing.append("commander_valid")
        return
    result["supply_effective_fraction_raw"] = component
    if component <= 0:
        result.update(supply_budget_soldiers=0, supply_budget_ready=True)
        return
    count = losses.get("supply_eligible_soldiers")
    if not _integer(count, 32):
        missing.append("supply_eligible_soldiers")
        return
    result.update(supply_budget_soldiers=_whole_budget(count, component), supply_budget_ready=True)
