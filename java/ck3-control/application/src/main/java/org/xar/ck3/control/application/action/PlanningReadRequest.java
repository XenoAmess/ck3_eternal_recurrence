package org.xar.ck3.control.application.action;

import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One collector contract. Read permission cannot authorize clipboard, foreground or other mutation. */
public record PlanningReadRequest(CommandOrigin origin, G2Source source, String sessionId,
        OperationKey operation, OpportunityJson.Obj arguments, Instant deadline) {
    public PlanningReadRequest {
        Objects.requireNonNull(origin); Objects.requireNonNull(source); StrictJson.text(sessionId);
        Objects.requireNonNull(operation); Objects.requireNonNull(arguments); Objects.requireNonNull(deadline);
        StrictJson.require(origin.machineId().equals(source.machineId()), "read source machine drift");
        if (origin instanceof CommandOrigin.Frontend frontend)
            StrictJson.require(frontend.identity().frontendSessionId().equals(sessionId), "frontend read session drift");
        if (origin instanceof CommandOrigin.Reconciliation reconciliation)
            StrictJson.require(reconciliation.identity().source().equals(source) && reconciliation.identity().sessionId().equals(sessionId), "reconciliation read changed its canonical pending source/session");
        if (origin instanceof CommandOrigin.LifecycleTerminal lifecycle)
            StrictJson.require(lifecycle.identity().sessionId().equals(sessionId), "lifecycle read session drift");
        if (origin instanceof CommandOrigin.PhysicalStatusOnly physical)
            StrictJson.require(physical.identity().source().equals(source) && physical.identity().sessionId().equals(sessionId)
                    && operation.value().equals(PhysicalStatusIdentity.OPERATION) && arguments.members().isEmpty(),
                    "physical status request changed the finite read source/session/operation or empty arguments");
        OpportunityJson.parse(OpportunityJson.encode(arguments));
    }
    public PlanningReadRequest(ObservationIdentity before, G2Source source, String sessionId,
            OperationKey operation, OpportunityJson.Obj arguments, Instant deadline) {
        this(new CommandOrigin.Gameplay(before), source, sessionId, operation, arguments, deadline);
    }
    public static PlanningReadRequest newReconciliation(ReconciliationIdentity identity, OperationKey operation,
            OpportunityJson.Obj arguments, Instant deadline) {
        Objects.requireNonNull(identity);
        return new PlanningReadRequest(new CommandOrigin.Reconciliation(identity), identity.source(), identity.sessionId(), operation, arguments, deadline);
    }
    public static PlanningReadRequest newStatusOnly(PhysicalStatusIdentity identity, OperationKey operation,
            OpportunityJson.Obj arguments, Instant deadline) {
        Objects.requireNonNull(identity);
        return new PlanningReadRequest(new CommandOrigin.PhysicalStatusOnly(identity), identity.source(), identity.sessionId(), operation, arguments, deadline);
    }
    public ObservationIdentity reconciliationBefore() { return origin.requireReconciliation().factual(); }
    public ObservationIdentity before() { return origin.requireGameplay(); }
}

