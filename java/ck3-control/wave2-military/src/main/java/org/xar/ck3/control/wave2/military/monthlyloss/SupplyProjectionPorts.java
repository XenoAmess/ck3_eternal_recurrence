package org.xar.ck3.control.wave2.military.monthlyloss;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** One supply consumer capability in the existing resident host, with no IO or fallback. */
public final class SupplyProjectionPorts {
    public record Response(byte[] rawJson) {
        public Response {
            Objects.requireNonNull(rawJson);
            StrictJson.parse(rawJson, SupplyConsumerBindings.MAX_BYTES);
            rawJson = rawJson.clone();
        }
        @Override public byte[] rawJson() { return rawJson.clone(); }
    }
    private SupplyProjectionPorts() { }
    public static List<RegisteredProjection> registrations(ProjectionOperation operation) {
        return List.of(RegisteredProjection.of(new Port(Objects.requireNonNull(operation))));
    }
    private record Port(ProjectionOperation operation)
            implements ProjectionPort<SupplyConsumerBindings.Request, Response> {
        @Override public SupplyConsumerBindings.Request decode(byte[] raw) {
            return SupplyConsumerBindings.decodeRequest(raw);
        }
        @Override public Response project(SupplyConsumerBindings.Request input) {
            return new Response(SupplyConsumerBindings.exchange(Objects.requireNonNull(input)));
        }
        @Override public byte[] encode(Response result) { return result.rawJson(); }
        @Override public int inputMaximumBytes() { return SupplyConsumerBindings.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return SupplyConsumerBindings.MAX_BYTES; }
    }
}
