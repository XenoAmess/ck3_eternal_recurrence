package org.xar.ck3.control.application.driver;

import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Test-only access to the actual package-private source replay; no alternate implementation. */
public final class DriverFactionReplayAssertions {
    private DriverFactionReplayAssertions() { }
    public static void requireOriginalSources(OpportunityJson.Obj auxiliary,ActionPorts.OutcomeArchive originals) {
        DriverSemanticReadState.replaySources(auxiliary,originals);
    }
}
