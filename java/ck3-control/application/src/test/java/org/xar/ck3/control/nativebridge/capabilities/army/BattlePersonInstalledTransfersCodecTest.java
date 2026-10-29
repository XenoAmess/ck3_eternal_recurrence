package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;

final class BattlePersonInstalledTransfersCodecTest {
    @TempDir Path temporary;
    private static ObjectNode parse(String value) { return (ObjectNode)StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode capture(long id,String pointer) {
        ObjectNode value=parse("""
          {"schema":"xar.ck3.person-native-six-stage-capture-12004-v1","build_version":"1.20.0.4",
           "executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
           "configured":false,"capture_observed":false,"capture_complete":false,"ready":false,"raw_counts_ready":false,
           "reason":"no-owned-capture","capture_sequence":0,"capture_date_raw":null,"character_id":0,
           "capture_thread_id":null,"query_thread_id":null,"character_identity":null,"context_identity":null,"source_return_rva":null,
           "stages":[],"source_stage":"ordered_six_attribute_native_calls","historical_capture":true,
           "actual_model_write_performed":false,"full_helper_ready":false}
          """);
        value.put("character_id",id);if(pointer!=null)value.put("character_identity",pointer);
        ArrayNode stages=(ArrayNode)value.get("stages");for(int index=0;index<6;index++) {
            ObjectNode stage=parse("{\"index\":0,\"observed\":false,\"raw_count_i32\":null,\"first_append_observed\":false,\"second_append_observed\":false,\"first_pc\":null,\"second_pc\":null}");stage.put("index",index);
            for(String key:List.of("first_pc","second_pc"))stage.set(key,parse("{\"ready\":false,\"reason\":\"not-observed\",\"admitted\":null,\"identity\":null,\"count_i32\":null,\"properties\":null,\"weight_q100000\":null}"));stages.add(stage);
        }
        return value;
    }
    private static BattlePersonSixStageCaptureCodec.NormalizedQuery owners(BigInteger revision,int date,long id,String pointer) {
        ObjectNode value=parse("{\"schema\":\"xar.ck3.person-native-six-stage-query-12004-v1\",\"snapshot_revision\":0,\"observed_date_raw\":0,\"character_captures\":[]}");
        value.put("snapshot_revision",revision);value.put("observed_date_raw",date);((ArrayNode)value.get("character_captures")).add(capture(id,pointer));
        return BattlePersonSixStageCaptureCodec.decode(value,"captures",revision,date,List.of(id));
    }
    private static ObjectNode query() {
        return parse("""
          {"schema":"xar.ck3.person-installed-transfer-capture-12004-v1","build_version":"1.20.0.4",
           "executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
           "historical_capture":true,"configured":false,"installed":false,"install_failure_flags":0,"request_filtered":true,
           "snapshot_revision":9,"observed_date_raw":53144328,"requested_receiver_count":1,"unresolved_receiver_count":0,
           "latest_record_sequence":0,"overwritten_records":0,"records":[]}
          """);
    }
    private static ObjectNode snapshot(long id,String pointer) {
        ObjectNode value=parse("{\"model_a_owner_identity\":null,\"model_a_owner_character_id\":null,\"model_b_owner_identity\":null,\"model_b_owner_character_id\":null,\"observed_owner_identity\":null,\"observed_owner_character_id\":null,\"carrier_identity\":null,\"installed_model_identity\":null,\"installed_model_owner_identity\":null,\"installed_owner_matches_observed_owner\":null,\"installed_model_is_a\":null,\"installed_model_is_b\":null,\"matching_installed_inline_context_identity\":null}");
        value.put("observed_owner_identity",pointer);value.put("observed_owner_character_id",id);return value;
    }
    private static ObjectNode record(long id,String pointer,long sequence) {
        ObjectNode row=parse("{\"record_sequence\":1,\"offline_fixture\":true,\"stage\":null,\"physical_postimage\":null}");row.put("record_sequence",sequence);
        ObjectNode stage=parse("""
          {"observation_stage":"actual_paired_transfer_return","observed":true,"original_called":true,"original_returned":true,
           "reason":"fixture-retained-data","model_a_identity":"0x2000","model_b_identity":"0x3000","original_return_rva":"0x2a3dc49",
           "before_event":{"clock_identity":"0x10","sequence":1,"thread_id":7},"completed_event":{"clock_identity":"0x10","sequence":2,"thread_id":7},
           "preparation":{"observed":false,"preparation_capture_complete":false,"preparation_capture_sequence":0,"preparation_capture_thread_id":null,
              "preparation_completion_thread_id":null,"preparation_character_identity":null,"preparation_model_identity":null,"preparation_context_identity":null,
              "preparation_owner_character_identity":null,"preparation_owner_character_id":null},"before":null,"after":null,
           "preparation_model_is_b":null,"preparation_owner_matches_before":null,"preparation_owner_matches_after":null,"before_after_owner_generation_equal":null,
           "event_clock_and_thread_match":null,"completion_ordered_after_begin":null,"generic_postimages_complete":false,
           "transfer_to_entry_association_proven":false,"observer_model_write_performed":false,"full_person_ready":false,"entry_ready":false}
          """);
        stage.set("before",snapshot(id,pointer));stage.set("after",snapshot(id,pointer));row.set("stage",stage);return row;
    }
    @Test void nativeIdZeroAndHighGenerationBitsRetainEngagedOwnerSemanticsAndRoundTrip() {
        for(long id:List.of(0L,0xab007485L,0xffff_ffffL)) {
            ObjectNode wire=query();wire.put("latest_record_sequence",1);((ArrayNode)wire.get("records")).add(record(id,"0x1000",1));
            var owners=owners(BigInteger.valueOf(9),53144328,id,"0x1000");var decoded=BattlePersonInstalledTransfersCodec.decode(wire,"transfers",owners,BigInteger.valueOf(9),53144328);
            assertEquals(0,decoded.unresolvedReceiverCount());assertEquals(id,decoded.records().get(0).beforeOwner().characterId());assertFalse(decoded.grantsEntryOrMutationAuthority());
            assertEquals(1,decoded.forReceiver(new BattlePersonInstalledTransfersCodec.Receiver(BigInteger.valueOf(4096),id)).size());
            assertArrayEquals(StrictJson.canonical(wire),StrictJson.canonical(decoded.toJson()));
            assertArrayEquals(StrictJson.canonical(decoded.toJson()),StrictJson.canonical(BattlePersonInstalledTransfersCodec.decode(decoded.toJson(),"transfers",owners,BigInteger.valueOf(9),53144328).toJson()));
            decoded.toJson().remove("records");assertEquals(1,decoded.records().size());
        }
    }
    @Test void missingNullWrongTypesAndStaleFramesCannotBecomeKnownTransfers() {
        var owners=owners(BigInteger.valueOf(9),53144328,0,"0x1000");
        ObjectNode missing=query();missing.remove("records");assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(missing,"transfers",owners,BigInteger.valueOf(9),53144328));
        ObjectNode nil=query();nil.putNull("records");assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(nil,"transfers",owners,BigInteger.valueOf(9),53144328));
        for(JsonNode bad:List.of(com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal("9.0")),com.fasterxml.jackson.databind.node.TextNode.valueOf("9"))) {
            ObjectNode value=query();value.set("snapshot_revision",bad);assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(value,"transfers",owners,BigInteger.valueOf(9),53144328));
        }
        ObjectNode stale=query();stale.put("observed_date_raw",53144352);assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(stale,"transfers",owners,BigInteger.valueOf(9),53144328));
        ObjectNode source=query();source.put("executable_sha256","0".repeat(64));assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(source,"transfers",owners,BigInteger.valueOf(9),53144328));
        ObjectNode extra=query();extra.put("backend_id","invented");assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(extra,"transfers",owners,BigInteger.valueOf(9),53144328));
        ObjectNode zero=query();zero.put("snapshot_revision",0);assertEquals(BigInteger.ZERO,BattlePersonInstalledTransfersCodec.decode(zero,"transfers",owners(BigInteger.ZERO,53144328,0,"0x1000"),BigInteger.ZERO,53144328).nativeRevision());
    }
    @Test void unresolvedOwnerCannotUseUnfilteredHistoryAndFullIdCannotAliasLowIndex() {
        ObjectNode wire=query();wire.put("latest_record_sequence",1);((ArrayNode)wire.get("records")).add(record(0xab007485L,"0x1000",1));
        var different=owners(BigInteger.valueOf(9),53144328,0xcd007485L,"0x1000");assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(wire,"transfers",different,BigInteger.valueOf(9),53144328));
        var unresolved=owners(BigInteger.valueOf(9),53144328,0xab007485L,null);wire.put("unresolved_receiver_count",1);assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(wire,"transfers",unresolved,BigInteger.valueOf(9),53144328));
        wire.putArray("records");assertEquals(1,BattlePersonInstalledTransfersCodec.decode(wire,"transfers",unresolved,BigInteger.valueOf(9),53144328).unresolvedReceiverCount());
        wire.put("request_filtered",false);assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(wire,"transfers",unresolved,BigInteger.valueOf(9),53144328));
        ObjectNode pointer=query();pointer.put("latest_record_sequence",1);((ArrayNode)pointer.get("records")).add(record(0xab007485L,"0x1000",1));
        ((ObjectNode)pointer.get("records").get(0).get("stage").get("before")).put("observed_owner_identity",4096);
        assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(pointer,"transfers",owners(BigInteger.valueOf(9),53144328,0xab007485L,"0x1000"),BigInteger.valueOf(9),53144328));
    }
    @Test void retainedRingAndLeafUnprovenFlagsAreRevalidatedByTheUniqueSharedRecord() {
        var owners=owners(BigInteger.valueOf(9),53144328,0,"0x1000");ObjectNode wire=query();wire.put("latest_record_sequence",129);wire.put("overwritten_records",1);
        ((ArrayNode)wire.get("records")).add(record(0,"0x1000",2));BattlePersonInstalledTransfersCodec.decode(wire,"transfers",owners,BigInteger.valueOf(9),53144328);
        ((ObjectNode)wire.get("records").get(0)).put("record_sequence",1);assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(wire,"transfers",owners,BigInteger.valueOf(9),53144328));
        ((ObjectNode)wire.get("records").get(0)).put("record_sequence",2);((ObjectNode)wire.get("records").get(0).get("stage")).put("entry_ready",true);
        assertThrows(IllegalArgumentException.class,()->BattlePersonInstalledTransfersCodec.decode(wire,"transfers",owners,BigInteger.valueOf(9),53144328));
    }
    @Test void actualNativeFilteredCaptureProducerFeedsTheOuterCodecAndTypedConsumer() throws Exception {
        Path executable=Path.of(required("xar.person.installed.transfer.fixture"));String expected=required("xar.person.installed.transfer.fixture.sha256");
        assertTrue(executable.isAbsolute());assertTrue(expected.matches("[a-f0-9]{64}"));long size=Files.size(executable);assertTrue(size>0 && size<=64L*1024*1024);
        assertEquals(expected,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(executable))));
        Path output=temporary.resolve("installed-transfer.stdout"),error=temporary.resolve("installed-transfer.stderr");
        Process process=new ProcessBuilder(executable.toString()).redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        try {
            assertTrue(process.waitFor(20,TimeUnit.SECONDS),"actual native fixture timeout");assertEquals(0,process.exitValue(),Files.readString(error));
            assertTrue(Files.size(output)<=1_048_576);List<String> rows=Files.readAllLines(output,StandardCharsets.UTF_8).stream().filter(line->line.startsWith("WIRE ")).toList();assertEquals(1,rows.size());
            ObjectNode wire=parse(rows.get(0).substring(5));JsonNode before=wire.get("records").get(0).get("stage").get("before");
            long id=before.get("observed_owner_character_id").longValue();String pointer=before.get("observed_owner_identity").textValue();
            var owners=owners(BigInteger.valueOf(88),12004,id,pointer);var decoded=BattlePersonInstalledTransfersCodec.decode(wire,"actual-native-transfers",owners,BigInteger.valueOf(88),12004);
            assertEquals(0xab007485L,decoded.records().get(0).beforeOwner().characterId());assertEquals(1,decoded.records().size());assertFalse(decoded.grantsEntryOrMutationAuthority());
            assertArrayEquals(StrictJson.canonical(wire),StrictJson.canonical(decoded.toJson()));
            ObjectNode snapshot=parse("{\"snapshot_id\":\"actual-native-fixture:88\",\"revision\":4,\"native_revision\":88,\"date_raw\":12004,\"paused\":true,\"episode_run_id\":\"offline-fixture\",\"backend_id\":\"native-headless\",\"diagnostics\":{\"hello\":{\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518\"}}}");
            var context=BattlePublicOriginalProducerTest.captured(snapshot).context();ObjectNode original=ArmyJson.empty();
            original.set("person_six_stage_captures",owners.toJson());original.set("person_installed_transfers",decoded.toJson());
            var projected=ArmyPublicWire.encode(org.xar.ck3.control.application.driver.DriverJson.object(ArmyJson.bytes(original),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES),context);
            var restored=ArmyPublicWire.decode(projected,context);var restoredJson=(ObjectNode)org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(restored);
            var restoredOwners=BattlePersonSixStageCaptureCodec.decode(restoredJson.get("person_six_stage_captures"),"public owners",BigInteger.valueOf(88),12004,List.of(id));
            var restoredTransfers=BattlePersonInstalledTransfersCodec.decode(restoredJson.get("person_installed_transfers"),"public transfer",restoredOwners,BigInteger.valueOf(88),12004);
            assertEquals(decoded.records().get(0).beforeOwner(),restoredTransfers.records().get(0).beforeOwner());assertFalse(restoredTransfers.grantsEntryOrMutationAuthority());
            assertEquals(projected,ArmyPublicWire.encode(restored,context));
            var publicRow=ArmyJson.parse(projected.bytes()).get("person_installed_transfers").get("records").get(0);
            assertTrue(publicRow.get("stage").get("before").get("observed_owner_identity").isTextual());assertTrue(publicRow.get("stage").get("before").get("observed_owner_character_id").isIntegralNumber());
            assertTrue(publicRow.get("stage").get("before_event").get("sequence").isTextual());assertTrue(publicRow.get("stage").get("before_event").get("thread_id").isIntegralNumber());
        } finally { process.destroyForcibly(); }
    }
    private static String required(String key) { String value=System.getProperty(key);if(value==null || value.isBlank())throw new IllegalStateException("NOT EXECUTED: missing qualified native fixture "+key);return value; }
}
