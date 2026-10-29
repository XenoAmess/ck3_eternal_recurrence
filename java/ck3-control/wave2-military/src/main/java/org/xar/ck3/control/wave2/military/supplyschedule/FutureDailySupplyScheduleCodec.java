package org.xar.ck3.control.wave2.military.supplyschedule;

import static org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplySchedule.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict native leaf codec. Extensible enclosing SDK rows are only projected. */
public final class FutureDailySupplyScheduleCodec {
    public static final String FAMILY_KEY = "future_daily_supply_schedule_inputs_v1";
    public static final String SOURCE = "native_future_daily_supply_schedule_inputs_12004";
    public static final int MAX_BYTES = 32_768;
    private static final Set<String> FIELDS = Set.of("schema_version", "source", "stage", "status", "ready",
            "unavailable_reason", "current_date_storage_raw64", "secondary_identity", "phases",
            "current_date_raw_i32", "native_day_index_raw_i32", "selected_phase_index_i32", "subject_army_id_u32",
            "subject_carmy_id_u32", "actual_future_callback_observed", "future_bucket_mutations_reconstructed",
            "full_daily_supply_transition_ready", "full_monthly_ready");
    private static final Set<String> PHASE_FIELDS = Set.of("phase_index_i32", "status", "ready", "unavailable_reason",
            "capacity_raw_i32", "count_raw_i32", "data_pointer_present", "matching_positions", "subject_occurrence_count_i32");
    private static final List<String> FALSE_FIELDS = List.of("actual_future_callback_observed", "future_bucket_mutations_reconstructed",
            "full_daily_supply_transition_ready", "full_monthly_ready");
    private FutureDailySupplyScheduleCodec() { }

    public static FutureDailySupplySchedule decode(byte[] raw) { return decode(StrictJson.parse(raw, MAX_BYTES)); }
    public static FutureDailySupplySchedule decode(JsonNode value) { return decode(value, null, null); }
    public static FutureDailySupplySchedule decode(JsonNode value, Integer expectedArmyId, Integer expectedCarmyId) {
        require(value != null, "missing family is distinct from JSON null");
        if (value.isNull()) return null;
        ObjectNode node = StrictJson.object(value, FIELDS);
        require(StrictJson.integer(node.get("schema_version"), 1, 1) == 1, "unsupported schema");
        literal(node, "source", SOURCE); literal(node, "stage", "observed_current_all_phase_schedule");
        literal(node, "secondary_identity", "game_data_plus_2a548");
        FALSE_FIELDS.forEach(field -> require(node.get(field).isBoolean() && !node.get(field).booleanValue(),
                "current buckets cannot claim future callback/stage execution"));
        Status status = status(node.get("status"));
        readiness(node, status == Status.AVAILABLE);
        Long army = unsigned32(node.get("subject_army_id_u32"));
        Long carmy = unsigned32(node.get("subject_carmy_id_u32"));
        sameSubject(army, expectedArmyId); sameSubject(carmy, expectedCarmyId);
        JsonNode rows = node.get("phases"); require(rows.isArray(), "phase array required");
        List<Phase> phases = new ArrayList<>();
        for (JsonNode row : rows) {
            ObjectNode phase = StrictJson.object(row, PHASE_FIELDS);
            PhaseStatus phaseStatus = switch (StrictJson.text(phase.get("status"))) {
                case "available" -> PhaseStatus.AVAILABLE;
                case "unavailable" -> PhaseStatus.UNAVAILABLE;
                default -> throw new IllegalArgumentException("invalid phase status");
            };
            readiness(phase, phaseStatus == PhaseStatus.AVAILABLE);
            phases.add(new Phase(signed32(phase.get("phase_index_i32")), phaseStatus, reason(phase),
                    nullable32(phase.get("capacity_raw_i32")), nullable32(phase.get("count_raw_i32")),
                    nullableBoolean(phase.get("data_pointer_present")), positions(phase.get("matching_positions")),
                    nullable32(phase.get("subject_occurrence_count_i32"))));
        }
        return new FutureDailySupplySchedule(status, reason(node), army, carmy,
                nullable64(node.get("current_date_storage_raw64")), nullable32(node.get("current_date_raw_i32")),
                nullable32(node.get("native_day_index_raw_i32")), nullable32(node.get("selected_phase_index_i32")), phases);
    }

    /** Missing/null/present is retained while unrelated enclosing SDK extension fields remain accepted. */
    public sealed interface FamilyField permits Missing, ExplicitNull, Present { }
    public record Missing() implements FamilyField { }
    public record ExplicitNull() implements FamilyField { }
    public record Present(FutureDailySupplySchedule schedule) implements FamilyField {
        public Present { java.util.Objects.requireNonNull(schedule); }
    }
    public static FamilyField fromSameQueryRow(JsonNode row, Integer expectedArmyId, Integer expectedCarmyId) {
        require(row != null && row.isObject(), "same-query row object required");
        if (!row.has(FAMILY_KEY)) return new Missing();
        FutureDailySupplySchedule schedule = decode(row.get(FAMILY_KEY), expectedArmyId, expectedCarmyId);
        return schedule == null ? new ExplicitNull() : new Present(schedule);
    }

