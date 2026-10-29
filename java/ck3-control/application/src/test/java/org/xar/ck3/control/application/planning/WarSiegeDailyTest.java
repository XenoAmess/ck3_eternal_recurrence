package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Raw native/history input through the actual Java daily producers and both leaves. */
final class WarSiegeDailyTest {
    private static Obj json(String value) {
        return OpportunityJson.object(OpportunityJson.parse(value.getBytes(StandardCharsets.UTF_8)), "daily fixture");
    }
    private static Obj fixed(long value) { return obj(f("raw", number(value)), f("scale", number(100000))); }
    private static Obj siege(int siege, int army, long work, boolean active) {
        return obj(f("siege_id", number(siege)), f("besieging_army_id", number(army)),
                f("player_army_besieging", new Bool(true)), f("current_work", fixed(work)),
                f("progress_fraction", fixed(work)), f("remaining_work", fixed(100000 - work)),
                f("total_work", fixed(100000)), f("days_left", number(10)),
                f("assault_observable", new Bool(true)), f("assault_in_progress", new Bool(active)),
                f("breach_level", number(1)), f("can_start_assault", new Bool(true)),
                f("can_stop_assault", new Bool(true)), f("assault_daily_progress", fixed(50)),
                f("assault_daily_casualties", number(20)));
    }
    private static Obj state(Obj siege, long strength, long garrison) {
        return obj(f("province_id", number(50)), f("siege_observable", new Bool(true)),
                f("active_siege", siege), f("besieging_strength", number(strength)), f("garrison_size", number(garrison)));
    }
    private static Obj armyRow(int id, String state) {
        return obj(f("army_id", number(id)), f("current_province_id", number(50)),
                f("owner_character_id", number(29829)), f("controllable", new Bool(true)),
                f("army_state", text(state)), f("in_combat", new Bool("combat".equals(state))),
                f("retreating", new Bool("retreating".equals(state))), f("move_target_province_id", Nil.INSTANCE),
                f("route_province_ids", new Arr(List.of())), f("route_read_status", text("complete_empty")),
                f("route_source_count", number(0)), f("move_target_observable", new Bool(false)));
    }
    private static Obj war(Obj state, Obj army) {
        return obj(f("war_id", number(88)), f("player_side", text("attacker")),
                f("player_is_primary_war_leader", new Bool(true)), f("player_relative_war_score", number(0)),
                f("war_objective_province_ids", numbers(List.of(50))), f("objective_province_states", objects(List.of(state))),
                f("player_armies", objects(List.of(army))), f("allied_armies", objects(List.of())), f("enemy_armies", objects(List.of())));
    }
    private static Obj snapshotFor(Obj state, Obj army) {
        return snapshot().with("war_objective_siege_progress_supported", new Bool(true))
                .with("war_objective_garrison_supported", new Bool(true))
                .with("war_objective_assault_supported", new Bool(true))
                .with("active_wars", objects(List.of(war(state, army)))).with("player_armies", objects(List.of(army)));
    }
    private static Obj slice(int index, long date, int days, Obj before, Obj after, Obj beforeArmy, Obj afterArmy) {
        return obj(f("index", number(index)), f("command", text("life-advance")), f("ok", new Bool(true)),
                f("result", obj(f("war_progress_before", obj(f("date_raw", number(date)), f("wars", objects(List.of(war(before, beforeArmy)))))),
                        f("war_progress_after", obj(f("date_raw", number(date + 24L * days)), f("wars", objects(List.of(war(after, afterArmy)))))))));
    }
    private static Obj start() {
        return obj(f("index", number(1)), f("command", text("start-assault-9")), f("ok", new Bool(true)),
                f("result", obj(f("assault_action", obj(f("status", text("assault_started")),
                        f("siege_id", number(9)), f("war_id", number(88)), f("province_id", number(50)))))));
    }
    private static EarlyWarCoreInputs.Actual actual(PlanningRequest request, Obj state, Obj army,
            Set<Integer> unsafe, Set<Integer> threatened, Set<Integer> startBlocking, Obj tactical) {
        var subject = MilitaryPlanInputs.army(army); Obj war = war(state, army);
        var context = new WarContactObservation.Context(List.of(subject), List.of(), List.of(), List.of(), List.of(),
                unsafe, threatened, startBlocking, Optional.of(subject), Optional.of(88), Optional.empty());
        var contact = new WarContactObservation.KnownContact(request.before(), request.source(), context);
        Obj relief = obj(f("status", text("not_applicable")));
        var objectives = WarObjectiveSources.collect(request, war, subject, relief, tactical);
        var exactSiege = WarSiegeDaily.siege(request, 88, 50, objectives.exactStates(), Optional.of(subject));
        var exactAssault = WarSiegeDaily.assault(request, 88, 50, objectives.exactStates(), List.of(), exactSiege);
        return new EarlyWarCoreInputs.Actual(request.before(), contact, subject, war, 88, Optional.empty(), relief,
                objectives, WarSiegeDaily.reviews(request, List.of()), exactSiege, exactAssault, tactical,
                List.of(war), obj(f("evidence", objects(List.of())), f("transitions", objects(List.of()))));
    }
    private static Obj tactical(int retreatDays) {
        return obj(f("retreat_days", number(retreatDays)), f("completed_objective_province_ids", numbers(List.of())),
                f("blocked_province_ids", numbers(List.of())));
    }

