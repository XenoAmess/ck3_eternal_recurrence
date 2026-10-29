package org.xar.ck3.control.runtime.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Persisted cause metadata DATA, not a private Root history/Native/writer authority fixture. */
final class PendingNaturalCauseProofTest {
    @Test void completeV2OriginalsRoundTripWithoutGrantingFinalOrReplayAuthority() {
        var produced=document();byte[] original=PendingNaturalCauseProof.encode(produced);
        var restored=PendingNaturalCauseProof.decode(original);
        assertEquals(produced,restored);assertArrayEquals(original,PendingNaturalCauseProof.encode(restored));
        assertEquals(1_048_577,restored.successorSemantic().bytes());assertEquals(2_097_153,restored.originalKnown().bytes());
        assertEquals(9_007_199_254_740_991L,restored.writerHeadSequence());
        JsonNode wire=StrictJson.parse(original,PendingNaturalCauseProof.MAX_BYTES);
        for(String field:List.of("ui_clearance_qualified","final_lifecycle_applied","replay_authorized"))
            assertTrue(wire.get(field).isBoolean()&&!wire.get(field).booleanValue());
        assertEquals(produced.successorRootRead(),ExactRef.fromJson(wire.get("successor_root_read")));
        assertEquals(produced.successorRootResult(),ExactRef.fromJson(wire.get("successor_root_result")));
        assertEquals(produced.successorSemantic(),ExactRef.fromJson(wire.get("successor_semantic")));
        assertEquals(produced.originalKnown(),ExactRef.fromJson(wire.get("original_known")));
    }
    @Test void legacyV1MissingKnownEstateOrSequenceCannotBecomeReplayableByAliasOrNullRepair() {
        for(String missing:List.of("writer_head_sequence","successor_root_read","successor_root_result","successor_semantic","original_known",
                "actual_precommit_snapshot","predecessor_root","engine_clock_proof")) {
            ObjectNode row=wire();row.remove(missing);assertThrows(IllegalArgumentException.class,()->decode(row));
            ObjectNode nil=wire();nil.putNull(missing);assertThrows(IllegalArgumentException.class,()->decode(nil));
        }
        ObjectNode old=wire();old.put("schema","xar.java.pending-natural-cause/v1");assertThrows(IllegalArgumentException.class,()->decode(old));
        ObjectNode alias=wire();alias.set("known",alias.remove("original_known"));assertThrows(IllegalArgumentException.class,()->decode(alias));
        ObjectNode extra=wire();extra.put("current_frame_can_replace_history",true);assertThrows(IllegalArgumentException.class,()->decode(extra));
    }
    @Test void exactIntegersAndDistinctPrivateActorsRejectBooleanFloatingUnsafeAndWrongIdentityDomains() {
        for(String field:List.of("writer_head_sequence","predecessor_character_id","successor_character_id","episode_epoch","driver_version")) {
            for(String token:List.of("true","false","1.0","\"1\"","null")){
                ObjectNode row=wire();row.set(field,StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->decode(row));
            }
        }
        for(long id:new long[]{-1,0,2_147_483_648L}){
            ObjectNode row=wire();row.put("predecessor_character_id",id);assertThrows(IllegalArgumentException.class,()->decode(row));
        }
        ObjectNode same=wire();same.put("successor_character_id",same.get("predecessor_character_id").intValue());assertThrows(IllegalArgumentException.class,()->decode(same));
        ObjectNode overflow=wire();overflow.put("writer_head_sequence",9_007_199_254_740_992L);assertThrows(IllegalArgumentException.class,()->decode(overflow));
        for(String field:List.of("parent_body_sha256","writer_head_sha256","estate_reconciliation_sha256","retained_death_original_sha256")){
            ObjectNode bad=wire();bad.put(field,"ABC");assertThrows(IllegalArgumentException.class,()->decode(bad));
        }
    }
    @Test void flagsAndOriginalByteGrammarCannotSmuggleAnAuthorityIntoData() {
        for(String field:List.of("ui_clearance_qualified","final_lifecycle_applied","replay_authorized")){
            for(JsonNode token:List.of(StrictJson.object().booleanNode(true),StrictJson.object().numberNode(0),StrictJson.object().textNode("false"))){
                ObjectNode row=wire();row.set(field,token);assertThrows(IllegalArgumentException.class,()->decode(row));
            }
        }
        byte[] original=PendingNaturalCauseProof.encode(document());String text=new String(original,StandardCharsets.UTF_8);
        String duplicate=text.replace("\"writer_head_sequence\":9007199254740991","\"writer_head_sequence\":9007199254740991,\"writer_head_sequence\":9007199254740991");
        assertNotEquals(text,duplicate);assertThrows(IllegalArgumentException.class,()->PendingNaturalCauseProof.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->PendingNaturalCauseProof.decode((text+"{}").getBytes(StandardCharsets.UTF_8)));
        ObjectNode time=wire();time.put("observed_at_utc","2026-10-24T09:00:00+01:00");assertThrows(IllegalArgumentException.class,()->decode(time));
    }
    private static PendingNaturalCauseProof.Document document() {
        return new PendingNaturalCauseProof.Document("xenoamess-full-tower-eb9d2c1186",Instant.parse("2026-10-24T08:50:00.123456700Z"),
                "1".repeat(64),"2".repeat(64),9_007_199_254_740_991L,41,42,"original-predecessor-run",3,8,
                ref("predecessor-root",100),ref("engine-clock",101),ref("old-terminal-native",102),ref("successor-root-read",103),
                ref("successor-root-result",104),ref("complete-old-terminal-semantic",1_048_577),ref("complete-old-terminal-known",2_097_153),
                "3".repeat(64),"4".repeat(64));
    }
    private static ExactRef ref(String name,long bytes){return new ExactRef("D:/software-fixture/"+name+".json",bytes,"5".repeat(64));}
    private static ObjectNode wire(){return (ObjectNode)StrictJson.parse(PendingNaturalCauseProof.encode(document()),PendingNaturalCauseProof.MAX_BYTES);}
    private static PendingNaturalCauseProof.Document decode(ObjectNode value){return PendingNaturalCauseProof.decode(StrictJson.canonical(value,PendingNaturalCauseProof.MAX_BYTES));}
}
