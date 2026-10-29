package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The loop invokes this actual completion port; the planner never becomes another ledger writer. */
public final class GovernancePlanCompletion implements OrdinaryPlanCompletion {
    @FunctionalInterface public interface EvidencePort {
        /** Resolve the complete original read closure actually used by these ordered no-action domain producers. */
        List<ExactRef> originals(PlanningRequest original, PlanningResult planned, GovernanceCadencePublication.Plan plan) throws IOException;
    }
    private final Supplier<ContinuityStorePort.Session> borrowedSession;
    private final GovernanceBorrowedSession.Authority authority;
    private final GovernanceCadencePublication publisher;
    private final EvidencePort evidence;
    public GovernancePlanCompletion(Supplier<ContinuityStorePort.Session> borrowedSession, GovernanceBorrowedSession.Authority authority,
            GovernanceCadencePublication publisher, EvidencePort evidence) {
        this.borrowedSession = Objects.requireNonNull(borrowedSession); this.authority = Objects.requireNonNull(authority);
        this.publisher = Objects.requireNonNull(publisher); this.evidence = Objects.requireNonNull(evidence);
    }
    @Override public PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult planned) {
        Objects.requireNonNull(original); Objects.requireNonNull(planned);
        try {
            StrictJson.require(planned.trace().before().equals(original.before()), "cadence completion crossed its original planning frame");
            if (planned.trace().finalPlan().isEmpty()) return new Unchanged("no complete domain plan was published by the actual planner");
            var retained = GovernanceCadencePublication.fromDetail(planned.trace().finalPlan().orElseThrow().detail());
            if (retained.isEmpty()) return new Unchanged("actual plan has no completed no-action cadence reads");
            var plan = retained.orElseThrow();
            StrictJson.require(plan.observed().equals(original.before()) && plan.source().equals(original.source())
                    && plan.sessionId().equals(original.sessionId()), "actual cadence plan source/session differs");
            var session = borrowedSession.get();
            if (session == null) return new Blocked("Root did not lend its live original writer Session", List.of());
            authority.requireSession(session);
            var predecessor = session.head(); var result = publisher.publish(session, plan, evidence.originals(original, planned, plan));
            authority.requireSession(session);
            if (result instanceof GovernanceCadencePublication.Changed changed) return new Published(predecessor, changed.committed());
            return new Unchanged("actual same-frame cadence reducer is already current");
        } catch (IOException | IllegalArgumentException | IllegalStateException unavailable) {
            return new Blocked("actual cadence plan publication unavailable: " + unavailable.getMessage(), List.of());
        }
    }
    @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
        Objects.requireNonNull(actual);
        // Completed no-action reads are published before dispatch. Actual-action cadence/reset remains the owning domain's real receipt reducer.
        return new Unchanged(actual.settled() ? "actual action receipt remains with its owning domain reducer"
                : "original pending/UNKNOWN action preserved without no-action cadence credit");
    }
}
