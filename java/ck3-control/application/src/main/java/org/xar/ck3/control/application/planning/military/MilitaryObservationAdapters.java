package org.xar.ck3.control.application.planning.military;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Concrete consumers of the sole M5 collector and complete surviving-history helpers. */
public final class MilitaryObservationAdapters implements WarStrengthRelief.MovementEvidence,SafeWarRendezvousPolicy.MovementState {
    @Override public WarStrengthRelief.EvidenceLookup activeIntent(PlanningRequest request,int army,int target){return evidence(request,WarHistorySteps.activeNativeMoveIntent(request.observations().history(),request.observations().snapshot(),army,target));}
    @Override public WarStrengthRelief.EvidenceLookup acceptedArrival(PlanningRequest request,int army,int target){return evidence(request,WarHistorySteps.acceptedNativeMoveArrival(request.observations().history(),request.observations().snapshot(),army,target));}
    @Override public WarStrengthRelief.EvidenceLookup observedErrorArrival(PlanningRequest request,int army,int target){return evidence(request,WarHistorySteps.observedNativeMoveIntent(request.observations().history(),request.observations().snapshot(),army,target,true));}
    @Override public WarStrengthRelief.EvidenceLookup deferredBackoff(PlanningRequest request,int army,int target){return evidence(request,WarHistorySteps.deferredMoveBackoff(request.observations().history(),request.observations().snapshot(),"move-army-"+army+"-to-"+target));}
    private static WarStrengthRelief.EvidenceLookup evidence(PlanningRequest request,Optional<Obj> actual){return actual.<WarStrengthRelief.EvidenceLookup>map(value->new WarStrengthRelief.EvidenceFound(request.before(),value)).orElseGet(WarStrengthRelief.EvidenceAbsent::new);}
    public static Optional<Obj> battle(PlanningRequest request){return Optional.of(BattleControlTurnState.collect(request));}
    public static OrdinaryActiveRetreatPolicy.CurrentControl controls(PlanningRequest request) {
        Obj actual=BattleControlTurnState.collect(request);
        if(!new OpportunityJson.Text("ready").equals(actual.get("status")))return new OrdinaryActiveRetreatPolicy.UnavailableControl("actual M5 battle collector status: "+actual.get("status"));
        List<Obj> frames=OpportunityJson.array(actual.get("full_frames"),"actual M5 full frames").stream().map(value->OpportunityJson.object(value,"actual normalized control")).toList();
        return new OrdinaryActiveRetreatPolicy.ReadyControl(request.before(),frames);
    }
}
