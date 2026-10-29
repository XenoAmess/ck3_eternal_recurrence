package org.xar.ck3.control.g2.m3;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.governance.succession.SuccessionConsumerPort;
import org.xar.ck3.control.wave2.governance.succession.SuccessionFreshnessCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionPlanningProducer;
import org.xar.ck3.control.wave2.governance.succession.SuccessionRetainedConsumers;
import org.xar.ck3.control.wave2.governance.succession.SuccessorUiQueueCodec;

/** Read-only M3 domain routing. Existing runtime owners keep actions, locks and persistence. */
public final class M3Research implements G2Domain {
    public static final int MAXIMUM_BYTES = 1_048_576;
    private static final ObjectMapper JSON = new ObjectMapper();
    @Override public Milestone milestone() { return Milestone.M3; }

    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request);
        if (request.milestone() != milestone()) { throw new IllegalArgumentException("M3 domain requires the M3 milestone"); }
        byte[] raw = ProjectionJson.object(request.payload().bytes(), MAXIMUM_BYTES).bytes();
        String schema = schema(raw);
        byte[] result = switch (schema) {
            case "xar.java-succession-planning-producer/v1" -> SuccessionPlanningProducer.apply(raw);
            case "xar.java-succession-retained-consumer/v1" -> SuccessionRetainedConsumers.apply(raw);
            case SuccessorUiQueueCodec.SCHEMA -> SuccessorUiQueueCodec.apply(raw);
            case SuccessionFreshnessCodec.SCHEMA -> SuccessionFreshnessCodec.observe(raw);
            case SuccessionConsumerPort.SCHEMA -> SuccessionConsumerPort.apply(raw);
            default -> throw new IllegalArgumentException("unknown M3 payload schema");
        };
        return new G2Response(request.requestId(), milestone(), request.source(), ProjectionJson.value(result, MAXIMUM_BYTES));
    }

    private static String schema(byte[] raw) {
        try {
            JsonNode value = JSON.readTree(raw).get("schema");
            if (value == null || !value.isTextual() || value.textValue().isEmpty()) {
                throw new IllegalArgumentException("M3 payload schema must be a nonempty string");
            }
            return value.textValue();
        } catch (IOException error) { throw new IllegalArgumentException("invalid M3 payload JSON", error); }
    }
}
