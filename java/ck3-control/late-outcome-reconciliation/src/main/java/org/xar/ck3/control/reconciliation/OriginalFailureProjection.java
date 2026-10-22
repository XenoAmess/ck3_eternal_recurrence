package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Assessment;
import org.xar.ck3.control.reconciliation.LateOutcome.Outcome;
import org.xar.ck3.control.reconciliation.LateOutcome.Reason;

/** A precise incomplete projection of an actual failed producer response, never a new STATUS reply. */
public record OriginalFailureProjection(String sourceSha256, long autoSequence, int startingDateRaw,
                                        int targetDateRaw, int speed, LateOutcome.Status historicalArm,
                                        boolean normalStatusQueryAttempted, boolean stopValidationAttempted) {
    private static final Set<String> ENVELOPE = Set.of("projection_schema", "projection_notice", "source_sha256",
            "source_json_pointer", "auto_sequence", "payload");
    private static final Set<String> PAYLOAD = Set.of("schema", "credit", "never_replay", "starting_date_raw", "target_date_raw", "requested_speed",
            "armed_reply", "normal_status_query_attempted", "stop_validation_attempted", "stopped_status", "stop_credit");
    public OriginalFailureProjection {
        LateOutcome.digest(sourceSha256); StrictJson.safe(autoSequence, 1);
        StrictJson.require(startingDateRaw >= 0 && targetDateRaw > startingDateRaw, "original date interval");
        StrictJson.require(speed >= 1 && speed <= 5, "original speed");
        java.util.Objects.requireNonNull(historicalArm);
        StrictJson.require(historicalArm.state() == LateOutcome.State.ARMED
                && historicalArm.startingDateRaw() == startingDateRaw && historicalArm.targetDateRaw() == targetDateRaw
                && historicalArm.speed() == speed, "original armed projection matches request");
        StrictJson.require(!normalStatusQueryAttempted && !stopValidationAttempted, "this version projects the before-status failure path");
    }
    public static OriginalFailureProjection decode(byte[] raw, String expectedSourceSha256) {
        LateOutcome.digest(expectedSourceSha256);
        ObjectNode root = StrictJson.object(StrictJson.parse(raw), ENVELOPE);
        StrictJson.require("xar.clock-original-failure-projection/v1".equals(StrictJson.text(root.get("projection_schema"))), "projection schema");
        StrictJson.require("selected_original_fields_not_original_bytes_incomplete".equals(StrictJson.text(root.get("projection_notice"))), "explicit projection notice");
        String source = StrictJson.text(root.get("source_sha256"));
        StrictJson.require(source.equals(expectedSourceSha256), "external original source digest pin mismatch");
        StrictJson.require("/result/structured_content/diagnostics/exact_day_clock_failure_v1".equals(StrictJson.text(root.get("source_json_pointer"))), "original producer pointer");
        JsonNode payload = StrictJson.object(root.get("payload"), PAYLOAD);
        StrictJson.require("xar.exact-day-clock-failure.v2".equals(StrictJson.text(payload.get("schema"))), "original failure schema");
        StrictJson.integer(payload.get("credit"), 0, 0); StrictJson.trueValue(payload.get("never_replay"));
        StrictJson.require(payload.get("stopped_status").isNull() && !SentinelCodec.bool(payload.get("stop_credit")), "no original stopped status/credit");
        Set<String> originalArmFields = new HashSet<>(SentinelCodec.FIELDS); originalArmFields.remove("trigger_reasons");
        ObjectNode originalArm = StrictJson.object(payload.get("armed_reply"), originalArmFields);
        StrictJson.require(StrictJson.integer(originalArm.get("trigger_flags"), 0, 0) == 0, "historical armed reply has no trigger");
        // Internal parsing derives an empty reasons list from flags=0. The preserved fixture stays 19 fields;
        // neither its bytes nor its meaning are presented as a fresh 20-field STATUS.
        ObjectNode view = originalArm.deepCopy(); view.putArray("trigger_reasons");
        return new OriginalFailureProjection(source, StrictJson.integer(root.get("auto_sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                SentinelCodec.i32(payload.get("starting_date_raw")), SentinelCodec.i32(payload.get("target_date_raw")),
                (int) StrictJson.integer(payload.get("requested_speed"), 1, 5), SentinelCodec.decodeNode(view),
                SentinelCodec.bool(payload.get("normal_status_query_attempted")), SentinelCodec.bool(payload.get("stop_validation_attempted")));
    }
    public Assessment assessIncomplete() {
        return new Assessment(Outcome.UNRESOLVED, Reason.ORIGINAL_PROJECTION_INCOMPLETE, null, 0, 0, List.of());
    }
}
