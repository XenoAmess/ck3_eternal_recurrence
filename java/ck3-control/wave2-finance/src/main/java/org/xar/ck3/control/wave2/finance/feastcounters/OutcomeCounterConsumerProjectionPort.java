package org.xar.ck3.control.wave2.finance.feastcounters;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Projection;

/** One typed projection supplies both the original stored seed and observation subtree. */
public final class OutcomeCounterConsumerProjectionPort implements ProjectionPort<Projection, Projection> {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Override public ProjectionOperation operation() { return ProjectionOperation.FEAST_COUNTER_PROJECT; }
    @Override public Projection decode(byte[] payload) { return OutcomeCounterCodec.decodeProjection(payload); }
    @Override public Projection project(Projection input) { return input; }
    @Override public byte[] encode(Projection output) {
        try {
            ObjectNode receipt = JSON.createObjectNode();
            receipt.set("pre_outcome_values", JSON.readTree(OutcomeCounterCodec.encodeStoredSeed(output.before())));
            receipt.set("value_observation", JSON.readTree(OutcomeCounterCodec.encodeProjection(output)));
            byte[] encoded = JSON.writeValueAsBytes(receipt);
            if (encoded.length > OutcomeCounterCodec.MAX_BYTES) {
                throw new IllegalArgumentException("counter consumer projection exceeds its existing leaf profile");
            }
            return encoded;
        } catch (IOException error) {
            throw new IllegalStateException("existing counter codec output could not be framed", error);
        }
    }
    @Override public int inputMaximumBytes() { return OutcomeCounterCodec.MAX_BYTES; }
    @Override public int outputMaximumBytes() { return OutcomeCounterCodec.MAX_BYTES; }
}
