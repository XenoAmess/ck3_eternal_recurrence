package org.xar.ck3.control.application.planning.finance.publicgift;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;

/** The five original public Gift invocations. Objects retain original data; domain codecs validate their meaning. */
public final class FactionGiftPublicContract {
    public static final int MAX_ARGUMENT_BYTES = 262_144;
    public static final int MAX_RESERVE_DIGITS = 4300;
    public static final int MAX_RESERVE_CHARACTERS = MAX_RESERVE_DIGITS + 1;
    public static final BigInteger DEFAULT_RESERVE = BigInteger.valueOf(10_000_000);
    private FactionGiftPublicContract() { }
    public enum Method {
        CANDIDATE("ck3_query_faction_gift_candidate_private_v1"),
        SEND("ck3_send_faction_gift_private_v1"),
        RECEIPT("ck3_query_faction_gift_receipt_private_v1"),
        COLD_RECOVERY("ck3_query_faction_gift_cold_recovery_private_v1"),
        RESOLVED("ck3_query_resolved_faction_gift_outcome_v1");
        private final String originalName;
        Method(String originalName) { this.originalName = originalName; }
        public String originalName() { return originalName; }
    }
    public sealed interface Request permits CandidateQuery, Send, ReceiptQuery, ColdRecoveryQuery, ResolvedQuery {
        BigInteger expectedRevision();
        Method method();
    }
    public record RootProjection(RawJson original) {
        public RootProjection { object(original); }
    }
    public record NativeCandidate(RawJson original) {
        public NativeCandidate { object(original); }
    }
    public record Checkpoint(RawJson original) {
        public Checkpoint { object(original); }
    }
    public record Pending(RawJson original) {
        public Pending { object(original); }
    }
    public record CandidateQuery(BigInteger expectedRevision, RootProjection sameFrameRoot,
                                 BigInteger minimumGoldReserveRaw) implements Request {
        public CandidateQuery {
            revision(expectedRevision); Objects.requireNonNull(sameFrameRoot); Objects.requireNonNull(minimumGoldReserveRaw);
            StrictJson.require(minimumGoldReserveRaw.abs().toString().length() <= MAX_RESERVE_DIGITS,
                    "public reserve exceeds the original Python/current MCP 4300-digit integer bound");
            // Negative reserves retain the real pure-policy unavailable branch; no long clipping.
        }
        @Override public Method method() { return Method.CANDIDATE; }
    }
    public record Send(BigInteger expectedRevision, NativeCandidate candidate, Checkpoint checkpoint) implements Request {
        public Send { revision(expectedRevision); Objects.requireNonNull(candidate); Objects.requireNonNull(checkpoint); }
        @Override public Method method() { return Method.SEND; }
    }
    public record ReceiptQuery(BigInteger expectedRevision, Pending pending) implements Request {
        public ReceiptQuery { revision(expectedRevision); Objects.requireNonNull(pending); }
        @Override public Method method() { return Method.RECEIPT; }
    }
    public record ColdRecoveryQuery(BigInteger expectedRevision, Pending pending) implements Request {
        public ColdRecoveryQuery { revision(expectedRevision); Objects.requireNonNull(pending); }
        @Override public Method method() { return Method.COLD_RECOVERY; }
    }
    public record ResolvedQuery(BigInteger expectedRevision, String requestId) implements Request {
        public ResolvedQuery {
            revision(expectedRevision); Objects.requireNonNull(requestId);
            StrictJson.require(!requestId.isEmpty(), "resolved gift request_id is required");
        }
        @Override public Method method() { return Method.RESOLVED; }
    }
    static void revision(BigInteger revision) {
        PublicUnsigned64.canonical(revision, PublicUnsigned64.Minimum.ZERO);
    }
    private static void object(RawJson original) {
        Objects.requireNonNull(original);
        StrictJson.require(StrictJson.parse(original.bytes(), MAX_ARGUMENT_BYTES).isObject(),
                "original Gift object required; missing/null/object have distinct semantics");
    }
}
