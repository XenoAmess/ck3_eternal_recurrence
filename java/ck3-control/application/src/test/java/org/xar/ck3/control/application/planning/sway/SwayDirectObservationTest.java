package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;

/** Explicit software native packets derived from mandatory retained originals; no current native or Root qualification. */
final class SwayDirectObservationTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");private static final long ACTOR=50331649,TARGET=50331650,ID=33554443;
    private static final ExactRef SOURCE=new ExactRef("software:sole-observation-source",1,"a".repeat(64));
    @Test void installedNativeFamiliesPreserveActionlessSubjectsThroughSoleDecoderOrdinaryConsumerAndPublicSerialization()throws Exception {
        var definitions=new SwayRootReads(new SwayRootReads.Sources(SOURCE,SOURCE,SOURCE));var catalog=new RootReadContractCatalog(List.of(),definitions.families());definitions.attach(catalog);
        for(var kind:List.of(SwayObservationReads.Kind.COMPLETION,SwayObservationReads.Kind.OPINION)) {
            var query=query(kind);var contract=definitions.direct(query);assertSame(contract,definitions.direct(query));assertTrue(catalog.containsIdentity(contract));
            var request=request(contract,query);var nativeRequest=contract.prepare(request,"software-direct-read");var fields=StrictJson.parse(nativeRequest.additionalFields().bytes());
            assertFalse(fields.has("action_id"));assertEquals(ACTOR,fields.get("actor_character_id").longValue());assertEquals(TARGET,fields.get("target_character_id").longValue());
            assertEquals(kind==SwayObservationReads.Kind.COMPLETION,fields.has("scheme_instance_id"));assertEquals(query.subject().instance().isPresent(),kind==SwayObservationReads.Kind.COMPLETION);
            var packet=packet(kind);var original=receipt(contract,request,packet);var plane=contract.decode(original);
            var ordinary=SwayObservationReads.decode(original,kind,new Identity("software-real-retained-origin",ACTOR,TARGET,ID,2));assertArrayEquals(plane.normalized().bytes(),ordinary.normalized().bytes());
            var result=StrictJson.parse(SwayPublicCodec.publicNormalized(new SwayObservationReads.DirectBatch(plane,Optional.empty())).bytes());
            assertEquals("7",result.get("snapshot_revision").textValue());assertFalse(result.has("action_id"));assertFalse(result.has("sway_terminal_sources_12004"));
            if(kind==SwayObservationReads.Kind.COMPLETION)assertEquals("-9007199254740993",result.get("native_success_chance_raw").textValue());
            else assertEquals(60,result.get("target_opinion_of_actor").intValue());
            assertArrayEquals(plane.normalized().bytes(),org.xar.ck3.control.contracts.projection.ProjectionJson.object(plane.normalized().bytes(),SwayNativeWire.MAX).bytes());
        }
    }
    @Test void recoveredOriginalSourceUint64ContextRemainsExactAtThePublicCompositionBoundary()throws Exception {
        var query=query(SwayObservationReads.Kind.COMPLETION);var contract=SwayObservationReads.directContract(SOURCE,query);var plane=contract.decode(receipt(contract,request(contract,query),packet(query.kind())));
        var composition=StrictJson.object();var copied=composition.putObject("original_instance").putObject("recovered_instance_observation").putObject("source_read");copied.put("capture_epoch",StrictJson.UINT64_MAX);copied.put("container_generation",new BigInteger("16786632562036001389"));
        var raw=org.xar.ck3.control.contracts.projection.ProjectionJson.object(StrictJson.canonical(composition),SwayNativeWire.MAX);var publicValue=StrictJson.parse(SwayPublicCodec.publicNormalized(new SwayObservationReads.DirectBatch(plane,Optional.of(raw))).bytes());
        assertEquals("18446744073709551615",publicValue.at("/sway_terminal_sources_12004/original_instance/recovered_instance_observation/source_read/capture_epoch").textValue());assertEquals("16786632562036001389",publicValue.at("/sway_terminal_sources_12004/original_instance/recovered_instance_observation/source_read/container_generation").textValue());
    }
    @Test void fullNativeIdentityEnvelopeAndStrictSourceFieldsRejectBeforePublicNormalization()throws Exception {
        var query=query(SwayObservationReads.Kind.COMPLETION);var contract=SwayObservationReads.directContract(SOURCE,query);var request=request(contract,query);
        for(String defect:List.of("actor","target","full-id","generation","bool-revision","float-revision","missing","alias","old-build","not-private","request-id")) {
            var packet=packet(query.kind());var body=(ObjectNode)packet.at("/result/sway_completion");
            switch(defect){case "actor"->body.put("actor_character_id",ACTOR+1);case "target"->body.put("target_character_id",TARGET+1);case "full-id"->body.put("scheme_instance_id",ID+1);case "generation"->body.put("scheme_instance_generation",0);case "bool-revision"->body.put("snapshot_revision",true);case "float-revision"->body.put("snapshot_revision",7.0);case "missing"->body.remove("terminal_cause_observed");case "alias"->body.put("completion_ready",true);case "old-build"->body.put("build_version","1.20.0.3");case "not-private"->((ObjectNode)packet.get("result")).put("private_build",false);case "request-id"->packet.put("request_id","other");default->throw new AssertionError(defect);}
            assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,request,packet)),defect);
        }
        assertThrows(IllegalArgumentException.class,()->new SwayObservationReads.DirectQuery(SwayObservationReads.Kind.COMPLETION,new SwayObservationReads.OpinionSubject(new SwayObservationReads.Actors(ACTOR,TARGET))));
    }
    @Test void originalPublicShapesHaveCanonicalUint64RoundtripAndDoNotAcceptInventedActionOrFullIdForOpinion() {
        for(var kind:List.of(SwayObservationReads.Kind.COMPLETION,SwayObservationReads.Kind.OPINION)) {
            var request=new SwayPublicCodec.DirectRequest(kind,StrictJson.UINT64_MAX,TARGET,kind==SwayObservationReads.Kind.COMPLETION?java.util.OptionalLong.of(ID):java.util.OptionalLong.empty());
            assertEquals(request,SwayPublicCodec.decodeDirect(kind,SwayPublicCodec.encodeDirectRequest(request)));
        }
        String opinion="{\"expected_revision\":%s,\"target_character_id\":50331650}";
        for(String value:List.of("null","true","1.0","9007199254740993","\"01\"","\"18446744073709551616\"","\"1\n\""))assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.OPINION,raw(opinion.formatted(value))),value);
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.OPINION,raw("{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":1}")));
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.COMPLETION,raw("{\"expected_revision\":17,\"target_character_id\":50331650}")));
    }
    private static SwayObservationReads.DirectQuery query(SwayObservationReads.Kind kind) {
        return new SwayObservationReads.DirectQuery(kind,kind==SwayObservationReads.Kind.COMPLETION?new SwayObservationReads.CompletionSubject(new NativeSubject(ACTOR,TARGET,ID,2)):new SwayObservationReads.OpinionSubject(new SwayObservationReads.Actors(ACTOR,TARGET)));
    }
    private static PlanningReadRequest request(ReadContract<?> contract,SwayObservationReads.DirectQuery query) {
        var binding=SwayNativeFormalTest.binding(73,7,53220000);return new PlanningReadRequest(binding.before(),new G2Source(binding.before().machineId(),NOW.toString(),SwayNativeWire.BUILD,SOURCE),binding.sessionId(),contract.operation(),SwayObservationReads.arguments(query),NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,ObjectNode packet) {
        var binding=SwayNativeFormalTest.binding(73,7,53220000);var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),binding.connectionGeneration(),contract.operation(),SOURCE,SOURCE,binding.authorityId(),NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));byte[] bytes=StrictJson.canonical(packet,SwayNativeWire.MAX);byte[] framed=java.nio.ByteBuffer.allocate(bytes.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack=new NativeActionPort.AckReceived("software-direct-read",true,Optional.of(new RawJson(StrictJson.canonical(packet.get("result"),SwayNativeWire.MAX))),new RawJson(bytes),framed);
        return new PlanningReadReceipt(request,contract.contractId(),"software-direct-read",guard,guard,ack);
    }
    private static ObjectNode packet(SwayObservationReads.Kind kind)throws Exception {
        byte[] original;try(var stream=SwayDirectObservationTest.class.getResourceAsStream("/sway/actual-retained-nonempty-ledger.json")){assertNotNull(stream,"mandatory historical original is never skipped");original=stream.readAllBytes();}
        assertEquals("6f1da9ee2c0e00839497a650cbcfaba527807342e85cce29d8a357344f55aad9",ActionCodec.sha256(original));var old=StrictJson.parse(original,SwayFormalCodec.MAX);
        var packet=StrictJson.object();packet.put("type","command_result");packet.put("protocol_version",1);packet.put("request_id","software-direct-read");packet.put("ok",true);
        var result=packet.putObject("result");result.put("step",kind.step());result.put("accepted",true);result.put("status","available");result.put("private_build",true);result.put("read_only",true);result.put("advertised",false);result.put("backend_id","native-headless");
        if(kind==SwayObservationReads.Kind.COMPLETION){var body=((ObjectNode)old.at("/resolved/latest_instance_observation/native_observation")).deepCopy();for(String field:List.of("exact_ck3_build","exe_sha256","queried_snapshot_id","queried_revision","queried_native_revision","backend_id","status"))body.remove(field);
            body.put("snapshot_revision",7);body.put("date_raw",53220000);body.put("actor_character_id",ACTOR);body.put("target_character_id",TARGET);body.put("scheme_instance_id",ID);body.put("scheme_instance_generation",2);body.put("native_owner_raw",ACTOR);body.put("native_success_chance_raw",new BigInteger("-9007199254740993"));result.set("sway_completion",body);
        }else{var body=result.putObject("sway_outcome_opinion");body.put("schema","xar.ck3.sway-outcome-opinion-v1");body.put("build",SwayNativeWire.BUILD);body.put("available",true);body.put("unavailable_reason","");body.put("snapshot_revision",7);body.put("date_raw",53220000);body.put("actor_character_id",ACTOR);body.put("target_character_id",TARGET);body.put("target_opinion_of_actor",60);
            body.set("scheme_sway_opinion",old.at("/resolved/material_intervention/scheme_sway_opinion").deepCopy());body.set("sway_blocker_opinion",old.at("/resolved/material_intervention/sway_blocker_opinion").deepCopy());body.put("instance_terminal_outcome_observed",false);body.put("cancel_outcome_observed",false);}
        return packet;
    }
    private static RawJson raw(String text){return new RawJson(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
}
