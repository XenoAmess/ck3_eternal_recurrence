package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/** Pure original ROOT/M3 -> complete Driver/serialization seam. This does not manufacture a live Root capture. */
final class DriverPreclockExpectationProducerTest {
    @Test void originalM3EstateReplacesOnlyExpectationAndPreservesAllOtherDriverSlotsAndRawHistory() {
        var before=driver(2,"old-episode");byte[] original=before.encode();
        var estate=SuccessionNativeEstate12004.freeze(root(),semantic());
        var after=DriverPreclockExpectationProducer.replace(before,estate);
        assertSame(before.session(),after.session());assertEquals(before.commandHistory(),after.commandHistory());
        assertSame(before.lastCheckpoint(),after.lastCheckpoint());assertSame(before.rollbackWarFailure(),after.rollbackWarFailure());
        assertSame(before.managedRestoreTransaction(),after.managedRestoreTransaction());assertSame(before.successionLifecycle(),after.successionLifecycle());
        assertSame(before.campaignGoal(),after.campaignGoal());assertSame(before.rollbackWarFailures(),after.rollbackWarFailures());
        assertArrayEquals(original,before.encode());
        assertArrayEquals(estate.wire(),assertInstanceOf(DriverStateSnapshot.Value.class,after.successionExpectation()).json());
        var decoded=DriverStateSnapshot.decodeComplete(after.encode());
        assertArrayEquals(after.encode(),decoded.encode());
        assertInstanceOf(DriverStateSnapshot.Missing.class,decoded.successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.Missing.class,decoded.rollbackWarFailures());
        assertArrayEquals(before.commandHistory().getFirst().originalRow().json(),decoded.commandHistory().getFirst().originalRow().json());
        assertArrayEquals(assertInstanceOf(DriverStateSnapshot.Value.class,before.campaignGoal()).json(),
                assertInstanceOf(DriverStateSnapshot.Value.class,decoded.campaignGoal()).json());
    }
    @Test void estateFromAnotherEpisodeOrActorCannotReplaceTheDriverExpectation() {
        var estate=SuccessionNativeEstate12004.freeze(root(),semantic());
        assertThrows(IllegalArgumentException.class,()->DriverPreclockExpectationProducer.replace(driver(3,"old-episode"),estate));
        assertThrows(IllegalArgumentException.class,()->DriverPreclockExpectationProducer.replace(driver(2,"other-episode"),estate));
        var wrong=assertInstanceOf(ObjectNode.class,StrictJson.parse(semantic()));wrong.put("native_revision",12);
        assertThrows(IllegalArgumentException.class,()->SuccessionNativeEstate12004.freeze(root(),StrictJson.canonical(wrong)));
    }
    private static DriverStateSnapshot.Complete driver(int actor,String episode) {
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-original-pipe",7,BigInteger.valueOf(actor),episode),
                List.of(new DriverStateSnapshot.HistoryEntry(1,value("{\"index\":1,\"command\":\"retained-original\",\"raw_identity\":90071992547409931234567890}"))),
                value("{\"original_checkpoint\":true}"),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.Missing(),value("{\"original_goal\":90071992547409931234567890}"),new DriverStateSnapshot.Missing());
    }
    private static DriverStateSnapshot.Value value(String json) {return new DriverStateSnapshot.Value(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static byte[] root() {
        var result=StrictJson.object().put("step","query-campaign-root-context-v1").put("accepted",true).put("status","available")
                .put("query_sequence",11).put("snapshot_revision",11).put("backend_id","native-headless");
        var root=result.putObject("campaign_root_context").put("schema_version",1).put("status","available").put("snapshot_revision",11)
                .put("date_raw",100).put("player_character_id",2).put("player_character_alive",true).putNull("unavailable_reason");
        root.set("primary_title",title(10));root.putArray("primary_title_succession_character_ids").add(3);
        root.putObject("provenance").put("game_version","1.20.0.4").put("executable_sha256",SuccessionNativeEstate12004.EXECUTABLE_SHA256)
                .put("backend_id","ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset","0x1E0").put("primary_title_rva","0x289DA10");
        var readiness=root.putObject("readiness");
        for(String key:List.of("player_identity_ready","primary_title_ready","primary_title_succession_ready","held_title_partition_ready","same_frame_ready"))readiness.put(key,true);
        var rows=root.putArray("held_title_partition");rows.add(row(10,3,true));rows.add(row(20,4,false));
        return StrictJson.canonical(result,SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
    }
    private static ObjectNode title(int id) {return StrictJson.object().put("title_id",id).put("tier_raw",2).put("tier_key","county");}
    private static ObjectNode row(int id,int heir,boolean primary) {
        var row=StrictJson.object().put("first_heir_character_id",heir).put("primary",primary).put("capital_province_id",id+1);row.set("title",title(id));return row;
    }
    private static byte[] semantic() {
        var semantic=StrictJson.object().put("snapshot_id","actual-11").put("revision",111).put("native_revision",11).put("date_raw",100)
                .put("episode_run_id","old-episode").put("episode_character_id",2).put("paused",true).put("map_ready",true).put("one_life_terminal",false)
                .putNull("one_life_terminal_reason").putNull("active_event").putNull("pending_character_interaction");
        semantic.putObject("played_character").put("character_id",2).put("alive",true);
        semantic.putObject("succession_lifecycle").put("lifecycle","ordinary_campaign_succession");
        return StrictJson.canonical(semantic,SuccessionNativeEstate12004.MAX_SOURCE_BYTES);
    }
}
