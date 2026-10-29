package org.xar.ck3.control.contracts.offline;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure wire values: these references name no actual files and grant no read or runtime authority.
 * Actual producer -> physical load/recheck coverage stays in the M2 local-service regressions. */
final class IncidentReadIndexTest {
    private static final ExactRef RECEIPT=new ExactRef("wire-receipt",11,"a".repeat(64));
    private static final ExactRef REQUEST=new ExactRef("wire-request",12,"b".repeat(64));
    private static final ExactRef OBSERVED=new ExactRef("wire-observation",13,"c".repeat(64));
    private static ObjectNode diagnostic(){return StrictJson.object().put("capture_stage","planning_diagnostic").putNull("action_id");}
    private static ObjectNode failure(ObjectNode index){return (ObjectNode)index.get("failed_read_originals");}

    @Test void legacyAndBothDeclaredBranchesKeepTheirVersionAndOnlyTheirExplicitReferences(){
        assertEquals(IncidentReadIndex.None.INSTANCE,IncidentReadIndex.decode(IncidentReadIndex.encode(
                IncidentReadIndex.None.INSTANCE,StrictJson.object().put("action_id","wire-action"))));
        var known=new IncidentReadIndex.KnownReceipt(RECEIPT);
        ObjectNode v2=IncidentReadIndex.encode(known,diagnostic());
        assertEquals("xar.episode-incident-before-index/v2",v2.path("schema").textValue());
        assertEquals(known,IncidentReadIndex.decode(v2));assertEquals(List.of(RECEIPT),known.references());
        assertFalse(v2.has("failed_read_originals"));
        var failed=new IncidentReadIndex.FailedQuery(RECEIPT,REQUEST,Optional.empty(),List.of(REQUEST,OBSERVED,OBSERVED));
        ObjectNode v3=IncidentReadIndex.encode(failed,diagnostic());
        assertEquals("xar.episode-incident-before-index/v3",v3.path("schema").textValue());
        assertEquals(failed,IncidentReadIndex.decode(v3));assertTrue(failure(v3).get("observed_failure_ref").isNull());
        assertEquals(3,failure(v3).get("dependency_refs").size(),"the explicit wire inventory is preserved");
        assertEquals(List.of(RECEIPT,REQUEST,OBSERVED),failed.references(),"I/O references keep the producer's ordered deduplication");
        assertFalse(v3.has("original_read_ref"));
    }

    @Test void nullableObservationAndRequiredDependencyArrayDoNotAdmitMissingOrMistypedValues(){
        ObjectNode original=IncidentReadIndex.encode(new IncidentReadIndex.FailedQuery(RECEIPT,REQUEST,
                Optional.of(OBSERVED),List.of()),diagnostic());
        var missing=original.deepCopy();failure(missing).remove("observed_failure_ref");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(missing));
        var absent=original.deepCopy();failure(absent).putNull("observed_failure_ref");
        assertEquals(Optional.empty(),((IncidentReadIndex.FailedQuery)IncidentReadIndex.decode(absent)).observedFailure());
        var wrongObservation=original.deepCopy();failure(wrongObservation).put("observed_failure_ref",true);
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(wrongObservation));
        for(String value:List.of("null","{}","true","0")){
            var wrong=original.deepCopy();failure(wrong).set("dependency_refs",StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(wrong));
        }
        var missingDependencies=original.deepCopy();failure(missingDependencies).remove("dependency_refs");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(missingDependencies));
    }

    @Test void mixedReadVersionsAndSubmittedActionCannotAliasTheDiagnosticWire(){
        var known=new IncidentReadIndex.KnownReceipt(RECEIPT);ObjectNode original=IncidentReadIndex.encode(known,diagnostic());
        var legacy=original.deepCopy();legacy.put("schema","xar.episode-incident-before-index/v1");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(legacy));
        var mixed=original.deepCopy();mixed.putNull("failed_read_originals");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(mixed));
        var missing=original.deepCopy();missing.remove("original_read_ref");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(missing));
        var nil=original.deepCopy();nil.putNull("original_read_ref");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(nil));
        var submitted=original.deepCopy();submitted.put("action_id","wire-action");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(submitted));
        var unknown=original.deepCopy();unknown.put("schema","xar.episode-incident-before-index/v4");
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.decode(unknown));
        assertThrows(IllegalArgumentException.class,()->IncidentReadIndex.encode(known,original));
    }
}
