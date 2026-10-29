package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import org.junit.jupiter.api.Test;

class DriverValueMaterialTest {
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    @Test void completeDriverWithNonemptyHistoryAndCheckpointEqualsItsFreshDecodedOriginal(){
        String progress="9".repeat(70000);
        byte[] original=bytes("{\"format_version\":2,\"pipe_name\":\"data-pipe\",\"bridge_pid\":17,\"episode_character_id\":-2,\"episode_run_id\":\"data-run\","
                +"\"command_history\":[{\"index\":1,\"command\":\"data\",\"opaque\":-0.0,\"progress\":"+progress+"}],"
                +"\"last_checkpoint\":{\"history_index\":1,\"saved_date_raw\":124,\"opaque\":1.0},\"rollback_war_failure\":null,"
                +"\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":{},\"campaign_goal\":{\"progress\":"+progress+"},\"rollback_war_failures\":[]}");
        var first=DriverStateSnapshot.decodeComplete(original);var decoded=DriverStateSnapshot.decodeComplete(first.encode());
        assertEquals(first,decoded);assertEquals(first.hashCode(),decoded.hashCode());assertEquals(1,new HashSet<>(List.of(first,decoded)).size());
        assertEquals(first.commandHistory(),decoded.commandHistory());assertEquals(first.lastCheckpoint(),decoded.lastCheckpoint());
        assertArrayEquals(first.encode(),decoded.encode());
    }
    @Test void checkedValueContentIdentityRetainsDefensiveCopiesAndExactDecimalTokens(){
        byte[] original=bytes("{\"opaque\":-0.0,\"ratio\":1.0}");
        var value=new DriverStateSnapshot.Value(original);var equal=new DriverStateSnapshot.Value(value.json());
        original[0]='[';byte[] copy=value.json();copy[0]='[';
        assertEquals(value,equal);assertEquals(value.hashCode(),equal.hashCode());assertEquals(1,new HashSet<>(List.of(value,equal)).size());
        assertNotEquals(value,new DriverStateSnapshot.Value(bytes("{\"opaque\":0.0,\"ratio\":1.0}")));
        assertNotEquals(value,new DriverStateSnapshot.Value(bytes("{\"opaque\":-0.0,\"ratio\":1}")));
        assertNotEquals(new DriverStateSnapshot.Missing(),new DriverStateSnapshot.NullValue());
        assertThrows(IllegalArgumentException.class,()->new DriverStateSnapshot.Value(bytes("null")));
    }
}
