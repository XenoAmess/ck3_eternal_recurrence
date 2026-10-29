package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Actual shared DeathSettlement normalizer -> typed inspection -> sole public role codec.
 * These DATA tests construct no Root, private physical lease, creator, action result or Host grant. */
final class LifecyclePublicCodecTest {
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static final String MACHINE="fixture-data-machine";
    private static final BigInteger FULL64=new BigInteger("18446744073709551615");
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static PublicBindings.Arguments arguments(String value){return PublicBindings.present(raw(value));}
    private static ObjectNode semantic() {
        return StrictJson.object().put("snapshot_id","original-snapshot").put("revision",FULL64).put("episode_character_id",42)
                .put("one_life_terminal",true).put("one_life_terminal_reason","played_character_dead").put("backend_id","pure-native");
    }
    private static LifecyclePublicCodec.Inspection inspect(ObjectNode original,boolean supported) {
        return LifecyclePublicCodec.inspect(DriverJson.object(PublicDataJson.encode(original).bytes(),RawJson.MAXIMUM_BYTES),
                supported?Set.of(LifecyclePublicCodec.SETTLEMENT_CAPABILITY):Set.of(),MACHINE,AT);
    }
    @Test void requestKeepsOuterAndRevisionMissingNullAndFullWidthStringStates() {
        assertEquals(LifecyclePublicCodec.ArgumentPresence.MISSING,LifecyclePublicCodec.decodeRequest(new PublicBindings.Missing()).presence());
        assertEquals(LifecyclePublicCodec.ArgumentPresence.NULL,LifecyclePublicCodec.decodeRequest(new PublicBindings.Null()).presence());
        assertInstanceOf(LifecyclePublicCodec.MissingRevision.class,LifecyclePublicCodec.decodeRequest(arguments("{}")).expectedRevision());
        assertInstanceOf(LifecyclePublicCodec.NullRevision.class,LifecyclePublicCodec.decodeRequest(arguments("{\"expected_revision\":null}")).expectedRevision());
        assertEquals(FULL64,LifecyclePublicCodec.decodeRequest(arguments("{\"expected_revision\":\"18446744073709551615\"}")).expected().orElseThrow());
        assertEquals(BigInteger.ZERO,LifecyclePublicCodec.decodeRequest(arguments("{\"expected_revision\":\"0\"}")).expected().orElseThrow());
        for(PublicBindings.Arguments original:List.of(new PublicBindings.Missing(),new PublicBindings.Null(),arguments("{}"),arguments("{\"expected_revision\":null}"),arguments("{\"expected_revision\":\"18446744073709551615\"}"))) {
            var decoded=LifecyclePublicCodec.decodeRequest(original);assertEquals(decoded,LifecyclePublicCodec.decodeRequest(LifecyclePublicCodec.encodeRequest(decoded)));
        }
        for(String invalid:List.of("true","false","0","1.0","9007199254740993","\"01\"","\"-1\"","\"18446744073709551616\"","\" 1\"","[]","{}"))
            assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeRequest(arguments("{\"expected_revision\":"+invalid+"}")),invalid);
        assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeRequest(arguments("{\"expected_revision\":null,\"unknown\":1}")));
        assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeNoArguments(arguments("{\"expected_revision\":null}")));
        assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeRequest(arguments("[]")));
    }
    @Test void pendingInspectionRetainsOriginalMissingNullAndPendingNormalization() {
        ObjectNode row=semantic();var missing=inspect(row,true);assertInstanceOf(LifecyclePublicCodec.MissingSettlement.class,missing.settlement());
        assertEquals(LifecyclePublicCodec.InspectionStatus.PENDING,missing.status());row.putNull("one_life_settlement");
        var explicitNull=inspect(row,true);assertInstanceOf(LifecyclePublicCodec.NullSettlement.class,explicitNull.settlement());
        var pendingWire=row.putObject("one_life_settlement").put("ready",false).putNull("commit_serial");var pending=inspect(row,true);
        assertInstanceOf(LifecyclePublicCodec.PendingSettlement.class,pending.settlement());
        var encoded=PublicDataJson.object(LifecyclePublicCodec.encode(pending));
        assertFalse(encoded.get("one_life_settlement").get("ready").booleanValue());assertTrue(encoded.get("one_life_settlement").get("commit_serial").isNull());
        assertEquals("18446744073709551615",encoded.get("revision").textValue());assertEquals(42,encoded.get("episode_character_id").intValue());
        assertEquals(encoded,PublicDataJson.object(LifecyclePublicCodec.encode(LifecyclePublicCodec.decodeInspection(LifecyclePublicCodec.encode(pending)))));
        pendingWire.put("commit_serial",1.0);assertThrows(IllegalArgumentException.class,()->inspect(row,true));
    }
    @Test void actualSharedReadyNormalizerBindsEpisodeAndPreservesOrdinaryScoreNumbersThroughPublicRoundtrip() {
        ObjectNode row=semantic();var settlement=row.putObject("one_life_settlement");settlement.put("ready",1).put("commit_serial",1).put("source_character_id",42);
        settlement.putObject("final_score").put("raw",2500).put("scale",1000);settlement.put("score_before_reject",3);
        settlement.put("record_candidate",3).put("old_record",2).put("record_delta",1).put("record_written",1)
                .put("blessing_count",1).put("refusal_count",0).put("contract_progress",2);
        row.set(NativeOneLifeSettlement.KEY,NativeOneLifeSettlement.normalize(settlement));
        var actual=inspect(row,true);assertEquals(LifecyclePublicCodec.InspectionStatus.READY,actual.status());
        var output=LifecyclePublicCodec.encode(actual);var encoded=PublicDataJson.object(output);
        assertTrue(encoded.get("one_life_settlement").get("final_score").isNumber());assertEquals(2.5,encoded.get("one_life_settlement").get("final_score").doubleValue());
        assertTrue(encoded.get("one_life_settlement").get("commit_serial").isIntegralNumber());assertTrue(encoded.get("heir_gameplay_actions").isIntegralNumber());
        assertEquals(MACHINE,encoded.get("machine_id").textValue());assertEquals(AT.toString(),encoded.get("observed_at_utc").textValue());
        assertEquals(encoded,PublicDataJson.object(LifecyclePublicCodec.encode(LifecyclePublicCodec.decodeInspection(output))));
        settlement.put("source_character_id",43);row.set(NativeOneLifeSettlement.KEY,NativeOneLifeSettlement.normalize(settlement));
        assertEquals(LifecyclePublicCodec.InspectionStatus.SOURCE_MISMATCH,inspect(row,true).status());
        assertEquals(LifecyclePublicCodec.InspectionStatus.UNAVAILABLE,inspect(row,false).status());
        row.put("one_life_terminal",false).putNull("one_life_terminal_reason");assertEquals(LifecyclePublicCodec.InspectionStatus.NOT_TERMINAL,inspect(row,true).status());
    }
    @Test void actualNormalizedRatioFloatsKeepSignedZeroAndIntegralFloatThroughSolePublicCodec() {
        ObjectNode row=semantic();ObjectNode nativeSettlement=StrictJson.object().put("ready",true).put("commit_serial",1)
                .put("source_character_id",42).put("record_candidate",0).put("old_record",0).put("record_delta",0)
                .put("record_written",false).put("blessing_count",0).put("refusal_count",0).put("contract_progress",0);
        nativeSettlement.putObject("final_score").put("raw",-1).put("scale",BigInteger.TEN.pow(400));
        nativeSettlement.putObject("score_before_reject").put("raw",new BigInteger("9007199254740993")).put("scale",new BigInteger("9007199254740992"));
        row.set(NativeOneLifeSettlement.KEY,NativeOneLifeSettlement.normalize(nativeSettlement));
        var actual=inspect(row,true);var ready=(LifecyclePublicCodec.ReadySettlement)actual.settlement();
        assertEquals(Double.doubleToRawLongBits(-0.0),Double.doubleToRawLongBits(ready.actual().normalizedJson().get("final_score").doubleValue()));
        assertTrue(ready.actual().normalizedJson().get("score_before_reject").isFloatingPointNumber());
        RawJson encoded=LifecyclePublicCodec.encode(actual);String wire=new String(encoded.bytes(),StandardCharsets.UTF_8);
        assertTrue(wire.contains("\"final_score\":-0.0"));assertTrue(wire.contains("\"score_before_reject\":1.0"));
        var decoded=LifecyclePublicCodec.decodeInspection(encoded);var again=(LifecyclePublicCodec.ReadySettlement)decoded.settlement();
        assertEquals(Double.doubleToRawLongBits(-0.0),Double.doubleToRawLongBits(again.actual().normalizedJson().get("final_score").doubleValue()));
        assertTrue(again.actual().normalizedJson().get("score_before_reject").isFloatingPointNumber());
        assertEquals(wire,new String(LifecyclePublicCodec.encode(decoded).bytes(),StandardCharsets.UTF_8));
        var applied=new LifecyclePublicCodec.Applied(Kind.DEATH,raw("{\"terminal\":true,\"continue_as_heir_after_death\":false,\"heir_gameplay_actions\":0,\"settlement_status\":\"complete\",\"score\":-0.0}"),MACHINE,AT);
        assertTrue(new String(LifecyclePublicCodec.encode(applied).bytes(),StandardCharsets.UTF_8).contains("\"score\":-0.0"),"DATA provenance projection must retain the actual normalized death score token");
    }
    @Test void dataOnlyAppliedProjectionRefusesNextAckOrNoHeirAndInspectionRefusesDetachedFields() {
        assertThrows(IllegalArgumentException.class,()->new LifecyclePublicCodec.Applied(Kind.NEXT_EPISODE,raw("{\"status\":\"started\",\"lifecycle_intent\":\"new_episode\",\"episode_run_id\":\"next\",\"cross_run_plan_used\":true}"),MACHINE,AT));
        assertThrows(IllegalArgumentException.class,()->new LifecyclePublicCodec.Applied(Kind.DEATH,raw("{\"terminal\":true,\"continue_as_heir_after_death\":true,\"heir_gameplay_actions\":0,\"settlement_status\":\"settlement_unavailable\"}"),MACHINE,AT));
        var output=LifecyclePublicCodec.encode(inspect(semantic(),true));var row=PublicDataJson.object(output);
        row.put("revision",FULL64);assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeInspection(PublicDataJson.encode(row)));
        row.put("revision",FULL64.toString()).put("status","ready");assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeInspection(PublicDataJson.encode(row)));
        row.put("status","pending").remove("machine_id");assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeInspection(PublicDataJson.encode(row)));
    }
}
