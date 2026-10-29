package org.xar.ck3.control.wave2.military.countyentry;

import static org.xar.ck3.control.wave2.military.countyentry.CountyEntryInputs.*;
import static org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict native subblock codec; outer SDK containers use only declared field projections. */
public final class CountyEntryCodec {
    private static final List<String> BUDGET = List.of("whole_soldiers", "current_loss_budget", "effective_fraction_raw", "minimum_multiplier_raw", "loaded_minimum_soldiers");
    private static final List<String> CONDITION = List.of("actor_character_id", "source_province_id", "target_province_id", "mode", "passes");
    private static final List<String> FLOORS = List.of("base_floor_raw", "army_1d4_nonzero_floor_raw", "army_1d4_raw");
    private static final Set<String> TOP = Set.of("status", "source", "unavailable_reason", "fraction_scale", "soldier_scale", "condition",
            "whole_soldiers", "current_loss_budget", "effective_fraction_raw", "minimum_multiplier_raw", "loaded_minimum_soldiers");
    private CountyEntryCodec() { }

    public static CountyEntryInputs decode(byte[] raw, int currentSoldiers) { return decode(StrictJson.parse(raw), currentSoldiers); }
    public static CountyEntryInputs decode(JsonNode node, int currentSoldiers) {
        object(node); Set<String> fields = fields(node), required = new HashSet<>(TOP);
        if (fields.contains("multiplier_floor_inputs_v1")) required.add("multiplier_floor_inputs_v1");
        StrictJson.require(fields.equals(required), "exact county entry fields required");
        source(node, SOURCE); exact(node, "fraction_scale", FRACTION_SCALE); exact(node, "soldier_scale", 1);
        Budget budget;
        if (available(node, BUDGET)) {
            AvailableBudget observed = new AvailableBudget(i32(node, "whole_soldiers"), i32(node, "current_loss_budget"),
                    i64(node, "effective_fraction_raw"), i64(node, "minimum_multiplier_raw"), i32(node, "loaded_minimum_soldiers"));
            StrictJson.require(observed.wholeSoldiers() == currentSoldiers, "county strength must match same-frame strength"); budget = observed;
        } else budget = new UnavailableBudget(text(node, "unavailable_reason"));
        JsonNode conditionNode = node.get("condition");
        exactObject(conditionNode, CONDITION, Set.of("status", "source", "unavailable_reason")); source(conditionNode, CONDITION_SOURCE);
        Condition condition = available(conditionNode, CONDITION)
                ? new AvailableCondition(i32(conditionNode, "actor_character_id"), i32(conditionNode, "source_province_id"),
                i32(conditionNode, "target_province_id"), i32(conditionNode, "mode"), bool(conditionNode, "passes"))
                : new UnavailableCondition(text(conditionNode, "unavailable_reason"));
        Optional<MultiplierFloors> floors = Optional.empty();
        if (node.has("multiplier_floor_inputs_v1")) {
            JsonNode child = node.get("multiplier_floor_inputs_v1");
            exactObject(child, FLOORS, Set.of("status", "source", "unavailable_reason", "fraction_scale"));
            source(child, FLOORS_SOURCE); exact(child, "fraction_scale", FRACTION_SCALE);
            floors = Optional.of(available(child, FLOORS) ? new AvailableFloors(i64(child, "base_floor_raw"),
                    i64(child, "army_1d4_nonzero_floor_raw"), (int) StrictJson.integer(child.get("army_1d4_raw"), 0, 255))
                    : new UnavailableFloors(text(child, "unavailable_reason")));
        }
        return new CountyEntryInputs(budget, condition, floors);
    }

    public static byte[] encode(CountyEntryInputs value) { return StrictJson.canonical(inputsNode(value)); }
    public static ObjectNode inputsNode(CountyEntryInputs value) {
        ObjectNode node = budgetNode(value.budget()); node.put("source", SOURCE); node.put("fraction_scale", FRACTION_SCALE); node.put("soldier_scale", 1);
        ObjectNode condition = StrictJson.object(); condition.put("source", CONDITION_SOURCE);
        if (value.condition() instanceof AvailableCondition known) {
            status(condition, true, null); condition.put("actor_character_id", known.actorCharacterId()); condition.put("source_province_id", known.sourceProvinceId());
            condition.put("target_province_id", known.targetProvinceId()); condition.put("mode", known.mode()); condition.put("passes", known.passes());
        } else { status(condition, false, ((UnavailableCondition) value.condition()).reason()); CONDITION.forEach(condition::putNull); }
        node.set("condition", condition); value.multiplierFloors().ifPresent(floors -> node.set("multiplier_floor_inputs_v1", floorsNode(floors))); return node;
    }

