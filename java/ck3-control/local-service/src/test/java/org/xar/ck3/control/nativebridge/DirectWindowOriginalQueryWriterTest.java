package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software ACTION/READ/writer boundaries. Unqualified DATA is deliberately rejected;
 * actual Root Recon source, captured owner query and completion positives remain mandatory external inputs. */
final class DirectWindowOriginalQueryWriterTest {
    @TempDir Path root;
    private static final OperationKey CLOSE = new OperationKey("close-war-declared-overview-v1");
    private record UnqualifiedToken(String actionId, PlanningReadReceipt queryReceipt, ExactRef queryRef,
            Instant deadline) implements DirectFixedWindowQueryContinuation { }
    private static ActionWriterIntegrationFixture.SoftwareActionScenario pending() {
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(CLOSE, "fixture.original-close",
                (command, attempt, dispatch) -> new ActionPorts.Pending("actual owner query source is absent", List.of()), () -> { });
    }
    private static PlanningReadResult.Known<RawJson> query(ActionWriterIntegrationFixture actual, ActionCommand command) {
        var result = actual.reads.read(actual.readContract, new PlanningReadRequest(command.before(), command.source(),
                command.sessionId(), actual.readContract.operation(), new OpportunityJson.Obj(Map.of()), command.deadline()));
        if (result instanceof PlanningReadResult.Known<RawJson> known) return known;
        throw new AssertionError("actual ordinary READ producer unavailable");
    }
    @Test void defaultWrapperReachesActualCentralButOrdinaryReadCannotAuthorizeOwnerQuery() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("original"), false, pending())) {
            var command = actual.command("pending-original-close"); var known = query(actual, command);
            var retained = actual.coordinator.execute(command);
            var unknown = assertInstanceOf(ActionState.Unknown.class, retained.state());
            assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class, unknown.dispatch().orElseThrow()).nativeOk());
            byte[] ledger = actual.ledgerBytes(); int reads = actual.nativeReadWrites();
            ActionCoordinatorPort wrapper = new ActionCoordinatorPort() {
                @Override public ActionReceipt execute(ActionCommand ignored) { throw new AssertionError("no execute"); }
                @Override public ActionReceipt reconcile(String id) { return actual.coordinator.reconcile(id); }
            };
            var token = new UnqualifiedToken(command.actionId(), known.receipt(), known.originalReceipt(), Instant.now().plusSeconds(5));
            var failure = assertThrows(IllegalArgumentException.class, () -> wrapper.reconcileOriginalDirectWindowQuery(token));
            assertTrue(failure.getMessage().contains("actual sampling query was not sent after"));
            assertEquals(retained, actual.coordinator.execute(command));
            assertEquals(retained, actual.reopenAndReturnExisting(command));
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(1, actual.nativeActionWrites());
            assertEquals(reads, actual.nativeReadWrites());
            var next = new ActionCommand("different-close", command.origin(), command.source(), command.sessionId(), command.operation(),
                    command.arguments(), command.expectation(), command.claims(), command.deadline(), command.protocolIdentity());
            assertThrows(IllegalArgumentException.class, () -> actual.coordinator.execute(next));
        }
    }
    @Test void wrapperCannotPretendItReachedTheCentralReducerOrLeakItsForwardingScope() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("wrapper"), false, pending())) {
            var command = actual.command("wrapper-original-close"); var known = query(actual, command);
            var retained = actual.coordinator.execute(command); byte[] ledger = actual.ledgerBytes();
            ActionCoordinatorPort missing = new ActionCoordinatorPort() {
                @Override public ActionReceipt execute(ActionCommand ignored) { throw new AssertionError("no execute"); }
                @Override public ActionReceipt reconcile(String ignored) { return retained; }
            };
            var token = new UnqualifiedToken(command.actionId(), known.receipt(), known.originalReceipt(), Instant.now().plusSeconds(5));
            assertThrows(IllegalArgumentException.class, () -> missing.reconcileOriginalDirectWindowQuery(token));
            // The failed adapter has exited. A fresh call reaches central, rather than inheriting an escaped scope.
            var failure = assertThrows(IllegalArgumentException.class, () -> actual.coordinator.reconcileOriginalDirectWindowQuery(token));
            assertTrue(failure.getMessage().contains("actual sampling query was not sent after"));
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(1, actual.nativeActionWrites());
        }
    }
    @Test void typedCompletionDataDoesNotTurnAnActualAckIntoExecutionCompletion() throws Exception {
        ExactRef[] basis = {null};
        var scenario = new ActionWriterIntegrationFixture.SoftwareActionScenario(CLOSE, "fixture.unqualified-completion",
                (command, attempt, dispatch) -> new ActionPorts.DirectFixedWindowObserved(new NativeDirectFixedWindowObservation.Completion(
                        command.actionId(), ActionCodec.bodySha256(command), attempt.requestId(), basis[0], command.before(), command.before(),
                        command.source(), command.sessionId(), List.of(basis[0]), NativeDirectFixedWindowObservation.Resolution.DIRECT_AVAILABLE)), () -> { });
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("data"), false, scenario)) {
            basis[0] = actual.archive.preserveMaterial(new RawJson("{\"unqualified_test_data\":true}".getBytes(StandardCharsets.UTF_8)));
            var command = actual.command("unqualified-completion"); var retained = actual.coordinator.execute(command);
            var unknown = assertInstanceOf(ActionState.Unknown.class, retained.state());
            assertTrue(unknown.dispatch().orElseThrow() instanceof NativeActionPort.AckReceived);
            assertEquals(1, actual.nativeActionWrites());
            assertEquals(retained, actual.reopenAndReturnExisting(command));
            assertFalse(retained.settled());
        }
    }
}
