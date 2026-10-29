package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

class DriverHistoryProjectionTest {
    @Test void completeSurvivingBranchRetainsFailedReadsAndMissingNullDistinction() {
        var original = List.of(HistoryFixtures.row(1, "query", false, null), HistoryFixtures.row(2, "query", false, "null"));
        var driver = HistoryFixtures.driver(original);
        var restored = org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(driver.encode());
        var rows = DriverSurvivingHistory.rows(restored);
        assertEquals(original, rows); assertFalse(rows.getFirst().members().containsKey("result"));
        assertEquals(OpportunityJson.Nil.INSTANCE, rows.getLast().get("result"));
    }
    @Test void effectiveAutoTurnUsesOuterFieldPresenceEvenWhenNull() {
        var nested = HistoryFixtures.row(1, "auto-turn", true, "{\"auto_turn\":{\"selected_step\":\"life-advance\",\"result\":{\"inner\":true}}}");
        assertEquals(HistoryFixtures.json("{\"inner\":true}"), DriverSurvivingHistory.effective(nested).result().orElseThrow());
        var outer = HistoryFixtures.row(1, "auto-turn", true, "{\"war_action\":null,\"auto_turn\":{\"selected_step\":\"life-advance\",\"result\":{\"inner\":true}}}");
        assertEquals(OpportunityJson.Nil.INSTANCE, DriverSurvivingHistory.effective(outer).result().orElseThrow().get("war_action"));
        assertEquals("life-advance", DriverSurvivingHistory.effective(outer).command().orElseThrow());
    }
    @Test void retainDiscardsAbandonedGameplayButKeepsAllProvenPhysicalRestarts() {
        var checkpoint = HistoryFixtures.checkpoint(2);
        var history = List.of(HistoryFixtures.row(1, HistoryFixtures.ADVANCE, true, HistoryFixtures.endpoint()), HistoryFixtures.anchor(2),
                HistoryFixtures.row(3, "move-army-1-to-30", true, "{\"war_action\":{\"status\":\"moving\"}}"),
                HistoryFixtures.row(4, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 7, 8)),
                HistoryFixtures.row(5, "life-advance", false, "{\"ending_date_raw\":124}"),
                HistoryFixtures.row(6, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 8, 9)));
        var actual = assertInstanceOf(DriverHistoryProjection.Available.class, DriverHistoryProjection.retain(checkpoint, history));
        assertEquals(4, actual.rows().size()); assertEquals(2, actual.retainedPhysicalRestarts());
        assertEquals(history.getFirst(), actual.rows().getFirst());
        assertEquals(3, OpportunityJson.integer(actual.rows().get(2).get("index"), "index").intValueExact());
        assertEquals(List.of(), DriverSurvivingHistory.afterLatestRestore(DriverSurvivingHistory.entries(HistoryFixtures.driver(actual.rows()))));
        assertEquals(1, RouteContactHistoryAdapter.timeline(DriverSurvivingHistory.entries(HistoryFixtures.driver(actual.rows()))).size());
    }
    @Test void managedCompletionReplacesOnlyItsMatchingLastProvisionalPhysicalRestart() {
        var checkpoint = HistoryFixtures.checkpoint(1);
        var earlier = HistoryFixtures.row(2, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 6, 7));
        var provisional = HistoryFixtures.row(3, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 7, 9));
        var completed = HistoryFixtures.row(4, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-lifecycle-queue", 7, 9));
        var actual = assertInstanceOf(DriverHistoryProjection.Available.class,
                DriverHistoryProjection.completedRestore(checkpoint, List.of(HistoryFixtures.anchor(1), earlier, provisional), completed));
        assertEquals(3, actual.rows().size()); assertEquals(earlier, actual.rows().get(1));
        assertEquals(3, OpportunityJson.integer(actual.rows().getLast().get("index"), "index").intValueExact());
        assertEquals("native-session-lifecycle-queue", OpportunityJson.text(OpportunityJson.object(actual.rows().getLast().get("result"), "result").get("source"), "source"));
    }
    @Test void malformedCheckpointAndRestoreNeverBecomeAnEmptySuccessfulHistory() {
        var checkpoint = HistoryFixtures.checkpoint(1);
        assertInstanceOf(DriverHistoryProjection.Unavailable.class, DriverHistoryProjection.retain(checkpoint, List.of()));
        assertTrue(DriverHistoryProjection.checkpointIdentity(HistoryFixtures.json("{\"sha256\":\"" + "a".repeat(64) + "\",\"size\":true,\"date_raw\":100}")).isEmpty());
        var samePid = HistoryFixtures.row(2, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 9, 9));
        assertFalse(DriverHistoryProjection.provenRestore(samePid, checkpoint));
        assertInstanceOf(DriverHistoryProjection.Unavailable.class, DriverHistoryProjection.completedRestore(checkpoint, List.of(HistoryFixtures.anchor(1)), samePid));
    }
    @Test void exactLifeClassifierRejectsLookalikeAndNoncanonicalCommands() {
        assertTrue(DriverSurvivingHistory.isLifeAdvanceStep("life-advance-one-day"));
        assertTrue(DriverSurvivingHistory.isLifeAdvanceStep("battle-terminal-cruise"));
        assertTrue(DriverSurvivingHistory.isLifeAdvanceStep(HistoryFixtures.ADVANCE));
        assertFalse(DriverSurvivingHistory.isLifeAdvanceStep("life-advance-one-day-extra"));
        assertFalse(DriverSurvivingHistory.isLifeAdvanceStep("advance-route-contact-horizon-v1-01-to-10-h-1-2"));
        assertFalse(DriverSurvivingHistory.isLifeAdvanceStep(HistoryFixtures.QUERY));
    }
    @Test void malformedOrReorderedBranchCannotGainRestoreQualification() {
        var checkpoint = HistoryFixtures.checkpoint(1);
        assertThrows(IllegalArgumentException.class, () -> DriverHistoryProjection.retain(checkpoint,
                List.of(HistoryFixtures.anchor(1), HistoryFixtures.row(3, "query", false, null))));
        assertThrows(IllegalArgumentException.class, () -> DriverHistoryProjection.retain(checkpoint,
                List.of(HistoryFixtures.anchor(1), HistoryFixtures.json("{\"index\":2,\"command\":\"query\",\"ok\":1}"))));
        var original = HistoryFixtures.row(1, "query", false, null);
        assertThrows(IllegalArgumentException.class, () -> new DriverSurvivingHistory.Row(1, "query", false, original,
                new DriverSurvivingHistory.Effective(java.util.Optional.of(HistoryFixtures.QUERY), java.util.Optional.empty())));
    }
}
