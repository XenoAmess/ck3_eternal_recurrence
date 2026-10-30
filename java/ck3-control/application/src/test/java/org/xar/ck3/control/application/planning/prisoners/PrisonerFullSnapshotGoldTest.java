package org.xar.ck3.control.application.planning.prisoners;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Complete contextual SDK snapshots preserve the signed native gold contract. */
final class PrisonerFullSnapshotGoldTest {
    @Test void completeSnapshotExtensionsPreserveSignedGoldWithoutNarrowing() {
        for(long value:new long[]{Long.MIN_VALUE,-26_000_000,0,26_000_000,Long.MAX_VALUE}) {
            var snapshot=snapshot(value);assertTrue(DriverJson.encode(snapshot).length>StrictJson.INPUT_MAX_BYTES);
            assertEquals(BigInteger.valueOf(value),PrisonerActionBinding12004.gold(snapshot));
        }
    }

    @Test void fullSnapshotGoldStillRejectsWrongTokenScaleAndSignedOverflow() {
        for(String raw:new String[]{"true","1.0","\"1\"","9223372036854775808","-9223372036854775809"}) {
            var snapshot=node();snapshot.putObject("played_character_gold").put("scale",100000).put("raw","$raw$");
            String encoded=new String(FullJsonTree.encode(snapshot,FullJsonTree.MAXIMUM_BYTES),java.nio.charset.StandardCharsets.UTF_8)
                    .replace("\"$raw$\"",raw);
            var actual=DriverJson.object(encoded.getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
            assertThrows(IllegalArgumentException.class,()->PrisonerActionBinding12004.gold(actual));
        }
        var snapshot=node();snapshot.putObject("played_character_gold").put("scale",1).put("raw",1);
        assertThrows(IllegalArgumentException.class,()->PrisonerActionBinding12004.gold(
                OpportunityJson.object(DriverJson.fromNode(snapshot),"software snapshot")));
    }

    private static OpportunityJson.Obj snapshot(long value) {
        var snapshot=node();snapshot.putObject("played_character_gold").put("scale",100000).put("raw",value);
        return OpportunityJson.object(DriverJson.fromNode(snapshot),"software snapshot");
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode node() {
        var snapshot=StrictJson.object();snapshot.put("paused",true);snapshot.putArray("active_wars");
        snapshot.put("software_contextual_sdk_extension","x".repeat(StrictJson.INPUT_MAX_BYTES+1));return snapshot;
    }
}
