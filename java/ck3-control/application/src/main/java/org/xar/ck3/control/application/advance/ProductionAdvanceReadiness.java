package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.Objects;
import java.time.Instant;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import java.io.IOException;
import java.io.UncheckedIOException;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.application.planning.governance.CrownRetryDue;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Life-specific history and feature consumer under the existing Driver/writer lease. */
public final class ProductionAdvanceReadiness implements AdvanceReadiness.Port {
    @FunctionalInterface public interface RuntimeFactsPort {
        RuntimeFacts inspect(ActionCommand parent, AdvanceObservationPort.Frame frame, DriverHistoryAccess.View history);
    }
    /** Enter the actual current Root lease before freezing the Driver history. */
    public interface RuntimeScope {
        <T> T current(ActionCommand parent, AdvanceObservationPort.Frame frame, Supplier<T> work);
    }
    /** A present due value is privately minted from the same-writer CROWN publication; absence applies no cached deadline. */
    public record RuntimeFacts(ObservationIdentity observed, G2Source source, String sessionId,
            DriverSnapshotFacts.Stamp historyStamp, Set<OperationKey> actionSteps, Set<String> bridgeCapabilities,
            Optional<CrownRetryDue.VerifiedDue> crownDue, boolean crownQueryEnabled, boolean crownPausedQueryEnabled,
            boolean warDailyWatchEnabled,
            ExactRef originalRuntimeEvidence) {
        public RuntimeFacts {
            Objects.requireNonNull(observed); Objects.requireNonNull(source); Objects.requireNonNull(sessionId);
            require(!sessionId.isEmpty(), "actual session identity required"); Objects.requireNonNull(historyStamp);
            actionSteps = Set.copyOf(actionSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities);
            Objects.requireNonNull(crownDue, "optional privately issued Crown due input must be explicit");
            Objects.requireNonNull(originalRuntimeEvidence);
            require(originalRuntimeEvidence.bytes() > 0, "actual runtime capability and feature evidence required");
        }
    }
    private final DriverHistoryAccess histories;
    private final RuntimeFactsPort runtime;
    private final CrownRetryDue crownDue;
    private final Supplier<ContinuityStorePort.Session> borrowedSession;
    private final RuntimeScope scope;
    public ProductionAdvanceReadiness(DriverHistoryAccess histories, RuntimeFactsPort runtime, CrownRetryDue crownDue,
            Supplier<ContinuityStorePort.Session> actualBorrowedSession, RuntimeScope actualScope) {
        this.histories = Objects.requireNonNull(histories); this.runtime = Objects.requireNonNull(runtime);
        this.crownDue = Objects.requireNonNull(crownDue); this.borrowedSession = Objects.requireNonNull(actualBorrowedSession);
        this.scope = Objects.requireNonNull(actualScope);
    }
    @Override public AdvanceReadiness.Facts inspect(ActionCommand parent, AdvanceObservationPort.Frame frame) {
        Objects.requireNonNull(parent); Objects.requireNonNull(frame);
        return scope.current(parent,frame,()->histories.withView(parent, history -> {
            RuntimeFacts actual = Objects.requireNonNull(runtime.inspect(parent, frame, history));
            require(actual.observed().equals(frame.identity()) && actual.source().equals(parent.source())
                    && actual.sessionId().equals(parent.sessionId()) && actual.historyStamp().equals(history.stamp()),
                    "life runtime features crossed the actual semantic frame or canonical history lease");
            require(history.stamp().game().equals(frame.identity().game())
                    && history.stamp().episodeRunId().equals(frame.identity().frame().episodeRunId()),
                    "life history belongs to another actual Game or episode");
            int crownBound = verifiedCrownMaximum(actual,frame,crownDue,borrowedSession.get(),parent.deadline());
            return AdvanceHistory.verifiedFacts(parent,frame,history.completeOriginalRows(),actual.actionSteps(),actual.bridgeCapabilities(),
                    crownBound,actual.warDailyWatchEnabled(),history.currentDriverEvidence());
        }));
    }
    /** Shared real consumer seam also exercised by publisher-to-advance regression fixtures. */
    public static int verifiedCrownMaximum(RuntimeFacts actual, AdvanceObservationPort.Frame frame, CrownRetryDue producer,
            ContinuityStorePort.Session actualBorrowedSession, Instant callerDeadline) {
        Objects.requireNonNull(callerDeadline);
        require(actual.observed().equals(frame.identity()) && actual.source().equals(frame.source()) && actual.sessionId().equals(frame.sessionId()),
                "Crown horizon input crossed the actual full native frame/source/session");
        if (actual.crownDue().isEmpty()) return 45;
        try {
            var due = actual.crownDue().orElseThrow(); producer.requireCurrent(actualBorrowedSession,due,callerDeadline);
            return due.horizonDays(frame.identity(),java.math.BigInteger.valueOf(45),actual.crownQueryEnabled(),actual.crownPausedQueryEnabled()).intValueExact();
        } catch (IOException failure) { throw new UncheckedIOException("actual same-writer Crown due input unavailable",failure); }
    }
}
