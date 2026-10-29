package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

final class ArmyOrdinaryPlannerCallsTest {
    @Test void everyInstalledOrdinarySelectionTraversesTheOriginalPublicCodecAndNativePrimitive() {
        Obj empty = new Obj(java.util.Map.of()); var source = ArmyOrdinaryActionBoundaryTest.context();
        List<String> steps = List.of("raise-troops-default", "move-army-0-to-31", "disband-army-0", "start-assault-7", "stop-assault-7",
                "enforce-demands-23", "surrender-war-23", "offer-white-peace-23", "declare-war-42-8--1", "close-war-declared-overview-v1", "close-war-results-window-v1");
        for (String step : steps) {
            var operation = new OperationKey(step); assertTrue(ArmyOrdinaryPlannerCalls.supports(operation));
            var call = ArmyOrdinaryPlannerCalls.decode(operation, empty, source.before().frame().revision(), "same-root-id");
            assertEquals(call, ArmyCallCodec.decode(call.method(), ArmyCallCodec.encode(call)));
            assertEquals(step, ArmyOrdinaryActionPreparation.primitive(call, source, List.of()).step());
            var actual = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionPreparation.kind(call), ArmyCallCodec.encode(call), List.of());
            ArmyOrdinaryPlannerSelection.requirePrepared(operation, empty, source.before().frame().revision(), actual);
        }
    }
    @Test void unknownOverlappingOriginalStillPreventsANewPreparedSelection() {
        var source = ArmyOrdinaryActionBoundaryTest.context();
        var call = ArmyOrdinaryPlannerCalls.decode(new OperationKey("move-army-0-to-31"), new Obj(java.util.Map.of()), source.before().frame().revision());
        var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionPreparation.kind(call), ArmyCallCodec.encode(call), List.of());
        var expected = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1, source.before(), source.source(), "controlled-test/v1",
                List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("actual"), true)));
        var command = new org.xar.ck3.control.application.action.ActionCommand("original-root-id", source.before(), source.source(), source.sessionId(),
                new OperationKey("move-army-0-to-31"), args.encode(), expected, ArmyOrdinaryActionPreparation.claims(call, source), source.deadline());
        var unknown = new org.xar.ck3.control.application.action.ActionReceipt(1, 1, command,
                org.xar.ck3.control.application.action.ActionCodec.bodySha256(command),
                new org.xar.ck3.control.application.action.ActionState.Unknown(java.util.Optional.empty(), java.util.Optional.empty(), "controlled original UNKNOWN", List.of(ArmyOrdinaryActionBoundaryTest.REF)));
        var next = ArmyOrdinaryPlannerCalls.decode(new OperationKey("disband-army-0"), new Obj(java.util.Map.of()), BigInteger.TEN);
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(List.of(unknown), next, source));
    }
}