    @Test void rawCurrentProducerToAllReviewConsumersPreservesOneDayAndExactStrengthEquality() {
        Obj state = state(siege(9, 0, 100, false), 120, 100), army = armyRow(0, "sieging");
        Obj snapshot = snapshotFor(state, army);
        List<Obj> reviews = WarSiegeDaily.reviews(snapshot, List.of(), List.of(war(state, army)), List.of());
        assertEquals(1, reviews.size()); Obj review = reviews.getFirst();
        assertEquals(new Bool(true), review.get("one_day_safe"));
        assertEquals(number(100), review.get("projected_strength_after_one_day"));
        assertEquals(number(1), review.get("projection_horizon_days"));
        assertFalse(review.members().containsKey("eta_days"));
        assertEquals(review, OpportunityJson.parse(OpportunityJson.encode(review)));
        Obj below = state(siege(9, 0, 100, false), 119, 100);
        Obj rejected = WarSiegeDaily.assault(snapshot, List.of(), 88, 50, Map.of(50, below), List.of(), Optional.empty()).orElseThrow();
        assertEquals(new Bool(false), rejected.get("one_day_safe"));
        assertTrue(((Arr)rejected.get("one_day_rejection_reasons")).items().contains(text("projected_strength_below_garrison")));
    }

    @Test void realizedBesiegingStrengthControlsNextDayWithoutInventingArmySoldiers() {
        Obj army = armyRow(0, "sieging"), before = state(siege(9, 0, 100, true), 1000, 200),
                after = state(siege(9, 0, 200, true), 900, 200);
        Obj row = slice(2, 24000, 1, before, after, army, army);
        Obj observed = WarSiegeDaily.previousDay(List.of(start(), row), 88, 50, 9).orElseThrow();
        assertEquals(number(1), observed.get("elapsed_days")); assertEquals(number(100), observed.get("strength_loss"));
        assertEquals(Nil.INSTANCE, observed.get("soldier_loss"));
        Obj review = WarSiegeDaily.assault(snapshotFor(after, army), List.of(start(), row), 88, 50,
                Map.of(50, after), List.of(), Optional.empty()).orElseThrow();
        assertEquals(new Bool(true), review.get("one_day_safe"));
        assertEquals(observed, review.get("previous_assault_day"));
    }

