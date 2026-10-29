package org.xar.ck3.control.application.planning.finance.publicgift;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.LinkedHashMap;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;

/** Public arguments only. Actual native/ledger/checkpoint parsers remain the sole domain validators. */
public final class FactionGiftPublicCodec {
    private FactionGiftPublicCodec() { }
    public static Request decode(Method method, RawJson arguments) {
        Objects.requireNonNull(method); Objects.requireNonNull(arguments);
        OpportunityJson.Obj original = DriverJson.object(arguments.bytes(), MAX_ARGUMENT_BYTES);
        JsonNode parsed = DriverJson.toNode(original);
        return switch (method) {
            case CANDIDATE -> {
                Set<String> keys = new HashSet<>(Set.of("expected_revision", "same_frame_root"));
                if (parsed.has("minimum_gold_reserve_raw")) keys.add("minimum_gold_reserve_raw");
                ObjectNode row = StrictJson.object(parsed, keys);
                yield new CandidateQuery(revision(row), new RootProjection(originalObject(original.get("same_frame_root"))),
                        row.has("minimum_gold_reserve_raw") ? reserve(row.get("minimum_gold_reserve_raw")) : DEFAULT_RESERVE);
            }
            case SEND -> {
                ObjectNode row = StrictJson.object(parsed, Set.of("candidate", "checkpoint", "expected_revision"));
                yield new Send(revision(row), new NativeCandidate(originalObject(original.get("candidate"))),
                        new Checkpoint(originalObject(original.get("checkpoint"))));
            }
            case RECEIPT -> {
                ObjectNode row = StrictJson.object(parsed, Set.of("pending", "expected_revision"));
                yield new ReceiptQuery(revision(row), new Pending(originalObject(original.get("pending"))));
            }
            case COLD_RECOVERY -> {
                ObjectNode row = StrictJson.object(parsed, Set.of("pending", "expected_revision"));
                yield new ColdRecoveryQuery(revision(row), new Pending(originalObject(original.get("pending"))));
            }
            case RESOLVED -> {
                ObjectNode row = StrictJson.object(parsed, Set.of("request_id", "expected_revision"));
                JsonNode id = row.get("request_id");
                StrictJson.require(id != null && id.isTextual(), "original resolved request_id string required");
                yield new ResolvedQuery(revision(row), id.textValue());
            }
        };
    }
    public static RawJson encode(Request request) {
        Objects.requireNonNull(request);
        var fields = new LinkedHashMap<String, OpportunityJson.Value>();
        fields.put("expected_revision", new OpportunityJson.Text(PublicUnsigned64.canonical(
                request.expectedRevision(), PublicUnsigned64.Minimum.ZERO)));
        switch (request) {
            case CandidateQuery query -> {
                fields.put("same_frame_root", DriverJson.object(query.sameFrameRoot().original().bytes(), MAX_ARGUMENT_BYTES));
                fields.put("minimum_gold_reserve_raw", new OpportunityJson.Text(query.minimumGoldReserveRaw().toString()));
            }
            case Send send -> {
                fields.put("candidate", DriverJson.object(send.candidate().original().bytes(), MAX_ARGUMENT_BYTES));
                fields.put("checkpoint", DriverJson.object(send.checkpoint().original().bytes(), MAX_ARGUMENT_BYTES));
            }
            case ReceiptQuery query -> fields.put("pending", DriverJson.object(query.pending().original().bytes(), MAX_ARGUMENT_BYTES));
            case ColdRecoveryQuery query -> fields.put("pending", DriverJson.object(query.pending().original().bytes(), MAX_ARGUMENT_BYTES));
            case ResolvedQuery query -> fields.put("request_id", new OpportunityJson.Text(query.requestId()));
        }
        return PublicDataJson.encodeTyped(new OpportunityJson.Obj(fields));
    }
    public static RawJson businessPublic(Method method, RawJson nativeBusiness) { return FactionGiftPublicNumbers.businessPublic(method, nativeBusiness); }
    public static RawJson businessNative(Method method, RawJson publicBusiness) { return FactionGiftPublicNumbers.businessNative(method, publicBusiness); }
    public static RawJson candidateNative(RawJson candidate) { return FactionGiftPublicNumbers.candidateNative(candidate); }
    public static RawJson pendingNative(RawJson pending) { return FactionGiftPublicNumbers.pendingNative(pending); }
    public static RawJson rootNative(RawJson root) { return FactionGiftPublicNumbers.rootNative(root); }
    public static RawJson checkpointNative(RawJson checkpoint) { return FactionGiftPublicNumbers.checkpointNative(checkpoint); }
    private static BigInteger revision(ObjectNode row) {
        return PublicUnsigned64.parse(row.get("expected_revision"), PublicUnsigned64.Minimum.ZERO,
                PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
    }
    private static BigInteger reserve(JsonNode node) {
        StrictJson.require(node != null && !node.isNull(), "reserve is missing or null");
        if (node.isTextual()) {
            String token = node.textValue();
            StrictJson.require(token.length() <= MAX_RESERVE_CHARACTERS && token.matches("0|-?[1-9][0-9]*")
                    && (token.charAt(0) == '-' ? token.length() - 1 : token.length()) <= MAX_RESERVE_DIGITS, "canonical signed reserve decimal required");
            return new BigInteger(token);
        }
        StrictJson.require(node.isIntegralNumber(), "reserve must be an integer, never bool/float");
        BigInteger exact = node.bigIntegerValue();
        StrictJson.require(exact.abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER) <= 0,
                "unsafe public reserve number requires canonical decimal text");
        return exact;
    }
    private static RawJson originalObject(OpportunityJson.Value value) {
        StrictJson.require(value instanceof OpportunityJson.Obj, "original Gift object required");
        return PublicDataJson.encodeTyped(value);
    }
}
