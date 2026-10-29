package org.xar.ck3.control.g2.m4;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Result;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionConsumer;

/**
 * The ordinary consumer's evaluator over the already registered M4 domain port.
 * Original observed bytes cross the common wire unchanged. Neither an envelope
 * nor a verified result grants a native observation, writer lock or submitter.
 */
public final class M4OrdinaryConstructionPort implements OrdinaryWartimeConstructionConsumer.Evaluator {
    public record Context(String requestId, G2Source source) {
        public Context { Objects.requireNonNull(requestId); Objects.requireNonNull(source); }
    }

    @FunctionalInterface public interface CurrentContext {
        /** The existing owner supplies current source provenance and a request identity for each evaluation. */
        Context readCurrent();
    }

    private final M4ConstructionConsumers.ProjectionPort port;
    private final CurrentContext contexts;

    public M4OrdinaryConstructionPort(M4ConstructionConsumers.ProjectionPort port, CurrentContext contexts) {
        this.port = Objects.requireNonNull(port);
        this.contexts = Objects.requireNonNull(contexts);
    }

    @Override public Result evaluate(ObservedRequest observed) {
        Objects.requireNonNull(observed);
        byte[] original = observed.original();
        Context context = Objects.requireNonNull(contexts.readCurrent(), "current M4 call context");
        G2Request request = new G2Request(context.requestId(), Milestone.M4, context.source(),
                ProjectionJson.object(original, OrdinaryWartimeConstructionCodec.MAX_BYTES));
        G2Response response = Objects.requireNonNull(port.evaluate(request), "M4 ordinary construction response");
        StrictJson.require(response.milestone() == Milestone.M4
                && request.requestId().equals(response.requestId()) && request.source().equals(response.source()),
                "ordinary construction response differs from the submitted M4 request/source");
        // This uses the sole existing composer to validate data. It grants no replay
        // permission and does not replace the consumer's fresh check under its owner lock.
        return OrdinaryWartimeConstructionCodec.verifyResponse(original, response.result().bytes());
    }
}