    @Test void newestFailedSliceAfterProvenStartHidesOldSuccessAndBlocksNextDay() {
        Obj army = armyRow(0, "sieging"), before = state(siege(9, 0, 100, true), 1000, 200),
                after = state(siege(9, 0, 200, true), 900, 200);
        Obj good = slice(2, 24000, 1, before, after, army, army);
        Obj failed = slice(3, 24024, 1, after, after, army, army).with("ok", new Bool(false));
        var history = List.of(start(), good, failed);
        Obj latest = WarSiegeDaily.previousDay(history, 88, 50, 9).orElseThrow();
        assertEquals(text("previous_assault_slice_failed_unknown"), latest.get("reason"));
        assertEquals(Nil.INSTANCE, latest.get("elapsed_days"));
        Obj review = WarSiegeDaily.assault(snapshotFor(after, army), history, 88, 50, Map.of(50, after), List.of(), Optional.empty()).orElseThrow();
        assertEquals(new Bool(false), review.get("one_day_safe"));
        assertTrue(((Arr)review.get("one_day_rejection_reasons")).items().contains(text("previous_assault_slice_failed_unknown")));
    }

    @Test void newestUnavailableOrMultiDaySliceDoesNotBorrowEarlierSafeObservation() {
        Obj army = armyRow(0, "sieging"), current = state(siege(9, 0, 200, true), 900, 200);
        Obj before = state(siege(9, 0, 100, true), 1000, 200);
        Obj twoDays = slice(2, 24000, 2, before, current, army, army);
        Obj review = WarSiegeDaily.assault(snapshotFor(current, army), List.of(start(), twoDays), 88, 50,
                Map.of(50, current), List.of(), Optional.empty()).orElseThrow();
        assertTrue(((Arr)review.get("one_day_rejection_reasons")).items().contains(text("previous_assault_slice_not_one_day")));
        Obj unavailable = slice(3, 24048, 1, state(siege(10, 0, 100, true), 900, 200), current, army, army);
        assertEquals(text("previous_assault_slice_state_unavailable"),
                WarSiegeDaily.previousDay(List.of(start(), twoDays, unavailable), 88, 50, 9).orElseThrow().get("reason"));
    }

    @Test void onlySuccessfulRestoreTruncatesTheAssaultBranchAndStallEvidence() {
        Obj army = armyRow(0, "sieging"), state = state(siege(9, 0, 100, true), 1000, 200);
        Obj stalled = slice(2, 24000, 7, state, state, army, army);
        Obj restore = obj(f("index", number(3)), f("command", text("restore-checkpoint")), f("ok", new Bool(true)),
                f("result", obj(f("status", text("restored")))));
        assertTrue(WarSiegeDaily.previousDay(List.of(start(), stalled, restore), 88, 50, 9).isEmpty());
        assertEquals(BigInteger.ZERO, WarSiegeDaily.stallDays(List.of(start(), stalled, restore), 88, 50, 9));
        assertEquals(BigInteger.valueOf(7), WarSiegeDaily.stallDays(List.of(start(), stalled, restore.with("ok", new Bool(false))), 88, 50, 9));
    }

    @Test void publicUnitZeroCountsExactStallButCombatGenerationAndProgressBreakTheStreak() {
        Obj army = armyRow(0, "sieging"), state = state(siege(9, 0, 100, false), 1000, 200);
        Obj seven = slice(1, 24000, 7, state, state, army, army);
        assertEquals(BigInteger.valueOf(7), WarSiegeDaily.stallDays(List.of(seven), 88, 50, 9));
        Obj result = WarSiegeDaily.siege(snapshotFor(state, army), List.of(seven), 88, 50, Map.of(50, state), Optional.of(MilitaryPlanInputs.army(army))).orElseThrow();
        assertEquals(text("stalled"), result.get("status"));
        Obj combat = slice(2, 24168, 1, state, state, armyRow(0, "combat"), armyRow(0, "combat"));
        Obj two = slice(3, 24192, 2, state, state, army, army);
        assertEquals(BigInteger.TWO, WarSiegeDaily.stallDays(List.of(seven, combat, two), 88, 50, 9));
        Obj advanced = state.with("active_siege", ((Obj)state.get("active_siege")).with("progress_fraction", fixed(101)));
        assertEquals(BigInteger.ZERO, WarSiegeDaily.stallDays(List.of(seven, slice(2, 24168, 1, state, advanced, army, army)), 88, 50, 9));
        Obj replacement = state(siege(10, 0, 100, false), 1000, 200);
        assertEquals(BigInteger.ZERO, WarSiegeDaily.stallDays(List.of(seven, slice(2, 24168, 1, state, replacement, army, army)), 88, 50, 9));
    }

