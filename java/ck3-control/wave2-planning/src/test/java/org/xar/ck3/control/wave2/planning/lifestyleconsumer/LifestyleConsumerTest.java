package org.xar.ck3.control.wave2.planning.lifestyleconsumer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistoryCodec;

final class LifestyleConsumerTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void matchesActualOriginalConsumerAcrossLife2V3AndClosedEducation() throws IOException {
        JsonNode fixture = fixture(); assertEquals(15, fixture.get("cases").size());
        for (JsonNode scenario : fixture.get("cases")) {
            assertEquals(scenario.get("expected"), JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(scenario.get("input")))), scenario.get("name").textValue());
        }
    }

    @Test void unrelatedAndOutsideScenePlansRetainTheirOriginalPriorityAndOpaqueFields() throws IOException {
        for (String name : List.of("unrelated-baseline-retained", "outside-scene-keeps-baseline")) {
            ObjectNode request = input(name);
            assertEquals(request.get("baseline_plan"), JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(request))));
        }
        ObjectNode request = input("root-query-needed");
        assertEquals("query-campaign-root-context-v1", JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(request))).get("selected_step").textValue());
    }

    @Test void identityAndCountFloatTokensAreRejectedBeforeSharedPolicyCoercion() throws IOException {
        String valid = JSON.writeValueAsString(input("life2-ready-perk"));
        for (String token : new String[] {"701.0", "true", "\"701\""}) {
            String bad = valid.replaceFirst("\"public_revision\":701", "\"public_revision\":" + token);
            assertFalse(bad.equals(valid));
            assertThrows(IllegalArgumentException.class, () -> LifestyleConsumerCodec.consume(bad.getBytes(StandardCharsets.UTF_8)));
        }
        String count = valid.replaceFirst("\"unspent_perk_points\":1", "\"unspent_perk_points\":1.0");
        assertFalse(count.equals(valid));
        assertThrows(IllegalArgumentException.class, () -> LifestyleConsumerCodec.consume(count.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void nativeErrorPrecedenceAndOpaqueDiagnosticDecimalsSurvive() throws IOException {
        ObjectNode request = input("exact-inner-error-retained"); ObjectNode query = (ObjectNode) request.get("query");
        query.putObject("native_error").put("opaque", 1.5); query.putObject("focus").put("native_error", "focus-error");
        JsonNode result = JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(request)));
        assertEquals(query.get("native_error"), result.get("lifestyle_native_error"));
        assertEquals(query, result.get("lifestyle_query"));
        assertEquals(request.get("baseline_plan").get("opaque_prior_note"), result.get("opaque_prior_note"));
    }

    @Test void v3PresenceAndNullNeverFallBackToLegacyCurrentFocusPoints() throws IOException {
        LifestyleConsumer.Request current = LifestyleConsumerCodec.decode(JSON.writeValueAsBytes(input("v3-cross-focus-nonfeudal-perk")));
        LifestyleConsumer.AvailableQuery query = (LifestyleConsumer.AvailableQuery) current.query();
        assertEquals(LifestyleMinCodec.ProgressRoute.ALL_LIFESTYLE_V3, query.policyRequest().route());
        JsonNode selected = JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(input("v3-cross-focus-nonfeudal-perk"))));
        assertEquals("thoughtful_perk", selected.get("lifestyle_action").get("target_key").textValue());
        LifestyleConsumer.Request unknown = LifestyleConsumerCodec.decode(JSON.writeValueAsBytes(input("v3-null-progress-does-not-fall-back-to-life2")));
        assertEquals(LifestyleMinCodec.ProgressRoute.ALL_LIFESTYLE_V3, ((LifestyleConsumer.AvailableQuery) unknown.query()).policyRequest().route());
        assertEquals(LifestyleMinPolicy.Status.OBSERVATION_UNAVAILABLE, LifestyleConsumer.consume(unknown).recommendation().status());
    }

    @Test void retainedEducationFactIsRequalifiedAgainstOriginalQuery() throws IOException {
        ObjectNode original = input("closed-education-fact-requalified");
        JsonNode result = JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(original)));
        assertEquals("life-advance", result.get("selected_step").textValue());
        assertFalse(result.get("lifestyle_decision").get("age_observed").booleanValue());
        assertTrue(result.get("lifestyle_decision").get("lifestyle_action_legal").isNull());
        ((ObjectNode) original.get("query").get("education_focus_query").get("source_context")).put("exe_sha256", "0".repeat(64));
        JsonNode changed = JSON.readTree(LifestyleConsumerCodec.consume(JSON.writeValueAsBytes(original)));
        assertTrue(changed.get("selected_step").isNull());
        assertEquals("lifestyle_native_query_unavailable", changed.get("phase").textValue());
    }

    @Test void applicationPortUsesSoleHistoryReducerToHoldUnknownWithoutInventingGameHalt() throws IOException {
        LifestyleConsumer.Request current = LifestyleConsumerCodec.decode(JSON.writeValueAsBytes(input("life2-ready-perk")));
        LifestyleConsumer.AvailableQuery query = (LifestyleConsumer.AvailableQuery) current.query();
        String episode = query.policyRequest().minimum().snapshot().value().episodeRunId().value();
        LifestyleHistory.Input clear = new LifestyleHistory.Input(episode, List.of());
        assertEquals(LifestyleConsumer.Route.PERK_SUBMIT, LifestyleConsumer.consumeWithHistory(current, clear).route());
        ObjectNode raw = JSON.createObjectNode().put("schema", LifestyleHistoryCodec.SCHEMA).put("episode_run_id", episode);
        ObjectNode pending = JSON.createObjectNode().put("status", "action_state_unknown").put("episode_run_id", episode)
                .put("action_request_id", "life-perk-original-unknown").put("target_key", "cutting_corners_perk").put("kind", "perk");
        raw.putArray("history").addObject().put("command", LifestyleHistory.PERK_SUBMIT).put("ok", true).put("result_json", JSON.writeValueAsString(pending));
        LifestyleHistory.Input history = LifestyleHistoryCodec.decode(JSON.writeValueAsBytes(raw));
        LifestyleConsumer.Outcome held = LifestyleConsumer.consumeWithHistory(current, history);
        assertEquals(LifestyleConsumer.Route.OBSERVATION_UNAVAILABLE, held.route());
        assertEquals(LifestyleMinPolicy.Status.ACTION_STATE_UNKNOWN, held.recommendation().status());
        assertThrows(IllegalArgumentException.class, () -> LifestyleConsumer.consumeWithHistory(current, new LifestyleHistory.Input("other-episode", List.of())));
        // This port only routes LIFE. It has no operation that stops war, saves, or advances the native clock.
        assertNotNull(held.recommendation());
    }

    @Test void strictWrapperRejectsMissingUnknownDuplicateAndMalformedUtf8() throws IOException {
        ObjectNode request = input("life2-ready-perk"); request.put("history_guard", true); byte[] unknown = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> LifestyleConsumerCodec.consume(unknown));
        request = input("life2-ready-perk"); request.remove("query"); byte[] missing = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> LifestyleConsumerCodec.consume(missing));
        String duplicated = JSON.writeValueAsString(input("life2-ready-perk")).replaceFirst("\\{", "{\"query\":null,");
        assertThrows(IllegalArgumentException.class, () -> LifestyleConsumerCodec.consume(duplicated.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LifestyleConsumerCodec.consume(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test void serializationRoundTripRetainsOpaquePlanAndOriginalNativeQueryDomain() throws IOException {
        for (JsonNode scenario : fixture().get("cases")) {
            byte[] original = JSON.writeValueAsBytes(scenario.get("input"));
            byte[] replay = JSON.writeValueAsBytes(JSON.readTree(original));
            assertEquals(JSON.readTree(LifestyleConsumerCodec.consume(original)), JSON.readTree(LifestyleConsumerCodec.consume(replay)));
        }
    }

    private static ObjectNode input(String name) throws IOException {
        for (JsonNode row : fixture().get("cases")) { if (row.get("name").textValue().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); } }
        throw new IOException("missing actual original-producer scenario " + name);
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = LifestyleConsumerTest.class.getResourceAsStream("/lifestyleconsumer/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual original-consumer golden required; not skipped"); }
            return JSON.readTree(stream);
        }
    }
}
