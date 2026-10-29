package org.xar.ck3.control.service.root;

import java.util.Objects;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.session.BatchReport;
import static org.junit.jupiter.api.Assertions.*;

/** Production Main -> Staged.finish -> Controller -> retained planned SAVE.
 * Only genuine RootStartupInputsProducer.Actual objects qualify; absent native scenarios are NOT_RUN. */
public final class RootControllerPlannedCheckpointActualTest {
    public enum Scenario { CONFIRMED_PLANNED_SAVE, UNKNOWN_PLANNED_SAVE }
    public interface InputsProducer {
        void withActualInputs(Scenario scenario, RootStartupInputsProducer.Work work) throws Exception;
    }
    private static void actual(Scenario scenario, RootStartupInputsProducer.Work work) throws Exception {
        var producers = ServiceLoader.load(InputsProducer.class).stream().toList();
        if (producers.size() != 1) throw new IllegalStateException("MISSING_ACTUAL_ROOT_PLANNED_SAVE_INPUTS_NOT_RUN: " + scenario);
        boolean[] entered = {false};
        producers.getFirst().get().withActualInputs(scenario, input -> {
            assertFalse(entered[0], "one original production Main lifetime per scenario"); entered[0] = true;
            Objects.requireNonNull(input); var current = input.core().sessionAccess().current();
            assertSame(input.original(), current); assertSame(current, input.catalogFor(current).context().actions());
            work.consume(input);
        });
        assertTrue(entered[0], "actual provider must enter the original admitted Root lifetime");
    }
    private static ActionReceipt selectedSave(BatchReport report) {
        assertEquals(1, report.turns().size(), "actual native scenario must select exactly one planned SAVE");
        assertTrue(report.lifecycleTurns().isEmpty());
        var turn = report.turns().getFirst(); var receipt = turn.receipt();
        assertEquals("save-checkpoint", receipt.command().operation().value());
        assertFalse(turn.facts().visibleGameplay()); assertFalse(turn.facts().eligibleAdvance());
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        return receipt;
    }
    @Test void actualOrdinaryControllerSaveCommitsItsMaterialAndAdoptsTheSamePhysicalPair() throws Exception {
        actual(Scenario.CONFIRMED_PLANNED_SAVE, input -> {
            var root = input.original(); var report = root.autoTurn(input.deadline()).execution();
            var receipt = selectedSave(report);
            assertEquals(BatchReport.Terminal.TURN_BOUND, report.terminal());
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, receipt.outcome()); assertTrue(receipt.settled());
            var pair = report.lastSavedPair().orElseThrow(); assertEquals(receipt.command().actionId(), pair.saveActionId());
            assertEquals(pair, CheckpointPairCodec.decode(CheckpointPairCodec.encode(pair)));
            assertFalse(report.dirtySinceSave()); assertEquals(0, report.eligibleAdvancesSinceSave());
            root.withPublicStandaloneRead(input.deadline(), same -> {
                assertSame(root.writer(), input.core().writer()); assertSame(root.archive(), input.core().archive());
                var material = root.savedMaterials().currentPhysical(same, pair); material.requirePhysical(same);
                assertEquals(SavedCheckpointMaterial.Kind.ORDINARY, material.kind());
                assertEquals(receipt.command().before(), material.sourceSemantic().frame()); assertEquals(pair, material.pair());
                var original = input.core().actions().withFrozen(same, frozen -> frozen.find(receipt.command().actionId()).orElseThrow());
                assertEquals(receipt, original);
                var scoped = root.archive().withSession(same);
                assertEquals(receipt, ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt, scoped), scoped));
                return null;
            });
            input.closeOriginal();
            var closed=assertThrows(java.io.IOException.class,input::readInputs);
            assertEquals("original Root startup lifetime is CLOSED; no new retained inputs",closed.getMessage());
            assertThrows(java.io.IOException.class,()->input.catalogFor(root));
        });
    }
    @Test void actualUnknownControllerSaveQueriesOnlyItsRetainedAttemptWithoutAnotherSave() throws Exception {
        actual(Scenario.UNKNOWN_PLANNED_SAVE, input -> {
            var root = input.original(); var report = root.autoTurn(input.deadline()).execution();
            var original = selectedSave(report);
            assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, report.terminal()); assertFalse(original.settled());
            assertNotEquals(original.command().actionId(), report.lastSavedPair().orElseThrow().saveActionId());
            var queried = root.reconcile(original.command().actionId());
            assertArrayEquals(ActionCodec.encodeCommand(original.command()), ActionCodec.encodeCommand(queried.command()));
            assertEquals(ActionTransitions.attempt(original.state()), ActionTransitions.attempt(queried.state()));
            assertEquals(ActionTransitions.dispatch(original.state()), ActionTransitions.dispatch(queried.state()));
            root.withPublicStandaloneRead(input.deadline(), same -> {
                var retained = input.core().actions().withFrozen(same, frozen -> frozen.find(original.command().actionId()).orElseThrow());
                assertEquals(queried, retained);
                var scoped = root.archive().withSession(same);
                assertEquals(retained, ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(retained, scoped), scoped));
                return null;
            });
        });
    }
}
