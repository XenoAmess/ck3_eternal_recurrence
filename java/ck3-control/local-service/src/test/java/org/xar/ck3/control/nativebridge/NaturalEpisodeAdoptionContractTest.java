package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.*;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Actual software canonical receipts establish negative admission boundaries; they do not mint a natural/M3 issuer. */
public final class NaturalEpisodeAdoptionContractTest {
    @TempDir Path temporary;
    @Test void realCanonicalSaveAndCycleDataCannotSubstituteForPrivateEpisodeAdmission()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("ordinary-is-not-natural"),false)) {
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request)).action();
            assertTrue(saved.settled());AtomicInteger legacyCalls=new AtomicInteger();
            EpisodeContinuation dataOnly=(owner,parent,deadline)->{legacyCalls.incrementAndGet();return f.proof;};
            var controller=controller(f,dataOnly);byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            assertEquals(f.proof,dataOnly.continueSameGame(f.owner,saved,Instant.now().plusSeconds(10)));
            assertThrows(IOException.class,()->dataOnly.continueAdmittedSameGame(f.owner,saved,Instant.now().plusSeconds(10)));
            assertEquals(1,legacyCalls.get(),"strong default must not call a constructible legacy DATA proof producer");
            assertTrue(controller.naturalEpisodeAdoption(saved).isEmpty());
            assertTrue(controller.naturalEpisodeAdoption(f.actual.archive.loadReceipt(f.actual.archive.receiptReferenceOf(saved))).isEmpty());
            assertTrue(controller.savedPair().isEmpty());assertTrue(controller.lastReport().isEmpty());
            assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());assertArrayEquals(ledger,f.actual.ledgerBytes());
        }
    }
    @Test void originalUnknownAndItsColdCanonicalReceiptNeverBecomeAnAcceptedNaturalEpisode()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("unknown"),true)) {
            assertInstanceOf(CheckpointResult.Unknown.class,f.service.checkpoint(f.request));
            var receipt=f.actual.coordinator.execute(f.request.saveCommand());
            assertNotNull(receipt);assertFalse(receipt.settled());
            EpisodeContinuation denied=(owner,parent,deadline)->{throw new AssertionError("UNKNOWN cannot continue");};
            var controller=controller(f,denied);byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            assertTrue(controller.naturalEpisodeAdoption(receipt).isEmpty());
            var cold=f.actual.reopenAndReturnExisting(f.request.saveCommand());
            assertFalse(cold.settled());assertTrue(controller.naturalEpisodeAdoption(cold).isEmpty());
            assertThrows(IOException.class,()->denied.continueAdmittedSameGame(f.owner,receipt,Instant.now().plusSeconds(10)));
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
        }
    }
    /** Genuine Root callers supply their existing completed input; this helper never manufactures an admission or proof. */
    public static void requireActualAdoption(SessionController actual,ContinuityBatchJournal journal,
            ContinuityStorePort.Session same,ActionReceipt exactParent)throws IOException {
        var accepted=actual.naturalEpisodeAdoption(exactParent).orElseThrow(()->new IOException("same Controller has not adopted this exact natural parent"));
        assertArrayEquals(ActionCodec.encodeCommand(exactParent.command()),ActionCodec.encodeCommand(accepted.parent().command()));
        assertEquals(accepted.owner(),accepted.admission().owner());
        assertEquals(0,accepted.admission().newSavedDayCredit());assertEquals(0,accepted.admission().newCompletedCycleCredit());
        String before=same.head().digest();journal.requireHistoricalEpisodeAdoption(same,accepted.admission());
        journal.requireHistoricalEpisodeAdoption(same,accepted.admission());assertEquals(before,same.head().digest());
    }
    private static SessionController controller(CheckpointSourceCompositionTest.Fixture f,EpisodeContinuation episodes) {
        var planner=new OrdinaryPlanner(List.of(),Clock.systemUTC(),new RealmLifecycle(f.request.saveCommand().source().sourceRef()));
        var scope=new OrdinaryPlanCompletion.PlanningScope(){
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
            @Override public PlanningDisposition afterPlanning(PlanningRequest request,PlanningResult result){throw new AssertionError("no planning");}
            @Override public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no dispatch");}
        };
        SessionClock clock=new SessionClock(){
            @Override public Tick now(){return new Tick(0,Instant.now());}
            @Override public void waitFor(Duration duration){throw new AssertionError("no wait");}
        };
        CheckpointRequest.ObservationPort read=until->{throw new AssertionError("no SAVE");};
        return new SessionController(f.owner,(owner,until)->new GameLifecycle.Running(owner.game(),f.request.saveCommand().source().sourceRef()),
                (owner,until)->{throw new AssertionError("no ordinary Ready");},planner,f.actual.coordinator,f.service,
                new CheckpointRequestFactory(f.request.expectedSavePath(),read),f.batch,work->{throw new AssertionError("no analysis");},
                clock,Optional.empty(),0,scope,episodes);
    }
}
