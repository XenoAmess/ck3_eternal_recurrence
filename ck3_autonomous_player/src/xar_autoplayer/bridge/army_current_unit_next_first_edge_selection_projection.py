"""Conditional first Unit NewDate edge selection under held current inputs."""
from __future__ import annotations

PROJECTION_KEY = "current_unit_next_first_edge_selection_v1"


def project_current_unit_next_first_edge_selection_v1(
    same_query_strength: dict[str, object], *,
    movement_prefix: dict[str, object],
) -> dict[str, object]:
    """Use the already-calculated first movement prefix, without rerunning it.

    The actual source compares signed post-ADD168 with a distinct signed cost.
    At or below cost it tests the static provider byte; above cost does not
    demand that byte. Current cost excludes168 in its closed body, but its
    route/region context and the other observed operands must remain held.
    This selects a branch conditionally; it does not execute arrival effects.
    """
    from .war_contract import _normalize_current_movement_progress

    movement = _normalize_current_movement_progress(
        same_query_strength.get("current_movement_progress"),
        name="current_movement_progress",
    ) or {}
    cost = movement.get("first_route_edge_weight_cost_raw")
    provider = movement.get("first_edge_arrival_provider_byte_e_u8")
    progress = movement_prefix["conditional_unit_168_raw_after_next_new_date_movement_prefix"]
    selected = None
    provider_demanded = None
    bypass = None
    reason = None
    if not movement_prefix["movement_prefix_input_ready"]:
        reason = movement_prefix["unavailable_reason"] or "conditional_movement_prefix_unavailable"
    elif movement_prefix["scheduled_by_observed_stored_ids"] is False:
        # No selected entry under the same observed schedule.
        selected, provider_demanded = False, False
        bypass = "not_scheduled_by_observed_stored_ids"
    elif movement_prefix["movement_gate"] == "route_zero":
        # The unexpanded earlier empty-route handler is not reconstructed.
        selected, provider_demanded = False, False
        bypass = "route_zero_under_inputs_held_at_movement_gate"
    elif progress is None:
        reason = "conditional_post_add_unit_168_unavailable"
    elif cost is None:
        reason = "first_route_edge_weight_cost_unavailable"
    elif progress > cost:
        selected, provider_demanded = True, False
    else:
        provider_demanded = True
        if provider is None:
            reason = "first_edge_arrival_provider_byte_e_unavailable"
        else:
            selected = provider != 0
    return {
        "schema_version": 1,
        "source": "source_conditional_unit_next_first_edge_selection_12004",
        "projection_boundary": "first_selected_unit_new_date_after_add168_before_arrival_subtraction",
        "condition": "observed_schedule_receiver_route_and_post_entry_movement_operands_cost_context_provider_held_at_first_edge_selection",
        "first_edge_selection_input_ready": reason is None,
        "unavailable_reason": reason,
        "subject_army_id_u32": movement_prefix["subject_army_id_u32"],
        "subject_carmy_id_u32": movement_prefix["subject_carmy_id_u32"],
        "subject_stored_id_positions": movement_prefix["subject_stored_id_positions"],
        "scheduled_by_observed_stored_ids": movement_prefix["scheduled_by_observed_stored_ids"],
        "unit_route_count_i32": movement_prefix["unit_route_count_i32"],
        "movement_add_selected": movement_prefix["movement_add_selected"],
        "selection_bypass": bypass,
        "conditional_post_add_unit_168_raw": progress,
        "first_route_edge_weight_cost_raw": cost,
        "first_edge_arrival_provider_byte_e_u8": provider,
        "provider_byte_demanded_by_conditional_first_edge_selection": provider_demanded,
        "conditional_first_edge_arrival_branch_selected": selected,
        "current_remaining_duration_days_existing": movement.get("first_route_edge_remaining_duration"),
        "actual_future_frame_observed": False,
        "actual_first_edge_selection_observed": False,
        "actual_first_edge_arrival_observed": False,
        "post_selection_subtraction_reconstructed": False,
        "route_consumption_reconstructed": False,
        "clamp_reconstructed": False,
        "repeated_callback_effects_reconstructed": False,
        "full_unit_new_date_callback_ready": False,
        "native_action_executed": False,
        "earlier_stage_outputs_reconstructed": False,
        "intervening_empty_route_handler_reconstructed": False,
        "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
