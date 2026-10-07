"""Native-produced conditional next clock pair and optional complete CDate64."""
from __future__ import annotations

from copy import deepcopy

FAMILY_KEY = "source_derived_next_daily_supply_frame_inputs_v1"
SOURCE = "native_source_derived_next_daily_supply_frame_inputs_12004"
STAGE = "source_derived_conditional_next_date_pair"
_I32 = (
    "current_date_raw_i32", "current_native_day_index_raw_i32",
    "source_derived_next_date_raw_i32",
    "source_derived_next_native_day_index_raw_i32",
)
_U32 = ("subject_army_id_u32", "subject_carmy_id_u32")
_FALSE = (
    "actual_future_date_stage_observed", "actual_future_callback_observed",
    "future_bucket_mutations_reconstructed", "future_stock_or_strength_ready",
    "full_daily_supply_transition_ready", "full_monthly_ready",
)
_KEYS = {
    "schema_version", "source", "stage", "status", "ready", "unavailable_reason",
    "current_date_storage_raw64", *_I32, *_U32, *_FALSE,
}
_FULL_VALUES = (
    "source_derived_next_date_storage_raw64",
    "source_derived_next_calendar_day_u8",
    "source_derived_next_calendar_month_u8",
)
_FULL_READY = "source_derived_full_cdate64_ready"
_EXTENDED_KEYS = _KEYS | {*_FULL_VALUES, _FULL_READY}


def _integer(value: object, bits: int, *, unsigned: bool = False) -> bool:
    lower, upper = (0, 1 << bits) if unsigned else (-(1 << (bits - 1)), 1 << (bits - 1))
    return type(value) is int and lower <= value < upper


def normalize_source_derived_next_daily_supply_frame_inputs_v1(
    value: object, *, expected_army_id: int | None = None,
    expected_carmy_id: int | None = None,
) -> dict[str, object] | None:
    """Preserve closed legacy19/extended23 rows without filling absent native keys."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) not in (_KEYS, _EXTENDED_KEYS):
        raise ValueError("source-derived native next supply frame schema is malformed")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("source-derived native next supply frame version is malformed")
    if value["source"] != SOURCE or value["stage"] != STAGE:
        raise ValueError("source-derived native next supply frame source is malformed")
    if any(value[key] is not False for key in _FALSE):
        raise ValueError("source-derived date pair cannot claim future execution or stock")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if status not in {"available", "unavailable"} or type(ready) is not bool:
        raise ValueError("source-derived native next supply frame readiness is malformed")
    if ready != (status == "available") or (
        ready and reason is not None
    ) or (
        not ready and (not isinstance(reason, str) or not reason)
    ):
        raise ValueError("source-derived native next supply frame reason disagrees with readiness")
    for field in _I32:
        if value[field] is not None and not _integer(value[field], 32):
            raise ValueError(f"source-derived native next supply frame {field} must be signed32 or null")
    for field in _U32:
        if value[field] is not None and not _integer(value[field], 32, unsigned=True):
            raise ValueError(f"source-derived native next supply frame {field} must be uint32 or null")
    storage = value["current_date_storage_raw64"]
    if storage is not None and not _integer(storage, 64):
        raise ValueError("source-derived native next supply frame current storage must be signed64 or null")
    for field, expected in (("subject_army_id_u32", expected_army_id),
                            ("subject_carmy_id_u32", expected_carmy_id)):
        if expected is not None and value[field] is not None and value[field] != (expected & 0xFFFFFFFF):
            raise ValueError("source-derived native next supply frame subject differs from same-query row")
    if ready and any(value[field] is None for field in (*_I32, *_U32, "current_date_storage_raw64")):
        raise ValueError("ready source-derived native next supply frame operands are incomplete")
    if _FULL_READY in value:
        full_ready = value[_FULL_READY]
        if type(full_ready) is not bool:
            raise ValueError("source-derived complete CDate64 readiness must be boolean")
        full_storage = value[_FULL_VALUES[0]]
        if full_storage is not None and not _integer(full_storage, 64):
            raise ValueError("source-derived complete CDate64 storage must be signed64 or null")
        for field in _FULL_VALUES[1:]:
            if value[field] is not None and not _integer(value[field], 8, unsigned=True):
                raise ValueError(f"source-derived complete CDate64 {field} must be uint8 or null")
        if full_ready and (not ready or any(value[field] is None for field in _FULL_VALUES)):
            raise ValueError("ready source-derived complete CDate64 operands are incomplete")
    return deepcopy(value)
