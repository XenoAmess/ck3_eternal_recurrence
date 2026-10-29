package org.xar.ck3.control.g2.m4;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentConsumers.EnrichedJson;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Context;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Outlay;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Input;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Reason;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Status;

/**
 * Three existing construction gate positions over the one G2 evaluator. These
 * data-only consumers never create an intent, submit an action or write a ledger.
 */
public final class M4ConstructionConsumers {
    public static final String ATTACHMENT_FIELD = "wartime_construction_cash_v1";
    private M4ConstructionConsumers() { }

    public enum Stage { BEFORE_OPTIONAL_QUERY, AFTER_NATIVE_QUOTE, BEFORE_EXISTING_INTENT }

    @FunctionalInterface
    public interface ProjectionPort {
        /** Direct M4Research/engine or the one typed Java client; transport failure propagates. */
        G2Response evaluate(G2Request request);
    }

    public record CurrentInput(G2Source source, Context context) {
        public CurrentInput { Objects.requireNonNull(source); Objects.requireNonNull(context); }
    }

    @FunctionalInterface
    public interface CurrentInputs {
        /** The existing caller supplies copied observations; this interface grants no native read. */
        CurrentInput readCurrent();
    }

    public record DecisionView(Status status, Optional<Reason> reason, boolean newSpendAllowed) {
        public DecisionView {
            Objects.requireNonNull(status); Objects.requireNonNull(reason);
            StrictJson.require(newSpendAllowed == (status != Status.DEFER), "M4 gate status/allow branch differs");
            StrictJson.require((status == Status.PEACE) == reason.isEmpty(), "M4 gate reason branch differs");
        }
    }

    /** An evaluation is a bound observation, never a reusable final submission permission. */
    public static final class Evaluation {
        private final Stage stage;
        private final G2Request request;
        private final G2Response response;
        private final DecisionView decision;
        private Evaluation(Stage stage, G2Request request, G2Response response, DecisionView decision) {
            this.stage = stage; this.request = request; this.response = response; this.decision = decision;
        }
        public Stage stage() { return stage; }
        public G2Request request() { return request; }
        public G2Response response() { return response; }
        public DecisionView decision() { return decision; }
    }

    public static Evaluation beforeOptionalQuery(ProjectionPort port, CurrentInputs inputs,
            String requestId, String kind) {
        return evaluate(Stage.BEFORE_OPTIONAL_QUERY, port, inputs, requestId,
                new Outlay(kind, Optional.of(BigInteger.ZERO)));
    }

    public static Evaluation afterNativeQuote(ProjectionPort port, CurrentInputs inputs,
            String requestId, Outlay actualNativeOutlay) {
        return evaluate(Stage.AFTER_NATIVE_QUOTE, port, inputs, requestId, actualNativeOutlay);
    }

    /** Must be called by the original submission owner after its original guards, before intent creation. */
    public static Evaluation requireCurrentBeforeIntent(ProjectionPort port, CurrentInputs inputs,
            String requestId, Outlay actualNativeOutlay) {
        Evaluation current = evaluate(Stage.BEFORE_EXISTING_INTENT, port, inputs, requestId, actualNativeOutlay);
        if (!current.decision().newSpendAllowed()) { throw new DeferredConstructionException(current); }
        return current;
    }

    private static Evaluation evaluate(Stage stage, ProjectionPort port, CurrentInputs inputs,
            String requestId, Outlay outlay) {
        Objects.requireNonNull(port); Objects.requireNonNull(inputs); Objects.requireNonNull(outlay);
        CurrentInput current = Objects.requireNonNull(inputs.readCurrent(), "current M4 input");
        var produced = M4WartimeInputProducer.produce(current.context(), outlay);
        G2Request request = new G2Request(requestId, Milestone.M4, current.source(),
                ProjectionJson.object(produced.utf8(), WartimeConstructionCodec.MAX_BYTES));
        G2Response response = Objects.requireNonNull(port.evaluate(request), "M4 response");
        return validate(stage, request, response, produced.input());
    }

    /** Used for persistence readback as well; it performs no evaluation, query or replay. */
    static Evaluation restore(Stage stage, G2Request request, G2Response response) {
        return validate(stage, request, response, WartimeConstructionCodec.decode(request.payload().bytes()));
    }

