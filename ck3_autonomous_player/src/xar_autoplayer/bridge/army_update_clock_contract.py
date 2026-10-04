"""Observed native army update operands; no future cash or troop prediction."""
from __future__ import annotations

_I32 = (
    "current_date_raw", "native_day_index", "selected_bucket_phase",
    "observed_army_bucket_phase", "last_supply_update_date_raw",
    "grace_anchor_date_raw", "loaded_grace_days",
)
_I64 = ("last_supply_update_date_storage_raw64", "grace_anchor_date_storage_raw64")
_KEYS = {"status", "ready", "unavailable_reason", *_I32, *_I64}

def normalize_army_update_clock_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native army_update_clock_v1 schema is malformed")
    status = value["status"]
    if status not in {"available", "not_registered", "unavailable"}:
        raise ValueError("native army_update_clock_v1 status is malformed")
    ready = value["ready"]
    if type(ready) is not bool or ready != (status != "unavailable"):
        raise ValueError("native army_update_clock_v1 ready disagrees with status")
    result = dict(value)
    for keys, bits in ((_I32, 32), (_I64, 64)):
        for key in keys:
            item = value[key]
            if item is not None and (type(item) is not int or not -(2**(bits-1)) <= item < 2**(bits-1)):
                raise ValueError(f"native army_update_clock_v1 {key} must be signed int{bits} or null")
    for key in ("selected_bucket_phase", "observed_army_bucket_phase"):
        if value[key] is not None and not 0 <= value[key] < 30:
            raise ValueError(f"native army_update_clock_v1 {key} must be a native bucket phase or null")
    if ready and any(value[key] is None for key in (*_I32, *_I64) if key != "observed_army_bucket_phase"):
        raise ValueError("native ready army_update_clock_v1 is incomplete")
    if ((status == "available" and value["observed_army_bucket_phase"] is None) or
            (status == "not_registered" and value["observed_army_bucket_phase"] is not None)):
        raise ValueError("native army_update_clock_v1 membership disagrees with status")
    reason = value["unavailable_reason"]
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native army_update_clock_v1 unavailable_reason disagrees with status")
    return result
