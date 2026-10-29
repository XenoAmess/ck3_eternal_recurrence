package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Exactly one write attempt per consumed permit. ACK never implies the intended game effect. */
public interface NativeActionPort {
    DispatchOutcome submit(SubmissionPermit permit, NativeRequest request, Instant deadline) throws InterruptedException;

    /** Exact-ID pop of an already received original. Empty means no matching cached ACK, never unsupported. */
    default Optional<AckReceived> pollOriginalOutcome(String attemptedRequestId) throws IOException {
        throw new IOException("actual Native action provider does not implement zero-I/O original outcome polling");
    }

    sealed interface DispatchOutcome permits AckReceived, RejectedBeforeDispatch, Unknown { String requestId(); }
    record OutboundPacket(String requestId, byte[] originalPacket) {
        public OutboundPacket {
            StrictJson.text(requestId); Objects.requireNonNull(originalPacket); originalPacket = originalPacket.clone();
            StrictJson.require(originalPacket.length > 0 && originalPacket.length <= RawJson.MAXIMUM_BYTES + 4, "bounded actual outbound native packet required");
        }
        @Override public byte[] originalPacket() { return originalPacket.clone(); }
        @Override public boolean equals(Object other) { return other instanceof OutboundPacket value && requestId.equals(value.requestId) && java.util.Arrays.equals(originalPacket, value.originalPacket); }
        @Override public int hashCode() { return Objects.hash(requestId, java.util.Arrays.hashCode(originalPacket)); }
    }
    record AckReceived(String requestId, boolean nativeOk, Optional<RawJson> originalResultToken, RawJson originalFrame,
            byte[] originalPacket, Optional<OutboundPacket> outbound, Optional<NativeRequestChronology> custody) implements DispatchOutcome {
        public AckReceived {
            StrictJson.text(requestId); Objects.requireNonNull(originalResultToken); Objects.requireNonNull(originalFrame);
            Objects.requireNonNull(originalPacket); originalPacket = originalPacket.clone();
            StrictJson.require(originalPacket.length > 0 && originalPacket.length <= RawJson.MAXIMUM_BYTES + 4, "bounded original native ACK packet required");
            outbound = Objects.requireNonNull(outbound); custody = Objects.requireNonNull(custody);
            StrictJson.require(custody.isEmpty() || outbound.isPresent(), "actual chronology requires the retained actual outbound packet");
            custody.ifPresent(value -> StrictJson.require(value.requestId().equals(requestId), "chronology belongs to another original request"));
            outbound.ifPresent(value -> StrictJson.require(value.requestId().equals(requestId), "outbound original belongs to another request"));
        }
        /** Historical ACKs retained outbound bytes without actual sampling chronology; no freshness is invented. */
        public AckReceived(String requestId, boolean nativeOk, Optional<RawJson> originalResultToken, RawJson originalFrame,
                byte[] originalPacket, Optional<OutboundPacket> outbound) {
            this(requestId, nativeOk, originalResultToken, originalFrame, originalPacket, outbound, Optional.empty());
        }
        /** Historical ACK data had no retained outbound proof; this constructor does not invent it. */
        public AckReceived(String requestId, boolean nativeOk, Optional<RawJson> originalResultToken, RawJson originalFrame, byte[] originalPacket) {
            this(requestId, nativeOk, originalResultToken, originalFrame, originalPacket, Optional.empty());
        }
        @Override public byte[] originalPacket() { return originalPacket.clone(); }
        @Override public boolean equals(Object other) { return other instanceof AckReceived value && requestId.equals(value.requestId) && nativeOk == value.nativeOk && originalResultToken.equals(value.originalResultToken) && originalFrame.equals(value.originalFrame) && java.util.Arrays.equals(originalPacket, value.originalPacket) && outbound.equals(value.outbound) && custody.equals(value.custody); }
        @Override public int hashCode() { return Objects.hash(requestId, nativeOk, originalResultToken, originalFrame, java.util.Arrays.hashCode(originalPacket), outbound, custody); }
    }
    enum ZeroDispatchStage { BEFORE_WRITE }
    record ZeroDispatchProof(ZeroDispatchStage stage, long requestBytesWritten, String reason, Optional<RawJson> diagnostic) {
        public ZeroDispatchProof {
            Objects.requireNonNull(stage); StrictJson.require(requestBytesWritten == 0, "zero written bytes required");
            StrictJson.text(reason); diagnostic = Objects.requireNonNull(diagnostic);
        }
    }
    record RejectedBeforeDispatch(String requestId, ZeroDispatchProof proof) implements DispatchOutcome {
        public RejectedBeforeDispatch { StrictJson.text(requestId); Objects.requireNonNull(proof); }
    }
    enum FailureKind { DEADLINE_EXPIRED, FRAME_BUDGET_EXHAUSTED, TRANSFER_IO, IO_FAILURE, RUNTIME_FAILURE, INTERRUPTED }
    enum FailureStage { WRITE, RESPONSE_WAIT }
    /** Actual Java diagnostic only; its original nullable/empty message is not a public exception classification. */
    record OriginalException(String javaType,String message) {
        public OriginalException { StrictJson.text(javaType); }
        public static OriginalException from(Throwable original) {
            Objects.requireNonNull(original);return new OriginalException(original.getClass().getName(),original.getMessage());
        }
    }
    record DeadlineObservation(Instant suppliedDeadline,Instant observedAt,boolean monotonicExpired) {
        public DeadlineObservation {
            Objects.requireNonNull(suppliedDeadline);Objects.requireNonNull(observedAt);
            StrictJson.require(monotonicExpired || !observedAt.isBefore(suppliedDeadline),"actual UTC or monotonic deadline expiration required");
        }
    }
    /** Source-owned dispatch failure DATA; frame limits, IO and interruption never imply a response timeout. */
    record FailureCause(FailureKind kind,FailureStage stage,Optional<OriginalException> originalException,
            Optional<OriginalException> originalCause,Optional<DeadlineObservation> deadline) {
        public FailureCause {
            Objects.requireNonNull(kind);Objects.requireNonNull(stage);Objects.requireNonNull(originalException);
            Objects.requireNonNull(originalCause);Objects.requireNonNull(deadline);
            StrictJson.require((kind==FailureKind.DEADLINE_EXPIRED)==deadline.isPresent(),"only actual deadline failures carry expiration evidence");
            StrictJson.require((kind==FailureKind.FRAME_BUDGET_EXHAUSTED)==originalException.isEmpty(),"actual exception diagnostic required except for the frame-limit branch");
            StrictJson.require(originalCause.isEmpty()||originalException.isPresent(),"nested actual cause requires its original exception");
            StrictJson.require(kind!=FailureKind.FRAME_BUDGET_EXHAUSTED||stage==FailureStage.RESPONSE_WAIT,"frame budget applies only to response waiting");
        }
    }
    record Unknown(String requestId, String reason, byte[] originalRequestPacket, Optional<RawJson> rawReturn,
            Optional<FailureCause> failureCause) implements DispatchOutcome {
        /** Historical/unclassified originals do not acquire a cause by parsing their reason. */
        public Unknown(String requestId,String reason,byte[] originalRequestPacket,Optional<RawJson> rawReturn) {
            this(requestId,reason,originalRequestPacket,rawReturn,Optional.empty());
        }
        public Unknown {
            StrictJson.text(requestId); StrictJson.text(reason); Objects.requireNonNull(originalRequestPacket);
            originalRequestPacket = originalRequestPacket.clone(); rawReturn = Objects.requireNonNull(rawReturn);failureCause=Objects.requireNonNull(failureCause);
            StrictJson.require(originalRequestPacket.length <= RawJson.MAXIMUM_BYTES + 4, "bounded original native request packet required");
        }
        @Override public byte[] originalRequestPacket() { return originalRequestPacket.clone(); }
        @Override public boolean equals(Object other) { return other instanceof Unknown value && requestId.equals(value.requestId) && reason.equals(value.reason) && rawReturn.equals(value.rawReturn) && failureCause.equals(value.failureCause) && java.util.Arrays.equals(originalRequestPacket, value.originalRequestPacket); }
        @Override public int hashCode() { return Objects.hash(requestId, reason, rawReturn, failureCause, java.util.Arrays.hashCode(originalRequestPacket)); }
    }
}

