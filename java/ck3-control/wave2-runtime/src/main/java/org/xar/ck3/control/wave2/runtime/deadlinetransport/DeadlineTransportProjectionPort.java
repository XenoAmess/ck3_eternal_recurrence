package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/**
 * Pure projection of one original authority return. The caller retains the full
 * original frames/actions and its durable UNKNOWN guard. HTTP never performs a
 * native action, authorizes replay, grants source qualification or awards days.
 */
public final class DeadlineTransportProjectionPort
        implements ProjectionPort<DeadlineTransportProjectionPort.Input, DeadlineTransport.Observation> {
    public static final int API_MAXIMUM_BYTES = 65_536;

    public record Input(DeadlineTransport.PreparedRequest request, DeadlineTransport.Completion completion) {
        public Input {
            Objects.requireNonNull(request, "request");
            Objects.requireNonNull(completion, "completion");
        }
    }

    @Override public ProjectionOperation operation() { return ProjectionOperation.DEADLINE_TRANSPORT_PROJECT; }

    @Override public Input decode(byte[] rawPayload) {
        ObjectNode payload = StrictJson.object(StrictJson.parse(rawPayload, API_MAXIMUM_BYTES),
                Set.of("request", "completion"));
        // The legacy JSON encoder retains integer versus decimal token types.
        return new Input(DeadlineTransportCodec.prepare(LegacyJsonValues.encode(payload.get("request"))),
                DeadlineTransportCodec.completion(LegacyJsonValues.encode(payload.get("completion"))));
    }

    @Override public DeadlineTransport.Observation project(Input input) {
        Objects.requireNonNull(input, "input");
        try {
            return DeadlineTransport.observe(input.request(), input.completion());
        } catch (DeadlineTransport.ObservationRejection refusal) {
            throw new ProjectionDomainRejection(refusal.getMessage());
        }
    }

    @Override public byte[] encode(DeadlineTransport.Observation result) {
        Objects.requireNonNull(result, "result");
        return DeadlineTransportCodec.encodeClock(result.completion().clock());
    }

    @Override public int inputMaximumBytes() { return API_MAXIMUM_BYTES; }
    @Override public int outputMaximumBytes() { return API_MAXIMUM_BYTES; }
}
