package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m5.M5FrameDispatcher;
import org.xar.ck3.control.g2.m5.M5ReservationCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;

/** Actual strict intake -> actual frame dispatcher; retains the original analytic-only reservation contract. */
public final class M5FormalCollection {
    private M5FormalCollection() {}
    public record Collected(Obj originalSources,Obj originalIntake,M5FrameDispatcher.Dispatch dispatch,Obj receipt) {
        public Collected {Objects.requireNonNull(originalSources);Objects.requireNonNull(originalIntake);Objects.requireNonNull(dispatch);Objects.requireNonNull(receipt);}
    }
    public static Collected collect(G2Source provenance,Obj snapshot,Obj sources) {
        Obj intake=OpportunityJson.object(OpportunityJson.parse(FormalProposalIntake.collect(OpportunityJson.encode(
                obj(f("schema",text(FormalProposalIntake.REQUEST_SCHEMA)),f("snapshot",snapshot),f("sources",sources))))),"complete original formal intake");
        Obj selector=OpportunityJson.object(intake.get("selector_request"),"actual original selector request");
        M5FrameDispatcher owner=new M5FrameDispatcher(provenance,snapshot,OpportunityJson.object(sources.get("existing_commitments"),"actual commitments"));
        M5FrameDispatcher.Dispatch selected=owner.chooseObserved(provenance,selector);
        Obj dispatch=OpportunityJson.object(OpportunityJson.parse(M5ReservationCodec.encode(selected)),"actual frame reservation");
        Obj result=obj(f("schema",text("xar.ck3.m5-formal-proposal-collection.v1")),f("policy",text("g2-m5-formal-query-only-collector-v1")),
                f("status",text(selected.selectedCandidateId().isPresent()?"reserved_analytic":"no_complete_feasible_proposal")),
                f("read_only",new Bool(true)),f("advertised",new Bool(false)),f("frame",intake.get("frame")),
                f("collected_domains",intake.get("collected_domains")),f("collected_candidate_ids",intake.get("collected_candidate_ids")),
                f("dispatch",dispatch),f("selected_step",Nil.INSTANCE),f("formal_action_ready",new Bool(false)));
        for(String field:List.of("war_cash_resource","producer_family_status","producer_faction_status","incomplete_domains"))
            if(intake.members().containsKey(field))result=put(result,field,intake.get(field));
        return new Collected(sources,intake,selected,result);
    }
    /** Reuse the same original family adapter, including full betrothal/marriage proof, to identify a selected plan. */
    public static String familyIdentity(Obj snapshot,Obj familyPlan) {
        return FormalProposalIntake.familyIdentity(snapshot,familyPlan);
    }
}
