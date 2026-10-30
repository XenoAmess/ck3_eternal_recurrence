package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.planning.sway.SwaySignedNativeCommonEndTest;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual dual-site Native public packets. The copied tuple is software identity, never an applied Start. */
final class M6NativePurgeCommonEndTest {
    private static final String V1="actual_2a48877_2a4adf0_v1";
    private static final String V2="actual_2a48877_2a48c7b_2a4adf0_v2";
    private static JsonNode packets()throws Exception{
        try(var stream=M6NativePurgeCommonEndTest.class.getResourceAsStream("/sway/m6-native-purge-common-end.json")){
            assertNotNull(stream,"mandatory new actual producer packets");JsonNode packets=StrictJson.parse(stream.readAllBytes(),M6SourceProducer.MAX_BYTES);
            assertTrue(packets.isArray());assertEquals(3,packets.size());return packets;
        }
    }
    private static JsonNode read(JsonNode packet){return StrictJson.parse(SwaySignedNativeCommonEndTest.decode(packet,packet).normalized().bytes());}
    private static JsonNode normalize(JsonNode read){return M6CommonEndSources.normalize(read.get("common_native_end"),read);}
    private static JsonNode original(JsonNode read){long scheme=read.get("scheme_instance_id").longValue();return M6TerminalSourceComposition.identityJson(new G2M6Contracts.Identity("software-purge-copied-tuple",NativeCharacterId.fromJson(read.get("actor_character_id")).value(),NativeCharacterId.fromJson(read.get("target_character_id")).value(),scheme,(int)(scheme>>>24)));}

    @Test void newNativePurgePacketsReachExactNormalizerAndNeutralRetainedReturn()throws Exception{
        List<String> rejected=new ArrayList<>();Set<Integer> before=new HashSet<>();int count=0;
        for(JsonNode packet:packets()){
            JsonNode read=read(packet),family=read.get("common_native_end");assertEquals(V2,family.get("source_contract").textValue());
            try{
                assertEquals(family,normalize(read));JsonNode retained=M6CommonEndSources.retained(family,read,original(read));
                assertNotNull(retained);assertTrue(retained.get("native_terminal_state_observed").booleanValue());assertFalse(retained.get("terminal_cause_observed").booleanValue());
                assertEquals("terminated_unattributed",retained.get("native_status_key").textValue());
                for(JsonNode row:family.get("records")){
                    assertTrue(row.get("original_forwarded_once").booleanValue());assertTrue(row.get("original_returned").booleanValue());
                    assertFalse(row.has("rax"));assertFalse(row.has("cause_relation"));assertEquals(row.get("callsite_rva").longValue()==0x2a48c7b?1:2,row.get("incoming_dl_raw_u8").intValue());
                    before.add(row.at("/entry/status_raw_i32").intValue());
                }
            }catch(IllegalArgumentException failure){rejected.add("packet"+count+": "+failure.getMessage());}
            count++;
        }
        assertEquals(List.of(),rejected,"new actual second-site packets rejected");assertEquals(Set.of(0,1),before);
    }
    @Test void mismatchedSiteReturnCalleeAndSourceContractRemainRejected()throws Exception{
        JsonNode read=read(packets().get(0));normalize(read);
        for(long[] edge:List.of(new long[]{0x2a48c7b,0x2a4887c,0x2a4adf0},new long[]{0x2a48877,0x2a48c80,0x2a4adf0},new long[]{0x267deb9,0x267debe,0x2a4adf0},new long[]{0x2a48c7b,0x2a48c80,0x2a4adf1})){
            ObjectNode bad=((ObjectNode)read).deepCopy();ObjectNode row=(ObjectNode)bad.at("/common_native_end/records/0");row.put("callsite_rva",edge[0]);row.put("call_return_rva",edge[1]);row.put("callee_rva",edge[2]);
            assertThrows(IllegalArgumentException.class,()->normalize(bad));
        }
        ObjectNode old=((ObjectNode)read).deepCopy();((ObjectNode)old.get("common_native_end")).put("source_contract",V1);assertThrows(IllegalArgumentException.class,()->normalize(old));
        ObjectNode unknown=((ObjectNode)read).deepCopy();((ObjectNode)unknown.get("common_native_end")).put("source_contract",V2+"x");assertThrows(IllegalArgumentException.class,()->normalize(unknown));
    }
    @Test void mixedActualRowsPreserveEachSiteAndLatestNeutralProvenance()throws Exception{
        JsonNode read=read(packets().get(2)),family=normalize(read),rows=family.get("records");assertEquals(2,rows.size());Set<Long> sites=new HashSet<>();
        for(JsonNode row:rows){long site=row.get("callsite_rva").longValue();sites.add(site);assertEquals(site+5,row.get("call_return_rva").longValue());}
        assertEquals(Set.of(0x2a48877L,0x2a48c7bL),sites);
        JsonNode retained=M6CommonEndSources.retained(family,read,original(read));assertNotNull(retained);assertEquals(rows.get(1),retained.get("copied_common_native_end_record"));assertFalse(retained.get("terminal_cause_observed").booleanValue());
    }
    @Test void actualFailureRotationAndFilteredPacketsFollowDynamicV1V2Contract()throws Exception{
        List<String> failures=new ArrayList<>();int count=0;
        try(var stream=getClass().getResourceAsStream("/sway/m6-native-common-edge.json")){
            assertNotNull(stream,"new actual partial-install and session packets required");JsonNode packets=StrictJson.parse(stream.readAllBytes(),M6SourceProducer.MAX_BYTES);assertEquals(5,packets.size());
            for(JsonNode item:packets){String name=item.get("name").textValue();
                try{
                    JsonNode read=read(item.get("packet")),family=normalize(read),rows=family.get("records");boolean second=false;
                    for(JsonNode row:rows)second|=row.get("callsite_rva").longValue()==0x2a48c7b;
                    assertEquals(second?V2:V1,family.get("source_contract").textValue(),name);
                    JsonNode retained=M6CommonEndSources.retained(family,read,original(read));
                    if(rows.isEmpty()){assertNull(retained,name);assertEquals(V1,family.get("source_contract").textValue());}
                    else {assertNotNull(retained,name);assertFalse(retained.get("terminal_cause_observed").booleanValue());}
                    if(name.equals("session-rotated")){assertFalse(family.get("available").booleanValue());assertTrue(rows.isEmpty());}
                    if(name.equals("failed-primary-filtered")||name.equals("filtered-empty")){assertTrue(family.get("available").booleanValue());assertTrue(rows.isEmpty());}
                    if(name.equals("recovered-primary")){assertEquals(1,rows.size());assertEquals(0x2a48877,rows.get(0).get("callsite_rva").longValue());}
                }catch(IllegalArgumentException failure){failures.add(name+": "+failure.getMessage());}
                count++;
            }
        }
        assertEquals(5,count);assertEquals(List.of(),failures,"actual filtered/empty families rejected");
    }
}
