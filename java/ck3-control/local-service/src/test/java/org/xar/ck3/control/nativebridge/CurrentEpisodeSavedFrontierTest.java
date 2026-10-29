package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Actual canonical SAVE/current Cycle into the shared dirty-frontier producer. No natural/M3 ticket is manufactured. */
public final class CurrentEpisodeSavedFrontierTest {
    @TempDir Path temporary;
    private static PublicCheckpointMaterialCapture.Captured save(CheckpointSourceCompositionTest.Fixture f)throws Exception {
        var producer=new PublicCheckpointMaterialCapture(f.actual.writer,f.batch,f.materials,new ActionSnapshotReader(f.actual.journal));
        var pending=f.actual.writer.locked(same->producer.begin(same,f.owner,f.proof.semantic(),f.request));
        var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
        return f.actual.writer.locked(same->producer.confirm(same,pending,confirmed));
    }
    @Test void realSavedFrontierIsCleanButAnActualLaterCompletedCycleRemainsDirty()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("real-frontier"),false)) {
            var initial=f.actual.writer.locked(same->f.batch.currentSavedFrontier(same,f.owner,f.proof));
            assertTrue(initial.checkpointRequired());assertTrue(initial.pair().isEmpty());
            var saved=save(f);var after=f.actual.ready();
            var savedProof=f.batch.cycleProof(f.owner,after.semanticEvidence().orElseThrow()).orElseThrow();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();byte[] ledger=f.actual.ledgerBytes();
            var clean=f.actual.writer.locked(same->f.batch.currentSavedFrontier(same,f.owner,savedProof));
            assertFalse(clean.checkpointRequired());assertEquals(Optional.of(saved.pair()),clean.pair());
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
            var action=f.actual.coordinator.execute(f.actual.command("after-real-saved-frontier"));
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,action.outcome());
            assertTrue(action.visibleGameplay());
            var unsavedAction=f.actual.writer.locked(same->f.batch.currentSavedFrontier(same,f.owner,savedProof));
            assertTrue(unsavedAction.checkpointRequired(),"a real unsaved gameplay action cannot be hidden by unchanged cycle count/date");
            f.batch.retainCycle(f.owner,action);var fresh=f.actual.ready();
            var current=f.batch.settleCycle(f.owner,action,fresh.semanticEvidence().orElseThrow());
            writes=f.actual.nativeActionWrites();reads=f.actual.nativeReadWrites();ledger=f.actual.ledgerBytes();
            var dirty=f.actual.writer.locked(same->f.batch.currentSavedFrontier(same,f.owner,current));
            assertTrue(dirty.checkpointRequired(),"same actor/run cannot erase a genuinely later unsaved completed Cycle");
            assertEquals(Optional.of(saved.pair()),dirty.pair(),"DATA keeps the actual saved pair; it never replaces it from an unsaved SEM");
            f.actual.writer.locked(same->{assertThrows(IllegalArgumentException.class,()->f.batch.currentSavedFrontier(same,f.owner,f.proof));return null;});
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
        }
    }
    @Test void constructedWrongCycleDigestAndForeignOwnerCannotProveACleanCanonicalFrontier()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("wrong-proof"),false)) {
            save(f);var fresh=f.actual.ready();
            var real=f.batch.cycleProof(f.owner,fresh.semanticEvidence().orElseThrow()).orElseThrow();
            byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            var fake=new CompletedCycleProof(real.completedCycles(),real.semantic(),"0".repeat(64));
            var foreign=new SessionIdentity(f.owner.machineId(),f.owner.game(),f.owner.sessionId()+"-foreign");
            f.actual.writer.locked(same->{
                assertThrows(IllegalArgumentException.class,()->f.batch.currentSavedFrontier(same,f.owner,fake));
                assertThrows(IllegalArgumentException.class,()->f.batch.currentSavedFrontier(same,foreign,real));return null;
            });
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
        }
    }
    /** Real NS/M7 input assertions. The actual Root/private source must supply this input; this is not an admission factory. */
    public static void requireActualCurrentAdoption(ContinuityBatchJournal journal,ContinuityStorePort.Session same,
            LifecycleEpisodeInputs.CurrentAdoptionBinding current)throws IOException {
        String head=same.head().digest();current.requireCurrent(same);current.historical().requireCurrent(same);
        var admitted=journal.admitCurrentEpisode(same,current);
        assertFalse(admitted.newBinding());assertEquals(current.historical().origin(),admitted.origin());
        assertEquals(0,admitted.newSavedDayCredit());assertEquals(0,admitted.newCompletedCycleCredit());
        var frontier=journal.currentSavedFrontier(same,current.owner(),admitted.proof());
        assertEquals(frontier.checkpointRequired(),admitted.checkpointRequired());assertEquals(frontier.pair(),admitted.savedFrontier());
        journal.requireHistoricalEpisodeAdoption(same,admitted);assertEquals(head,same.head().digest());
    }
    /** Called only after the actual original Controller turn; never invokes a replacement turn or clears isolation. */
    public static void requireActualControllerAdoption(SessionController controller,ContinuityBatchJournal journal,
            ContinuityStorePort.Session same,ActionReceipt exactParent)throws IOException {
        var accepted=controller.naturalEpisodeAdoption(exactParent).orElseThrow(()->new IOException("real Controller has not accepted this original episode"));
        String head=same.head().digest();journal.requireHistoricalEpisodeAdoption(same,accepted.admission());
        assertArrayEquals(ActionCodec.encodeCommand(exactParent.command()),ActionCodec.encodeCommand(accepted.parent().command()));
        assertEquals(0,accepted.admission().newSavedDayCredit());assertEquals(0,accepted.admission().newCompletedCycleCredit());
        if(accepted.admission().checkpointRequired())assertTrue(controller.lastReport().orElseThrow().dirtySinceSave());
        assertEquals(head,same.head().digest());
    }
}
