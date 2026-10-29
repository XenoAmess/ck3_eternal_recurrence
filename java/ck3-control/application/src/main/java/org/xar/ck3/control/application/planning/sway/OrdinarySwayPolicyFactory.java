package org.xar.ck3.control.application.planning.sway;

import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual ORDINARY_SWAY instance construction, registered once by the sole composition root. */
public final class OrdinarySwayPolicyFactory {
    private OrdinarySwayPolicyFactory() { }

    public static OrdinarySwayPolicy create(ExactRef policySource, PlanningReadPort reads,
            ReadContract<Obj> installedSharedRoot, OrdinarySwayReadSource.InputsPort inputs,
            OrdinarySwayReadSource.CapabilitiesPort capabilities,
            OrdinarySwayPolicy.CompositePostcondition nativePostcondition) {
        return create(policySource,reads,SwaySharedRoot.original(installedSharedRoot),inputs,capabilities,nativePostcondition);
    }
    public static OrdinarySwayPolicy create(ExactRef policySource,PlanningReadPort reads,
            SwaySharedRoot installedSharedRoot,OrdinarySwayReadSource.InputsPort inputs,
            OrdinarySwayReadSource.CapabilitiesPort capabilities,
            OrdinarySwayPolicy.CompositePostcondition nativePostcondition) {
        return new OrdinarySwayPolicy(policySource,
                new OrdinarySwayReadSource(reads, installedSharedRoot, inputs, capabilities), nativePostcondition);
    }
}
