package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Real software ACTION ACK/UNKNOWN and retained packets feed deliberately untrusted control DATA.
 * No actual Root running authority, fresh Push, successful pause or canonical parent is invented. */
final class NativeOutcomeArchivePauseControlTest {
    @TempDir Path root;
    private record Run(ActionWriterIntegrationFixture actual, ActionReceipt unknown,
            ActionState.Attempt attempt, NativeActionPort.AckReceived ack, ActionState.EffectObservation query)
            implements AutoCloseable {
        @Override public void close() throws Exception { actual.close(); }
    }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static Run open(Path root) throws Exception {
        var observed = new AtomicReference<ActionState.EffectObservation>();
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
                (command, attempt, dispatch) -> {
                    var query = new ActionState.EffectObservation(command.before(), command.source(), command.sessionId(),
                            PauseConfirmation.OBSERVER, PauseConfirmation.actualValues(),
                            new ObservationProvenance.Query("untrusted-old-query"), Instant.now(),
                            attempt.guard().nativeEvidence(), List.of(attempt.guard().nativeEvidence()));
                    observed.set(query); return new ActionPorts.PauseObserved(query);
                }, () -> { });
        var actual = new ActionWriterIntegrationFixture(root, false, scenario);
        try {
            var initial = actual.command("original-pause");
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, initial.before(), initial.source(),
                    PauseConfirmation.OBSERVER, PauseConfirmation.expectedValues());
            var command = new ActionCommand(initial.actionId(), initial.before(), initial.source(), initial.sessionId(),
                    initial.operation(), initial.arguments(), expected, initial.claims(), initial.deadline());
            var retained = actual.coordinator.execute(command);
            var unknown = assertInstanceOf(ActionState.Unknown.class, retained.state());
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, unknown.dispatch().orElseThrow());
            assertTrue(ack.nativeOk()); assertTrue(ack.outbound().isPresent()); assertTrue(ack.custody().isPresent());
            ack.custody().orElseThrow().verify(ack, unknown.attempt().orElseThrow().guard());
            assertEquals(1, actual.nativeActionWrites()); assertNotNull(observed.get());
            return new Run(actual, retained, unknown.attempt().orElseThrow(), ack, observed.get());
        } catch (Exception | Error failure) { actual.close(); throw failure; }
    }
    private static ActionReceipt pauseData(Run run, boolean oldPush) {
        var effect = run.query();
        if (oldPush) {
            // The packet and frame are the actual BEFORE original. Encoding a Push DATA tag
            // never turns this same old packet into a newly received independent after-state.
            var before = run.unknown().command().before();
            effect = new ActionState.EffectObservation(before, effect.source(), effect.sessionId(), effect.observerSchema(),
                    effect.actual(), new ObservationProvenance.Push(before.frame().snapshotId(),
                            before.frame().identity().nativeRevision(), run.attempt().guard().nativeEvidence()),
                    effect.observedAt(), run.attempt().guard().nativeEvidence(), effect.supportingEvidence());
        }
        return new ActionReceipt(1, run.unknown().sequence(), run.unknown().command(), run.unknown().bodySha256(),
                new ActionState.Settled(run.attempt(), run.ack(), new ActionState.PauseConfirmed(effect)));
    }
    private static ExactRef retainData(Run run, byte[] bytes) throws Exception {
        return run.actual().writer.locked(same -> run.actual().archive.preserveArtifact(same, bytes, StrictJson.EXPLICIT_MAX_BYTES));
    }
    private static long files(Path root) throws Exception {
        try (var paths = Files.walk(root)) { return paths.filter(Files::isRegularFile).count(); }
    }
    private static void rejectWithoutPublication(Run run, ActionReceipt data, ExactRef metadata) throws Exception {
        var actual = run.actual(); byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
        assertThrows(RuntimeException.class, () -> actual.archive.preserveReceipt(data));
        assertThrows(RuntimeException.class, () -> actual.archive.receiptReferenceOf(data));
        assertThrows(RuntimeException.class, () -> actual.archive.loadReceipt(metadata));
        assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
        assertEquals(1, actual.nativeActionWrites()); assertFalse(run.unknown().settled());
        assertFalse(run.unknown().visibleGameplay()); assertFalse(run.unknown().eligibleAdvance());
        assertEquals(run.unknown(), actual.coordinator.execute(run.unknown().command()));
        assertEquals(1, actual.nativeActionWrites());
    }
    @Test void actualAckAndOldQueryCannotBecomeTypedPauseInProducerOrColdArchive() throws Exception {
        try (var run = open(root.resolve("query"))) {
            var data = pauseData(run, false); byte[] bytes = ActionReceiptCodec.encodeReceipt(data, run.actual().archive);
            assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(bytes, run.actual().archive));
            rejectWithoutPublication(run, data, retainData(run, bytes));
            assertEquals(run.unknown(), run.actual().reopenAndReturnExisting(run.unknown().command()));
        }
    }
    @Test void strictV8DataRoundtripCannotPromoteActualBeforePacketIntoIndependentPausedPush() throws Exception {
        try (var run = open(root.resolve("old-push"))) {
            var data = pauseData(run, true); byte[] bytes = ActionReceiptCodec.encodeReceipt(data, run.actual().archive);
            assertEquals(data, ActionReceiptCodec.decodeReceipt(bytes, run.actual().archive)); // DATA only.
            assertFalse(data.visibleGameplay()); assertFalse(data.eligibleAdvance()); assertTrue(data.applied().isEmpty());
            rejectWithoutPublication(run, data, retainData(run, bytes));
        }
    }
    @Test void actualControlDataRejectsLegacySchemaMissingWrongTypeAndDuplicateFields() throws Exception {
        try (var run = open(root.resolve("strict"))) {
            byte[] original = ActionReceiptCodec.encodeReceipt(pauseData(run, true), run.actual().archive);
            for (int version = 1; version < 8; version++) {
                var row = assertInstanceOf(ObjectNode.class, StrictJson.parse(original, StrictJson.EXPLICIT_MAX_BYTES));
                row.put("schema", "xar.java-action-receipt/v" + version);
                assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(
                        StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES), run.actual().archive));
            }
            for (int mutation = 0; mutation < 3; mutation++) {
                var row = assertInstanceOf(ObjectNode.class, StrictJson.parse(original, StrictJson.EXPLICIT_MAX_BYTES));
                var state = assertInstanceOf(ObjectNode.class, row.get("state"));
                var settlement = assertInstanceOf(ObjectNode.class, state.get("settlement"));
                if (mutation == 0) settlement.remove("semantic");
                else if (mutation == 1) settlement.putNull("semantic");
                else settlement.put("unrecognized_field", true);
                assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(
                        StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES), run.actual().archive));
            }
            String duplicate = new String(original, StandardCharsets.UTF_8)
                    .replace("\"kind\":\"PAUSE_CONFIRMED\"", "\"kind\":\"PAUSE_CONFIRMED\",\"kind\":\"PAUSE_CONFIRMED\"");
            assertFalse(duplicate.equals(new String(original, StandardCharsets.UTF_8)));
            assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(
                    duplicate.getBytes(StandardCharsets.UTF_8), run.actual().archive));
            assertEquals(1, run.actual().nativeActionWrites());
        }
    }
    @Test void realCanonicalUnknownChildAndMissingReceiptNeverBecomeACompletedControlSequence() throws Exception {
        try (var run = open(root.resolve("sequence"))) {
            var actual = run.actual(); var child = run.unknown(); var initial = child.command();
            var expected = new ProposalLifecycle.ExpectedPostcondition(1, initial.before(), initial.source(),
                    ControlSequenceObservation.OBSERVER, ControlSequenceObservation.expected());
            var parent = new ActionCommand("untrusted-control-parent", initial.before(), initial.source(), initial.sessionId(),
                    ControlSequenceObservation.OPERATION, initial.arguments(), expected, initial.claims(), initial.deadline());
            var old = run.attempt().guard();
            var guard = new GuardEvidence(parent.origin(), parent.source(), parent.sessionId(), old.connectionGeneration(),
                    parent.operation(), old.nativeEvidence(), old.capabilityEvidence(), old.authorityId(), old.observedAt(),
                    old.validUntil(), old.supportingEvidence());
            ExactRef retainedChild = actual.archive.receiptReferenceOf(child);
            ExactRef proof = actual.archive.preserveMaterial(raw("{\"untrusted_control_proof_DATA\":true}"));
            var observation = new ControlSequenceObservation(parent, ControlSequenceObservation.Mode.DIRECT_PAUSE,
                    parent.before(), proof, List.of(new ControlSequenceObservation.Child(initial.actionId(),
                    child.bodySha256(), retainedChild)), List.of());
            var execution = new CompositeExecution("untrusted-control-DATA", old.observedAt(), guard,
                    List.of(new CompositeExecution.Child(initial.actionId(), child.bodySha256())));
            var data = new ActionReceipt(1, child.sequence(), parent, ActionCodec.bodySha256(parent),
                    new ActionState.CompositeSettled(execution, new ActionState.ControlSequenceCompleted(observation)));
            byte[] bytes = ActionReceiptCodec.encodeReceipt(data, actual.archive);
            assertEquals(data, ActionReceiptCodec.decodeReceipt(bytes, actual.archive)); // Closed DATA, not ledger authority.
            ExactRef metadata = retainData(run, bytes);
            rejectWithoutPublication(run, data, metadata); // Existing canonical UNKNOWN is not a settled pause child.
            Path missing = Path.of(retainedChild.path()); assertTrue(missing.normalize().startsWith(actual.root.normalize()));
            Files.delete(missing); byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
            assertThrows(RuntimeException.class, () -> actual.archive.loadReceipt(metadata));
            assertThrows(RuntimeException.class, () -> actual.archive.preserveReceipt(data));
            assertFalse(Files.exists(missing)); assertEquals(count, files(actual.root));
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(1, actual.nativeActionWrites());
        }
    }
}
