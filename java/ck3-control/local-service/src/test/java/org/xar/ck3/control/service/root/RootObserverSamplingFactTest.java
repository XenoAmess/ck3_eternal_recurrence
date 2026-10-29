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
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Typed canonical DATA to the actual fact-consumer helpers. No archive verifier, query or Native qualification is supplied. */
final class RootObserverSamplingFactTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef ORIGINAL = new ExactRef("software-original", 1, "a".repeat(64));
    private static final ExactRef BASIS = new ExactRef("software-basis", 1, "b".repeat(64));
    private static final G2Source SOURCE = new G2Source("software-control-facts", NOW.toString(), "software-only", ORIGINAL);
    private static ObservationIdentity frame() {
        return new ObservationIdentity(SOURCE.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(100)),
                        "software-native-1", BigInteger.ONE, "software-episode"), 1);
    }
    private static ActionCommand command(String step) {
        var before = frame();
        return new ActionCommand("software-control-action", before, SOURCE, "software-session", new OperationKey(step),
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, SOURCE, ArmyObserverSampling.OBSERVER,
                        ArmyObserverSampling.expected(!ArmyObserverSampling.DISABLE.equals(step),ArmyObserverSampling.Family.ALL)),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static GuardEvidence guard(ActionCommand command, Instant at) {
        return new GuardEvidence(command.before(), SOURCE, command.sessionId(), BigInteger.ONE, command.operation(), ORIGINAL, BASIS,
                "software-authority", at, NOW.plusSeconds(20));
    }
    private static RawJson empty() { return new RawJson("{}".getBytes(StandardCharsets.UTF_8)); }
    private static ActionState.Attempt attempt(ActionCommand command) {
        return new ActionState.Attempt("software-request", NOW, guard(command, NOW), new NativeRequest(command.operation().value(), Optional.empty(), empty()));
    }
    private static NativeActionPort.AckReceived ack() { return new NativeActionPort.AckReceived("software-request", true, Optional.empty(), empty(), new byte[]{1}); }
    private static PlanningReadReceipt read(String id, Instant at) {
        ActionCommand query = command(ArmyObserverSampling.QUERY); var binding = new PlanningReadGuard(guard(query, at), true, true, true, "c".repeat(64));
        var request = new PlanningReadRequest(query.before(), SOURCE, query.sessionId(), query.operation(), query.arguments(), query.deadline());
        var result = new NativeActionPort.AckReceived(id, true, Optional.empty(), empty(), new byte[]{1});
        return new PlanningReadReceipt(request, "software-read-contract", id, binding, binding, result);
    }
    private static ActionReceipt receipt(ActionCommand command, ActionState state) {
        return new ActionReceipt(1, 3, command, ActionCodec.bodySha256(command), state);
    }
    @Test void independentControlAppliedIsAcceptedOnlyAsControlWithoutGameplayAdvanceOrSaveCredit() {
        for (String operation : List.of(ArmyObserverSampling.ENABLE, ArmyObserverSampling.DISABLE)) {
            var command = command(operation); var independent = new ActionState.ControlApplied(read("after", NOW.plusSeconds(1)), ArmyObserverSampling.OBSERVER, List.of());
            var original = receipt(command, new ActionState.Settled(attempt(command), ack(), independent));
            RootPlanningInputsFactory.requireSettledControl(new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.OBSERVER_SAMPLING_CONTROL), original);
            assertTrue(original.settled()); assertFalse(original.visibleGameplay()); assertFalse(original.eligibleAdvance()); assertTrue(original.applied().isEmpty());
            assertThrows(IllegalArgumentException.class, () -> RootPlanningInputsFactory.requireSettledControl(
                    new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE), original));
        }
    }
    @Test void unresolvedSamplingAndAnAppliedGameplayRelabelRemainRejectedByTheActualControlConsumer() {
        var command = command(ArmyObserverSampling.ENABLE); var control = new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.OBSERVER_SAMPLING_CONTROL);
        var unknown = receipt(command, new ActionState.Unknown(Optional.of(attempt(command)), Optional.empty(), "original outcome unknown", List.of(ORIGINAL)));
        assertThrows(IllegalArgumentException.class, () -> RootPlanningInputsFactory.requireSettledControl(control, unknown));
        var effect = new ActionState.EffectObservation(command.before(), SOURCE, command.sessionId(), ArmyObserverSampling.OBSERVER, command.expected().values(),
                "software-read", NOW.plusSeconds(1), ORIGINAL);
        var relabelled = receipt(command, new ActionState.Settled(attempt(command), ack(), new ActionState.Applied(effect)));
        assertThrows(IllegalArgumentException.class, () -> RootPlanningInputsFactory.requireSettledControl(control, relabelled));
        var rejected = receipt(command, new ActionState.Settled(attempt(command), ack(), new ActionState.Rejected("software-request", "actual refusal DATA", ORIGINAL)));
        RootPlanningInputsFactory.requireSettledControl(control, rejected);
    }
}