    @Test void measuredSubjectContributionRequiresEveryOccurrenceRatherThanSelectionMatch() {
        Obj army = armyRow(0, "sieging");
        Obj first = obj(f("public_unit_id", number(0)), f("native_carmy_id", number(11)), f("eligible", new Bool(true)), f("occurrence_index", number(0)));
        Obj second = first.with("occurrence_index", number(1)).with("eligible", new Bool(false));
        Obj siege = siege(0, 7, 0, false).with("player_army_besieging", new Bool(false))
                .with("province_unit_occurrences", objects(List.of(first, second)));
        Obj state = state(siege, 1000, 200).with("current_besieging_army_selection", obj(f("native_carmy_id", number(99))));
        Obj contribution = WarSiegeDaily.subjectContribution(state, Optional.of(MilitaryPlanInputs.army(army)));
        assertEquals(text("excluded"), contribution.get("status"));
        assertEquals(new Bool(false), contribution.get("matches_current_selection"));
        Obj selected = WarSiegeDaily.siege(snapshotFor(state, army), List.of(), 88, 50, Map.of(50, state), Optional.of(MilitaryPlanInputs.army(army))).orElseThrow();
        assertEquals(text("not_player_besieging"), selected.get("status"));
        assertEquals(number(0), selected.get("siege_id"));
        Obj allEligible = state.with("active_siege", siege.with("province_unit_occurrences", objects(List.of(first, second.with("eligible", new Bool(true))))));
        assertEquals(text("progressing"), WarSiegeDaily.siege(snapshotFor(allEligible, army), List.of(), 88, 50, Map.of(50, allEligible),
                Optional.of(MilitaryPlanInputs.army(army))).orElseThrow().get("status"));
        Obj wrongType = state.with("active_siege", siege.with("province_unit_occurrences", objects(List.of(first.with("eligible", number(1))))));
        assertEquals(text("unavailable"), WarSiegeDaily.subjectContribution(wrongType, Optional.of(MilitaryPlanInputs.army(army))).get("status"));
    }

    @Test void everyPrimarySiegeIsReviewedAndZeroIdentitySortsWithoutBecomingAnAssaultCommand() {
        Obj army = armyRow(0, "sieging"), zero = state(siege(0, 0, 100, false), 1000, 200);
        Obj second = state(siege(2, 7, 100, false), 1000, 200).with("province_id", number(51));
        Obj nonPrimary = state(siege(1, 8, 100, false).with("player_army_besieging", new Bool(false)), 1000, 200).with("province_id", number(52));
        Obj war = war(zero, army).with("objective_province_states", objects(List.of(zero, second, nonPrimary)));
        Obj snapshot = snapshotFor(zero, army).with("active_wars", objects(List.of(war)));
        var reviews = WarSiegeDaily.reviews(snapshot, List.of(), List.of(war), List.of(MilitaryPlanInputs.army(armyRow(0, "regular"))));
        assertEquals(2, reviews.size());
        assertEquals(number(2), reviews.getFirst().get("siege_id"));
        assertEquals(number(0), reviews.getLast().get("siege_id"));
        assertEquals(new Bool(false), reviews.getLast().get("one_day_safe"));
        assertTrue(((Arr)reviews.getLast().get("one_day_rejection_reasons")).items().contains(text("enemy_convergence_observed")));
        var request = request(snapshotFor(zero, army), List.of(), Set.of(new OperationKey("start-assault-0")));
        assertInstanceOf(MilitaryPlanningDecision.Keep.class, WarSiegeDaily.armyState(request,
                actual(request, zero, army, Set.of(), Set.of(), Set.of(), tactical(0))));
    }