    private static Evaluation validate(Stage stage, G2Request request, G2Response response, Input input) {
        Objects.requireNonNull(stage); Objects.requireNonNull(request); Objects.requireNonNull(response);
        StrictJson.require(request.milestone() == Milestone.M4 && response.milestone() == Milestone.M4,
                "construction consumer requires M4");
        StrictJson.require(request.requestId().equals(response.requestId()) && request.source().equals(response.source()),
                "M4 response request/source binding differs");
        JsonNode result = StrictJson.parse(response.result().bytes(), WartimeConstructionCodec.MAX_BYTES);
        StrictJson.require(result.isObject() && text(result, "schema").equals("xar.wartime-construction-cash.v1"),
                "M4 wartime gate result schema");
        StrictJson.require(text(result, "construction_kind").equals(input.kindWire()), "M4 construction kind differs");
        JsonNode cost = required(result, "construction_gold_raw");
        StrictJson.require(input.cost().known()
                ? cost.isIntegralNumber() && cost.bigIntegerValue().equals(input.cost().value())
                : cost.isNull(), "M4 construction quote differs");
        StrictJson.require(GiftWarCashCodec.encodeFrame(input.context().snapshot().frame()).equals(required(result, "source_frame")),
                "M4 inner observed source frame differs");
        Status status = status(text(result, "status"));
        Optional<Reason> reason = result.has("reason") ? Optional.of(reason(text(result, "reason"))) : Optional.empty();
        DecisionView view = new DecisionView(status, reason, flag(result, "new_spend_allowed"));
        zero(result, "future_income_credited_raw"); zero(result, "loan_or_refund_credited_raw");
        StrictJson.require(flag(result, "does_not_open_or_refresh_mercenary_procurement_epoch"),
                "construction gate cannot open a procurement epoch");
        if (stage == Stage.BEFORE_OPTIONAL_QUERY) {
            StrictJson.require(input.cost().known() && input.cost().value().signum() == 0,
                    "prequery checkpoint requires zero outlay");
        }
        return new Evaluation(stage, request, response, view);
    }

    /** Preserve the exact old plan/query field. Original bytes remain available and are never overwritten. */
    public static EnrichedJson attach(Evaluation evaluation, ProjectionJson original, int maximumBytes) {
        Objects.requireNonNull(evaluation); Objects.requireNonNull(original);
        StrictJson.require(original.isObject(), "construction attachment requires an original object");
        byte[] before = original.bytes();
        ObjectNode copy = ((ObjectNode) StrictJson.parse(before, maximumBytes)).deepCopy();
        copy.set(ATTACHMENT_FIELD, StrictJson.parse(evaluation.response().result().bytes(), WartimeConstructionCodec.MAX_BYTES));
        byte[] after = ProjectionJson.object(SdkProjectionJson.encode(copy, maximumBytes), maximumBytes).bytes();
        return new EnrichedJson(before, sha256(before), after);
    }

    public static final class DeferredConstructionException extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        // Exception serialization carries diagnostics; business DTOs use the checkpoint codec.
        private final transient Evaluation evaluation;
        private DeferredConstructionException(Evaluation evaluation) {
            super("wartime optional construction deferred before intent/send: "
                    + evaluation.decision().reason().orElseThrow().wire());
            this.evaluation = evaluation;
        }
        public Evaluation evaluation() {
            return Objects.requireNonNull(evaluation,
                    "M4 evaluation is not Java-serialized; restore the request/response checkpoint");
        }
    }

    private static JsonNode required(JsonNode node, String key) {
        JsonNode value = node.get(key); StrictJson.require(value != null, "missing M4 result field: " + key); return value;
    }
    private static String text(JsonNode node, String key) {
        JsonNode value = required(node, key); StrictJson.require(value.isTextual(), "M4 result text required: " + key); return value.textValue();
    }
    private static boolean flag(JsonNode node, String key) {
        JsonNode value = required(node, key); StrictJson.require(value.isBoolean(), "M4 result bool required: " + key); return value.booleanValue();
    }
    private static void zero(JsonNode node, String key) {
        JsonNode value = required(node, key); StrictJson.require(value.isIntegralNumber() && value.bigIntegerValue().signum() == 0,
                "unreceived M4 funding must retain zero credit: " + key);
    }
    private static Status status(String wire) {
        for (Status value : Status.values()) if (value.wire().equals(wire)) return value;
        throw new IllegalArgumentException("unknown M4 gate status");
    }
    private static Reason reason(String wire) {
        for (Reason value : Reason.values()) if (value.wire().equals(wire)) return value;
        throw new IllegalArgumentException("unknown M4 gate reason");
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 unavailable", error); }
    }
}
