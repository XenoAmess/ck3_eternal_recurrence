package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed DATA contract only; the actual private pending source and registered continuation still grant all permission. */
final class SuccessorUiContinuationJsonTest {
    @Test void boundedDateContinuationIsADistinctVariantAndKeepsRealAttemptMetadataAcrossJson() {
        var row=data();SuccessorUiContinuationJson.validate(row);
        var roundTrip=StrictJson.parse(StrictJson.canonical(row,262_144));SuccessorUiContinuationJson.validate(roundTrip);
        assertEquals(row,roundTrip);assertEquals("SUCCESSOR_UI_DATE_ADVANCE",roundTrip.get("kind").textValue());
        assertFalse(roundTrip.get("new_parent_submitted").booleanValue());
        assertEquals("9007199254740991",roundTrip.get("new_child_attempts").get(0).get("writer_sequence").textValue());
        assertEquals("UNRESOLVED",roundTrip.get("new_child_attempts").get(0).get("outcome").textValue());
        assertFalse(roundTrip.has("new_action_submitted"));assertFalse(roundTrip.has("gameplay_verified"));
    }
    @Test void fieldRangeMatchesTheActualReceiptAndNoUnknownKindOrReadonlyClaimCanReplaceAnAttempt() {
        for(String value:java.util.List.of("0","01","-1","9007199254740992","9223372036854775807")) {
            var row=data();((ObjectNode)row.get("new_child_attempts").get(0)).put("writer_sequence",value);
            assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(row));
        }
        var numeric=data();((ObjectNode)numeric.get("new_child_attempts").get(0)).put("writer_sequence",1);
        assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(numeric));
        var unknown=data();unknown.put("kind","SUCCESSOR_UI_ANY");assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(unknown));
        var readonly=data();readonly.put("disposition","NO_NEW_CHILD_ATTEMPT");assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(readonly));
        var replacement=data();replacement.put("new_parent_submitted",true);assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(replacement));
    }
    private static ObjectNode data() {
        var row=StrictJson.object();row.put("schema",SuccessorUiContinuationJson.SCHEMA).put("kind","SUCCESSOR_UI_DATE_ADVANCE")
                .put("disposition","NEW_CHILD_ATTEMPT").put("new_parent_submitted",false)
                .put("original_parent_action_id","retained-original-continue").put("original_parent_body_sha256","a".repeat(64));
        var source=new ExactRef("report-data-only",1,"b".repeat(64));
        row.set("canonical_domain",source.toJson());row.set("actual_published_driver",source.toJson());row.set("canonical_publication_proof",source.toJson());
        row.putArray("new_child_attempts").addObject().put("action_id","actual-attempt-data").put("body_sha256","c".repeat(64))
                .put("operation","wait-for-native-game-day").put("outcome","UNRESOLVED").put("writer_sequence","9007199254740991");
        return row;
    }
}
