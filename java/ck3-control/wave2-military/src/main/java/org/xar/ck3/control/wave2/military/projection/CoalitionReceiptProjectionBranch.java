package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.coalition.CoalitionRiskJsonAdapter;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition;
import org.xar.ck3.control.wave2.military.coalitionreceipt.CoalitionExecutionReceipt;

/** Three explicit contracts on the existing coalition-normalize role; no query or qualification authority. */
public final class CoalitionReceiptProjectionBranch {
    public static final int LIMIT = 65_536;
    private CoalitionReceiptProjectionBranch() { }

    public sealed interface Request permits NormalizeRequest, ReceiptRequest, HistoryRequest { }
    public sealed interface Result permits Normalized, Validated, History { }
    private static final class Raw {
        private final JsonNode value;
        Raw(JsonNode value) { StrictJson.require(value != null, "required original field missing"); this.value = value.deepCopy(); }
        JsonNode copy() { return value.deepCopy(); }
    }
    private record NormalizeRequest(Raw value, Raw snapshot, Raw declaration, Raw binding, String requestId,
                                    BigInteger captureEpoch) implements Request { }
    private record ReceiptRequest(Raw frame, String requestId, byte[] resultToken) implements Request {
        private ReceiptRequest { resultToken = resultToken.clone(); }
        @Override public byte[] resultToken() { return resultToken.clone(); }
    }
    private record HistoryRequest(Raw result) implements Request { }
    private record Normalized(PrewarCoalition.Observation value) implements Result { }
    private record Validated(CoalitionExecutionReceipt.ValidatedCommandResult value, byte[] resultToken) implements Result {
        private Validated { resultToken = resultToken.clone(); }
        @Override public byte[] resultToken() { return resultToken.clone(); }
    }
    private record History(CoalitionExecutionReceipt.HistoryProjection value) implements Result { }

    public static Request decode(byte[] raw) {
        JsonNode parsed = StrictJson.parse(raw, LIMIT);
        StrictJson.require(parsed instanceof ObjectNode, "coalition request object required");
        ObjectNode row = (ObjectNode) parsed;
        if (!row.has("operation")) {
            StrictJson.object(row, Set.of("value", "snapshot", "expected_declaration", "expected_request_binding",
                    "expected_request_id", "expected_capture_epoch"));
            JsonNode epoch = row.get("expected_capture_epoch");
            return new NormalizeRequest(new Raw(row.get("value")), new Raw(row.get("snapshot")),
                    new Raw(row.get("expected_declaration")), new Raw(row.get("expected_request_binding")),
                    StrictJson.text(row.get("expected_request_id")),
                    epoch.isNull() ? null : StrictJson.integer(epoch, BigInteger.ONE, StrictJson.UINT64_MAX));
        }
        String operation = StrictJson.text(row.get("operation"));
        if (operation.equals("receipt-validate")) {
            StrictJson.object(row, Set.of("operation", "frame", "expected_request_id"));
            // Source spans preserve opaque body floats, exponent notation and negative zero. Requires span addendum02.
            byte[] token = new HolySdkJson.Source(raw).token("/frame/result");
            return new ReceiptRequest(new Raw(row.get("frame")), StrictJson.text(row.get("expected_request_id")), token);
        }
        StrictJson.require(operation.equals("history-projection"), "unknown coalition branch operation");
        StrictJson.object(row, Set.of("operation", "result"));
        return new HistoryRequest(new Raw(row.get("result")));
    }

    public static Result project(Request request) {
        if (request instanceof NormalizeRequest input) {
            return new Normalized(CoalitionRiskJsonAdapter.normalize(input.value().copy(),
                    input.snapshot().copy(), input.declaration().copy(), input.binding().copy(), input.requestId(), input.captureEpoch()));
        }
        if (request instanceof ReceiptRequest input) {
            return new Validated(CoalitionExecutionReceipt.validate(input.frame().copy(), input.requestId()),
                    input.resultToken());
        }
        if (request instanceof HistoryRequest input) {
            return new History(CoalitionExecutionReceipt.historyProjection(input.result().copy()));
        }
        throw new IllegalStateException("unhandled sealed coalition request");
    }

    public static byte[] encode(Result result) {
        if (result instanceof Normalized value) return StrictJson.canonical(CoalitionRiskJsonAdapter.encodeObservation(value.value()), LIMIT);
        if (result instanceof History value) return StrictJson.canonical(CoalitionExecutionReceipt.historySummary(value.value()), LIMIT);
        if (result instanceof Validated value) {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            output.writeBytes("{\"receipt\":".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
            output.writeBytes(StrictJson.canonical(value.value().receipt().toJson(), LIMIT));
            output.writeBytes(",\"result\":".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
            output.writeBytes(value.resultToken());
            output.write('}');
            byte[] raw = output.toByteArray();
            StrictJson.parse(raw, LIMIT); // Validate bounded output without canonicalizing the unvalidated result token.
            return raw;
        }
        throw new IllegalStateException("unhandled sealed coalition result");
    }

}

