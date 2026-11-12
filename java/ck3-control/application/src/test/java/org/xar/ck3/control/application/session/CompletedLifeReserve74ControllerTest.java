package org.xar.ck3.control.application.session;

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

/** Real shared-clock Controller reports; advisory public hint DATA only, never Root/Native authority. */
final class CompletedLifeReserve74ControllerTest {
    private static final Instant AT=Instant.parse("2026-11-12T18:00:00Z");
    private static final long INITIAL_DATE=53144328L;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final SessionIdentity OWNER=new SessionIdentity("test-machine",GAME,"held-session");
    private static final ExactRef SOURCE=ref("source","a"),GUARD=ref("guard","b"),EFFECT=ref("effect","c");
    private static final G2Source BUILD=new G2Source(OWNER.machineId(),AT.toString(),"controlled-software-source",SOURCE);


    @Test void actualConsecutiveEarlyDeferralsRetainUnsavedEnvelopeAcrossTheSameAndRestoredController() {
        Fixture f=new Fixture();SessionController controller=f.controller();
        BatchReport first=controller.runBatch(optedLimits("sample-first",3));
        assertCleanEarly(first,f,1);assertEquals(Duration.ofSeconds(659).toNanos(),first.fullWallNanos());
        assertEquals(Duration.ofSeconds(19).toNanos(),actionSpans(first).getLast().began().elapsedNanos());
        RawJson hint1=SessionController.retainLifeBudgetHint(first,Optional.empty()).orElseThrow();
        assertHint(hint1,640,0);
        assertEquals(Duration.ofSeconds(640).toNanos(),controller.retainedLifeBudgetReserveNanos(optedLimits("use-first",3),f.latestRequest.before()));
        byte[] original=ActionCodec.encodeCommand(f.actions.getFirst().command());
        f.lifeSeconds=730;
        BatchReport second=controller.runBatch(optedLimits("sample-second",3));
        assertCleanEarly(second,f,2);assertEquals(Duration.ofSeconds(788).toNanos(),second.fullWallNanos());
        RawJson hint2=SessionController.retainLifeBudgetHint(second,Optional.of(hint1)).orElseThrow();
        assertHint(hint2,769,0);
        assertEquals(Duration.ofSeconds(769).toNanos(),controller.retainedLifeBudgetReserveNanos(optedLimits("use-second",3),f.latestRequest.before()));
        assertArrayEquals(original,ActionCodec.encodeCommand(f.actions.getFirst().command()),"neither hint updates an old command deadline/body");
        Fixture replacement=new Fixture();replacement.lifeLimit=1;
        SessionController restored=replacement.controller();assertTrue(restored.restoreLifeBudgetHint(hint2));
        assertEquals(Duration.ofSeconds(769).toNanos(),restored.retainedLifeBudgetReserveNanos(optedLimits("restored-use",3),frame(INITIAL_DATE,8)));
        BatchReport next=restored.runBatch(optedLimits("restored-next",3));assertCleanEarly(next,replacement,1);
        assertHint(SessionController.retainLifeBudgetHint(next,Optional.of(hint2)).orElseThrow(),769,0);
        assertEquals(Duration.ofSeconds(769).toNanos(),restored.retainedLifeBudgetReserveNanos(optedLimits("still-retained",3),replacement.latestRequest.before()));
    }

    @Test void precedingSmallActionAndRealNestedPhaseWorkDoNotReplaceTheLastLifeEnvelope() {
        Fixture f=new Fixture();f.smallBeforeLife=true;f.lifeLimit=1;
        BatchReport report=f.controller().runBatch(optedLimits("small-then-life",3));
        assertCleanEarly(report,f,2);assertEquals(2,report.turns().size());
        assertEquals("fixture-small-action",report.turns().getFirst().receipt().command().operation().value());
        assertEquals("life-advance",report.turns().getLast().receipt().command().operation().value());
        assertEquals(Duration.ofSeconds(833).toNanos(),report.fullWallNanos());
        var actions=actionSpans(report);assertEquals(2,actions.size());
        assertEquals(Duration.ofSeconds(19).toNanos(),actions.getFirst().began().elapsedNanos());
        assertEquals(Duration.ofSeconds(193).toNanos(),actions.getLast().began().elapsedNanos());
        // 601 action + 7 outcome + 3 retain + 11 fresh after-SEM + 13 SETTLE + 5 final journal.
        // The preceding small action takes 121+7+3+11+13=155 seconds; the final journal5 runs once per batch.
        // Last Life starts at19+155+19=193, report ends833. Earlier action begins19, yielding814, not640.
        // The preceding small action and both pre-planning Ready intervals cannot enter this sample.
        RawJson hint=SessionController.retainLifeBudgetHint(report,Optional.empty()).orElseThrow();assertHint(hint,640,0);
        assertNotEquals(Duration.ofSeconds(814).toNanos(),nanos(hint,"reserve_floor_nanos"));
        long phaseSum=report.phases().stream().mapToLong(span->span.ended().elapsedNanos()-span.began().elapsedNanos()).sum();
        assertNotEquals(phaseSum,nanos(hint,"reserve_floor_nanos"),"use the observed last-action-to-report envelope, not nested span sums");
    }

