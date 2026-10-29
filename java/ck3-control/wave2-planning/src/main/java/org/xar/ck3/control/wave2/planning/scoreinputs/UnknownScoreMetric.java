package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation.Metric;

/** Exact unknown metric representation shared by the existing input/realm consumers. */
public record UnknownScoreMetric(Metric name, String reason) {
    public static Metric nameFromWire(String value) {
        for (Metric name : Metric.values()) { if (name.wire().equals(value)) { return name; } }
        throw new IllegalArgumentException("unknown scoring metric");
    }

    public UnknownScoreMetric {
        require(name != null && reason != null, "explicit metric and reason string required");
        if (!reason.isEmpty()) { StrictJson.text(reason); }
    }

    public ObjectNode toJson() {
        ObjectNode object = StrictJson.object();
        object.putNull("value"); object.put("unit", name.unit()); object.put("availability", "unknown");
        object.putNull("source_ref"); object.put("reason_zh", reason);
        return object;
    }
}
