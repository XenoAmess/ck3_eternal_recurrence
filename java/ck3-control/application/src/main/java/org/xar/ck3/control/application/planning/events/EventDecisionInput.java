package org.xar.ck3.control.application.planning.events;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Pure event-decision DATA. This input has no read lease, Prepared command, ordinary Ready,
 * private token or Native qualification. Each real caller retains its own original source custody. */
public record EventDecisionInput(ObservationIdentity before,G2Source source,String sessionId,
        OpportunityJson.Obj snapshot,List<OpportunityJson.Obj> history,Set<OperationKey> actionSteps,
        Set<String> bridgeCapabilities,Instant deadline,RetainedJson.ObjectValue currentWindow,Optional<String> focus) {
    public EventDecisionInput {
        Objects.requireNonNull(before);Objects.requireNonNull(source);Objects.requireNonNull(sessionId);
        Objects.requireNonNull(snapshot);history=List.copyOf(history);actionSteps=Set.copyOf(actionSteps);
        bridgeCapabilities=Set.copyOf(bridgeCapabilities);Objects.requireNonNull(deadline);Objects.requireNonNull(currentWindow);Objects.requireNonNull(focus);
        StrictJson.require(before.machineId().equals(source.machineId()),"event decision source machine differs from its observed DATA");
    }
    /** Maps only an existing genuine ordinary request after its original window validator succeeded. */
    public static EventDecisionInput ordinary(PlanningRequest original,RetainedJson.ObjectValue currentWindow) {
        Objects.requireNonNull(original);return new EventDecisionInput(original.before(),original.source(),original.sessionId(),
                original.observations().snapshot(),original.observations().history(),original.observations().actionSteps(),
                original.observations().bridgeCapabilities(),original.deadline(),currentWindow,OrdinaryCorePolicy.focus(original));
    }
    public boolean paused(){return snapshot.get("paused") instanceof OpportunityJson.Bool value&&value.value();}
}
