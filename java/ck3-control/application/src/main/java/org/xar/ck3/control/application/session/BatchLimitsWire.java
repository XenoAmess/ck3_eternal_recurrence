package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Duration;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** No bean coercion, aliases, defaulted missing values or floating-point durations. */
public final class BatchLimitsWire {
    public static final String SCHEMA = "xar.ordinary-session-batch-request/v1";
    public static final int MAXIMUM_BYTES = 4096;
    private static final Set<String> FIELDS = Set.of("schema", "batch_id", "maximum_turns", "wall_time_ms",
            "readiness_timeout_ms", "poll_interval_ms", "checkpoint_every_eligible_advances");
    private BatchLimitsWire() { }
    public static BatchLimits decode(byte[] bytes) {
        ObjectNode value = StrictJson.object(StrictJson.parse(bytes, MAXIMUM_BYTES), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "unsupported ordinary batch schema");
        return new BatchLimits(StrictJson.text(value.get("batch_id")), integer(value, "maximum_turns", 100_000),
                millis(value, "wall_time_ms", 86_400_000), millis(value, "readiness_timeout_ms", 3_600_000),
                millis(value, "poll_interval_ms", 60_000), integer(value, "checkpoint_every_eligible_advances", 100_000));
    }
    public static byte[] encode(BatchLimits value) {
        ObjectNode result = StrictJson.object(); result.put("schema", SCHEMA); result.put("batch_id", value.batchId());
        result.put("maximum_turns", value.maximumTurns()); result.put("wall_time_ms", value.wallTime().toMillis());
        result.put("readiness_timeout_ms", value.readinessTimeout().toMillis()); result.put("poll_interval_ms", value.pollInterval().toMillis());
        result.put("checkpoint_every_eligible_advances", value.checkpointEveryEligibleAdvances());
        return StrictJson.canonical(result, MAXIMUM_BYTES);
    }
    private static int integer(ObjectNode value, String field, int maximum) {
        return Math.toIntExact(StrictJson.integer(value.get(field), 1, maximum));
    }
    private static Duration millis(ObjectNode value, String field, long maximum) {
        return Duration.ofMillis(StrictJson.integer(value.get(field), 1, maximum));
    }
}
