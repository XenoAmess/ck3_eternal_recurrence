package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** The sole ordinary planner projection enters the sole public call decoder; no Native action is submitted. */
public final class ArmyOrdinaryPlannerCalls {
    private ArmyOrdinaryPlannerCalls() { }
    public static boolean supports(OperationKey operation) { return ArmyOrdinaryPlannerSelection.supports(operation); }
    public static ArmyCalls.Call decode(OperationKey operation, Obj selectedArguments, BigInteger actualRevision) {
        var selection = ArmyOrdinaryPlannerSelection.decode(operation, selectedArguments, actualRevision);
        var call = ArmyCallCodec.decode(PublicMethod.valueOf(selection.kind().name()), selection.publicArguments());
        call.revision().requireCurrent(actualRevision);
        return call;
    }
    /** Preserve the caller's Root action identity; it is never regenerated or copied into Native arguments here. */
    public static ArmyCalls.Call decode(OperationKey operation, Obj selectedArguments, BigInteger actualRevision, String originalActionId) {
        StrictJson.text(originalActionId); return decode(operation, selectedArguments, actualRevision);
    }
}
