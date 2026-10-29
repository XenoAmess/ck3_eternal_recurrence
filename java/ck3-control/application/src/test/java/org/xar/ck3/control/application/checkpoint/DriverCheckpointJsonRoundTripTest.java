package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class DriverCheckpointJsonRoundTripTest {
    @Test void actualNativeScoreAndLargeIntegerSurviveTheRealCompleteDriverAndPublicSerializers() {
        for(String ratio:List.of("{\"raw\":1,\"scale\":2}","{\"raw\":-1,\"scale\":"+BigInteger.ONE.shiftLeft(2000)+"}")) {
            var normalized=NativeOneLifeSettlement.encodeScore(NativeOneLifeSettlement.normalizeScore(
                    FullJsonTree.parse(bytes(ratio),4096),"actual native ratio"));
            var row=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(bytes("{\"index\":1,\"command\":\"opaque-old-step\",\"ok\":false,"
                    +"\"contract_progress\":"+"8".repeat(70000)+",\"opaque\":[-0.0,1.0,1.234567890123456789]}"),FullJsonTree.MAXIMUM_BYTES);
            row.set("actual_native_score",normalized);
            var entry=new DriverStateSnapshot.HistoryEntry(1,new DriverStateSnapshot.Value(FullJsonTree.encode(row,FullJsonTree.MAXIMUM_BYTES)));
            var nil=new DriverStateSnapshot.NullValue();
            var actual=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("original-pipe",42,BigInteger.valueOf(73),"original-episode"),
                    List.of(entry),nil,nil,nil,nil,nil,nil,new DriverStateSnapshot.Value(bytes("[]")));
            byte[] original=actual.encode();var restored=DriverStateSnapshot.decodeComplete(original);
            assertArrayEquals(original,restored.encode());assertArrayEquals(entry.originalRow().json(),restored.commandHistory().getFirst().originalRow().json());
            var immutable=DriverJson.object(original,DriverCheckpointStore.MAX_DRIVER_BYTES);
            assertEquals(immutable,DriverJson.object(PublicDataJson.encode(DriverJson.toNormalizedNode(immutable)).bytes(),DriverJson.MAX_NATIVE_BYTES));
            var decoded=FullJsonTree.parse(restored.commandHistory().getFirst().originalRow().json(),FullJsonTree.MAXIMUM_BYTES);
            assertEquals(Double.doubleToRawLongBits(normalized.doubleValue()),Double.doubleToRawLongBits(decoded.get("actual_native_score").doubleValue()));
            assertEquals("1.234567890123456789",decoded.get("opaque").get(2).asText());
            assertEquals(70000,decoded.get("contract_progress").bigIntegerValue().toString().length());
            assertEquals(new OpportunityJson.DecimalValue("-0.0"),OpportunityJson.array(
                    DriverJson.object(entry.originalRow().json(),FullJsonTree.MAXIMUM_BYTES).get("opaque"),"opaque").getFirst());
        }
    }
    @Test void realDriverRequiredFieldsAndIntegerIdentitiesStayStrict() {
        String valid="{\"format_version\":2,\"pipe_name\":\"actual\",\"bridge_pid\":42,\"episode_character_id\":73,\"episode_run_id\":\"episode\","
                +"\"command_history\":[],\"last_checkpoint\":null,\"rollback_war_failure\":null,\"managed_restore_transaction\":null,"
                +"\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":[]}";
        DriverStateSnapshot.decodeComplete(bytes(valid));
        for(String invalid:List.of(valid.replace("\"bridge_pid\":42","\"bridge_pid\":42.0"),valid.replace("\"episode_character_id\":73","\"episode_character_id\":true"),
                valid.replace("\"campaign_goal\":null,",""),valid.replace("\"format_version\":2","\"format_version\":true")))
            assertThrows(IllegalArgumentException.class,()->DriverStateSnapshot.decodeComplete(bytes(invalid)));
        assertThrows(IllegalArgumentException.class,()->new DriverStateSnapshot.Value(bytes("null")));
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
}
