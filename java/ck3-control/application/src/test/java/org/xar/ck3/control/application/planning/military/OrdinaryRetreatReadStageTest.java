package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual original territorial-retreat order goes through the ordinary consumer's domain-read continuation. */
final class OrdinaryRetreatReadStageTest {
    private static final ExactRef SOURCE=new ExactRef("synthetic-retreat-read-regression",1,"a".repeat(64));
    private static final String ORIGINAL="""
            import json,pathlib,runpy,sys
            repo=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(repo/'ck3_autonomous_player'/'src'));sys.path.insert(0,str(repo/'ck3_autonomous_player'/'tests'/'unit'))
            m=runpy.run_path(str(repo/'ck3_autonomous_player/tests/unit/test_ordinary_active_retreat_v1.py'));s,c,v=m['scene']();budget=m['policy'].normal_retreat_loss_budget(s,c)
            p=m['policy'].propose_retreat(s,c,m['CAPS'],maximum_next_tick_hard_loss_raw=budget['maximum_next_tick_hard_loss_raw'],preview=v)
            keys=('source_binding','selected_owner_character_id','arguments','affected_public_cunit_ids_in_stored_order','unaffected_same_side_public_cunit_ids_in_stored_order','route_province_ids','assessment')
            print(json.dumps({'snapshot':s,'order':{k:p[k] for k in keys}},separators=(',',':')))
            """;
    @Test void pendingOriginalRunsOnlyIndependentReadThenRefreshesTheWholeRequest() throws Exception {
        Obj original=OrdinaryMilitaryOriginalProducerTest.original(ORIGINAL);var request=request(original);var order=ActiveRetreatState.order(OpportunityJson.object(original.get("order"),"original retreat order"));
        var pending=ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartOrder(order));var reads=new AtomicInteger();
        var port=new OrdinaryActiveRetreatPolicy.RetreatReadPort(){
            @Override public OrdinaryActiveRetreatPolicy.ReadResult preview(PlanningRequest r,int army,int target){throw new AssertionError("pending intent must never preview or replace its token");}
            @Override public OrdinaryActiveRetreatPolicy.ReadResult observe(PlanningRequest r){assertSame(request,r);reads.incrementAndGet();return new OrdinaryActiveRetreatPolicy.ReadCompleted(r.before(),ActiveRetreatProposal.SourceFrame.read(r.observations().snapshot()),List.of(SOURCE));}
        };
        var policy=policy(request,pending,port);var decision=policy.review(request,draft());
        var application=assertInstanceOf(MilitaryPlanningDecision.ApplicationDecision.class,decision);assertInstanceOf(OrdinaryPolicy.Refresh.class,application.decision());assertEquals(1,reads.get());
        assertFalse(application.decision() instanceof OrdinaryPolicy.Replace,"a read/domain update must not become a world-action command");
    }
    @Test void unavailableOriginalReadRetainsThePendingClaimWithoutCreatingAnOrder() throws Exception {
        Obj original=OrdinaryMilitaryOriginalProducerTest.original(ORIGINAL);var request=request(original);var order=ActiveRetreatState.order(OpportunityJson.object(original.get("order"),"order"));
        var pending=ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartOrder(order));
        var port=new OrdinaryActiveRetreatPolicy.RetreatReadPort(){
            @Override public OrdinaryActiveRetreatPolicy.ReadResult preview(PlanningRequest r,int army,int target){throw new AssertionError("must not replace pending intent");}
            @Override public OrdinaryActiveRetreatPolicy.ReadResult observe(PlanningRequest r){return new OrdinaryActiveRetreatPolicy.ReadUnavailable("original lifecycle source is unavailable");}
        };
        assertInstanceOf(MilitaryPlanningDecision.Keep.class,policy(request,pending,port).review(request,draft()));
        assertEquals(pending,ActiveRetreatState.decode(ActiveRetreatState.encode(pending)));assertTrue(pending.claimed(ActiveRetreatState.ClaimKey.of(order)));
    }
    @Test void completedReadCannotBorrowAnotherNativeGeneration() throws Exception {
        Obj original=OrdinaryMilitaryOriginalProducerTest.original(ORIGINAL);var request=request(original);var order=ActiveRetreatState.order(OpportunityJson.object(original.get("order"),"order"));
        var pending=ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartOrder(order));
        var source=ActiveRetreatProposal.SourceFrame.read(request.observations().snapshot());
        var port=new OrdinaryActiveRetreatPolicy.RetreatReadPort(){
            @Override public OrdinaryActiveRetreatPolicy.ReadResult preview(PlanningRequest r,int army,int target){throw new AssertionError();}
            @Override public OrdinaryActiveRetreatPolicy.ReadResult observe(PlanningRequest r){return new OrdinaryActiveRetreatPolicy.ReadCompleted(r.before(),new ActiveRetreatProposal.SourceFrame(source.snapshotId(),source.revision(),source.nativeRevision(),source.dateRaw(),source.episodeRunId(),source.connectionGeneration().add(java.math.BigInteger.ONE)),List.of(SOURCE));}
        };
        assertThrows(IllegalArgumentException.class,()->policy(request,pending,port).review(request,draft()));
    }
    private static OrdinaryActiveRetreatPolicy policy(PlanningRequest request,ActiveRetreatState.State original,OrdinaryActiveRetreatPolicy.RetreatReadPort port) {
        return new OrdinaryActiveRetreatPolicy(SOURCE,r->new OrdinaryActiveRetreatPolicy.KnownDomain(request.before(),original),r->{throw new AssertionError("pending intent cannot be replaced by a new model opportunity");},
                new CurrentBattleRetreatModel(),port,(r,p,d)->{throw new AssertionError("review test has no world action adapter");});
    }
    private static PlanningRequest request(Obj original){return GeneralBattleForecastIngressOriginalTest.request(obj(f("snapshot",original.get("snapshot")),f("history",new Arr(List.of())),f("steps",new Arr(List.of())),f("capabilities",new Arr(List.of()))));}
    private static OrdinaryPolicy.Draft draft(){return new OrdinaryPolicy.Draft("one-life-turn-v1","native_war_global_battle_control_progress","actual ordinary battle continuation",OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),
            obj(f("policy",text("one-life-turn-v1")),f("selected_step",text("life-advance")),f("phase",text("native_war_global_battle_control_progress")),f("reason",text("actual ordinary battle continuation"))));}
}
