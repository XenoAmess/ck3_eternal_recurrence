package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.client.G2ClientEvaluationPort;
import org.xar.ck3.control.g2.client.G2ClientOutcome;
import org.xar.ck3.control.g2.client.G2ClientOutcomeWire;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;

/** Borrowed resident transport. This adapter has no Native, queue submission or ledger port. */
public final class SuccessorUiQueueClient {
    private final G2ClientEvaluationPort client;
    public SuccessorUiQueueClient(G2ClientEvaluationPort client) { this.client = Objects.requireNonNull(client); }
    public SuccessorUiQueueClient(G2JavaClient client) { this(new G2ClientEvaluationPort(client)); }

    public record OriginalInputs(ProjectionJson transition, ProjectionJson appResponse, ProjectionJson independentSnapshot) {
        public OriginalInputs { Objects.requireNonNull(transition); Objects.requireNonNull(appResponse); Objects.requireNonNull(independentSnapshot); }
    }
    public sealed interface Outcome permits Evaluated, Unavailable, Failed, InvalidResult { G2ClientOutcome transport(); }
    public record Evaluated(SuccessorUiQueueModel.Result result, G2ClientOutcome.Success transport) implements Outcome {
        public Evaluated { Objects.requireNonNull(result); Objects.requireNonNull(transport); }
    }
    public record Unavailable(G2ClientOutcome.Unavailable transport) implements Outcome {
        public Unavailable { Objects.requireNonNull(transport); }
    }
    public record Failed(G2ClientOutcome.Failed transport) implements Outcome {
        public Failed { Objects.requireNonNull(transport); }
    }
    public record InvalidResult(G2ClientOutcome.Success transport) implements Outcome {
        public InvalidResult { Objects.requireNonNull(transport); }
    }

    public static G2Request request(String requestId, G2Source source, OriginalInputs originals) {
        Objects.requireNonNull(originals);
        ObjectNode body = SuccessionCodec.objectNode();
        body.put("schema", SuccessorUiQueueCodec.SCHEMA).put("operation", "consume_resume");
        body.set("transition", SuccessionCodec.parse(originals.transition().bytes()));
        body.set("app_response", SuccessionCodec.parse(originals.appResponse().bytes()));
        body.set("independent_snapshot", SuccessionCodec.parse(originals.independentSnapshot().bytes()));
        byte[] raw = SuccessionCodec.encode(body);
        SuccessorUiQueueCodec.decode(raw);
        return new G2Request(requestId, Milestone.M3, source, ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
    }

    public Outcome consume(String requestId, G2Source source, OriginalInputs originals) {
        return fromTransport(client.evaluate(request(requestId, source, originals)));
    }

    /** Uses the one shared evidence codec; restoring never invokes transport or any action. */
    public static byte[] persist(Outcome outcome) { return G2ClientOutcomeWire.encode(Objects.requireNonNull(outcome).transport()); }
    public static Outcome restore(byte[] bytes) { return fromTransport(G2ClientOutcomeWire.decode(bytes)); }

    private static Outcome fromTransport(G2ClientOutcome outcome) {
        return switch (outcome) {
            case G2ClientOutcome.Success success -> {
                try { yield new Evaluated(SuccessorUiQueueCodec.decodeResult(success.evaluation().response().result().bytes()), success); }
                catch (IllegalArgumentException invalid) { yield new InvalidResult(success); }
            }
            case G2ClientOutcome.Unavailable unavailable -> new Unavailable(unavailable);
            case G2ClientOutcome.Failed failure -> new Failed(failure);
        };
    }
}
