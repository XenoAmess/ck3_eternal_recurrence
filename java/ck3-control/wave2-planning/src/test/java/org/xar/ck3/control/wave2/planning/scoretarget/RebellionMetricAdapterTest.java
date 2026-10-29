package org.xar.ck3.control.wave2.planning.scoretarget;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

final class RebellionMetricAdapterTest {

    @Test void javaResultContinuesTheCompleteOriginalProjectMetricsConsumer() throws Exception {
        List<String> requests = corpus().stream().skip(1).map(row -> row.path("input_json").textValue()).toList();
        JsonNode result = RebellionConsumerGoldenExporter.verifyOriginalConsumers(requests);
        assertEquals("PASS", result.path("status").textValue());
        assertTrue(result.path("complete_consumer_comparisons").intValue() > 0);
    }

    @TestFactory
    Stream<DynamicTest> actualOriginalProjectMetricsConsumerStage() throws IOException {
        List<JsonNode> corpus = corpus(); JsonNode header = corpus.getFirst();
        assertEquals("g2.scoretarget-rebellion-consumer-golden/v1", header.path("schema").textValue());
        assertEquals("actual_original_project_metrics_and_observation_call_stack_825_842", header.path("capture").textValue());
        assertEquals("ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e",
                header.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py").textValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertFalse(header.path("production_consumer_switched").booleanValue());
        StrictJson.utc(StrictJson.text(header.get("observed_at_utc")));
        StrictJson.text(header.get("machine_id"));
        assertEquals(corpus.size() - 1, header.path("vector_count").intValue());
        return corpus.stream().skip(1).map(row -> DynamicTest.dynamicTest(row.path("case").textValue(), () -> {
            JsonNode input = row.get("input_json"); assertTrue(input != null && input.isTextual());
            byte[] raw = bytes(input.textValue()); assertTrue(raw.length > 0 && raw.length <= StrictJson.INPUT_MAX_BYTES);
            if ("invalid_contract".equals(row.path("expected_kind").textValue())) {
                assertEquals("qualified-python-integer-digit-limit", row.path("case").textValue());
                assertThrows(ProjectionDomainRejection.class, () -> RebellionMetricCodec.evaluate(raw));
                ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                        org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.registeredResult(
                                new SavedScoreProjectionPortCatalog().registrations().stream()
                                        .filter(port -> port.operation() == org.xar.ck3.control.contracts.projection.ProjectionOperation.SCORE_REBELLION_PROJECT)
                                        .findFirst().orElseThrow(), raw));
                assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
            } else {
                byte[] expected = StrictJson.canonical(row.get("expected"));
                assertArrayEquals(expected, RebellionMetricCodec.evaluate(raw));
                ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class,
                        org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.registeredResult(
                                new SavedScoreProjectionPortCatalog().registrations().stream()
                                        .filter(port -> port.operation() == org.xar.ck3.control.contracts.projection.ProjectionOperation.SCORE_REBELLION_PROJECT)
                                        .findFirst().orElseThrow(), raw));
                assertArrayEquals(expected, succeeded.result().bytes());
            }
        }));
    }

    @Test
    void noFallbackForMalformedListAndNoGreenBooleanSubstituteForCounters() {
        JsonNode noFallback = evaluate("{\"landed_data.wars\":\"9 9\"}", "{}", "0", "false", "[[\"wars\"]]");
        assertEquals("INVALID_OR_DUPLICATE_WAR_IDS", noFallback.path("player_war_scope").path("reason").textValue());
        assertTrue(noFallback.path("metric_update").isNull());
        for (String wrong : List.of("false", "0.0", "\"0\"", "null", "-1")) {
            assertThrows(ContractViolationException.class, () -> evaluate("{}", "{}", wrong, "false", "[[\"wars\"]]"));
        }
        for (String wrong : List.of("0", "0.0", "\"false\"", "null")) {
            assertThrows(ContractViolationException.class, () -> evaluate("{}", "{}", "0", wrong, "[[\"wars\"]]"));
        }
    }

    @Test
    void preservedFloatSdkExtensionDoesNotBlockKnownListedWar() {
        JsonNode result = evaluate("{\"landed_data.wars\":\"9\",\"sdk_extension\":1.0}",
                "{\"9\":{\"casus_belli.defender\":\"7\",\"sdk_extension\":1.0}}", "0", "false", "[]");
        assertEquals("rebel_share", result.path("metric_update").path("metric").textValue());
        assertEquals("0", result.path("metric_update").path("observation").path("value").textValue());
    }

    @Test
    void emptyCompleteRosterAndUnknownRosterHaveDifferentScopes() {
        JsonNode complete = evaluate("{}", "{}", "0", "false", "[[\"wars\"]]");
        assertEquals("independent_complete_world_war_roster", complete.path("player_war_scope").path("method").textValue());
        assertFalse(complete.path("player_war_scope").has("listed_war_ids"));
        assertEquals("rebel_share", complete.path("metric_update").path("metric").textValue());
        JsonNode missing = evaluate("{}", "{}", "0", "false", "[]");
        assertEquals("MISSING_LIST", missing.path("player_war_scope").path("reason").textValue());
        assertTrue(missing.path("metric_update").isNull());
    }

    private static JsonNode evaluate(String fields, String wars, String count, String layout, String containers) {
        String raw = "{\"player\":{\"actor\":3,\"character_fields\":" + fields + ",\"wars\":" + wars
                + "},\"unknown_key_fields\":" + count + ",\"war_containers\":" + containers
                + ",\"war_layout_unknown\":" + layout + ",\"source_ref\":\"synthetic\"}";
        return StrictJson.parse(RebellionMetricCodec.evaluate(bytes(raw)));
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static List<JsonNode> corpus() throws IOException {
        try (InputStream stream = RebellionMetricAdapterTest.class.getResourceAsStream("/scoretarget/rebellion_consumer_python_v1.jsonl")) {
            if (stream == null) { throw new AssertionError("actual consumer golden missing; no skip"); }
            byte[] raw = stream.readNBytes(24 * 1024 + 1); assertTrue(raw.length > 0 && raw.length <= 24 * 1024);
            String text = new String(raw, StandardCharsets.UTF_8);
            String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]);
            List<JsonNode> rows = new ArrayList<>();
            for (int index = 0; index < lines.length - 1; index++) { rows.add(StrictJson.parse(bytes(lines[index]))); }
            return List.copyOf(rows);
        }
    }
}
