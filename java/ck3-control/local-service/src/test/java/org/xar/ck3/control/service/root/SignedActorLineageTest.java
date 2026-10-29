package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.LongNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalWindowReducer;

/** JSON numeric domain regression only; these values confer no writer or Game authority. */
final class SignedActorLineageTest {
    @Test void equivalentIntegralRepresentationsDoNotCreateAnotherLineage(){
        for(JsonNode node:List.of(IntNode.valueOf(-2),LongNode.valueOf(-2),BigIntegerNode.valueOf(BigInteger.valueOf(-2)))){
            ObjectNode before=running();((ObjectNode)before.get("latest_binding")).set("actor_character_id",node);
            ObjectNode after=OriginalWindowReducer.reduce(before,"attach_verified",details(-2));
            assertEquals(before.get("binding_lineage_count"),after.get("binding_lineage_count"));
            assertEquals(before.get("manual_repair_count"),after.get("manual_repair_count"));assertEquals(before.get("opaque_unknown"),after.get("opaque_unknown"));
        }
    }
    @Test void coldJsonRoundTripRetainsActorAndUnknownWithoutCredit(){
        ObjectNode before=running();ObjectNode cold=ContinuityJson.parseObject(ContinuityJson.canonical(before),ContinuityJson.DOCUMENT_MAX_BYTES);
        ObjectNode after=OriginalWindowReducer.reduce(cold,"attach_verified",details(-2));
        assertEquals(cold.get("binding_lineage_count"),after.get("binding_lineage_count"));assertEquals(cold.get("last_settled_cycles").bigIntegerValue(),after.get("last_settled_cycles").bigIntegerValue());
        assertEquals(cold.get("opaque_unknown"),after.get("opaque_unknown"));assertEquals(-2,after.get("latest_binding").get("actor_character_id").intValue());
    }
    @Test void genuineChangeCountsOnceAndMalformedOriginalActorIsRejected(){
        ObjectNode before=running();ObjectNode changed=OriginalWindowReducer.reduce(before,"attach_verified",details(-3));
        assertEquals(before.get("binding_lineage_count").longValue()+1,changed.get("binding_lineage_count").longValue());
        for(JsonNode bad:List.of(StrictJson.object().put("v",true).get("v"),StrictJson.object().put("v",-2.0).get("v"),StrictJson.object().put("v","-2").get("v"),IntNode.valueOf(-1))){
            ObjectNode malformed=before.deepCopy();((ObjectNode)malformed.get("latest_binding")).set("actor_character_id",bad);
            assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(malformed,"attach_verified",details(-2)));
        }
    }
    private static ObjectNode running(){
        ObjectNode initial=OriginalWindowReducer.reduce(null,"repair_required",details(-2));
        ObjectNode running=OriginalWindowReducer.reduce(initial,"attach_verified",details(-2));running.set("opaque_unknown",StrictJson.object().put("must_not_replay",true));return running;
    }
    private static ObjectNode details(int actor){
        ObjectNode n=StrictJson.object().put("machine_id","software-lineage").put("evidence_id","controlled-json-only").put("source","controlled-source").put("reason","controlled-repair").put("completed_cycles",0);
        n.putObject("game").put("pid",7).put("creation_date","1");
        n.putObject("frame").put("date_raw",100).put("actor_character_id",actor).put("episode_run_id","same-episode").put("snapshot_id","native:8").put("revision",7).put("native_revision",8);return n;
    }
}
