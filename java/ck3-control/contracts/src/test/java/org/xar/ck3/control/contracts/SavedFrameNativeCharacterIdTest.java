package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;

final class SavedFrameNativeCharacterIdTest {
    private static SavedFrame frame(long actor) {return new SavedFrame("native:7",11,7,1000,actor,"controlled-native-domain");}

    @Test void actualSavedFrameProducerToSoleJsonCodecRetainsSignedActorAndAllOtherFields() {
        for(long actor:new long[]{Integer.MIN_VALUE,-16777217,-2,0,1,Integer.MAX_VALUE}) {
            var expected=frame(actor);var produced=expected.toJson();
            assertEquals(BigInteger.valueOf(actor),produced.get("actor_character_id").bigIntegerValue());
            assertTrue(produced.get("actor_character_id").isIntegralNumber());
            assertEquals(expected,SavedFrame.fromJson(produced));
            assertEquals(expected,SavedFrame.fromJson(StrictJson.parse(StrictJson.canonical(produced))));
            assertEquals(11,produced.get("revision").longValue());assertEquals(7,produced.get("native_revision").longValue());
            assertEquals(1000,produced.get("date_raw").longValue());assertEquals("native:7",produced.get("snapshot_id").textValue());
            assertEquals("controlled-native-domain",produced.get("episode_run_id").textValue());
        }
    }
    @Test void constructorAndActualJsonConsumerBothRefuseSentinelAndNarrowing() {
        for(long actor:new long[]{-1,((long)Integer.MIN_VALUE)-1,((long)Integer.MAX_VALUE)+1,Long.MIN_VALUE,Long.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class,()->frame(actor));
            var original=frame(1).toJson();original.put("actor_character_id",actor);
            assertThrows(IllegalArgumentException.class,()->SavedFrame.fromJson(original));
        }
        var factory=JsonNodeFactory.instance;
        for(JsonNode actor:List.of(factory.booleanNode(true),factory.booleanNode(false),factory.nullNode(),factory.textNode("-2"),
                factory.numberNode(-2.0),factory.numberNode(new BigInteger("2147483648")),factory.objectNode(),factory.arrayNode())) {
            var original=frame(1).toJson();original.set("actor_character_id",actor);
            assertThrows(IllegalArgumentException.class,()->SavedFrame.fromJson(original));
        }
        var missing=frame(1).toJson();missing.remove("actor_character_id");assertThrows(IllegalArgumentException.class,()->SavedFrame.fromJson(missing));
        var extra=frame(-2).toJson();extra.put("player_id",-2);assertThrows(IllegalArgumentException.class,()->SavedFrame.fromJson(extra));
    }
    @Test void signedActorDoesNotChangeSnapshotRevisionDateOrEpisodeGuards() {
        assertThrows(IllegalArgumentException.class,()->new SavedFrame("native:8",11,7,1000,-2,"controlled"));
        assertThrows(IllegalArgumentException.class,()->new SavedFrame("native:7",0,7,1000,-2,"controlled"));
        assertThrows(IllegalArgumentException.class,()->new SavedFrame("native:7",11,0,1000,-2,"controlled"));
        assertThrows(IllegalArgumentException.class,()->new SavedFrame("native:7",11,7,-1,-2,"controlled"));
        for(String field:List.of("revision","native_revision","date_raw")) {
            var original=frame(-2).toJson();original.put(field,true);assertThrows(IllegalArgumentException.class,()->SavedFrame.fromJson(original));
        }
    }
}