    @Test void integerBoundariesRejectBooleanAndFloatAndMissingRemainDifferentFromZero() {
        Obj army = armyRow(0, "sieging"), good = state(siege(9, 0, 100, true), 1000, 200);
        for (Value invalid : List.<Value>of(new Bool(true), json("{\"value\":20.0}").get("value"), Nil.INSTANCE)) {
            Obj bad = good.with("active_siege", ((Obj)good.get("active_siege")).with("assault_daily_casualties", invalid));
            Obj review = WarSiegeDaily.assault(snapshotFor(bad, army), List.of(), 88, 50, Map.of(50, bad), List.of(), Optional.empty()).orElseThrow();
            assertEquals(new Bool(false), review.get("one_day_safe"));
            assertTrue(((Arr)review.get("one_day_rejection_reasons")).items().contains(text("daily_casualties_unavailable")));
        }
        Obj zero = good.with("active_siege", ((Obj)good.get("active_siege")).with("siege_id", number(0)));
        Obj observed = WarSiegeDaily.assault(snapshotFor(zero, army), List.of(), 88, 50, Map.of(50, zero), List.of(), Optional.empty()).orElseThrow();
        assertEquals(number(0), observed.get("siege_id"));
        Obj missing = good.with("active_siege", ((Obj)good.get("active_siege")).with("siege_id", new Bool(false)));
        assertEquals(Nil.INSTANCE, WarSiegeDaily.assault(snapshotFor(missing, army), List.of(), 88, 50, Map.of(50, missing), List.of(), Optional.empty()).orElseThrow().get("siege_id"));
    }

