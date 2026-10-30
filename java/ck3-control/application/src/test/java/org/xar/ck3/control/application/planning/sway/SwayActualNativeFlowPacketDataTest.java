package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Actual first-direction direct-handler packet DATA. No guard, Complete, writer or Game. */
final class SwayActualNativeFlowPacketDataTest {
    @Test void actualFirstFivePacketsUseProductionRawTypedParsers() throws IOException {
        var rows = originals();
        var q0 = step(rows, "01.query0");
        var s2 = step(rows, "02.start");
        var r3 = step(rows, "03.receipt");
        var p4 = step(rows, "04.post-start");
        var f5 = step(rows, "05.finish-target");
        var epoch1 = new BigInteger("18300436759549338012");
        var epoch2 = new BigInteger("15189419816273770301");

        var binding = softwareParserBinding(payload(q0, "active_scheme_sway"));
        var before = SwayNativeWire.target(response(q0), requestId(q0), binding, 0L);
        assertEquals(0L, before.target());
        assertEquals(-2L, before.binding().actor());
        assertEquals(7L, before.binding().revision().longValueExact());
        assertEquals(53220000, before.binding().date());
        assertEquals(BigInteger.valueOf(3), before.captureEpoch());
        assertEquals(epoch1, before.containerGeneration());
        assertEquals(37, before.targetOpinion());
        assertEquals(0, before.activeCount());
        assertFalse(before.matching());
        assertTrue(before.canSend());
        assertTrue(before.legal());
        assertEquals("", before.failure());
        assertTrue(before.instances().isEmpty());

        var startReq = request(s2);
        assertEquals(BigInteger.valueOf(7), startReq.get("expected_revision").bigIntegerValue());
        assertEquals("sway-flow-minus2-zero", startReq.get("action_id").textValue());
        assertEquals(before.captureEpoch(), startReq.get("expected_capture_epoch").bigIntegerValue());
        assertEquals(before.containerGeneration(), startReq.get("expected_container_generation").bigIntegerValue());
        assertEquals("37", startReq.get("expected_target_opinion_of_actor").textValue());

        var ack = SwayNativeWire.startAck(response(s2), requestId(s2), startReq.get("action_id").textValue(), before);
        assertEquals("sway-flow-minus2-zero", ack.actionId());
        assertEquals(-2L, ack.actor());
        assertEquals(0L, ack.target());
        assertEquals(BigInteger.valueOf(4), ack.preCaptureEpoch());
        assertEquals(epoch1, ack.preContainerGeneration());
        assertEquals(53220000, ack.preDateRaw());
        assertFalse(ack.applied());

        var receipt = SwayNativeWire.receipt(response(r3), requestId(r3), binding, ack.actionId(), 0L, ack.preCaptureEpoch());
        assertEquals("sway-flow-minus2-zero", receipt.actionId());
        assertEquals(BigInteger.valueOf(5), receipt.postCaptureEpoch());
        assertEquals(epoch2, receipt.postContainerGeneration());
        assertEquals(53220000, receipt.postDateRaw());
        assertEquals(0L, receipt.fullId());
        assertEquals(0, receipt.generation());

        var post = SwayNativeWire.target(response(p4), requestId(p4), binding, 0L);
        assertEquals(BigInteger.valueOf(6), post.captureEpoch());
        assertEquals(epoch2, post.containerGeneration());
        assertEquals(73, post.targetOpinion());
        assertEquals(1, post.activeCount());
        assertTrue(post.matching());
        assertTrue(post.canSend());
        assertFalse(post.legal());
        assertEquals("", post.failure());
        assertEquals(1, post.instances().size());
        var inst = post.instances().get(0);
        assertEquals(0L, inst.fullId());
        assertEquals(0, inst.generation());
        assertEquals(0L, inst.target());
        assertEquals(1, inst.progress());
        assertEquals(10, inst.progressGoal());
        assertFalse(inst.exposed());
        assertFalse(inst.frozen());
        assertTrue(post.captureEpoch().compareTo(receipt.postCaptureEpoch()) > 0);

        var current = SwayNativeWire.target(response(f5), requestId(f5), binding, 0L);
        assertEquals(BigInteger.valueOf(7), current.captureEpoch());
        assertEquals(epoch2, current.containerGeneration());
        assertEquals(73, current.targetOpinion());
        assertEquals(1, current.activeCount());
        assertTrue(current.matching());
        assertTrue(current.canSend());
        assertFalse(current.legal());
        assertEquals("", current.failure());
        assertEquals(1, current.instances().size());
        assertTrue(current.captureEpoch().compareTo(post.captureEpoch()) > 0);
    }

@Test void actualDirectPublicFieldsPreservePendingCompletionAndNamedOpinionData() throws IOException {
    var rows = originals();
    var completionReq = step(rows, "06.finish-completion");
    var opinionReq = step(rows, "07.finish-opinion");
    var stopReq = step(rows, "08.stop");
    var postStopResp = step(rows, "09.post-stop");

    // Public value codec round-trip: Completion sourced from actual request
    var completionRequestJson = request(completionReq);
    var completionDirect = new SwayPublicCodec.DirectRequest(SwayObservationReads.Kind.COMPLETION, completionRequestJson.get("expected_revision").bigIntegerValue(), NativeCharacterId.fromJson(completionRequestJson.get("target_character_id")).value(), java.util.OptionalLong.of(completionRequestJson.get("scheme_instance_id").longValue()));
    var completionEncoded = SwayPublicCodec.encodeDirectRequest(completionDirect);
    var completionDecoded = SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.COMPLETION, completionEncoded);
    assertEquals(completionDirect, completionDecoded);
    assertEquals(BigInteger.valueOf(7), completionDecoded.expectedRevision());
    assertEquals(0, completionDecoded.targetCharacterId());
    assertEquals(java.util.OptionalLong.of(0), completionDecoded.schemeInstanceId());

