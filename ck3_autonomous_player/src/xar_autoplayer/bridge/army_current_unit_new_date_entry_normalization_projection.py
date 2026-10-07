"""Strict raw entry inputs and a conditional first Unit NewDate prefix value."""
from __future__ import annotations

from .army_current_unit_new_date_schedule_inputs_contract import (
    normalize_current_unit_new_date_schedule_inputs_v1,
)
from .army_monthly_loss_budget_inputs_contract import normalize_monthly_loss_budget_inputs_v1
from .army_source_derived_next_daily_supply_frame_contract import (
    FAMILY_KEY as CLOCK_FAMILY,
    normalize_source_derived_next_daily_supply_frame_inputs_v1,
)

FAMILY_KEY = "current_unit_new_date_callback_entry_inputs_v1"
PROJECTION_KEY = "current_unit_new_date_entry_normalization_v1"
_SOURCE = "native_current_unit_new_date_callback_entry_inputs_12004"
_BOUNDARY = "current_query_before_unit_new_date_stage"
_IDS = ("subject_army_id_u32", "subject_carmy_id_u32")
_KEYS = {
    "schema_version", "source", "capture_boundary", "status", "ready",
    "unavailable_reason", *_IDS, "unit_route_count_i32",
}
_FALSE_FIELDS = (
    "actual_unit_new_date_callback_observed",
    "actual_movement_or_arrival_observed",
    "actual_future_frame_observed",
    "earlier_stage_outputs_reconstructed",
    "repeated_full_callback_effects_reconstructed",
    "full_daily_supply_transition_ready",
    "full_monthly_ready",
)
_VALUE = "conditional_unit_170_raw_after_next_new_date_entry_prefix"


