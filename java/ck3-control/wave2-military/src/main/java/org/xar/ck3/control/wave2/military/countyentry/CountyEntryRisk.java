package org.xar.ck3.control.wave2.military.countyentry;

import static org.xar.ck3.control.wave2.military.countyentry.CountyEntryInputs.*;
import static org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.*;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/** Held-input first-edge explanation; no route selection, native call or action qualification. */
public final class CountyEntryRisk {
    private CountyEntryRisk() { }

    /** The existing Service only supplies context when all three source revisions match. */
    public static RouteContext joinContext(Provenance query, QueryFrame snapshot, int armyId) {
        if (query == null || !query.complete() || snapshot == null || !query.equals(snapshot.provenance())) return null;
        RouteContext selected = null;
        for (RouteContext context : snapshot.playerArmies()) if (context.armyId() == armyId) selected = context;
        return selected;
    }

    public static Risk projectSameQuery(Strength strength, Provenance query, QueryFrame snapshot,
                                       MovementPrefix prefix, MovementOperands movement, PrestoreCall prestore) {
        return project(strength, joinContext(query, snapshot, strength.armyId()), prefix, movement, prestore);
    }

    public static Risk project(Strength strength, RouteContext context, MovementPrefix prefix,
                               MovementOperands movement, PrestoreCall prestore) {
        Objects.requireNonNull(strength); Objects.requireNonNull(movement); Objects.requireNonNull(prestore);
        CountyEntryInputs inputs = strength.countyInputs();
        AvailableBudget budget = inputs != null && inputs.budget() instanceof AvailableBudget value ? value : null;
        AvailableCondition condition = inputs != null && inputs.condition() instanceof AvailableCondition value ? value : null;
        String conditionReason = inputs != null && inputs.condition() instanceof UnavailableCondition value ? value.reason() : null;
        MultiplierFloors floors = inputs == null ? null : inputs.multiplierFloors().orElse(null);
        AvailableFloors knownFloors = floors instanceof AvailableFloors value ? value : null;
        boolean budgetReady = budget != null, floorReady = knownFloors != null;
        boolean emptyReader = budgetReady && "no_stored_route".equals(conditionReason);
        List<Integer> route = context == null ? null : context.routeProvinceIds();
        Integer count = context == null ? null : context.routeSourceCount();
        boolean fresh = context != null && context.armyId() == strength.armyId()
                && ("complete_empty".equals(context.routeReadStatus()) || "complete_nonempty".equals(context.routeReadStatus()))
                && route != null && count != null && count >= 0 && route.size() == count && context.currentProvinceId() != null;
        boolean ready = fresh && count > 0;
        boolean empty = fresh && count == 0 || emptyReader;
        boolean conditionReady = condition != null && ready && condition.sourceProvinceId() == context.currentProvinceId()
                && condition.targetProvinceId() == route.getFirst();
        List<Requirement> requirements = new ArrayList<>();
        if (!fresh) need(requirements, "same_query_player_armies.current_province_id/complete_route/revision", "fresh_route_context_unavailable");
        else if (!ready) need(requirements, "actual_legal_first_edge_and_its_native_county_condition", "observed_complete_route_is_empty_no_next_county_target");
        if (!budgetReady) need(requirements, "county_entry_inputs_v1",
                inputs != null && inputs.budget() instanceof UnavailableBudget unavailable ? unavailable.reason() : "current_native_county_budget_absent",
                "current_native_budget_explanation");

        List<Predicate> predicates = new ArrayList<>();
        Boolean call = ready ? prestore.selected() : null;
        predicate(predicates, "arrival_prestore_county_call", value(call), call, "existing_arrival_prestore_consumer_24aec3f");
        String[] typedFields = {"current_province_type_tag_u32", "unit_kind_18_raw_i32", "first_route_target_province_type_tag_u32"};
        Boolean[] typedChecks = {equal(movement.currentProvinceType(), 0x50726F76L), equal(movement.unitKind(), 0), equal(movement.targetProvinceType(), 0x50726F76L)};
        Boolean distinct = ready ? !route.getFirst().equals(context.currentProvinceId()) : null;
        Boolean edgeCall = ready ? all(typedChecks[0], typedChecks[1], typedChecks[2], distinct) : null;
        predicate(predicates, "county_call_eligible_if_this_edge_arrives", value(edgeCall), edgeCall,
                "existing_arrival_helper_typed_current_unitkind0_distinct_typed_target_gates");
        String[] byteFields = {"first_route_target_province_definition_byte_1b_u8", "current_province_definition_byte_1b_u8"};
        Integer[] byteValues = {movement.targetDefinitionByte(), movement.currentDefinitionByte()};
        Boolean[] bytePasses = new Boolean[2];
        for (int index = 0; index < 2; index++) {
            bytePasses[index] = byteValues[index] == null ? null : byteValues[index] != 0;
            predicate(predicates, byteFields[index], value(byteValues[index]), bytePasses[index], "24e23e0_definition_1b_admission");
        }
        boolean prefixMatches = prefix != null && prefix.ready() && prefix.armyId() != null
                && prefix.armyId() == (long) strength.armyId()
                && (prefix.nativeCarmyId() == null && strength.nativeCarmyId() == null
                    || prefix.nativeCarmyId() != null && strength.nativeCarmyId() != null
                    && prefix.nativeCarmyId() == (long) strength.nativeCarmyId());
        Long state = prefixMatches ? prefix.conditionalUnit170() : null;
        Integer special = state == null ? null : state > 0 ? 1 : 0;
        Boolean specialZero = special == null ? null : special == 0;
        predicate(predicates, "conditional_arrival_special_flag_zero", value(special), specialZero,
                "24ab93e_943_948_descriptor1_prior_signed170_gt0_then24aec3f_r9b");
        Boolean conditionValue = conditionReady ? condition.passes() : null;
        predicate(predicates, "native_current_route_county_condition", value(conditionValue), conditionValue,
                "24e2230_actual_actor_old_first_target_mode");
        Boolean admission = ready ? all(call, bytePasses[0], bytePasses[1], specialZero, conditionValue) : null;
        Boolean edgeAdmission = ready ? all(edgeCall, bytePasses[0], bytePasses[1], specialZero, conditionValue) : null;
        Boolean positive = budgetReady ? budget.currentLossBudget() > 0 : null;
        Boolean selected = ready ? all(admission, positive) : null;
        Boolean edgePositive = ready ? all(edgeAdmission, positive) : null;
        if (!Boolean.FALSE.equals(edgeAdmission) && !Boolean.FALSE.equals(positive)) {
            for (int index = 0; index < typedFields.length; index++) if (typedChecks[index] == null)
                need(requirements, "current_movement_progress." + typedFields[index], "typed_county_call_eligibility_if_edge_arrives_unavailable");
            if (call == null) need(requirements, "current_unit_arrival_prestore_disembark_write_v1.conditional_prestore_24e23e0_call_selected",
                    prestore.unavailableReason() == null ? "conditional_prestore_call_unavailable" : prestore.unavailableReason(), "next_entry_arrival_timing");
            for (int index = 0; index < byteFields.length; index++) if (bytePasses[index] == null)
                need(requirements, "current_movement_progress." + byteFields[index], "county_definition_admission_byte_unavailable");
            if (special == null) need(requirements,
                    "current_unit_next_movement_prefix_v1.conditional_unit_170_raw_after_next_new_date_entry_prefix",
                    "same_query_post_entry_state_required_for_conditional_arrival_descriptor");
            if (!conditionReady) need(requirements, "county_entry_inputs_v1.condition",
                    conditionReason == null ? "condition_does_not_join_current_first_edge" : conditionReason);
        }

        Long multiplier = budgetReady ? budget.minimumMultiplierRaw() : null;
        Integer flag = floorReady ? knownFloors.army1d4Raw() : null;
        Boolean zero = null;
        String zeroBasis = "not_observed_or_deducible";
        if (flag != null && flag == 0) { zero = false; zeroBasis = "24dd830_returns_false_when_raw_army1d4_zero"; }
        else if (multiplier != null && multiplier != 0) { zero = false; zeroBasis = "24dd9a0_true_predicate_would_return_exact_zero"; }
        else if (flag != null && multiplier != null && multiplier == 0 && knownFloors.army1d4NonzeroFloorRaw() > 0) {
            zero = true; zeroBasis = "nonzero_flag_false_path_signed_max_with_positive_loaded_second_floor_cannot_return_zero";
        }
        // Java long subtraction has the exact native signed64 wrapping semantics.
        Long ordinary = floorReady && flag == 0 && multiplier != null && multiplier > knownFloors.baseFloorRaw()
                ? multiplier - 100_000L : null;
        if (!floorReady) need(requirements, "county_entry_inputs_v1.multiplier_floor_inputs_v1",
                floors instanceof UnavailableFloors unavailable ? unavailable.reason() : "loaded_multiplier_floors_absent", "multiplier_branch_explanation");
        if (zero == null) need(requirements, "native24dd830_result_or_exact_dynamic_owner_government_situation_inputs",
                "M_zero_alone_does_not_identify_the_zero_predicate", "multiplier_branch_explanation");

        Allocation allocation = new Allocation(false, null, null, null, null, null);
        LossPartition loss = strength.lossPartition();
        if (budgetReady && loss != null && loss.available() && Objects.equals(loss.wholeSoldiers(), strength.currentSoldiers())
                && loss.preferredSoldiers() != null && loss.preferredSoldiers() >= 0 && loss.preferredSoldiers() <= strength.currentSoldiers()) {
            int primary = Math.min(budget.currentLossBudget(), loss.preferredSoldiers()), residual = budget.currentLossBudget() - primary;
            allocation = new Allocation(true, loss.preferredSoldiers(), primary, residual, all(edgeAdmission, primary > 0), all(edgeAdmission, residual > 0));
        } else if (!Boolean.FALSE.equals(edgePositive)) need(requirements, "loss_application_inputs_v1.definition_le_zero_soldiers+same_whole_soldiers",
                "preferred_and_residual_partition_unavailable", "request_source_preselection");
        Review review; String reason;
        if (empty) { review = Review.NO_CURRENT_FIRST_EDGE_TO_ASSESS; reason = "observed_complete_empty_route_has_no_next_county_target"; }
        else if (Boolean.TRUE.equals(edgePositive)) { review = Review.REVIEW_CURRENT_EDGE_BEFORE_ADVANCING; reason = "positive_native_county_budget_if_this_edge_arrives_under_held_inputs"; }
        else if (Boolean.FALSE.equals(edgePositive) && ready) { review = Review.NO_POSITIVE_COUNTY_BUDGET_ON_THIS_LOCAL_BRANCH; reason = "a_source_admission_gate_rejects_or_current_native_budget_is_zero"; }
        else { review = Review.OBTAIN_MISSING_CURRENT_OBSERVATIONS; reason = "next_edge_county_budget_selection_unresolved"; }
        Boolean firstEdge = empty ? Boolean.FALSE : fresh ? Boolean.valueOf(count > 0) : null;
        Boolean secondDemanded = null;
        if (flag != null && flag == 0 || Boolean.TRUE.equals(zero)) secondDemanded = false;
        else if (flag != null && Boolean.FALSE.equals(zero)) secondDemanded = true;
        return new Risk(edgePositive != null && ready ? Status.AVAILABLE : inputs != null ? Status.PARTIAL : Status.UNAVAILABLE,
                strength, budgetReady, floorReady, fresh, ready, firstEdge, empty,
                emptyReader ? "native_county_reader_complete_empty_route" : empty ? "same_query_army_context_complete_empty" : null,
                fresh ? context.currentProvinceId() : null, ready ? route.getFirst() : null, admission, selected, edgeAdmission, edgePositive,
                Boolean.FALSE.equals(selected) && !Boolean.FALSE.equals(edgePositive), state, predicates, new ZeroPredicate(zero, zeroBasis),
                new MultiplierExplanation(zero == null ? null : !zero, secondDemanded, ordinary),
                allocation, new Decision(review, reason, !Boolean.FALSE.equals(edgePositive), empty), requirements);
    }

    private static Boolean equal(Number value, long expected) { return value == null ? null : value.longValue() == expected; }
    private static Boolean all(Boolean... values) {
        List<Boolean> entries = Arrays.asList(values);
        if (entries.contains(Boolean.FALSE)) return false;
        if (entries.contains(null)) return null;
        return true;
    }
    private static Value value(Boolean observed) { return observed == null ? null : new BooleanValue(observed); }
    private static Value value(Integer observed) { return observed == null ? null : new IntegerValue(observed.longValue()); }
    private static void predicate(List<Predicate> values, String name, Value value, Boolean passed, String source) { values.add(new Predicate(name, value, passed, source)); }
    private static void need(List<Requirement> values, String field, String reason) { need(values, field, reason, "conditional_route_budget"); }
    private static void need(List<Requirement> values, String field, String reason, String purpose) {
        Requirement value = new Requirement(field, reason, purpose); if (!values.contains(value)) values.add(value);
    }
}
