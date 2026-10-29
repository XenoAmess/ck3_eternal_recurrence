package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.SavedFrame;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared pending/UNKNOWN contracts. Neither branch can produce replay or credit. */
public final class RetainedRequestState {
    private RetainedRequestState() { }
    public record Unknown(long sequence, ExactRef evidenceRef) {
        public Unknown { StrictJson.safe(sequence, 1); java.util.Objects.requireNonNull(evidenceRef); }
        public static Unknown fromJson(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("sequence", "evidence_ref", "status", "replayed", "cycle_credit", "day_credit"));
            StrictJson.require(StrictJson.text(row.get("status")).equals("unknown"), "UNKNOWN remains UNKNOWN");
            requireFalse(row.get("replayed"));
            StrictJson.require(ContinuityState.number(row, "cycle_credit", 0) == 0
                    && ContinuityState.number(row, "day_credit", 0) == 0, "UNKNOWN grants zero credit");
            return new Unknown(ContinuityState.number(row, "sequence", 1), ExactRef.fromJson(row.get("evidence_ref")));
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("sequence", sequence); row.set("evidence_ref", evidenceRef.toJson());
            row.put("status", "unknown"); row.put("replayed", false); row.put("cycle_credit", 0); row.put("day_credit", 0);
            return row;
        }
    }
    public record UnsettledAuto(long globalTurn, SavedFrame before, String beforeMetricsResponse, long autoSequence) {
        public UnsettledAuto {
            StrictJson.safe(globalTurn, 1); StrictJson.safe(autoSequence, 1);
            java.util.Objects.requireNonNull(before); StrictJson.text(beforeMetricsResponse);
        }
        public static UnsettledAuto fromJson(JsonNode value) {
            ObjectNode row = StrictJson.object(value, Set.of("global_turn", "before", "before_metrics_response", "auto_sequence", "stage"));
            StrictJson.require(StrictJson.text(row.get("stage")).equals("auto_unsettled"), "original unsettled AUTO stage");
            return new UnsettledAuto(ContinuityState.number(row, "global_turn", 1), SavedFrame.fromJson(row.get("before")),
                    StrictJson.text(row.get("before_metrics_response")), ContinuityState.number(row, "auto_sequence", 1));
        }
        public ObjectNode toJson() {
            ObjectNode row = StrictJson.object(); row.put("global_turn", globalTurn); row.set("before", before.toJson());
            row.put("before_metrics_response", beforeMetricsResponse); row.put("auto_sequence", autoSequence);
            row.put("stage", "auto_unsettled"); return row;
        }
    }
    private static void requireFalse(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(), "UNKNOWN cannot replay");
    }
}