    @Test void actualRawProducerFeedsTheTwoRegisteredBoundaryLeavesAndStartIsNotAConfirmation() {
        Obj army = armyRow(0, "sieging"), state = state(siege(9, 0, 100, false), 1000, 200);
        var request = request(snapshotFor(state, army), List.of(), Set.of(new OperationKey("start-assault-9")));
        var actual = actual(request, state, army, Set.of(), Set.of(), Set.of(), tactical(0));
        var leaves = WarSiegeDaily.factories(SOURCE, (input, previous) -> new EarlyWarCoreInputs.Available(actual));
        assertEquals(List.of(WarCorePlanner.Boundary.ASSAULT_STABILITY, WarCorePlanner.Boundary.ASSAULT_AND_ARMY_STATE),
                leaves.stream().map(WarCorePlanner.Leaf::boundary).toList());
        assertInstanceOf(MilitaryPlanningDecision.Keep.class, leaves.getFirst().producer().evaluate(request, OrdinaryPolicy.Draft.empty()));
        var selected = assertInstanceOf(MilitaryPlanningDecision.Select.class, leaves.getLast().producer().evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertEquals("start-assault-9", selected.operation().value());
        assertEquals(OrdinaryPolicy.Purpose.WORLD_ACTION, selected.purpose());
        assertFalse(selected.detail().members().containsKey("native_confirmed"));
        assertTrue(AssaultLifecycle.open(request.observations().history()).isEmpty());
        assertEquals(selected.detail(), OpportunityJson.parse(OpportunityJson.encode(selected.detail())));
    }

    @Test void unsafeDailyReviewStopsBeforeTimeAndAnUnadvertisedStopProducesHold() {
        Obj army = armyRow(0, "sieging"), state = state(siege(9, 0, 100, true).with("assault_daily_progress", fixed(0)), 1000, 200);
        for (boolean advertised : List.of(false, true)) {
            var request = request(snapshotFor(state, army), List.of(), advertised ? Set.of(new OperationKey("stop-assault-9")) : Set.of(new OperationKey("life-advance")));
            var actual = actual(request, state, army, Set.of(), Set.of(), Set.of(), tactical(0));
            var result = WarSiegeDaily.stability(request, actual);
            if (advertised) assertEquals("stop-assault-9", assertInstanceOf(MilitaryPlanningDecision.Select.class, result).operation().value());
            else assertEquals("native_war_assault_stop_blocked", assertInstanceOf(MilitaryPlanningDecision.Hold.class, result).phase());
        }
        Obj unobservable = state.with("active_siege", ((Obj)state.get("active_siege")).with("assault_observable", new Bool(false)));
        var blockedRequest = request(snapshotFor(unobservable, army), List.of(), Set.of(new OperationKey("life-advance")));
        assertEquals("native_war_assault_observation_blocked", assertInstanceOf(MilitaryPlanningDecision.Hold.class,
                WarSiegeDaily.stability(blockedRequest, actual(blockedRequest, unobservable, army, Set.of(), Set.of(), Set.of(), tactical(0)))).phase());
    }

    @Test void safeActiveDailyIsExactlyOneDayAndMissingCaptureNeverMeansEmptySafetySets() {
        Obj army = armyRow(0, "sieging"), state = state(siege(9, 0, 100, true), 1000, 200);
        var request = request(snapshotFor(state, army), List.of(), Set.of(new OperationKey("life-advance")));
        var actual = actual(request, state, army, Set.of(), Set.of(), Set.of(), tactical(0));
        var selected = assertInstanceOf(MilitaryPlanningDecision.Select.class, WarSiegeDaily.armyState(request, actual));
        assertEquals("life-advance", selected.operation().value()); assertEquals(OrdinaryPolicy.Purpose.DATE_ADVANCE, selected.purpose());
        assertEquals(number(1), ((Obj)selected.detail().get("assault_state")).get("projection_horizon_days"));
        var missing = WarSiegeDaily.factories(SOURCE, (input, previous) -> new EarlyWarCoreInputs.Unavailable(List.of("actual-route-input")));
        assertInstanceOf(MilitaryPlanningDecision.Unavailable.class, missing.getFirst().producer().evaluate(request, OrdinaryPolicy.Draft.empty()));
        assertInstanceOf(MilitaryPlanningDecision.Unavailable.class, missing.getLast().producer().evaluate(request, OrdinaryPolicy.Draft.empty()));
    }

    @Test void gatheringLocalRetreatAndCombatKeepTheirOriginalBoundsAndOriginalMissingActionReturns() {
        Obj noSiege = state(siege(9, 0, 100, false), 1000, 200).with("active_siege", Nil.INSTANCE);
        for (String state : List.of("gathering", "retreating", "combat")) {
            Obj army = armyRow(0, state);
            var request = request(snapshotFor(noSiege, army), List.of(), Set.of(new OperationKey("life-advance")));
            var result = assertInstanceOf(MilitaryPlanningDecision.Select.class,
                    WarSiegeDaily.armyState(request, actual(request, noSiege, army, Set.of(), Set.of(), Set.of(), tactical(31))));
            assertEquals("life-advance", result.operation().value());
            assertEquals(state.equals("gathering") ? "native_war_gathering_progress" : state.equals("retreating")
                    ? "native_war_recovery_wait" : "native_war_battle_control_progress", result.phase());
            var unsupported = request(snapshotFor(noSiege, army), List.of(), Set.of());
            assertInstanceOf(MilitaryPlanningDecision.Hold.class,
                    WarSiegeDaily.armyState(unsupported, actual(unsupported, noSiege, army, Set.of(), Set.of(), Set.of(), tactical(31))));
        }
    }
}

