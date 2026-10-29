package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual pure descriptor -> reducer -> event cold decoder. These DATA fixtures grant no Root/ACK permission. */
class OriginalRootOperatorReplayTest {
    private static ContinuityState originalRoot(){var row=EpisodeOperatorRebindTest.active().toJson();row.remove(EpisodeWindow.FIELD);
        row.put("schema","root.ck3.continuity-window/v1");return ContinuityState.fromJson(row,"fixture-machine");}
    @Test void originalRootUsesIndependentLineageWithoutInventingFirstSaveAndColdEventReplaysExactly(){
        var before=originalRoot();var change=EpisodeOperatorRebindTest.rebind();var reduced=EpisodeWindow.reduce(before,change.request());
        assertFalse(reduced.toJson().has(EpisodeWindow.FIELD));assertEquals(before.origin(),reduced.origin());
        assertEquals(List.of(change),EpisodeWindow.operatorLineage(reduced));assertEquals(before.toJson().get("UNKNOWN"),reduced.toJson().get("UNKNOWN"));
        var sequenced=reduced.toJson();sequenced.put("sequence",before.sequence()+1);sequenced.put("last_event_identity",change.request().identity());
        var after=ContinuityState.fromJson(sequenced,before.machineId());
        var event=new ContinuityEvent(after.sequence(),"2026-10-24T08:00:00Z",change.request().kind(),change.request().details(),
                change.request().identity(),ContinuityJson.digest(before.toJson()),after);
        assertEquals(after.toJson(),ContinuityEvent.fromJson(event.toJson(),before).after().toJson());
        var invalid=event.toJson();((com.fasterxml.jackson.databind.node.ObjectNode)invalid.get("after")).put("last_settled_cycles",9);
        assertThrows(IllegalArgumentException.class,()->ContinuityEvent.fromJson(invalid,before));
    }
    @Test void nullableLegacyOpeningIsPreservedAsDataAndDoesNotBecomeFullGameOrFirstSaveQualification(){
        var before=originalRoot();var change=EpisodeOperatorRebindTest.rebind();
        var missing=before.toJson();missing.putNull("latest_binding");
        missing.putNull("game_binding");var legacy=ContinuityState.fromJson(missing,before.machineId());
        var independent=EpisodeWindow.reduce(legacy,change.request());
        assertTrue(independent.toJson().get("latest_binding").isNull());assertTrue(independent.toJson().get("game_binding").isNull());
        assertFalse(independent.toJson().has(EpisodeWindow.FIELD));assertEquals(List.of(change),EpisodeWindow.operatorLineage(independent));
        var reduced=EpisodeWindow.reduce(before,change.request());
        var bad=reduced.toJson();bad.put("sequence",before.sequence()+2);bad.put("last_event_identity",change.request().identity());
        assertThrows(IllegalArgumentException.class,()->EpisodeWindow.requireReduction(before,ContinuityState.fromJson(bad,before.machineId()),change.request(),true));
        var lineage=(com.fasterxml.jackson.databind.node.ObjectNode)reduced.toJson().get(EpisodeWindow.ORIGINAL_OPERATOR_FIELD);
        var wrong=lineage.deepCopy();wrong.put("schema",EpisodeWindow.SCHEMA);
        assertThrows(IllegalArgumentException.class,()->EpisodeWindow.OriginalRootOperators.fromJson(wrong));
    }
}
