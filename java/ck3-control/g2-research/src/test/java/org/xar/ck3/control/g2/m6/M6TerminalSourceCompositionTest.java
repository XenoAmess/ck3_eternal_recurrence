package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Actual historical inputs remain distinct from explicitly synthetic prospective native records. */
public final class M6TerminalSourceCompositionTest {
    @Test void twoWholeCompositionsMatchActualOriginalProducerAndHistoricalUnknownIsNotReplayed() throws Exception {
        var evidence = evidence(); JsonNode oracle = StrictJson.parse(resource("actual-original-producers.json"));
        assertEquals(2, evidence.episodes().size());
        for (int index = 0; index < 2; index++) {
            var episode = evidence.episodes().get(index); JsonNode completion = completion(episode);
            var result = M6TerminalSourceComposition.compose(episode, inputs(completion, null, null, null));
            assertEquals(oracle.get("compositions").get(index), tree(result));
            assertTrue(result.cause().isEmpty()); assertFalse(result.actionAuthorized()); assertFalse(result.requestRetried());
            assertFalse(result.ledgerCommitted());
        }
        var current = M6TerminalSourceComposition.compose(evidence.episodes().getFirst(), inputs(completion(evidence.episodes().getFirst()), null, null, null));
        assertEquals(M6TerminalSourceComposition.NativeState.UNKNOWN, current.nativeState());
        assertFalse(new M6Research().evaluateCampaign(evidence).schemeComplete());
    }

    @Test void unqueriedAndAvailableEmptyEndRemainDifferentAndNoCauseIsInvented() throws Exception {
        var episode = evidence().episodes().getFirst();
        var absent = M6TerminalSourceComposition.compose(episode, M6TerminalSourceComposition.Inputs.unqueried());
        var empty = M6TerminalSourceComposition.compose(episode, inputs(null, journal(episode, true), journal(episode, false), null));
        assertTrue(tree(absent).get("cause_input_pair").isNull());
        assertEquals(0, tree(empty).at("/cause_input_pair/termination_read/records").size());
        assertTrue(absent.cause().isEmpty()); assertTrue(empty.cause().isEmpty());
    }

    @Test void exactSyntheticDynamicParentAndEndYieldCauseWithoutMaterialOrAuthority() throws Exception {
        var episode = evidence().episodes().getFirst(); ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        execution.withArray("records").add(parent(episode)); termination.withArray("records").add(end(episode, true));
        var result = M6TerminalSourceComposition.compose(episode, inputs(null, execution, termination, null));
        assertEquals(M6TerminalSourceComposition.COMPLETE, result.cause().orElseThrow().key());
        assertEquals(new BigInteger("18446744073709551001"), tree(result).at("/causal_observation/observer_session_identity").bigIntegerValue());
        assertTrue(result.material().isEmpty()); assertEquals(M6TerminalSourceComposition.NativeState.UNKNOWN, result.nativeState());
        assertFalse(result.actionAuthorized());
    }

