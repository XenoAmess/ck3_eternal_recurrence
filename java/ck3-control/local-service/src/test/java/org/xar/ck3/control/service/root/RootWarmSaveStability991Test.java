package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public DATA eligibility only. No Root issuer, physical file, canonical writer, reconciliation or SAVE is exercised. */
final class RootWarmSaveStability991Test {
    private static final Instant NOW = Instant.parse("2026-11-02T16:08:06Z");
    private static final String PENDING = "SAVE awaits second stable physical observation";
    private static final RawJson EMPTY = new RawJson("{}".getBytes(StandardCharsets.UTF_8));
    private record Scene(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack) { }

    @Test void firstStablePositiveAckIsOnlyDataAndPreservesOriginalExpiredDeadline() {
        var scene = scene("save-checkpoint", Map.of(), true, true);
        var original = unknown(scene, PENDING, true);
        byte[] command = ActionCodec.encodeCommand(scene.command());
        byte[] packet = scene.ack().outbound().orElseThrow().originalPacket();

        assertTrue(scene.command().deadline().isBefore(NOW));
        assertTrue(RootOrdinaryWorkerLoop.awaitsSecondStableSave(original));
        assertFalse(original.settled());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, original.outcome());
        assertEquals(Instant.parse("2026-11-02T16:07:38Z"), original.command().deadline());
        assertArrayEquals(command, ActionCodec.encodeCommand(original.command()));
        assertArrayEquals(packet, original.ack().orElseThrow().outbound().orElseThrow().originalPacket());
        assertEquals(scene.attempt(), ((ActionState.Unknown) original.state()).attempt().orElseThrow());
        assertTrue(original.applied().isEmpty());
        assertFalse(original.visibleGameplay());
        assertFalse(original.eligibleAdvance());
    }

    @Test void otherUnknownReasonsMissingAckAndNonSaveContractsStayIneligible() {
        var exact = scene("save-checkpoint", Map.of(), true, true);
        for (String reason : List.of("SAVE physical file has not changed", "SAVE physical pair pending: source unavailable",
                "SAVE awaits second stable physical observation ", "native request response unknown")) {
            assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(unknown(exact, reason, true)), reason);
        }
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(unknown(exact, PENDING, false)));
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(unknown(scene("save-checkpoint", Map.of(), false, true), PENDING, true)));
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(unknown(scene("save-checkpoint", Map.of(), true, false), PENDING, true)));
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(unknown(scene("unrelated-operation", Map.of(), true, true), PENDING, true)));
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(unknown(scene("save-checkpoint",
                Map.of("extra", new OpportunityJson.Text("not-the-original-empty-arguments")), true, true), PENDING, true)));
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(new ActionReceipt(1, 9, exact.command(),
                ActionCodec.bodySha256(exact.command()), new ActionState.AckReceived(exact.attempt(), exact.ack()))));
        assertFalse(RootOrdinaryWorkerLoop.awaitsSecondStableSave(new ActionReceipt(1, 9, exact.command(),
                ActionCodec.bodySha256(exact.command()), new ActionState.IntentDurable())));
    }

    private static ActionReceipt unknown(Scene scene, String reason, boolean retainAck) {
        return new ActionReceipt(1, 9, scene.command(), ActionCodec.bodySha256(scene.command()),
                new ActionState.Unknown(Optional.of(scene.attempt()),
                        retainAck ? Optional.of(scene.ack()) : Optional.empty(), reason, List.of()));
    }

    private static Scene scene(String operation, Map<String, OpportunityJson.Value> arguments, boolean nativeOk, boolean retainOutbound) {
        var generation = new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100)));
        var frame = new JointBudgetSelector.Frame(BigInteger.valueOf(31254), BigInteger.valueOf(556), BigInteger.valueOf(53150520));
        var before = new ProposalLifecycle.ObservationIdentity("software-warm-save", generation,
                new JointBudgetSelector.ProposalFrame(frame, "native:556", BigInteger.valueOf(498), "software-episode"), 3);
        var source = new G2Source("software-warm-save", "2026-11-02T16:05:00Z", "software-build",
                new ExactRef("software-source", 1, "1".repeat(64)));
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, CheckpointRequestFactory.OBSERVER_SCHEMA,
                List.of(new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("date_raw"), BigInteger.valueOf(53150520)),
                        new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("played_character_id"), BigInteger.valueOf(31254)),
                        new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("checkpoint_pair_verified"), true)));
        var command = new ActionCommand("save-software-warm-original", before, source, "software-session", new OperationKey(operation),
                new OpportunityJson.Obj(arguments), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                Instant.parse("2026-11-02T16:07:38Z"));
        var ref = new ExactRef("software-data-only-evidence", 1, "2".repeat(64));
        var guard = new GuardEvidence(before, source, "software-session", BigInteger.valueOf(44), command.operation(), ref, ref,
                "software-authority-label-only", Instant.parse("2026-11-02T16:05:31Z"), command.deadline());
        var attempt = new ActionState.Attempt("software-save-request", Instant.parse("2026-11-02T16:06:53Z"), guard,
                new NativeRequest("save-checkpoint", "game.save-checkpoint", EMPTY));
        var outbound = new NativeActionPort.OutboundPacket(attempt.requestId(), new byte[]{1, 2, 3});
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), nativeOk, Optional.of(EMPTY), EMPTY,
                new byte[]{4, 5, 6}, retainOutbound ? Optional.of(outbound) : Optional.empty());
        return new Scene(command, attempt, ack);
    }
}
