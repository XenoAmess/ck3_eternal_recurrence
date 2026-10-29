package org.xar.ck3.control.admission.closedpartial;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict new schema, deliberately rejected by historical Python cold-input dispatch. */
public final class ClosedPartialEpochCodec {
    public static final String SCHEMA = "xar.closed-partial-full-epoch/v1";
    public static final String PREFIX_SCHEMA = "xar.closed-partial-full-settled-prefix/v1";
    private ClosedPartialEpochCodec() { }
    public record Epoch(String machineId, String observedAtUtc, String inputDigest,
            long fullSequence, long unknownSequence, long nextSequence,
            long savedCycles, long settledCycles, long savedDateRaw,
            ExactRef sdkClosed, ExactRef gameExit, ExactRef supervisorClosed,
            ExactRef recordingClosed, ExactRef screenReleased) {
        public Epoch {
            StrictJson.text(machineId); StrictJson.utc(observedAtUtc);
            StrictJson.require(inputDigest != null && inputDigest.matches("[0-9a-f]{64}"), "exact input digest");
            StrictJson.safe(fullSequence, 1); StrictJson.safe(unknownSequence, 1); StrictJson.safe(nextSequence, 1);
            StrictJson.safe(savedCycles, 0); StrictJson.safe(settledCycles, 1); StrictJson.safe(savedDateRaw, 0);
            StrictJson.require(settledCycles <= 30, "bounded closed partial FULL cycle domain");
            StrictJson.require(unknownSequence == fullSequence + 1 + settledCycles * 2
                    && nextSequence == unknownSequence + 1, "exact consumed AUTO/MET/UNKNOWN sequence domain");
            java.util.Objects.requireNonNull(sdkClosed); java.util.Objects.requireNonNull(gameExit);
            java.util.Objects.requireNonNull(supervisorClosed); java.util.Objects.requireNonNull(recordingClosed);
            java.util.Objects.requireNonNull(screenReleased);
        }
        public boolean grantsReady() { return false; }
        public boolean grantsWriterOrReducerRecovery() { return false; }
    }
    public static Epoch decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "machine_id", "observed_at_utc",
                "input_digest", "full_sequence", "unknown_sequence", "next_sequence", "saved_cycles", "settled_cycles",
                "saved_date_raw", "sdk_closed", "game_exit", "supervisor_closed", "recording_closed", "screen_released",
                "ready", "ordinary_cycle_credit", "game_day_credit", "pending_modified", "original_actions_replayed",
                "qualification_scope"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))
                && "PURE_CLOSED_EPOCH_METADATA_ONLY".equals(StrictJson.text(row.get("qualification_scope"))), "distinct closed partial epoch");
        for (String field : Set.of("ready", "pending_modified", "original_actions_replayed")) { falseValue(row.get(field)); }
        for (String field : Set.of("ordinary_cycle_credit", "game_day_credit")) { StrictJson.integer(row.get(field), 0, 0); }
        return new Epoch(StrictJson.text(row.get("machine_id")), StrictJson.utc(StrictJson.text(row.get("observed_at_utc"))),
                StrictJson.text(row.get("input_digest")), number(row, "full_sequence", 1), number(row, "unknown_sequence", 1),
                number(row, "next_sequence", 1), number(row, "saved_cycles", 0), number(row, "settled_cycles", 1),
                number(row, "saved_date_raw", 0), ExactRef.fromJson(row.get("sdk_closed")), ExactRef.fromJson(row.get("game_exit")),
                ExactRef.fromJson(row.get("supervisor_closed")), ExactRef.fromJson(row.get("recording_closed")),
                ExactRef.fromJson(row.get("screen_released")));
    }
    public static byte[] encode(Epoch epoch) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA); row.put("machine_id", epoch.machineId());
        row.put("observed_at_utc", epoch.observedAtUtc()); row.put("input_digest", epoch.inputDigest());
        row.put("full_sequence", epoch.fullSequence()); row.put("unknown_sequence", epoch.unknownSequence());
        row.put("next_sequence", epoch.nextSequence()); row.put("saved_cycles", epoch.savedCycles());
        row.put("settled_cycles", epoch.settledCycles()); row.put("saved_date_raw", epoch.savedDateRaw());
        row.set("sdk_closed", epoch.sdkClosed().toJson()); row.set("game_exit", epoch.gameExit().toJson());
        row.set("supervisor_closed", epoch.supervisorClosed().toJson()); row.set("recording_closed", epoch.recordingClosed().toJson());
        row.set("screen_released", epoch.screenReleased().toJson()); row.put("ready", false);
        row.put("ordinary_cycle_credit", 0); row.put("game_day_credit", 0); row.put("pending_modified", false);
        row.put("original_actions_replayed", false); row.put("qualification_scope", "PURE_CLOSED_EPOCH_METADATA_ONLY");
        return StrictJson.canonical(row, StrictJson.OUTPUT_MAX_BYTES);
    }
    static long number(ObjectNode row, String field, long min) {
        return StrictJson.integer(row.get(field), min, StrictJson.MAX_SAFE_INTEGER);
    }
    static ObjectNode object(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "required object; missing/null distinct"); return (ObjectNode) node;
    }
    static void falseValue(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean() && !node.booleanValue(), "actual false required");
    }
}
