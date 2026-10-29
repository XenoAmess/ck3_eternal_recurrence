package org.xar.ck3.control.g2.m0;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m0.RaiktorRawOperations.Operation;

/** Existing captured producer inputs and the actual Java composer verify the SDK output boundary. */
final class RaiktorRawResultCodecTest {
    @Test void originalAvailableLegacyProviderShapesNormalizeWithoutFileReadsOrBusinessReexecution() throws Exception {
        JsonNode args = fixture().path("immediate_cases").get(0).path("request");
        assertTrue(args.isArray()); assertEquals(4, args.size());
        JsonNode white = valid(Operation.WHITE, args.get(0));
        JsonNode session = valid(Operation.BIND, args.get(1));
        JsonNode aggregate = valid(Operation.PROJECT, session.path("aggregate"));
        valid(Operation.BUDGET, args.get(2).path("owner_budget_profile"));
        valid(Operation.MODEL, args.get(3).path("exit_utility_model"));
        valid(Operation.PROVIDE_BUDGET, args.get(2)); valid(Operation.PROVIDE_MODEL, args.get(3));
        ObjectNode pair = StrictJson.object(); pair.set("budget_provider", args.get(2)); pair.set("model_provider", args.get(3));
        valid(Operation.CONFIGURATION, pair);
        ObjectNode unknown = ((ObjectNode) white).deepCopy(); unknown.put("unexpected_readiness", true); rejects(Operation.WHITE, unknown);
        ObjectNode badContext = ((ObjectNode) white).deepCopy(); ((ObjectNode) badContext.at("/white_peace_observation/option")).put("context_constructed", 1);
        rejects(Operation.WHITE, badContext);
        ObjectNode badSource = ((ObjectNode) white).deepCopy(); ((ObjectNode) badSource.path("source_evidence")).put("game_version", "1.20.0.4");
        rejects(Operation.WHITE, badSource);
        ObjectNode badAggregate = ((ObjectNode) aggregate).deepCopy(); badAggregate.put("automatic_surrender_ready", true); rejects(Operation.PROJECT, badAggregate);
        ObjectNode readyModel = ((ObjectNode) args.get(3)).deepCopy(); ((ObjectNode) readyModel.path("downstream_readiness")).put("automatic_surrender_ready", true);
        rejects(Operation.PROVIDE_MODEL, readyModel);
        ObjectNode badBudget = ((ObjectNode) args.get(2)).deepCopy(); badBudget.put("default_source_used", false); rejects(Operation.PROVIDE_BUDGET, badBudget);
        ObjectNode malformedLimit = ((ObjectNode) args.get(2).path("owner_budget_profile")).deepCopy();
        ((ObjectNode) malformedLimit.path("pairwise_limits")).put("maximum_surrender_claims_removed", true); rejects(Operation.BUDGET, malformedLimit);
    }

