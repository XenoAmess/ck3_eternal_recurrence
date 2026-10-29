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
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Typed canonical DATA to the actual fact-consumer helpers. No archive verifier, query or Native qualification is supplied. */
final class RootRiteControlFactProjectionTest {
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
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, SOURCE, RootRiteCreationRuntimeFactory.OBSERVER,
                        List.of(new ExpectedBoolean(new FieldKey("software-control"), true))),
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
        ActionCommand query = command(RiteCreation.PREVIEW.operationKey().value()); var binding = new PlanningReadGuard(guard(query, at), true, true, true, "c".repeat(64));
        var request = new PlanningReadRequest(query.before(), SOURCE, query.sessionId(), query.operation(), query.arguments(), query.deadline());
        var result = new NativeActionPort.AckReceived(id, true, Optional.empty(), empty(), new byte[]{1});
        return new PlanningReadReceipt(request, "software-read-contract", id, binding, binding, result);
    }
    private static ActionReceipt receipt(ActionCommand command, ActionState state) {
        return new ActionReceipt(1, 3, command, ActionCodec.bodySha256(command), state);
    }
    private static RootPlanningInputsFactory.SystemControl control() {
        return new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.RITE_CREATION_CONTROL);
    }
    @Test void sixIndependentUiControlPostsNeverCreateBusinessAdvanceOrSaveCredit() {
        for(RiteCreation selector:RiteCreation.values())if(selector!=RiteCreation.PREVIEW&&selector!=RiteCreation.CONFIRM_ONCE) {
            var command=command(selector.operationKey().value());
            var observed=new ActionState.ControlApplied(read("after",NOW.plusSeconds(1)),RootRiteCreationRuntimeFactory.OBSERVER,List.of());
            var original=receipt(command,new ActionState.Settled(attempt(command),ack(),observed));
            RootPlanningInputsFactory.requireSettledControl(control(),original);
            assertTrue(original.settled());assertFalse(original.visibleGameplay());assertFalse(original.eligibleAdvance());assertTrue(original.applied().isEmpty());
            assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(
                    new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.CHECKPOINT_SAVE),original));
        }
    }
    @Test void confirmationUnknownStaysBlockingAndEvenControlAppliedCannotRelabelItAsSettledUi() {
        var command=command(RiteCreation.CONFIRM_ONCE.operationKey().value());
        var unknown=receipt(command,new ActionState.Unknown(java.util.Optional.of(attempt(command)),java.util.Optional.empty(),
                "final religious business post unavailable",List.of(ORIGINAL)));
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(control(),unknown));
        var falsePost=new ActionState.ControlApplied(read("after",NOW.plusSeconds(1)),RootRiteCreationRuntimeFactory.OBSERVER,List.of());
        var relabelled=receipt(command,new ActionState.Settled(attempt(command),ack(),falsePost));
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(control(),relabelled));
        var actualRefusal=receipt(command,new ActionState.Settled(attempt(command),ack(),
                new ActionState.Rejected("software-request","known no-dispatch refusal DATA",ORIGINAL)));
        RootPlanningInputsFactory.requireSettledControl(control(),actualRefusal);
    }
    @Test void ordinaryAppliedReadSelectorsAndForeignObserversCannotBorrowRiteControlClassification() {
        var command=command(RiteCreation.OPEN_CREATE_DRAFT.operationKey().value());
        var effect=new ActionState.EffectObservation(command.before(),SOURCE,command.sessionId(),RootRiteCreationRuntimeFactory.OBSERVER,
                command.expected().values(),"software-read",NOW.plusSeconds(1),ORIGINAL);
        var applied=receipt(command,new ActionState.Settled(attempt(command),ack(),new ActionState.Applied(effect)));
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(control(),applied));
        var preview=command(RiteCreation.PREVIEW.operationKey().value());
        var rejected=receipt(preview,new ActionState.Settled(attempt(preview),ack(),new ActionState.Rejected("software-request","not a control",ORIGINAL)));
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(control(),rejected));
        var foreign=new ActionState.ControlApplied(read("after",NOW.plusSeconds(1)),AubOperations.OBSERVER,List.of());
        var foreignReceipt=receipt(command,new ActionState.Settled(attempt(command),ack(),foreign));
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(control(),foreignReceipt));
    }
}
