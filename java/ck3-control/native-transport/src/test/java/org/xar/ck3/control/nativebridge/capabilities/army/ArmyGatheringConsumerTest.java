package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** The existing Native transport consumer and closed public codec share the one application parser. */
final class ArmyGatheringConsumerTest {
    private static final String RAW="""
      {"step":"query-army-gathering-research-sampling-v1","accepted":true,"status":"enabled","backend_id":"native-headless",
       "army_gathering_research_sampling_v1":{"capture_enabled":true,"busy":false,"clear_completed":false,
        "epoch":18446744073709551615,"active_captures":0,"retained_records":1,"qualified_records":1,"readiness":"retained_observation"}}
      """;
    @Test void originalConsumerAndPublicRoundTripRetainAllU64Fields() {
        byte[] original=RAW.getBytes(StandardCharsets.UTF_8);var actual=ArmyGatheringCodec.decode(original,ArmyGatheringCodec.QUERY);
        var consumed=ArmyResponseCodec.gathering(original,ArmyGatheringCodec.QUERY);assertEquals(actual.epoch(),consumed.epoch().value());
        assertEquals(actual.status().name(),consumed.status().name());assertEquals(actual.readiness().name(),consumed.readiness().name());
        var call=ArmyClosedReadCodecTest.call(PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1,"{\"expected_revision\":7}");
        var context=ArmyClosedReadCodecTest.context("1.20.0.4",0);
        var value=ArmyClosedReadCodec.decodeToken(call,context,original);RawJson publicResult=ArmyClosedReadCodec.encode(value,context);
        assertEquals(value,ArmyClosedReadCodec.decodePublic(call,context,publicResult));
        assertEquals(new BigInteger("18446744073709551615"),actual.epoch());
        assertTrue(ArmyJson.parse(publicResult.bytes()).get("army_gathering_research_sampling_v1").get("epoch").isTextual());
        assertTrue(ArmyJson.parse(original).get("army_gathering_research_sampling_v1").get("epoch").isIntegralNumber());
    }
    @Test void bothActualConsumersRejectMissingUnknownAndWrongScalarDomains() {
        for(String token:List.of("true","0.0","\"0\"","null","-1","18446744073709551616")) {
            String wrong=RAW.replace("\"active_captures\":0","\"active_captures\":"+token);
            assertThrows(IllegalArgumentException.class,()->ArmyGatheringCodec.decode(wrong.getBytes(StandardCharsets.UTF_8),ArmyGatheringCodec.QUERY));
            assertThrows(IllegalArgumentException.class,()->ArmyResponseCodec.gathering(wrong.getBytes(StandardCharsets.UTF_8),ArmyGatheringCodec.QUERY));
        }
        var extra=ArmyJson.parse(RAW.getBytes(StandardCharsets.UTF_8)).put("invented",1);
        assertThrows(IllegalArgumentException.class,()->ArmyResponseCodec.gathering(ArmyJson.bytes(extra),ArmyGatheringCodec.QUERY));
        var missing=ArmyJson.parse(RAW.getBytes(StandardCharsets.UTF_8));((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("army_gathering_research_sampling_v1")).remove("epoch");
        assertThrows(IllegalArgumentException.class,()->ArmyGatheringCodec.decode(ArmyJson.bytes(missing),ArmyGatheringCodec.QUERY));
        assertThrows(IllegalArgumentException.class,()->ArmyGatheringCodec.decode(RAW.getBytes(StandardCharsets.UTF_8),"query-invented-sampling"));
    }
    @Test void busyDisableIsNotAcceptedAndRetainedRecordsNeverMeanMilitaryReadiness() {
        String busy="""
          {"step":"disable-army-gathering-research-sampling-v1","accepted":false,"status":"busy","backend_id":"native-headless",
           "army_gathering_research_sampling_v1":{"capture_enabled":false,"busy":true,"clear_completed":false,
            "epoch":4,"active_captures":1,"retained_records":1,"qualified_records":1,"readiness":"off"}}
          """;
        var value=ArmyGatheringCodec.decode(busy.getBytes(StandardCharsets.UTF_8),ArmyGatheringCodec.DISABLE);
        assertFalse(value.accepted());assertEquals(ArmyGatheringCodec.Status.BUSY,value.status());assertEquals(ArmyGatheringCodec.Readiness.OFF,value.readiness());
        assertFalse(ArmyResponseCodec.gathering(busy.getBytes(StandardCharsets.UTF_8),ArmyGatheringCodec.DISABLE).accepted());
    }
}
