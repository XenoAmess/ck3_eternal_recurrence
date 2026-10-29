package org.xar.ck3.control.contracts.offline;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;

/** Versioned source DATA and report binding only. No actual incident, packet, worker custody or Game is minted. */
final class OfflineBatchBindingActorTest {
    private static final ExactRef INDEX=new ExactRef("source-index",12,"a".repeat(64));
    private static final ExactRef MANIFEST=new ExactRef("source-manifest",34,"b".repeat(64));
    private static CrossJsDecimalUInt64 u(String value) { return new CrossJsDecimalUInt64(value); }
    private static OfflineBatchBinding.Frame frame(NativeCharacterId actor) {
        return new OfflineBatchBinding.Frame(actor,u("18446744073709551615"),u("0"),"source-snapshot",u("18446744073709551614"),"source-episode");
    }
    private static OfflineBatchBinding.ObservedScan scan(OfflineBatchBinding.Frame frame) {
        return new OfflineBatchBinding.ObservedScan("source-session",new OfflineBatchBinding.Observation("source-machine",
                new GameGeneration(12345,new PythonOnlyUInt64(BigInteger.ONE)),1,frame),
                new OfflineBatchBinding.Source("source-machine","2026-10-24T00:00:00Z","source-build",INDEX),INDEX);
    }
    private static ObjectNode manifest(OfflineBatchBinding.ObservedScan scan) {
        ObjectNode out=StrictJson.object();out.put("schema",OfflineBatchBinding.manifestSchema(scan));out.put("session_id",scan.sessionId());
        out.set("scan_observation",scan.observation().toJson());out.set("scan_source",scan.source().toJson());out.set("index_ref",scan.indexRef().toJson());out.putArray("new_incidents");return out;
    }
    private static ObjectNode report(OfflineBatchBinding.Binding scan) {
        ObjectNode out=StrictJson.object();out.put("machine_id","source-machine");out.set("manifest",MANIFEST.toJson());OfflineBatchBinding.addReportBinding(out,scan);return out;
    }
    private static JsonNode persisted(JsonNode value) { return StrictJson.parse(StrictJson.canonical(value),65536); }
    @Test void signedActualFrameDataAndReportsPreserveAllBoundaryValuesThroughPersistentJson() {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE}) {
            var actual=scan(frame(new NativeCharacterId(actor)));ObjectNode manifest=manifest(actual);
            assertEquals(OfflineBatchBinding.MANIFEST_V3,manifest.path("schema").textValue());
            assertTrue(manifest.path("scan_observation").path("frame").path("played_character_id").isIntegralNumber());
            assertEquals(actor,manifest.path("scan_observation").path("frame").path("played_character_id").intValue());
            assertEquals(actual,OfflineBatchBinding.manifest(persisted(manifest)));
            ObjectNode report=report(actual);assertEquals(OfflineBatchBinding.REPORT_V3,report.path("schema").textValue());
            assertEquals(actual.observation(),OfflineBatchBinding.observationForReport(persisted(report)));
            OfflineBatchBinding.requireReport(persisted(report),actual,MANIFEST);
            assertEquals("18446744073709551615",actual.observation().frame().nativeRevision().decimal());
            assertEquals("0",actual.observation().frame().dateRaw().decimal());
        }
    }
    @Test void historicalUnsignedV2AndCompletedV1KeepTheirOriginalDomainsAndDoNotBecomeNativeV3() {
        var old=scan(new OfflineBatchBinding.Frame(u("18446744073709551615"),u("2"),u("0"),"old-snapshot",u("3"),"old-episode"));
        ObjectNode manifest=manifest(old);assertEquals(OfflineBatchBinding.MANIFEST_V2,manifest.path("schema").textValue());
        assertTrue(manifest.path("scan_observation").path("frame").path("played_character_id").isTextual());
        assertEquals(old,OfflineBatchBinding.manifest(persisted(manifest)));OfflineBatchBinding.requireReport(persisted(report(old)),old,MANIFEST);
        ObjectNode wrong=manifest.deepCopy();wrong.put("schema",OfflineBatchBinding.MANIFEST_V3);
        assertThrows(IllegalArgumentException.class,()->OfflineBatchBinding.manifest(wrong));
        var legacy=new OfflineBatchBinding.LegacyCompleted(BigInteger.ZERO);ObjectNode v1=StrictJson.object();v1.put("completed_control_sequence",0);v1.putArray("new_incidents");
        assertEquals(legacy,OfflineBatchBinding.manifest(v1));ObjectNode legacyReport=report(legacy);
        assertEquals(OfflineBatchBinding.REPORT_V1,legacyReport.path("schema").textValue());OfflineBatchBinding.requireReport(legacyReport,legacy,MANIFEST);
    }
    @Test void malformedNativeActorsAndVersionRelabelingRejectWithoutUnsignedAliasing() {
        ObjectNode base=manifest(scan(frame(new NativeCharacterId(-2))));
        JsonNode[] bad={StrictJson.object().put("v",-1).get("v"),StrictJson.object().put("v",true).get("v"),
            StrictJson.object().put("v","-2").get("v"),StrictJson.object().put("v",-2.0).get("v"),
            StrictJson.object().put("v",BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)).get("v"),StrictJson.object().putNull("v").get("v")};
        for(JsonNode actor:bad) {ObjectNode altered=base.deepCopy();((ObjectNode)altered.path("scan_observation").path("frame")).set("played_character_id",actor);
            assertThrows(IllegalArgumentException.class,()->OfflineBatchBinding.manifest(altered));}
        ObjectNode down=base.deepCopy();down.put("schema",OfflineBatchBinding.MANIFEST_V2);
        assertThrows(IllegalArgumentException.class,()->OfflineBatchBinding.manifest(down));
        var original=scan(frame(new NativeCharacterId(-2)));ObjectNode changed=report(original);changed.put("schema",OfflineBatchBinding.REPORT_V2);
        assertThrows(IllegalArgumentException.class,()->OfflineBatchBinding.requireReport(changed,original,MANIFEST));
        ObjectNode missing=base.deepCopy();((ObjectNode)missing.path("scan_observation").path("frame")).remove("played_character_id");
        assertThrows(IllegalArgumentException.class,()->OfflineBatchBinding.manifest(missing));
    }
}
