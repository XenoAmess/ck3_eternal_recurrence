"""SOURCE_PREPARED/NOTRUN: exact current selected-bucket subject occurrences."""
from __future__ import annotations

_I32 = (
    "subject_army_id", "subject_carmy_id", "current_date_raw", "native_day_index",
    "selected_bucket_phase", "selected_bucket_capacity_raw", "selected_bucket_count_raw",
    "subject_dispatch_occurrence_count",
)
_FALSE = (
    "actual_callback_observed", "earlier_stage_outputs_reconstructed",
    "full_daily_supply_transition_ready", "full_monthly_ready",
)
_KEYS = {"source", "status", "ready", "unavailable_reason", "capture_boundary",
         "selected_bucket_data_present", "subject_occurrence_indices", *_I32, *_FALSE}


def normalize_current_daily_supply_dispatch_inputs_v1(
    value: object, *, expected_army_id: int | None = None,
    expected_carmy_id: int | None = None,
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native current daily supply dispatch schema is malformed")
    if value["source"] != "native_current_selected_supply_bucket_subject_occurrences":
        raise ValueError("native current daily supply dispatch source is malformed")
    if value["capture_boundary"] != "current_paused_strength":
        raise ValueError("native current daily supply dispatch capture boundary is malformed")
    if any(value[key] is not False for key in _FALSE):
        raise ValueError("current bucket inputs cannot claim actual later callback or stage output")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if status not in {"available", "unavailable"} or type(ready) is not bool:
        raise ValueError("native current daily supply dispatch readiness is malformed")
    if ready != (status == "available") or (ready and reason is not None) or (
        not ready and (not isinstance(reason, str) or not reason)
    ):
        raise ValueError("native current daily supply dispatch reason disagrees with readiness")
    for key in _I32:
        item = value[key]
        if item is not None and (type(item) is not int or not -(1 << 31) <= item < (1 << 31)):
            raise ValueError(f"native current daily supply dispatch {key} has invalid width")
    present = value["selected_bucket_data_present"]
    if present is not None and type(present) is not bool:
        raise ValueError("native selected bucket data presence must be bool or null")
    indices = value["subject_occurrence_indices"]
    if indices is not None and (
        not isinstance(indices, list) or any(type(index) is not int or not 0 <= index < (1 << 31)
                                            for index in indices)
    ):
        raise ValueError("native selected bucket subject indices must be int32 list or null")
    for field, expected in (("subject_army_id", expected_army_id),
                            ("subject_carmy_id", expected_carmy_id)):
        if expected is not None and value[field] is not None and value[field] != expected:
            raise ValueError(f"native daily supply dispatch {field} differs from same-query row")
    if ready:
        if any(value[key] is None for key in _I32 if key != "selected_bucket_capacity_raw") or present is None or indices is None:
            raise ValueError("ready native daily supply dispatch operands are incomplete")
        if value["selected_bucket_phase"] != (value["native_day_index"] & 0xFFFFFFFF) % 30:
            raise ValueError("native selected bucket must use unsigned stored day modulo30")
        count = value["selected_bucket_count_raw"]
        if count < 0 or (count > 0 and not present):
            raise ValueError("ready native selected bucket count or pointer data is unavailable")
        if value["subject_dispatch_occurrence_count"] != len(indices):
            raise ValueError("native subject occurrence count differs from original index list")
        if any(index >= count for index in indices) or any(a >= b for a, b in zip(indices, indices[1:])):
            raise ValueError("native subject indices must retain distinct original traversal positions in order")
    result = dict(value)
    if indices is not None:
        result["subject_occurrence_indices"] = list(indices)
    return result
