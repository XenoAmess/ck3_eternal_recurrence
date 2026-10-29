package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryPolicy;

/** Conditional mutations of an exact retained original input, not a claim of live Native provenance.
 * The signed32 observed-actor repair intentionally differs from the old Python positive-only predicate. */
final class RootConstructionWorldObservedActorTest {
    @Test void materialPublicConsumerAndColdWirePreserveZeroAndEverySignedNativeActorExceptAbsent()throws Exception {
        for(int actor:List.of(Integer.MIN_VALUE,-42,-2,0,1,Integer.MAX_VALUE)){
            ObjectNode input=input();replaceActor(input,actor);input.put("material_receipt",true);input.put("wartime_observation",false);
            var observation=ConstructionQueryCodec.decode(PublicDataJson.encode(input).bytes());
            var expected=input.get("expected_revision").bigIntegerValue();
            assertEquals(actor,NativeCharacterId.fromJson(input.path("starting_snapshot").path("played_character").get("character_id")).value());
            assertEquals(actor>0,ConstructionQueryPolicy.bound(observation.starting(),expected,false),"ordinary action/selection positive-only bound must stay unchanged");
            var before=DriverJson.object(PublicDataJson.encode(input.get("starting_snapshot")).bytes(),262144);
            var after=DriverJson.object(PublicDataJson.encode(input.get("ending_snapshot")).bytes(),262144);
            var response=RootConstructionWorldPublicProducts.finalizeOriginal(new RootConstructionWorldPublicProducts.Request(expected),before,after,
                    PublicDataJson.encode(input.get("native_envelope")),input.get("native_query_request_id").textValue());
            var memory=PublicDataJson.object(response.originalMemory());assertEquals("material_source",memory.path("status").textValue());
            assertEquals(actor,memory.path("source_frame").path("actor_character_id").intValue());
            assertEquals(actor,memory.path("world").path("player_character_id").intValue());
            assertEquals(memory,PublicDataJson.object(RootConstructionWorldPublicProducts.restore(RootConstructionWorldPublicProducts.encode(response)).originalMemory()));
            input.put("material_receipt",false);
            if(actor<=0)assertEquals("read_rejected",StrictJson.parse(ConstructionQueryCodec.finalizeObservation(PublicDataJson.encode(input).bytes()),262144).path("status").textValue());
        }
    }
    @Test void observedActorRejectsSentinelOverflowBoolFloatStringAndKeepsTheOtherFrameGuards()throws Exception {
        for(JsonNode token:List.of(StrictJson.object().numberNode(-1),StrictJson.object().numberNode(new BigInteger("2147483648")),
                StrictJson.object().numberNode(new BigInteger("-2147483649")),StrictJson.object().booleanNode(true),StrictJson.object().numberNode(1.0),StrictJson.object().textNode("0"))){
            ObjectNode input=input();((ObjectNode)input.path("starting_snapshot").path("played_character")).set("character_id",token);
            var before=DriverJson.object(PublicDataJson.encode(input.get("starting_snapshot")).bytes(),262144);
            assertThrows(IllegalArgumentException.class,()->RootConstructionWorldPublicProducts.requireFrame(before,new RootConstructionWorldPublicProducts.Request(input.get("expected_revision").bigIntegerValue())));
        }
        for(String field:List.of("paused","map_ready")){
            ObjectNode input=input();replaceActor(input,0);((ObjectNode)input.get("starting_snapshot")).put(field,false);
            var before=DriverJson.object(PublicDataJson.encode(input.get("starting_snapshot")).bytes(),262144);
            assertThrows(IllegalArgumentException.class,()->RootConstructionWorldPublicProducts.requireFrame(before,new RootConstructionWorldPublicProducts.Request(input.get("expected_revision").bigIntegerValue())));
        }
        ObjectNode input=input();replaceActor(input,0);((ObjectNode)input.path("starting_snapshot").path("played_character")).put("alive",false);
        assertEquals("read_rejected",StrictJson.parse(ConstructionQueryCodec.finalizeObservation(PublicDataJson.encode(input).bytes()),262144).path("status").textValue());
    }
    private static void replaceActor(ObjectNode input,int actor){
        for(String key:List.of("starting_snapshot","ending_snapshot"))((ObjectNode)input.path(key).path("played_character")).put("character_id",actor);
        ((ObjectNode)input.path("native_envelope").path("result").path("private_probe").path("player_world_building_sources")).put("player_character_id",actor);
    }
    private static ObjectNode input()throws Exception {
        Path path=Path.of(required("xar.construction.world.original.input"));byte[] bytes=Files.readAllBytes(path);
        assertEquals(required("xar.construction.world.original.sha256"),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode input=(ObjectNode)StrictJson.parse(bytes,262144);assertTrue(input.path("material_receipt").booleanValue());return input;
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("actual retained material input prerequisite missing: "+key);return value;}
}
