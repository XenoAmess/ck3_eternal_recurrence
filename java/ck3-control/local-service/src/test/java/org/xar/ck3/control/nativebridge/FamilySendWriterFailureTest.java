package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Exercises the actual coordinator/writer refusal. Software packets grant no Family business qualification. */
final class FamilySendWriterFailureTest {
    @TempDir Path root;
    @Test void reusingTheActualBeforeQueryAsAfterProofStaysUnknownAndNeverWritesTwice() throws Exception {
        var owner = new AtomicReference<ActionWriterIntegrationFixture>();
        ActionPorts.PreparationPort preparation = new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { throw new AssertionError("must borrow actual original Session"); }
            @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) {
                var fixture = owner.get(); var archive = fixture.archive.withSession(same);
                assertEquals(RequestIds.forActionBody(ActionCodec.bodySha256(command)), requestId);
                var before = fixture.lastNestedRead.get(); assertNotNull(before);
                return new NativeRequest(command.operation().value(), Optional.of("game.command.pause-map"), new RawJson(new byte[]{'{', '}'}),
                        List.of(archive.readReferenceOf(before)));
            }
        };
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
                (command, attempt, dispatch) -> {
                    var fixture = owner.get(); var archive = fixture.archive.withSession(fixture.journal.borrowedWriterSession());
                    var before = fixture.lastNestedRead.get(); var guard = attempt.guard();
                    var basis = new NativeEffectEvidence.FrameBasis(guard.nativeEvidence(), guard.capabilityEvidence());
                    // These are retained actual originals. Deliberately reusing one original READ as both samples is invalid.
                    var data = new FamilySendObservation(FamilySendObservation.Profile.MARRIAGE, command.actionId(), ActionCodec.bodySha256(command),
                            attempt.requestId(), archive.referenceOf(dispatch), archive.requestReferenceOf(attempt.preparedRequest()), basis, basis,
                            command.before(), command.before(), command.source(), command.sessionId(), before, before,
                            attempt.preparedRequest().preparationEvidence(), 0, 73,
                            FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE, 7, 8, 0));
                    return new ActionPorts.FamilySendObserved(data);
                }, () -> { }, Optional.empty(), Optional.empty(), false, Optional.of(preparation));
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("same-sem-refusal"), false, scenario)) {
            owner.set(fixture); var seed = fixture.command("family-invalid-after-read");
            var command = new ActionCommand(seed.actionId(), seed.before(), seed.source(), seed.sessionId(), seed.operation(), seed.arguments(),
                    FamilyMarriageSendExpectation.expected(seed.before(), seed.source(), 7, 8), seed.claims(), seed.deadline());
            var receipt = fixture.coordinator.execute(command); var pending = assertInstanceOf(ActionState.Unknown.class, receipt.state());
            assertTrue(pending.reason().contains("postcondition not proven"), pending.reason());
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, receipt.outcome()); assertFalse(receipt.settled());
            assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertTrue(receipt.applied().isEmpty());
            assertEquals(1, fixture.nativeActionWrites()); assertEquals(1, fixture.attemptCompletions.get());
            assertEquals(receipt, fixture.coordinator.execute(command)); assertEquals(1, fixture.nativeActionWrites());
            var reconciled = fixture.coordinator.reconcile(command.actionId());
            assertInstanceOf(ActionState.Unknown.class, reconciled.state()); assertEquals(1, fixture.nativeActionWrites());
            assertEquals(ActionTransitions.attempt(receipt.state()), ActionTransitions.attempt(reconciled.state()));
        }
    }
}
