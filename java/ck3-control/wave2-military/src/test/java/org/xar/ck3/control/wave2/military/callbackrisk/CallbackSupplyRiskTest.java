package org.xar.ck3.control.wave2.military.callbackrisk;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.GZIPOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

class CallbackSupplyRiskTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void originalRiskAndActualSoldierEffectsConsumerMatchTheSharedNumericalChain() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.callbackrisk.original-producer-consumer-golden/v1", golden.path("schema").textValue());
        assertFalse(golden.path("machine_id").asText().isBlank());
        assertFalse(golden.path("observed_at_utc").asText().isBlank());
        assertEquals(8, golden.path("vectors").size());
        for (JsonNode vector : golden.path("vectors")) {
            byte[] original = JSON.writeValueAsBytes(vector.get("input"));
            var risk = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decode(original));
            var effectsInput = CallbackSoldierEffectsCodec.decodeRow(vector.get("input"), risk);
            assertEquals(risk.supplyEntry().component().ready(), effectsInput.budget().ready());
            assertEquals(risk.supplyEntry().component().soldiers(), effectsInput.budget().soldiers());
            assertEquals(risk.supplyEntry().postStockReady(), effectsInput.budget().postStockReady());
            assertEquals(risk.supplyEntry().postStockRaw(), effectsInput.budget().postStockRaw());
            var effects = CallbackSoldierEffects.project(effectsInput);
            assertJsonEquals(vector.get("expected_risk"), normalize(CallbackSupplyRiskCodec.encode(risk)), vector.path("id").textValue());
            assertJsonEquals(vector.get("expected_effects"), normalize(CallbackSoldierEffectsCodec.encode(effects)), vector.path("id").textValue());
            assertJsonEquals(vector.get("input"), JSON.readTree(original));
        }
    }

    @Test void actualOriginalServiceConsumerFieldsMatchTheJavaJoin() throws IOException {
        JsonNode golden = golden();
        JsonNode evidence = golden.path("service_consumer");
        assertEquals("GameplayBridgeService.query_army_strengths", evidence.path("actual_service_method").asText());
        assertEquals(1, evidence.path("execute_step_calls").intValue());
        assertFalse(evidence.path("registered_mcp_or_native_pipeline_executed").booleanValue());
        ObjectNode query = JSON.createObjectNode();
        query.putArray("army_strengths").add(golden.path("vectors").get(0).get("input"));
        assertJsonEquals(evidence.get("expected_fields"), JSON.readTree(CallbackSoldierEffectsCodec.projectServiceFields(JSON.writeValueAsBytes(query))));
        query.putArray("army_strengths");
        JsonNode empty = JSON.readTree(CallbackSoldierEffectsCodec.projectServiceFields(JSON.writeValueAsBytes(query)));
        assertTrue(empty.path(CallbackSupplyRiskCodec.SERVICE_FIELD).isEmpty());
        assertTrue(empty.path(CallbackSoldierEffectsCodec.SERVICE_FIELD).isEmpty());
    }

    @Test void independentZeroBudgetReachesEffectsEvenWhenStockIsUnknown() throws IOException {
        JsonNode vector = golden().path("vectors").get(4);
        var risk = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(vector.get("input"))));
        assertFalse(risk.ready());
        assertFalse(risk.supplyEntry().postStockReady());
        assertTrue(risk.supplyEntry().component().ready());
        assertEquals(0, risk.supplyEntry().component().soldiers());
        var effects = CallbackSoldierEffects.project(CallbackSoldierEffectsCodec.decodeRow(vector.get("input"), risk));
        assertTrue(effects.ready());
        assertEquals(101, effects.sequence().finalCurrentSoldiers());
    }

    @Test void preservedMissingSiegeBudgetFailsTheRealSequenceWithoutInventingZero() throws IOException {
        JsonNode vector = golden().path("vectors").get(7);
        var risk = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(vector.get("input"))));
        assertTrue(risk.supplyEntry().component().ready());
        var effects = CallbackSoldierEffects.project(CallbackSoldierEffectsCodec.decodeRow(vector.get("input"), risk));
        assertFalse(effects.ready());
        assertEquals("signed32_loss_budgets", CallbackSoldierEffectsCodec.encode(effects).path("missing_inputs").get(0).textValue());
    }

    @Test void selectionIsAnObservationAndNeverMultipliesTheConditionalBudget() throws IOException {
        JsonNode vectors = golden().path("vectors");
        var repeated = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(vectors.get(0).get("input"))));
        var empty = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(vectors.get(6).get("input"))));
        assertEquals(List.of(1, 3), repeated.input().dispatch().subjectOccurrenceIndices());
        assertEquals(List.of(), empty.input().dispatch().subjectOccurrenceIndices());
        assertEquals(repeated.supplyEntry().component(), empty.supplyEntry().component());
        assertEquals(2, empty.supplyEntry().component().soldiers());
        assertEquals(repeated.input().dispatch(), CurrentSupplyDispatchCodec.decode(
                CurrentSupplyDispatchCodec.encode(repeated.input().dispatch()), 0, 0));
    }

    @Test void runtimeFamilyValidationPreservesNullAndEmptyAndRejectsWrongTokenWidths() throws IOException {
        ObjectNode base = golden().path("vectors").get(0).get("input").deepCopy();
        ObjectNode dispatch = (ObjectNode) base.get("current_daily_supply_dispatch_inputs_v1");
        String original = JSON.writeValueAsString(base);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "2147483648")) {
            byte[] raw = original.replace("\"subject_dispatch_occurrence_count\":2", "\"subject_dispatch_occurrence_count\":" + token)
                    .getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> CallbackSupplyRiskCodec.decode(raw));
        }
        dispatch.put("future_callback", true);
        assertThrows(IllegalArgumentException.class, () -> CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(base)));
        dispatch.remove("future_callback"); dispatch.remove("selected_bucket_count_raw");
        assertThrows(IllegalArgumentException.class, () -> CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(base)));
        ObjectNode nullable = golden().path("vectors").get(0).get("input").deepCopy();
        nullable.putNull("current_daily_supply_dispatch_inputs_v1");
        assertNull(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(nullable)).dispatch());
        nullable.remove("current_daily_supply_dispatch_inputs_v1");
        assertNull(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(nullable)).dispatch());
        assertThrows(IllegalArgumentException.class, () -> CallbackSupplyRiskCodec.decode("{\"status\":null,\"status\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CallbackSupplyRiskCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> CallbackSupplyRiskCodec.decode((original + "{}").getBytes(StandardCharsets.UTF_8)));
    }

    @Test void mismatchedSubjectCannotBorrowAReadyCallbackBudget() throws IOException {
        ObjectNode base = golden().path("vectors").get(0).get("input").deepCopy();
        var risk = CallbackSupplyRisk.project(CallbackSupplyRiskCodec.decode(JSON.writeValueAsBytes(base)));
        base.put("army_id", 1);
        assertThrows(IllegalArgumentException.class, () -> CallbackSoldierEffectsCodec.decodeRow(base, risk));
        ((ObjectNode) base.get("current_daily_supply_dispatch_inputs_v1")).put("subject_army_id", 1);
        assertThrows(IllegalArgumentException.class, () -> CurrentSupplyDispatchCodec.decode(
                base.get("current_daily_supply_dispatch_inputs_v1"), 0, 0));
    }

    private static JsonNode normalize(JsonNode node) { return StrictJson.parse(StrictJson.canonical(node, CallbackSupplyRiskCodec.MAX_BYTES)); }
    @Test void losslessGzipPreservesRawTokenBytesAndBothFiniteBudgets() throws IOException {
        byte[] raw = "{\"integer\":1,\"float\":1.0,\"exponent\":1e0,\"boolean\":false,\"null\":null,\"empty\":[]}"
                .getBytes(StandardCharsets.UTF_8);
        assertArrayEquals(raw, CaptureCallbackRiskGolden.decompressGolden(CaptureCallbackRiskGolden.compressGolden(raw)));
        assertThrows(IOException.class, () -> CaptureCallbackRiskGolden.compressGolden(new byte[131_073]));
        assertThrows(IOException.class, () -> CaptureCallbackRiskGolden.decompressGolden(new byte[16_385]));
        assertThrows(IOException.class, () -> CaptureCallbackRiskGolden.compressGolden(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IOException.class, () -> CaptureCallbackRiskGolden.decompressGolden(new byte[]{0, 1, 2}));
        ByteArrayOutputStream bomb = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(bomb)) { gzip.write(new byte[131_073]); }
        assertThrows(IOException.class, () -> CaptureCallbackRiskGolden.decompressGolden(bomb.toByteArray()));
    }
    @Test void trackedFreshProducerBytesRoundTripWithoutReencoding() throws IOException {
        byte[] raw = goldenRaw();
        assertArrayEquals(raw, CaptureCallbackRiskGolden.decompressGolden(CaptureCallbackRiskGolden.compressGolden(raw)));
    }
    private static byte[] goldenRaw() throws IOException {
        try (var stream = CallbackSupplyRiskTest.class.getResourceAsStream("/callbackrisk/original-callback-risk-golden-v1.json.gz")) {
            if (stream == null) throw new IOException("tracked fresh actual producer/consumer gzip required; no fallback or skip");
            return CaptureCallbackRiskGolden.decompressGolden(stream.readNBytes(CaptureCallbackRiskGolden.MAX_GZIP_BYTES + 1));
        }
    }
    private static JsonNode golden() throws IOException { return JSON.readTree(goldenRaw()); }

    @Test void integerNodeClassesUseOneJsonDomainWithoutTokenCoercion() throws IOException {
        JsonNode integer = JSON.readTree("{\"n\":1}");
        assertJsonEquals(integer, StrictJson.parse("{\"n\":1}".getBytes(StandardCharsets.UTF_8)));
        assertJsonEquals(JSON.readTree("{\"items\":[{\"n\":1}]}"),
                StrictJson.parse("{\"items\":[{\"n\":1}]}".getBytes(StandardCharsets.UTF_8)));
        JsonNode parsedDecimal = StrictJson.parse("{\"n\":1.0}".getBytes(StandardCharsets.UTF_8));
        JsonNode parsedExponent = StrictJson.parse("{\"n\":1e0}".getBytes(StandardCharsets.UTF_8));
        assertThrows(AssertionError.class, () -> assertJsonEquals(integer, parsedDecimal));
        assertThrows(AssertionError.class, () -> assertJsonEquals(integer, parsedExponent));
        assertThrows(AssertionError.class, () -> assertJsonEquals(
                StrictJson.parse("{\"items\":[{\"n\":1}]}".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse("{\"items\":[{\"n\":1.0}]}".getBytes(StandardCharsets.UTF_8))));
        JsonNode wide = JSON.readTree("{\"n\":9223372036854775807}");
        assertJsonEquals(wide, StrictJson.parse("{\"n\":9223372036854775807}".getBytes(StandardCharsets.UTF_8)));
        for (String raw : List.of("{\"n\":1.0}", "{\"n\":1e0}", "{\"n\":true}", "{\"n\":null}", "{}")) {
            assertThrows(AssertionError.class, () -> assertJsonEquals(integer, JSON.readTree(raw)));
        }
        assertThrows(AssertionError.class, () -> assertJsonEquals(JSON.readTree("{\"n\":null}"), JSON.readTree("{}")));
        assertThrows(AssertionError.class, () -> assertJsonEquals(JSON.readTree("[1,2]"), JSON.readTree("[2,1]")));
    }

    private static void assertJsonEquals(JsonNode expected, JsonNode actual) {
        assertJsonEquals(expected, actual, "same JSON value domain");
    }

    private static void assertJsonEquals(JsonNode expected, JsonNode actual, String message) {
        assertTrue(expected.equals((left, right) -> {
            if (left.isIntegralNumber() && right.isIntegralNumber()) {
                return left.bigIntegerValue().compareTo(right.bigIntegerValue());
            }
            return left.equals(right) ? 0 : 1;
        }, actual), message);
    }
}
