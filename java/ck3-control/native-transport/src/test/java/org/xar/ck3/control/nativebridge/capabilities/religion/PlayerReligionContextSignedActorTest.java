package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Pure component DATA regression for the actual signed C++ field. No fixture creates Native or Game authority. */
final class PlayerReligionContextSignedActorTest {
    @Test void actualComponentDecodeEncodeAndFrameConsumerPreserveSignedActors() {
        for(int actor:List.of(Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE)){
            ObjectNode raw=component(actor,true);var actual=PlayerReligionContext.decode(raw);
            assertEquals(BigInteger.valueOf(actor),actual.playedCharacterId());
            assertEquals(raw,actual.encode());assertEquals(actual,PlayerReligionContext.decode(actual.encode()));
            actual.requireAvailableFrame(BigInteger.ONE,BigInteger.valueOf(actor));
            assertThrows(IllegalArgumentException.class,()->actual.requireAvailableFrame(BigInteger.ONE,BigInteger.valueOf(actor).add(BigInteger.ONE)));
        }
    }
    @Test void nativeUnavailableSentinelRemainsDiagnosticAndNeverBecomesAnAvailableCharacter() {
        ObjectNode raw=component(-1,false);var unavailable=PlayerReligionContext.decode(raw);
        assertFalse(unavailable.available());assertEquals(BigInteger.valueOf(-1),unavailable.playedCharacterId());assertEquals(raw,unavailable.encode());
        unavailable.requireAvailableFrame(BigInteger.ONE,BigInteger.valueOf(29829));
        assertThrows(IllegalArgumentException.class,()->PlayerReligionContext.decode(component(-1,true)));
        for(ObjectNode malformed:List.of(raw.deepCopy().put("played_character_id",4294967294L),raw.deepCopy().put("played_character_id",2147483648L),raw.deepCopy().put("played_character_id",true),raw.deepCopy().put("played_character_id",-2.0),raw.deepCopy().put("played_character_id","-2")))assertThrows(IllegalArgumentException.class,()->PlayerReligionContext.decode(malformed));
    }
    @Test void actualObservationAndPublicProjectionKeepTheSameSignedPlayer() {
        var context=PlayerReligionContext.decode(component(-2,true));
        var metadata=new PlayerReligionContextRead.Metadata("software-source-frame",BigInteger.ONE,BigInteger.ONE,1,BigInteger.valueOf(-2),"ck3-1.20.0.4-native-player-religion-context-v1","observed");
        var observed=new PlayerReligionContextRead.Observation(context,metadata);
        ObjectNode nativeView=PlayerReligionContextRead.flattened(observed);
        ObjectNode publicView=org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec.publicResult(
                org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec.method("ck3_query_player_religion_context_v1"),nativeView);
        assertEquals(-2,nativeView.get("played_character_id").intValue());assertEquals(-2,publicView.get("played_character_id").intValue());
        assertTrue(nativeView.get("capture_epoch").isIntegralNumber());assertEquals("1",publicView.get("capture_epoch").textValue());
        assertThrows(IllegalArgumentException.class,()->new PlayerReligionContextRead.Metadata("software-source-frame",BigInteger.ONE,BigInteger.ONE,1,new BigInteger("4294967294"),"ck3-1.20.0.4-native-player-religion-context-v1","observed"));
    }
    private static ObjectNode component(int actor,boolean available){
        var build=PlayerReligionContext.Build.CROZIER4;
        ObjectNode value=StrictJson.object().put("schema",build.schema()).put("game_version",build.version()).put("executable_sha256",build.sha256()).put("available",available)
                .put("capture_epoch",1).put("date_raw",1).put("played_character_id",actor).put("raw_scale",100000);
        for(String name:List.of("rite_id","faith_id","religion_id","faith_main_rite_id","faith_key","religion_key","faith_fervor_raw"))value.putNull(name);
        if(available)value.putNull("unavailable_reason").put("spiritual_fulfillment_raw",1);
        else value.put("unavailable_reason","native_context_unavailable").putNull("spiritual_fulfillment_raw");
        return value;
    }
}
