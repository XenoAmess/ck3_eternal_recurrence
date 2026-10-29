package org.xar.ck3.control.application.planning.events;

import java.io.IOException;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Persists the actual displayed fallback diagnosis when no legal ActionCommand can be created. */
@FunctionalInterface
public interface EventIncidentCapturePort {
    void captureBlocked(PlanningRequest actual, OpportunityJson.Obj retainedPlan) throws IOException;
    /** The production Root observes a real failed READ inside its original coordinator callback.
     * Pure capture adapters retain the original read behavior; no unavailable result becomes Known. */
    default <T> PlanningReadResult<T> read(PlanningReadPort reads, ReadContract<T> contract,
            PlanningReadRequest request, PlanningRequest planning) {
        return reads.read(contract, request);
    }
    static EventIncidentCapturePort unavailable() {
        return (actual, plan) -> { throw new IOException("Actual per-Game incident capture producer is not installed"); };
    }
}
