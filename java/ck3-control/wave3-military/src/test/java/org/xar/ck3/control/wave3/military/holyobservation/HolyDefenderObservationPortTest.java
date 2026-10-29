package org.xar.ck3.control.wave3.military.holyobservation;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.wave3.military.landcontext.LandContextProjectionCatalog;

final class HolyDefenderObservationPortTest {
    private static final ProjectionOperation OPERATION = ProjectionOperation.MILITARY_HOLY_DEFENDER_OBSERVATION;
    private static final com.fasterxml.jackson.databind.ObjectMapper SDK_JSON = new com.fasterxml.jackson.databind.ObjectMapper()
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static JsonNode parse(byte[] value, int limit) {
        StrictJson.parse(value, limit); // Validate the shared JSON boundary, then retain float kinds and signed zero for SDK comparisons.
        try { return SDK_JSON.readTree(value); }
        catch (java.io.IOException error) { throw new IllegalArgumentException("test SDK JSON failed", error); }
    }
    private static JsonNode golden() throws Exception {
        try (var input = HolyDefenderObservationPortTest.class.getResourceAsStream("/holyobservation/original-producer-golden01.json.gz")) {
            assertNotNull(input, "actual original producer capture is required; missing fixture never skips");
            byte[] compressed = input.readNBytes(65_537); assertTrue(compressed.length <= 65_536);
            try (var expanded = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                JsonNode value = parse(expanded.readNBytes(524_289), 524_288);
                assertEquals("xar.holy-defender-original-producer-golden/v1", value.path("schema").textValue());
                assertTrue(value.path("actual_original_functions").booleanValue());
                assertTrue(value.path("synthetic_world_and_callback_outcomes").booleanValue());
                assertFalse(value.path("native_compiled_packet_qualification").booleanValue());
                assertFalse(value.path("machine_id").asText().isBlank());
                assertEquals(0, value.path("game_calls").intValue());
                assertTrue(value.path("source_refs").size() >= 6); return value;
            }
        }
    }
    private static ProjectionResult call(String stage, JsonNode request) {
        ObjectNode packet = StrictJson.object().put("operation", stage); packet.set("request", request);
        return raw(json(packet));
    }
    private static byte[] json(JsonNode value) {
        try { return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(value); }
        catch (com.fasterxml.jackson.core.JsonProcessingException error) { throw new IllegalArgumentException("test JSON transport failed", error); }
    }
    private static ProjectionResult raw(byte[] payload) {
        var port = RegisteredProjection.of(new HolyDefenderObservationPort(OPERATION));
        return port.execute(new ProjectionCall(new ProjectionCall.Identity("holy-observation-real-oracle", OPERATION),
                ProjectionJson.object(payload, 131_072)));
    }
    private static JsonNode success(ProjectionResult result) {
        return parse(assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes(), 131_072);
    }
    private static ObjectNode example(String operation) throws Exception {
        for (JsonNode row : golden().path("cases")) {
            if (operation.equals(row.path("operation").textValue()) && row.path("accepted").booleanValue()) {
                return row.path("input").deepCopy();
            }
        }
        throw new IllegalArgumentException("original captured operation missing");
    }

    @TestFactory List<DynamicTest> unchangedOriginalReadersAndEveryPlannerBranchCrossTheRegisteredPort() throws Exception {
        List<DynamicTest> cases = new ArrayList<>();
        for (JsonNode row : golden().path("cases")) {
            cases.add(DynamicTest.dynamicTest(row.path("name").asText(), () -> {
                ProjectionResult actual = call(row.path("operation").textValue(), row.get("input"));
                if (!row.path("accepted").booleanValue()) { assertInstanceOf(ProjectionResult.Rejected.class, actual); }
                else {
                    JsonNode output = success(actual); JsonNode expected = row.get("expected");
                    if (row.path("diagnostic_reason_text_reimplemented").booleanValue()) {
                        output = output.deepCopy(); expected = expected.deepCopy();
                        var actualAnnotation = (ObjectNode) output.path("plan").path(HolyDefenderObservation.ANNOTATION);
                        var expectedAnnotation = (ObjectNode) expected.path("plan").path(HolyDefenderObservation.ANNOTATION);
                        assertFalse(actualAnnotation.remove("reason").asText().isBlank());
                        assertFalse(expectedAnnotation.remove("reason").asText().isBlank());
                    }
                    assertEquals(expected, output);
                    assertEquals(output, parse(json(output), 131_072));
                    if (row.path("operation").asText().equals("fold")) {
                        assertEquals(row.path("input").path("planned").path("plan").get("selected_step"), output.path("plan").get("selected_step"));
                        JsonNode directive = success(call("prepare", row.get("input")));
                        assertEquals(row.path("original_query_calls").intValue() == 1, directive.path("query_current_candidate").booleanValue());
                    }
                }
            }));
        }
        assertTrue(cases.size() >= 35); return cases;
    }