    // Public value codec round-trip: Opinion sourced from actual request
    var opinionRequestJson = request(opinionReq);
    var opinionDirect = new SwayPublicCodec.DirectRequest(SwayObservationReads.Kind.OPINION, opinionRequestJson.get("expected_revision").bigIntegerValue(), NativeCharacterId.fromJson(opinionRequestJson.get("target_character_id")).value(), java.util.OptionalLong.empty());
    var opinionEncoded = SwayPublicCodec.encodeDirectRequest(opinionDirect);
    var opinionDecoded = SwayPublicCodec.decodeDirect(SwayObservationReads.Kind.OPINION, opinionEncoded);
    assertEquals(opinionDirect, opinionDecoded);
    assertEquals(BigInteger.valueOf(7), opinionDecoded.expectedRevision());
    assertEquals(0, opinionDecoded.targetCharacterId());
    assertEquals(java.util.OptionalLong.empty(), opinionDecoded.schemeInstanceId());

    assertEquals(-2, completionRequestJson.get("actor_character_id").intValue());
    assertEquals(-2, opinionRequestJson.get("actor_character_id").intValue());
    assertEquals(0L, completionRequestJson.get("scheme_instance_id").longValue());
    assertFalse(opinionRequestJson.has("scheme_instance_id"));
    // Raw payload assertions for Completion (06) and post-Stop (09)
    var completionPayload = payload(completionReq, "sway_completion");
    var postStopPayload = payload(postStopResp, "sway_completion");
    assertEquals(-2, completionPayload.get("actor_character_id").intValue());
    assertEquals(0, completionPayload.get("target_character_id").intValue());
    assertEquals(0, completionPayload.get("scheme_instance_id").intValue());
    assertEquals(0, completionPayload.get("scheme_instance_generation").intValue());
    assertEquals(7, completionPayload.get("snapshot_revision").intValue());
    assertEquals(53220000, completionPayload.get("date_raw").intValue());
    assertEquals(4294967294L, completionPayload.get("native_owner_raw").longValue());
    assertEquals(0, completionPayload.get("native_status_raw").intValue());
    assertFalse(completionPayload.get("native_terminal_state_observed").booleanValue());
    assertTrue(completionPayload.get("instance_present").booleanValue());

    assertEquals(-2, postStopPayload.get("actor_character_id").intValue());
    assertEquals(0, postStopPayload.get("target_character_id").intValue());
    assertEquals(0, postStopPayload.get("scheme_instance_id").intValue());
    assertEquals(0, postStopPayload.get("scheme_instance_generation").intValue());
    assertEquals(7, postStopPayload.get("snapshot_revision").intValue());
    assertEquals(53220000, postStopPayload.get("date_raw").intValue());
    assertEquals(4294967294L, postStopPayload.get("native_owner_raw").longValue());
    assertEquals(0, postStopPayload.get("native_status_raw").intValue());
    assertFalse(postStopPayload.get("native_terminal_state_observed").booleanValue());
    assertTrue(postStopPayload.get("instance_present").booleanValue());

    // Raw payload assertions for Opinion (07)
    var opinionPayload = payload(opinionReq, "sway_outcome_opinion");
    assertEquals(-2, opinionPayload.get("actor_character_id").intValue());
    assertEquals(0, opinionPayload.get("target_character_id").intValue());
    assertEquals(7, opinionPayload.get("snapshot_revision").intValue());
    assertEquals(53220000, opinionPayload.get("date_raw").intValue());
    assertEquals(73, opinionPayload.get("target_opinion_of_actor").intValue());
    assertTrue(opinionPayload.get("scheme_sway_opinion").get("observed").booleanValue());
    assertTrue(opinionPayload.get("scheme_sway_opinion").get("present").booleanValue());
    assertEquals(12, opinionPayload.get("scheme_sway_opinion").get("value").intValue());
    assertTrue(opinionPayload.get("sway_blocker_opinion").get("observed").booleanValue());
    assertFalse(opinionPayload.get("sway_blocker_opinion").get("present").booleanValue());
    assertTrue(opinionPayload.get("sway_blocker_opinion").get("value").isNull());

