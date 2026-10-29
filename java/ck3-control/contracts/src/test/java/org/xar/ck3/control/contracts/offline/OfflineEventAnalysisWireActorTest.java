package org.xar.ck3.control.contracts.offline;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.*;

/** Real binding producer to public wire DATA only; no incident, worker or Game authority. */
final class OfflineEventAnalysisWireActorTest {
    @TempDir Path temporary;
    private static CrossJsDecimalUInt64 u(String value) { return new CrossJsDecimalUInt64(value); }
    private ExactRef file(String name) throws Exception {
        Path path=temporary.resolve(name);byte[] raw=name.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(path,raw);return new ExactRef(path.toString(),raw.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
    private ObjectNode result(OfflineBatchBinding.Frame frame,String name) throws Exception {
        ExactRef index=file(name+".index"),manifest=file(name+".manifest"),reportRef=file(name+".report"),grants=file(name+".grants");
        var binding=new OfflineBatchBinding.ObservedScan("source-session",new OfflineBatchBinding.Observation("source-machine",
                new GameGeneration(1,new PythonOnlyUInt64(BigInteger.ONE)),1,frame),
                new OfflineBatchBinding.Source("source-machine","2026-10-24T00:00:00Z","source-build",index),index);
        ObjectNode report=StrictJson.object();OfflineBatchBinding.addReportBinding(report,binding);
        report.put("machine_id","source-machine");report.put("observed_at_utc","2026-10-24T00:00:00Z");report.set("manifest",manifest.toJson());
        report.putArray("entries");report.putArray("already_known");report.putArray("unresolved");report.put("Game_MCP_OBS_calls",0);report.put("material_effects_verified",false);
        ObjectNode out=StrictJson.object();out.put("schema",OfflineEventAnalysisContract.BATCH_RESULT_SCHEMA);out.put("batch_id","source-batch");
        out.put("machine_id","source-machine");out.put("observed_at_utc","2026-10-24T00:00:00Z");out.put("idempotent",false);
        out.set("report_ref",reportRef.toJson());out.set("report",report);out.putArray("outputs");
        ObjectNode publication=grants.toJson();publication.put("grants",0);publication.put("added",0);out.set("grants_manifest",publication);
        out.put("Game_MCP_OBS_calls",0);out.put("timeline_writer_calls",0);return out;
    }
    private static OfflineBatchBinding.Frame nativeFrame(int actor) {
        return new OfflineBatchBinding.Frame(new NativeCharacterId(actor),u("18446744073709551615"),u("0"),"source-snapshot",u("2"),"source-episode");
    }
    private static byte[] raw(JsonNode value) { return StrictJson.canonical(value); }
    @Test void signedNativeReportProducerSurvivesPublicWireWithoutActorReencoding() throws Exception {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE}) {
            ObjectNode out=result(nativeFrame(actor),"native"+actor);byte[] original=raw(out);
            assertEquals(OfflineBatchBinding.REPORT_V3,out.path("report").path("schema").textValue());
            assertArrayEquals(original,OfflineEventAnalysisWire.validateBatchResult(original,"source-batch"));
            JsonNode persisted=OfflineEventAnalysisWire.parseMetadataObject(original);
            JsonNode actual=OfflineBatchBinding.observationForReport(persisted.get("report")).frame().toJson().get("played_character_id");
            assertTrue(actual.isIntegralNumber());assertEquals(actor,actual.intValue());
        }
    }
    @Test void historicalUnsignedAndCompletedVersionsKeepTheirOwnActorDomains() throws Exception {
        ObjectNode old=result(new OfflineBatchBinding.Frame(u("18446744073709551615"),u("2"),u("0"),"old-snapshot",u("3"),"old-episode"),"old");
        assertEquals(OfflineBatchBinding.REPORT_V2,old.path("report").path("schema").textValue());
        assertArrayEquals(raw(old),OfflineEventAnalysisWire.validateBatchResult(raw(old),"source-batch"));
        ObjectNode legacy=old.deepCopy();ObjectNode report=StrictJson.object();report.put("schema",OfflineBatchBinding.REPORT_V1);report.put("completed_control_sequence",0);legacy.set("report",report);
        assertArrayEquals(raw(legacy),OfflineEventAnalysisWire.validateBatchResult(raw(legacy),"source-batch"));
    }
    @Test void explicitNativeVersionRejectsUnsignedAliasesAndMalformedActors() throws Exception {
        ObjectNode original=result(nativeFrame(-2),"negative");
        JsonNode[] invalid=java.util.Arrays.stream(new String[]{"-1","true","\"-2\"","-2.0","2147483648","null"})
                .map(text->StrictJson.parse(text.getBytes(java.nio.charset.StandardCharsets.UTF_8),32)).toArray(JsonNode[]::new);
        for(JsonNode bad:invalid) {
            ObjectNode out=original.deepCopy();((ObjectNode)out.path("report").path("scan_observation").path("frame")).set("played_character_id",bad);
            assertThrows(IllegalArgumentException.class,()->OfflineEventAnalysisWire.validateBatchResult(raw(out),"source-batch"));
        }
        ObjectNode relabeled=original.deepCopy();((ObjectNode)relabeled.get("report")).put("schema",OfflineBatchBinding.REPORT_V2);
        assertThrows(IllegalArgumentException.class,()->OfflineEventAnalysisWire.validateBatchResult(raw(relabeled),"source-batch"));
    }
}