    public static Strength decodeStrength(JsonNode node) {
        object(node); String status = text(node, "status"); StrictJson.require(Set.of("available", "unavailable").contains(status), "strength status malformed");
        boolean ready = status.equals("available"); int army = (int) StrictJson.integer(node.get("army_id"), 0, Integer.MAX_VALUE);
        Integer current = nullableI32(node.get("current_soldiers")), nativeArmy = nullableI32(node.get("native_carmy_id"));
        CountyEntryInputs inputs = null;
        if (node.has("county_entry_inputs_v1")) {
            StrictJson.require(ready && current != null, "unavailable strength cannot publish county inputs");
            inputs = decode(node.get("county_entry_inputs_v1"), current);
        }
        LossPartition loss = null; JsonNode rawLoss = node.get("loss_application_inputs_v1");
        if (rawLoss != null && !rawLoss.isNull()) {
            object(rawLoss); String lossStatus = text(rawLoss, "status");
            StrictJson.require(Set.of("available", "unavailable").contains(lossStatus), "loss partition status malformed");
            loss = new LossPartition(lossStatus.equals("available"), nullableI32(rawLoss.get("whole_soldiers")), nullableI32(rawLoss.get("definition_le_zero_soldiers")));
        }
        return new Strength(ready, army, nativeArmy, current, inputs, loss);
    }
    public static RouteContext decodeRouteContext(JsonNode node) {
        if (absent(node)) return null; object(node);
        int army = (int) StrictJson.integer(node.get("army_id"), 0, Integer.MAX_VALUE);
        List<Integer> route = null;
        if (!absent(node.get("route_province_ids"))) {
            JsonNode raw = node.get("route_province_ids"); StrictJson.require(raw.isArray(), "route array required"); route = new ArrayList<>();
            for (JsonNode entry : raw) route.add((int) StrictJson.integer(entry, 1, Integer.MAX_VALUE));
        }
        return new RouteContext(army, nullableI32(node.get("current_province_id")), nullableText(node.get("route_read_status")),
                nullableI32(node.get("route_source_count")), route);
    }
    public static MovementPrefix decodeMovementPrefix(JsonNode node) {
        if (absent(node)) return null; object(node);
        return new MovementPrefix(optionalTrue(node.get("movement_prefix_input_ready")), nullableInteger(node.get("subject_army_id_u32"), 0, 0xffff_ffffL),
                nullableInteger(node.get("subject_carmy_id_u32"), 0, 0xffff_ffffL), nullableInteger(node.get("conditional_unit_170_raw_after_next_new_date_entry_prefix"), Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
    public static MovementOperands decodeMovementOperands(JsonNode node) {
        if (absent(node)) return new MovementOperands(null, null, null, null, null); object(node);
        return new MovementOperands(nullableInteger(node.get("current_province_type_tag_u32"), 0, 0xffff_ffffL),
                nullableI32(node.get("unit_kind_18_raw_i32")), nullableInteger(node.get("first_route_target_province_type_tag_u32"), 0, 0xffff_ffffL),
                nullableByte(node.get("first_route_target_province_definition_byte_1b_u8")), nullableByte(node.get("current_province_definition_byte_1b_u8")));
    }
    public static Provenance decodeProvenance(JsonNode node, boolean queryNames) {
        if (absent(node)) return null; object(node); String prefix = queryNames ? "queried_" : "";
        return new Provenance(nullableText(node.get(prefix + "snapshot_id")), nullableInteger(node.get(prefix + "revision"), 0, StrictJson.MAX_SAFE_INTEGER),
                nullableInteger(node.get(prefix + "native_revision"), 0, StrictJson.MAX_SAFE_INTEGER));
    }
    public static QueryFrame decodeQueryFrame(JsonNode node) {
        if (absent(node)) return null; object(node); List<RouteContext> contexts = new ArrayList<>(); JsonNode armies = node.get("player_armies");
        if (!absent(armies)) {
            StrictJson.require(armies.isArray(), "player armies array required");
            for (JsonNode army : armies) if (army.isObject() && army.has("army_id")) contexts.add(decodeRouteContext(army));
        }
        return new QueryFrame(decodeProvenance(node, false), contexts);
    }

    /** Exact small application packet; strength/context/prefix remain extension projections. */
    public static Input decodeProjection(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw), Set.of("strength", "army_context", "movement_prefix", "prestore_call"));
        ObjectNode call = StrictJson.object(node.get("prestore_call"), Set.of("selected", "unavailable_reason"));
        Strength strength = decodeStrength(node.get("strength"));
        return new Input(strength, decodeRouteContext(node.get("army_context")), decodeMovementPrefix(node.get("movement_prefix")),
                decodeMovementOperands(node.get("strength").get("current_movement_progress")),
                new PrestoreCall(nullableBool(call.get("selected")), nullableText(call.get("unavailable_reason"))));
    }
    public static byte[] project(byte[] raw) {
        Input input = decodeProjection(raw);
        return encodeRisk(CountyEntryRisk.project(input.strength(), input.context(), input.prefix(), input.movement(), input.prestore()));
    }
    public static byte[] encodeRisk(Risk risk) { return StrictJson.canonical(riskNode(risk)); }

    public static ObjectNode riskNode(Risk risk) {
        ObjectNode node = StrictJson.object(); node.put("schema_version", 1); node.put("source", "same_query_conditional_county_first_edge_risk_12004");
        node.put("source_contract_game_version", "1.20.0.4"); node.put("status", wire(risk.status()));
        node.put("current_native_budget_ready", risk.budgetReady()); node.put("conditional_budget_selection_ready", risk.edgePositive() != null && risk.contextReady());
        node.put("loaded_multiplier_floor_inputs_ready", risk.floorReady()); node.put("army_id", risk.strength().armyId()); number(node, "native_carmy_id", risk.strength().nativeCarmyId());
        node.put("fresh_route_context_ready", risk.freshContext()); booleanValue(node, "first_route_edge_present", risk.firstEdgePresent());
        node.put("observed_complete_empty_route", risk.observedEmptyRoute()); string(node, "empty_route_evidence", risk.emptyRouteEvidence());
        number(node, "current_province_id", risk.currentProvinceId()); number(node, "first_route_target_province_id", risk.targetProvinceId());
        CountyEntryInputs inputs = risk.strength().countyInputs();
        ObjectNode budget = inputs == null ? StrictJson.object() : budgetNode(inputs.budget());
        if (inputs == null) { budget.putNull("status"); budget.putNull("unavailable_reason"); BUDGET.forEach(budget::putNull); }
        node.set("observed_current_native_budget", budget);
        MultiplierFloors floors = inputs == null ? null : inputs.multiplierFloors().orElse(null);
        if (floors == null) node.putNull("observed_loaded_multiplier_floors"); else node.set("observed_loaded_multiplier_floors", floorsNode(floors));
        booleanValue(node, "conditional_admission", risk.admission()); booleanValue(node, "conditional_positive_county_budget_selected", risk.positiveSelected());
        booleanValue(node, "conditional_edge_admission_if_arrival", risk.edgeAdmission()); booleanValue(node, "conditional_positive_county_budget_if_this_edge_arrives", risk.edgePositive());
        node.put("next_entry_no_arrival_does_not_prove_route_county_budget_zero", risk.noArrivalDoesNotProveZero());
        number(node, "conditional_prior_unit170_at_arrival_descriptor", risk.priorUnit170());
        ArrayNode predicates = node.putArray("predicates");
        for (Predicate entry : risk.predicates()) {
            ObjectNode predicate = predicates.addObject(); predicate.put("name", entry.name());
            if (entry.value() instanceof BooleanValue value) predicate.put("value", value.value());
            else if (entry.value() instanceof IntegerValue value) predicate.put("value", value.value()); else predicate.putNull("value");
            booleanValue(predicate, "passes", entry.passes()); predicate.put("source", entry.source());
        }
        ObjectNode zero = node.putObject("multiplier_zero_predicate"); booleanValue(zero, "passes", risk.zeroPredicate().passes());
        zero.put("basis", risk.zeroPredicate().basis()); zero.put("native_predicate_rva", 0x24DD830); zero.put("formal_army1d4_and_army1d8_types", "unknown");
        ObjectNode multiplier = node.putObject("multiplier_branch_explanation"); booleanValue(multiplier, "base_floor_demanded", risk.multiplier().baseFloorDemanded());
        booleanValue(multiplier, "army_1d4_nonzero_floor_demanded", risk.multiplier().secondFloorDemanded()); number(multiplier, "inferred_ordinary_army_property_1a7_raw", risk.multiplier().ordinaryProperty());
        string(multiplier, "ordinary_property_inference_basis", risk.multiplier().ordinaryProperty() == null ? null : "raw1d4_zero_and_M_strictly_above_loaded_base_floor_inverts_wrap64_100000_plus_A");
        multiplier.putArray("unobserved_other_modifier_values").add("ArmyProperty1A8").add("PC_Army1D8_object_plus280_key1A8");
        Allocation allocation = risk.allocation(); ObjectNode partition = node.putObject("conditional_allocation"); partition.put("ready", allocation.ready());
        number(partition, "preferred_definition_le_zero_soldiers", allocation.preferred()); number(partition, "primary_budget_soldiers", allocation.primary()); number(partition, "residual_budget_soldiers", allocation.residual());
        booleanValue(partition, "conditional_primary_positive_budget", allocation.primarySelected()); booleanValue(partition, "conditional_residual_allocator_selected", allocation.residualSelected());
        partition.put("raw_county_primary_return_rva", 0x24E25EE); partition.put("raw_county_residual_outer_return_rva", 0x24E2630); partition.putNull("actual_physical_debit_soldiers");
        ObjectNode decision = node.putObject("decision"); decision.put("review", wire(risk.decision().review())); decision.put("reason", risk.decision().reason()); decision.putNull("selected_new_target_province_id");
        ArrayNode choices = decision.putArray("readonly_choices");
        if (risk.decision().emptyRoute()) {
            ObjectNode choice = choices.addObject(); choice.put("choice", "obtain_native_legal_route_preview_before_selecting_any_target"); choice.putNull("target_province_id");
            choice.putArray("requires").add("observed_legal_candidate_first_edge").add("actual_candidate_county_condition_and_definition_bytes"); choice.putNull("physical_soldier_saving");
        } else if (risk.decision().showEdgeChoices()) {
            ObjectNode hold = choices.addObject(); hold.put("choice", "keep_paused_for_current_edge_review"); hold.putNull("target_province_id");
            hold.put("source_basis", "no_arrival_callback_without_this_edge_being_taken"); hold.put("effect_boundary", "defers_this_conditional_entry_only_other_war_and_supply_costs_not_evaluated"); hold.putNull("physical_soldier_saving");
            ObjectNode compare = choices.addObject(); compare.put("choice", "compare_an_already_observed_legal_alternative_first_edge"); compare.putNull("target_province_id");
            compare.put("source_basis", "county_admission_depends_on_actual_old_target_definition_bytes_and24e2230");
            compare.put("avoidance_criterion", "observed_candidate_definition1b_zero_or_native24e2230_false_bypasses_the_county_budget_under_held_inputs");
            compare.putArray("requires").add("same_frame_legal_native_route_preview").add("actual_candidate_first_edge_24e2230_condition_and_definition_bytes").add("fresh_budget_after_any_current_army_or_modifier_change"); compare.putNull("physical_soldier_saving");
        }
        ArrayNode requirements = node.putArray("required_observations");
        for (Requirement required : risk.requirements()) { ObjectNode item = requirements.addObject(); item.put("field", required.field()); item.put("reason", required.reason()); item.put("needed_for", required.neededFor()); }
        node.put("held_input_condition", "same_query_army_route_roster_modifiers_post_entry_state_and_county_operands_hold_until_first_arrival_with_normal_prior_returns");
        node.put("actual_arrival_observed", false); node.put("actual_county_loss_observed", false); node.put("army_or_wallet_net_change_used", false); node.put("native_action_executed", false);
        node.putNull("route_overall_safe"); node.putNull("complete_county_or_periodic_loss"); return node;
    }

    private static ObjectNode budgetNode(Budget value) {
        ObjectNode node = StrictJson.object();
        if (value instanceof AvailableBudget known) { status(node, true, null); node.put("whole_soldiers", known.wholeSoldiers()); node.put("current_loss_budget", known.currentLossBudget());
            node.put("effective_fraction_raw", known.effectiveFractionRaw()); node.put("minimum_multiplier_raw", known.minimumMultiplierRaw()); node.put("loaded_minimum_soldiers", known.loadedMinimumSoldiers()); }
        else { status(node, false, ((UnavailableBudget) value).reason()); BUDGET.forEach(node::putNull); } return node;
    }
    private static ObjectNode floorsNode(MultiplierFloors value) {
        ObjectNode node = StrictJson.object(); node.put("source", FLOORS_SOURCE); node.put("fraction_scale", FRACTION_SCALE);
        if (value instanceof AvailableFloors known) { status(node, true, null); node.put("base_floor_raw", known.baseFloorRaw()); node.put("army_1d4_nonzero_floor_raw", known.army1d4NonzeroFloorRaw()); node.put("army_1d4_raw", known.army1d4Raw()); }
        else { status(node, false, ((UnavailableFloors) value).reason()); FLOORS.forEach(node::putNull); } return node;
    }
    private static boolean available(JsonNode node, List<String> observations) {
        String status = text(node, "status"); StrictJson.require(status.equals("available") || status.equals("unavailable"), "native status malformed");
        JsonNode reason = node.get("unavailable_reason");
        if (status.equals("unavailable")) { StrictJson.text(reason); for (String field : observations) StrictJson.require(node.get(field).isNull(), "unavailable native observations must be null"); return false; }
        StrictJson.require(reason != null && reason.isNull(), "available native observation cannot have unavailable reason"); return true;
    }
    private static void exactObject(JsonNode node, List<String> observed, Set<String> other) { Set<String> required = new HashSet<>(other); required.addAll(observed); StrictJson.object(node, required); }
    private static void object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "JSON object required"); }
    private static Set<String> fields(JsonNode node) { Set<String> fields = new HashSet<>(); node.fieldNames().forEachRemaining(fields::add); return fields; }
    private static void source(JsonNode node, String source) { StrictJson.require(source.equals(text(node, "source")), "native source marker differs"); }
    private static void exact(JsonNode node, String key, long expected) { StrictJson.integer(node.get(key), expected, expected); }
    private static int i32(JsonNode node, String key) { return (int) StrictJson.integer(node.get(key), Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static long i64(JsonNode node, String key) { return StrictJson.integer(node.get(key), Long.MIN_VALUE, Long.MAX_VALUE); }
    private static String text(JsonNode node, String key) { return StrictJson.text(node.get(key)); }
    private static boolean bool(JsonNode node, String key) { Boolean value = nullableBool(node.get(key)); StrictJson.require(value != null, "actual native boolean required"); return value; }
    private static boolean absent(JsonNode node) { return node == null || node.isNull(); }
    private static Long nullableInteger(JsonNode node, long min, long max) { return absent(node) ? null : StrictJson.integer(node, min, max); }
    private static Integer nullableI32(JsonNode node) { Long value = nullableInteger(node, Integer.MIN_VALUE, Integer.MAX_VALUE); return value == null ? null : value.intValue(); }
    private static Integer nullableByte(JsonNode node) { Long value = nullableInteger(node, 0, 255); return value == null ? null : value.intValue(); }
    private static String nullableText(JsonNode node) { return absent(node) ? null : StrictJson.text(node); }
    private static Boolean nullableBool(JsonNode node) { if (absent(node)) return null; StrictJson.require(node.isBoolean(), "actual JSON boolean required"); return node.booleanValue(); }
    private static boolean optionalTrue(JsonNode node) { return Boolean.TRUE.equals(nullableBool(node)); }
    private static void status(ObjectNode node, boolean available, String reason) { node.put("status", available ? "available" : "unavailable"); string(node, "unavailable_reason", reason); }
    private static void number(ObjectNode node, String key, Number value) { if (value == null) node.putNull(key); else node.put(key, value.longValue()); }
    private static void booleanValue(ObjectNode node, String key, Boolean value) { if (value == null) node.putNull(key); else node.put(key, value.booleanValue()); }
    private static void string(ObjectNode node, String key, String value) { if (value == null) node.putNull(key); else node.put(key, value); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
}