def normalize_current_unit_new_date_callback_entry_inputs_v1(
    value: object, *, expected_army_id: int | None = None,
    expected_carmy_id: int | None = None,
) -> dict[str, object] | None:
    """Accept absent old packets and preserve the exact signed Unit+44 operand."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native Unit NewDate callback entry schema is malformed")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("native Unit NewDate callback entry schema_version is malformed")
    if value["source"] != _SOURCE or value["capture_boundary"] != _BOUNDARY:
        raise ValueError("native Unit NewDate callback entry source/boundary is malformed")
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    if not isinstance(status, str) or status not in {"available", "unavailable"} or type(ready) is not bool:
        raise ValueError("native Unit NewDate callback entry readiness is malformed")
    if ready != (status == "available") or (ready and reason is not None) or (
        not ready and (not isinstance(reason, str) or not reason)
    ):
        raise ValueError("native Unit NewDate callback entry reason disagrees with readiness")
    for key in _IDS:
        item = value[key]
        if item is not None and (type(item) is not int or not 0 <= item < (1 << 32)):
            raise ValueError(f"native Unit NewDate callback entry {key} must be uint32 or null")
    count = value["unit_route_count_i32"]
    if count is not None and (type(count) is not int or not -(1 << 31) <= count < (1 << 31)):
        raise ValueError("native Unit NewDate callback entry route count must be int32 or null")
    for key, expected in (
        ("subject_army_id_u32", expected_army_id),
        ("subject_carmy_id_u32", expected_carmy_id),
    ):
        if expected is not None and value[key] is not None and (
            type(expected) is not int or value[key] != (expected & 0xFFFFFFFF)
        ):
            raise ValueError(f"native Unit NewDate callback entry {key} differs from same-query row")
    if ready and (count is None or value["subject_army_id_u32"] is None):
        raise ValueError("ready native Unit NewDate callback entry has incomplete operands")
    return dict(value)


def project_current_unit_new_date_entry_normalization_v1(
    same_query_strength: dict[str, object],
) -> dict[str, object]:
    """Compute one prefix under held entry inputs; never simulate a full callback.

    The actual .4 prefix tests unsigned32(Unit+170 - 2) <= 1 and signed
    Unit+44 == 0 before writing Unit+170 = 0. Repeated stored IDs are
    opportunities, not completed callbacks. Only the first selected prefix
    value is projected: the unexpanded remainder may change state or route
    before a later opportunity. This date-free predicate does not require
    Source23 clock readiness.
    """
    army_id = same_query_strength.get("army_id")
    carmy_id = same_query_strength.get("native_carmy_id")
    entry = normalize_current_unit_new_date_callback_entry_inputs_v1(
        same_query_strength.get(FAMILY_KEY),
        expected_army_id=army_id, expected_carmy_id=carmy_id,
    )
    schedule = normalize_current_unit_new_date_schedule_inputs_v1(
        same_query_strength.get("current_unit_new_date_schedule_inputs_v1"),
        expected_army_id=army_id, expected_carmy_id=carmy_id,
    )
    budget = normalize_monthly_loss_budget_inputs_v1(
        same_query_strength.get("monthly_loss_budget_inputs_v1"),
    )
    clock = normalize_source_derived_next_daily_supply_frame_inputs_v1(
        same_query_strength.get(CLOCK_FAMILY),
        expected_army_id=army_id, expected_carmy_id=carmy_id,
    )
    raw_state = None if budget is None else budget["unit_native_170_raw"]
    route_count = None if entry is None else entry["unit_route_count_i32"]
    positions = None if schedule is None else schedule["subject_stored_id_positions"]
    reason = None
    if entry is None:
        reason = "current_unit_new_date_callback_entry_inputs_absent"
    elif not entry["ready"]:
        reason = entry["unavailable_reason"]
    elif schedule is None:
        reason = "current_unit_new_date_schedule_inputs_absent"
    elif not schedule["ready"]:
        reason = schedule["unavailable_reason"]
    elif raw_state is None:
        reason = "current_unit_native_170_raw_unavailable"
    ready = reason is None
    scheduled = None if schedule is None or not schedule["ready"] else bool(positions)
    output_state = None
    would_write = None
    if ready:
        # One first-entry prefix only; no full-callback threading across repeats.
        would_write = bool(scheduled and ((raw_state - 2) & 0xFFFFFFFF) <= 1 and route_count == 0)
        output_state = 0 if would_write else raw_state
    observed_clock = clock or {}
    return {
        "schema_version": 1,
        "source": "source_conditional_unit_new_date_entry_normalization_12004",
        "projection_boundary": "first_selected_unit_new_date_entry_prefix",
        "condition": "observed_schedule_receiver_state_and_route_count_held_at_first_selected_entry",
        "prefix_input_ready": ready,
        "unavailable_reason": reason,
        "subject_army_id_u32": None if entry is None else entry["subject_army_id_u32"],
        "subject_carmy_id_u32": None if entry is None else entry["subject_carmy_id_u32"],
        "unit_native_170_raw": raw_state,
        "unit_route_count_i32": route_count,
        "subject_stored_id_positions": None if positions is None else list(positions),
        "scheduled_by_observed_stored_ids": scheduled,
        _VALUE: output_state,
        "conditional_first_entry_prefix_would_write": would_write,
        "source_derived_full_cdate64_ready": observed_clock.get("source_derived_full_cdate64_ready", False),
        "source_derived_next_date_raw_i32": observed_clock.get("source_derived_next_date_raw_i32"),
        "source_derived_next_native_day_index_raw_i32": observed_clock.get("source_derived_next_native_day_index_raw_i32"),
        "source_derived_next_date_storage_raw64": observed_clock.get("source_derived_next_date_storage_raw64"),
        "source_derived_next_calendar_day_u8": observed_clock.get("source_derived_next_calendar_day_u8"),
        "source_derived_next_calendar_month_u8": observed_clock.get("source_derived_next_calendar_month_u8"),
        **{key: False for key in _FALSE_FIELDS},
    }
