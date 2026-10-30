package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Field;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.session.SessionPorts.JournalInput;
import org.xar.ck3.control.application.session.SessionPorts.JournalKind;

/** Relocated actual event1..42 topology; an unfinished read-only batch gains no invented terminal event. */
final class SettledOpenBatchRecoveryRegressionTest {
    @TempDir Path temporary;

    @Test void actualOpen42RecoversAndStartsBatchFourWithoutInventingAClosedBatchOrAction() throws Exception {
        var fixture=new SettledSameGameRecoveryRegressionTest.Fixture(PortableSettledFixture.materialize42(temporary));
        var data=fixture.read();var controller=data.controller();
        assertEquals(42,data.canonicalSequence());assertEquals(ContinuityState.Status.RUNNING,fixture.current.status());
        assertEquals(4,controller.nextBatchSequence());assertEquals(4,controller.usedBatches().size());
        String prefix=controller.batchPrefix();
        assertEquals(Set.of(prefix+"-0",prefix+"-1",prefix+"-2",prefix+"-3"),controller.usedBatches());
        var priorBoundary=fixture.current.toJson().get("java_ordinary_batch_boundary").deepCopy();
        assertEquals("BATCH_STARTED",priorBoundary.path("boundary").textValue());assertEquals(prefix+"-3",priorBoundary.path("batch_id").textValue());
        var priorCycle=fixture.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).deepCopy();
        var priorActions=fixture.current.toJson().get(ContinuityActionJournal.STATE_FIELD).deepCopy();
        assertEquals(1,data.settledActions().size());assertEquals(1,controller.unsavedGameplayActions().size());
        assertTrue(controller.dirty());assertTrue(controller.savedPair().isEmpty());
        assertFalse(controller.localUnresolved());assertFalse(controller.quarantined());assertEquals(0,fixture.commits);

        var fresh=fixture.semantic(data,0,0,1);fixture.allow(fresh);
        var recovery=fixture.locked(same->fixture.journal.recoverSettledSameGame(same,data,fresh));
        assertTrue(recovery.isPresent(),"an actually open read-only batch needs the real recovery commit");
        assertEquals(43,fixture.current.sequence());assertEquals(1,fixture.commits);
        assertEquals(OrdinaryCycleTransitions.CYCLE_KIND,fixture.lastPrepared.request().kind());
        assertEquals("SETTLED_SAME_GAME_RECOVERY",fixture.lastPrepared.request().detailsObject().path("operation").textValue());
        assertTrue(ContinuityJson.same(priorBoundary,fixture.current.toJson().get("java_ordinary_batch_boundary")),
                "recovery must not fabricate BATCH_INTERRUPTED, DEFERRED or FINISHED");
        assertTrue(ContinuityJson.same(priorCycle,fixture.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD)));
        var restored=fixture.controller(data.source().sourceRef());
        fixture.locked(same->{restored.restoreSettledSameGame(same,data);return null;});
        assertEquals(controller.usedBatches(),field(restored,"usedBatches"));
        assertEquals(controller.unsavedGameplayActions(),field(restored,"unsavedGameplayActions"));
        assertEquals(true,field(restored,"dirty"));assertTrue(restored.savedPair().isEmpty());

        fixture.acceptedBatchBoundaries=Set.of(JournalKind.BATCH_STARTED.name());
        fixture.locked(same->fixture.journal.commit(same,new JournalInput(fixture.owner,prefix+"-4",JournalKind.BATCH_STARTED,
                Optional.of(fresh.frame()),Optional.empty(),Optional.empty(),List.of())));
        assertEquals(44,fixture.current.sequence());assertEquals(2,fixture.commits);
        assertEquals(OrdinaryCycleTransitions.BATCH_KIND,fixture.lastPrepared.request().kind());
        assertEquals("BATCH_STARTED",fixture.lastPrepared.request().detailsObject().path("boundary").textValue());
        assertEquals(prefix+"-4",fixture.lastPrepared.request().detailsObject().path("batch_id").textValue());
        assertTrue(ContinuityJson.same(priorCycle,fixture.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD)));
        assertTrue(ContinuityJson.same(priorActions,fixture.current.toJson().get(ContinuityActionJournal.STATE_FIELD)));
        var suffix=fixture.history().stream().filter(edge->edge.sequence()>42).toList();
        assertEquals(2,suffix.size());
        assertEquals(List.of(OrdinaryCycleTransitions.CYCLE_KIND,OrdinaryCycleTransitions.BATCH_KIND),suffix.stream().map(WriterContracts.HistoricalTransition::kind).toList());
        fixture.assertNoCredit();
    }

    @Test void recoveredOpenBatchReadyReentryAddsNoSecondRecoveryBeforeStartingFour() throws Exception {
        var fixture=new SettledSameGameRecoveryRegressionTest.Fixture(PortableSettledFixture.materialize42(temporary));
        var data=fixture.read();String prefix=data.controller().batchPrefix();
        var fresh=fixture.semantic(data,0,0,1);fixture.allow(fresh);
        assertTrue(fixture.locked(same->fixture.journal.recoverSettledSameGame(same,data,fresh)).isPresent());
        fixture.newJournal();var ready=fixture.read();
        assertEquals(43,ready.canonicalSequence());assertEquals(4,ready.controller().nextBatchSequence());
        assertTrue(ready.controller().usedBatches().contains(prefix+"-3"));
        var newer=fixture.semantic(ready,0,0,1);fixture.allow(newer);
        byte[] before=fixture.current.canonicalBytes();
        assertTrue(fixture.locked(same->fixture.journal.recoverSettledSameGame(same,ready,newer)).isEmpty());
        assertEquals(1,fixture.commits);assertArrayEquals(before,fixture.current.canonicalBytes());
        fixture.acceptedBatchBoundaries=Set.of(JournalKind.BATCH_STARTED.name());
        fixture.locked(same->fixture.journal.commit(same,new JournalInput(fixture.owner,prefix+"-4",JournalKind.BATCH_STARTED,
                Optional.of(newer.frame()),Optional.empty(),Optional.empty(),List.of())));
        assertEquals(44,fixture.current.sequence());assertEquals(2,fixture.commits);fixture.assertNoCredit();
    }

    private static Object field(SessionController controller,String name) throws ReflectiveOperationException {
        Field field=SessionController.class.getDeclaredField(name);field.setAccessible(true);return field.get(controller);
    }
}
