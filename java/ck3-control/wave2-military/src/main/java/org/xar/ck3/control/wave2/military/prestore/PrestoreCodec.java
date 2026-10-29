package org.xar.ck3.control.wave2.military.prestore;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRisk;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.Provenance;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.QueryFrame;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.RouteContext;
import org.xar.ck3.control.wave2.military.disembark.DisembarkCodec;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.FixedPoint;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark.Arrival;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark.Input;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark.Operand;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark.Result;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark.Selection;

/** Complete prestore consumer; county risk and observed-day normalization are reused typed dependencies. */
public final class PrestoreCodec {
    private static final List<String> FALSE_FIELDS = List.of("prior170_or_descriptor1_demanded_by_fixed_write", "native_fleet_validity_demanded_by_fixed_write",
            "current_remaining_days_readiness_demanded_by_fixed_write", "actual_future_frame_observed", "actual_prestore_callback_executed",
            "actual_fixed_disembark_write_observed", "final_disembark_penalty_reconstructed", "final_arrival_reconstructed",
            "final_helper_current_province_reconstructed", "unit30_or_unit160_reconstructed", "recursive_other_unit_arrival_reconstructed",
            "full_unit_new_date_callback_ready", "repeated_callback_effects_reconstructed", "battle_contact_supply_day_effects_reconstructed", "native_action_executed");
    private PrestoreCodec() { }