    @Test void nearestToastBarrierCannotBorrowOuterAuthoredCause() throws Exception {
        var episode = evidence().episodes().getFirst(); ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        execution.withArray("records").add(parent(episode)); ObjectNode end = end(episode, true);
        ((ObjectNode)end.get("cause_relation")).putArray("native_return_rvas").add(0x2d67c04).add(0x2cc93cc).add(0x3766146).add(0x2cc93cc);
        termination.withArray("records").add(end);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.compose(episode, inputs(null, execution, termination, null)));
    }

    @Test void duplicateDynamicParentAndWrongGenerationAreRejected() throws Exception {
        var episode = evidence().episodes().getFirst(); ObjectNode execution = journal(episode, true), termination = journal(episode, false);
        execution.withArray("records").add(parent(episode)).add(parent(episode));
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.compose(episode, inputs(null, execution, termination, null)));
        ObjectNode wrong = journal(episode, false); wrong.put("scheme_instance_generation", false);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.compose(episode, inputs(null, null, wrong, null)));
    }

    @Test void retainedWrapperUsesCopiedQueryStampAndKeepsUnknownCause() throws Exception {
        var episode = evidence().episodes().getFirst(); ObjectNode termination = journal(episode, false);
        termination.withArray("records").add(end(episode, false));
        var result = M6TerminalSourceComposition.compose(episode, inputs(null, null, termination, null));
        assertEquals(M6TerminalSourceComposition.EndSource.RETAINED_WRAPPER_RETURN, result.wrapperEnd().orElseThrow().source());
        assertEquals(9000, tree(result).at("/retained_end_observation/source_read/snapshot_revision").intValue());
        assertEquals(53290000, tree(result).at("/retained_end_observation/source_read/date_raw").intValue());
        assertEquals(53280000, tree(result).at("/retained_end_observation/copied_termination_record/native_invocation/post_date_raw").intValue());
        assertTrue(result.cause().isEmpty());
    }

    @Test void commonEndAndPartialCommonReturnRemainIndependentOfWrapperAndCause() throws Exception {
        var episode = evidence().episodes().getFirst(); ObjectNode termination = journal(episode, false);
        termination.set("common_native_end", common(episode, 1));
        var result = M6TerminalSourceComposition.compose(episode, inputs(null, null, termination, null));
        assertTrue(result.wrapperEnd().isEmpty()); assertTrue(result.commonEnd().isPresent()); assertTrue(result.cause().isEmpty());
        assertEquals(53290000, tree(result).at("/retained_common_end_observation/source_read/date_raw").intValue());
        termination.set("common_native_end", common(episode, 0));
        var status0 = M6TerminalSourceComposition.compose(episode, inputs(null, null, termination, null));
        assertTrue(status0.commonFamily().isPresent()); assertTrue(status0.commonEnd().isEmpty());
        ObjectNode partial = common(episode, 1); ObjectNode frame = (ObjectNode)partial.at("/records/0/returned");
        frame.put("status_observed", false); frame.putNull("status_raw_i32"); termination.set("common_native_end", partial);
        var partialResult = M6TerminalSourceComposition.compose(episode, inputs(null, null, termination, null));
        assertTrue(partialResult.commonFamily().isPresent()); assertTrue(partialResult.commonEnd().isEmpty());
    }

    @Test void commonStrictNullMissingBooleanAndSourceEdgeCannotBeRelaxed() throws Exception {
        var episode = evidence().episodes().getFirst();
        for (int mutation = 0; mutation < 3; mutation++) {
            ObjectNode termination = journal(episode, false), common = common(episode, 1); ObjectNode frame = (ObjectNode)common.at("/records/0/returned");
            if (mutation == 0) frame.put("status_raw_i32", true);
            if (mutation == 1) frame.remove("status_raw_i32");
            if (mutation == 2) ((ObjectNode)common.at("/records/0")).put("callee_rva", 1);
            termination.set("common_native_end", common);
            assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.compose(episode, inputs(null, null, termination, null)));
        }
    }

    @Test void namedOpinionNeedsSameCompletionFrameAndNeverSuppliesTerminalCause() throws Exception {
        var episode = evidence().episodes().get(1); ObjectNode completion = completion(episode), opinion = opinion(episode, completion);
        var result = M6TerminalSourceComposition.compose(episode, inputs(completion, null, null, opinion));
        assertEquals(BigInteger.valueOf(25), result.material().orElseThrow().sway().value().orElseThrow());
        assertTrue(result.cause().isEmpty()); assertTrue(tree(result).at("/named_material_observation/incremental_named_gain_observed").isNull());
        opinion.put("snapshot_revision", 2943);
        assertTrue(M6TerminalSourceComposition.compose(episode, inputs(completion, null, null, opinion)).material().isEmpty());
    }

    @Test void serviceProducerAllConsumersAndWireRoundTripKeepExactOriginalPackets() throws Exception {
        byte[] ledger = resource("closed-ledger-original.json"), auto = resource("ordinary-start-auto48-original.json");
        byte[] packet = M6SourceProducer.encodeEvidencePacket(ledger, ref("fixture:ledger", ledger), auto, ref("fixture:AUTO48", auto),
                new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
        var evidence = M6SourceProducer.fromEvidencePacket(packet, source("fixture:packet", packet));
        List<M6ServiceIntegration.EpisodeSources> sources = evidence.episodes().stream()
                .map(episode -> new M6ServiceIntegration.EpisodeSources(episode.identity().actionId(), inputs(completion(episode), null, null, null))).toList();
        byte[] payload = M6ServiceIntegration.encode(packet, ref("fixture:packet", packet), sources);
        G2Request request = new G2Request("m6-service-composition", Milestone.M6, source("fixture:service", payload), ProjectionJson.object(payload, M6SourceProducer.MAX_BYTES));
        var response = new M6Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        JsonNode result = StrictJson.parse(response.result().bytes(), M6SourceProducer.MAX_BYTES);
        assertEquals(M6ServiceIntegration.RESULT_SCHEMA, result.get("schema").textValue()); assertEquals(2, result.get("compositions").size());
        assertFalse(result.get("whole_m6_complete").booleanValue()); assertFalse(result.get("request_retried").booleanValue());
        assertEquals(response.source(), G2Wire.decodeResponse(G2Wire.encodeResponse(response)).source());
        assertArrayEquals(ledger, evidence.originalLedger().bytes());
        G2Request unbound = new G2Request("m6-wrong-outer-ref", Milestone.M6, source("fixture:wrong", ledger), request.payload());
        assertThrows(IllegalArgumentException.class, () -> new M6Research().evaluate(unbound));
        ObjectNode bad = (ObjectNode)StrictJson.parse(payload, M6SourceProducer.MAX_BYTES); bad.withArray("episode_sources").add(bad.withArray("episode_sources").get(0).deepCopy());
        byte[] wrong = bad.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        G2Request duplicate = new G2Request("m6-duplicate", Milestone.M6, source("fixture:duplicate", wrong), ProjectionJson.object(wrong, M6SourceProducer.MAX_BYTES));
        assertThrows(IllegalArgumentException.class, () -> new M6Research().evaluate(duplicate));
    }

    static ObjectNode journal(G2M6Contracts.Episode episode, boolean execution) {
        ObjectNode value = identity(episode); value.put("schema", execution ? "xar.ck3.sway-completion-execution.v1" : "xar.ck3.sway-completion-termination.v1");
        build(value); value.put("available", true); value.put("retention_gap", false); value.put("snapshot_revision", 9000); value.put("date_raw", 53290000); value.putArray("records"); return value;
    }
    static ObjectNode parent(G2M6Contracts.Episode episode) {
        ObjectNode row = identity(episode); row.put("source_branch", M6TerminalSourceComposition.COMPLETE); row.put("sequence", 21); row.put("date_raw", 53280000);
        row.putNull("stock_event"); row.putNull("phase_result"); row.put("executing_input_observed", true); row.put("exact_scope_join_ready", true);
        row.put("message_enqueue_observed", false); row.put("material_effect_observed", false); row.put("native_terminal_state_observed", false);
        ObjectNode invocation = row.putObject("native_invocation"); dynamic(invocation); invocation.put("toast_invocation_id", 33); invocation.put("branch_source_sequence", 21);
        ObjectNode scopes = invocation.putObject("copied_scopes");
        for (String name : List.of("root", "owner", "target", "scheme")) {
            ObjectNode scope = scopes.putObject(name); scope.put("type", name.equals("scheme") ? 9 : 4); scope.put("subtype", 0); scope.put("reserved", 0);
            scope.put("payload", name.equals("scheme") ? episode.identity().schemeInstanceId() : name.equals("target") ? episode.identity().targetCharacterId() : episode.identity().actorCharacterId());
        }
        return row;
    }
    static ObjectNode end(G2M6Contracts.Episode episode, boolean causal) {
        ObjectNode row = identity(episode); row.put("source_class", "authored_end_scheme_false_execute"); row.put("date_raw", 53280000);
        row.put("pre_status", 0); row.put("post_status", 1); row.put("pre_owner", episode.identity().actorCharacterId()); row.put("post_owner", 0xffff_ffffL);
        for (String flag : List.of("executing_source_observed", "post_read_succeeded", "post_instance_present", "post_exact_instance_join_ready", "post_status_observed", "native_terminal_state_observed", "native_terminal_transition_observed")) row.put(flag, true);
        row.put("post_storage_slot_reused", false); row.put("input_root_scope_kind", 9);
        ObjectNode invocation = row.putObject("native_invocation"); dynamic(invocation); invocation.put("original_invocation_id", 44); invocation.put("original_rva", 0x2d11b30);
        invocation.put("incoming_return_address_observed", true); invocation.put("caller_return_rva", 0x2d67c04);
        invocation.put("original_forwarded_once", true); invocation.put("original_returned", true); invocation.put("pre_frame_observed", true);
        invocation.put("pre_date_raw", 53280000); invocation.put("post_frame_observed", true); invocation.put("post_date_raw", 53280000);
        if (causal) {
            ObjectNode relation = identity(episode); dynamic(relation); relation.put("source_contract", "sway_child_end_causal_path_12004_v1"); relation.put("source_contract_version", 1);
            relation.put("relationship_observed", true); relation.put("branch_source_sequence", 21); relation.put("parent_toast_invocation_id", 33);
            relation.put("end_original_invocation_id", 44); relation.put("end_original_rva", 0x2d11b30); relation.put("native_returns_observed", true); relation.put("native_returns_truncated", false);
            relation.putArray("native_return_rvas").add(0x2d67c04).add(0x3766146).add(0x2cc93cc); row.set("cause_relation", relation);
        }
        return row;
    }
    static ObjectNode common(G2M6Contracts.Episode episode, int status) {
        ObjectNode value = identity(episode); value.put("schema", "xar.ck3.sway-common-native-end.v1"); value.put("source_contract", "actual_2a48877_2a4adf0_v1");
        value.put("available", true); value.put("unavailable_reason", ""); value.put("read_only", true); value.put("observer_attached", true); dynamic(value);
        value.put("after_sequence", 0); value.put("earliest_sequence", 1); value.put("latest_sequence", 1); value.put("retention_gap", false); value.put("session_records_only", true);
        ObjectNode row = value.putArray("records").addObject(); row.put("sequence", 1); dynamic(row); row.put("original_invocation_id", 50);
        row.put("callsite_rva", 0x2a48877); row.put("callee_rva", 0x2a4adf0); row.put("call_return_rva", 0x2a4887c); row.put("incoming_return_address_observed", false); row.putNull("caller_return_rva");
        row.put("incoming_dl_observed", false); row.putNull("incoming_dl_raw_u8"); row.put("original_forwarded_once", true); row.put("original_returned", true);
        row.put("return_same_scheme_full_id_observed", false); row.putNull("return_same_scheme_full_id"); row.set("entry", commonFrame(episode, 0)); row.set("returned", commonFrame(episode, status)); return value;
    }
    private static ObjectNode commonFrame(G2M6Contracts.Episode episode, int status) {
        ObjectNode value = StrictJson.object(); value.put("scheme_header_observed", true); value.put("scheme_full_id_observed", true); value.put("scheme_full_id_raw_u32", episode.identity().schemeInstanceId());
        value.put("scheme_instance_generation_u8", episode.identity().schemeInstanceGeneration()); value.put("status_observed", true); value.put("status_raw_i32", status);
        value.put("owner_observed", true); value.put("owner_character_full_id_raw_u32", episode.identity().actorCharacterId()); value.put("other_kind_observed", true); value.put("other_kind_raw_u32", 0);
        value.put("target_observed", true); value.put("target_character_full_id_raw_u32", episode.identity().targetCharacterId()); value.put("core_frame_observed", false); value.putNull("core_frame"); return value;
    }
    private static ObjectNode opinion(G2M6Contracts.Episode episode, JsonNode completion) {
        ObjectNode value = identity(episode); build(value); value.put("schema", "xar.ck3.sway-outcome-opinion-v1"); value.put("available", true);
        value.set("snapshot_revision", completion.get("snapshot_revision")); value.set("date_raw", completion.get("date_raw"));
        ObjectNode sway = value.putObject("scheme_sway_opinion"); sway.put("observed", true); sway.put("present", true); sway.put("value", 25);
        ObjectNode blocker = value.putObject("sway_blocker_opinion"); blocker.put("observed", true); blocker.put("present", false); blocker.putNull("value"); return value;
    }
    private static void dynamic(ObjectNode value) { value.put("observer_session_identity", new BigInteger("18446744073709551001")); value.put("owner_thread_id", 55); }
    private static ObjectNode identity(G2M6Contracts.Episode episode) { ObjectNode node = M6TerminalSourceComposition.identityJson(episode.identity()); node.remove("action_id"); return node; }
    private static void build(ObjectNode node) { node.put("build_version", M6SourceProducer.BUILD); node.put("executable_sha256", M6SourceProducer.EXE); }
    static M6TerminalSourceComposition.Inputs inputs(JsonNode completion, JsonNode execution, JsonNode termination, JsonNode opinion) {
        return new M6TerminalSourceComposition.Inputs(optional(completion), optional(execution), optional(termination), optional(opinion));
    }
    private static Optional<ProjectionJson> optional(JsonNode value) { return value == null ? Optional.empty() : Optional.of(M6TerminalSourceComposition.json(value)); }
    static G2M6Contracts.CampaignEvidence evidence() throws Exception { byte[] ledger = resource("closed-ledger-original.json"); return M6SourceProducer.fromClosedLedger(ledger, source("fixture:closed-ledger", ledger)); }
    static ObjectNode completion(G2M6Contracts.Episode episode) { return (ObjectNode)StrictJson.parse(episode.originalResolved().bytes()).at("/latest_instance_observation/native_observation").deepCopy(); }
    private static JsonNode tree(M6TerminalSourceComposition.Result result) { return StrictJson.parse(result.wire().bytes(), M6SourceProducer.MAX_BYTES); }
    static byte[] resource(String name) throws Exception { try (InputStream input = M6TerminalSourceCompositionTest.class.getResourceAsStream("/" + name)) { if (input == null) throw new IllegalStateException("required original fixture absent: " + name); return input.readAllBytes(); } }
    static ExactRef ref(String path, byte[] bytes) throws Exception { return new ExactRef(path, bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
    static G2Source source(String path, byte[] bytes) throws Exception { return new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-20T00:47:10Z", M6SourceProducer.BUILD, ref(path, bytes)); }
}
