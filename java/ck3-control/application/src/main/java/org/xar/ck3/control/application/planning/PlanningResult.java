package org.xar.ck3.control.application.planning;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

public sealed interface PlanningResult permits PlanningResult.ActionSelected, PlanningResult.ReadOnlyWait,
        PlanningResult.Stopped, PlanningResult.IncompleteMigration, PlanningResult.RefreshRequired, PlanningResult.ExistingActionReconciliation {
    PlanTrace trace();

    record ActionSelected(ActionCommand command, PlanTrace trace) implements PlanningResult {
        public ActionSelected {
            Objects.requireNonNull(command); Objects.requireNonNull(trace);
            StrictJson.require(command.before().equals(trace.before()) && trace.finalPlan().filter(plan -> plan.command().equals(java.util.Optional.of(command))).isPresent(),
                    "selected action crossed the observed frame or detached final plan");
        }
    }
    record ReadOnlyWait(ObservationIdentity before, String reason, PlanTrace trace) implements PlanningResult {
        public ReadOnlyWait { Objects.requireNonNull(before); StrictJson.text(reason); Objects.requireNonNull(trace); StrictJson.require(before.equals(trace.before()), "wait trace frame differs"); }
    }
    record RefreshRequired(ObservationIdentity before, String reason, PlanTrace trace) implements PlanningResult {
        public RefreshRequired { Objects.requireNonNull(before); StrictJson.text(reason); Objects.requireNonNull(trace); StrictJson.require(before.equals(trace.before()), "refresh trace frame differs"); }
    }
    record ExistingActionReconciliation(String actionId, ObservationIdentity before,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj detail, PlanTrace trace) implements PlanningResult {
        public ExistingActionReconciliation {
            StrictJson.require(actionId != null && actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "bounded existing action identity required");
            Objects.requireNonNull(before); Objects.requireNonNull(detail); Objects.requireNonNull(trace);
            StrictJson.require(before.equals(trace.before()), "reconciliation planning frame differs");
        }
    }
    record Stopped(ObservationIdentity before, StopReason reason, String detail, PlanTrace trace) implements PlanningResult {
        public Stopped { Objects.requireNonNull(before); Objects.requireNonNull(reason); StrictJson.text(detail); Objects.requireNonNull(trace); StrictJson.require(before.equals(trace.before()), "stop trace frame differs"); }
    }
    record IncompleteMigration(ObservationIdentity before, List<PlanningStage> missingStages, PlanTrace trace) implements PlanningResult {
        public IncompleteMigration {
            Objects.requireNonNull(before); missingStages = List.copyOf(missingStages); Objects.requireNonNull(trace);
            StrictJson.require(!missingStages.isEmpty() && before.equals(trace.before()), "incomplete migration must identify actual missing production stages");
        }
    }
    enum StopReason {
        TERMINAL_COMPLETE, NATURAL_SUCCESSION_REQUIRED, UNKNOWN_ACTION_UNRESOLVED, INVALID_FRAME,
        POLICY_BLOCKED, UNSUPPORTED_ACTION, DEADLINE, INCOMPLETE_PRODUCTION_CHAIN
    }
}