    public static JsonNode encode(FutureDailySupplySchedule value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = StrictJson.object();
        node.put("schema_version", 1); node.put("source", SOURCE); node.put("stage", "observed_current_all_phase_schedule");
        node.put("status", wire(value.status())); node.put("ready", value.ready()); nullable(node, "unavailable_reason", value.unavailableReason());
        nullable(node, "subject_army_id_u32", value.subjectArmyIdU32()); nullable(node, "subject_carmy_id_u32", value.subjectCarmyIdU32());
        nullable(node, "current_date_storage_raw64", value.currentDateStorageRaw64()); nullable(node, "current_date_raw_i32", value.currentDateRawI32());
        nullable(node, "native_day_index_raw_i32", value.nativeDayIndexRawI32()); nullable(node, "selected_phase_index_i32", value.selectedPhaseIndexI32());
        node.put("secondary_identity", "game_data_plus_2a548");
        ArrayNode rows = node.putArray("phases");
        for (Phase phase : value.phases()) {
            ObjectNode row = rows.addObject(); row.put("phase_index_i32", phase.phaseIndexI32());
            row.put("status", phase.ready() ? "available" : "unavailable"); row.put("ready", phase.ready());
            nullable(row, "unavailable_reason", phase.unavailableReason()); nullable(row, "capacity_raw_i32", phase.capacityRawI32());
            nullable(row, "count_raw_i32", phase.countRawI32());
            if (phase.dataPointerPresent() == null) row.putNull("data_pointer_present"); else row.put("data_pointer_present", phase.dataPointerPresent());
            if (phase.matchingPositions() == null) row.putNull("matching_positions");
            else { ArrayNode positions = row.putArray("matching_positions"); phase.matchingPositions().forEach(positions::add); }
            nullable(row, "subject_occurrence_count_i32", phase.subjectOccurrenceCountI32());
        }
        FALSE_FIELDS.forEach(field -> node.put(field, false));
        return node;
    }
    public static byte[] encodeBytes(FutureDailySupplySchedule value) { return StrictJson.canonical(encode(value), MAX_BYTES); }
    private static Status status(JsonNode node) {
        return switch (StrictJson.text(node)) {
            case "available" -> Status.AVAILABLE; case "partial" -> Status.PARTIAL; case "unavailable" -> Status.UNAVAILABLE;
            default -> throw new IllegalArgumentException("invalid schedule status");
        };
    }
    private static String wire(Status status) { return switch (status) { case AVAILABLE -> "available"; case PARTIAL -> "partial"; case UNAVAILABLE -> "unavailable"; }; }
    private static void literal(ObjectNode node, String field, String expected) { require(expected.equals(StrictJson.text(node.get(field))), field + " source differs"); }
    private static void readiness(ObjectNode node, boolean expected) { require(node.get("ready").isBoolean() && node.get("ready").booleanValue() == expected, "readiness differs from status"); }
    private static String reason(ObjectNode node) { return node.get("unavailable_reason").isNull() ? null : StrictJson.text(node.get("unavailable_reason")); }
    private static int signed32(JsonNode node) { return (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static Integer nullable32(JsonNode node) { return node.isNull() ? null : signed32(node); }
    private static Long nullable64(JsonNode node) { return node.isNull() ? null : StrictJson.integer(node, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static Long unsigned32(JsonNode node) { return node.isNull() ? null : StrictJson.integer(node, 0, 0xFFFF_FFFFL); }
    private static Boolean nullableBoolean(JsonNode node) { if (node.isNull()) return null; require(node.isBoolean(), "bool or null required"); return node.booleanValue(); }
    private static List<Integer> positions(JsonNode node) {
        if (node.isNull()) return null;
        require(node.isArray(), "positions must be array or null"); List<Integer> result = new ArrayList<>();
        for (JsonNode position : node) result.add((int) StrictJson.integer(position, 0, Integer.MAX_VALUE));
        return result;
    }
    private static void sameSubject(Long observed, Integer expected) { require(observed == null || expected == null || observed == Integer.toUnsignedLong(expected), "subject differs from same-query row"); }
    private static void nullable(ObjectNode node, String key, Number value) { if (value == null) node.putNull(key); else node.put(key, value.longValue()); }
    private static void nullable(ObjectNode node, String key, String value) { if (value == null) node.putNull(key); else node.put(key, value); }
}
