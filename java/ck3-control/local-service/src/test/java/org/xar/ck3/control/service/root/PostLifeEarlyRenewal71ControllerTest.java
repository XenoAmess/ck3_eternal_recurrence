package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Controller/Planner/RootLoop consumers with checked public software ports; no private Root issuer or live authority. */
final class PostLifeEarlyRenewal71ControllerTest {
    private static final Instant AT=Instant.parse("2026-11-12T18:00:00Z");
    private static final long INITIAL_DATE=53144328L;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final SessionIdentity OWNER=new SessionIdentity("test-machine",GAME,"held-session");
    private static final ExactRef SOURCE=ref("source","a"),GUARD=ref("guard","b"),EFFECT=ref("effect","c");
    private static final G2Source BUILD=new G2Source(OWNER.machineId(),AT.toString(),"controlled-software-source",SOURCE);

    @Test void originalSettledLifeDefersCleanlyThenRealRootLoopRunsAFreshSmallActionWithoutRenewingTheOldCommand() throws Exception {
        Fixture f=new Fixture();f.nextSmall=true;
        SessionController controller=f.controller();
        var reports=new ArrayList<BatchReport>();var seenLimits=new ArrayList<BatchLimits>();
        RootOrdinaryWorkerLoop.Control control=new RootOrdinaryWorkerLoop.Control(){
            @Override public boolean stopRequested(){return false;}
            @Override public boolean allowPostCycleBudgetRenewal(){return true;}
            @Override public void onBatchCompleted(BatchReport report,long next){
                f.events.add("callback:"+next);reports.add(report);
                assertSame(report,controller.lastReport().orElseThrow());
                assertFalse(controller.isRunning());
                if(next==1){
                    assertEquals(BatchReport.Terminal.WALL_TIMEOUT,report.terminal());
                    assertTrue(report.detail().startsWith("POST_SETTLE_LIFE_BUDGET_DEFERRED:"));
                    assertEquals(JournalKind.BATCH_DEFERRED,f.journal.getLast().kind());
                    assertEquals(2,f.observations,"only original planning and actual after-SEM were observed; no duplicate tail Ready");
                    assertEquals(1,f.policyCalls);assertEquals(1,f.actions.size());
                    assertEquals(1,f.settled.size());assertSame(f.actions.getFirst(),f.settled.getFirst());
                    assertFalse(controller.isQuarantined());assertFalse(controller.lastBatchBoundary().orElseThrow().pendingAction());
                }
            }
        };
        var configuration=new RootOrdinaryWorkerLoop.Configuration("renew71",2,Duration.ofSeconds(1200),Duration.ofSeconds(60),Duration.ofMillis(1),3);
        var loop=new RootOrdinaryWorkerLoop(configuration,control,f.time);
        RootOrdinaryWorkerLoop.BatchAccess access=()->new RootOrdinaryWorkerLoop.BatchCurrent(controller,limits->{seenLimits.add(limits);return controller.runBatch(limits);});
        var result=loop.run(access,0);
        assertEquals(2,reports.size());assertEquals(2,result.nextBatchSequence());
        assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,result.stopReason());
        assertTrue(result.failureDetail().isEmpty());
        assertEquals(List.of("renew71-0","renew71-1"),seenLimits.stream().map(BatchLimits::batchId).toList());
        assertTrue(seenLimits.stream().allMatch(BatchLimits::optInEarlyRenew));
        BatchReport first=reports.getFirst(),second=reports.getLast();
        assertEquals(Duration.ofSeconds(601).toNanos(),first.fullWallNanos());
        assertEquals(1,first.turns().size());assertEquals(1,first.eligibleAdvancesSinceSave());
        assertEquals(1,second.turns().size());assertEquals("fixture-small-action",second.turns().getFirst().receipt().command().operation().value());
        assertEquals(BatchReport.Terminal.OPERATOR_STOP,second.terminal());
        assertEquals(1,second.eligibleAdvancesSinceSave());
        assertEquals(2,f.actions.size());assertEquals(2,f.retained.size());assertEquals(2,f.settled.size());
        assertEquals(2,f.policyCalls);assertEquals(0,f.checkpointReadinessCalls);
        ActionCommand original=f.actions.getFirst().command(),small=f.actions.getLast().command();
        assertEquals(AT.plusSeconds(1200),original.deadline());
        assertEquals(AT.plusSeconds(1801),small.deadline());
        assertNotEquals(original.actionId(),small.actionId());assertNotEquals(original.before(),small.before());
        assertArrayEquals(f.originalLifeBody,ActionCodec.encodeCommand(original));
        assertTrue(small.before().frame().identity().nativeRevision().compareTo(original.before().frame().identity().nativeRevision())>0);
        assertEquals(INITIAL_DATE+24,small.before().frame().identity().dateRaw().longValueExact());
        assertBefore(f.events,"settle:life","journal:BATCH_DEFERRED");
        assertBefore(f.events,"journal:BATCH_DEFERRED","callback:1");
        assertBefore(f.events,"callback:1","observe:3");assertBefore(f.events,"observe:3","execute:small");
        assertNoSavedCredit(first,f);assertNoSavedCredit(second,f);
    }

    @Test void originalSixArgumentFiniteCallerAndDefaultRootControlKeepTheirPreviousPath() {
        Fixture f=new Fixture();SessionController controller=f.controller();
        BatchLimits old=legacyLimits("old-six",2);
        assertFalse(old.optInEarlyRenew());
        assertEquals(old,new BatchLimits("old-six",2,Duration.ofSeconds(1200),Duration.ofSeconds(60),Duration.ofMillis(1),3,false));
        RootOrdinaryWorkerLoop.Control defaults=new RootOrdinaryWorkerLoop.Control(){
            @Override public boolean stopRequested(){return false;}
            @Override public void onBatchCompleted(BatchReport report,long next){throw new AssertionError("default flag inspection executes no worker");}
        };
        assertFalse(defaults.allowPostCycleBudgetRenewal());
        BatchReport report=controller.runBatch(old);
        assertEquals(BatchReport.Terminal.PLANNER_STOPPED,report.terminal());
        assertFalse(report.detail().contains("POST_SETTLE_LIFE_BUDGET_DEFERRED"));
        assertEquals(2,f.policyCalls);assertEquals(3,f.observations);
        assertEquals(1,f.actions.size());assertEquals(1,f.settled.size());assertFalse(controller.isQuarantined());
        assertEquals(JournalKind.BATCH_INTERRUPTED,f.journal.getLast().kind());
        assertNoSavedCredit(report,f);
        assertSame(report,controller.runBatch(old));assertEquals(1,f.actions.size());assertEquals(3,f.observations);
    }

    @Test void mandatoryFixedYearSaveStillReachesOriginalReadinessGuardInsteadOfEarlyRenewal() {
        Fixture f=new Fixture();f.savedDate=INITIAL_DATE+24-8760;f.rejectRequiredSave=true;
        SessionController controller=f.controller();
        BatchReport report=controller.runBatch(optedLimits("annual-due",2));
        assertEquals(1,f.settled.size());assertEquals(1,f.actions.size());
        assertEquals(3,f.observations,"annual due keeps the next real Ready and original SAVE path before another action");
        assertEquals(1,f.checkpointReadinessCalls,"original SAVE factory must be entered");
        assertEquals(INITIAL_DATE+24-f.savedDate,8760);
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,report.terminal());
        assertTrue(report.detail().contains("fresh native SAVE readiness changed"));
        assertFalse(report.detail().contains("POST_SETTLE_LIFE_BUDGET_DEFERRED"));
        assertTrue(controller.isQuarantined());
        assertNoSavedCredit(report,f);
    }

    @Test void turnBoundStopAndMissingPhysicalBaselineDoNotUseTheNewEarlyBoundary() {
        Fixture turn=new Fixture();var turnController=turn.controller();
        BatchReport bound=turnController.runBatch(optedLimits("turn-bound",1));
        assertEquals(BatchReport.Terminal.TURN_BOUND,bound.terminal());assertEquals(3,turn.observations);
        assertEquals(JournalKind.BATCH_FINISHED,turn.journal.getLast().kind());assertFalse(turnController.isQuarantined());
        assertNoSavedCredit(bound,turn);
        Fixture stop=new Fixture();stop.stopAfterLife=true;var stopController=stop.controller();
        BatchReport stopped=stopController.runBatch(optedLimits("stop-bound",2));
        assertEquals(BatchReport.Terminal.OPERATOR_STOP,stopped.terminal());assertEquals(3,stop.observations);
        assertEquals(JournalKind.BATCH_FINISHED,stop.journal.getLast().kind());assertEquals(1,stop.policyCalls);
        assertFalse(stopController.isQuarantined());assertNoSavedCredit(stopped,stop);
        Fixture missing=new Fixture();missing.withBaseline=false;missing.rejectRequiredSave=true;var missingController=missing.controller();
        BatchReport noBaseline=missingController.runBatch(optedLimits("no-baseline",2));
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,noBaseline.terminal());
        assertTrue(noBaseline.detail().contains("fresh native SAVE readiness changed"));
        assertFalse(noBaseline.detail().contains("POST_SETTLE_LIFE_BUDGET_DEFERRED"));
        assertEquals(1,missing.policyCalls);assertEquals(3,missing.observations);assertEquals(1,missing.checkpointReadinessCalls);assertTrue(noBaseline.lastSavedPair().isEmpty());
        assertTrue(missingController.isQuarantined());assertNoSavedCredit(noBaseline,missing);
    }

    private static BatchLimits legacyLimits(String id,int turns){return new BatchLimits(id,turns,Duration.ofSeconds(1200),Duration.ofSeconds(60),Duration.ofMillis(1),3);}
    private static BatchLimits optedLimits(String id,int turns){return new BatchLimits(id,turns,Duration.ofSeconds(1200),Duration.ofSeconds(60),Duration.ofMillis(1),3,true);}
    private static ExactRef ref(String label,String hash){return new ExactRef("D:/fixture/renew71-"+label+".json",1,hash.repeat(64));}
    private static ObservationIdentity frame(long date,long revision){
        return new ObservationIdentity(OWNER.machineId(),GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(revision),BigInteger.valueOf(date)),
                "snapshot-"+revision,BigInteger.valueOf(revision),"episode-real-1"),1);
    }
    private static List<ExpectedValue> flags(boolean eligible){return List.of(
            new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true),
            new ExpectedBoolean(new FieldKey("timeline.advance_verified"),eligible),
            new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),eligible),
            new ExpectedText(new FieldKey("progress_status"),"postcondition"));}
    private static ActionCommand command(PlanningRequest request,String id,String operation,List<ExpectedValue> expected){
        return new ActionCommand(id,request.before(),request.source(),request.sessionId(),new OperationKey(operation),new OpportunityJson.Obj(Map.of()),
                new ExpectedPostcondition(1,request.before(),request.source(),"test-effect/v1",expected),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
    private static void assertBefore(List<String> events,String a,String b){assertTrue(events.indexOf(a)>=0);assertTrue(events.indexOf(b)>events.indexOf(a),()->a+" must precede "+b+": "+events);}
    private static void assertNoSavedCredit(BatchReport report,Fixture f){
        assertEquals(0,report.committedSavedDays());assertTrue(report.dirtySinceSave());assertEquals(1,report.eligibleAdvancesSinceSave());
        assertEquals(f.withBaseline,report.lastSavedPair().isPresent());
        if(f.withBaseline)assertSame(f.baseline,report.lastSavedPair().orElseThrow());
        assertTrue(report.reconciliations().isEmpty());assertTrue(report.lifecycleTurns().isEmpty());
    }
    private static final class MutableClock extends Clock implements SessionClock {
        long nanos;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC only");return this;}
        @Override public Instant instant(){return AT.plusNanos(nanos);}
        @Override public Tick now(){return new Tick(nanos,instant());}
        @Override public void waitFor(Duration duration){nanos+=duration.toNanos();}
    }
    private static final class Fixture {
        final MutableClock time=new MutableClock();
        final List<String> events=new ArrayList<>();final List<JournalInput> journal=new ArrayList<>();
        final List<ActionReceipt> actions=new ArrayList<>(),retained=new ArrayList<>(),settled=new ArrayList<>();
        final List<SemanticEvidence> semantics=new ArrayList<>();
        long date=INITIAL_DATE,revision=8,savedDate=INITIAL_DATE,completedCycles=1;
        int observations,policyCalls,checkpointReadinessCalls;boolean withBaseline=true,nextSmall,stopAfterLife,rejectRequiredSave;
        ActionReceipt pending;SessionController controller;CheckpointPair baseline;byte[] originalLifeBody;
        PlanningRequest latestRequest;
        SessionController controller(){
            var realm=new RealmLifecycle(SOURCE);
            List<OrdinaryPolicy> policies=Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
                if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
                return new OrdinaryPolicy(){
                    @Override public PlanningStage stage(){return stage;}
                    @Override public ExactRef implementationSource(){return SOURCE;}
                    @Override public Decision evaluate(PlanningRequest request,Draft previous){
                        if(stage!=PlanningStage.ORDINARY_CORE)return new Keep("preserve original stage order");
                        policyCalls++;
                        if(actions.isEmpty())return new Replace(new Draft("test-life","original","complete original Life DATA",Kind.ORDINARY,
                                Optional.of(command(request,"life-original","life-advance",flags(true))),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"original Life");
                        if(nextSmall&&actions.size()==1)return new Replace(new Draft("test-small","fresh","next independent small DATA",Kind.ORDINARY,
                                Optional.of(command(request,"fresh-small","fixture-small-action",flags(false))),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"independent small action");
                        return new Stop(PlanningResult.StopReason.POLICY_BLOCKED,"controlled finite next-policy boundary");
                    }
                };
            }).toList();
            var planner=new OrdinaryPlanner(policies,time,realm);
            CheckpointFiles files=new CheckpointFiles(){
                @Override public Optional<CheckpointPair.FileWitness> observe(Path path){throw unused();}
                @Override public byte[] read(CheckpointPair.FileWitness witness,int maximum){throw unused();}
                @Override public CheckpointPair.FileWitness replace(Path path,byte[] bytes){throw unused();}
                @Override public CheckpointPair.FileWitness createNew(Path path,byte[] bytes){throw unused();}
                @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source,Path target){throw unused();}
            };
            var drivers=new DriverCheckpointStore(files,Path.of("D:/fixture/renew71-Driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
                @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw unused();}
            });
            CheckpointRequest.ObservationPort checkpointReady=until->{
                checkpointReadinessCalls++;events.add("save-readiness");
                assertTrue(rejectRequiredSave,"unexpected SAVE factory path");
                return new CheckpointRequest.Readiness(latestRequest.before(),BUILD,OWNER.sessionId(),"lineage-1",true,true,false,
                        "controlled unavailable physical SAVE readiness",EFFECT,time.instant());
            };
            var checkpoints=new CheckpointService(files,drivers,checkpointReady,Path.of("D:/fixture/renew71-evidence"),time,(pair,receipt)->{throw unused();});
            var checkpointRequests=new CheckpointRequestFactory(Path.of("D:/fixture/xar_checkpoint.ck3"),checkpointReady);
            ObservationPort observe=new ObservationPort(){
                @Override public Observation observe(SessionIdentity owner,Instant until){return ready(owner,until);}
                @Override public Observation observe(SessionIdentity owner,Instant readinessUntil,Instant planningUntil){return ready(owner,planningUntil);}
                @Override public Observation observeAfter(SessionIdentity owner,ActionReceipt actual,Instant readinessUntil,Instant planningUntil){
                    assertSame(pending,actual,"actual retained receipt must supply after-cycle capture");return ready(owner,planningUntil);
                }
                private Observation ready(SessionIdentity owner,Instant until){
                    assertEquals(OWNER,owner);observations++;events.add("observe:"+observations);revision++;
                    var before=frame(date,revision);
                    var snapshot=OpportunityJson.object(OpportunityJson.parse(("{\"paused\":true,\"map_ready\":true,\"revision\":"+revision
                            +",\"native_revision\":"+revision+",\"date_raw\":"+date+",\"snapshot_id\":\"snapshot-"+revision
                            +"\",\"episode_run_id\":\"episode-real-1\",\"played_character\":{\"character_id\":73},\"active_wars\":[],\"player_armies\":[]}").getBytes(StandardCharsets.UTF_8)),"fixture");
                    var data=new PlanningObservation(snapshot,List.of(),Set.of(new OperationKey("life-advance"),new OperationKey("fixture-small-action")),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
                    latestRequest=new PlanningRequest(before,BUILD,OWNER.sessionId(),until,data);
                    var semantic=new SemanticEvidence(before,ref("semantic-"+observations,"d"),ref("native-"+observations,"e"),ref("stamp-"+observations,"f"),ref("driver-"+observations,"a"),time.instant());
                    semantics.add(semantic);return new Ready(latestRequest,CheckpointEligibility.SAFE,Optional.empty(),Optional.of(semantic));
                }
            };
            ActionCoordinatorPort actionPort=new ActionCoordinatorPort(){
                @Override public ActionReceipt execute(ActionCommand original){
                    boolean life=original.operation().value().equals("life-advance");events.add("execute:"+(life?"life":"small"));
                    assertEquals(latestRequest.before(),original.before());assertEquals(latestRequest.deadline(),original.deadline());
                    if(life){assertTrue(actions.isEmpty());originalLifeBody=ActionCodec.encodeCommand(original);}
                    Instant started=time.instant();time.waitFor(Duration.ofSeconds(life?601:1));
                    ActionReceipt receipt=applied(original,life,started);actions.add(receipt);return receipt;
                }
                @Override public ActionReceipt reconcile(String id){throw unused();}
            };
            OrdinaryPlanCompletion.PlanningScope completion=new OrdinaryPlanCompletion.PlanningScope(){
                @Override public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
                @Override public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult result){return new Unchanged("controlled no publication");}
                @Override public ExecutionDisposition afterExecution(ActionReceipt receipt){assertSame(actions.getLast(),receipt);return new Unchanged("original public receipt consumed");}
            };
            BatchJournal writer=new BatchJournal(){
                @Override public JournalCommit commit(JournalInput input){
                    assertEquals(OWNER,input.session());events.add("journal:"+input.kind());journal.add(input);
                    if(input.kind()!=JournalKind.BATCH_STARTED)assertNull(pending,"a pending cycle cannot disappear at batch completion");
                    return new JournalCommit(ref("journal-"+journal.size(),"b"),0);
                }
                @Override public void validateOrdinarySubmission(SessionIdentity owner,SemanticEvidence actual){
                    assertEquals(OWNER,owner);assertSame(semantics.getLast(),actual);assertEquals(latestRequest.before(),actual.frame());assertNull(pending);
                }
                @Override public void retainCycle(SessionIdentity owner,ActionReceipt actual){
                    assertEquals(OWNER,owner);assertSame(actions.getLast(),actual);assertNull(pending);assertTrue(actual.settled());
                    assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,actual.outcome());pending=actual;retained.add(actual);
                    events.add("retain:"+(actual.command().operation().value().equals("life-advance")?"life":"small"));
                }
                @Override public boolean requiresFreshAfterCycle(SessionIdentity owner,ActionReceipt actual){assertSame(pending,actual);return true;}
                @Override public CompletedCycleProof settleCycle(SessionIdentity owner,ActionReceipt original,SemanticEvidence after){
                    assertEquals(OWNER,owner);assertSame(pending,original);assertSame(semantics.getLast(),after);assertEquals(latestRequest.before(),after.frame());
                    var effect=original.applied().orElseThrow().observation();
                    assertEquals(effect.after().frame().identity().dateRaw(),after.frame().frame().identity().dateRaw());
                    assertTrue(after.frame().frame().identity().nativeRevision().compareTo(effect.after().frame().identity().nativeRevision())>0);
                    settled.add(original);pending=null;completedCycles++;
                    boolean life=original.command().operation().value().equals("life-advance");events.add("settle:"+(life?"life":"small"));
                    if(stopAfterLife&&life||nextSmall&&!life)controller.requestStop();
                    return new CompletedCycleProof(completedCycles,after,"d".repeat(64));
                }
                @Override public Optional<CompletedCycleProof> cycleProof(SessionIdentity owner,SemanticEvidence actual){
                    assertEquals(OWNER,owner);assertNull(pending);assertSame(semantics.getLast(),actual);
                    return Optional.of(new CompletedCycleProof(completedCycles,actual,"d".repeat(64)));
                }
            };
            baseline=new CheckpointPair(new CheckpointPair.FileWitness(ref("save-baseline","a"),new FileStatIdentity(BigInteger.ONE,"9007199254740993","134000000000000001")),
                    new CheckpointPair.FileWitness(ref("driver-baseline","b"),new FileStatIdentity(BigInteger.ONE,"9007199254740995","134000000000000003")),
                    frame(savedDate,8),"lineage-1",1,"original-save",SOURCE,AT);
            controller=new SessionController(OWNER,(owner,until)->new GameLifecycle.Running(GAME,SOURCE),observe,planner,actionPort,checkpoints,checkpointRequests,
                    writer,work->{throw unused();},time,withBaseline?Optional.of(baseline):Optional.empty(),0,completion,(owner,receipt,until)->{throw unused();});
            controller.bindRetainedIncidents(List::of);return controller;
        }
        private ActionReceipt applied(ActionCommand parent,boolean life,Instant started){
            var guard=new GuardEvidence(new CommandOrigin.Gameplay(parent.before()),BUILD,OWNER.sessionId(),BigInteger.ONE,parent.operation(),GUARD,SOURCE,"controlled-public-DATA",started,parent.deadline());
            List<ActionReceipt> children=new ArrayList<>();List<CompositeExecution.Child> childBindings=new ArrayList<>();
            if(life){
                var child=command(new PlanningRequest(parent.before(),BUILD,OWNER.sessionId(),parent.deadline(),latestRequest.observations()),"resume-child","resume-map",
                        List.of(new ExpectedBoolean(new FieldKey("timeline.resume_observed"),true)));
                var childGuard=new GuardEvidence(new CommandOrigin.Gameplay(child.before()),BUILD,OWNER.sessionId(),BigInteger.ONE,child.operation(),GUARD,SOURCE,"controlled-public-DATA",started,child.deadline());
                var attempt=new ActionState.Attempt("child-request",started,childGuard,new NativeRequest("resume-map",Optional.empty(),new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
                var childEffect=new ActionState.EffectObservation(frame(date+1,revision+1),BUILD,OWNER.sessionId(),"test-effect/v1",child.expected().values(),
                        new ObservationProvenance.Query("independent-child-query"),started.plusSeconds(1),EFFECT);
                var ack=new NativeActionPort.AckReceived("child-request",true,Optional.empty(),new RawJson("{}".getBytes(StandardCharsets.UTF_8)),"software-ack-DATA".getBytes(StandardCharsets.UTF_8));
                var childState=new ActionState.Settled(attempt,ack,new ActionState.Applied(childEffect));
                ActionEffects.validate(child,attempt,ack,childState.settlement());
                var childReceipt=new ActionReceipt(1,9,child,ActionCodec.bodySha256(child),childState);children.add(childReceipt);
                childBindings.add(new CompositeExecution.Child(child.actionId(),childReceipt.bodySha256()));
            }
            date+=life?24:0;revision+=2;
            var effect=new ActionState.EffectObservation(frame(date,revision),BUILD,OWNER.sessionId(),"test-effect/v1",parent.expected().values(),
                    new ObservationProvenance.Query("independent-parent-query"),time.instant(),EFFECT);
            var execution=new CompositeExecution(life?LifeAdvanceComposite.HANDLER:"controlled-small-composite/v1",started,guard,childBindings);
            var settlement=new ActionState.Applied(effect);
            ActionEffects.validateComposite(parent,execution,settlement);ActionEffects.validateCompositeChildren(parent,execution,settlement,children);
            if(life)AdvanceClockArchivedReplay.verifyChildBindings(parent,children);
            var receipt=new ActionReceipt(1,10+actions.size(),parent,ActionCodec.bodySha256(parent),new ActionState.CompositeSettled(execution,settlement));
            assertEquals(life,receipt.eligibleAdvance());assertTrue(receipt.visibleGameplay());return receipt;
        }
        private static AssertionError unused(){return new AssertionError("unexpected actual Game, SAVE file, reconciliation or private issuer path");}
    }
}
