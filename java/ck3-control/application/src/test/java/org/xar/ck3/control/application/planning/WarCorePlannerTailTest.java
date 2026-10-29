package org.xar.ck3.control.application.planning;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

final class WarCorePlannerTailTest {
    @Test void anActualRankedLeafRunsAfterTheObjectiveSourceAndRetainsTheWholePlan() {
        var calls = new ArrayList<WarCorePlanner.Boundary>();
        var request = warRequest();
        var expected = new MilitaryPlanningDecision.Hold("one-life-turn-v1", "native_war_route_hold",
                "original ranked route found a current-frame hold", Optional.empty(),
                new OpportunityJson.Obj(java.util.Map.of("native_original_fact", new OpportunityJson.Text("retained"))));
        var planner = planner(calls, WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE, expected, request, false);
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, planner.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals("native_war_route_hold", result.draft().phase());
        assertEquals(expected.detail(), result.draft().detail());
        assertEquals(WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE, calls.getLast());
        assertTrue(calls.indexOf(WarCorePlanner.Boundary.OBJECTIVE_SOURCE_SELECTION)
                < calls.indexOf(WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE));
        assertFalse(calls.contains(WarCorePlanner.Boundary.DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT));
    }
    @Test void exhaustedRankedRoutesReachTheDefensiveFallbackInsteadOfInventingIncompleteMigration() {
        var calls = new ArrayList<WarCorePlanner.Boundary>(); var request = warRequest();
        var planner = planner(calls, WarCorePlanner.Boundary.DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT,
                new MilitaryPlanningDecision.Hold("one-life-turn-v1", "native_war_defensive_hold",
                        "actual fallback hold", Optional.empty(), new OpportunityJson.Obj(java.util.Map.of())), request, false);
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, planner.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals("native_war_defensive_hold", result.draft().phase());
        assertTrue(result.draft().command().isEmpty());
        assertEquals(Arrays.asList(WarCorePlanner.Boundary.values()), calls);
        assertTrue(planner.missingBoundaries().isEmpty());
    }
    @Test void missingRankedProducerIsNamedAndDoesNotFallThroughToTheLaterFallback() {
        var calls = new ArrayList<WarCorePlanner.Boundary>(); var request = warRequest();
        var planner = planner(calls, WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE, null, request, false);
        assertEquals(List.of(WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE), planner.missingBoundaries());
        var result = assertInstanceOf(OrdinaryPolicy.Stop.class, planner.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, result.stopReason());
        assertTrue(result.reason().contains("ORDINARY_RANKED_ROUTE"));
        assertFalse(calls.contains(WarCorePlanner.Boundary.DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT));
    }
    @Test void unknownTacticsNeverBecomeAnEmptySafeSetOrReachTheLateFallback() {
        var calls = new ArrayList<WarCorePlanner.Boundary>(); var request = warRequest();
        var planner = planner(calls, WarCorePlanner.Boundary.DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT,
                new MilitaryPlanningDecision.Keep(new OpportunityJson.Obj(java.util.Map.of())), request, true);
        var result = assertInstanceOf(OrdinaryPolicy.Stop.class, planner.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertTrue(result.reason().contains("route_tactics_actual_provider"));
        assertFalse(calls.contains(WarCorePlanner.Boundary.ASSAULT_AND_ARMY_STATE));
        assertFalse(calls.contains(WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE));
    }
    @Test void registeredEventCoreCannotBeBypassedByAnActiveWarPrelude() {
        var request = warRequest(); var calls = new ArrayList<WarCorePlanner.Boundary>();
        var war = planner(calls, WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE,
                new MilitaryPlanningDecision.Unavailable(List.of("should_not_run"), "war should not preempt the active event"), request, false);
        var core = new OrdinaryCorePolicy(SOURCE, war,
                (input, previous) -> new OrdinaryPolicy.Wait("the registered active event requires its exact current option"),
                (input, previous) -> { throw new AssertionError("council must not preempt an active event"); },
                (input, previous) -> { throw new AssertionError("marriage must not preempt an active event"); },
                (input, previous) -> { throw new AssertionError("war entry must not preempt an active event"); },
                (input, operation, arguments, plan, purpose, domain) -> { throw new AssertionError("blocked event cannot submit"); },
                step -> step.equals("life-advance"));
        var result = assertInstanceOf(OrdinaryPolicy.Wait.class, core.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertTrue(result.reason().contains("registered active event")); assertTrue(calls.isEmpty());
    }
    @Test void latchedAssaultGuardPreventsAStagedPendingReplyFromBeingConsumed() {
        var calls = new ArrayList<WarCorePlanner.Boundary>(); var request = warRequest();
        var planner = planner(calls, WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE,
                new MilitaryPlanningDecision.Hold("one-life-turn-v1", "native_war_assault_lifecycle_blocked",
                        "the exact started SiegeID lifecycle is unobservable", Optional.empty(),
                        new OpportunityJson.Obj(java.util.Map.of())), request, false);
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, planner.evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals("native_war_assault_lifecycle_blocked", result.draft().phase());
        assertTrue(calls.contains(WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_PRELUDE));
        assertTrue(calls.contains(WarCorePlanner.Boundary.BATTLE_CONTROL_PRELUDE));
        assertFalse(calls.contains(WarCorePlanner.Boundary.PENDING_WAR_INTERACTION_CONSUMPTION));
    }
    private static PlanningRequest warRequest() {
        var war = new OpportunityJson.Obj(java.util.Map.of("war_id", integer(1),
                "allied_armies", new OpportunityJson.Arr(List.of()), "enemy_armies", new OpportunityJson.Arr(List.of())));
        return request(snapshot().with("active_wars", new OpportunityJson.Arr(List.of(war))), List.of(), Set.of());
    }
    private static WarCorePlanner planner(List<WarCorePlanner.Boundary> calls, WarCorePlanner.Boundary selected,
            MilitaryPlanningDecision answer, PlanningRequest request, boolean unknownTactics) {
        var leaves = new ArrayList<WarCorePlanner.Leaf>();
        for (var boundary : WarCorePlanner.Boundary.values()) {
            if (boundary == selected && answer == null) continue;
            leaves.add(new WarCorePlanner.Leaf(boundary, SOURCE, (input, previous) -> {
                calls.add(boundary);
                return boundary == selected ? answer : new MilitaryPlanningDecision.Keep(new OpportunityJson.Obj(java.util.Map.of()));
            }));
        }
        PlanningReadPort reads = new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest read) {
                throw new AssertionError("these real hold boundaries must not perform a query");
            }
        };
        return new WarCorePlanner(leaves,
                input -> unknownTactics ? new WarCorePlanner.UnknownTactics(List.of("route_tactics_actual_provider"))
                        : new WarCorePlanner.KnownTactics(request.before(), new WarCorePlanner.RouteTactics(Set.of(), Set.of())),
                (input, selection) -> { throw new AssertionError("a hold is never a world command"); },
                reads, (input, selection) -> { throw new AssertionError("no readonly query in this production regression path"); },
                (input, previous) -> { throw new AssertionError("no transition replan in these cases"); });
    }
}
