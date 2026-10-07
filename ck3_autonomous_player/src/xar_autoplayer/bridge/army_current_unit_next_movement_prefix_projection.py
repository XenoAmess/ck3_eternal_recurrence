"""Conditional first Unit NewDate movement accumulation prefix, exact .4."""
from __future__ import annotations

from .army_current_unit_new_date_entry_normalization_projection import (
    FAMILY_KEY as ENTRY_FAMILY,
    normalize_current_unit_new_date_callback_entry_inputs_v1,
    project_current_unit_new_date_entry_normalization_v1,
)

PROJECTION_KEY = "current_unit_next_movement_prefix_v1"
VALUE_KEY = "conditional_unit_168_raw_after_next_new_date_movement_prefix"


def project_current_unit_next_movement_prefix_v1(
    same_query_strength: dict[str, object],
) -> dict[str, object]:
    """Project only the movement gate/ADD slice under held inputs at that gate.

    The unexpanded handler between the old entry prefix and this slice may
    alter a route. This value explicitly assumes the observed route, receiver,
    post-entry state and rate inputs hold at the movement gate. It observes
    neither a future callback nor route consumption/arrival.
    """
    # Reuse closed current DTOs after normal production row normalization.
    from .war_contract import (
        _normalize_current_movement_progress, _normalize_native_army_resolution_v1,
    )

    prefix = project_current_unit_new_date_entry_normalization_v1(same_query_strength)
    entry = normalize_current_unit_new_date_callback_entry_inputs_v1(
        same_query_strength.get(ENTRY_FAMILY),
        expected_army_id=same_query_strength.get("army_id"),
        expected_carmy_id=same_query_strength.get("native_carmy_id"),
    )
    movement = _normalize_current_movement_progress(
        same_query_strength.get("current_movement_progress"), name="current_movement_progress",
    ) or {}
    raw_resolution = same_query_strength.get("native_army_resolution_v1")
    resolution = None if raw_resolution is None else _normalize_native_army_resolution_v1(
        raw_resolution, name="native_army_resolution_v1",
    )
    weight = movement.get("accumulated_movement_weight_raw")
    cached = movement.get("cached_edge_speed_raw")
    current_edge = movement.get("current_edge_movement_rate_raw")
    reference = None if resolution is None else resolution["raw_reference"]
    count = None if entry is None else entry["unit_route_count_i32"]
    state = prefix["conditional_unit_170_raw_after_next_new_date_entry_prefix"]
    positions = prefix["subject_stored_id_positions"]
    scheduled = prefix["scheduled_by_observed_stored_ids"]
    reason = None
    output = None
    gate = None
    add_selected = None
    rate = None
    rate_source = None
    rate_demanded = False
    if scheduled is None:
        reason = "current_unit_new_date_schedule_inputs_unavailable"
    elif weight is None:
        reason = "current_unit_accumulated_movement_weight_unavailable"
    elif not scheduled:
        gate, add_selected, rate_source, output = "not_scheduled", False, "not_demanded", weight
    elif entry is None or not entry["ready"]:
        reason = "current_unit_new_date_callback_entry_inputs_absent" if entry is None else entry["unavailable_reason"]
    elif count == 0:
        # Conditional no ADD at this gate; the earlier empty-route handler is not simulated.
        gate, add_selected, rate_source, output = "route_zero", False, "not_demanded", weight
    else:
        if reference == -1:
            gate, add_selected = "direct_raw_unit178_absent", True
        elif state == 1:
            gate, add_selected = "direct_raw_unit170_1", True
        else:
            gate = "native_army_predicate_unresolved"
            reason = "unit_new_date_native_army_movement_admission_predicate_unavailable"
        if add_selected:
            if cached is None:
                reason = "current_unit_cached_edge_speed_unavailable"
            elif cached > 0:
                rate, rate_source = cached, "cached_unit_190"
            else:
                rate_demanded = True
                rate, rate_source = current_edge, "current_edge_getter"
                if rate is None:
                    reason = "current_edge_movement_rate_unavailable"
            if reason is None:
                bits = (weight + rate) & 0xFFFFFFFFFFFFFFFF
                output = bits - (1 << 64) if bits >= (1 << 63) else bits
    result = {
        "schema_version": 1,
        "source": "source_conditional_unit_next_movement_prefix_12004",
        "projection_boundary": "first_selected_unit_new_date_after_add168_before_edge_cost",
        "condition": "observed_schedule_receiver_and_post_entry_state_reference_route_weight_and_rate_held_at_movement_gate",
        "movement_prefix_input_ready": reason is None,
        "unavailable_reason": reason,
        "subject_army_id_u32": prefix["subject_army_id_u32"],
        "subject_carmy_id_u32": prefix["subject_carmy_id_u32"],
        "subject_stored_id_positions": positions,
        "scheduled_by_observed_stored_ids": scheduled,
        "unit_route_count_i32": count,
        "unit_native_178_raw_reference": reference,
        "conditional_unit_170_raw_after_next_new_date_entry_prefix": state,
        "accumulated_movement_weight_raw": weight,
        "cached_edge_speed_raw": cached,
        "current_edge_movement_rate_raw": current_edge,
        "movement_gate": gate,
        "movement_add_selected": add_selected,
        "current_edge_rate_demanded_by_conditional_prefix": rate_demanded,
        "selected_movement_rate_raw": rate,
        "movement_rate_source": rate_source,
        VALUE_KEY: output,
        "actual_unit_new_date_callback_observed": False,
        "actual_movement_or_arrival_observed": False,
        "actual_future_frame_observed": False,
        "earlier_stage_outputs_reconstructed": False,
        "intervening_empty_route_handler_reconstructed": False,
        "route_consumption_or_arrival_reconstructed": False,
        "repeated_full_callback_effects_reconstructed": False,
        "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
    for key in (
        "source_derived_full_cdate64_ready", "source_derived_next_date_raw_i32",
        "source_derived_next_native_day_index_raw_i32",
        "source_derived_next_date_storage_raw64", "source_derived_next_calendar_day_u8",
        "source_derived_next_calendar_month_u8",
    ):
        result[key] = prefix[key]
    return result
