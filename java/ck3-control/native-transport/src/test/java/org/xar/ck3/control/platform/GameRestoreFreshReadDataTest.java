package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;

/** Archive DATA contract only; no Managed, private window, receiver or restoration is constructed. */
final class GameRestoreFreshReadDataTest {
    private static ExactRef ref(String role){return new ExactRef("D:/source-only/"+role,20,"a".repeat(64));}
    private static GameRestoreNativeAdapter.PairData data(){
        return new GameRestoreNativeAdapter.PairData("restore-original",ref("lifecycle"),ref("save"),
                new GameRestoreNativeAdapter.ReadOriginal(ref("ack-one"),ref("native-one"),"9007199254740993","2026-10-25T02:00:00Z"),
                new GameRestoreNativeAdapter.ReadOriginal(ref("ack-two"),ref("native-two"),"9007199254740998","2026-10-25T02:00:01Z"));
    }
    @Test void exactArchiveRolesAndDecimalReceiveOrdersRoundTripWithoutGrantingAuthority(){
        var actual=data();byte[] encoded=actual.encode();var decoded=GameRestoreNativeAdapter.PairData.decode(encoded);
        assertEquals(actual,decoded);assertArrayEquals(encoded,decoded.encode());
        assertEquals("9007199254740993",decoded.first().receivedOrder());
        var locators=new RestoreCheckpointService.IndependentReadPair(ref("manifest"),decoded.first().acknowledgement(),decoded.first().nativePacket(),decoded.second().acknowledgement(),decoded.second().nativePacket());
        assertEquals(5,locators.references().size());
    }
    @Test void missingNullExtraAndWrongJsonTypesNeverBecomeReadOriginals(){
        for(String field:List.of("schema","restore_request_id","lifecycle_evidence","loaded_save","first","second")){
            var missing=(ObjectNode)StrictJson.parse(data().encode());missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(missing)),field);
            var nil=(ObjectNode)StrictJson.parse(data().encode());nil.putNull(field);
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(nil)),field);
        }
        var extra=(ObjectNode)StrictJson.parse(data().encode());extra.put("private_issuer",true);
        assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(extra)));
        for(String field:List.of("acknowledgement","native_packet","received_order","received_at_utc")){
            var row=(ObjectNode)StrictJson.parse(data().encode());((ObjectNode)row.get("first")).remove(field);
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(row)),field);
        }
        for(String wrong:List.of("true","9007199254740993","1.5","null","\"01\"","\"0\"","\"-1\"")){
            var row=(ObjectNode)StrictJson.parse(data().encode());((ObjectNode)row.get("first")).set("received_order",StrictJson.parse(wrong.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(row)),wrong);
        }
        var booleanSize=(ObjectNode)StrictJson.parse(data().encode());((ObjectNode)booleanSize.get("first").get("acknowledgement")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->GameRestoreNativeAdapter.PairData.decode(StrictJson.canonical(booleanSize)));
    }
    @Test void repeatedAndReversedReadRolesAreRejectedBeforeAnyAuthorityConsumer(){
        var original=data();
        assertThrows(IllegalArgumentException.class,()->new GameRestoreNativeAdapter.PairData(original.restoreRequestId(),original.lifecycleEvidence(),original.loadedSave(),original.first(),original.first()));
        assertThrows(IllegalArgumentException.class,()->new GameRestoreNativeAdapter.PairData(original.restoreRequestId(),original.lifecycleEvidence(),original.loadedSave(),original.second(),original.first()));
        assertThrows(IllegalArgumentException.class,()->new RestoreCheckpointService.IndependentReadPair(ref("manifest"),ref("same-ack"),ref("native-one"),ref("same-ack"),ref("native-two")));
    }
}
