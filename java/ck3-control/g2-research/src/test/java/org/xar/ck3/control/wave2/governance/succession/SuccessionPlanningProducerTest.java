package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;

/** Requires actual captured original Service/root/Driver producer output; absent resources are RED. */
class SuccessionPlanningProducerTest {
    private static JsonNode golden() throws IOException {
        try (var input = SuccessionPlanningProducerTest.class.getResourceAsStream("/g2/m3/original-producer-golden.json")) {
            assertNotNull(input, "actual original M3 producer capture is required");
            byte[] raw = input.readNBytes(786_433);
            assertTrue(raw.length > 0 && raw.length <= 786_432);
            JsonNode result = com.fasterxml.jackson.databind.json.JsonMapper.builder()
                    .enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                            com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS,
                            com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
                    .disable(com.fasterxml.jackson.databind.cfg.JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES)
                    .build().readTree(raw);
            assertEquals("xar.g2.m3.original-producer-golden/v1", result.path("schema").textValue());
            assertTrue(result.path("source_refs_unchanged").booleanValue());
            assertTrue(result.path("synthetic_fixture").booleanValue());
            assertFalse(result.path("machine_id").asText().isEmpty());
            return result;
        }
    }
    private static byte[] wire(JsonNode value) { return SuccessionCodec.encode(value); }
    private static JsonNode run(JsonNode value) { return SuccessionCodec.parse(SuccessionPlanningProducer.apply(wire(value))); }

    @Test void actualServiceFullBundlesAndOriginalDriverProducerMatchEveryCompleteField() throws IOException {
        JsonNode data = golden();
        assertTrue(data.path("producer_cases").size() >= 6);
        for (JsonNode row : data.path("producer_cases")) {
            assertEquals(row.get("expected"), run(row.get("request")), row.path("name").asText());
        }
        assertTrue(data.path("service_observations").size() >= 4,
                "real Service/root-materializer/full-bundle chain must have executed");
        for (JsonNode observation : data.path("service_observations")) {
            assertTrue(observation.path("same_frame_replan_reused").booleanValue());
            assertEquals(0, observation.path("submissions").intValue());
        }
    }

    @Test void fullRetainedProducerOutputSurvivesAllOriginalReaderSerializationDomains() throws IOException {
        for (JsonNode row : golden().path("producer_cases")) {
            byte[] actual = SuccessionPlanningProducer.apply(wire(row.get("request")));
            if ("retain".equals(row.path("request").path("operation").textValue())) {
                JsonNode expected = row.get("expected");
                assertEquals(expected, SuccessionCodec.parse(SuccessionCodec.normalize(actual)));
                assertEquals(expected, SuccessionCodec.parse(SuccessionCodec.encodeExpectation(SuccessionCodec.decodeExpectation(actual))));
                assertTrue(expected.path("title_expectations").size() > 0);
            }
        }
    }

    @Test void actualOriginalStaleFrameAndTransitionRejectionsRemainRejected() throws IOException {
        JsonNode rejected = golden().path("producer_rejected");
        assertTrue(rejected.size() >= 6);
        for (JsonNode row : rejected) {
            assertThrows(IllegalArgumentException.class, () -> run(row.get("request")), row.path("name").asText());
            assertFalse(row.path("error_type").asText().isEmpty());
        }
    }

    @Test void publicRawTokensCannotCoerceEquivalentWrongTypesOrDiscardMissingNullSemantics() throws IOException {
        ObjectNode seed = (ObjectNode) golden().path("producer_cases").get(0).get("request");
        List<Consumer<ObjectNode>> changes = List.of(
                row -> row.put("expected_revision", true),
                row -> row.put("expected_revision", row.get("expected_revision").doubleValue()),
                row -> row.put("expected_revision", row.get("expected_revision").asText()),
                row -> row.put("expected_revision", new BigInteger("18446744073709551616")),
                row -> row.remove("expected_revision"),
                row -> row.putNull("snapshot"),
                row -> ((ObjectNode) row.get("snapshot")).put("episode_character_id", true),
                row -> ((ObjectNode) row.get("snapshot")).put("episode_character_id", row.get("snapshot").get("episode_character_id").doubleValue()),
                row -> ((ObjectNode) row.get("snapshot")).putNull("episode_run_id"),
                row -> ((ObjectNode) row.get("snapshot")).put("paused", 1),
                row -> ((ObjectNode) row.get("snapshot")).put("revision", true),
                row -> ((ObjectNode) row.get("snapshot")).put("native_revision", row.get("snapshot").get("native_revision").doubleValue()),
                row -> row.putNull("turn_bundle"),
                row -> row.put("unreviewed_authority", true));
        for (Consumer<ObjectNode> change : changes) {
            ObjectNode request = seed.deepCopy();
            change.accept(request);
            assertThrows(IllegalArgumentException.class, () -> run(request));
        }
    }
}
