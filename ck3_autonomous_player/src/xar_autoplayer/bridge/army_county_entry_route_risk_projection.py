"""County risk at the existing source-conditional first-arrival consumer seam.

This consumes one normalized query; it never previews a route, chooses a new
destination, queries CK3 or treats a native budget as a physical loss ledger.
"""
from __future__ import annotations

from .army_county_entry_inputs_contract import normalize_army_county_entry_inputs_v1


def _all(values: list[bool | None]) -> bool | None:
    return False if False in values else None if None in values else True


def project_county_entry_route_risk_v1(
    same_query_strength: dict[str, object], *,
    arrival_transition: dict[str, object],
    army_context: dict[str, object] | None,
    movement_prefix: dict[str, object] | None,
    prestore_call_selected: bool | None,
    prestore_unavailable_reason: str | None,
    movement_inputs: dict[str, object],
) -> dict[str, object]:
    """Explain the current native B and a conditional first-edge admission.

    The same query's post-entry state is held until the arrival descriptor;
    descriptor byte1 is prior signed Unit170>0. Unexpanded earlier handlers and
    future modifier/roster/route changes are not simulated. The existing Service
    supplies Army context only when query/snapshot/native revisions all match.
    """
    context = army_context or {}
    prefix = movement_prefix or {}
    raw = same_query_strength.get("county_entry_inputs_v1")
    current = same_query_strength.get("current_soldiers")
    inputs = None
    if raw is not None and same_query_strength.get("status") == "available":
        inputs = normalize_army_county_entry_inputs_v1(raw, current_soldiers=current)
    inputs = inputs or {}
    budget_ready = inputs.get("status") == "available"
    condition = inputs.get("condition") or {}
    empty_route_from_county_reader = budget_ready and condition.get("status") == "unavailable" and (
        condition.get("unavailable_reason") == "no_stored_route")
    floors = inputs.get("multiplier_floor_inputs_v1")
    floor_ready = isinstance(floors, dict) and floors["status"] == "available"
    route = context.get("route_province_ids")
    count = context.get("route_source_count")
    fresh_context = (
        context.get("army_id") == same_query_strength.get("army_id")
        and context.get("route_read_status") in {"complete_empty", "complete_nonempty"}
        and isinstance(route, list) and type(count) is int and count >= 0 and len(route) == count
        and type(context.get("current_province_id")) is int
    )
    context_ready = fresh_context and count > 0
    observed_empty_route = (fresh_context and count == 0) or empty_route_from_county_reader
    # The route condition DTO itself binds both Province IDs. No target is
    # inferred from an old order or a map name when this join is unavailable.
    condition_ready = condition.get("status") == "available" and context_ready and (
        condition["source_province_id"] == context["current_province_id"]
        and condition["target_province_id"] == route[0]
    )
    requirements = []

    def need(field: str, reason: str, purpose: str = "conditional_route_budget") -> None:
        item = {"field": field, "reason": reason, "needed_for": purpose}
        if item not in requirements:
            requirements.append(item)

    if not fresh_context:
        need("same_query_player_armies.current_province_id/complete_route/revision", "fresh_route_context_unavailable")
    elif not context_ready:
        need("actual_legal_first_edge_and_its_native_county_condition", "observed_complete_route_is_empty_no_next_county_target")
    if not budget_ready:
        need("county_entry_inputs_v1", inputs.get("unavailable_reason") or "current_native_county_budget_absent",
             "current_native_budget_explanation")

    predicates = []

    def predicate(name: str, value: object, passed: bool | None, source: str) -> None:
        predicates.append({"name": name, "value": value, "passes": passed, "source": source})

    call = prestore_call_selected if context_ready else None
    predicate("arrival_prestore_county_call", call, call, "existing_arrival_prestore_consumer_24aec3f")
    typed_fields = (
        ("current_province_type_tag_u32", 0x50726F76),
        ("unit_kind_18_raw_i32", 0),
        ("first_route_target_province_type_tag_u32", 0x50726F76),
    )
    typed_checks = [movement_inputs.get(key) == expected if type(movement_inputs.get(key)) is int else None
                    for key, expected in typed_fields]
    distinct = route[0] != context["current_province_id"] if context_ready else None
    edge_call = _all([*typed_checks, distinct]) if context_ready else None
    predicate("county_call_eligible_if_this_edge_arrives", edge_call, edge_call,
              "existing_arrival_helper_typed_current_unitkind0_distinct_typed_target_gates")
    byte_passes = []
    for field in ("first_route_target_province_definition_byte_1b_u8", "current_province_definition_byte_1b_u8"):
        value = movement_inputs.get(field)
        passed = value != 0 if type(value) is int else None
        predicate(field, value, passed, "24e23e0_definition_1b_admission")
        byte_passes.append(passed)

    state = prefix.get("conditional_unit_170_raw_after_next_new_date_entry_prefix")
    prefix_matches = prefix.get("movement_prefix_input_ready") is True and (
        prefix.get("subject_army_id_u32") == same_query_strength.get("army_id")
        and prefix.get("subject_carmy_id_u32") == same_query_strength.get("native_carmy_id")
    )
    special = int(state > 0) if prefix_matches and type(state) is int else None
    predicate("conditional_arrival_special_flag_zero", special,
              special == 0 if special is not None else None,
              "24ab93e_943_948_descriptor1_prior_signed170_gt0_then24aec3f_r9b")
    condition_value = condition.get("passes") if condition_ready else None
    predicate("native_current_route_county_condition", condition_value, condition_value,
              "24e2230_actual_actor_old_first_target_mode")
    admission = _all([call, *byte_passes, special == 0 if special is not None else None, condition_value]) if context_ready else None
    edge_admission = _all([edge_call, *byte_passes, special == 0 if special is not None else None, condition_value]) if context_ready else None
    positive = inputs.get("current_loss_budget", 0) > 0 if budget_ready else None
    selected = _all([admission, positive]) if context_ready else None
    edge_positive = _all([edge_admission, positive]) if context_ready else None
    if edge_admission is not False and positive is not False:
        for (field, _), passed in zip(typed_fields, typed_checks):
            if passed is None:
                need("current_movement_progress." + field, "typed_county_call_eligibility_if_edge_arrives_unavailable")
        if call is None:
            need("current_unit_arrival_prestore_disembark_write_v1.conditional_prestore_24e23e0_call_selected",
                 prestore_unavailable_reason or "conditional_prestore_call_unavailable", "next_entry_arrival_timing")
        for field, passed in zip(("first_route_target_province_definition_byte_1b_u8", "current_province_definition_byte_1b_u8"), byte_passes):
            if passed is None:
                need("current_movement_progress." + field, "county_definition_admission_byte_unavailable")
        if special is None:
            need("current_unit_next_movement_prefix_v1.conditional_unit_170_raw_after_next_new_date_entry_prefix",
                 "same_query_post_entry_state_required_for_conditional_arrival_descriptor")
        if not condition_ready:
            need("county_entry_inputs_v1.condition", condition.get("unavailable_reason") or "condition_does_not_join_current_first_edge")

    multiplier = inputs.get("minimum_multiplier_raw") if budget_ready else None
    flag = floors["army_1d4_raw"] if floor_ready else None
    zero_predicate, zero_basis = None, "not_observed_or_deducible"
    if flag == 0:
        zero_predicate, zero_basis = False, "24dd830_returns_false_when_raw_army1d4_zero"
    elif multiplier is not None and multiplier != 0:
        zero_predicate, zero_basis = False, "24dd9a0_true_predicate_would_return_exact_zero"
    elif flag is not None and multiplier == 0 and floors["army_1d4_nonzero_floor_raw"] > 0:
        zero_predicate, zero_basis = True, "nonzero_flag_false_path_signed_max_with_positive_loaded_second_floor_cannot_return_zero"
    ordinary_property = None
    if floor_ready and flag == 0 and multiplier is not None and multiplier > floors["base_floor_raw"]:
        bits = (multiplier - 100_000) & 0xFFFFFFFFFFFFFFFF
        ordinary_property = bits - (1 << 64) if bits >= (1 << 63) else bits
    if not floor_ready:
        need("county_entry_inputs_v1.multiplier_floor_inputs_v1",
             floors.get("unavailable_reason") if isinstance(floors, dict) else "loaded_multiplier_floors_absent",
             "multiplier_branch_explanation")
    if zero_predicate is None:
        need("native24dd830_result_or_exact_dynamic_owner_government_situation_inputs",
             "M_zero_alone_does_not_identify_the_zero_predicate", "multiplier_branch_explanation")

    allocation = {"ready": False, "preferred_definition_le_zero_soldiers": None,
                  "primary_budget_soldiers": None, "residual_budget_soldiers": None,
                  "conditional_primary_positive_budget": None, "conditional_residual_allocator_selected": None,
                  "raw_county_primary_return_rva": 0x24E25EE, "raw_county_residual_outer_return_rva": 0x24E2630,
                  "actual_physical_debit_soldiers": None}
    losses = same_query_strength.get("loss_application_inputs_v1") or {}
    preferred = losses.get("definition_le_zero_soldiers")
    if budget_ready and losses.get("status") == "available" and (
        losses.get("whole_soldiers") == current and type(preferred) is int and 0 <= preferred <= current
    ):
        budget = inputs["current_loss_budget"]
        primary = min(budget, preferred)
        residual = budget - primary
        allocation.update(ready=True, preferred_definition_le_zero_soldiers=preferred,
                          primary_budget_soldiers=primary, residual_budget_soldiers=residual,
                          conditional_primary_positive_budget=_all([edge_admission, primary > 0]),
                          conditional_residual_allocator_selected=_all([edge_admission, residual > 0]))
    elif edge_positive is not False:
        need("loss_application_inputs_v1.definition_le_zero_soldiers+same_whole_soldiers",
             "preferred_and_residual_partition_unavailable", "request_source_preselection")

    if observed_empty_route:
        decision, reason = "no_current_first_edge_to_assess", "observed_complete_empty_route_has_no_next_county_target"
    elif edge_positive is True:
        decision, reason = "review_current_edge_before_advancing", "positive_native_county_budget_if_this_edge_arrives_under_held_inputs"
    elif edge_positive is False and context_ready:
        decision, reason = "no_positive_county_budget_on_this_local_branch", "a_source_admission_gate_rejects_or_current_native_budget_is_zero"
    else:
        decision, reason = "obtain_missing_current_observations", "next_edge_county_budget_selection_unresolved"
    choices = []
    if edge_positive is not False:
        choices = [
            {"choice": "keep_paused_for_current_edge_review", "target_province_id": None,
             "source_basis": "no_arrival_callback_without_this_edge_being_taken",
             "effect_boundary": "defers_this_conditional_entry_only_other_war_and_supply_costs_not_evaluated",
             "physical_soldier_saving": None},
            {"choice": "compare_an_already_observed_legal_alternative_first_edge", "target_province_id": None,
             "source_basis": "county_admission_depends_on_actual_old_target_definition_bytes_and24e2230",
             "avoidance_criterion": "observed_candidate_definition1b_zero_or_native24e2230_false_bypasses_the_county_budget_under_held_inputs",
             "requires": ["same_frame_legal_native_route_preview", "actual_candidate_first_edge_24e2230_condition_and_definition_bytes",
                          "fresh_budget_after_any_current_army_or_modifier_change"],
             "physical_soldier_saving": None},
        ]
    if observed_empty_route:
        choices = [{"choice": "obtain_native_legal_route_preview_before_selecting_any_target",
                    "target_province_id": None,
                    "requires": ["observed_legal_candidate_first_edge", "actual_candidate_county_condition_and_definition_bytes"],
                    "physical_soldier_saving": None}]
    return {
        "schema_version": 1, "source": "same_query_conditional_county_first_edge_risk_12004",
        "source_contract_game_version": "1.20.0.4",
        "status": "available" if edge_positive is not None and context_ready else "partial" if inputs else "unavailable",
        "current_native_budget_ready": budget_ready,
        "conditional_budget_selection_ready": edge_positive is not None and context_ready,
        "loaded_multiplier_floor_inputs_ready": floor_ready,
        "army_id": same_query_strength.get("army_id"), "native_carmy_id": same_query_strength.get("native_carmy_id"),
        "fresh_route_context_ready": fresh_context,
        "first_route_edge_present": False if observed_empty_route else bool(count) if fresh_context else None,
        "observed_complete_empty_route": observed_empty_route,
        "empty_route_evidence": "native_county_reader_complete_empty_route" if empty_route_from_county_reader else "same_query_army_context_complete_empty" if observed_empty_route else None,
        "current_province_id": context.get("current_province_id") if fresh_context else None,
        "first_route_target_province_id": route[0] if context_ready else None,
        "observed_current_native_budget": {key: inputs.get(key) for key in
            ("status", "unavailable_reason", "whole_soldiers", "current_loss_budget", "effective_fraction_raw",
             "minimum_multiplier_raw", "loaded_minimum_soldiers")},
        "observed_loaded_multiplier_floors": dict(floors) if isinstance(floors, dict) else None,
        "conditional_admission": admission, "conditional_positive_county_budget_selected": selected,
        "conditional_edge_admission_if_arrival": edge_admission,
        "conditional_positive_county_budget_if_this_edge_arrives": edge_positive,
        "next_entry_no_arrival_does_not_prove_route_county_budget_zero": selected is False and edge_positive is not False,
        "conditional_prior_unit170_at_arrival_descriptor": state if prefix_matches else None,
        "predicates": predicates,
        "multiplier_zero_predicate": {"passes": zero_predicate, "basis": zero_basis,
            "native_predicate_rva": 0x24DD830, "formal_army1d4_and_army1d8_types": "unknown"},
        "multiplier_branch_explanation": {
            "base_floor_demanded": not zero_predicate if zero_predicate is not None else None,
            "army_1d4_nonzero_floor_demanded": False if flag == 0 or zero_predicate is True else True if flag is not None and zero_predicate is False else None,
            "inferred_ordinary_army_property_1a7_raw": ordinary_property,
            "ordinary_property_inference_basis": "raw1d4_zero_and_M_strictly_above_loaded_base_floor_inverts_wrap64_100000_plus_A" if ordinary_property is not None else None,
            "unobserved_other_modifier_values": ["ArmyProperty1A8", "PC_Army1D8_object_plus280_key1A8"],
        },
        "conditional_allocation": allocation,
        "decision": {"review": decision, "reason": reason, "selected_new_target_province_id": None,
                     "readonly_choices": choices},
        "required_observations": requirements,
        "held_input_condition": "same_query_army_route_roster_modifiers_post_entry_state_and_county_operands_hold_until_first_arrival_with_normal_prior_returns",
        "actual_arrival_observed": False, "actual_county_loss_observed": False,
        "army_or_wallet_net_change_used": False, "native_action_executed": False,
        "route_overall_safe": None, "complete_county_or_periodic_loss": None,
    }
