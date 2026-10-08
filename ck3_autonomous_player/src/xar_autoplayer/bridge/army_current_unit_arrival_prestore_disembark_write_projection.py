"""Source-conditional local arrival pre-store fixed disembark-days write."""
from __future__ import annotations

PROJECTION_KEY = "current_unit_arrival_prestore_disembark_write_v1"
RAW_FIELDS = (
    "current_province_type_tag_u32",
    "unit_kind_18_raw_i32",
    "current_province_definition_byte_1b_u8",
    "first_route_target_province_definition_byte_1b_u8",
    "loaded_disembark_penalty_days_rule_i32",
)


def project_current_unit_arrival_prestore_disembark_write_v1(
    same_query_strength: dict[str, object], *,
    arrival_transition: dict[str, object],
    army_context: dict[str, object] | None,
) -> dict[str, object]:
    """Reuse the identical Source31 result; do not invoke departure/arrival.

    At the held local stage, target definition byte!=0 and current byte==0
    select Army1D0:=loaded signed32 rule. Reached prior calls must return
    normally. A skipped node does not prove final days stay unchanged; neither
    prior170, Fleet validity nor current remaining-days readiness selects this
    particular write value.
    """
    from .war_contract import _normalize_current_movement_progress
    from .army_current_disembark_penalty_contract import normalize_current_disembark_penalty_v1

    movement = _normalize_current_movement_progress(
        same_query_strength.get("current_movement_progress"),
        name="current_movement_progress",
    ) or {}
    observed_days = same_query_strength.get("current_disembark_penalty_v1")
    if observed_days is not None:
        observed_days = normalize_current_disembark_penalty_v1(observed_days)
    raw = {key: movement.get(key) for key in RAW_FIELDS}
    demands = {key: False for key in RAW_FIELDS}
    helper_selected = arrival_transition["conditional_first_province_assignment_selected"]

    def evaluate() -> tuple[bool | None, bool | None, int | None, str | None]:
        if not arrival_transition["arrival_transition_input_ready"]:
            return None, None, None, (
                arrival_transition["unavailable_reason"] or "source31_arrival_transition_unavailable"
            )
        if helper_selected is False:
            return False, False, None, None
        if helper_selected is not True:
            return None, None, None, "source31_typed_distinct_target_unavailable"

        key = "current_province_type_tag_u32"
        demands[key] = True
        if raw[key] is None:
            return None, None, None, "current_province_type_tag_unavailable"
        if raw[key] != 0x50726F76:
            return False, False, None, None

        key = "unit_kind_18_raw_i32"
        demands[key] = True
        if raw[key] is None:
            return None, None, None, "unit_kind_18_raw_unavailable"
        if raw[key] != 0:
            return False, False, None, None

        key = "first_route_target_province_definition_byte_1b_u8"
        demands[key] = True
        if raw[key] is None:
            return True, None, None, "first_route_target_province_definition_byte_1b_unavailable"
        if raw[key] == 0:
            return True, False, None, None

        key = "current_province_definition_byte_1b_u8"
        demands[key] = True
        if raw[key] is None:
            return True, None, None, "current_province_definition_byte_1b_unavailable"
        if raw[key] != 0:
            return True, False, None, None

        key = "loaded_disembark_penalty_days_rule_i32"
        demands[key] = True
        if raw[key] is None:
            return True, True, None, "loaded_disembark_penalty_days_rule_unavailable"
        return True, True, raw[key], None

    call, write, value, reason = evaluate()
    context = army_context or {}
    return {
        "schema_version": 1,
        "source": "source_conditional_unit_arrival_prestore_disembark_write_12004",
        "projection_boundary": "first_selected_arrival_prestore_local_army1d0_fixed_write_24e2822",
        "condition": "same_query_source31_receiver_original_route_current_and_target_province_definition_operands_held_with_normal_prior_call_returns",
        "fixed_disembark_write_input_ready": reason is None,
        "unavailable_reason": reason,
        "subject_army_id_u32": arrival_transition["subject_army_id_u32"],
        "subject_carmy_id_u32": arrival_transition["subject_carmy_id_u32"],
        "subject_stored_id_positions": arrival_transition["subject_stored_id_positions"],
        "source31_first_province_assignment_selected_existing": helper_selected,
        "current_province_id_existing": context.get("current_province_id"),
        "current_route_province_ids_existing": context.get("route_province_ids"),
        **raw,
        "raw_input_demanded_by_conditional_fixed_write": demands,
        "conditional_prestore_24e23e0_call_selected": call,
        "conditional_fixed_disembark_days_write_selected": write,
        "conditional_disembark_days_fixed_write_value_i32": value,
        "loaded_days_rule_demanded_by_conditional_fixed_write": demands["loaded_disembark_penalty_days_rule_i32"],
        "observed_current_disembark_penalty_existing": observed_days,
        "prior170_or_descriptor1_demanded_by_fixed_write": False,
        "native_fleet_validity_demanded_by_fixed_write": False,
        "current_remaining_days_readiness_demanded_by_fixed_write": False,
        "descriptor_byte2_caller_constant": 0,
        "current_remaining_duration_days_existing": movement.get("first_route_edge_remaining_duration"),
        "actual_future_frame_observed": False,
        "actual_prestore_callback_executed": False,
        "actual_fixed_disembark_write_observed": False,
        "final_disembark_penalty_reconstructed": False,
        "final_arrival_reconstructed": False,
        "final_helper_current_province_reconstructed": False,
        "unit30_or_unit160_reconstructed": False,
        "recursive_other_unit_arrival_reconstructed": False,
        "full_unit_new_date_callback_ready": False,
        "repeated_callback_effects_reconstructed": False,
        "battle_contact_supply_day_effects_reconstructed": False,
        "native_action_executed": False,
    }
