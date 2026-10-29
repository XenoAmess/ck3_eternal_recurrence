package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryPlannerSelection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowKind;

/** Software producer/custody regression. Synthetic receipts grant no native/Game authority. */
final class EventForegroundPreparedCommandTest {
    private static final Obj EMPTY = new Obj(Map.of());
    private static final ExactRef SYNTHETIC_READ = new ExactRef("software-window-read", 1, "b".repeat(64));
    private static final PlanningReadPort NO_READS = new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            throw new AssertionError("an already collected foreground window needs no second observation");
        }
    };

    @Test void bothWindowProducersRetainActualOwnerPreparedCommandAndStrictJsonRoundTrip() {
        for (WindowKind kind : WindowKind.values()) {
            PlanningRequest request = request(kind, false);
            AtomicReference<ActionCommand> original = new AtomicReference<>();
            AtomicReference<Obj> originalPlan = new AtomicReference<>();
            AtomicInteger calls = new AtomicInteger();
            OrdinaryCorePolicy.CommandBinding owner = (actual, operation, arguments, plan, purpose, domain) -> {
                assertSame(request, actual);
                assertEquals(kind.closeStep(), operation.value());
                assertEquals(EMPTY, arguments);
                assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION, purpose);
                assertTrue(domain.isEmpty());
                calls.incrementAndGet(); originalPlan.set(plan);
                ActionCommand command = armyCommand(actual, operation, arguments);
                original.set(command);
                return new OrdinaryCorePolicy.OwnerPrepared(MilitaryPlanningDecision.PreparedSelection.army(
                        command.actionId(), actual, selection(operation, arguments, plan), command));
            };
            var result = assertInstanceOf(OrdinaryPolicy.Replace.class,
                    policy(request, owner).evaluate(request, OrdinaryPolicy.Draft.empty()));
            ActionCommand command = result.draft().command().orElseThrow();
            assertSame(original.get(), command);
            assertSame(originalPlan.get(), result.draft().detail());
            assertNotEquals(result.draft().detail(), command.arguments());
            assertEquals(1, calls.get());
            var decoded = ArmyOrdinaryActionArguments.decode(command.arguments());
            assertEquals(List.of(SYNTHETIC_READ), decoded.preflightReads());
            assertEquals(Set.of("software-shared-window-claim"), command.claims().commitmentKeys());
            assertEquals(new Text("1"), org.xar.ck3.control.application.driver.DriverJson.object(
                    decoded.publicArguments().bytes(), 65536).get("expected_revision"));
            assertEquals(new Bool(false), OpportunityJson.object(result.draft().detail().get(kind.phase()),
                    "original window summary").get("close_action_credit"));
            ActionCommand restored = ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
            assertEquals(command, restored);
            assertEquals(command.origin(), restored.origin());
            assertEquals(command.expected(), restored.expected());
            assertEquals(command.claims(), restored.claims());
            assertEquals(decoded, ArmyOrdinaryActionArguments.decode(restored.arguments()));
        }
    }

    @Test void missingActualOwnerPreparationProducesIncompleteWithoutInventingAnExpectedOrCommand() {
        PlanningRequest request = request(WindowKind.RESULTS, false);
        AtomicInteger calls = new AtomicInteger();
        var result = assertInstanceOf(OrdinaryPolicy.Stop.class, policy(request,
                (actual, operation, arguments, plan, purpose, domain) -> {
                    calls.incrementAndGet(); assertEquals(EMPTY, arguments);
                    return new OrdinaryCorePolicy.MissingHandler("actual owner preflight receipt unavailable");
                }).evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, result.stopReason());
        assertEquals(1, calls.get());
    }

    @Test void actualOwnerCustodyRejectsACommandPreparedForAnotherOriginalPlan() {
        PlanningRequest request = request(WindowKind.DECLARED_OVERVIEW, false);
        assertThrows(IllegalArgumentException.class, () -> policy(request,
                (actual, operation, arguments, plan, purpose, domain) -> {
                    Map<String, Value> changed = new HashMap<>(plan.members());
                    changed.put("unrelated_added_detail", new Bool(true));
                    ActionCommand command = armyCommand(actual, operation, arguments);
                    return new OrdinaryCorePolicy.OwnerPrepared(MilitaryPlanningDecision.PreparedSelection.army(
                            command.actionId(), actual, selection(operation, arguments, new Obj(changed)), command));
                }).evaluate(request, OrdinaryPolicy.Draft.empty()));
    }

    @Test void legacyExactBranchCannotSmuggleAnEnrichedArmyEnvelope() {
        PlanningRequest request = request(WindowKind.RESULTS, false);
        assertThrows(IllegalArgumentException.class, () -> policy(request,
                (actual, operation, arguments, plan, purpose, domain) ->
                    new OrdinaryCorePolicy.Prepared(armyCommand(actual, operation, arguments)))
                .evaluate(request, OrdinaryPolicy.Draft.empty()));
    }

    @Test void unknownOriginalCloseDoesNotPrepareOrSubmitAnotherCloseForEitherWindow() {
        for (WindowKind kind : WindowKind.values()) {
            PlanningRequest request = request(kind, true);
            assertInstanceOf(OrdinaryPolicy.Wait.class, policy(request,
                    (actual, operation, arguments, plan, purpose, domain) -> {
                        throw new AssertionError("UNKNOWN original close must never be prepared again");
                    }).evaluate(request, OrdinaryPolicy.Draft.empty()));
        }
    }

    private static OrdinaryPolicy policy(PlanningRequest request, OrdinaryCorePolicy.CommandBinding binding) {
        return EventPolicies.policies(request.source().sourceRef(), Optional.empty(),
                (actual, operation, plan, trait) -> { throw new AssertionError("foreground must use actual shared preparation"); },
                NO_READS, List.of(),
                (actual, raw) -> { throw new AssertionError("no event context expected for Window2"); },
                (actual, retained) -> { throw new AssertionError("no unknown-event capture expected for Window2"); }, binding)
                .stream().filter(row -> row.stage() == PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS)
                .findFirst().orElseThrow();
    }

    private static MilitaryPlanningDecision.Select selection(OperationKey operation, Obj args, Obj plan) {
        return new MilitaryPlanningDecision.Select(OpportunityJson.text(plan.get("policy"), "policy"),
                OpportunityJson.text(plan.get("phase"), "phase"), OpportunityJson.text(plan.get("reason"), "reason"),
                operation, args, OrdinaryPolicy.Purpose.WORLD_ACTION, plan);
    }

    private static ActionCommand armyCommand(PlanningRequest request, OperationKey operation, Obj selectedArgs) {
        var selected = ArmyOrdinaryPlannerSelection.decode(operation, selectedArgs, request.before().frame().revision());
        var envelope = new ArmyOrdinaryActionArguments(selected.kind(), selected.publicArguments(), List.of(SYNTHETIC_READ));
        ActionCommand exact = PlanningFixtures.command(request, operation, envelope.encode());
        return new ActionCommand(exact.actionId(), exact.origin(), exact.source(), exact.sessionId(), exact.operation(),
                exact.arguments(), exact.expectation(), new JointBudgetSelector.Claims(Set.of(), Set.of(),
                    Set.of(request.before().frame().identity().player()), Set.of("software-shared-window-claim")), exact.deadline());
    }

    private static PlanningRequest request(WindowKind kind, boolean pending) {
        Map<String, Value> fields = new HashMap<>(PlanningFixtures.snapshot().members());
        fields.put(kind.publicPrefix() + "_observation", new Obj(Map.ofEntries(
                Map.entry("sdk_validation_schema", new Text(kind.sourceSchema())),
                Map.entry("queried_snapshot_id", new Text("snapshot-1")),
                Map.entry("queried_revision", PlanningFixtures.integer(1)),
                Map.entry("queried_native_revision", PlanningFixtures.integer(1)),
                Map.entry("queried_date_raw", PlanningFixtures.integer(24000)),
                Map.entry("queried_actor_character_id", PlanningFixtures.integer(29829)),
                Map.entry("queried_connection_generation", PlanningFixtures.integer(1)),
                Map.entry("queried_episode_run_id", new Text("episode-1")),
                Map.entry("available", new Bool(true)), Map.entry("post_observed", new Bool(true)),
                Map.entry("scope_unchanged", new Bool(true)), Map.entry("post_window_present", new Bool(true)),
                Map.entry("post_effective_visible", new Bool(true)),
                Map.entry("close_retry_deferred_for_native_frame", new Bool(false)),
                Map.entry("accepted", new Bool(false)), Map.entry("dispatch_attempted", new Bool(false)),
                Map.entry("dispatch_invoked", new Bool(false)))));
        if (pending) fields.put(kind.publicPrefix() + "_close_pending", new Obj(Map.of(
                "native_request_id", new Text("original-close-unknown"), "status", new Text("UNKNOWN"))));
        PlanningRequest base = PlanningFixtures.request(new Obj(fields), List.of(), Set.of(new OperationKey(kind.closeStep())));
        var observed = base.observations();
        return new PlanningRequest(base.before(), base.source(), base.sessionId(), base.deadline(),
                new PlanningObservation(observed.snapshot(), observed.history(), observed.actionSteps(),
                        Set.of(kind.closeCapability()), observed.battleSpeedReadiness(), observed.actionFacts(),
                        observed.campaignGoal(), observed.crossRunPlan(), observed.initialLifestyleFocusRequired()));
    }
}