    // Stop request identity and response pending semantics
    var stopRequestJson = request(stopReq);
    assertEquals(-2, stopRequestJson.get("actor_character_id").intValue());
    assertEquals(0, stopRequestJson.get("target_character_id").intValue());
    assertEquals(0, stopRequestJson.get("scheme_instance_id").intValue());
    assertEquals(0, stopRequestJson.get("scheme_instance_generation").intValue());
    assertEquals("stop-sway-flow-minus2-zero", stopRequestJson.get("action_id").textValue());
    assertEquals(BigInteger.valueOf(7), stopRequestJson.get("expected_revision").bigIntegerValue());

    var stopPayload = payload(stopReq, "sway_stop");
    assertEquals("submitted_verification_pending", stopPayload.get("status").textValue());
    assertFalse(stopPayload.get("postcondition_verified").booleanValue());
    assertFalse(stopPayload.get("terminal_observed").booleanValue());
    assertFalse(stopPayload.get("terminal_cause_observed").booleanValue());
    assertEquals("unknown", stopPayload.get("terminal_cause").textValue());

    // Cross-step consistency: TARGET05 total equals OPINION total
    var target05Payload = payload(step(rows, "05.finish-target"), "active_scheme_sway");
    assertEquals(target05Payload.get("target_opinion_of_actor").intValue(), opinionPayload.get("target_opinion_of_actor").intValue());
    assertEquals(7, target05Payload.get("snapshot_revision").intValue());
    assertEquals(53220000, target05Payload.get("date_raw").intValue());
    assertEquals(-2, target05Payload.get("actor_character_id").intValue());
    assertEquals(0, target05Payload.get("target_character_id").intValue());

    // Production reply decoder and SelectedFinish.prepare remain unexecuted due to missing real guarded receipts, not skipped as passed tests.
}

    private static JsonNode originals() throws IOException {
        try(var in=SwayActualNativeFlowPacketDataTest.class.getResourceAsStream("/sway/m6-native-flow-first-direction-originals.json")) {
            if(in==null)throw new IOException("actual original first-direction Native packets required");
            var rows=StrictJson.parse(in.readAllBytes(),262144);assertTrue(rows.isArray());assertEquals(9,rows.size());for(var row:rows)for(String role:java.util.List.of("request.json","response.json","request-id.txt"))original(row,role);return rows;
        }
    }
    private static JsonNode step(JsonNode originals,String name) {
        for(var row:originals)if(row.get("step").textValue().equals(name))return row;
        throw new AssertionError("actual Native step absent: "+name);
    }
    private static byte[] original(JsonNode row,String role) {
        var record=row.get("files").get(role);assertNotNull(record);
        byte[] raw=record.get("original_utf8").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(record.get("bytes").longValue(),raw.length);assertEquals(record.get("sha256").textValue(),ActionCodec.sha256(raw));return raw;
    }
    private static byte[] response(JsonNode row) {return original(row,"response.json");}
    private static JsonNode request(JsonNode row) {return StrictJson.parse(original(row,"request.json"),65536);}
    private static String requestId(JsonNode row) {return new String(original(row,"request-id.txt"),StandardCharsets.UTF_8);}
    private static JsonNode payload(JsonNode row,String field) {return StrictJson.parse(response(row),65536).get("result").get(field);}
    private static SwayNativeWire.Binding softwareParserBinding(JsonNode nativeTarget) {
        int actor=NativeCharacterId.fromJson(nativeTarget.get("actor_character_id")).value();
        var nativeIdentity=new JointBudgetSelector.Frame(BigInteger.valueOf(actor),nativeTarget.get("snapshot_revision").bigIntegerValue(),nativeTarget.get("date_raw").bigIntegerValue());
        var publicMetadata=new JointBudgetSelector.ProposalFrame(nativeIdentity,"software-parser-metadata-snapshot",BigInteger.ONE,"software-parser-metadata-episode");
        var identity=new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",new GameGeneration(234284,new PythonOnlyUInt64(BigInteger.ONE)),publicMetadata,1);
        return new SwayNativeWire.Binding(identity,"software-parser-metadata-session",BigInteger.ONE,"software-parser-metadata-authority",SwayNativeWire.BUILD,SwayNativeWire.EXE);
    }
}
