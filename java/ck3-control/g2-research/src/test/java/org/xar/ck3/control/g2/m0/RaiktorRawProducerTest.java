package org.xar.ck3.control.g2.m0;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.*;

/** Real raw producers and the actual G2 dispatcher; synthetic offline frames confer no Native credit. */
final class RaiktorRawProducerTest {
    private static final String ARTIFACT = "A".repeat(64);
    private static final int OPPONENT = Integer.MIN_VALUE + 1;

    @Test void actualDispatcherAndOuterWireKeepSplitPublicNativeAndHighBitCharacterIdentities() {
        ObjectNode request = campaignRequest();
        JsonNode direct = dispatch(request);
        ObjectNode certificate = (ObjectNode) direct.get("campaign_dominance_certificate");
        assertEquals(900, certificate.at("/frame/snapshot_revision").intValue());
        assertEquals(51, certificate.at("/frame/native_revision").intValue());
        assertEquals(Integer.MIN_VALUE, certificate.at("/frame/actor_character_id").intValue());
        assertEquals(OPPONENT, certificate.at("/frame/opponent_character_id").intValue());
        assertEquals(ARTIFACT, certificate.at("/evidence/source_artifact_sha256").textValue());
        assertEquals("opponent_stronger", certificate.at("/power/relation").textValue());
        var source = new G2Source("fixture-machine", "2026-10-23T17:50:00Z", "synthetic-wire-only",
                new ExactRef("synthetic-raw-input", 1, "a".repeat(64)));
        var g2 = new G2Request("raw-m0-fixture", Milestone.M0, source,
                ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(request), ProjectionJson.MAX_BYTES));
        var response = new M0Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(g2)));
        var returned = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertTrue(RaiktorRawJson.same(direct, StrictJson.parse(returned.result().bytes(), StrictJson.EXPLICIT_MAX_BYTES)));
        ObjectNode normalize = StrictJson.object().put("operation", "normalize-campaign-dominance");
        normalize.set("certificate", certificate);
        assertTrue(RaiktorRawJson.same(certificate, dispatch(normalize)));
    }

    @Test void shapeTypesOrderAndPublicNativeDriftFailAtTheActualRawProducer() {
        ObjectNode missing = campaignRequest(); missing.remove("source_artifact_sha256"); rejects(missing);
        ObjectNode renamed = campaignRequest(); renamed.set("source_sha256", renamed.remove("source_artifact_sha256")); rejects(renamed);
        ObjectNode boolId = campaignRequest(); boolId.put("war_id", true); rejects(boolId);
        ObjectNode floatId = campaignRequest(); floatId.put("war_id", 17.0); rejects(floatId);
        ObjectNode stale = campaignRequest(); ((ObjectNode) stale.get("first")).put("queried_native_revision", 900); rejects(stale);
        ObjectNode gap = campaignRequest(); ((ObjectNode) gap.get("second")).put("query_sequence", 42); rejects(gap);
        ObjectNode mismatch = campaignRequest(); ((ObjectNode) mismatch.at("/second/war_entry_assessments/assessments/0"))
                .put("target_power_total_raw", 4_000_000); rejects(mismatch);
        ObjectNode wrongReady = campaignRequest(); ((ObjectNode) wrongReady.at("/first/war_entry_assessments/readiness"))
                .put("ready", 1); rejects(wrongReady);
    }

    @Test void immutableCheckpointReplayRetainsSeparateRuntimeAndNeverGrantsSameFrameOrAction() {
        JsonNode certificate = dispatch(campaignRequest()).get("campaign_dominance_certificate");
        ObjectNode target = ((ObjectNode) certificate.get("frame")).deepCopy(); target.put("ck3_pid", 124);
        ObjectNode request = replayRequest(certificate, target);
        JsonNode replay = dispatch(request); JsonNode rebound = replay.get("campaign_dominance_certificate");
        assertEquals(124, rebound.at("/frame/ck3_pid").intValue());
        assertEquals(123, rebound.at("/evidence/source_runtime_frame/ck3_pid").intValue());
        assertFalse(rebound.at("/boundaries/same_runtime_frame_ready").booleanValue());
        assertFalse(rebound.at("/boundaries/action_ready").booleanValue());
        ObjectNode samePid = replayRequest(certificate, (ObjectNode) certificate.get("frame")); rejects(samePid);
        ObjectNode changedCheckpoint = request.deepCopy(); changedCheckpoint.put("target_checkpoint_sha256", "C".repeat(64)); rejects(changedCheckpoint);
        ObjectNode stateDrift = request.deepCopy(); ((ObjectNode) stateDrift.get("target_frame")).put("native_revision", 52); rejects(stateDrift);
        ObjectNode recursive = replayRequest(rebound, target); rejects(recursive);
    }

    @Test void persistedPowerPayloadHashAndSequenceCannotBeSilentlyRetagged() {
        ObjectNode certificate = (ObjectNode) dispatch(campaignRequest()).get("campaign_dominance_certificate");
        ObjectNode request = StrictJson.object().put("operation", "normalize-campaign-dominance");
        ObjectNode tampered = certificate.deepCopy(); ((ObjectNode) tampered.get("power")).put("actor_network_contribution_raw", 8);
        request.set("certificate", tampered); rejects(request);
        ObjectNode forgedSequence = certificate.deepCopy(); ((ObjectNode) forgedSequence.get("evidence")).put("second_query_sequence", 99);
        request.set("certificate", forgedSequence); rejects(request);
    }

    @Test void absentRawDomainsStayNullOrExplicitUnavailableWithoutInventedFrame() {
        ObjectNode project = StrictJson.object().put("operation", "project-surrender-six-domain");
        for (String field : new String[] {"snapshot", "terms", "passive_truce", "generic_war_bound_current"}) project.putNull(field);
        assertTrue(dispatch(project).isNull());
        ObjectNode bind = StrictJson.object().put("operation", "bind-surrender-aggregate-session");
        bind.putNull("snapshot"); bind.putNull("query_receipt"); bind.putNull("aggregate");
        JsonNode unavailable = dispatch(bind);
        assertEquals("unavailable", unavailable.get("status").textValue());
        assertEquals("missing_binding_fields", unavailable.at("/failure/code").textValue());
        assertTrue(unavailable.get("binding").isNull());
        ObjectNode white = StrictJson.object().put("operation", "produce-white-peace-narrow-projection").put("production_live", false);
        white.putNull("snapshot"); white.putNull("options_query"); white.putNull("terms_query");
        assertFalse(dispatch(white).get("observation_ready").booleanValue());
    }

    @Test void exactRepositoryConfigurationAndGenuineActual4UnsupportedPacketPassThroughFactory(@TempDir Path directory) throws Exception {
        var budget = resource(directory, "raiktor_exit_budget_v1.json");
        var model = resource(directory, "raiktor_exit_utility_v1.json");
        var configuration = RaiktorActualRecommendationFactory.loadConfiguration(new RaiktorActualRecommendationFactory.ConfigurationSources(
                budget, model, Optional.empty(), Optional.empty()));
        ObjectNode termsQuery = StrictJson.object().put("accepted", true).put("status", "available");
        termsQuery.set("war_termination_terms", actual4Unsupported());
        var result = RaiktorActualRecommendationFactory.produce(inputs(termsQuery), configuration);
        var unavailable = assertInstanceOf(RaiktorActualRecommendationFactory.Unavailable.class, result);
        assertEquals(java.util.List.of(RaiktorActualRecommendationFactory.Blocker.NATIVE_TERMS_UNSUPPORTED), unavailable.blockers());
        ObjectNode malformed = termsQuery.deepCopy(); ((ObjectNode) malformed.get("war_termination_terms")).remove("provenance");
        assertThrows(RaiktorActualRecommendationFactory.InputRejected.class,
                () -> RaiktorActualRecommendationFactory.produce(inputs(malformed), configuration));
        ObjectNode rejectedEnvelope = termsQuery.deepCopy(); rejectedEnvelope.put("accepted", false);
        assertThrows(RaiktorActualRecommendationFactory.InputRejected.class,
                () -> RaiktorActualRecommendationFactory.produce(inputs(rejectedEnvelope), configuration));
        ObjectNode wrongIdentity = termsQuery.deepCopy(); ((ObjectNode) wrongIdentity.get("war_termination_terms")).put("war_id", 18);
        assertThrows(RaiktorActualRecommendationFactory.InputRejected.class,
                () -> RaiktorActualRecommendationFactory.produce(inputs(wrongIdentity), configuration));
        ObjectNode actual = actualRequest(termsQuery, budget, model);
        assertEquals("NATIVE_TERMS_UNSUPPORTED", dispatch(actual).at("/blockers/0").textValue());
        assertFalse(dispatch(actual).get("action_authority").booleanValue());
        ObjectNode nativeUnsupported = actual.deepCopy(); ((ObjectNode) nativeUnsupported.get("terms_query")).put("status", "unsupported");
        for (String key : new String[] {"before_power_snapshot", "first_power_query", "between_power_snapshot", "second_power_query", "after_power_snapshot"}) nativeUnsupported.putNull(key);
        assertEquals("NATIVE_TERMS_UNSUPPORTED", dispatch(nativeUnsupported).at("/blockers/0").textValue(), "the actual unsupported native envelope needs no invented power samples");
        assertFalse(dispatch(nativeUnsupported).get("action_authority").booleanValue());
        ObjectNode drift = actual.deepCopy(); ((ObjectNode) drift.at("/configuration_sources/default_budget")).put("sha256", "D".repeat(64)); rejects(drift);
    }

    private static JsonNode dispatch(ObjectNode request) {
        return StrictJson.parse(RaiktorRawOperations.execute(RaiktorExitObservationCodec.encodeWire(request)), StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static void rejects(ObjectNode request) { assertThrows(IllegalArgumentException.class, () -> dispatch(request)); }
    private static ObjectNode snapshot() {
        ObjectNode result = StrictJson.object().put("snapshot_id", "p900").put("revision", 900).put("native_revision", 51)
                .put("date_raw", 53144520).put("paused", true).put("map_ready", true).put("episode_run_id", "fixture-episode");
        result.putObject("diagnostics").put("connection_generation", 7).put("bridge_pid", 123);
        result.putObject("played_character").put("character_id", Integer.MIN_VALUE);
        result.putArray("active_wars").addObject().put("war_id", 17).put("player_side", "attacker")
                .put("player_is_primary_war_leader", true).put("primary_opponent_character_id", OPPONENT);
        return result;
    }
    private static ObjectNode query(int sequence) {
        ObjectNode query = StrictJson.object().put("query_sequence", sequence).put("accepted", true).put("status", "available")
                .put("queried_snapshot_id", "p900").put("queried_revision", 900).put("queried_native_revision", 51);
        query.putArray("target_scopes").addObject().put("target_character_id", OPPONENT).putArray("sources").add("active_war_primary_opponent");
        ObjectNode observation = query.putObject("war_entry_assessments").put("status", "available").put("snapshot_revision", 51)
                .put("date_raw", 53144520).put("actor_character_id", Integer.MIN_VALUE);
        observation.putArray("requested_target_character_ids").add(OPPONENT);
        observation.putObject("readiness").put("ready", true).put("actual_power_ratio_ready", true);
        observation.putObject("provenance").put("fixed_point_scale", 100_000);
        observation.putArray("assessments").addObject().put("target_character_id", OPPONENT).put("effective_target_character_id", OPPONENT)
                .put("actor_power_base_raw", 1_000_000).put("actor_network_contribution_raw", 1_000_000).put("actor_power_total_raw", 2_000_000)
                .put("target_power_base_raw", 2_000_000).put("target_network_contribution_raw", 1_000_000)
                .put("target_pre_adjustment_total_raw", 3_000_000).put("target_adjustment_delta_raw", 0)
                .put("target_power_total_raw", 3_000_000).put("actual_power_ratio_raw", 150_000);
        return query;
    }
    private static ObjectNode campaignRequest() {
        ObjectNode request = StrictJson.object().put("operation", "produce-campaign-dominance").put("war_id", 17)
                .put("opponent_character_id", OPPONENT).put("source_artifact_sha256", ARTIFACT);
        request.set("before", snapshot()); request.set("between", snapshot()); request.set("after", snapshot());
        request.set("first", query(40)); request.set("second", query(41)); return request;
    }
    private static ObjectNode replayRequest(JsonNode certificate, ObjectNode target) {
        ObjectNode request = StrictJson.object().put("operation", "produce-checkpoint-replay-dominance")
                .put("source_checkpoint_sha256", ARTIFACT).put("target_checkpoint_sha256", ARTIFACT)
                .put("source_driver_state_sha256", "B".repeat(64)).put("target_driver_state_sha256", "B".repeat(64));
        request.set("source_certificate", certificate); request.set("target_frame", target); return request;
    }
    private static RaiktorActualRecommendationFactory.Inputs inputs(ObjectNode termsQuery) {
        ObjectNode value = StrictJson.object();
        return new RaiktorActualRecommendationFactory.Inputs(value, value, termsQuery, value, value, value, value, value, 17, 99, false);
    }
    private static ObjectNode actual4Unsupported() {
        ObjectNode packet = StrictJson.object().put("schema_version", 1).put("status", "unsupported").put("war_id", 17)
                .put("supported_slice", "claim_cb_claim_disposition").put("reason", "casus_belli_not_claim_cb");
        packet.putObject("casus_belli").put("database_index", 91).put("canonical_key", "raiktor_claim_cb");
        packet.putObject("readiness").put("ready", false);
        packet.putObject("provenance").put("game_version", "1.20.0.4")
                .put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                .put("native_reader", "CWar+0x270/+0x290;0x2B9ECB0")
                .put("present_claim_lifecycle", "present_only_vtable_slot_0_delete_flags_0")
                .put("claim_script_sha256", "887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4"); return packet;
    }
    private static RaiktorActualRecommendationFactory.FileRef resource(Path directory, String name) throws Exception {
        byte[] raw;
        try (InputStream input = RaiktorRawProducerTest.class.getResourceAsStream("/g2/m0/raw-producers/" + name)) {
            if (input == null) throw new IllegalStateException("required real repository policy source absent: " + name);
            raw = input.readNBytes(65537); if (raw.length == 0 || raw.length > 65536) throw new IllegalStateException("policy fixture outside bound");
        }
        Path path = directory.resolve(name); Files.write(path, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        return new RaiktorActualRecommendationFactory.FileRef(path, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
    private static ObjectNode fileRef(RaiktorActualRecommendationFactory.FileRef ref) {
        return StrictJson.object().put("path", ref.path().toString()).put("bytes", ref.bytes()).put("sha256", ref.sha256());
    }
    private static ObjectNode actualRequest(ObjectNode query, RaiktorActualRecommendationFactory.FileRef budget,
            RaiktorActualRecommendationFactory.FileRef model) {
        ObjectNode request = StrictJson.object().put("operation", "produce-actual-recommendation").put("war_id", 17)
                .put("opponent_character_id", 99).put("production_live", false);
        for (String key : new String[] {"current_snapshot", "options_query", "before_power_snapshot", "first_power_query",
                "between_power_snapshot", "second_power_query", "after_power_snapshot"}) request.set(key, StrictJson.object());
        request.set("terms_query", query); ObjectNode sources = request.putObject("configuration_sources");
        sources.set("default_budget", fileRef(budget)); sources.set("default_model", fileRef(model));
        sources.putNull("budget_override"); sources.putNull("model_override"); return request;
    }
}