    @Test void invalidOrUnmarkedSamplesPreserveValidHintsAndNeverCreateSavedTailOrForeignAdmission() {
        Fixture f=new Fixture();SessionController c=f.controller();
        BatchReport first=c.runBatch(optedLimits("valid-prior",3));assertCleanEarly(first,f,1);
        RawJson prior=SessionController.retainLifeBudgetHint(first,Optional.empty()).orElseThrow();assertHint(prior,640,0);
        byte[] originalHint=prior.bytes();f.lifeSeconds=901;
        BatchReport larger=c.runBatch(optedLimits("larger-source",3));assertCleanEarly(larger,f,2);
        assertHint(SessionController.retainLifeBudgetHint(larger,Optional.of(prior)).orElseThrow(),940,0);
        var failed=new ArrayList<BatchReport.PhaseSpan>();
        for(var span:larger.phases())failed.add(span.phase()==BatchReport.Phase.ACTION
                ?new BatchReport.PhaseSpan(span.phase(),span.began(),span.ended(),BatchReport.PhaseTerminal.FAILED):span);
        var turn=larger.turns().getLast();
        var mixed=List.of(new BatchReport.Reconciliation(1,turn.before(),turn.plan(),turn.receipt()));
        long afterDay=actionSpans(larger).getLast().began().elapsedNanos()+Duration.ofDays(1).toNanos()+1;
        var tooLate=new SessionClock.Tick(afterDay,AT.plusNanos(afterDay));
        for(BatchReport bad:List.of(
                copy(larger,larger.session(),"not an early-deferral marker",larger.phases(),List.of(),larger.ended(),larger.lastSavedPair()),
                copy(larger,larger.session(),larger.detail(),failed,List.of(),larger.ended(),larger.lastSavedPair()),
                copy(larger,larger.session(),larger.detail(),larger.phases(),mixed,larger.ended(),larger.lastSavedPair()),
                copy(larger,larger.session(),larger.detail(),larger.phases(),List.of(),tooLate,larger.lastSavedPair()))) {
            assertHint(SessionController.retainLifeBudgetHint(bad,Optional.of(prior)).orElseThrow(),640,0);
        }
        Fixture legacy=new Fixture();legacy.lifeLimit=1;
        BatchReport old=legacy.controller().runBatch(legacyLimits("legacy-six",3));
        assertFalse(old.detail().startsWith("POST_SETTLE_LIFE_BUDGET_DEFERRED:"));
        assertHint(SessionController.retainLifeBudgetHint(old,Optional.of(prior)).orElseThrow(),640,0);
        var foreignOwner=new SessionIdentity(OWNER.machineId(),OWNER.game(),"another-session");
        BatchReport foreign=copy(larger,foreignOwner,larger.detail(),larger.phases(),List.of(),larger.ended(),larger.lastSavedPair());
        assertTrue(SessionController.retainLifeBudgetHint(foreign,Optional.of(prior)).isEmpty());
        var oldPair=larger.lastSavedPair().orElseThrow();var originalFrame=oldPair.frame();
        var otherSubject=new ObservationIdentity(originalFrame.machineId(),originalFrame.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(74),originalFrame.frame().identity().nativeRevision(),originalFrame.frame().identity().dateRaw()),
                originalFrame.frame().snapshotId(),originalFrame.frame().revision(),originalFrame.frame().episodeRunId()),originalFrame.observationVersion());
        var wrongPair=new CheckpointPair(oldPair.save(),oldPair.driver(),otherSubject,oldPair.lineageId(),oldPair.historyIndex(),oldPair.saveActionId(),oldPair.nativeAckRef(),oldPair.observedAt());
        assertTrue(SessionController.retainLifeBudgetHint(copy(larger,larger.session(),larger.detail(),larger.phases(),List.of(),larger.ended(),Optional.of(wrongPair)),Optional.of(prior)).isEmpty());
        assertArrayEquals(originalHint,prior.bytes());
        var fresh=new Fixture().controller();assertTrue(fresh.restoreLifeBudgetHint(prior));
        assertEquals(Duration.ofSeconds(640).toNanos(),fresh.retainedLifeBudgetReserveNanos(optedLimits("prior-still-valid",3),frame(INITIAL_DATE,8)));
    }

    private static List<BatchReport.PhaseSpan> actionSpans(BatchReport report){return report.phases().stream().filter(span->span.phase()==BatchReport.Phase.ACTION).toList();}
    private static long nanos(RawJson hint,String key){return Long.parseLong(StrictJson.text(StrictJson.parse(hint.bytes()).get(key)));}
    private static void assertHint(RawJson hint,long floorSeconds,long savedTailSeconds){
        var row=StrictJson.parse(hint.bytes());assertEquals("xar.life-budget-hint/v1",row.get("schema").textValue());
        assertEquals(OWNER,OrdinaryCycleTransitions.sessionFromJson(row.get("owner")));
        assertEquals(Duration.ofSeconds(floorSeconds).toNanos(),nanos(hint,"reserve_floor_nanos"));
        assertEquals(Duration.ofSeconds(savedTailSeconds).toNanos(),nanos(hint,"saved_life_tail_nanos"));
    }
    private static void assertCleanEarly(BatchReport report,Fixture f,int completedActions){
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT,report.terminal(),report.detail());
        assertTrue(report.detail().startsWith("POST_SETTLE_LIFE_BUDGET_DEFERRED: "),report.detail());
        assertEquals(0,report.committedSavedDays());assertTrue(report.dirtySinceSave());assertEquals(f.lifeExecuted,report.eligibleAdvancesSinceSave());
        assertEquals(completedActions,f.settled.size());assertNull(f.pending);assertFalse(f.controller.isQuarantined());
        assertEquals(JournalKind.BATCH_DEFERRED,f.journal.getLast().kind());assertTrue(report.lastLifecycle().orElseThrow() instanceof GameLifecycle.Running);
        assertTrue(report.phases().stream().anyMatch(span->span.phase()==BatchReport.Phase.LIFECYCLE));
        assertSame(f.baseline,report.lastSavedPair().orElseThrow());assertTrue(report.reconciliations().isEmpty());
    }
    private static BatchReport copy(BatchReport r,SessionIdentity owner,String detail,List<BatchReport.PhaseSpan> phases,
            List<BatchReport.Reconciliation> reconciliations,SessionClock.Tick ended,Optional<CheckpointPair> saved){
        return new BatchReport(owner,r.batchId(),r.terminal(),detail,r.began(),ended,phases,r.turns(),reconciliations,r.lifecycleTurns(),
                r.readPublicationReconciliations(),r.revisionReplans(),r.lastPlan(),r.lastTerminalObservation(),r.lastLifecycle(),saved,
                r.committedLedgerHead(),r.committedSavedDays(),r.eligibleAdvancesSinceSave(),r.dirtySinceSave(),r.pendingAnalysisBatchIds(),r.completedAnalyses(),r.failedAnalysisBatchIds());
    }
    private static BatchLimits legacyLimits(String id,int turns){return new BatchLimits(id,turns,Duration.ofSeconds(1200),Duration.ofSeconds(60),Duration.ofMillis(1),3);}
    private static BatchLimits optedLimits(String id,int turns){return new BatchLimits(id,turns,Duration.ofSeconds(1200),Duration.ofSeconds(60),Duration.ofMillis(1),3,true);}
    private static ExactRef ref(String label,String hash){return new ExactRef("D:/fixture/reserve74-"+label+".json",1,hash.repeat(64));}
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
        int observations,policyCalls,checkpointReadinessCalls,lifeExecuted; boolean withBaseline=true,nextSmall,stopAfterLife,rejectRequiredSave,smallBeforeLife;
        int lifeLimit=2; long lifeSeconds=601;
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
                        if(smallBeforeLife&&actions.isEmpty())return new Replace(new Draft("test-small","first","independent first small DATA",Kind.ORDINARY,
                                Optional.of(command(request,"first-small","fixture-small-action",flags(false))),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"first small action");
                        if(lifeExecuted<lifeLimit)return new Replace(new Draft("test-life","original","complete original Life DATA",Kind.ORDINARY,
                                Optional.of(command(request,"life-original-"+lifeExecuted,"life-advance",flags(true))),Purpose.WORLD_ACTION,Optional.empty(),new OpportunityJson.Obj(Map.of())),"original Life");
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
            var drivers=new DriverCheckpointStore(files,Path.of("D:/fixture/reserve74-Driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
                @Override public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw unused();}
            });
            CheckpointRequest.ObservationPort checkpointReady=until->{
                checkpointReadinessCalls++;events.add("save-readiness");
                assertTrue(rejectRequiredSave,"unexpected SAVE factory path");
                return new CheckpointRequest.Readiness(latestRequest.before(),BUILD,OWNER.sessionId(),"lineage-1",true,true,false,
                        "controlled unavailable physical SAVE readiness",EFFECT,time.instant());
            };
            var checkpoints=new CheckpointService(files,drivers,checkpointReady,Path.of("D:/fixture/reserve74-evidence"),time,(pair,receipt)->{throw unused();});
            var checkpointRequests=new CheckpointRequestFactory(Path.of("D:/fixture/xar_checkpoint.ck3"),checkpointReady);
            ObservationPort observe=new ObservationPort(){
                @Override public Observation observe(SessionIdentity owner,Instant until){return ready(owner,until);}
                @Override public Observation observe(SessionIdentity owner,Instant readinessUntil,Instant planningUntil){return ready(owner,planningUntil);}
                @Override public Observation observeAfter(SessionIdentity owner,ActionReceipt actual,Instant readinessUntil,Instant planningUntil){
                    assertSame(pending,actual,"actual retained receipt must supply after-cycle capture");time.waitFor(Duration.ofSeconds(11));return ready(owner,planningUntil);
                }
                private Observation ready(SessionIdentity owner,Instant until){
                    assertEquals(OWNER,owner);if(pending==null)time.waitFor(Duration.ofSeconds(19));observations++;events.add("observe:"+observations);revision++;
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
                    if(life){if(originalLifeBody==null)originalLifeBody=ActionCodec.encodeCommand(original);lifeExecuted++;}
                    Instant started=time.instant();time.waitFor(Duration.ofSeconds(life?lifeSeconds:121));
                    ActionReceipt receipt=applied(original,life,started);actions.add(receipt);return receipt;
                }
                @Override public ActionReceipt reconcile(String id){throw unused();}
            };
            OrdinaryPlanCompletion.PlanningScope completion=new OrdinaryPlanCompletion.PlanningScope(){
                @Override public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
                @Override public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult result){return new Unchanged("controlled no publication");}
                @Override public ExecutionDisposition afterExecution(ActionReceipt receipt){assertSame(actions.getLast(),receipt);time.waitFor(Duration.ofSeconds(7));return new Unchanged("original public receipt consumed");}
            };
            BatchJournal writer=new BatchJournal(){
                @Override public JournalCommit commit(JournalInput input){
                    assertEquals(OWNER,input.session());events.add("journal:"+input.kind());journal.add(input);
                    if(input.kind()!=JournalKind.BATCH_STARTED){assertNull(pending,"a pending cycle cannot disappear at batch completion");time.waitFor(Duration.ofSeconds(5));}
                    return new JournalCommit(ref("journal-"+journal.size(),"b"),0);
                }
                @Override public void validateOrdinarySubmission(SessionIdentity owner,SemanticEvidence actual){
                    assertEquals(OWNER,owner);assertSame(semantics.getLast(),actual);assertEquals(latestRequest.before(),actual.frame());assertNull(pending);
                }
                @Override public void retainCycle(SessionIdentity owner,ActionReceipt actual){
                    assertEquals(OWNER,owner);assertSame(actions.getLast(),actual);assertNull(pending);assertTrue(actual.settled());
                    assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,actual.outcome());pending=actual;retained.add(actual);
                    events.add("retain:"+(actual.command().operation().value().equals("life-advance")?"life":"small"));time.waitFor(Duration.ofSeconds(3));
                }
                @Override public boolean requiresFreshAfterCycle(SessionIdentity owner,ActionReceipt actual){assertSame(pending,actual);return true;}
                @Override public CompletedCycleProof settleCycle(SessionIdentity owner,ActionReceipt original,SemanticEvidence after){
                    assertEquals(OWNER,owner);assertSame(pending,original);assertSame(semantics.getLast(),after);assertEquals(latestRequest.before(),after.frame());
                    var effect=original.applied().orElseThrow().observation();
                    assertEquals(effect.after().frame().identity().dateRaw(),after.frame().frame().identity().dateRaw());
                    assertTrue(after.frame().frame().identity().nativeRevision().compareTo(effect.after().frame().identity().nativeRevision())>0);
                    time.waitFor(Duration.ofSeconds(13));settled.add(original);pending=null;completedCycles++;
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
                var child=command(new PlanningRequest(parent.before(),BUILD,OWNER.sessionId(),parent.deadline(),latestRequest.observations()),"resume-child-"+lifeExecuted,"resume-map",
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
