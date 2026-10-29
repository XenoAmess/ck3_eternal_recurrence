package org.xar.ck3.control.wave2.military.supplyschedule;

import static org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleProjection.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Declared projection at the legacy schedule producer boundary. */
public final class FutureDailySupplyScheduleProjectionCodec {
    private FutureDailySupplyScheduleProjectionCodec() { }
    public static FutureDailySupplySchedule decodeRowOrFamily(JsonNode rowOrFamily) {
        StrictJson.require(rowOrFamily != null && rowOrFamily.isObject(), "schedule row or family object required");
        JsonNode source = rowOrFamily.get("source");
        if (source != null && source.isTextual() && source.textValue().equals(FutureDailySupplyScheduleCodec.SOURCE)) {
            return FutureDailySupplyScheduleCodec.decode(rowOrFamily);
        }
        JsonNode family = rowOrFamily.get(FutureDailySupplyScheduleCodec.FAMILY_KEY);
        return family == null ? null : FutureDailySupplyScheduleCodec.decode(family);
    }
    public static List<NativeFrame> decodeFrames(JsonNode node) {
        StrictJson.require(node != null && node.isArray(), "separately supplied native frame array required");
        List<NativeFrame> frames = new ArrayList<>();
        for (JsonNode value : node) {
            ObjectNode frame = StrictJson.object(value, Set.of("date_raw_i32", "native_day_index_raw_i32"));
            frames.add(new NativeFrame((int) StrictJson.integer(frame.get("date_raw_i32"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                    (int) StrictJson.integer(frame.get("native_day_index_raw_i32"), Integer.MIN_VALUE, Integer.MAX_VALUE)));
        }
        return List.copyOf(frames);
    }
    public static JsonNode encode(Projection projection) {
        if (projection == null) return NullNode.getInstance();
        FutureDailySupplySchedule schedule = projection.observedSchedule();
        ObjectNode node = StrictJson.object();
        node.put("schema_version", 1); node.put("source", "same_input_conditional_future_daily_supply_schedule_v1");
        node.put("ready", schedule.ready());
        node.put("status", switch (schedule.status()) { case AVAILABLE -> "available"; case PARTIAL -> "partial"; case UNAVAILABLE -> "unavailable"; });
        nullable(node, "unavailable_reason", schedule.unavailableReason());
        nullable(node, "subject_army_id_u32", schedule.subjectArmyIdU32()); nullable(node, "subject_carmy_id_u32", schedule.subjectCarmyIdU32());
        nullable(node, "current_date_storage_raw64", schedule.currentDateStorageRaw64());
        nullable(node, "native_day_index_raw_i32", schedule.nativeDayIndexRawI32());
        nullable(node, "selected_phase_index_i32", schedule.selectedPhaseIndexI32());
        ArrayNode matching = node.putArray("observed_matching_phases");
        for (MatchingPhase phase : projection.observedMatchingPhases()) {
            ObjectNode row = matching.addObject(); row.put("phase_index_i32", phase.phaseIndexI32());
            positions(row, phase.matchingPositions()); row.put("subject_occurrence_count_i32", phase.subjectOccurrenceCountI32());
        }
        ArrayNode unavailable = node.putArray("unavailable_phases"); projection.unavailablePhases().forEach(unavailable::add);
        ArrayNode frames = node.putArray("prospective_frames");
        for (SelectedFrame frame : projection.prospectiveFrames()) {
            ObjectNode row = frames.addObject(); row.put("prospective_index", frame.prospectiveIndex()); row.put("date_raw_i32", frame.dateRawI32());
            row.put("native_day_index_raw_i32", frame.nativeDayIndexRawI32()); row.put("selected_phase_index_i32", frame.selectedPhaseIndexI32());
            row.put("conditional_bucket_occurrences_ready", frame.conditionalBucketOccurrencesReady()); positions(row, frame.matchingPositions());
            nullable(row, "subject_occurrence_count_i32", frame.subjectOccurrenceCountI32()); nullable(row, "unavailable_reason", frame.unavailableReason());
            row.put("actual_callback_observed", false);
        }
        node.put("condition", CONDITION); node.put("calendar_derived", false); node.put("actual_future_callback_observed", false);
        node.put("future_bucket_mutations_reconstructed", false); node.put("future_supply_eligibility_ready", false);
        node.put("future_stock_or_strength_ready", false); node.put("full_daily_supply_transition_ready", false); node.put("full_monthly_ready", false);
        return node;
    }
    private static void positions(ObjectNode node, List<Integer> values) {
        if (values == null) node.putNull("matching_positions");
        else { ArrayNode array = node.putArray("matching_positions"); values.forEach(array::add); }
    }
    private static void nullable(ObjectNode node, String key, Number value) { if (value == null) node.putNull(key); else node.put(key, value.longValue()); }
    private static void nullable(ObjectNode node, String key, String value) { if (value == null) node.putNull(key); else node.put(key, value); }
}
