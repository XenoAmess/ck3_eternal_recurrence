package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Actual held-transport request custody. Event order is assigned at real endpoint operations,
 * never from SEM publication, query identifiers, a reconstructed packet, or an ACK's business meaning.
 */
public record NativeRequestChronology(NativeObservationPort.TransportSession session, UUID custodyEpoch, String requestId,
        PacketIdentity originalRequest, PacketIdentity originalResponse, Event writeEntered,
        Event writeCompleted, Event responseReceived) {
    public record PacketIdentity(long bytes, String sha256) {
        public PacketIdentity {
            StrictJson.require(bytes > 0 && bytes <= RawJson.MAXIMUM_BYTES + 4L, "bounded original native packet identity required");
            StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "canonical original native packet SHA256 required");
        }
        public static PacketIdentity of(byte[] actualPacket) {
            Objects.requireNonNull(actualPacket);
            return new PacketIdentity(actualPacket.length, ActionCodec.sha256(actualPacket));
        }
        public boolean matches(byte[] actualPacket) {
            return actualPacket != null && bytes == actualPacket.length && sha256.equals(ActionCodec.sha256(actualPacket));
        }
    }
    public record Event(BigInteger order, Instant observedAt) {
        public Event {
            StrictJson.require(order != null && order.signum() > 0 && order.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "positive held-transport event order required");
            Objects.requireNonNull(observedAt);
        }
    }
    public NativeRequestChronology {
        Objects.requireNonNull(session); Objects.requireNonNull(custodyEpoch); StrictJson.text(requestId);
        Objects.requireNonNull(originalRequest); Objects.requireNonNull(originalResponse);
        Objects.requireNonNull(writeEntered); Objects.requireNonNull(writeCompleted); Objects.requireNonNull(responseReceived);
        StrictJson.require(writeEntered.order().compareTo(writeCompleted.order()) < 0
                && writeCompleted.order().compareTo(responseReceived.order()) < 0, "actual endpoint write/receive event order regressed");
        StrictJson.require(!writeCompleted.observedAt().isBefore(writeEntered.observedAt())
                && !responseReceived.observedAt().isBefore(writeCompleted.observedAt()),
                "actual endpoint clock regressed; do not repair or relabel observation time");
    }
    /** Packet digests bind to the bytes already retained by the sole transport/archive; no wire result is inferred. */
    public void verify(NativeActionPort.AckReceived original) {
        Objects.requireNonNull(original);
        StrictJson.require(original.requestId().equals(requestId)
                && original.custody().filter(this::equals).isPresent(), "chronology is not the original ACK's retained custody");
        var outbound = original.outbound().orElseThrow(() -> new IllegalArgumentException("actual outbound packet is absent; no chronology reconstruction allowed"));
        StrictJson.require(outbound.requestId().equals(requestId) && originalRequest.matches(outbound.originalPacket())
                && originalResponse.matches(original.originalPacket()), "chronology crossed original request/response packet bytes");
    }
    /** The dispatch's actual before guard, for every origin phase. It does not grant source/readiness authority. */
    public void verify(NativeActionPort.AckReceived original, GuardEvidence originalBeforeGuard) {
        verify(original); requireBinding(originalBeforeGuard);
        StrictJson.require(!writeEntered.observedAt().isBefore(originalBeforeGuard.observedAt())
                && !writeEntered.observedAt().isAfter(originalBeforeGuard.validUntil()), "actual write escaped its original before-guard interval");
    }
    public void verify(PlanningReadReceipt originalRead) {
        Objects.requireNonNull(originalRead);
        verify(originalRead.original(), originalRead.before().binding()); requireBinding(originalRead.after().binding());
        StrictJson.require(originalRead.requestId().equals(requestId)
                && originalRead.request().sessionId().equals(session.sessionId())
                && originalRead.request().source().machineId().equals(session.machineId())
                && originalRead.request().origin().machineId().equals(session.machineId())
                && originalRead.request().origin().game().equals(session.game()), "query chronology changed the actual request/source/Game/session");
        Instant receiptDeadline = originalRead.request().deadline();
        if (originalRead.adoption().isPresent()) {
            PlanningReadAdoption adoption = originalRead.adoption().orElseThrow(); adoption.requireReceipt(originalRead);
            receiptDeadline = adoption.currentRequest().deadline();
        }
        StrictJson.require(writeEntered.observedAt().isBefore(originalRead.request().deadline())
                && !responseReceived.observedAt().isAfter(receiptDeadline)
                && !responseReceived.observedAt().isAfter(originalRead.after().binding().validUntil()), "actual query escaped its deadline or after-guard validity");
    }
    private void requireBinding(GuardEvidence guard) {
        Objects.requireNonNull(guard);
        StrictJson.require(guard.source().machineId().equals(session.machineId()) && guard.origin().machineId().equals(session.machineId())
                && guard.origin().game().equals(session.game()) && guard.sessionId().equals(session.sessionId())
                && guard.connectionGeneration().equals(session.connectionGeneration()), "chronology crossed the actual held guard source/Game/connection/session");
    }
    private static NativeRequestChronology custody(NativeActionPort.AckReceived original) {
        StrictJson.require(original.custody().isPresent(), "actual request chronology absent; historical data cannot grant query freshness");
        NativeRequestChronology value = original.custody().orElseThrow(); value.verify(original); return value;
    }
    private static NativeRequestChronology submission(ActionState.Attempt attempt, NativeActionPort.AckReceived originalSubmission) {
        Objects.requireNonNull(attempt); Objects.requireNonNull(originalSubmission);
        StrictJson.require(originalSubmission.nativeOk() && originalSubmission.requestId().equals(attempt.requestId()),
                "successful exact original submission ACK required for ordered sampling");
        NativeRequestChronology value = custody(originalSubmission); value.verify(originalSubmission, attempt.guard());
        StrictJson.require(!value.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "original dispatch write predates its canonical submitted attempt");
        return value;
    }
    /** The independent query really entered the same endpoint after the original submission ACK was received. */
    public static void requireSampledAfter(PlanningReadReceipt actualRead, ActionState.Attempt attempt,
            NativeActionPort.AckReceived actualSubmission) {
        NativeRequestChronology query = custody(actualRead.original()); query.verify(actualRead);
        NativeRequestChronology original = submission(attempt, actualSubmission);
        StrictJson.require(!query.requestId().equals(attempt.requestId()) && query.session().equals(original.session()) && query.custodyEpoch().equals(original.custodyEpoch()),
                "sampling query is not independent in the same actual held connection");
        StrictJson.require(query.writeEntered().order().compareTo(original.responseReceived().order()) > 0
                && !query.writeEntered().observedAt().isBefore(original.responseReceived().observedAt())
                && !query.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "actual sampling query was not sent after the original submitted command and ACK");
    }
    /** Only the typed original-pending Status profile can bridge an actual same-Game reconnection. */
    public static void requireReconciledSampledAfter(PlanningReadReceipt read, ActionCommand command,
            ActionState.Attempt attempt, NativeActionPort.AckReceived actualSubmission) {
        Objects.requireNonNull(read); Objects.requireNonNull(command); Objects.requireNonNull(attempt);
        var request = read.request();
        StrictJson.require(request.origin() instanceof CommandOrigin.Reconciliation
                && read.contractId().equals("java.tactical-daily-sentinel.status.reconciliation.v1")
                && request.operation().value().equals(org.xar.ck3.control.application.advance.ClockStatusRead.STEP)
                && request.arguments().members().isEmpty() && read.adoption().isEmpty()
                && read.before().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                && read.after().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION,
                "exact typed original-pending sentinel Status reconciliation read required");
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                && command.expected().observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePrimitives.CLOCK_OBSERVER)
                && (command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.ARM_PREFIX)
                    || command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX))
                && org.xar.ck3.control.application.advance.AdvancePrimitives.supports(command.operation()),
                "reconciliation chronology belongs only to an exact original ARM or generation-bound CANCEL");
        var identity = request.origin().requireReconciliation(); var pending = identity.pending();
        StrictJson.require(pending.actionId().equals(command.actionId()) && pending.bodySha256().equals(ActionCodec.bodySha256(command))
                && pending.requestId().equals(attempt.requestId()) && pending.originalBefore().equals(command.before())
                && command.source().equals(request.source()) && command.sessionId().equals(request.sessionId())
                && command.origin().acceptsGuard(attempt.guard().origin()) && command.source().equals(attempt.guard().source())
                && command.sessionId().equals(attempt.guard().sessionId()) && command.operation().equals(attempt.guard().operation()),
                "reconciliation query changed its complete original command, Attempt or pending identity");
        identity.requireOriginalConnection(attempt.guard());
        StrictJson.require(read.before().binding().origin() instanceof CommandOrigin.Reconciliation
                && read.after().binding().origin() instanceof CommandOrigin.Reconciliation
                && identity.sameGuardFrame(read.before().binding().origin().requireReconciliation())
                && identity.sameGuardFrame(read.after().binding().origin().requireReconciliation())
                && read.before().originalBindingSha256().equals(identity.bindingSha256())
                && read.after().originalBindingSha256().equals(identity.bindingSha256()),
                "reconciliation query guards differ from its exact current factual pending identity");
        NativeRequestChronology query = custody(read.original()); query.verify(read);
        NativeRequestChronology original = submission(attempt, actualSubmission);
        StrictJson.require(!query.requestId().equals(attempt.requestId())
                && query.session().machineId().equals(original.session().machineId())
                && query.session().game().equals(original.session().game())
                && query.session().sessionId().equals(original.session().sessionId()),
                "reconciliation query is not independent in the same original physical Game/session");
        int connectionOrder = query.session().connectionGeneration().compareTo(original.session().connectionGeneration());
        StrictJson.require(connectionOrder >= 0 && (connectionOrder > 0 || query.custodyEpoch().equals(original.custodyEpoch())),
                "reconciliation query connection regressed or same connection changed custody epoch");
        if (query.custodyEpoch().equals(original.custodyEpoch()))
            StrictJson.require(query.writeEntered().order().compareTo(original.responseReceived().order()) > 0,
                    "same-custody reconciliation query predates its original ACK event");
        StrictJson.require(!query.writeEntered().observedAt().isBefore(original.responseReceived().observedAt())
                && !query.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "actual reconciliation query was not sent after the original submitted command and ACK");
    }
    /** Initial modal/source reads precede the actual write; this never equates an ACK with a state transition. */
    public static void requireBeforeSubmission(PlanningReadReceipt actualRead, ActionState.Attempt attempt,
            NativeActionPort.AckReceived actualSubmission) {
        NativeRequestChronology query = custody(actualRead.original()); query.verify(actualRead);
        NativeRequestChronology original = submission(attempt, actualSubmission);
        StrictJson.require(!query.requestId().equals(attempt.requestId()) && query.session().equals(original.session()) && query.custodyEpoch().equals(original.custodyEpoch()),
                "initial source query is not independent in the same actual held connection");
        StrictJson.require(query.responseReceived().order().compareTo(original.writeEntered().order()) < 0
                && !query.responseReceived().observedAt().isAfter(original.writeEntered().observedAt()),
                "initial source query did not precede the actual original write");
    }
}
