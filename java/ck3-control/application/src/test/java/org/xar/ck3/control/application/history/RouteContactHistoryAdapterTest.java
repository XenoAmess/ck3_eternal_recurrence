package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.routecontact.RouteContactModel;
import org.xar.ck3.control.application.routecontact.RouteContactProofs;

class RouteContactHistoryAdapterTest {
    @Test void latestFailedQueryShadowsPriorSuccessfulSameScope() {
        var history = DriverSurvivingHistory.entries(HistoryFixtures.driver(List.of(
                HistoryFixtures.row(1, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult()),
                HistoryFixtures.row(2, HistoryFixtures.QUERY, false, null))));
        var entries = RouteContactHistoryAdapter.queries(history, HistoryFixtures.frame());
        assertEquals(2, entries.size()); assertTrue(entries.getFirst().valid().isPresent()); assertTrue(entries.getLast().valid().isEmpty());
        assertTrue(RouteContactProofs.oneDayEntries(HistoryFixtures.frame(), entries, List.of()).isEmpty());
    }
    @Test void malformedOrStaleLatestSuccessfulReadStillShadowsPriorSuccess() {
        var history = DriverSurvivingHistory.entries(HistoryFixtures.driver(List.of(
                HistoryFixtures.row(1, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult()),
                HistoryFixtures.row(2, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult().replace("\"queried_native_revision\":7", "\"queried_native_revision\":8")))));
        var entries = RouteContactHistoryAdapter.queries(history, HistoryFixtures.frame());
        assertTrue(entries.getFirst().valid().isPresent()); assertTrue(entries.getLast().valid().isEmpty());
        assertTrue(RouteContactProofs.oneDayEntries(HistoryFixtures.frame(), entries, List.of()).isEmpty());
    }
    @Test void successfulRestoreSlicesQueriesButDoesNotHideSurvivingEndpoint() {
        var checkpoint = HistoryFixtures.checkpoint(2);
        var history = DriverSurvivingHistory.entries(HistoryFixtures.driver(List.of(
                HistoryFixtures.row(1, HistoryFixtures.ADVANCE, true, HistoryFixtures.endpoint()), HistoryFixtures.anchor(2),
                HistoryFixtures.row(3, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 8, 9)),
                HistoryFixtures.row(4, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult()))));
        assertEquals(1, DriverSurvivingHistory.afterLatestRestore(history).size());
        var timeline = RouteContactHistoryAdapter.timeline(history);
        assertEquals(1, timeline.size()); assertInstanceOf(RouteContactModel.AdvanceHistory.class, timeline.getFirst());
        var entries = RouteContactHistoryAdapter.queries(DriverSurvivingHistory.afterLatestRestore(history), HistoryFixtures.frame());
        var proof = RouteContactProofs.oneDayEntries(HistoryFixtures.frame(), entries, timeline).values().iterator().next();
        assertTrue(proof.strictFollowup());
    }
    @Test void failedStrictFollowupRetainedBeforeCheckpointPreventsThirdDayAfterRestore() {
        var checkpoint = HistoryFixtures.checkpoint(2);
        var history = DriverSurvivingHistory.entries(HistoryFixtures.driver(List.of(
                HistoryFixtures.row(1, HistoryFixtures.ADVANCE, false, HistoryFixtures.strictFailure()), HistoryFixtures.anchor(2),
                HistoryFixtures.row(3, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 8, 9)),
                HistoryFixtures.row(4, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult()))));
        var timeline = RouteContactHistoryAdapter.timeline(history);
        var last = assertInstanceOf(RouteContactModel.AdvanceHistory.class, timeline.getLast());
        assertFalse(last.ok()); assertTrue(last.strictFollowupUnresolved());
        assertTrue(RouteContactProofs.oneDayEntries(HistoryFixtures.frame(),
                RouteContactHistoryAdapter.queries(DriverSurvivingHistory.afterLatestRestore(history), HistoryFixtures.frame()), timeline).isEmpty());
    }
    @Test void interveningNonrouteOrMalformedLifeAdvanceCreatesBarrierWithoutInventedIdentity() {
        var history = DriverSurvivingHistory.entries(HistoryFixtures.driver(List.of(
                HistoryFixtures.row(1, HistoryFixtures.ADVANCE, true, HistoryFixtures.endpoint()),
                HistoryFixtures.row(2, "life-advance-one-day", false, "{\"status\":\"unknown\"}"))));
        var timeline = RouteContactHistoryAdapter.timeline(history);
        assertEquals(2, timeline.size()); var barrier = assertInstanceOf(RouteContactModel.TimelineBarrier.class, timeline.getLast());
        assertEquals("life-advance-one-day", barrier.originalStep());
        var queries = RouteContactHistoryAdapter.queries(DriverSurvivingHistory.entries(HistoryFixtures.driver(
                List.of(HistoryFixtures.row(1, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult())))), HistoryFixtures.frame());
        assertFalse(RouteContactProofs.oneDayEntries(HistoryFixtures.frame(), queries, timeline).values().iterator().next().strictFollowup());
    }
    @Test void failedAutoTurnQueryRetainsScopeTombstoneAndFailedRestoreDoesNotEraseIt() {
        var rows = DriverSurvivingHistory.entries(HistoryFixtures.driver(List.of(
                HistoryFixtures.row(1, HistoryFixtures.QUERY, true, HistoryFixtures.queryResult()),
                HistoryFixtures.row(2, "auto-turn", false, "{\"auto_turn\":{\"selected_step\":\"" + HistoryFixtures.QUERY + "\",\"result\":null}}"),
                HistoryFixtures.row(3, "restore-checkpoint", false, "{\"status\":\"unknown\"}"))));
        var queries = RouteContactHistoryAdapter.queries(DriverSurvivingHistory.afterLatestRestore(rows), HistoryFixtures.frame());
        assertEquals(2, queries.size()); assertTrue(queries.getFirst().valid().isPresent()); assertTrue(queries.getLast().valid().isEmpty());
        assertTrue(RouteContactProofs.oneDayEntries(HistoryFixtures.frame(), queries, List.of()).isEmpty());
    }
}