    /** Narrow application packet; nested SDK rows/predecessor projections are declared field projections. */
    public static Input decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), Set.of("strength", "arrival_transition", "army_context", "movement_prefix"));
        return decode(root.get("strength"), root.get("arrival_transition"), CountyEntryCodec.decodeRouteContext(root.get("army_context")), root.get("movement_prefix"));
    }
    public static Input decode(JsonNode strength, JsonNode arrival, RouteContext context, JsonNode prefix) {
        StrictJson.require(strength != null && strength.isObject(), "same query strength object required");
        JsonNode rawDays = strength.get(DisembarkPenalty.LEAF);
        Optional<DisembarkPenalty.Observation> observed = rawDays == null || rawDays.isNull() ? Optional.empty() : Optional.of(DisembarkCodec.normalize(evidence(rawDays)));
        return new Input(CountyEntryCodec.decodeStrength(strength), arrival(arrival), CurrentMovementCodec.normalize(strength.get("current_movement_progress")),
                context, CountyEntryCodec.decodeMovementPrefix(prefix), observed);
    }

    /** Reuse the existing three-field same-query join; drift removes context rather than inventing a future route. */
    public static Input decodeSameQuery(JsonNode strength, JsonNode arrival, JsonNode prefix, Provenance query, QueryFrame snapshot) {
        int armyId = (int) StrictJson.integer(strength.get("army_id"), 0, Integer.MAX_VALUE);
        return decode(strength, arrival, CountyEntryRisk.joinContext(query, snapshot, armyId), prefix);
    }
    public static byte[] project(byte[] raw) { return encode(PrestoreDisembark.project(decode(raw))); }
    public static byte[] encode(Result result) { return StrictJson.canonical(node(result)); }
    public static ObjectNode serviceRow(Result result, Provenance provenance) {
        ObjectNode node = StrictJson.object(); node.put("army_id", result.input().strength().armyId());
        ObjectNode source = node.putObject("source_provenance");
        string(source, "snapshot_id", provenance.snapshotId()); number(source, "revision", provenance.revision());
        number(source, "native_revision", provenance.nativeRevision()); node.set("projection", node(result)); return node;
    }
    public static ObjectNode node(Result result) {
        Input input = result.input(); Selection selection = result.selection(); Arrival arrival = input.arrival();
        CurrentMovement movement = input.movement().orElse(null); RouteContext context = input.context();
        ObjectNode node = StrictJson.object(); node.put("schema_version", 1); node.put("source", "source_conditional_unit_arrival_prestore_disembark_write_12004");
        node.put("projection_boundary", "first_selected_arrival_prestore_local_army1d0_fixed_write_24e2822");
        node.put("condition", "same_query_source31_receiver_original_route_current_and_target_province_definition_operands_held_with_normal_prior_call_returns");
        node.put("fixed_disembark_write_input_ready", selection.ready()); string(node, "unavailable_reason", selection.unavailableReason());
        number(node, "subject_army_id_u32", arrival.subjectArmyId()); number(node, "subject_carmy_id_u32", arrival.subjectCarmyId());
        numbers(node, "subject_stored_id_positions", arrival.storedIdPositions()); bool(node, "source31_first_province_assignment_selected_existing", arrival.firstProvinceAssignmentSelected());
        number(node, "current_province_id_existing", context == null ? null : context.currentProvinceId());
        numbers(node, "current_route_province_ids_existing", context == null ? null : context.routeProvinceIds());
        number(node, "current_province_type_tag_u32", movement == null ? null : movement.currentProvinceType().value());
        number(node, "unit_kind_18_raw_i32", movement == null ? null : movement.unitKind().value());
        number(node, "current_province_definition_byte_1b_u8", movement == null ? null : movement.currentDefinitionByte().value());
        number(node, "first_route_target_province_definition_byte_1b_u8", movement == null ? null : movement.targetDefinitionByte().value());
        number(node, "loaded_disembark_penalty_days_rule_i32", movement == null ? null : movement.loadedDisembarkDays().value());
        ObjectNode demands = node.putObject("raw_input_demanded_by_conditional_fixed_write");
        demands.put("current_province_type_tag_u32", selection.demanded().contains(Operand.CURRENT_PROVINCE_TYPE));
        demands.put("unit_kind_18_raw_i32", selection.demanded().contains(Operand.UNIT_KIND));
        demands.put("current_province_definition_byte_1b_u8", selection.demanded().contains(Operand.CURRENT_DEFINITION_BYTE));
        demands.put("first_route_target_province_definition_byte_1b_u8", selection.demanded().contains(Operand.TARGET_DEFINITION_BYTE));
        demands.put("loaded_disembark_penalty_days_rule_i32", selection.demanded().contains(Operand.LOADED_DAYS_RULE));
        bool(node, "conditional_prestore_24e23e0_call_selected", selection.callSelected());
        bool(node, "conditional_fixed_disembark_days_write_selected", selection.writeSelected());
        number(node, "conditional_disembark_days_fixed_write_value_i32", selection.writeValue());
        node.put("loaded_days_rule_demanded_by_conditional_fixed_write", selection.demanded().contains(Operand.LOADED_DAYS_RULE));
        if (input.observedCurrentDays().isPresent()) { node.set("observed_current_disembark_penalty_existing", StrictJson.parse(DisembarkCodec.encodeObservation(input.observedCurrentDays().orElseThrow()))); }
        else { node.putNull("observed_current_disembark_penalty_existing"); }
        node.put("descriptor_byte2_caller_constant", 0);
        FixedPoint remaining = movement == null ? null : movement.remainingDuration();
        node.set("current_remaining_duration_days_existing", CurrentMovementCodec.fixedNode(remaining));
        FALSE_FIELDS.forEach(key -> node.put(key, false)); node.set("county_entry_risk_v1", CountyEntryCodec.riskNode(result.countyRisk())); return node;
    }

    private static Arrival arrival(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "arrival transition projection required");
        JsonNode ready = node.get("arrival_transition_input_ready"); StrictJson.require(ready != null && ready.isBoolean(), "exact arrival input readiness boolean required");
        JsonNode helper = node.get("conditional_first_province_assignment_selected");
        StrictJson.require(helper != null && (helper.isNull() || helper.isBoolean()), "explicit bool/null helper selection required");
        return new Arrival(ready.booleanValue(), helper.isNull() ? null : helper.booleanValue(), nullableText(node.get("unavailable_reason")),
                nullableU32(node.get("subject_army_id_u32")), nullableU32(node.get("subject_carmy_id_u32")), positions(node.get("subject_stored_id_positions")));
    }

    /** Preserve numeric token kind when adapting a Jackson boundary to the shared observation normalizer. */
    private static EvidenceJson.Value evidence(JsonNode node) {
        if (node.isNull()) { return EvidenceJson.NullValue.INSTANCE; }
        if (node.isTextual()) { return EvidenceJson.text(node.textValue()); }
        if (node.isBoolean()) { return new EvidenceJson.BooleanValue(node.booleanValue()); }
        if (node.isIntegralNumber()) { return new EvidenceJson.IntegerValue(node.bigIntegerValue()); }
        if (node.isFloatingPointNumber()) {
            String token = node.decimalValue().toString();
            if (token.indexOf('.') < 0 && token.indexOf('e') < 0 && token.indexOf('E') < 0) { token += ".0"; }
            return new EvidenceJson.DecimalValue(token);
        }
        if (node.isArray()) {
            List<EvidenceJson.Value> values = new ArrayList<>(); node.forEach(value -> values.add(evidence(value))); return new EvidenceJson.ArrayValue(values);
        }
        StrictJson.require(node.isObject(), "JSON evidence value required"); List<EvidenceJson.Member> values = new ArrayList<>();
        node.properties().forEach(entry -> values.add(EvidenceJson.member(entry.getKey(), evidence(entry.getValue()))));
        return new EvidenceJson.ObjectValue(values);
    }
    private static String nullableText(JsonNode value) { return value == null || value.isNull() ? null : StrictJson.text(value); }
    private static Long nullableU32(JsonNode value) { return value == null || value.isNull() ? null : StrictJson.integer(value, 0, 0xffff_ffffL); }
    private static List<Integer> positions(JsonNode node) {
        if (node == null || node.isNull()) { return null; }
        StrictJson.require(node.isArray(), "stored ID positions array required"); List<Integer> values = new ArrayList<>();
        node.forEach(value -> values.add((int) StrictJson.integer(value, 0, Integer.MAX_VALUE))); return values;
    }
    private static void number(ObjectNode node, String key, Number value) { if (value == null) { node.putNull(key); } else { node.put(key, value.longValue()); } }
    private static void string(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void bool(ObjectNode node, String key, Boolean value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void numbers(ObjectNode node, String key, List<? extends Number> values) {
        if (values == null) { node.putNull(key); return; } ArrayNode array = node.putArray(key); values.forEach(value -> array.add(value.longValue()));
    }
}
