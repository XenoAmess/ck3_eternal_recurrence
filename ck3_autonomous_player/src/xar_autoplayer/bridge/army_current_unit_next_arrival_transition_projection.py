"""Conditional first route pop and first local Unit20 province assignment."""
from __future__ import annotations

PROJECTION_KEY = "current_unit_next_arrival_transition_v1"
PROVINCE_TYPE_TAG = 0x50726F76


def project_current_unit_next_arrival_transition_v1(
    same_query_strength: dict[str, object], *,
    movement_prefix: dict[str, object],
    first_edge_selection: dict[str, object],
    army_context: dict[str, object] | None,
) -> dict[str, object]:
    """Reuse source30 results and the query-start current Army context.

    Values describe the first selected entry with its route, receiver, target
    and preceding operands held. The first Unit20 store assumes normal return
    of the reached pre-store external calls, whose effects are not simulated.
    It is not the final helper/callback state or an observed future arrival.
    """
    from .war_contract import _normalize_current_movement_progress

    movement = _normalize_current_movement_progress(
        same_query_strength.get("current_movement_progress"),
        name="current_movement_progress",
    ) or {}
    tag = movement.get("first_route_target_province_type_tag_u32")
    selected = first_edge_selection["conditional_first_edge_arrival_branch_selected"]
    progress = first_edge_selection["conditional_post_add_unit_168_raw"]
    cost = first_edge_selection["first_route_edge_weight_cost_raw"]
    context = army_context or {}
    current = context.get("current_province_id")
    route = context.get("route_province_ids")
    count = context.get("route_source_count")
    complete = context.get("route_read_status") in {"complete_empty", "complete_nonempty"}
    reason = None
    consumed = None
    residual = None
    remaining = None
    remaining_count = None
    write = None
    next_province = None
    tag_demanded = None

    if not first_edge_selection["first_edge_selection_input_ready"]:
        reason = first_edge_selection["unavailable_reason"] or "conditional_first_edge_selection_unavailable"
    elif selected is False:
        tag_demanded = False
        write = False
        residual = progress
        next_province = current
        if complete:
            remaining, remaining_count = list(route), count
    elif selected is True:
        tag_demanded = True
        if progress is not None and cost is not None:
            bits = (progress - cost) & 0xFFFFFFFFFFFFFFFF
            residual = bits - (1 << 64) if bits >= (1 << 63) else bits
        else:
            reason = "conditional_arrival_subtraction_inputs_unavailable"
        if complete and type(count) is int and count > 0 and len(route) == count:
            consumed = route[0]
            remaining, remaining_count = list(route[1:]), count - 1
        else:
            reason = reason or "complete_current_route_unavailable"
        if tag is None:
            reason = reason or "first_route_target_province_type_tag_unavailable"
        elif current is not None and consumed is not None:
            write = tag == PROVINCE_TYPE_TAG and consumed != current
            next_province = consumed if write else current
    else:
        reason = "conditional_first_edge_selection_unavailable"

    if not context or context.get("army_id") != same_query_strength["army_id"]:
        reason = "query_start_army_context_unavailable"
        write = False if selected is False else None
        next_province = None
    elif current is None:
        reason = reason or "current_province_id_unavailable"
        next_province = None

    return {
        "schema_version": 1,
        "source": "source_conditional_unit_next_arrival_transition_12004",
        "projection_boundary": "first_selected_unit_new_date_route_pop_and_first_unit20_assignment_24aec82",
        "condition": "observed_schedule_receiver_post_entry_operands_original_route_current_and_target_province_type_held_with_normal_prestore_callback_returns",
        "arrival_transition_input_ready": reason is None,
        "unavailable_reason": reason,
        "subject_army_id_u32": movement_prefix["subject_army_id_u32"],
        "subject_carmy_id_u32": movement_prefix["subject_carmy_id_u32"],
        "subject_stored_id_positions": movement_prefix["subject_stored_id_positions"],
        "scheduled_by_observed_stored_ids": movement_prefix["scheduled_by_observed_stored_ids"],
        "conditional_first_edge_arrival_branch_selected": selected,
        "selection_bypass": first_edge_selection["selection_bypass"],
        "conditional_post_add_unit_168_raw": progress,
        "first_route_edge_weight_cost_raw": cost,
        "current_province_id_existing": current,
        "current_route_province_ids_existing": route,
        "current_route_read_status_existing": context.get("route_read_status"),
        "current_route_source_count_existing": count,
        "first_route_target_province_type_tag_u32": tag,
        "target_type_tag_demanded_by_conditional_arrival": tag_demanded,
        "conditional_route_pop_selected": selected,
        "conditional_unit_168_raw_after_arrival_subtraction": residual,
        "conditional_consumed_first_route_province_id": consumed,
        "conditional_route_province_ids_after_first_pop": remaining,
        "conditional_unit_route_count_i32_after_first_pop": remaining_count,
        "conditional_first_province_assignment_selected": write,
        "conditional_current_province_id_after_first_assignment": next_province,
        "prestore_callback_normal_returns_condition": "reached_24e23e0_c46100_2479780_return_normally",
        "current_remaining_duration_days_existing": movement.get("first_route_edge_remaining_duration"),
        "current_committed_route_timeline_existing": movement.get("committed_route_timeline"),
        "actual_future_frame_observed": False,
        "actual_arrival_transition_observed": False,
        "final_helper_current_province_reconstructed": False,
        "unit30_or_unit160_reconstructed": False,
        "post_helper_state_or_progress_reconstructed": False,
        "clamp_reconstructed": False,
        "repeated_callback_effects_reconstructed": False,
        "full_unit_new_date_callback_ready": False,
        "native_action_executed": False,
        "earlier_stage_outputs_reconstructed": False,
        "intervening_empty_route_handler_reconstructed": False,
        "battle_contact_siege_effects_reconstructed": False,
        "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
