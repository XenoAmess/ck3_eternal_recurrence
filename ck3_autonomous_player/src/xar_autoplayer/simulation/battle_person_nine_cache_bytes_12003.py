"""2949010's nine signed cache bytes from its actual scratch-selected model.

This pure adapter uses native ordered property operands and real constants.
It never initializes a model, invokes native code, writes a cache, refreshes
Entry or substitutes an earlier fallback-selected context for scratch258.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .battle_trait_numeric_inputs_12003 import (
    _Calculation, _container_from_mapping, _trunc_q,
    native_wrap32_12003, native_wrap64_12003,
)

BASE_KEYS_12003 = (0x22A, 0x228, 0x22B, 0x229, 0x225, 0x22D, 0x22C, 0x226, 0x227)


@dataclass(frozen=True, slots=True)
class NineCacheByteResult12003:
    character_id: int | None
    sums_q64: tuple[int | None, ...]
    points_low32: tuple[int | None, ...]
    cache_bytes: tuple[int | None, ...]
    optional_family_admitted: bool | None
    calculation_ready: bool
    status: str
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_native_callback_ready: bool = False
    entry_refresh_ready: bool = False
    actual_game_days_advanced: int = 0


def _optional_family(calc: _Calculation, nine: Mapping[str, object]) -> bool | None:
    if nine.get("carrier278_present") is not True:
        calc.gap("nine_cache_byte_inputs.carrier278_present")
        return None
    magic = calc.i32(nine.get("carrier278_magic_raw"), "nine_cache_byte_inputs.carrier278_magic_raw")
    if magic is None:
        return None
    if magic != 0x41495374:
        return False
    if type(nine.get("linked20_present")) is not bool:
        calc.gap("nine_cache_byte_inputs.linked20_present")
        return None
    if nine.get("used_native_definition_fallback") is not (nine["linked20_present"] is False):
        calc.gap("nine_cache_byte_inputs.used_native_definition_fallback")
        return None
    if nine.get("selected_definition_present") is not True:
        calc.gap("nine_cache_byte_inputs.selected_definition_present")
        return None
    magic = calc.i32(nine.get("selected_definition_magic_raw"),
                     "nine_cache_byte_inputs.selected_definition_magic_raw")
    return None if magic is None else magic == 0x4744624F


def compute_nine_cache_bytes_from_native_inputs_12003(
    payload: Mapping[str, object] | None, *,
    source_provenance: Mapping[str, object] | None = None,
) -> NineCacheByteResult12003:
    """Consume normalized raw_numeric_inputs.nine_cache_byte_inputs.

    Legal skipped families/FFFF/absent keys are zero; unread demanded operands
    remain partial. Current signed bytes are evidence independent of calculated
    output. Future use requires an explicit changed-stage actual model.
    """
    raw = payload if isinstance(payload, Mapping) else {}
    nine = raw.get("nine_cache_byte_inputs")
    nine = nine if isinstance(nine, Mapping) else {}
    calc = _Calculation()
    character_id = raw.get("character_id")
    character_id = character_id if type(character_id) is int else None
    current = nine.get("current_cache_bytes")
    ledger: dict[str, object] = {
        "source_rva": "2949010", "source_callsite": "28C4017",
        "source_scope": "actual_scratch258_model_aggregate",
        "base_keys_in_native_order": BASE_KEYS_12003,
        "observed_current_cache_bytes": tuple(current) if isinstance(current, (list, tuple)) else None,
        "observed_cache_equals_calculated_assumed": False,
        "source_provenance": dict(source_provenance or {}),
        "native_write_destination": "QWORD[scratch310]",
        "changed_stage_context_constructed": False,
    }
    empty = (None,) * 9
    if raw.get("scratch_present") is False:
        ledger["branch"] = "native_null_scratch_noop"
        return NineCacheByteResult12003(character_id, empty, empty, empty, None,
                                       True, "native_noop", (), ledger)
    if raw.get("scratch_present") is not True:
        calc.gap("scratch_present")
    if not nine:
        calc.gap("nine_cache_byte_inputs")
    if nine.get("model_present") is not True:
        calc.gap("nine_cache_byte_inputs.model_present")
    properties = _container_from_mapping(nine.get("aggregate_properties"))
    admitted = _optional_family(calc, nine)
    selected = nine.get("selected_definition_keys_u16")
    sums, points, result, occurrences = [], [], [], []
    for index, base_key in enumerate(BASE_KEYS_12003):
        base = calc.property_value(properties, base_key, "nine_cache_byte_inputs.aggregate_properties")
        selected_key = term = None
        if admitted is False:
            term = 0
        elif admitted is True:
            selected_key = calc.item(selected, index, f"nine_cache_byte_inputs.selected_definition_keys_u16[{index}]")
            if type(selected_key) is not int:
                calc.gap(f"nine_cache_byte_inputs.selected_definition_keys_u16[{index}]")
            else:
                term = calc.property_value(properties, selected_key,
                                           "nine_cache_byte_inputs.aggregate_properties")
        total = native_wrap64_12003(base + term) if base is not None and term is not None else None
        low32 = native_wrap32_12003(_trunc_q(total)) if total is not None else None
        cache_byte = max(-100, min(low32, 100)) if low32 is not None else None
        sums.append(total)
        points.append(low32)
        result.append(cache_byte)
        occurrences.append({"native_index": index, "base_key_u16": base_key,
                            "base_q64": base, "selected_key_u16": selected_key,
                            "selected_q64": term, "wrapped_sum_q64": total,
                            "points_low32": low32, "clamped_signed_byte": cache_byte})
    ledger.update({"branch": "nonnull_scratch_nine_byte_calculation",
                   "optional_family_admitted": admitted,
                   "occurrences": tuple(occurrences),
                   "native_q_scale": 100000, "native_point_clamp": (-100, 100),
                   "narrow_signed32_before_clamp": True,
                   "property_lookups": tuple(calc.lookups)})
    ready = not calc.missing and all(value is not None for value in result)
    return NineCacheByteResult12003(character_id, tuple(sums), tuple(points), tuple(result),
                                   admitted, ready, "computed" if ready else "partial",
                                   tuple(calc.missing), ledger)
