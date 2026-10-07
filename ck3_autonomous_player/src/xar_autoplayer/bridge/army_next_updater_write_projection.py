"""Readonly next-entry writes from the same native Army query.

The source-defined +22 and +188 writes do not observe a future callback. Stock,
budget and earlier-stage reconstruction stay in their existing independent lanes.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_source_derived_next_daily_supply_frame_contract import (
    normalize_source_derived_next_daily_supply_frame_inputs_v1,
)


def _integer(value: object, bits: int) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < (1 << (bits - 1))


def _signed32(value: int) -> int:
    raw = value & 0xFFFFFFFF
    return raw - (1 << 32) if raw >= (1 << 31) else raw


def _trunc24(value: int) -> int:
    quotient = abs(value) // 24
    return -quotient if value < 0 else quotient


def _admission(inputs: Mapping[str, object], clock: Mapping[str, object],
               next_low32: object) -> dict[str, object]:
    """Retained updater gate order; unused later operands are not required."""
    result: dict[str, object] = {
        "ready": False, "admitted": None, "rejection": None,
        "witnesses": [], "missing_inputs": [],
    }
    for key, bits, passes in (
        ("unit_native_170_raw", 32, lambda value: value != 3),
        ("native_unit_in_combat", None, lambda value: not value),
        ("native_unit_gathering", None, lambda value: not value),
        ("army_gathering_count_raw", 32, lambda value: value == 0),
    ):
        value = inputs.get(key)
        valid = type(value) is bool if bits is None else _integer(value, bits)
        passed = passes(value) if valid else None
        result["witnesses"].append({"input": key, "value": value, "passed": passed})
        if not valid:
            result["missing_inputs"].append("monthly_loss_budget_inputs_v1." + key)
            return result
        if not passed:
            result.update(ready=True, admitted=False, rejection=key)
            return result
    values = {
        "source_derived_next_date_raw_i32": next_low32,
        "grace_anchor_date_raw": clock.get("grace_anchor_date_raw"),
        "loaded_grace_days": clock.get("loaded_grace_days"),
    }
    absent = [key for key, value in values.items() if not _integer(value, 32)]
    if absent:
        result["missing_inputs"].extend(absent)
        return result
    elapsed = _signed32(next_low32 - values["grace_anchor_date_raw"])
    days = _trunc24(elapsed)
    admitted = days > values["loaded_grace_days"]
    result["witnesses"].append({
        "input": "native_grace_strict_greater",
        "passed_date_raw_i32": next_low32,
        "grace_anchor_date_raw_i32": values["grace_anchor_date_raw"],
        "elapsed_date_raw_i32": elapsed, "elapsed_days": days,
        "loaded_grace_days": values["loaded_grace_days"], "passed": admitted,
    })
    result.update(ready=True, admitted=admitted,
                  rejection=None if admitted else "native_grace_strict_greater")
    return result


def project_source_derived_next_updater_writes_v1(
    same_query_strength: Mapping[str, object],
) -> dict[str, object]:
    """Join source-owned next CDate to the two writes of a held receiver entry.

    Witness equality reports values only. It does not establish a previous
    callback, and no aggregate schedule or stock/budget readiness is required.
    """
    row = same_query_strength
    clock = row.get("army_update_clock_v1")
    clock = clock if isinstance(clock, Mapping) else {}
    caller = row.get("monthly_caller_effect_inputs_v1")
    caller = caller if isinstance(caller, Mapping) else {}
    inputs = row.get("monthly_loss_budget_inputs_v1")
    inputs = inputs if isinstance(inputs, Mapping) else {}
    native_next = normalize_source_derived_next_daily_supply_frame_inputs_v1(
        row.get("source_derived_next_daily_supply_frame_inputs_v1"),
        expected_army_id=row.get("army_id"), expected_carmy_id=row.get("native_carmy_id"))
    next_low32 = native_next.get("source_derived_next_date_raw_i32") if native_next else None
    next_full = native_next.get("source_derived_next_date_storage_raw64") if native_next else None
    full_ready = bool(native_next and
                      native_next.get("source_derived_full_cdate64_ready") is True and
                      _integer(next_full, 64))
    typed_row = row.get("status") == "available" and type(row.get("native_carmy_id")) is int
    old22 = caller.get("army_byte_22_raw")
    old188 = clock.get("last_supply_update_date_storage_raw64")
    anchor190 = clock.get("grace_anchor_date_storage_raw64")
    current_full = caller.get("current_date_storage_raw64")
    source_current_full = native_next.get("current_date_storage_raw64") if native_next else None
    comparison_ready = _integer(old188, 64) and _integer(current_full, 64)
    current_low32 = clock.get("current_date_raw")
    anchor_low32 = clock.get("grace_anchor_date_raw")
    current_elapsed = (_trunc24(_signed32(current_low32 - anchor_low32))
                       if _integer(current_low32, 32) and _integer(anchor_low32, 32) else None)
    admission = _admission(inputs, clock, next_low32)
    if not typed_row:
        admission = {"ready": False, "admitted": None, "rejection": None,
                     "witnesses": [], "missing_inputs": ["available_typed_army_row"]}
    admitted = admission["admitted"]
    after188 = next_full if admitted is True and full_ready else (
        old188 if admitted is False and _integer(old188, 64) else None)
    after188_ready = (admitted is True and full_ready) or (
        admitted is False and _integer(old188, 64))
    missing = list(admission["missing_inputs"])
    if admitted is True and not full_ready:
        missing.append("source_derived_next_daily_supply_frame_inputs_v1.source_derived_next_date_storage_raw64")
    elif admitted is False and not _integer(old188, 64):
        missing.append("army_update_clock_v1.last_supply_update_date_storage_raw64")
    ready = typed_row and admission["ready"] and after188_ready
    return {
        "schema_version": 1,
        "source": "same_input_conditional_source_derived_next_updater_writes",
        "status": "available" if ready else "partial" if typed_row else "unavailable",
        "ready": ready, "missing_inputs": list(dict.fromkeys(missing)),
        "army_id": row.get("army_id"), "native_carmy_id": row.get("native_carmy_id"),
        "condition": "one source updater invocation for this CURRENT captured receiver at source-derived next passedDate, all non-date gate values unchanged after earlier Unit stages",
        "callback_entry_is_conditional": True,
        "source_next_date": deepcopy(native_next),
        "observed_current_army_byte_22_raw": old22,
        "observed_current_army_byte_22_ready": type(old22) is int and 0 <= old22 < 256,
        "observed_current_last_supply_update_date_storage_raw64": old188,
        "observed_current_last_supply_update_date_raw_i32": clock.get("last_supply_update_date_raw"),
        "observed_current_caller_date_storage_raw64": current_full,
        "observed_current_update_date_comparison_ready": comparison_ready,
        "observed_current_update_date_matches_current_clock": old188 == current_full if comparison_ready else None,
        "observed_current_clock_matches_source_seed": current_full == source_current_full if (
            _integer(current_full, 64) and _integer(source_current_full, 64)) else None,
        "observed_current_grace_elapsed_days": current_elapsed,
        "next_admission": admission,
        "conditional_writes": [
            {"order": 0, "member": "CArmy+0x22", "stage": "before_admission",
             "write_ready": typed_row, "would_write": True if typed_row else None,
             "observed_value": old22, "conditional_value": 1 if typed_row else None,
             "actual_write_observed": False},
            {"order": 1, "member": "CArmy+0x188", "stage": "after_admission_before_rate",
             "write_ready": bool(after188_ready), "write_predicate_ready": bool(admission["ready"]),
             "would_write": admitted,
             "after_value_ready": bool(after188_ready), "observed_value": old188,
             "conditional_value": after188,
             "value_origin": "source_derived_next_full_cdate64" if admitted is True else (
                 "observed_current_188_retained" if admitted is False else None),
             "actual_write_observed": False},
        ],
        "conditional_grace_anchor_190": {
            "would_write": False, "ready": _integer(anchor190, 64),
            "observed_value": anchor190, "conditional_value": anchor190,
            "observed_low32": anchor_low32, "conditional_low32": anchor_low32,
            "actual_write_observed": False,
        },
        "source_next_full_date_ready": full_ready,
        "earlier_stage_effects_reconstructed": False,
        "actual_future_date_stage_observed": False,
        "actual_future_callback_observed": False,
        "actual_future_writes_observed": False,
        "future_stock_or_strength_ready": False,
        "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
