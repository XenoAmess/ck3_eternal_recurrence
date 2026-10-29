package org.xar.ck3.control.application.planning;

import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision.PreparedSelection;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPlannerSelection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

/** DATA-only command-custody regressions; no receipt reference here grants preflight or dispatch authority. */
final class MilitaryPreparedSelectionTest {
    private static final OperationKey RAISE = new OperationKey("raise-troops-default");

    @Test void existingExactFactoryRetainsTheOriginalSelectionAndRunsOnce() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var command = command(request, RAISE, selected.arguments());
        var calls = new java.util.concurrent.atomic.AtomicInteger();
        var draft = MilitaryPlanningDecision.draft(request, selected, (input, choice) -> {
            assertSame(request, input); assertSame(selected, choice); calls.incrementAndGet();
            return command;
        });
        assertSame(command, draft.command().orElseThrow());
        assertSame(selected.detail(), draft.detail());
        assertEquals(1, calls.get());
    }

    @Test void aLegacyBareFactoryCannotSneakInEnrichedOrArbitraryArguments() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var actual = command(request, RAISE, selected.arguments().with("unowned", new Text("extra")));
        assertThrows(IllegalArgumentException.class,
                () -> MilitaryPlanningDecision.draft(request, selected, (input, choice) -> actual));
    }

    @Test void theSingleArmySelectionProducerFeedsTheStrictPreparedConsumer() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var mapped = ArmyOrdinaryPlannerSelection.decode(RAISE, selected.arguments(), request.before().frame().revision());
        var arguments = new ArmyOrdinaryActionArguments(mapped.kind(), mapped.publicArguments(),
                List.of(new ExactRef("data-only-original-preflight", 1, "b".repeat(64))));
        var command = command(request, RAISE, arguments.encode());
        var token = PreparedSelection.army(command.actionId(), request, selected, command);
        var draft = MilitaryPlanningDecision.draft(request, selected, prepared(command, token));
        assertSame(command, draft.command().orElseThrow());
        assertEquals(arguments, ArmyOrdinaryActionArguments.decode(draft.command().orElseThrow().arguments()));
        assertSame(selected.detail(), draft.detail());
        assertNotEquals(selected.arguments(), command.arguments());
    }

    @Test void strictArmyPreparationRejectsAnotherRevisionOrActionKind() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var wrongRevision = ArmyOrdinaryPlannerSelection.decode(RAISE, selected.arguments(),
                request.before().frame().revision().add(java.math.BigInteger.ONE));
        var arguments = new ArmyOrdinaryActionArguments(wrongRevision.kind(), wrongRevision.publicArguments(), List.of());
        var command = command(request, RAISE, arguments.encode());
        assertThrows(IllegalArgumentException.class,
                () -> PreparedSelection.army(command.actionId(), request, selected, command));
        var correct = ArmyOrdinaryPlannerSelection.decode(RAISE, selected.arguments(), request.before().frame().revision());
        var otherKind = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1,
                correct.publicArguments(), List.of());
        var changed = command(request, RAISE, otherKind.encode());
        assertThrows(IllegalArgumentException.class,
                () -> PreparedSelection.army(changed.actionId(), request, selected, changed));
    }

    @Test void preparedCustodyRejectsChangedActionIdentityAndDeadline() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var actual = command(request, RAISE, selected.arguments());
        assertThrows(IllegalArgumentException.class,
                () -> PreparedSelection.exact("another-action", request, selected, actual));
        var changed = new ActionCommand(actual.actionId(), actual.before(), actual.source(), actual.sessionId(),
                actual.operation(), actual.arguments(), actual.expected(), actual.claims(), actual.deadline().plusSeconds(1));
        assertThrows(IllegalArgumentException.class,
                () -> PreparedSelection.exact(actual.actionId(), request, selected, changed));
    }

    @Test void aTokenCannotBeReusedForAnEqualButDifferentOriginalRequestOrSelection() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var command = command(request, RAISE, selected.arguments());
        var token = PreparedSelection.exact(command.actionId(), request, selected, command);
        var copiedRequest = request(snapshot(), List.of(), Set.of(RAISE));
        var copiedSelection = selection(RAISE);
        assertEquals(request, copiedRequest);
        assertEquals(selected, copiedSelection);
        assertThrows(IllegalArgumentException.class,
                () -> MilitaryPlanningDecision.draft(copiedRequest, selected, prepared(command, token)));
        assertThrows(IllegalArgumentException.class,
                () -> MilitaryPlanningDecision.draft(request, copiedSelection, prepared(command, token)));
    }

    @Test void choosingTheLifeBranchDoesNotAdmitAnArmyEnvelope() {
        var request = request(snapshot(), List.of(), Set.of(RAISE));
        var selected = selection(RAISE);
        var command = command(request, RAISE, selected.arguments());
        assertThrows(IllegalArgumentException.class,
                () -> PreparedSelection.life(command.actionId(), request, selected, command));
    }

    private static MilitaryPlanningDecision.CommandFactory prepared(ActionCommand actual, PreparedSelection token) {
        return new MilitaryPlanningDecision.CommandFactory() {
            @Override public ActionCommand create(PlanningRequest request, MilitaryPlanningDecision.Select selected) {
                throw new AssertionError("the actual owner already prepared this command once");
            }
            @Override public PreparedSelection prepare(PlanningRequest request, MilitaryPlanningDecision.Select selected) {
                assertSame(actual, token.command());
                return token;
            }
        };
    }

    private static MilitaryPlanningDecision.Select selection(OperationKey operation) {
        String policy = "one-life-turn-v1", phase = "native_war_raise", reason = "retain the exact original selection";
        var detail = new Obj(Map.of("selected_step", new Text(operation.value()), "policy", new Text(policy),
                "phase", new Text(phase), "reason", new Text(reason)));
        return new MilitaryPlanningDecision.Select(policy, phase, reason, operation, new Obj(Map.of()),
                OrdinaryPolicy.Purpose.WORLD_ACTION, detail);
    }
}

