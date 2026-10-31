package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Private coordinator custody for the complete original-pending observation callback.
 * Complete/Identity/Guard constructors provide data; only Root's installed physical lease supplies this scope.
 */
public final class ActionReconciliationScope {
    private static final ThreadLocal<Held> ACTIVE = new ThreadLocal<>();
    private record Held(ActionJournal.LockedJournal locked, ContinuityStorePort.Session session,
            ActionReceipt pending, ActionState.Attempt attempt, Complete frame, ObservationProvenance provenance,
            ReconciliationIdentity identity, GuardEvidence observationGuard, String headDigest, String authorityId, Instant deadline, Clock clock) { }
    private ActionReconciliationScope() { }
    public static boolean activeFor(ActionCommand command) {
        Held held = ACTIVE.get();
        if (held == null) return false;
        try { require(held, command, null); return true; }
        catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    public static Complete requireFrame(ActionCommand command) throws IOException { return requireCurrent(command, null).frame(); }
    public static Complete requireFrame(ActionCommand command, ActionState.Attempt attempt) throws IOException { return requireCurrent(command, Objects.requireNonNull(attempt)).frame(); }
    public static ObservationProvenance requireProvenance(ActionCommand command) throws IOException { return requireCurrent(command, null).provenance(); }
    public static ObservationProvenance requireProvenance(ActionCommand command, ActionState.Attempt attempt) throws IOException { return requireCurrent(command, Objects.requireNonNull(attempt)).provenance(); }
    public static ReconciliationIdentity requireIdentity(ActionCommand command) throws IOException { return requireCurrent(command, null).identity(); }
    public static ReconciliationIdentity requireIdentity(ActionCommand command, ActionState.Attempt attempt) throws IOException { return requireCurrent(command, Objects.requireNonNull(attempt)).identity(); }
    public static GuardEvidence requireObservationGuard(ActionCommand command) throws IOException { return requireCurrent(command, null).observationGuard(); }
    public static GuardEvidence requireObservationGuard(ActionCommand command, ActionState.Attempt attempt) throws IOException { return requireCurrent(command, Objects.requireNonNull(attempt)).observationGuard(); }
    private static Held requireCurrent(ActionCommand command, ActionState.Attempt attempt) throws IOException {
        Held held = ACTIVE.get();
        StrictJson.require(held != null, "no original canonical pending reconciliation callback is active");
        require(held, command, attempt); return held;
    }
    /** Package-private: only the sole coordinator enters after its installed Root provider captures actual originals. */
    static <T> T within(ActionJournal.LockedJournal locked, ActionReceipt pending, ActionState.Attempt attempt,
            Complete frame, ObservationProvenance provenance, ReconciliationIdentity identity, GuardEvidence observationGuard, String authorityId,
            Instant deadline, Clock clock, Supplier<T> observer) {
        Objects.requireNonNull(locked); Objects.requireNonNull(pending); Objects.requireNonNull(attempt);
        Objects.requireNonNull(frame); Objects.requireNonNull(provenance); Objects.requireNonNull(identity); Objects.requireNonNull(observationGuard);
        Objects.requireNonNull(deadline); Objects.requireNonNull(clock); Objects.requireNonNull(observer);
        StrictJson.require(ACTIVE.get() == null, "reconciliation cannot recursively replace the original physical observation");
        Held held = new Held(locked, locked.writerSession(), pending, attempt, frame, provenance, identity, observationGuard,
                locked.head().digest(), StrictJson.text(authorityId), deadline, clock);
        try {
            require(held, pending.command(), attempt); ACTIVE.set(held);
            try { T result = observer.get(); require(held, pending.command(), attempt); return result; }
            finally { ACTIVE.remove(); }
        } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }
    private static void require(Held held, ActionCommand command, ActionState.Attempt expectedAttempt) throws IOException {
        Objects.requireNonNull(command);
        StrictJson.require(held.locked().writerSession() == held.session(), "reconciliation escaped its original writer Session");
        var actualHead = held.session().head();
        StrictJson.require(actualHead.digest().equals(held.headDigest())
                && held.locked().head().digest().equals(held.headDigest()), "reconciliation callback changed its canonical writer head");
        ActionReceipt actual = held.locked().find(held.pending().command().actionId()).orElseThrow(
                () -> new IllegalArgumentException("original pending disappeared from the canonical writer"));
        StrictJson.require(actual.equals(held.pending()) && !actual.settled()
                && (actual.state() instanceof ActionState.Submitting || actual.state() instanceof ActionState.AckReceived || actual.state() instanceof ActionState.Unknown),
                "reconciliation requires the exact current unresolved primitive receipt");
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                && command.actionId().equals(actual.command().actionId())
                && ActionCodec.bodySha256(command).equals(actual.bodySha256())
                && Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(actual.command())),
                "reconciliation command differs from its complete canonical original body");
        ActionState.Attempt actualAttempt = ActionTransitions.attempt(actual.state()).orElseThrow();
        StrictJson.require(actualAttempt.equals(held.attempt())
                && (expectedAttempt == null || expectedAttempt.equals(actualAttempt)), "reconciliation borrowed another primitive Attempt");
        StrictJson.require(ActionScope.currentActionId().filter(command.actionId()::equals).isPresent()
                && ActionCommandScope.current().filter(value -> Arrays.equals(ActionCodec.encodeCommand(value), ActionCodec.encodeCommand(command))).isPresent(),
                "reconciliation data escaped its actual coordinator command/thread scope");
        ReconciliationIdentity identity = held.identity(); Complete frame = held.frame(); ObservationProvenance provenance = held.provenance(); GuardEvidence guard = held.observationGuard();
        StrictJson.require(identity.pending().actionId().equals(command.actionId())
                && identity.pending().bodySha256().equals(actual.bodySha256())
                && identity.pending().requestId().equals(actualAttempt.requestId())
                && identity.pending().originalBefore().equals(command.before()), "actual reconciliation identity differs from the canonical pending binding");
        StrictJson.require(frame.identity().equals(identity.factual()) && frame.source().equals(identity.source())
                && frame.sessionId().equals(identity.sessionId()) && frame.connectionGeneration().equals(identity.connectionGeneration())
                && frame.originalEvidence().equals(identity.nativeEvidence()) && frame.observedAt().equals(identity.observedAt()),
                "actual reconciliation Complete and identity do not share original source/Native/Driver data");
        provenance.validate(frame.identity(), frame.originalEvidence());
        StrictJson.require(identity.source().equals(command.source()) && identity.sessionId().equals(command.sessionId()),
                "reconciliation crossed the original source/session");
        identity.requireOriginalConnection(actualAttempt.guard());
        StrictJson.require(guard.origin() instanceof CommandOrigin.Reconciliation
                && guard.origin().requireReconciliation().equals(identity) && guard.operation().equals(command.operation())
                && guard.source().equals(command.source()) && guard.sessionId().equals(command.sessionId())
                && guard.connectionGeneration().equals(identity.connectionGeneration())
                && guard.nativeEvidence().equals(identity.nativeEvidence()) && guard.capabilityEvidence().equals(identity.capabilityEvidence())
                && guard.authorityId().equals(held.authorityId()) && !guard.supportingEvidence().isEmpty(),
                "actual observation guard does not retain its dedicated pending/source/writer-point custody");
        StrictJson.require(held.clock().instant().isBefore(held.deadline())
                && held.clock().instant().isBefore(guard.validUntil()), "original-pending observation callback expired");
        // Raw cached SEM time remains unchanged. Fresh query sampling is independently proved by actual wire chronology.
    }
}

