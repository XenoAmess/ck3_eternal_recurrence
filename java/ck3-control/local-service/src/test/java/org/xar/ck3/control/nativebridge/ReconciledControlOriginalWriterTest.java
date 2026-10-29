package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;

/** Actual ACTION write-return/read-IO UNKNOWN -> passive original receive -> strict sidecar DATA.
 * This does not issue a Control settlement or stand in for the installed domain's independent after observation. */
final class ReconciledControlOriginalWriterTest {
    @TempDir Path root;
    private static ActionWriterIntegrationFixture.SoftwareActionScenario scenario() {
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("fixture-original-control-v1"),
                "fixture.original-control", (command, attempt, original) -> new ActionPorts.Pending("independent control observation is absent", List.of()), () -> { });
    }
    private static NativeActionPort.AckReceived receiveActualLate(ActionWriterIntegrationFixture actual, String requestId) throws Exception {
        var transport = actual.physicalInputs().transport(); Instant deadline = Instant.now().plusSeconds(5);
        for (int i = 0; i < 8 && Instant.now().isBefore(deadline); i++) {
            var retained = transport.pollOriginalOutcome(requestId); if (retained.isPresent()) return retained.orElseThrow();
            transport.observe(deadline);
        }
        return transport.pollOriginalOutcome(requestId).orElseThrow(() -> new AssertionError("original ACTION ACK not observed within the bounded passive receive"));
    }
    @Test void actualLateOriginalIsRetainedWithoutChangingUnknownOrReleasingItsGlobalGate() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("late"), false, scenario())) {
            actual.loseActionAckOnce(); var command = actual.command("late-control-original");
            var retained = actual.coordinator.execute(command);
            var unknown = assertInstanceOf(ActionState.Unknown.class, retained.state());
            var attempt = unknown.attempt().orElseThrow();
            var original = assertInstanceOf(NativeActionPort.Unknown.class, unknown.dispatch().orElseThrow());
            assertTrue(original.originalRequestPacket().length > 0); assertEquals(1, actual.nativeActionWrites());
            var receiptRef = actual.archive.receiptReferenceOf(retained); byte[] ledger = actual.ledgerBytes();
            var transport = actual.physicalInputs().transport();
            assertTrue(transport.pollOriginalOutcome(attempt.requestId()).isEmpty());
            actual.releaseLateActionAck();
            var received = receiveActualLate(actual, attempt.requestId());
            var sidecar = new ReconciledControlAck(received);
            sidecar.requireMatches(command, attempt, original);
            assertEquals(attempt.requestId(), received.requestId());
            assertArrayEquals(original.originalRequestPacket(), received.outbound().orElseThrow().originalPacket());
            var receivedRef = actual.archive.preserve(received);
            assertEquals(receivedRef, sidecar.reference(actual.archive));
            assertEquals(received, actual.archive.load(receivedRef));
            assertTrue(transport.pollOriginalOutcome(attempt.requestId()).isEmpty());
            // Retain this exact object before any domain validation; no second cache lookup is required on retry.
            sidecar.requireMatches(command, attempt, original);
            assertEquals(retained, actual.archive.loadReceipt(receiptRef));
            assertEquals(retained, actual.coordinator.execute(command));
            assertEquals(retained, actual.reopenAndReturnExisting(command));
            var next = new ActionCommand("another-control", command.origin(), command.source(), command.sessionId(), command.operation(),
                    command.arguments(), command.expectation(), command.claims(), command.deadline(), command.protocolIdentity());
            assertThrows(IllegalArgumentException.class, () -> actual.coordinator.execute(next));
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(1, actual.nativeActionWrites());
        }
    }
    @Test void actualAckCannotReplaceAnotherAttemptOrAnAlreadyRetainedResult() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("binding"), false, scenario())) {
            actual.loseActionAckOnce(); var command = actual.command("bound-control-original");
            var retained = actual.coordinator.execute(command); var unknown = assertInstanceOf(ActionState.Unknown.class, retained.state());
            var attempt = unknown.attempt().orElseThrow(); var original = unknown.dispatch().orElseThrow();
            actual.releaseLateActionAck(); var transport = actual.physicalInputs().transport();
            var received = receiveActualLate(actual, attempt.requestId());
            var sidecar = new ReconciledControlAck(received); sidecar.requireMatches(command, attempt, original);
            var foreign = new ActionState.Attempt(attempt.requestId() + "-foreign", attempt.submittedAt(), attempt.guard(), attempt.preparedRequest());
            assertThrows(IllegalArgumentException.class, () -> sidecar.requireMatches(command, foreign, original));
            assertThrows(IllegalArgumentException.class, () -> sidecar.requireMatches(command, attempt, received));
            assertThrows(IllegalArgumentException.class, actual::releaseLateActionAck);
            assertEquals(1, actual.nativeActionWrites()); assertEquals(retained, actual.reopenAndReturnExisting(command));
        }
    }
}
