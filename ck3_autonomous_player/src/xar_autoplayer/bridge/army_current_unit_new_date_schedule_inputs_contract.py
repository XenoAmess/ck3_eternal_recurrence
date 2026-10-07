"""Strict current raw Unit NewDate schedule inputs from one Army query."""
from __future__ import annotations

_SOURCE = "native_current_unit_new_date_schedule_inputs_12004"
_BOUNDARY = "current_query_before_unit_new_date_stage"
_IDS = ("subject_army_id_u32", "subject_carmy_id_u32")
_I32 = ("vector_header_count_i32", "subject_stored_id_occurrence_count_i32")
_FALSE = (
    "actual_unit_new_date_callback_observed",
    "actual_movement_or_arrival_observed",
    "earlier_stage_outputs_reconstructed",
    "full_daily_supply_transition_ready",
    "full_monthly_ready",
)
_KEYS = {
    "schema_version", "source", "capture_boundary", "status", "ready",
    "unavailable_reason", *_IDS, *_I32, "vector_data_present",
    "subject_stored_id_positions", *_FALSE,
}


def normalize_current_unit_new_date_schedule_inputs_v1(
    value: object, *, expected_army_id: int | None = None,
    expected_carmy_id: int | None = None,
) -> dict[str, object] | None:
    """Preserve raw DWORD equality positions without qualifying a callback."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native current Unit NewDate schedule schema is malformed")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("native current Unit NewDate schedule schema_version is malformed")
    if value["source"] != _SOURCE or value["capture_boundary"] != _BOUNDARY:
        raise ValueError("native current Unit NewDate schedule source/boundary is malformed")
    if any(value[key] is not False for key in _FALSE):
        raise ValueError("current Unit schedule cannot claim callback, movement or future effects")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if not isinstance(status, str) or status not in {"available", "unavailable"} or type(ready) is not bool:
        raise ValueError("native current Unit NewDate schedule readiness is malformed")
    if ready != (status == "available") or (ready and reason is not None) or (
        not ready and (not isinstance(reason, str) or not reason)
    ):
        raise ValueError("native current Unit NewDate schedule reason disagrees with readiness")
    for key in _IDS:
        item = value[key]
        if item is not None and (type(item) is not int or not 0 <= item < (1 << 32)):
            raise ValueError(f"native current Unit NewDate schedule {key} must be uint32 or null")
    for key in _I32:
        item = value[key]
        if item is not None and (
            type(item) is not int or not -(1 << 31) <= item < (1 << 31)
        ):
            raise ValueError(f"native current Unit NewDate schedule {key} must be int32 or null")
    present = value["vector_data_present"]
    if present is not None and type(present) is not bool:
        raise ValueError("native Unit schedule data presence must be bool or null")
    positions = value["subject_stored_id_positions"]
    if positions is not None and (
        not isinstance(positions, list) or any(
            type(index) is not int or not 0 <= index < (1 << 31) for index in positions
        )
    ):
        raise ValueError("native Unit schedule positions must be an int32 list or null")
    if positions is not None and any(a >= b for a, b in zip(positions, positions[1:])):
        raise ValueError("native Unit schedule positions must preserve distinct stored order")
    occurrences = value["subject_stored_id_occurrence_count_i32"]
    if occurrences is not None and occurrences < 0:
        raise ValueError("native Unit schedule occurrence count cannot be negative")
    for field, expected in (
        ("subject_army_id_u32", expected_army_id),
        ("subject_carmy_id_u32", expected_carmy_id),
    ):
        if expected is not None and value[field] is not None and (
            type(expected) is not int or value[field] != (expected & 0xFFFFFFFF)
        ):
            raise ValueError(f"native Unit schedule {field} differs from same-query row")
    if ready:
        count = value["vector_header_count_i32"]
        if any(value[key] is None for key in _IDS) or count is None or present is None:
            raise ValueError("ready native Unit schedule has incomplete subject or header")
        if count < 0 or (count > 0 and not present):
            raise ValueError("ready native Unit schedule has unavailable vector data")
        if positions is None or occurrences != len(positions):
            raise ValueError("ready native Unit schedule occurrence count disagrees with positions")
        if any(index >= count for index in positions):
            raise ValueError("native Unit schedule position exceeds the captured vector count")
    elif positions is not None or occurrences is not None:
        raise ValueError("unavailable native Unit schedule must retain unknown positions/count")
    return {
        **value,
        "subject_stored_id_positions": None if positions is None else list(positions),
    }
