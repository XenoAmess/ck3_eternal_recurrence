package org.xar.ck3.control.wave2.military.prestore;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.Field;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.FixedPoint;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.Presence;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.Status;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.Timeline;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.TimelineStatus;

/** Authoritative Java migration of _normalize_current_movement_progress and its committed-route dependency. */
public final class CurrentMovementCodec {
    private static final Set<String> REQUIRED = Set.of("status", "source", "unit_state_raw", "accumulated_movement_weight_raw",
            "cached_edge_speed_raw", "normalized_edge_progress", "first_route_edge_remaining_duration", "unavailable_reason");
    private static final Set<String> OPTIONAL = Set.of("committed_route_timeline", "current_edge_movement_rate_raw", "native_army_movement_admission",
            "first_route_edge_weight_cost_raw", "first_edge_arrival_provider_byte_e_u8", "first_route_target_province_type_tag_u32",
            "current_province_type_tag_u32", "unit_kind_18_raw_i32", "current_province_definition_byte_1b_u8",
            "first_route_target_province_definition_byte_1b_u8", "loaded_disembark_penalty_days_rule_i32", "loaded_movement_lock_cutoff");
    private CurrentMovementCodec() { }

    public static Optional<CurrentMovement> normalize(byte[] raw) { return normalize(StrictJson.parse(raw)); }
    public static Optional<CurrentMovement> normalize(JsonNode node) {
        if (node == null || node.isNull()) { return Optional.empty(); }
        StrictJson.require(node.isObject(), "current movement must be an object or null");
        Set<String> keys = new HashSet<>(); node.fieldNames().forEachRemaining(keys::add);
        Set<String> allowed = new HashSet<>(REQUIRED); allowed.addAll(OPTIONAL);
        StrictJson.require(keys.containsAll(REQUIRED) && allowed.containsAll(keys), "current movement exact required/optional fields");
        StrictJson.require(text(node.get("source")).equals("native_current_route_edge"), "movement source drift");
        Status status = parseStatus(node.get("status"));
        return Optional.of(new CurrentMovement(status, nullableI32(node.get("unit_state_raw")), nullableI64(node.get("accumulated_movement_weight_raw")),
                nullableI64(node.get("cached_edge_speed_raw")), nullableFixed(node.get("normalized_edge_progress")),
                nullableFixed(node.get("first_route_edge_remaining_duration")), nullableText(node.get("unavailable_reason")),
                field(node, "current_edge_movement_rate_raw", CurrentMovementCodec::i64),
                field(node, "native_army_movement_admission", CurrentMovementCodec::bool),
                field(node, "first_route_edge_weight_cost_raw", CurrentMovementCodec::i64),
                field(node, "first_edge_arrival_provider_byte_e_u8", value -> (int) StrictJson.integer(value, 0, 255)),
                field(node, "first_route_target_province_type_tag_u32", value -> StrictJson.integer(value, 0, 0xffff_ffffL)),
                field(node, "current_province_type_tag_u32", value -> StrictJson.integer(value, 0, 0xffff_ffffL)),
                field(node, "unit_kind_18_raw_i32", CurrentMovementCodec::i32),
                field(node, "current_province_definition_byte_1b_u8", value -> (int) StrictJson.integer(value, 0, 255)),
                field(node, "first_route_target_province_definition_byte_1b_u8", value -> (int) StrictJson.integer(value, 0, 255)),
                field(node, "loaded_disembark_penalty_days_rule_i32", CurrentMovementCodec::i32),
                field(node, "loaded_movement_lock_cutoff", CurrentMovementCodec::fixed),
                // Explicit null committed_route_timeline is not accepted by the original nested normalizer.
                node.has("committed_route_timeline") ? Field.of(timeline(node.get("committed_route_timeline"))) : Field.missing()));
    }

    public static byte[] encode(Optional<CurrentMovement> movement) {
        return StrictJson.canonical(movement.<JsonNode>map(CurrentMovementCodec::node).orElse(NullNode.getInstance()));
    }
    public static ObjectNode node(CurrentMovement value) {
        ObjectNode node = StrictJson.object(); node.put("status", value.status().name().toLowerCase(Locale.ROOT)); node.put("source", "native_current_route_edge");
        number(node, "unit_state_raw", value.unitState()); number(node, "accumulated_movement_weight_raw", value.accumulatedWeight());
        number(node, "cached_edge_speed_raw", value.cachedEdgeSpeed()); node.set("normalized_edge_progress", fixedNode(value.normalizedProgress()));
        node.set("first_route_edge_remaining_duration", fixedNode(value.remainingDuration())); string(node, "unavailable_reason", value.unavailableReason());
        write(node, "current_edge_movement_rate_raw", value.currentEdgeRate(), CurrentMovementCodec::numberNode);
        write(node, "native_army_movement_admission", value.nativeArmyAdmission(), com.fasterxml.jackson.databind.node.BooleanNode::valueOf);
        write(node, "first_route_edge_weight_cost_raw", value.firstEdgeCost(), CurrentMovementCodec::numberNode);
        write(node, "first_edge_arrival_provider_byte_e_u8", value.arrivalProviderByte(), CurrentMovementCodec::numberNode);
        write(node, "first_route_target_province_type_tag_u32", value.targetProvinceType(), CurrentMovementCodec::numberNode);
        write(node, "current_province_type_tag_u32", value.currentProvinceType(), CurrentMovementCodec::numberNode);
        write(node, "unit_kind_18_raw_i32", value.unitKind(), CurrentMovementCodec::numberNode);
        write(node, "current_province_definition_byte_1b_u8", value.currentDefinitionByte(), CurrentMovementCodec::numberNode);
        write(node, "first_route_target_province_definition_byte_1b_u8", value.targetDefinitionByte(), CurrentMovementCodec::numberNode);
        write(node, "loaded_disembark_penalty_days_rule_i32", value.loadedDisembarkDays(), CurrentMovementCodec::numberNode);
        write(node, "loaded_movement_lock_cutoff", value.loadedLockCutoff(), CurrentMovementCodec::fixedNode);
        write(node, "committed_route_timeline", value.timeline(), CurrentMovementCodec::timelineNode); return node;
    }

