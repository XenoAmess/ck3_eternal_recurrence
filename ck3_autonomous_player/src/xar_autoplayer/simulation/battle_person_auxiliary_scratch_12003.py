"""Source-closed 2948DF0/2948F00 arithmetic from same-frame current operands.

The existing raw_numeric_inputs context supplies actual ordered native rows.
Prepared scratch430/438 and copied2E0/2F0 are observed independently; neither is
a source-stage baseline. This primitive never prepares or writes a Character,
model, scratch or Entry and does not advance a simulation horizon.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .battle_trait_numeric_inputs_12003 import (
    _Calculation,
    from_raw_numeric_inputs_12003,
    native_wrap64_12003,
)


@dataclass(frozen=True, slots=True)
class AuxiliaryScratchResult12003:
    character_id: int | None
    scratch430_q64: int | None
    scratch438_q64: int | None
    selected_property_key_u16: int | None
    calculation_ready: bool
    status: str
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_native_callback_ready: bool = False
    entry_refresh_ready: bool = False
    actual_game_days_advanced: int = 0


def compute_auxiliary_scratch_from_native_inputs_12003(
    payload: Mapping[str, object] | None, *,
    source_provenance: Mapping[str, object] | None = None,
) -> AuxiliaryScratchResult12003:
    """Consume normalized raw_numeric_inputs without calling native getters.

    Observation availability is separate from calculability. Undemanded high
    thresholds and native-empty properties are valid; absent demanded inputs
    remain partial. Future use needs explicitly materialized changed operands.
    """
    raw = payload if isinstance(payload, Mapping) else {}
    native = from_raw_numeric_inputs_12003(raw)
    aux = raw.get("auxiliary_scratch_inputs")
    aux = aux if isinstance(aux, Mapping) else {}
    calc = _Calculation()
    ledger: dict[str, object] = {
        "source_rvas": ("2948DF0", "2948F00", "28C3EB0", "28C3F1C"),
        "scope": "current_materialized_context",
        "source_provenance": dict(source_provenance or {}),
        "observed_prepared_q64": (aux.get("prepared430_q64"), aux.get("prepared438_q64")),
        "observed_copied_q64": (aux.get("copied430_q64"), aux.get("copied438_q64")),
        "observed_ready440_raw": aux.get("ready440_raw"),
        "prepared_equals_copied_assumed": False,
        "changed_stage_context_constructed": False,
        "native_copy_executed": False,
        "following_2949010_replayed": False,
    }
    if native.scratch_present is False:
        ledger["branch"] = "native_null_scratch_noop"
        return AuxiliaryScratchResult12003(native.character_id, None, None, None,
                                          True, "native_noop", (), ledger)
    if native.scratch_present is not True:
        calc.gap("scratch_present")
    if not aux:
        calc.gap("auxiliary_scratch_inputs")

    positive430 = calc.context_value(native.context, 0x38, 1)
    negative430 = calc.context_value(native.context, 0x38, 2)
    absolute430 = calc.context_value(native.context, 0x3D, 0)
    base430 = calc.i64(aux.get("base430_q64"), "auxiliary_scratch_inputs.base430_q64")
    tail430 = total430 = result430 = None
    if all(v is not None for v in (positive430, negative430, absolute430, base430)):
        tail430 = min(native_wrap64_12003(negative430 + absolute430), 0)
        total430 = native_wrap64_12003(
            positive430 + native_wrap64_12003(tail430 + base430))
        result430 = max(0, min(total430, 100000))

    metric = calc.i32(aux.get("selector_metric_raw"), "auxiliary_scratch_inputs.selector_metric_raw")
    flag = calc.i32(aux.get("selector_flag_raw"), "auxiliary_scratch_inputs.selector_flag_raw")
    low = calc.i32(aux.get("selected_low_threshold_raw"),
                   "auxiliary_scratch_inputs.selected_low_threshold_raw")
    key = high = None
    if flag is not None and metric is not None and low is not None:
        if metric < low:
            key = 0x3A
        else:
            high = calc.i32(aux.get("selected_high_threshold_raw"),
                            "auxiliary_scratch_inputs.selected_high_threshold_raw")
            if high is not None:
                key = 0x3B if metric < high else 0x3C

    negative438 = calc.context_value(native.context, 0x39, 2)
    absolute438 = calc.context_value(native.context, 0x3E, 0)
    positive438 = calc.context_value(native.context, 0x39, 1)
    selected438 = calc.context_value(native.context, key, 0) if key is not None else None
    base438 = calc.i64(aux.get("base438_q64"), "auxiliary_scratch_inputs.base438_q64")
    tail438 = after_base438 = after_selected438 = result438 = None
    if all(v is not None for v in (negative438, absolute438, positive438, selected438, base438)):
        tail438 = min(native_wrap64_12003(negative438 + absolute438), 0)
        after_base438 = native_wrap64_12003(tail438 + base438)
        after_selected438 = native_wrap64_12003(after_base438 + selected438)
        result438 = native_wrap64_12003(after_selected438 + positive438)
    ledger.update({
        "branch": "nonnull_scratch_auxiliary_calculation",
        "430": {"positive_q64": positive430, "negative_q64": negative430,
                "absolute_q64": absolute430, "base_q64": base430,
                "negative_tail_q64": tail430, "wrapped_total_q64": total430,
                "clamp_low": 0, "clamp_high": 100000},
        "selector": {"flag_raw": flag, "metric_raw": metric, "low_raw": low,
                     "demanded_high_raw": high, "selected_key_u16": key},
        "438": {"positive_q64": positive438, "negative_q64": negative438,
                "absolute_q64": absolute438, "selected_q64": selected438,
                "base_q64": base438, "negative_tail_q64": tail438,
                "after_base_q64": after_base438, "after_selected_q64": after_selected438,
                "final_clamp": False},
        "property_lookups": tuple(calc.lookups),
        "weighted_terms": tuple(calc.weighted_terms),
    })
    ready = not calc.missing and result430 is not None and result438 is not None
    return AuxiliaryScratchResult12003(native.character_id, result430, result438,
                                      key, ready, "computed" if ready else "partial",
                                      tuple(calc.missing), ledger)
