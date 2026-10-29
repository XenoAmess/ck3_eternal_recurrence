package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

class DriverHistoryOriginalProducerTest {
    @Test void actualOriginalRetentionProducerAgreesAcrossAbandonedActionsAndPhysicalRestarts() throws Exception {
        var checkpoint = HistoryFixtures.checkpoint(2);
        var rows = List.of(HistoryFixtures.row(1, HistoryFixtures.ADVANCE, false, HistoryFixtures.strictFailure()), HistoryFixtures.anchor(2),
                HistoryFixtures.row(3, HistoryFixtures.QUERY, false, "{\"status\":\"unknown\"}"),
                HistoryFixtures.row(4, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 7, 8)),
                HistoryFixtures.row(5, "move-army-1-to-99", true, "{\"war_action\":{\"status\":\"moving\"}}"),
                HistoryFixtures.row(6, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 8, 9)));
        Obj request = new Obj(Map.of("operation", new OpportunityJson.Text("retain"), "checkpoint", checkpoint, "history", new Arr(List.copyOf(rows))));
        var actual = assertInstanceOf(DriverHistoryProjection.Available.class, DriverHistoryProjection.retain(checkpoint, rows));
        assertEquals(new Arr(List.copyOf(actual.rows())), OriginalDriverHistoryOracle.call(request));
        assertEquals(new Arr(List.of()), OriginalDriverHistoryOracle.call(new Obj(Map.of("operation", new OpportunityJson.Text("after"), "history", new Arr(List.copyOf(actual.rows()))))));
    }
    @Test void actualOriginalRecordCommandReplacesMatchingProvisionalOnly() throws Exception {
        var checkpoint = HistoryFixtures.checkpoint(1);
        var rows = List.of(HistoryFixtures.anchor(1),
                HistoryFixtures.row(2, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 6, 7)),
                HistoryFixtures.row(3, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-cold-start", 7, 9)));
        var completed = HistoryFixtures.row(4, "restore-checkpoint", true, HistoryFixtures.result(checkpoint, "native-session-lifecycle-queue", 7, 9));
        Obj request = new Obj(Map.of("operation", new OpportunityJson.Text("record"), "checkpoint", checkpoint, "history", new Arr(List.copyOf(rows)), "completed", completed));
        var actual = assertInstanceOf(DriverHistoryProjection.Available.class, DriverHistoryProjection.completedRestore(checkpoint, rows, completed));
        assertEquals(new Arr(List.copyOf(actual.rows())), OriginalDriverHistoryOracle.call(request));
    }
    @Test void originalEffectiveProducerKeepsOuterExplicitNullAndNestedAutoTurnResult() throws Exception {
        for (Obj row : List.of(
                HistoryFixtures.row(1, "auto-turn", true, "{\"war_action\":null,\"auto_turn\":{\"selected_step\":\"life-advance\",\"result\":{\"ending_date_raw\":100}}}"),
                HistoryFixtures.row(1, "auto-turn", false, "{\"auto_turn\":{\"selected_step\":\"" + HistoryFixtures.ADVANCE + "\",\"result\":" + HistoryFixtures.strictFailure() + "}}"))) {
            var effective = DriverSurvivingHistory.effective(row);
            var expected = new Arr(List.of(new OpportunityJson.Text(effective.command().orElseThrow()), effective.result().orElseThrow()));
            assertEquals(expected, OriginalDriverHistoryOracle.call(new Obj(Map.of("operation", new OpportunityJson.Text("effective"), "row", row))));
        }
    }
    @Test void strictOriginalV2ImportBindsActualBytesAndRejectsChangedVersionOrReceiptType() {
        var complete = HistoryFixtures.driver(List.of(HistoryFixtures.row(1, "query", false, null)));
        byte[] raw = complete.encode(); ExactRef original = new ExactRef("actual-driver-v2.json", raw.length, DriverJson.sha256(raw));
        var game = HistoryFixtures.game();
        var imported = DriverHistoryImport.originalV2(original, raw, 3, 1, game, new Obj(Map.of()));
        assertEquals(1, imported.completeSurvivingBranch().size()); assertFalse(imported.completeSurvivingBranch().getFirst().ok());
        byte[] changed = raw.clone(); changed[changed.length - 2] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> DriverHistoryImport.originalV2(original, changed, 3, 1, game, new Obj(Map.of())));
        String version = new String(raw, java.nio.charset.StandardCharsets.UTF_8).replace("\"format_version\":2", "\"format_version\":3");
        byte[] versionRaw = version.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> DriverHistoryImport.originalV2(new ExactRef("version3", versionRaw.length, DriverJson.sha256(versionRaw)), versionRaw, 3, 1, game, new Obj(Map.of())));
        assertThrows(IllegalArgumentException.class, () -> DriverSurvivingHistory.row(HistoryFixtures.json("{\"index\":true,\"command\":\"query\",\"ok\":true}")));
    }
}
