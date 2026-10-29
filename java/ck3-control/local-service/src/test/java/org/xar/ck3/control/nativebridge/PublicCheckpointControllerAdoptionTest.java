package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Real software SAVE/canonical writer/private material into Controller. No Managed/Root admission is fabricated. */
public final class PublicCheckpointControllerAdoptionTest {
    @TempDir Path temporary;
    private static PublicCheckpointMaterialCapture.Captured capture(CheckpointSourceCompositionTest.Fixture f)throws Exception {
        var producer=new PublicCheckpointMaterialCapture(f.actual.writer,f.batch,f.materials,new ActionSnapshotReader(f.actual.journal));
        var pending=f.actual.writer.locked(same->producer.begin(same,f.owner,f.proof.semantic(),f.request));
        var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
        var result=f.actual.writer.locked(same->producer.confirm(same,pending,confirmed));
        assertArrayEquals(ActionCodec.encodeCommand(f.request.saveCommand()),ActionCodec.encodeCommand(result.originalCommand()));
        assertEquals(confirmed.action(),result.originalReceipt());assertTrue(result.originalReceipt().settled());
        return result;
    }
    @Test void actualPrivateCaptureUpdatesOriginalControllerWithoutSavingOrCommittingAgain()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("adopt"),false)) {
            var actual=capture(f);var controller=controller(f,f.batch,false);
            int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();byte[] ledger=f.actual.ledgerBytes();
            assertTrue(controller.savedPair().isEmpty());assertTrue(controller.lastReport().isEmpty());
            f.actual.writer.locked(same->{controller.acceptPublicCheckpoint(same,actual,Instant.now().plusSeconds(10));return null;});
            assertEquals(Optional.of(actual.pair()),controller.savedPair());assertFalse(controller.isRunning());assertFalse(controller.isQuarantined());
            controller.acceptPublicCheckpoint(actual,Instant.now().plusSeconds(10));
            assertEquals(Optional.of(actual.pair()),controller.savedPair());assertTrue(controller.lastReport().isEmpty());
            assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());assertArrayEquals(ledger,f.actual.ledgerBytes());
            assertEquals(actual.journalCommit(),f.actual.writer.locked(same->f.batch.acceptPublicCheckpoint(same,f.owner,actual)));
        }
    }
    @Test void defaultJournalCannotAdoptARealCaptureWithoutItsPrivateIssuerQualification()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("default-deny"),false)) {
            var actual=capture(f);BatchJournal refusing=input->{throw new AssertionError("no replacement boundary");};
            var controller=controller(f,refusing,false);byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites();
            assertThrows(IOException.class,()->controller.acceptPublicCheckpoint(actual,Instant.now().plusSeconds(10)));
            assertTrue(controller.savedPair().isEmpty());assertFalse(controller.isRunning());assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());
        }
    }
    @Test void unrelatedLocalWriterUnknownCannotBeClearedByActualLatestPrivateCapture()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("other-unknown"),false)) {
            var actual=capture(f);var controller=controller(f,f.batch,true);
            var report=controller.runBatch(new BatchLimits("unrelated-observation-failure",1,Duration.ofSeconds(3),Duration.ofSeconds(1),Duration.ofMillis(5),3));
            assertEquals(BatchReport.Terminal.WRITER_UNKNOWN,report.terminal());assertTrue(controller.isQuarantined());
            byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            assertThrows(IllegalArgumentException.class,()->controller.acceptPublicCheckpoint(actual,Instant.now().plusSeconds(10)));
            assertTrue(controller.savedPair().isEmpty());assertTrue(controller.isQuarantined());assertFalse(controller.isRunning());
            assertEquals(Optional.of(report),controller.lastReport());assertArrayEquals(ledger,f.actual.ledgerBytes());
            assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
        }
    }
    @Test void expiredOrRetiredControllerCannotAdoptRealCapture()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("expired"),false)) {
            var actual=capture(f);var controller=controller(f,f.batch,false);byte[] ledger=f.actual.ledgerBytes();
            assertThrows(IllegalArgumentException.class,()->controller.acceptPublicCheckpoint(actual,Instant.EPOCH));
            assertTrue(controller.savedPair().isEmpty());controller.retire();
            assertThrows(IllegalArgumentException.class,()->controller.acceptPublicCheckpoint(actual,Instant.now().plusSeconds(10)));
            assertTrue(controller.savedPair().isEmpty());assertFalse(controller.isRunning());assertArrayEquals(ledger,f.actual.ledgerBytes());
        }
    }
    @Test void samePrivateOriginalCaptureCanBeAdoptedAfterExpiredIdleAttemptWithNoRepeatSave()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("late-adoption"),false)) {
            var actual=capture(f);var controller=controller(f,f.batch,false);
            byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            assertThrows(IllegalArgumentException.class,()->controller.acceptPublicCheckpoint(actual,Instant.EPOCH));
            assertTrue(controller.savedPair().isEmpty());assertFalse(controller.isRunning());
            assertEquals(actual.originalReceipt().command(),actual.originalCommand());
            assertEquals(actual.pair().saveActionId(),actual.originalReceipt().command().actionId());
            controller.acceptPublicCheckpoint(actual,Instant.now().plusSeconds(10));
            assertEquals(Optional.of(actual.pair()),controller.savedPair());assertFalse(controller.isQuarantined());
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
        }
    }
    @Test void realCanonicalCycleAnchorIsCheckedBeforeOperatorWithoutNativeOrWriterMutation()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("operator-before"),false)) {
            var saved=capture(f);
            var action=f.actual.coordinator.execute(f.actual.command("real-cycle-anchor"));
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,action.outcome());
            f.batch.retainCycle(f.owner,action);var fresh=f.actual.ready();
            f.batch.settleCycle(f.owner,action,fresh.semanticEvidence().orElseThrow());
            var driver=new FrozenDriverSnapshotSupplier(f.actual.driverAuthority()).withFrozen((snapshot,publisher)->assertInstanceOf(DriverStateSnapshot.Complete.class,snapshot));
            var date=fresh.request().before().frame().identity().dateRaw();
            byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            f.actual.writer.locked(same->{
                f.batch.requireOperatorBefore(same,f.owner,driver,date);
                var session=driver.session();
                for(var changed:List.of(new DriverStateSnapshot.Session(session.pipeName(),session.bridgePid(),session.actorId().add(java.math.BigInteger.ONE),session.episodeRunId()),
                        new DriverStateSnapshot.Session(session.pipeName(),session.bridgePid(),session.actorId(),session.episodeRunId()+"-other"))) {
                    var wrong=new DriverStateSnapshot.Complete(changed,driver.commandHistory(),driver.lastCheckpoint(),driver.rollbackWarFailure(),
                            driver.managedRestoreTransaction(),driver.successionExpectation(),driver.successionLifecycle(),driver.campaignGoal(),driver.rollbackWarFailures());
                    assertThrows(IllegalArgumentException.class,()->f.batch.requireOperatorBefore(same,f.owner,wrong,date));
                }
                assertThrows(IllegalArgumentException.class,()->f.batch.requireOperatorBefore(same,f.owner,driver,date.subtract(java.math.BigInteger.ONE)));
                assertThrows(IllegalArgumentException.class,()->f.batch.acceptPublicCheckpoint(same,f.owner,saved),"actual later unsaved cycle prevents stale SAVE adoption");
                return null;
            });
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
        }
    }
    private static SessionController controller(CheckpointSourceCompositionTest.Fixture f,BatchJournal journal,boolean failLifecycle) {
        var realm=new RealmLifecycle(f.request.saveCommand().source().sourceRef());
        var planner=new OrdinaryPlanner(List.of(),Clock.systemUTC(),realm); // Never plans; no fabricated migration roster.
        var scope=new OrdinaryPlanCompletion.PlanningScope(){
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException {return new ScopeResult<>(work.run(),Optional.empty());}
            @Override public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult result){throw new AssertionError("adoption does not plan");}
            @Override public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("adoption does not dispatch");}
        };
        SessionClock clock=new SessionClock(){
            final long began=System.nanoTime();
            @Override public Tick now(){return new Tick(System.nanoTime()-began,Instant.now());}
            @Override public void waitFor(Duration duration){throw new AssertionError("adoption does not wait");}
        };
        LifecyclePort life=(owner,until)->{if(failLifecycle)throw new IOException("separate observation failure, not the captured SAVE");return new GameLifecycle.Running(f.owner.game(),f.request.saveCommand().source().sourceRef());};
        CheckpointRequest.ObservationPort checkpointRead=until->{throw new AssertionError("adoption must not SAVE");};
        var controller = new SessionController(f.owner,life,(owner,until)->{throw new AssertionError("adoption must not observe ordinary Ready");},planner,f.actual.coordinator,f.service,
                new CheckpointRequestFactory(f.request.expectedSavePath(),checkpointRead),journal,
                work->{throw new AssertionError("no incident work captured");},clock,Optional.empty(),0,scope,
                (owner,receipt,deadline)->{throw new AssertionError("adoption is not an episode transition");});
        controller.bindRetainedIncidents(List::of); // This SAVE-only software fixture has no incident journal.
        return controller;
    }
}
