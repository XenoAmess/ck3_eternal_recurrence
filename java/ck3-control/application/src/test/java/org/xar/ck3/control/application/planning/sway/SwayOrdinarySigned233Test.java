package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire;

/** New finite software inputs only: no Root issuer, native read, actual Start or ledger write. */
public final class SwayOrdinarySigned233Test {
    private static final BigInteger DATE=BigInteger.valueOf(24000), REV=BigInteger.valueOf(5);
    private static final ExactRef PIN=new ExactRef("fixture:software233-source",1,"1".repeat(64));
    private static int scenes,checks;
    private SwayOrdinarySigned233Test() { }
    public static void main(String[] args) {
        run("zeroActorSignedFrontier",SwayOrdinarySigned233Test::zeroActorSignedFrontier);
        run("signedPendingWithoutRoot",SwayOrdinarySigned233Test::signedPendingWithoutRoot);
        run("appliedStateSignedRoundTrip",SwayOrdinarySigned233Test::appliedStateSignedRoundTrip);
        run("resolvedHighSchemeWire",SwayOrdinarySigned233Test::resolvedHighSchemeWire);
        run("invalidCharactersRemainUnavailable",SwayOrdinarySigned233Test::invalidCharactersRemainUnavailable);
        run("actualPolicyProjectionStageRestore",SwayOrdinarySigned233Test::actualPolicyProjectionStageRestore);
        run("positiveCadenceAndReaderGuard",SwayOrdinarySigned233Test::positiveCadenceAndReaderGuard);
        run("pendingNotDuePreservesIdentity",SwayOrdinarySigned233Test::pendingNotDuePreservesIdentity);
        System.out.println("PASS scenes="+scenes+" checks="+checks+" softwareOnly=true naturalSway=false privateRootAuthority=false Native=false Game=false replayOriginalArchiveDynamicCoverage=false");
    }
    private static void zeroActorSignedFrontier() {
        var decision=plan(request(0,Optional.of(root(0,List.of((long)Integer.MIN_VALUE,-2L,7L))),Ledger.empty(),Optional.empty(),DATE));
        equal(decision.job(),Optional.of(Job.QUERY_SELECTED_TARGET)); equal(decision.targetCharacterId(),Optional.of((long)Integer.MIN_VALUE));
        equal(decision.state().orElseThrow().frontierMembership(),Optional.of(List.of((long)Integer.MIN_VALUE,-2L,7L)));
        check(!decision.submitAllowed()&&!decision.nativeAiRankClaimed()&&!decision.terminalOrUsefulGainClaimed());
    }
    private static void signedPendingWithoutRoot() {
        var held=new Pending("sway-held233",-2,0);
        var decision=plan(request(-2,Optional.empty(),new Ledger(Optional.of(held),Optional.empty()),Optional.empty(),DATE));
        equal(decision.job(),Optional.of(Job.RECONCILE_PENDING)); equal(decision.targetCharacterId(),Optional.of(0L));
        equal(decision.actionId(),Optional.of(held.actionId())); equal(decision.reason(),Reason.EXISTING_PENDING_READ_ONLY);
    }
    private static void appliedStateSignedRoundTrip() {
        var state=complete(State.initial(0),DATE,Job.QUERY_SELECTED_TARGET,Outcome.APPLIED,Optional.of(-2L),Optional.of("sway-new233"));
        equal(state.lastTargetCharacterId(),Optional.of(-2L));equal(state.nextCheckDateRaw(),Optional.of(BigInteger.valueOf(24720)));
        equal(state.noOperationCount(),0);equal(SwayScheduleWire.decodeState(SwayScheduleWire.encodeState(state)),state);
    }
    private static void resolvedHighSchemeWire() {
        ObjectNode row=wire((long)Integer.MIN_VALUE); ObjectNode resolved=((ObjectNode)row.get("ledger")).putObject("resolved");
        ObjectNode identity=resolved.putObject("identity");identity.put("action_id","sway-known233").put("actor_character_id",Integer.MIN_VALUE)
                .put("target_character_id",0).put("scheme_instance_id",0x80000000L).put("scheme_instance_generation",128);
        resolved.put("applied",true).put("postcondition_verified",true).put("terminal_observed",false).putNull("reuse_gap");
        var decoded=SwayScheduleWire.decode(StrictJson.canonical(row));var held=decoded.ledger().resolved().orElseThrow().identity();
        equal(held,new Identity("sway-known233",Integer.MIN_VALUE,0,0x80000000L,128));
        var decision=plan(decoded);equal(decision.job(),Optional.of(Job.OBSERVE_APPLIED));equal(decision.targetCharacterId(),Optional.of(0L));
        identity.put("scheme_instance_id",0xffffffffL);reject(()->SwayScheduleWire.decode(StrictJson.canonical(row)));
    }
    private static void invalidCharactersRemainUnavailable() {
        for(long bad:new long[]{-1,2147483648L,4294967294L,-2147483649L}) {
            reject(()->State.initial(bad));reject(()->new Pending("sway-bad233",1,bad));
            var decision=plan(request(1,Optional.of(root(1,List.of(bad))),Ledger.empty(),Optional.empty(),DATE));
            equal(decision.reason(),Reason.FRONTIER_UNAVAILABLE);check(decision.job().isEmpty());
            ObjectNode row=wire(bad);reject(()->SwayScheduleWire.decode(StrictJson.canonical(row)));
        }
        var self=plan(request(0,Optional.of(root(0,List.of(0L))),Ledger.empty(),Optional.empty(),DATE));equal(self.reason(),Reason.FRONTIER_UNAVAILABLE);
        var duplicate=plan(request(0,Optional.of(root(0,List.of(-2L,-2L))),Ledger.empty(),Optional.empty(),DATE));equal(duplicate.reason(),Reason.FRONTIER_UNAVAILABLE);
    }
    private static void actualPolicyProjectionStageRestore() {
        PlanningRequest request=planning(0);ObjectNode root=StrictJson.object();ObjectNode context=root.putObject("campaign_root_context");
        context.put("status","available").put("player_character_id",0).put("player_character_alive",true).put("snapshot_revision",5).put("date_raw",DATE);
        context.putArray("direct_landed_vassal_character_ids").add(-2).add(7);
        var view=OrdinarySwayPolicy.project(request.before(),OpportunityJson.parse(StrictJson.canonical(root)),capabilities(),()->Optional.of(new OrdinarySwayService.Inputs(Ledger.empty(),Optional.empty())));
        equal(view.root().orElseThrow().actorCharacterId(),0L);equal(view.root().orElseThrow().frontier().orElseThrow(),List.of(-2L,7L));
        var policy=new OrdinarySwayPolicy(PIN,ignored->view,SwayOrdinarySigned233Test::expected);
        var evaluated=policy.evaluate(request,previous(request));check(evaluated instanceof OrdinaryPolicy.Replace);
        ActionCommand command=((OrdinaryPolicy.Replace)evaluated).draft().command().orElseThrow();var restored=OrdinarySwayPolicy.restoreStaged(command);
        equal(restored.frame().actorCharacterId(),0L);equal(restored.decision().targetCharacterId(),Optional.of(-2L));
        equal(command.claims().characterIds(),Set.of(BigInteger.ZERO,BigInteger.valueOf(-2)));check(!restored.decision().submitAllowed());
        ObjectNode args=(ObjectNode)StrictJson.parse(OpportunityJson.encode(command.arguments()));
        ((ObjectNode)args.get("decision")).put("target_character_id",2147483648L);
        reject(()->OrdinarySwayPolicy.restoreStaged(new ActionCommand(command.actionId(),command.before(),command.source(),command.sessionId(),command.operation(),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"mutated233"),command.expected(),command.claims(),command.deadline())));
    }
    private static void positiveCadenceAndReaderGuard() {
        var decision=plan(request(1,Optional.of(root(1,List.of(2L,3L))),Ledger.empty(),Optional.empty(),DATE));equal(decision.targetCharacterId(),Optional.of(2L));
        var first=complete(State.initial(1),DATE,Job.QUERY_SELECTED_TARGET,Outcome.NO_OPERATION,Optional.of(2L),Optional.empty());equal(first.nextCheckDateRaw(),Optional.of(DATE.add(RAW_PER_DAY)));
        var second=complete(first,DATE.add(RAW_PER_DAY),Job.QUERY_SELECTED_TARGET,Outcome.NO_OPERATION,Optional.of(3L),Optional.empty());equal(second.nextCheckDateRaw(),Optional.of(DATE.add(RAW_PER_DAY).add(MONTH_RAW)));equal(second.noOperationCount(),2);
        AtomicInteger loads=new AtomicInteger();var captured=new OrdinarySwayService.Captured(source(),new OrdinarySwayService.Wrapper("native:5",BigInteger.valueOf(17)),Step.LIFE_ADVANCE,Optional.of(frame(0,DATE)),Optional.of(root(0,List.of(-2L))),new OrdinarySwayService.Capabilities(false,false,false));
        var result=new OrdinarySwayService().stage(captured,()->{loads.incrementAndGet();return Optional.of(new OrdinarySwayService.Inputs(Ledger.empty(),Optional.empty()));});
        equal(result.reason(),OrdinarySwayService.StageReason.READERS_DISABLED);equal(loads.get(),0);
    }
    private static void pendingNotDuePreservesIdentity() {
        var state=complete(State.initial(-2),DATE,Job.RECONCILE_PENDING,Outcome.PENDING,Optional.of(0L),Optional.of("sway-held233"));
        var decision=plan(request(-2,Optional.empty(),new Ledger(Optional.of(new Pending("sway-held233",-2,0)),Optional.empty()),Optional.of(state),DATE.add(BigInteger.ONE)));
        equal(decision.reason(),Reason.PENDING_READ_NOT_DUE);check(decision.job().isEmpty());equal(decision.state(),Optional.of(state));
    }
    private static Request request(long actor,Optional<Root> root,Ledger ledger,Optional<State> state,BigInteger date) {return new Request(source(),Optional.of(frame(actor,date)),Step.LIFE_ADVANCE,root,ledger,state,false);}
    private static Frame frame(long actor,BigInteger date) {return new Frame("native:5",BigInteger.valueOf(17),REV,date,actor,true,true,true,Context.CLEAR);}
    private static Root root(long actor,List<Long> ids) {return new Root(true,actor,true,REV,DATE,Optional.of(ids));}
    private static G2Source source() {return new G2Source("xenoamess-full-tower-eb9d2c1186","2026-11-03T00:00:00Z","1.20.0.4",PIN);}
    private static OrdinarySwayService.Capabilities capabilities() {return new OrdinarySwayService.Capabilities(true,true,true);}
    private static ObjectNode wire(long actor) {
        ObjectNode row=StrictJson.object();ObjectNode src=row.putObject("source");src.put("machine_id",source().machineId()).put("observed_at_utc",source().observedAtUtc()).put("exact_build",source().exactBuild()).set("source_ref",PIN.toJson());
        ObjectNode snap=row.putObject("snapshot");snap.put("snapshot_id","native:5").put("revision",17).put("native_revision",5).put("date_raw",DATE).put("paused",true).put("map_ready",true);
        snap.putObject("played_character").put("character_id",actor).put("alive",true);snap.putObject("active_context").putNull("active_event").putNull("pending_character_interaction");
        row.put("selected_step","life-advance").putNull("root").putNull("state").put("active_observation_only",false);row.putObject("ledger").putNull("pending").putNull("resolved");return row;
    }
    private static PlanningRequest planning(long actor) {
        var identity=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(actor),REV,DATE);
        var proposal=new ProposalFrame(identity,"native:5",BigInteger.valueOf(17),"episode:software233");
        var before=new ObservationIdentity(source().machineId(),new GameGeneration(73,new PythonOnlyUInt64(new BigInteger("134370000000000001"))),proposal,1);
        ObjectNode snap=StrictJson.object();snap.put("snapshot_id",proposal.snapshotId()).put("episode_run_id",proposal.episodeRunId()).put("revision",proposal.revision()).put("native_revision",REV).put("date_raw",DATE).put("paused",true).put("map_ready",true);
        snap.putArray("active_wars");snap.putArray("player_armies");snap.putNull("active_event");snap.putNull("pending_character_interaction");snap.putObject("played_character").put("character_id",actor).put("alive",true);
        var observation=new PlanningObservation(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(snap)),"software233-snapshot"),List.of(),Set.of(OrdinarySwayPolicy.OPERATION),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,source(),"fixture:software233-session",Instant.parse("2030-01-01T00:00:00Z"),observation);
    }
    private static ExpectedPostcondition expected(PlanningRequest request,OrdinarySwayService.Staged ignored) {return new ExpectedPostcondition(1,request.before(),request.source(),"fixture:software233-observer",List.of(new ExpectedBoolean(new FieldKey("software233.observed"),true)));}
    private static OrdinaryPolicy.Draft previous(PlanningRequest request) {
        var command=new ActionCommand("fixture:software233-earlier",request.before(),request.source(),request.sessionId(),new OperationKey("life-advance"),new OpportunityJson.Obj(java.util.Map.of()),expected(request,null),new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        return new OrdinaryPolicy.Draft("fixture:software233-policy","life-advance","software233 only",OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(java.util.Map.of()));
    }
    private static void run(String name,Runnable body) {body.run();scenes++;System.out.println("PASS "+name);}
    private static void check(boolean value) {checks++;if(!value)throw new AssertionError("check "+checks);}
    private static void equal(Object actual,Object expected) {check(java.util.Objects.equals(actual,expected));}
    private static void reject(Runnable body) {checks++;try {body.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expected rejection");}
}
