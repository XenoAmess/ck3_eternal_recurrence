package org.xar.ck3.control.wave2.finance.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Two original bounded documents share one wrapper; normalization stays in the existing codec. */
public final class RawCashNormalizeProjectionPort
        implements ProjectionPort<RawCashNormalizeProjectionPort.Request, RawCashCodec.NormalizedCurrentCash> {
    public static final int INPUT_MAX_BYTES = 2 * 65_536 + 1_024;
    public static final int OUTPUT_MAX_BYTES = 65_536;
    private static final Set<String> FIELDS = Set.of("value", "snapshot");

    public record Request(JsonNode value, ObjectNode snapshot) {
        public Request {
            StrictJson.require(value != null && !value.isMissingNode(), "raw cash value is required");
            StrictJson.require(snapshot != null, "raw cash SDK snapshot object is required");
            value = value.deepCopy();
            snapshot = snapshot.deepCopy();
        }
        @Override public JsonNode value() { return value.deepCopy(); }
        @Override public ObjectNode snapshot() { return snapshot.deepCopy(); }
    }

    @Override public ProjectionOperation operation() { return ProjectionOperation.RAW_CASH_NORMALIZE; }
    @Override public int inputMaximumBytes() { return INPUT_MAX_BYTES; }
    @Override public int outputMaximumBytes() { return OUTPUT_MAX_BYTES; }
    @Override public Request decode(byte[] rawPayload) {
        ObjectNode wrapper = StrictJson.object(StrictJson.parse(rawPayload, INPUT_MAX_BYTES), FIELDS);
        StrictJson.require(wrapper.get("snapshot") instanceof ObjectNode, "raw cash SDK snapshot object is required");
        return new Request(wrapper.get("value"), (ObjectNode) wrapper.get("snapshot"));
    }
    @Override public RawCashCodec.NormalizedCurrentCash project(Request input) {
        Objects.requireNonNull(input, "input");
        // Each original document retains its separate 64KiB encoding and codec boundary.
        try {
            return RawCashCodec.normalize(SdkProjectionJson.encode(input.value()),
                    SdkProjectionJson.encode(input.snapshot()));
        } catch (ContractViolationException error) {
            // RawCashCodec reserves this type for known input checks; generated output failures escape.
            var refusal = new ProjectionDomainRejection(error.getMessage());
            refusal.initCause(error);
            throw refusal;
        }
    }
    @Override public byte[] encode(RawCashCodec.NormalizedCurrentCash result) {
        byte[] raw = Objects.requireNonNull(result, "result").toJson();
        StrictJson.require(raw.length <= OUTPUT_MAX_BYTES, "raw cash result exceeds declared role budget");
        return raw;
    }
}