    private static Timeline timeline(JsonNode node) {
        StrictJson.object(node, Set.of("status", "source", "native_duration_scale", "unavailable_reason", "native_full_route_remaining_days_q100000",
                "committed_route_province_ids", "native_route_prefix_remaining_days_q100000", "projected_route_arrival_date_raws"));
        StrictJson.require(text(node.get("source")).equals("native_committed_route"), "committed route source drift"); scale(node.get("native_duration_scale"));
        TimelineStatus status;
        try {
            String wire = text(node.get("status")); status = TimelineStatus.valueOf(wire.toUpperCase(Locale.ROOT));
            StrictJson.require(wire.equals(status.name().toLowerCase(Locale.ROOT)), "exact timeline status spelling");
        }
        catch (IllegalArgumentException error) { throw new IllegalArgumentException("committed route status malformed", error); }
        return new Timeline(status, nullableText(node.get("unavailable_reason")), nullableI64(node.get("native_full_route_remaining_days_q100000")),
                list(node.get("committed_route_province_ids"), value -> (int) StrictJson.integer(value, 1, Integer.MAX_VALUE)),
                list(node.get("native_route_prefix_remaining_days_q100000"), CurrentMovementCodec::i64),
                list(node.get("projected_route_arrival_date_raws"), CurrentMovementCodec::i32));
    }
    private static ObjectNode timelineNode(Timeline value) {
        ObjectNode node = StrictJson.object(); node.put("status", value.status().name().toLowerCase(Locale.ROOT)); node.put("source", "native_committed_route");
        node.put("native_duration_scale", FixedPoint.SCALE); string(node, "unavailable_reason", value.unavailableReason());
        number(node, "native_full_route_remaining_days_q100000", value.fullDuration());
        numbers(node, "committed_route_province_ids", value.provinces()); numbers(node, "native_route_prefix_remaining_days_q100000", value.prefixDurations());
        numbers(node, "projected_route_arrival_date_raws", value.arrivalDates()); return node;
    }

    public static JsonNode fixedNode(FixedPoint value) {
        if (value == null) { return NullNode.getInstance(); }
        ObjectNode node = StrictJson.object(); node.put("raw", value.raw()); node.put("scale", FixedPoint.SCALE); return node;
    }
    private static FixedPoint fixed(JsonNode value) {
        StrictJson.object(value, Set.of("raw", "scale")); scale(value.get("scale")); return new FixedPoint(i64(value.get("raw")));
    }
    private static FixedPoint nullableFixed(JsonNode value) { return value.isNull() ? null : fixed(value); }
    private static void scale(JsonNode value) { StrictJson.require(StrictJson.integer(value, 100_000, 100_000) == 100_000, "exact Q100000 scale"); }
    private static Status parseStatus(JsonNode value) {
        try {
            String wire = text(value); Status status = Status.valueOf(wire.toUpperCase(Locale.ROOT));
            StrictJson.require(wire.equals(status.name().toLowerCase(Locale.ROOT)), "exact movement status spelling"); return status;
        }
        catch (IllegalArgumentException error) { throw new IllegalArgumentException("movement status malformed", error); }
    }
    private static String text(JsonNode value) { return StrictJson.text(value); }
    private static String nullableText(JsonNode value) { return value == null || value.isNull() ? null : text(value); }
    private static int i32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static long i64(JsonNode value) { return StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static Integer nullableI32(JsonNode value) { return value == null || value.isNull() ? null : i32(value); }
    private static Long nullableI64(JsonNode value) { return value == null || value.isNull() ? null : i64(value); }
    private static boolean bool(JsonNode value) { StrictJson.require(value.isBoolean(), "exact boolean required"); return value.booleanValue(); }
    private static <T> Field<T> field(JsonNode node, String key, Function<JsonNode, T> parse) {
        if (!node.has(key)) { return Field.missing(); }
        return node.get(key).isNull() ? Field.nullValue() : Field.of(parse.apply(node.get(key)));
    }
    private static <T> void write(ObjectNode node, String key, Field<T> field, Function<T, JsonNode> encode) {
        if (field.presence() != Presence.MISSING) { node.set(key, field.presence() == Presence.NULL ? NullNode.getInstance() : encode.apply(field.value())); }
    }
    private static <T> List<T> list(JsonNode node, Function<JsonNode, T> parse) {
        if (node.isNull()) { return null; }
        StrictJson.require(node.isArray(), "committed route array or null required"); List<T> values = new ArrayList<>();
        for (JsonNode value : node) { values.add(parse.apply(value)); } return values;
    }
    private static JsonNode numberNode(Number value) { return com.fasterxml.jackson.databind.node.LongNode.valueOf(value.longValue()); }
    private static void number(ObjectNode node, String key, Number value) { node.set(key, value == null ? NullNode.getInstance() : numberNode(value)); }
    private static void string(ObjectNode node, String key, String value) { if (value == null) { node.putNull(key); } else { node.put(key, value); } }
    private static void numbers(ObjectNode node, String key, List<? extends Number> values) {
        if (values == null) { node.putNull(key); return; } ArrayNode array = node.putArray(key); values.forEach(value -> array.add(value.longValue()));
    }
}
