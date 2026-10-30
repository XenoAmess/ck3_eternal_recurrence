package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact actual875B pre1 Native body; no public transport, applied Start or new transition claim. */
final class M6NativeOriginalPreEndedSourceTest {
    @Test void actualOriginalPreEndedReturnKeepsRawOwnerAndNeutralSource()throws Exception{
        try(var stream=getClass().getResourceAsStream("/sway/m6-native-original-pre-ended.json")){
            assertNotNull(stream,"mandatory actual Native body");JsonNode read=StrictJson.parse(stream.readAllBytes(),M6SourceProducer.MAX_BYTES);
            JsonNode family=read.get("common_native_end"),normalized=M6CommonEndSources.normalize(family,read),row=normalized.get("records").get(0);
            assertEquals(family,normalized);assertEquals(-2,normalized.get("actor_character_id").intValue());assertEquals(0,normalized.get("target_character_id").intValue());assertEquals(0,normalized.get("scheme_instance_id").intValue());
            for(String frame:new String[]{"entry","returned"}){assertEquals(1,row.at("/"+frame+"/status_raw_i32").intValue());assertEquals(4294967294L,row.at("/"+frame+"/owner_character_full_id_raw_u32").longValue());}
            assertTrue(row.get("original_forwarded_once").booleanValue());assertTrue(row.get("original_returned").booleanValue());assertTrue(row.get("return_same_scheme_full_id").booleanValue());
            assertEquals(0x2a48c7b,row.get("callsite_rva").longValue());assertEquals(0x2a48c80,row.get("call_return_rva").longValue());assertEquals(1,row.get("incoming_dl_raw_u8").intValue());
            assertTrue(read.get("records").isEmpty());assertFalse(read.get("material_effect_observed").booleanValue());assertFalse(row.has("cause_relation"));assertFalse(row.get("incoming_return_address_observed").booleanValue());assertTrue(row.get("caller_return_rva").isNull());
        }
    }
}
