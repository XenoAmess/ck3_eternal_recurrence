"""SOURCE_PREPARED / NOTRUN: current native C0 BYTE and mask0x02 call input.

This observation does not read a saved callback register, run a prepare/refill,
or derive tomorrow's flag from an already published calendar/date value.
"""
from __future__ import annotations

_ACTUAL_FALSE = (
    "actual_pre_date_prepare_observed", "actual_post_date_refill_observed",
    "actual_after", "full_monthly_ready",
)
_KEYS = {
    "source", "status", "ready", "unavailable_reason", "subject_army_id", "subject_carmy_id",
    "game_state_calendar_flags_raw_u8", "month_first_mask_2_set", *_ACTUAL_FALSE,
}


def normalize_current_month_first_refill_call_inputs_v1(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native current month-first refill call input schema is malformed")
    if value["source"] != "native_current_month_first_refill_call_inputs":
        raise ValueError("native current month-first refill call input source is malformed")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if status not in {"available", "unavailable"} or type(ready) is not bool:
        raise ValueError("native current month-first refill call input readiness is malformed")
    if ready != (status == "available") or (ready and reason is not None) or (
            not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native current month-first refill call input reason disagrees with readiness")
    for key in ("subject_army_id", "subject_carmy_id"):
        item = value[key]
        if item is not None and (type(item) is not int or not -(1 << 31) <= item < 1 << 31):
            raise ValueError(f"native current month-first refill call {key} must be int32 or null")
    flags = value["game_state_calendar_flags_raw_u8"]
    if flags is not None and (type(flags) is not int or not 0 <= flags <= 255):
        raise ValueError("native month-first calendar flags must be uint8 or null")
    mask = value["month_first_mask_2_set"]
    if mask is not None and type(mask) is not bool:
        raise ValueError("native month-first mask2 verdict must be bool or null")
    if (flags is None) != (mask is None) or (flags is not None and mask != bool(flags & 0x02)):
        raise ValueError("native month-first mask2 verdict disagrees with raw byte")
    if ready and any(value[key] is None for key in (
            "subject_army_id", "subject_carmy_id", "game_state_calendar_flags_raw_u8", "month_first_mask_2_set")):
        raise ValueError("native ready month-first refill call input is incomplete")
    for key in _ACTUAL_FALSE:
        if value[key] is not False:
            raise ValueError("native month-first call input cannot claim an actual callback or full monthly result")
    return dict(value)