    @Test void actualComposerRecommendationUsesOneStrictResultCodecAndCannotPromotePostconditions() throws Exception {
        JsonNode root = fixture(); JsonNode args = root.path("immediate_cases").get(0).path("request");
        JsonNode ranking = root.path("cases").get(0).path("request");
        ObjectNode request = StrictJson.object().put("operation", RaiktorRecommendationComposer.OPERATION);
        request.set("white_peace_projection", args.get(0)); request.set("surrender_session", args.get(1));
        request.set("budget_provider", args.get(2)); request.set("model_provider", args.get(3));
        request.set("normalized_power", ranking.path("normalized_power")); request.set("terminal_control", ranking.path("terminal_control"));
        JsonNode recommendation = StrictJson.parse(RaiktorRecommendationComposer.executeOperation(
                RaiktorExitObservationCodec.encodeWire(request)), StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(recommendation.path("production_recommendation_ready").booleanValue());
        ObjectNode result = StrictJson.object().put("schema", "xar.ck3.raiktor-actual-recommendation-result/v1")
                .put("status", "available").put("action_authority", false);
        result.set("recommendation", recommendation); result.putArray("blockers"); result.putArray("diagnostics");
        valid(Operation.ACTUAL, result);
        ObjectNode authority = result.deepCopy(); authority.put("action_authority", true); rejects(Operation.ACTUAL, authority);
        ObjectNode hashDrift = result.deepCopy();
        ((ObjectNode) hashDrift.at("/recommendation/recommendation_certificate/action_plan")).put("literal", "surrender-war-1");
        rejects(Operation.ACTUAL, hashDrift);
        ObjectNode verified = result.deepCopy(); ((ObjectNode) verified.path("recommendation")).put("postcondition_verified", true); rejects(Operation.ACTUAL, verified);
        ObjectNode inputDrift = result.deepCopy();
        ((ObjectNode) inputDrift.at("/recommendation/immediate_exit_evaluation/evaluation_certificate/strategy_identity")).put("profile_version", true);
        rejects(Operation.ACTUAL, inputDrift);
        ObjectNode unavailable = StrictJson.object().put("schema", "xar.ck3.raiktor-actual-recommendation-result/v1")
                .put("status", "unavailable").put("action_authority", false).putNull("recommendation");
        unavailable.putArray("blockers").add("NATIVE_TERMS_UNSUPPORTED"); unavailable.putArray("diagnostics").add("native_raiktor_terms_unsupported");
        valid(Operation.ACTUAL, unavailable);
        ObjectNode forgedBlocker = unavailable.deepCopy(); forgedBlocker.putArray("blockers").add("guess_zero_loss"); rejects(Operation.ACTUAL, forgedBlocker);
    }

    @Test void attachPreservesTheActualQueryReceiptAndRequiresTheOriginalRequest() throws Exception {
        JsonNode args = fixture().path("immediate_cases").get(0).path("request");
        JsonNode aggregate = args.get(1).path("aggregate");
        ObjectNode query = StrictJson.object().put("accepted", true).put("status", "available").put("private_extra_source", "retained-original");
        // Reuse exact genuine current4 unsupported shape already covered by the actual raw factory.
        ObjectNode terms = query.putObject("war_termination_terms").put("schema_version", 1).put("status", "unsupported")
                .put("war_id", 17).put("supported_slice", "claim_cb_claim_disposition").put("reason", "casus_belli_not_claim_cb");
        terms.putObject("casus_belli").put("database_index", 91).put("canonical_key", "raiktor_claim_cb");
        terms.putObject("readiness").put("ready", false);
        terms.putObject("provenance").put("game_version", "1.20.0.4")
                .put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                .put("native_reader", "CWar+0x270/+0x290;0x2B9ECB0").put("present_claim_lifecycle", "present_only_vtable_slot_0_delete_flags_0")
                .put("claim_script_sha256", "887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4");
        ObjectNode request = StrictJson.object().put("operation", Operation.ATTACH.wire());
        request.set("terms_query", query); request.putNull("snapshot"); request.putNull("passive_truce");
        JsonNode actual = StrictJson.parse(RaiktorRawOperations.execute(RaiktorExitObservationCodec.encodeWire(request)), StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals("retained-original", actual.path("private_extra_source").textValue());
        assertEquals("unsupported", actual.at("/war_termination_terms/status").textValue());
        assertEquals("unavailable", actual.at("/raiktor_surrender_aggregate_session/status").textValue());
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.ATTACH, actual));
        JsonNode validated = RaiktorRawOperations.validateResult(Operation.ATTACH, request, actual);
        assertTrue(RaiktorRawJson.same(actual, validated));
        ObjectNode newExtra = ((ObjectNode) actual).deepCopy(); newExtra.put("not_from_original_query", true);
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.ATTACH, request, newExtra));
        ObjectNode altered = ((ObjectNode) actual).deepCopy(); altered.put("private_extra_source", "forged");
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.ATTACH, request, altered));
        assertTrue(RaiktorRawOperations.validateResult(Operation.PROJECT, com.fasterxml.jackson.databind.node.NullNode.instance).isNull());
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.PROJECT, (JsonNode) null));
        assertNotNull(aggregate); // Existing full aggregate is independently validated in the first test.
    }

    @Test void powerResultOperationAndDeepCopyCannotBeRetaggedAcrossConsumers() throws Exception {
        JsonNode certificate = fixture().path("cases").get(0).path("request").path("normalized_power");
        assertEquals(2, certificate.path("schema_version").intValue());
        valid(Operation.NORMALIZE_POWER, certificate);
        ObjectNode provider = StrictJson.object().put("schema", "xar.ck3.raiktor_campaign_dominance_provider.v1")
                .put("provider", "raiktor-active-war-power-dominance-provider-v1").put("status", "available").put("certificate_available", true);
        provider.set("campaign_dominance_certificate", certificate); provider.putArray("blockers"); provider.putArray("boundaries").add("factual_power_relation_only");
        JsonNode validated = valid(Operation.CAMPAIGN, provider);
        ((ObjectNode) validated).put("status", "forged-after-validation");
        assertEquals("available", provider.path("status").textValue());
        rejects(Operation.REPLAY_POWER, provider);
        ObjectNode replayRequest = StrictJson.object().put("operation", Operation.REPLAY_POWER.wire())
                .put("source_checkpoint_sha256", "A".repeat(64)).put("target_checkpoint_sha256", "A".repeat(64))
                .put("source_driver_state_sha256", "B".repeat(64)).put("target_driver_state_sha256", "B".repeat(64));
        replayRequest.set("source_certificate", certificate);
        ObjectNode frame = ((ObjectNode) certificate.path("frame")).deepCopy(); frame.put("ck3_pid", frame.path("ck3_pid").intValue() + 1);
        replayRequest.set("target_frame", frame);
        JsonNode replay = StrictJson.parse(RaiktorRawOperations.execute(RaiktorExitObservationCodec.encodeWire(replayRequest)), StrictJson.EXPLICIT_MAX_BYTES);
        valid(Operation.REPLAY_POWER, replay); rejects(Operation.CAMPAIGN, replay);
        assertTrue(RaiktorRawJson.same(replay, RaiktorRawOperations.validateResult(Operation.REPLAY_POWER, replayRequest, replay)));
        ObjectNode otherFrame = replayRequest.deepCopy();
        ((ObjectNode) otherFrame.path("target_frame")).put("ck3_pid", frame.path("ck3_pid").intValue() + 1);
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.REPLAY_POWER, otherFrame, replay));
        ObjectNode otherCheckpoint = replayRequest.deepCopy(); otherCheckpoint.put("target_checkpoint_sha256", "C".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.REPLAY_POWER, otherCheckpoint, replay));
        ObjectNode normalizeRequest = StrictJson.object().put("operation", Operation.NORMALIZE_POWER.wire());
        normalizeRequest.set("certificate", certificate);
        assertTrue(RaiktorRawJson.same(certificate, RaiktorRawOperations.validateResult(Operation.NORMALIZE_POWER, normalizeRequest, certificate)));
        ObjectNode otherSource = normalizeRequest.deepCopy();
        ((ObjectNode) otherSource.at("/certificate/frame")).put("snapshot_revision", certificate.at("/frame/snapshot_revision").intValue() + 1);
        // Each result still has its own legal shape; the original request makes replay across frames fail.
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(Operation.NORMALIZE_POWER, otherSource, certificate));
        ObjectNode booleanReady = ((ObjectNode) replay).deepCopy(); booleanReady.put("certificate_available", 1); rejects(Operation.REPLAY_POWER, booleanReady);
        ObjectNode unknown = provider.deepCopy(); unknown.put("authority", true); rejects(Operation.CAMPAIGN, unknown);
    }

    private static JsonNode valid(Operation operation, JsonNode result) {
        JsonNode validated = RaiktorRawOperations.validateResult(operation, result);
        assertTrue(RaiktorRawJson.same(result, validated)); return validated;
    }
    private static void rejects(Operation operation, JsonNode value) {
        assertThrows(IllegalArgumentException.class, () -> RaiktorRawOperations.validateResult(operation, value));
    }
    private static JsonNode fixture() throws Exception {
        try (InputStream resource = RaiktorRawResultCodecTest.class.getResourceAsStream("/g2/m0/original-producer01.json.gz")) {
            if (resource == null) throw new IllegalStateException("actual original producer resource missing");
            try (GZIPInputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(StrictJson.EXPLICIT_MAX_BYTES + 1);
                if (raw.length > StrictJson.EXPLICIT_MAX_BYTES) throw new IllegalStateException("original producer fixture exceeds bound");
                return StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES);
            }
        }
    }
}

