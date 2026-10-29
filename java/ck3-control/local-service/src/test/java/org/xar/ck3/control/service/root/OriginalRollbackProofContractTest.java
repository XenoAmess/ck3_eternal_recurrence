package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure contract regressions. Parsed original DATA grants no reducer, writer or Managed qualification. */
final class OriginalRollbackProofContractTest {
    @TempDir Path temporary;
    private static final String MACHINE="rollback-contract-fixture";

    @Test void everyFullResponseRequiresTheSameNonemptyAbsoluteSourceAsOtherOriginals() {
        for(ExactRef invalid:List.of(new ExactRef("relative-full.json",1,"a".repeat(64)),
                new ExactRef(temporary.resolve("empty-full.json").toString(),0,"b".repeat(64)))) {
            ObjectNode row=proof();row.withObject("sources").withArray("successful_full_responses").removeAll().add(invalid.toJson());
            IllegalArgumentException failure=assertThrows(IllegalArgumentException.class,
                    ()->OriginalRollbackProof.decode(StrictJson.canonical(row),MACHINE));
            assertTrue(failure.getMessage().contains("nonempty absolute original material source"));
        }
    }

    @Test void fullResponseSourceContractSurvivesCanonicalJsonRoundTrip() {
        ObjectNode row=proof();byte[] original=StrictJson.canonical(row);
        var decoded=OriginalRollbackProof.decode(original,MACHINE);
        byte[] persisted=StrictJson.canonical(StrictJson.parse(original,32768));
        assertArrayEquals(original,persisted);
        assertEquals(decoded,OriginalRollbackProof.decode(persisted,MACHINE));
        assertEquals(List.of(source()),decoded.sources().successfulFullResponses());
        assertThrows(UnsupportedOperationException.class,()->decoded.sources().successfulFullResponses().clear());
    }

    @Test void fullResponseListStillRejectsMissingNullWrongShapeAndWrongExactRefTypes() {
        ObjectNode missing=proof();missing.withObject("sources").remove("successful_full_responses");reject(missing);
        ObjectNode nil=proof();nil.withObject("sources").putNull("successful_full_responses");reject(nil);
        ObjectNode wrong=proof();wrong.withObject("sources").put("successful_full_responses","not-an-array");reject(wrong);
        for(Object invalid:List.of(Boolean.TRUE,1.0d)) {
            ObjectNode row=proof();var full=(ObjectNode)row.withObject("sources").withArray("successful_full_responses").get(0);
            if(invalid instanceof Boolean value)full.put("bytes",value);else full.put("bytes",((Double)invalid).doubleValue());
            reject(row);
        }
        ObjectNode duplicate=proof();duplicate.withObject("sources").withArray("successful_full_responses").add(source().toJson());reject(duplicate);
        ObjectNode empty=proof();empty.withObject("sources").withArray("successful_full_responses").removeAll();reject(empty);
    }

    private void reject(ObjectNode row) {
        assertThrows(IllegalArgumentException.class,()->OriginalRollbackProof.decode(StrictJson.canonical(row),MACHINE));
    }
    private ExactRef source(){return new ExactRef(temporary.resolve("actual-original.json").toString(),1,"a".repeat(64));}
    private ObjectNode proof() {
        var row=StrictJson.object();row.put("schema",OriginalRollbackProof.SCHEMA);row.put("status","CLOSED_COMPLETED_UNSAVED_TAIL");
        row.put("machine_id",MACHINE);row.put("observed_at_utc","2026-10-24T00:00:00Z");row.put("runtime_root",temporary.toString());
        row.put("new_ordinary_cycle_credit",0);row.put("new_game_day_credit",0);row.put("original_actions_replayed",false);row.put("Driver_history_truncated",false);
        var sources=row.putObject("sources");
        for(String field:List.of("prior_basis","prior_validation","raw_state","raw_governance","interruption","inventory","abnormal_closed_epoch",
                "current_driver_review","actual_next","canonical_checkpoint_qualification","continuity_frontier"))sources.set(field,source().toJson());
        sources.putArray("successful_full_responses").add(source().toJson());return row;
    }
}
