package org.xar.ck3.control.wave2.military.holyhirecontract;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcement.Frame;

/** Typed submission-only contract; native queue acceptance never proves employer, payment or an army. */
public final class HolyHireContract {
    private HolyHireContract() { }
    public enum Status { SUBMITTED, ALREADY_HIRED, REJECTED, UNAVAILABLE }
    public record Request(long holyOrderId, BigInteger expectedRevision) {
        public Request {
            require(holyOrderId >= 0 && holyOrderId < 0xffff_ffffL, "holy_order_id must be a full uint32 holy-order reference; zero is valid");
            require(expectedRevision != null && expectedRevision.signum() >= 0, "expected_revision must be a non-negative public revision");
        }
    }
    public record Action(Status status, Frame frame, long holyOrderId, Long actorCharacterId,
            boolean holyOrderResolved, boolean validationObservable, Boolean commandValid,
            boolean commandSubmitted, boolean verificationPending, boolean afterStateObserved,
            Long priorEmployerCharacterId, String unavailableReason, boolean priorCapturePresent) { }
    public record Acknowledgement(String version, BigInteger commandSequence, Frame frame, boolean readOnly,
            boolean accepted, String envelopeStatus, int nativeHireMode, Action action) { }
    public record QueryEnvelope(String version, String backendId, String domainKey, String status,
            BigInteger nativeRevision, BigInteger dateRaw) { }

    public static Acknowledgement validate(Acknowledgement ack, Frame snapshot, Request request) {
        Objects.requireNonNull(ack); Objects.requireNonNull(snapshot); Objects.requireNonNull(request);
        require(!ack.readOnly() && ack.commandSequence() != null && ack.commandSequence().signum() > 0
                && Objects.equals(ack.frame().nativeRevision(), snapshot.nativeRevision())
                && Objects.equals(ack.frame().dateRaw(), snapshot.dateRaw()), "native holy-order hire ACK differs from its submission frame");
        Action action = ack.action(); boolean accepted = action.status() == Status.SUBMITTED || action.status() == Status.ALREADY_HIRED;
        String expectedStatus = action.status() == Status.SUBMITTED ? "submitted_verification_pending" : action.status().name().toLowerCase(java.util.Locale.ROOT);
        require(ack.accepted() == accepted && expectedStatus.equals(ack.envelopeStatus())
                && Objects.equals(action.frame().nativeRevision(), ack.frame().nativeRevision())
                && Objects.equals(action.frame().dateRaw(), ack.frame().dateRaw())
                && action.holyOrderId() == request.holyOrderId() && ack.nativeHireMode() == 3,
                "native holy-order hire result identity/status is malformed");
        require(action.actorCharacterId() == null || Objects.equals(action.actorCharacterId(), snapshot.playedCharacterId()), "native holy-order hire actor differs from current player");
        require(!accepted || action.actorCharacterId() != null && Objects.equals(action.actorCharacterId(), snapshot.playedCharacterId()), "accepted holy-order hire lacks the current actor");
        require(action.validationObservable() == (action.commandValid() != null), "native holy-order command validation observation is malformed");
        require(action.unavailableReason() == null || !action.unavailableReason().isEmpty(), "native holy-order hire unavailable reason is malformed");
        require(!action.afterStateObserved(), "native holy-order hire ACK does not supply an independent after-state");
        require(action.priorCapturePresent() || action.status() == Status.UNAVAILABLE, "native holy-order hire lacks a current context");
        if (action.status() == Status.SUBMITTED) {
            require(action.holyOrderResolved() && action.validationObservable() && Boolean.TRUE.equals(action.commandValid())
                    && action.commandSubmitted() && action.verificationPending(), "submitted holy-order hire lacks native validation/queue acceptance");
        } else { require(!action.commandSubmitted() && !action.verificationPending(), "unsubmitted holy-order hire claims a queued mutation"); }
        require(action.status() != Status.ALREADY_HIRED || Objects.equals(action.priorEmployerCharacterId(), action.actorCharacterId()), "already hired holy-order result lacks current employer observation");
        return ack;
    }
    public static QueryEnvelope validateQuery(QueryEnvelope envelope, Frame snapshot, boolean available) {
        require(envelope.backendId().equals("ck3-" + envelope.version() + "-native-player-holy-order-context-v1")
                && envelope.domainKey().equals("player_holy_order_context_v1")
                && Objects.equals(envelope.nativeRevision(), snapshot.nativeRevision())
                && Objects.equals(envelope.dateRaw(), snapshot.dateRaw()), "native holy-order envelope differs from its queried build/frame");
        require(envelope.status().equals(available ? "observed" : "unavailable"), "native holy-order envelope lost its source status");
        return envelope;
    }
    private static void require(boolean condition, String message) { if (!condition) { throw new ProjectionDomainRejection(message); } }
}
