package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure durable-state contract vectors. Real writer/guard/producer coverage is in the host integration test. */
final class ActionCoordinatorTest {
    static final Instant NOW = Instant.parse("2026-10-23T18:00:00Z");
    static final ExactRef REF = new ExactRef("D:/contract-vectors/source.json", 1, "a".repeat(64));
    static final ExactRef AFTER = new ExactRef("D:/contract-vectors/after.json", 1, "b".repeat(64));
    static final ExactRef BASIS = new ExactRef("D:/contract-vectors/basis.json", 1, "c".repeat(64));
    static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    static final JointBudgetSelector.Claims CLAIMS = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of());
    static ProposalLifecycle.ObservationIdentity frame(int revision) {
        return new ProposalLifecycle.ObservationIdentity(SOURCE.machineId(), new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(revision), BigInteger.valueOf(100)),
                        "native-" + revision, BigInteger.valueOf(revision), "episode-1"), 1);
    }
    static ActionCommand command(String id, String operation) {
        var before = frame(1); var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, SOURCE, "paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, SOURCE, "session-1", new OperationKey(operation), new OpportunityJson.Obj(Map.of()), expected, CLAIMS, NOW.plusSeconds(30));
    }
    static GuardEvidence guard(ActionCommand command, Instant at) {
        return new GuardEvidence(command.before(), SOURCE, command.sessionId(), BigInteger.ONE, command.operation(), REF, BASIS, "authority-1", at, NOW.plusSeconds(20));
    }
    static ActionState.Attempt attempt(ActionCommand command, String request) {
        return new ActionState.Attempt(request, NOW, guard(command, NOW), new NativeRequest(command.operation().value(), "timeline-control", new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
    }
    static PlanningReadReceipt read(String id, Instant at) {
        ActionCommand query = command("query", "query-native-clock");
        var binding = new PlanningReadGuard(guard(query, at), true, true, true, "d".repeat(64));
        var request = new PlanningReadRequest(query.before(), SOURCE, query.sessionId(), query.operation(), query.arguments(), query.deadline());
        var ack = new NativeActionPort.AckReceived(id, true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[] {1});
        return new PlanningReadReceipt(request, "exact-clock-status", id, binding, binding, ack);
    }
    static ActionState.EffectObservation zeroDay(ActionCommand parent, Instant at) {
        List<ProposalLifecycle.ExpectedValue> values = new java.util.ArrayList<>(parent.expected().values());
        for (String field : List.of("native.gameplay_verified", "timeline.advance_verified", "timeline.checkpoint_eligible"))
            values.add(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey(field), false));
        return new ActionState.EffectObservation(parent.before(), SOURCE, parent.sessionId(), parent.expected().observerSchema(),
                values, "fresh-semantic", at, AFTER, List.of(BASIS));
    }
    @Test void unknownHasNoTransitionBackToSubmitting() {
        ActionCommand command = command("a", "pause-map"); var attempt = attempt(command, "original");
        ActionReceipt unknown = new ActionReceipt(1, 3, command, ActionCodec.bodySha256(command), new ActionState.Unknown(Optional.of(attempt), Optional.empty(), "wire extent unknown", List.of(REF)));
        assertThrows(IllegalArgumentException.class, () -> ActionTransitions.validate(Optional.of(unknown), command, unknown.bodySha256(), new ActionState.Submitting(attempt)));
    }
    @Test void unknownCannotReplaceOriginalAttemptDuringReconciliation() {
        ActionCommand command = command("a", "pause-map"); var original = attempt(command, "original");
        ActionReceipt unknown = new ActionReceipt(1, 3, command, ActionCodec.bodySha256(command), new ActionState.Unknown(Optional.of(original), Optional.empty(), "unknown", List.of(REF)));
        var changed = new ActionState.Unknown(Optional.of(attempt(command, "replacement")), Optional.empty(), "unknown", List.of(REF));
        assertThrows(IllegalArgumentException.class, () -> ActionTransitions.validate(Optional.of(unknown), command, unknown.bodySha256(), changed));
    }
    @Test void sameActionIdRequiresTheCompleteOriginalBody() {
        ActionCommand first = command("a", "pause-map");
        ActionCommand changed = new ActionCommand(first.actionId(), first.before(), SOURCE, first.sessionId(), first.operation(), first.arguments(), first.expected(), CLAIMS, first.deadline().plusSeconds(1));
        ActionReceipt intent = new ActionReceipt(1, 1, first, ActionCodec.bodySha256(first), new ActionState.IntentDurable());
        assertThrows(IllegalArgumentException.class, () -> ActionTransitions.validate(Optional.of(intent), changed, ActionCodec.bodySha256(changed), new ActionState.Submitting(attempt(changed, "other"))));
    }
    @Test void ordinaryEffectsStillRequireLaterNativeRevisionAndIndependentRequest() {
        ActionCommand command = command("a", "pause-map");
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(command, attempt(command, "write"), new ActionState.Applied(zeroDay(command, NOW.plusSeconds(3)))));
        var effect = new ActionState.EffectObservation(frame(2), SOURCE, command.sessionId(), command.expected().observerSchema(), command.expected().values(), "write", NOW.plusSeconds(3), AFTER, List.of(BASIS));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validate(command, attempt(command, "write"), new ActionState.Applied(effect)));
    }
    @Test void zeroDayControlWithoutActualSamplingCustodyCannotQualifyFromConstructedData() {
        ActionCommand parent = command("parent", "life-advance-one-day"); var execution = new CompositeExecution("life-v1", NOW, guard(parent, NOW), List.of());
        var observed = new CompositeControlObservation(read("idle", NOW.plusSeconds(2)), List.of(read("cancel-proof", NOW.plusSeconds(1))), zeroDay(parent, NOW.plusSeconds(3)));
        var settled = new ActionState.CompositeControlApplied(observed);
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateComposite(parent, execution, settled));
        // The actual transport/writer Life fixture owns the positive sampling chain; these legacy DATA records carry no custody.
        var receipt = new ActionReceipt(1, 5, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution, settled));
        assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertTrue(receipt.applied().isEmpty());
        assertEquals(observed.semantic(), ActionEffects.observation(receipt).orElseThrow());
    }
    @Test void zeroDayControlCannotUseSemanticEvidenceOlderThanTerminalStatus() {
        ActionCommand parent = command("parent", "life-advance-one-day"); var execution = new CompositeExecution("life-v1", NOW, guard(parent, NOW), List.of());
        var control = new ActionState.CompositeControlApplied(new CompositeControlObservation(read("idle", NOW.plusSeconds(4)), List.of(read("cancel-proof", NOW.plusSeconds(1))), zeroDay(parent, NOW.plusSeconds(3))));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateComposite(parent, execution, control));
    }
    @Test void zeroDayControlCannotSettleOverASubmittedResume() {
        ActionCommand parent = command("parent", "life-advance-one-day"), child = command("child", "resume-map"); var attempt = attempt(child, "resume");
        var proof = read("cancel-proof", NOW.plusSeconds(1));
        var ack = new NativeActionPort.AckReceived(attempt.requestId(), true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[]{1});
        var childReceipt = new ActionReceipt(1, 4, child, ActionCodec.bodySha256(child), new ActionState.Settled(attempt, ack, new ActionState.ControlApplied(proof, "paused/v1", child.expected().values())));
        var execution = new CompositeExecution("life-v1", NOW, guard(parent, NOW), List.of(new CompositeExecution.Child(child.actionId(), childReceipt.bodySha256())));
        var control = new ActionState.CompositeControlApplied(new CompositeControlObservation(read("idle", NOW.plusSeconds(2)), List.of(proof), zeroDay(parent, NOW.plusSeconds(3))));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateCompositeChildren(execution, control, List.of(childReceipt)));
    }
    @Test void zeroDayControlRequiresARealCanonicalControlChild() {
        ActionCommand parent = command("parent", "life-advance-one-day"); var execution = new CompositeExecution("life-v1", NOW, guard(parent, NOW), List.of());
        var control = new ActionState.CompositeControlApplied(new CompositeControlObservation(read("idle", NOW.plusSeconds(2)), List.of(read("cancel-proof", NOW.plusSeconds(1))), zeroDay(parent, NOW.plusSeconds(3))));
        assertThrows(IllegalArgumentException.class, () -> ActionEffects.validateCompositeChildren(execution, control, List.of()));
    }
    @Test void commandRoundtripRejectsBooleanVersionAndMissingSession() {
        ActionCommand command = command("a", "pause-map"); byte[] encoded = ActionCodec.encodeCommand(command); assertEquals(command, ActionCodec.decodeCommand(encoded));
        String text = new String(encoded, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(text.replace("\"observation_version\":1", "\"observation_version\":true").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(text.replace("\"session_id\":\"session-1\",", "").getBytes(StandardCharsets.UTF_8)));
    }
}

