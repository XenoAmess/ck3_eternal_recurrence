package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Actual writer, original ACTION ACK and cold UNKNOWN; malformed control DATA never grants pause or gameplay credit. */
final class PauseControlCanonicalWriterFailureTest {
    @TempDir Path root;
    private static ActionWriterIntegrationFixture.SoftwareActionScenario scenario() {
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
                (command, attempt, dispatch) -> new ActionPorts.PauseObserved(new ActionState.EffectObservation(
                        command.before(), command.source(), command.sessionId(), PauseConfirmation.OBSERVER,
                        PauseConfirmation.actualValues(), new ObservationProvenance.Query("unqualified-old-query"),
                        Instant.now(), attempt.guard().nativeEvidence(), List.of(attempt.guard().nativeEvidence()))), () -> { });
    }
    private void rejectOriginal(String name, boolean claimGameplay) throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve(name), false, scenario())) {
            var initial = actual.command("original-" + name);
            var values = new ArrayList<>(PauseConfirmation.expectedValues());
            if (claimGameplay) values.add(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true));
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, initial.before(), initial.source(), PauseConfirmation.OBSERVER, values);
            var command = new ActionCommand(initial.actionId(), initial.before(), initial.source(), initial.sessionId(), initial.operation(),
                    initial.arguments(), expected, initial.claims(), initial.deadline());
            var retained = actual.coordinator.execute(command);
            var unknown = assertInstanceOf(ActionState.Unknown.class, retained.state());
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, unknown.dispatch().orElseThrow());
            assertTrue(ack.nativeOk()); assertTrue(ack.outbound().isPresent()); assertTrue(ack.custody().isPresent());
            ack.custody().orElseThrow().verify(ack, unknown.attempt().orElseThrow().guard());
            assertEquals(1, actual.nativeActionWrites());
            assertFalse(retained.settled()); assertFalse(retained.visibleGameplay()); assertFalse(retained.eligibleAdvance()); assertTrue(retained.applied().isEmpty());
            var ref = actual.archive.receiptReferenceOf(retained);
            assertEquals(retained, actual.archive.loadReceipt(ref));
            assertEquals(retained, actual.coordinator.execute(command));
            assertEquals(retained, actual.reopenAndReturnExisting(command));
            var next = new ActionCommand("blocked-" + name, command.before(), command.source(), command.sessionId(), command.operation(),
                    command.arguments(), command.expected(), command.claims(), command.deadline());
            assertThrows(IllegalArgumentException.class, () -> actual.coordinator.execute(next));
            assertEquals(1, actual.nativeActionWrites());
        }
    }
    @Test void positiveOriginalAckAndOldQueryCannotInventIndependentPausedPush() throws Exception { rejectOriginal("old-query", false); }
    @Test void pauseContractCannotClaimGameplayWhileReturningControlData() throws Exception { rejectOriginal("claimed-gameplay", true); }
}