    @Test void prepareSelectsTheFirstCurrentCanonicalCandidateAndQueriesOnlyOnce() throws Exception {
        ObjectNode request = example("fold"); JsonNode result = success(call("prepare", request));
        assertTrue(result.path("query_current_candidate").booleanValue()); assertTrue(result.path("result").isNull());
        assertEquals(request.path("planned").get("revision"), result.get("expected_revision"));
        assertEquals(request.path("normalized_query").get("declaration_id"), result.get("declaration_id"));
        assertEquals(0, result.path("source_ordinal").intValue());
        ((ObjectNode) request.path("snapshot")).put("paused", false);
        result = success(call("prepare", request)); assertFalse(result.path("query_current_candidate").booleanValue());
        assertEquals("frame_not_ready", result.path("result").path("plan").path(HolyDefenderObservation.ANNOTATION).path("status").textValue());
    }

    @Test void queryFailureRetainsTheActualWarActionAndDoesNotClaimAnObservedSet() throws Exception {
        ObjectNode request = example("fold"); request.put("query_error", "original endpoint timed out"); request.putNull("normalized_query");
        JsonNode result = success(call("fold", request));
        assertEquals(request.path("planned").path("plan").get("selected_step"), result.path("plan").get("selected_step"));
        JsonNode annotation = result.path("plan").path(HolyDefenderObservation.ANNOTATION);
        assertEquals("query_failed", annotation.path("status").textValue());
        assertEquals("original endpoint timed out", annotation.path("reason").textValue());
        assertFalse(annotation.path("automatic_declaration_enabled").booleanValue()); assertFalse(annotation.has("native_joiner_set_observed"));
    }

    @Test void wrongSameFrameCandidateAndWrongExactBuildCannotBecomeAnnotations() throws Exception {
        ObjectNode request = example("fold"); ObjectNode snapshot = (ObjectNode) request.path("snapshot");
        ObjectNode other = snapshot.path("declarable_wars").get(0).deepCopy();
        other.put("target_character_id", 1).put("declaration_id", "1-0-0");
        ((com.fasterxml.jackson.databind.node.ArrayNode) snapshot.get("declarable_wars")).insert(0, other);
        assertInstanceOf(ProjectionResult.Rejected.class, call("fold", request));
        request = example("project"); ((ObjectNode) request.path("snapshot").path("diagnostics").path("hello")).put("expected_ck3_sha256", "0".repeat(64));
        assertInstanceOf(ProjectionResult.Rejected.class, call("project", request));
    }

    @Test void opaqueSdkTokensStayExactWhileOwnedFloatAndBoolIdentifiersAreRejected() throws Exception {
        ObjectNode request = example("fold"); ObjectNode packet = StrictJson.object().put("operation", "fold"); packet.set("request", request);
        String input = new String(json(packet), StandardCharsets.UTF_8);
        input = input.replace("\"zero\":0.0", "\"zero\":-0.0");
        byte[] encoded = assertInstanceOf(ProjectionResult.Succeeded.class, raw(input.getBytes(StandardCharsets.UTF_8))).result().bytes();
        String output = new String(encoded, StandardCharsets.UTF_8);
        assertTrue(output.contains("\"zero\":-0.0")); assertTrue(output.contains("18446744073709551615"));
        ObjectNode normalize = example("normalize"); ((ObjectNode) normalize.path("value")).put("joiner_count", 1.0);
        assertInstanceOf(ProjectionResult.Rejected.class, call("normalize", normalize));
        ((ObjectNode) normalize.path("value")).put("joiner_count", true);
        assertInstanceOf(ProjectionResult.Rejected.class, call("normalize", normalize));
    }

    @Test void theExistingServiceLoaderCatalogRegistersTheTypedPortWithoutAnotherHost() {
        var catalogs = java.util.ServiceLoader.load(ProjectionPortCatalog.class).stream().map(java.util.ServiceLoader.Provider::get).toList();
        var catalog = catalogs.stream().filter(value -> value instanceof LandContextProjectionCatalog).findFirst().orElseThrow();
        var registrations = catalog.registrations();
        assertEquals(2, registrations.size()); assertEquals(1, registrations.stream().filter(item -> item.operation() == OPERATION).count());
        assertEquals(ProjectionOperation.MILITARY_LAND_CONTEXT_STOCK, registrations.getFirst().operation());
        assertEquals(131_072, registrations.getLast().inputMaximumBytes());
    }
}
