package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software Controller/Loop execution with the existing observation-deadline fixture shape. No Game or transport. */
final class RootOrdinaryWorkerNoProgressTest {
    private static final Instant BASE=Instant.parse("2026-10-30T00:00:00Z");
    private static final Duration WALL=Duration.ofSeconds(300);
    private static final BigInteger DATE=BigInteger.valueOf(53144328);
    private static final ExactRef REF=new ExactRef("D:/fixture/no-progress-source",1,"a".repeat(64));
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER=new SessionIdentity("fixture-machine-1",GAME,"no-progress-session");
    private static ObservationIdentity observed(BigInteger date,int revision) {
        return new ObservationIdentity(OWNER.machineId(),GAME,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(31254),BigInteger.valueOf(revision),date),
                "software-frame-"+revision,BigInteger.valueOf(revision),"software-episode"),3);
    }
    private static BatchReport report(BatchReport.Terminal terminal,long seconds,List<BatchReport.PhaseSpan> phases) {
        return new BatchReport(OWNER,"software-batch",terminal,"software boundary",
                new SessionClock.Tick(0,BASE),new SessionClock.Tick(Duration.ofSeconds(seconds).toNanos(),BASE.plusSeconds(seconds)),
                phases,List.of(),List.of(),List.of(),List.of(),List.of(),Optional.empty(),Optional.empty(),Optional.empty(),
                Optional.empty(),Optional.of(REF),0,0,true,List.of(),List.of(),List.of());
    }
    private static SessionController.BatchBoundary boundary(int count,BigInteger lastDate,boolean changed,boolean pending) {
        return new SessionController.BatchBoundary("software-batch",OWNER,
                count==0?Optional.empty():Optional.of(observed(DATE,1)),
                count==0?Optional.empty():Optional.of(observed(lastDate,2)),count,changed,pending);
    }
    private static boolean noProgress(BatchReport report,SessionController.BatchBoundary actual) {
        return RootOrdinaryWorkerLoop.noProgressAfterWall(report,Optional.of(actual),WALL);
    }
    @Test void completeZeroWorkTimeoutUsesActualStableDatesDespiteMetadataHead() {
        assertTrue(noProgress(report(BatchReport.Terminal.WALL_TIMEOUT,300,List.of()),boundary(2,DATE,false,false)));
        var result=new RootOrdinaryWorkerLoop.Result(Optional.of(report(BatchReport.Terminal.WALL_TIMEOUT,300,List.of())),
                29,RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,Optional.empty());
        assertFalse(RootOrdinaryWorkerMain.classifyFailureStop(result),"NO_PROGRESS must reach existing capture without a failure detail");
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,result.stopReason());
    }
    @Test void observedDateProgressAndAdvanceThenReturnDoNotBecomeNoProgress() {
        var report=report(BatchReport.Terminal.WALL_TIMEOUT,300,List.of());
        assertFalse(noProgress(report,boundary(2,DATE.add(BigInteger.valueOf(24)),true,false)));
        assertFalse(noProgress(report,boundary(3,DATE,true,false)),"an earlier real date change remains progress even if the latest date returns");
    }
    @Test void missingTypedBoundaryAndForeignBatchCannotProveNoProgress() {
        var report=report(BatchReport.Terminal.WALL_TIMEOUT,300,List.of());
        assertFalse(RootOrdinaryWorkerLoop.noProgressAfterWall(report,Optional.empty(),WALL));
        assertTrue(noProgress(report,boundary(0,DATE,false,false)),"date remains unknown; complete zero-dispatch wall bound may stop business");
        assertTrue(noProgress(report,boundary(1,DATE,false,false)),"one actual Ready must not force another empty full batch");
        var good=boundary(2,DATE,false,false);
        assertFalse(noProgress(report,new SessionController.BatchBoundary("other-batch",OWNER,good.firstObservation(),good.lastObservation(),2,false,false)));
        var other=new SessionIdentity(OWNER.machineId(),new GameGeneration(124,GAME.creationFiletime()),OWNER.sessionId());
        assertFalse(noProgress(report,new SessionController.BatchBoundary(report.batchId(),other,good.firstObservation(),good.lastObservation(),2,false,false)));
    }
    @Test void pendingUnknownActionOrActualActionSpanCannotBecomeNoProgress() {
        var report=report(BatchReport.Terminal.WALL_TIMEOUT,300,List.of());
        assertFalse(noProgress(report,boundary(2,DATE,false,true)));
        for(var phase:List.of(BatchReport.Phase.ACTION,BatchReport.Phase.ACTION_RECONCILIATION,BatchReport.Phase.CHECKPOINT)) {
            var tick=new SessionClock.Tick(0,BASE);
            var span=new BatchReport.PhaseSpan(phase,tick,tick,BatchReport.PhaseTerminal.RETURNED);
            assertFalse(noProgress(report(BatchReport.Terminal.WALL_TIMEOUT,300,List.of(span)),boundary(2,DATE,false,false)));
        }
        var unknown=report(BatchReport.Terminal.ACTION_UNKNOWN,300,List.of());
        assertFalse(noProgress(unknown,boundary(2,DATE,false,false)));
        assertTrue(RootOrdinaryWorkerMain.classifyFailureStop(new RootOrdinaryWorkerLoop.Result(Optional.of(unknown),29,
                RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,Optional.empty())));
    }
    @Test void partialWallAndNormalNonWallWaitAreNotTimeoutNoProgress() {
        assertFalse(noProgress(report(BatchReport.Terminal.WALL_TIMEOUT,299,List.of()),boundary(2,DATE,false,false)));
        assertFalse(noProgress(report(BatchReport.Terminal.TURN_BOUND,300,List.of()),boundary(2,DATE,false,false)));
        assertFalse(noProgress(report(BatchReport.Terminal.READINESS_TIMEOUT,60,List.of()),boundary(2,DATE,false,false)));
    }
    @Test void realControllerLateReadyBoundaryStopsTheActualLoopAfterOneFullBatch()throws Exception {
        for(boolean slow:List.of(false,true)) {
        var fixture=new Fixture(false,false,slow);var controller=fixture.controller();var completed=new ArrayList<BatchReport>();
        var loop=new RootOrdinaryWorkerLoop(configuration(),new RootOrdinaryWorkerLoop.Control(){
            public boolean stopRequested(){return false;}
            public void onBatchCompleted(BatchReport report,long next)throws IOException {
                completed.add(report);if(completed.size()>1)throw new IOException("fixture refuses a second empty batch");
            }
        });
        var actual=loop.run(()->new RootOrdinaryWorkerLoop.BatchCurrent(controller,controller::runBatch),28);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,actual.stopReason(),()->actual.failureDetail().orElse("no failure detail"));
        assertTrue(actual.failureDetail().isEmpty());assertEquals(29,actual.nextBatchSequence());assertEquals(1,completed.size());
        assertEquals(slow?1:2,fixture.observations);assertEquals(0,fixture.actions);assertEquals(BatchReport.Terminal.WALL_TIMEOUT,completed.getFirst().terminal());
        assertFalse(controller.isQuarantined());assertEquals(slow?1:2,controller.lastBatchBoundary().orElseThrow().observationCount());
        assertFalse(RootOrdinaryWorkerMain.classifyFailureStop(actual));
        }
    }
    @Test void realDateAdvanceAndObservedUnknownAreRetainedByController() {
        for(boolean unknown:List.of(false,true)) {
            var fixture=new Fixture(!unknown,unknown);var controller=fixture.controller();
            var actual=controller.runBatch(limits("observed-boundary"));var boundary=controller.lastBatchBoundary();
            assertEquals(2,boundary.orElseThrow().observationCount());
            if(unknown)assertTrue(boundary.orElseThrow().pendingAction());
            else assertTrue(boundary.orElseThrow().observedDateChanged());
            assertFalse(RootOrdinaryWorkerLoop.noProgressAfterWall(actual,boundary,WALL));
            assertSame(actual,controller.runBatch(limits("observed-boundary")),"same batch returns its original report");
            assertEquals(boundary,controller.lastBatchBoundary(),"returning a cached report must not clear its actual boundary");
            assertEquals(0,fixture.actions);
        }
    }
    private static RootOrdinaryWorkerLoop.Configuration configuration() {
        return new RootOrdinaryWorkerLoop.Configuration("software-loop",3,WALL,Duration.ofSeconds(60),Duration.ofSeconds(1),16);
    }
    private static BatchLimits limits(String id) {
        return new BatchLimits(id,3,WALL,Duration.ofSeconds(60),Duration.ofSeconds(1),16);
    }
    private static final class TestClock implements SessionClock {
        long nanos;
        public Tick now(){return new Tick(nanos,BASE.plusNanos(nanos));}
        public void waitFor(Duration duration){nanos+=duration.toNanos();}
    }
    /** Reuses the no-files/no-SAVE/no-action ports of SessionControllerObservationDeadlineTest. */
    private static final class Fixture {
        final TestClock clock=new TestClock();final boolean advance,unknown,slowPlanning;int observations,actions;
        Fixture(boolean advance,boolean unknown){this(advance,unknown,false);}
        Fixture(boolean advance,boolean unknown,boolean slowPlanning){this.advance=advance;this.unknown=unknown;this.slowPlanning=slowPlanning;}
        private Ready observe(SessionIdentity owner,Instant until) {
            assertEquals(OWNER,owner);observations++;
            var identity=observed(observations>1&&advance?DATE.add(BigInteger.valueOf(24)):DATE,observations);
            var snapshot=new OpportunityJson.Obj(java.util.Map.ofEntries(
                    java.util.Map.entry("paused",new OpportunityJson.Bool(true)),java.util.Map.entry("map_ready",new OpportunityJson.Bool(true)),
                    java.util.Map.entry("revision",new OpportunityJson.IntegerValue(BigInteger.valueOf(observations))),
                    java.util.Map.entry("native_revision",new OpportunityJson.IntegerValue(BigInteger.valueOf(observations))),
                    java.util.Map.entry("date_raw",new OpportunityJson.IntegerValue(identity.frame().identity().dateRaw())),
                    java.util.Map.entry("snapshot_id",new OpportunityJson.Text(identity.frame().snapshotId())),
                    java.util.Map.entry("episode_run_id",new OpportunityJson.Text(identity.frame().episodeRunId())),
                    java.util.Map.entry("played_character",new OpportunityJson.Obj(java.util.Map.of("character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(31254))))),
                    java.util.Map.entry("active_wars",new OpportunityJson.Arr(List.of())),java.util.Map.entry("player_armies",new OpportunityJson.Arr(List.of()))));
            List<ExternalFact> facts=unknown?List.of(new ExternalFact("software-original-unknown","b".repeat(64),identity,
                    ExternalState.UNKNOWN,UnknownScope.GLOBAL,org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.marriage,
                    new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),REF)):List.of();
            var input=new PlanningRequest(identity,new G2Source(OWNER.machineId(),BASE.toString(),"SOFTWARE-FIXTURE",REF),OWNER.sessionId(),until,
                    new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),facts,Optional.empty(),Optional.empty(),false));
            if(observations>1)clock.nanos=WALL.toNanos();
            return new Ready(input,CheckpointEligibility.UNAVAILABLE,Optional.empty(),Optional.empty());
        }
        SessionController controller() {
            CheckpointFiles files=new CheckpointFiles(){
                public Optional<CheckpointPair.FileWitness> observe(Path path){throw unused();}
                public byte[] read(CheckpointPair.FileWitness witness,int max){throw unused();}
                public CheckpointPair.FileWitness replace(Path path,byte[] raw){throw unused();}
                public CheckpointPair.FileWitness createNew(Path path,byte[] raw){throw unused();}
                public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source,Path target){throw unused();}
            };
            var snapshots=new DriverCheckpointStore.SnapshotSupplier(){public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw unused();}};
            var drivers=new DriverCheckpointStore(files,Path.of("D:/fixture/unused-Driver.json"),"no-progress-only",snapshots);
            CheckpointRequest.ObservationPort noCheckpoint=until->{throw unused();};
            var saves=new CheckpointService(files,drivers,noCheckpoint,Path.of("D:/fixture/unused-evidence"),Clock.fixed(BASE,ZoneOffset.UTC),(pair,receipt)->{throw unused();});
            var requests=new CheckpointRequestFactory(Path.of("D:/fixture/unused.ck3"),noCheckpoint);
            var realm=new RealmLifecycle(REF);
            var policies=java.util.Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
                if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
                return new OrdinaryPolicy(){public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return REF;}
                    public Decision evaluate(PlanningRequest input,Draft previous){
                        if(stage==PlanningStage.ORDINARY_CORE&&slowPlanning)clock.nanos=WALL.toNanos();
                        return stage==PlanningStage.ORDINARY_CORE?new Wait("software ordinary waiting"):new Keep("unrelated software stage");}};
            }).toList();
            var planner=new OrdinaryPlanner(policies,Clock.fixed(BASE,ZoneOffset.UTC),realm);
            var noActions=new ActionCoordinatorPort(){public ActionReceipt execute(ActionCommand command){actions++;throw unused();}
                public ActionReceipt reconcile(String actionId){actions++;throw unused();}};
            var scope=new OrdinaryPlanCompletion.PlanningScope(){
                public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
                public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult planned){return new OrdinaryPlanCompletion.Unchanged("software no publication");}
                public ExecutionDisposition afterExecution(ActionReceipt receipt){throw unused();}
            };
            var controller=new SessionController(OWNER,(owner,until)->new GameLifecycle.Running(GAME,REF),this::observe,
                    planner,noActions,saves,requests,input->new JournalCommit(REF,0),work->{throw unused();},clock,Optional.empty(),0,scope,
                    (owner,receipt,until)->{throw unused();});
            controller.bindRetainedIncidents(List::of);return controller;
        }
        private static AssertionError unused(){return new AssertionError("software no-progress fixture reached action, checkpoint or transport");}
    }
}
