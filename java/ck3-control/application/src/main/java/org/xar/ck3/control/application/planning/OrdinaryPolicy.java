package org.xar.ck3.control.application.planning;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** One real Java domain producer in the ordinary application call sequence. */
public interface OrdinaryPolicy {
    PlanningStage stage();
    ExactRef implementationSource();
    Decision evaluate(PlanningRequest request, Draft previous);

    enum Purpose { READ_ONLY, WORLD_ACTION, OPTIONAL_CONSTRUCTION, DATE_ADVANCE }
    enum Kind { ORDINARY, FOREGROUND, OPENING_FOCUS, MATERIAL_RECEIPT, WAR_EXIT, TERMINAL }
    record Draft(String policy, String phase, String reason, Kind kind, Optional<ActionCommand> command, Purpose purpose,
            Optional<Domain> domain, OpportunityJson.Obj detail) {
        public Draft {
            StrictJson.text(policy); StrictJson.text(phase); StrictJson.text(reason);
            Objects.requireNonNull(kind); Objects.requireNonNull(command); Objects.requireNonNull(purpose);
            Objects.requireNonNull(domain); Objects.requireNonNull(detail);
            DriverJson.object(DriverJson.encode(detail), DriverJson.MAX_NATIVE_BYTES);
        }
        public static Draft empty() { return new Draft("ordinary-java-planner-v1", "initial", "no domain producer has run", Kind.ORDINARY, Optional.empty(), Purpose.READ_ONLY, Optional.empty(), new OpportunityJson.Obj(java.util.Map.of())); }
    }
    sealed interface Decision permits Keep, Replace, NotApplicable, Wait, Stop, Refresh, Defer, ReconcileExisting, Annotate { String reason(); }
    record Keep(String reason) implements Decision { public Keep { StrictJson.text(reason); } }
    record NotApplicable(String reason) implements Decision { public NotApplicable { StrictJson.text(reason); } }
    record Replace(Draft draft, String reason) implements Decision { public Replace { Objects.requireNonNull(draft); StrictJson.text(reason); } }
    record Wait(String reason) implements Decision { public Wait { StrictJson.text(reason); } }
    /** Successful read requires a real observation refresh; no world time or world action is authorized. */
    record Refresh(String reason) implements Decision { public Refresh { StrictJson.text(reason); } }
    /** Missing optional input is recorded without clearing an independently legal war action. */
    record Defer(String reason, OpportunityJson.Obj evidence) implements Decision {
        public Defer { StrictJson.text(reason); Objects.requireNonNull(evidence); }
    }
    /** Reconcile the already durable original command; never manufacture a new body on the current frame. */
    record ReconcileExisting(String actionId, OpportunityJson.Obj detail, String reason) implements Decision {
        public ReconcileExisting {
            StrictJson.require(actionId != null && actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "bounded existing action identity required");
            Objects.requireNonNull(detail); StrictJson.text(reason);
        }
    }
    /** Preserve the exact chosen action while retaining independently collected annotations. */
    record Annotate(Draft retained, String reason) implements Decision {
        public Annotate { Objects.requireNonNull(retained); StrictJson.text(reason); }
    }
    record Stop(PlanningResult.StopReason stopReason, String reason) implements Decision {
        public Stop { Objects.requireNonNull(stopReason); StrictJson.text(reason); }
    }
}
