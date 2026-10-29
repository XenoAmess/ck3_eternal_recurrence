package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Shared contract DATA vectors. Actual domain/native proof acceptance remains with installed archived verifiers. */
final class TerminalActionContractTest {
    private static PlanningReadReceipt collection(String id, int revision, Instant at) {
        var command = ActionCoordinatorTest.command("collection-" + id, "query-prisoners"); var frame = ActionCoordinatorTest.frame(revision);
        var guard = new GuardEvidence(frame, command.source(), command.sessionId(), BigInteger.ONE, command.operation(), ActionCoordinatorTest.AFTER,
                ActionCoordinatorTest.BASIS, "authority-1", at, at.plusSeconds(5));
        var bound = new PlanningReadGuard(guard, true, true, true, "d".repeat(64));
        var request = new PlanningReadRequest(frame, command.source(), command.sessionId(), command.operation(), command.arguments(), at.plusSeconds(5));
        var ack = new NativeActionPort.AckReceived(id, true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[] {1});
        return new PlanningReadReceipt(request, "prisoner-collection-contract-data", id, bound, bound, ack);
    }
    private static ActionTerminalObservation terminal(ActionCommand command, String mutation) {
        return new ActionTerminalObservation(ActionCodec.bodySha256(command), mutation, new ActionTerminalObservation.PrisonerTransferred(BigInteger.valueOf(900), BigInteger.valueOf(901)),
                command.before(), ActionCoordinatorTest.frame(2), command.source(), command.sessionId(), new ObservationProvenance.Query("after-query"), ActionCoordinatorTest.NOW.plusSeconds(3),
                ActionCoordinatorTest.AFTER, ActionCoordinatorTest.REF, collection("selection", 1, ActionCoordinatorTest.NOW.minusSeconds(1)), collection("after-query", 2, ActionCoordinatorTest.NOW.plusSeconds(2)), List.of(ActionCoordinatorTest.BASIS));
    }
    @Test void independentTransferredDispositionIsSettledWithoutReleasePaymentOrGameplayCredit() {
        var command = ActionCoordinatorTest.command("release", "release-prisoner-900"); var attempt = ActionCoordinatorTest.attempt(command, "release-original");
        var observed = terminal(command, attempt.requestId()); assertDoesNotThrow(() -> observed.validate(command, attempt));
        var rejection = new ActionState.NonAppliedTerminal(observed);
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[] {1});
        var receipt = new ActionReceipt(1, 4, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack, rejection));
        assertTrue(receipt.settled()); assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT, receipt.outcome());
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertTrue(receipt.applied().isEmpty());
        var encoded = ActionTerminalCodec.encode(observed, read -> read.requestId().equals("selection") ? ActionCoordinatorTest.REF : ActionCoordinatorTest.AFTER);
        assertEquals(observed, ActionTerminalCodec.decode(encoded, ref -> ref.equals(ActionCoordinatorTest.REF) ? observed.selectedCollection() : observed.afterCollection()));
        var invalid = encoded.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) invalid.get("disposition")).put("current_jailer_id", true);
        assertThrows(IllegalArgumentException.class, () -> ActionTerminalCodec.decode(invalid, ref -> observed.afterCollection()));
        var missing = encoded.deepCopy(); missing.remove("original_submission");
        assertThrows(IllegalArgumentException.class, () -> ActionTerminalCodec.decode(missing, ref -> observed.afterCollection()));
    }
    @Test void terminalDispositionCannotChangeOriginalBodyOrUseMutationAsIndependentQuery() {
        var command = ActionCoordinatorTest.command("release", "release-prisoner-900"); var attempt = ActionCoordinatorTest.attempt(command, "after-query");
        assertThrows(IllegalArgumentException.class, () -> terminal(command, attempt.requestId()).validate(command, attempt));
        var changed = ActionCoordinatorTest.command("other", command.operation().value());
        assertThrows(IllegalArgumentException.class, () -> terminal(command, "original").validate(changed, ActionCoordinatorTest.attempt(changed, "original")));
    }
    @Test void negativeCompositeRetainsCanonicalRejectionAndCannotEraseAnAppliedChild() {
        var parent = ActionCoordinatorTest.command("retreat", "army-order-retreat"); var child = ActionCoordinatorTest.command("move", "army-move"); var attempt = ActionCoordinatorTest.attempt(child, "move-original");
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), false, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[] {1});
        var rejected = new ActionReceipt(1, 4, child, ActionCodec.bodySha256(child), new ActionState.Settled(attempt, ack, new ActionState.Rejected(attempt.requestId(), "actual domain rejection DATA", ActionCoordinatorTest.AFTER)));
        var children = List.of(new CompositeExecution.Child(child.actionId(), rejected.bodySha256()));
        var execution = new CompositeExecution("army-retreat", ActionCoordinatorTest.NOW, ActionCoordinatorTest.guard(parent, ActionCoordinatorTest.NOW), children);
        var negative = new ActionState.CompositeRejected("the only actual movement child was rejected", children);
        assertDoesNotThrow(() -> ActionEffects.validateComposite(parent, execution, negative));
        assertDoesNotThrow(() -> ActionEffects.validateCompositeChildren(execution, negative, List.of(rejected)));
        var receipt = new ActionReceipt(1, 5, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution, negative));
        assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED, receipt.outcome()); assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        var applied = new ActionReceipt(1, 4, child, rejected.bodySha256(), new ActionState.Settled(attempt, ack, new ActionState.Applied(ActionCoordinatorTest.zeroDay(child, ActionCoordinatorTest.NOW.plusSeconds(3)))));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateCompositeChildren(execution, negative, List.of(applied)));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(parent, ActionCoordinatorTest.attempt(parent, "parent"), negative));
    }
    @Test void freshReadOnlyWindowLeavesTheOriginalCommandBodyAndDeadlineUnchanged() {
        var command = ActionCoordinatorTest.command("old-unknown", "release-prisoner-900"); byte[] original = ActionCodec.encodeCommand(command);
        Instant now = command.deadline().plusSeconds(600); var clock = Clock.fixed(now, ZoneOffset.UTC);
        assertEquals(command.deadline(), ActionObservationWindow.deadline(command));
        ActionScope.run(command.actionId(), () -> ActionObservationWindow.reconcile(command.actionId(), clock, () -> {
            assertEquals(now.plusSeconds(30), ActionObservationWindow.deadline(command));
            assertThrows(IllegalArgumentException.class, () -> ActionObservationWindow.deadline(ActionCoordinatorTest.command("another", "pause-map"))); return null;
        }));
        assertEquals(command.deadline(), ActionObservationWindow.deadline(command)); assertArrayEquals(original, ActionCodec.encodeCommand(command));
    }
    @Test void reviewedSwayChildIdsFitTheActualNativePrefixAndLengthWithoutChangingOtherContracts() {
        var start = new OperationKey("submit-active-scheme-sway-v1-private-4294967295"); var stop = new OperationKey("stop-active-scheme-sway-v1-private");
        String started = ActionIds.child("parent", 1, start), stopped = ActionIds.child("parent", 1, stop);
        assertEquals(64, started.length()); assertEquals(64, stopped.length()); assertTrue(started.matches("sway-[A-Za-z0-9_-]+")); assertTrue(stopped.startsWith("stop-sway-"));
        assertEquals(started, ActionIds.child("parent", 1, start)); assertNotEquals(started, ActionIds.child("parent", 2, start)); assertNotEquals(started, stopped);
        assertEquals(ActionIds.child("parent", 1), ActionIds.child("parent", 1, new OperationKey("army-move")));
        for (String target : List.of("0", "01", "4294967296", "-1")) assertThrows(IllegalArgumentException.class, () -> ActionIds.child("parent", 1, new OperationKey("submit-active-scheme-sway-v1-private-" + target)));
    }
}
