package org.xar.ck3.control.application.planning;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Evidence of which production policies ran; never a native/action acceptance receipt. */
public record PlanTrace(ObservationIdentity before, List<StageVisit> visits, java.util.Optional<OrdinaryPolicy.Draft> finalPlan) {
    public PlanTrace { Objects.requireNonNull(before); visits = List.copyOf(visits); Objects.requireNonNull(finalPlan); }

    public enum Outcome { KEPT, REPLACED, BLOCKED, TERMINAL, NOT_APPLICABLE, MISSING_PRODUCER, DEFERRED_OPTIONAL_SPEND, DEFERRED_INPUT, REFRESH_REQUIRED }
    public record StageVisit(PlanningStage stage, Outcome outcome, String reason, java.util.Optional<ExactRef> source,
            java.util.Optional<org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj> evidence) {
        public StageVisit {
            Objects.requireNonNull(stage); Objects.requireNonNull(outcome); StrictJson.text(reason); Objects.requireNonNull(source); Objects.requireNonNull(evidence);
        }
    }
}
