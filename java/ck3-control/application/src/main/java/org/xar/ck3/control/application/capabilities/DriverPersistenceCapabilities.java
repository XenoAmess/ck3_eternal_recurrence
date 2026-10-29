package org.xar.ck3.control.application.capabilities;

import java.util.Objects;
import org.xar.ck3.control.application.history.DriverPersistenceStatus;

/** The existing capabilities session presentation is the sole public error outlet; no gameplay capability is added. */
public final class DriverPersistenceCapabilities {
    private DriverPersistenceCapabilities(){ }
    public static CapabilitySessionPresentation withStatus(CapabilitySessionPresentation actual,
            DriverPersistenceStatus.Snapshot sameRootStatus) {
        Objects.requireNonNull(actual);Objects.requireNonNull(sameRootStatus);
        // A diagnostic cache with no proof covering a pre-existing restore/persistence error cannot erase that error.
        var error=sameRootStatus.driverStateError().or(actual::driverStateError);
        return new CapabilitySessionPresentation(actual.driverStateRestored(),error,actual.restoreKind(),actual.bindingState(),
                actual.coldCandidateRejection(),actual.episodeTransitionError(),actual.queueDirectory(),actual.driverStatePath());
    }
    /** Overlay only the public technical error on an already-qualified result. Every capability and source field is retained. */
    public static DynamicCapabilities.Result withStatus(DynamicCapabilities.Result actual,CapabilitySessionPresentation actualBaseline,
            DriverPersistenceStatus.Snapshot sameRootStatus) {
        Objects.requireNonNull(actual);
        if(actual instanceof DynamicCapabilities.Incomplete)return actual;
        Objects.requireNonNull(actualBaseline);Objects.requireNonNull(sameRootStatus);
        var projected=(DynamicCapabilities.Projected)actual;var before=projected.snapshot();
        var session=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(before.canonical().get("native_session_control"),"native_session_control");
        for(var original:actualBaseline.original().members().entrySet())
            org.xar.ck3.control.contracts.StrictJson.require(original.getValue().equals(session.members().get(original.getKey())),"capability presentation differs from its actual baseline");
        var fields=new java.util.LinkedHashMap<>(session.members());
        var error=withStatus(actualBaseline,sameRootStatus).driverStateError();
        fields.put("driver_state_error",error.<org.xar.ck3.control.planning.opportunity.OpportunityJson.Value>map(org.xar.ck3.control.planning.opportunity.OpportunityJson.Text::new)
                .orElse(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE));
        var canonical=new java.util.LinkedHashMap<>(before.canonical().members());
        canonical.put("native_session_control",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(fields));
        var after=new DynamicCapabilities.CapabilitySnapshot(before.actionSteps(),before.bridgeCapabilities(),before.compositeActionSteps(),
                before.battleSpeedReadiness(),before.independentBattleSpeedReady(),before.snapshot(),before.waitForChange(),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(canonical),before.runtimeFacts(),before.driverStamp(),before.frameBindingSha256());
        return new DynamicCapabilities.Projected(after,projected.gaps());
    }

}
