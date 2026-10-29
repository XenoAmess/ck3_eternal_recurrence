package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;

/** Source-bound interpretation of existing .4 native prisoner responses, not a writer or terminal-proof authority. */
public final class PrisonerSubmissionEvidence12004 {
    public static final String RELEASE_STEP = "submit-player-prisoner-release-private-v1";
    public static final String RANSOM_STEP = "submit-player-prisoner-ransom-private-v1";
    public static final String MAILBOX_SHA256 = "5b92eedeb54e5e2c5056be377628ee18793bc305c1e6d909feb950bde5527dd1";
    public static final String ROUTER_SHA256 = "888d93ae8c360cc72c612b16b4db4879a573cf8fefde825bd8349bc61984b506";
    private static final String FRAME_STALE = "prisoner request revision or paused player frame is stale";
    private static final int MAX_BYTES = 1_048_576;
    private static final BigInteger MAX_CHARACTER = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.TWO);

    public enum Kind { RELEASE, RANSOM }
    public enum State { PRE_SUBMIT_REJECTION_OBSERVED, SUBMITTED_PENDING, SUBMISSION_UNKNOWN }
    /** Root owns qualification of this loaded-native/source-epoch relation. Merely constructing this record is no qualification. */
    public record Scope(Session session, ExactRef loadedNative, String sourceEpoch, ExactRef nativeQualification,
            ExactRef mailboxSource, ExactRef routerSource) {
        public Scope {
            Objects.requireNonNull(session); Objects.requireNonNull(loadedNative); Objects.requireNonNull(nativeQualification);
            Objects.requireNonNull(mailboxSource); Objects.requireNonNull(routerSource);
            StrictJson.require(session.executable().sha256().equals(NativePlayerHeirObservation12004.EXE_SHA256), "actual .4 source scope required");
            StrictJson.require(sourceEpoch != null && sourceEpoch.matches("0|[1-9][0-9]{0,19}"), "canonical source epoch decimal required");
            StrictJson.require(new BigInteger(sourceEpoch).compareTo(StrictJson.UINT64_MAX) <= 0, "source epoch range");
            StrictJson.require(mailboxSource.bytes() == 26343 && mailboxSource.sha256().equals(MAILBOX_SHA256)
                    && routerSource.bytes() == 55344 && routerSource.sha256().equals(ROUTER_SHA256), "reviewed native error producer/caller source required");
        }
    }
    public sealed interface Terms permits ReleaseTerms, RansomTerms { BigInteger prisonerCharacterId(); }
    public record ReleaseTerms(BigInteger prisonerCharacterId, int selectedOptionMask) implements Terms {
        public ReleaseTerms { character(prisonerCharacterId); StrictJson.require(selectedOptionMask >= 0 && selectedOptionMask <= 8191, "native thirteen-option mask required"); }
    }
    public record RansomTerms(BigInteger prisonerCharacterId, BigInteger payerCharacterId, BigInteger quotedGoldRaw) implements Terms {
        public RansomTerms { character(prisonerCharacterId); character(payerCharacterId); positive(quotedGoldRaw); }
    }
    public record Request(Scope scope, Kind kind, String requestId, BigInteger expectedNativeRevision,
            BigInteger selectedQuerySequence, Terms terms, ExactRef original) {
        public Request {
            Objects.requireNonNull(scope); Objects.requireNonNull(kind); StrictJson.text(requestId);
            positive(expectedNativeRevision); positive(selectedQuerySequence); Objects.requireNonNull(terms); Objects.requireNonNull(original);
            StrictJson.require((kind == Kind.RELEASE) == (terms instanceof ReleaseTerms), "typed native request kind/terms differ");
        }
        public String step() { return kind == Kind.RELEASE ? RELEASE_STEP : RANSOM_STEP; }
    }
    public record Observation(State state, Request request, ExactRef originalResponse, Optional<String> nativeError) {
        public Observation { Objects.requireNonNull(state); Objects.requireNonNull(request); Objects.requireNonNull(originalResponse); Objects.requireNonNull(nativeError); }
        /** Outer archive must rederive against qualified runtime source and its original request before ActionState.Rejected. */
        public boolean terminalProofInIsolation() { return false; }
        public boolean replayAuthorized() { return false; }
        public boolean releaseOrPaymentProven() { return false; }
    }
    private PrisonerSubmissionEvidence12004() { }

    public static Request parseRequest(byte[] raw, ExactRef original, Scope scope) {
        exact(raw, original); Objects.requireNonNull(scope); JsonNode value = StrictJson.parse(raw, MAX_BYTES);
        StrictJson.require("execute_step".equals(text(value, "type")), "original execute_step request required");
        StrictJson.integer(field(value, "protocol_version"), 1, 1);
        String step = text(value, "step"); Kind kind;
        ObjectNode request;
        if (step.equals(RELEASE_STEP)) {
            kind = Kind.RELEASE;
            request = StrictJson.object(value, Set.of("type", "protocol_version", "request_id", "step", "expected_revision",
                    "release_query_sequence", "prisoner_character_id", "release_option_mask_bits"));
        } else {
            StrictJson.require(step.equals(RANSOM_STEP), "reviewed native prisoner step required"); kind = Kind.RANSOM;
            request = StrictJson.object(value, Set.of("type", "protocol_version", "request_id", "step", "expected_revision",
                    "quote_query_sequence", "prisoner_character_id", "payer_character_id", "quoted_gold_raw"));
        }
        BigInteger prisoner = StrictJson.integer(field(request, "prisoner_character_id"), BigInteger.ZERO, MAX_CHARACTER);
        Terms terms = kind == Kind.RELEASE
                ? new ReleaseTerms(prisoner, (int) StrictJson.integer(field(request, "release_option_mask_bits"), 0, 8191))
                : new RansomTerms(prisoner, StrictJson.integer(field(request, "payer_character_id"), BigInteger.ZERO, MAX_CHARACTER), uint(request, "quoted_gold_raw"));
        return new Request(scope, kind, text(request, "request_id"), uint(request, "expected_revision"),
                uint(request, kind == Kind.RELEASE ? "release_query_sequence" : "quote_query_sequence"), terms, original);
    }

    /** A parsed native rejection is after pipe dispatch; it must never be relabelled RejectedBeforeDispatch/zero bytes. */
    public static Observation parseResponse(byte[] raw, ExactRef original, Request request) {
        Objects.requireNonNull(request); exact(raw, original); JsonNode value = StrictJson.parse(raw, MAX_BYTES);
        StrictJson.require("command_result".equals(text(value, "type")) && request.requestId().equals(text(value, "request_id")), "original native request/response identity differs");
        StrictJson.integer(field(value, "protocol_version"), 1, 1);
        JsonNode ok = field(value, "ok"); StrictJson.require(ok.isBoolean(), "exact native ok boolean required");
        if (ok.booleanValue()) {
            ObjectNode envelope = StrictJson.object(value, Set.of("type", "protocol_version", "request_id", "ok", "result"));
            ObjectNode ack = StrictJson.object(field(envelope, "result"), Set.of("step", "accepted", "status"));
            StrictJson.require(request.step().equals(text(ack, "step")) && "submitted_verification_pending".equals(text(ack, "status")), "native pending-only prisoner ACK required");
            StrictJson.trueValue(field(ack, "accepted"));
            return new Observation(State.SUBMITTED_PENDING, request, original, Optional.empty());
        }
        StrictJson.object(value, Set.of("type", "protocol_version", "request_id", "ok", "error"));
        String error = text(value, "error");
        String kindStale = request.kind() == Kind.RELEASE ? "private release terms or request are stale" : "private ransom quote or request is stale";
        State state = error.equals(FRAME_STALE) || error.equals(kindStale)
                ? State.PRE_SUBMIT_REJECTION_OBSERVED : State.SUBMISSION_UNKNOWN;
        return new Observation(state, request, original, Optional.of(error));
    }
    private static void exact(byte[] raw, ExactRef reference) {
        Objects.requireNonNull(raw); Objects.requireNonNull(reference);
        StrictJson.require(raw.length > 0 && raw.length <= MAX_BYTES && reference.bytes() == raw.length
                && reference.sha256().equals(G2RetainedNativeSourceProvider.sha256(raw)), "original prisoner packet bytes/SHA differ");
    }
    private static JsonNode field(JsonNode value, String key) { StrictJson.require(value != null && value.isObject() && value.has(key), "required prisoner field: " + key); return value.get(key); }
    private static String text(JsonNode value, String key) { return StrictJson.text(field(value, key)); }
    private static BigInteger uint(JsonNode value, String key) { return StrictJson.integer(field(value, key), BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static void positive(BigInteger value) { StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 value required"); }
    private static void character(BigInteger value) { StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(MAX_CHARACTER) <= 0, "native non-null uint32 character bits required"); }
}
