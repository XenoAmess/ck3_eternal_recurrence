package org.xar.ck3.control.wave2.military.callbackrisk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact native family boundary, separate from the extension-bearing SDK strength row. */
public final class CurrentSupplyDispatchCodec {
    private static final String SOURCE = "native_current_selected_supply_bucket_subject_occurrences";
    private static final String BOUNDARY = "current_paused_strength";
    private static final Set<String> FALSE_FIELDS = Set.of("actual_callback_observed", "earlier_stage_outputs_reconstructed",
            "full_daily_supply_transition_ready", "full_monthly_ready");
    private static final Set<String> FIELDS = Set.of("source", "status", "ready", "unavailable_reason", "capture_boundary",
            "subject_army_id", "subject_carmy_id", "current_date_raw", "native_day_index", "selected_bucket_phase",
            "selected_bucket_capacity_raw", "selected_bucket_count_raw", "selected_bucket_data_present",
            "subject_dispatch_occurrence_count", "subject_occurrence_indices", "actual_callback_observed",
            "earlier_stage_outputs_reconstructed", "full_daily_supply_transition_ready", "full_monthly_ready");
    private CurrentSupplyDispatchCodec() {}

    public static CurrentSupplyDispatch decode(JsonNode raw, Integer armyId, Integer carmyId) {
        if (raw == null || raw.isNull()) return null;
        ObjectNode node = StrictJson.object(raw, FIELDS);
        StrictJson.require(SOURCE.equals(StrictJson.text(node.get("source"))), "current dispatch source differs");
        StrictJson.require(BOUNDARY.equals(StrictJson.text(node.get("capture_boundary"))), "current dispatch boundary differs");
        for (String field : FALSE_FIELDS) StrictJson.require(Boolean.FALSE.equals(predicate(node, field)), "dispatch cannot claim later callbacks or output");
        CurrentSupplyDispatch.Status status = switch (StrictJson.text(node.get("status"))) {
            case "available" -> CurrentSupplyDispatch.Status.AVAILABLE;
            case "unavailable" -> CurrentSupplyDispatch.Status.UNAVAILABLE;
            default -> throw new IllegalArgumentException("unsupported current dispatch status");
        };
        StrictJson.require(Boolean.valueOf(status == CurrentSupplyDispatch.Status.AVAILABLE).equals(predicate(node, "ready")),
                "current dispatch status differs from readiness");
        Integer subjectArmy = integer(node, "subject_army_id"), subjectCarmy = integer(node, "subject_carmy_id");
        StrictJson.require(armyId == null || subjectArmy == null || armyId.equals(subjectArmy), "current dispatch Army subject differs");
        StrictJson.require(carmyId == null || subjectCarmy == null || carmyId.equals(subjectCarmy), "current dispatch CArmy subject differs");
        return new CurrentSupplyDispatch(status, text(node, "unavailable_reason"), subjectArmy, subjectCarmy,
                integer(node, "current_date_raw"), integer(node, "native_day_index"), integer(node, "selected_bucket_phase"),
                integer(node, "selected_bucket_capacity_raw"), integer(node, "selected_bucket_count_raw"),
                predicate(node, "selected_bucket_data_present"), integer(node, "subject_dispatch_occurrence_count"),
                indices(node.get("subject_occurrence_indices")));
    }
    public static JsonNode encode(CurrentSupplyDispatch value) {
        if (value == null) return NullNode.getInstance();
        ObjectNode node = StrictJson.object();
        node.put("source", SOURCE); node.put("capture_boundary", BOUNDARY);
        node.put("status", value.status().name().toLowerCase(Locale.ROOT)); node.put("ready", value.ready());
        node.put("unavailable_reason", value.unavailableReason());
        node.put("subject_army_id", value.subjectArmyId()); node.put("subject_carmy_id", value.subjectCarmyId());
        node.put("current_date_raw", value.currentDateRaw()); node.put("native_day_index", value.nativeDayIndex());
        node.put("selected_bucket_phase", value.selectedBucketPhase()); node.put("selected_bucket_capacity_raw", value.selectedBucketCapacityRaw());
        node.put("selected_bucket_count_raw", value.selectedBucketCountRaw()); node.put("selected_bucket_data_present", value.selectedBucketDataPresent());
        node.put("subject_dispatch_occurrence_count", value.subjectDispatchOccurrenceCount());
        if (value.subjectOccurrenceIndices() == null) node.putNull("subject_occurrence_indices");
        else { var values = node.putArray("subject_occurrence_indices"); value.subjectOccurrenceIndices().forEach(values::add); }
        FALSE_FIELDS.forEach(field -> node.put(field, false));
        return node;
    }
    private static Integer integer(ObjectNode object, String field) {
        JsonNode value = object.get(field);
        return value.isNull() ? null : (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }
    private static Boolean predicate(ObjectNode object, String field) {
        JsonNode value = object.get(field);
        if (value.isNull()) return null;
        StrictJson.require(value.isBoolean(), field + " must be bool or null"); return value.booleanValue();
    }
    private static String text(ObjectNode object, String field) {
        JsonNode value = object.get(field); return value.isNull() ? null : StrictJson.text(value);
    }
    private static List<Integer> indices(JsonNode value) {
        if (value.isNull()) return null;
        StrictJson.require(value.isArray(), "current dispatch indices must be an array or null");
        List<Integer> result = new ArrayList<>();
        for (JsonNode item : value) result.add((int) StrictJson.integer(item, 0, Integer.MAX_VALUE));
        return List.copyOf(result);
    }
}
