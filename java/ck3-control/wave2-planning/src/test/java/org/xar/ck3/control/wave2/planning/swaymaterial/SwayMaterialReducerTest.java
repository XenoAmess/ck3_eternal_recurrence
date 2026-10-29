package org.xar.ck3.control.wave2.planning.swaymaterial;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class SwayMaterialReducerTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = SwayMaterialReducerTest.class.getResourceAsStream("/swaymaterial/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed actual two-route producer golden required; no oracle fallback or skip"); }
            byte[] raw = stream.readAllBytes();
            if (raw.length == 0 || raw.length > 98_304) { throw new IOException("bounded producer golden exceeds 96 KiB"); }
            ObjectMapper mapper = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                    .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
            return mapper.readTree(raw);
        }
    }
    private static byte[] bytes(JsonNode value) {
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator generator = new ObjectMapper().getFactory().createGenerator(output)) { token(value, generator); }
            return output.toByteArray();
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static void token(JsonNode value, JsonGenerator writer) throws IOException {
        if (value.isObject()) {
            writer.writeStartObject(); for (var field : value.properties()) { writer.writeFieldName(field.getKey()); token(field.getValue(), writer); } writer.writeEndObject();
        } else if (value.isArray()) {
            writer.writeStartArray(); for (JsonNode item : value) { token(item, writer); } writer.writeEndArray();
        } else if (value.isFloatingPointNumber()) {
            String raw = value.decimalValue().toString(); if (!raw.contains(".") && !raw.contains("E") && !raw.contains("e")) { raw += ".0"; } writer.writeNumber(raw);
        } else { writer.writeTree(value); }
    }
    private static ObjectNode firstStage() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            if (row.get("operation").textValue().equals("stage")) { return row.get("input").deepCopy(); }
        }
        throw new IllegalArgumentException("actual stage case missing");
    }

    @Test
    void actualCensusAndRegisteredMcpProducerFollowingConsumerGoldenMatches() throws IOException {
        JsonNode fixture = golden();
        assertEquals("xar.java.sway-material-producer-golden.v1", fixture.get("schema").textValue());
        assertTrue(fixture.get("original_census_compound_executed").booleanValue());
        assertEquals(1, fixture.get("original_registered_mcp_compound_tests").intValue());
        assertEquals(0, fixture.get("original_registered_mcp_skipped").intValue());
        assertEquals(0, fixture.get("game_rpc_count").intValue()); assertEquals(0, fixture.get("canonical_ledger_write_count").intValue());
        assertFalse(fixture.get("production_cutover").booleanValue());
        boolean census = false, completion = false, following = false;
        for (JsonNode row : fixture.get("cases")) {
            ObjectNode input = row.get("input").deepCopy(); byte[] before = bytes(input);
            if (row.get("operation").textValue().equals("stage")) {
                census |= input.get("source").get("kind").textValue().equals("census");
                completion |= input.get("source").get("kind").textValue().equals("completion");
                SwayMaterialReducer.StageResult result = SwayMaterialReducer.stage(before);
                assertEquals(row.get("expected_material"), StrictJson.parse(result.material().toJson()), row.get("id").textValue());
                assertEquals(row.get("expected_write_count").intValue() != 0, result.updatedResolved().isPresent(), row.get("id").textValue());
                assertEquals(row.get("first_named_gain_created").booleanValue(), result.firstNamedGainCreated(), row.get("id").textValue());
                assertFalse(result.ledgerCommitted()); assertFalse(result.submissionAuthorized());
                if (result.updatedResolved().isPresent()) {
                    ObjectNode expected = input.get("resolved").deepCopy(); expected.set("material_intervention", row.get("expected_material"));
                    if (result.firstNamedGainCreated()) { expected.set("first_named_gain_intervention", row.get("expected_first_named_gain")); }
                    assertEquals(expected, StrictJson.parse(result.updatedResolved().orElseThrow().toJson()), row.get("id").textValue());
                }
            } else {
                assertEquals("following", row.get("operation").textValue()); following = true;
                var result = SwayMaterialReducer.following(before);
                assertEquals(row.get("expected").isNull(), result.isEmpty(), row.get("id").textValue());
                if (result.isPresent()) { assertEquals(row.get("expected"), StrictJson.parse(result.orElseThrow().toJson()), row.get("id").textValue()); }
            }
            assertArrayEquals(before, bytes(input), "pure reducer must not mutate original producer inputs");
        }
        assertTrue(census && completion && following, "both actual stage consumer routes and original following consumer must execute");
    }

    @Test
    void unchangedNamedValuesNeverRearmAlreadyConsumedMaterialOrReplaceFirstGain() throws IOException {
        boolean consumedRefreshSeen = false, retainedFirstSeen = false;
        for (JsonNode row : golden().get("cases")) {
            if (!row.get("operation").textValue().equals("stage")) { continue; }
            JsonNode input = row.get("input"), previous = input.get("resolved").get("material_intervention");
            SwayMaterialReducer.StageResult result = SwayMaterialReducer.stage(bytes(input));
            if (previous != null && previous.get("next_turn_consumed").booleanValue()
                    && previous.get("scheme_sway_opinion").equals(input.get("opinion_read").get("scheme_sway_opinion"))
                    && previous.get("sway_blocker_opinion").equals(input.get("opinion_read").get("sway_blocker_opinion"))
                    && previous.get("target_opinion_of_actor").equals(input.get("opinion_read").get("target_opinion_of_actor"))
                    && row.get("expected_material").get("next_turn_consumed").booleanValue()) {
                consumedRefreshSeen = true; assertTrue(StrictJson.parse(result.material().toJson()).get("next_turn_consumed").booleanValue());
            }
            if (input.get("resolved").has("first_named_gain_intervention") && result.updatedResolved().isPresent()) {
                retainedFirstSeen = true;
                assertEquals(input.get("resolved").get("first_named_gain_intervention"),
                        StrictJson.parse(result.updatedResolved().orElseThrow().toJson()).get("first_named_gain_intervention"));
            }
        }
        assertTrue(consumedRefreshSeen && retainedFirstSeen, "real cold refresh and first-gain retention cases required");
    }

    @Test
    void observedAbsentNamedModifierMeansZeroWhileUnobservedIsRejected() throws IOException {
        ObjectNode input = firstStage();
        ObjectNode sway = (ObjectNode) input.get("opinion_read").get("scheme_sway_opinion");
        sway.put("observed", true); sway.put("present", false); sway.putNull("value");
        assertFalse(StrictJson.parse(SwayMaterialReducer.stage(bytes(input)).material().toJson()).get("dedicated_benefit_observed").booleanValue());
        sway.put("observed", false);
        assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(bytes(input)));
        sway.remove("observed");
        assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(bytes(input)));
    }

    @Test
    void realFloatTokenBooleanAndStringDoNotBecomeNamedIntegerMeasurements() throws IOException {
        for (JsonNode invalid : List.of(new ObjectMapper().getNodeFactory().numberNode(25.0),
                new ObjectMapper().getNodeFactory().booleanNode(true), new ObjectMapper().getNodeFactory().textNode("25"))) {
            ObjectNode input = firstStage(); ObjectNode sway = (ObjectNode) input.get("opinion_read").get("scheme_sway_opinion");
            sway.put("observed", true); sway.put("present", true); sway.set("value", invalid);
            byte[] raw = bytes(input);
            if (invalid.isFloatingPointNumber()) { assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"value\":25.0")); }
            assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(raw));
        }
    }

    @Test
    void followingConsumesOnceForSameActorWhenEitherOriginalProgressAxisAdvances() throws IOException {
        ObjectNode stage = firstStage(); JsonNode material = StrictJson.parse(SwayMaterialReducer.stage(bytes(stage)).material().toJson());
        ObjectNode input = StrictJson.object(); input.set("material", material); input.set("actor_character_id", material.get("actor_character_id"));
        BigInteger revision = material.get("source_native_revision").bigIntegerValue(), date = material.get("source_date_raw").bigIntegerValue();
        input.put("native_revision", revision); input.put("date_raw", date);
        assertTrue(SwayMaterialReducer.following(bytes(input)).isEmpty());
        input.put("native_revision", revision.add(BigInteger.ONE)); input.put("date_raw", date.subtract(BigInteger.ONE));
        var advanced = SwayMaterialReducer.following(bytes(input)); assertTrue(advanced.isPresent());
        input.set("material", StrictJson.parse(advanced.orElseThrow().toJson()));
        input.put("native_revision", revision.add(BigInteger.TEN)); input.put("date_raw", date.add(BigInteger.TEN));
        assertTrue(SwayMaterialReducer.following(bytes(input)).isEmpty());
        input.set("material", material); input.put("native_revision", revision.subtract(BigInteger.ONE)); input.put("date_raw", date.add(BigInteger.ONE));
        assertTrue(SwayMaterialReducer.following(bytes(input)).isPresent());
        input.put("actor_character_id", 999);
        assertTrue(SwayMaterialReducer.following(bytes(input)).isEmpty());
    }

    @Test
    void firstGainExplicitNullIsNotOverwrittenAndArbitraryIntegerPrecisionSurvives() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            if (row.get("operation").textValue().equals("stage") && row.get("first_named_gain_created").booleanValue()) {
                ObjectNode input = row.get("input").deepCopy(); ((ObjectNode) input.get("resolved")).putNull("first_named_gain_intervention");
                SwayMaterialReducer.StageResult result = SwayMaterialReducer.stage(bytes(input));
                assertFalse(result.firstNamedGainCreated());
                assertTrue(StrictJson.parse(result.updatedResolved().orElseThrow().toJson()).get("first_named_gain_intervention").isNull());
                ObjectNode sway = (ObjectNode) input.get("opinion_read").get("scheme_sway_opinion");
                BigInteger huge = new BigInteger("184467440737095516160000001"); sway.put("present", true); sway.put("value", huge);
                assertEquals(huge, StrictJson.parse(SwayMaterialReducer.stage(bytes(input)).material().toJson()).get("scheme_sway_opinion").get("value").bigIntegerValue());
                return;
            }
        }
        throw new IllegalStateException("actual first named gain transition missing from golden");
    }

    @Test
    void nativeCompletionProjectionCannotBeReplacedByCallerTruthFlags() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            if (row.get("operation").textValue().equals("stage") && row.get("input").get("source").get("kind").textValue().equals("completion")) {
                ObjectNode input = row.get("input").deepCopy(); ObjectNode completion = (ObjectNode) input.get("resolved").get("latest_instance_observation");
                completion.put("tracked_instance_active", true); ((ObjectNode) completion.get("native_observation")).put("owner_matches_actor", false);
                assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(bytes(input)));
                return;
            }
        }
        throw new IllegalStateException("actual completion consumer route missing");
    }

    @Test
    void strictEnvelopeAndImmutableOutputPreserveActualBoundary() throws IOException {
        ObjectNode input = firstStage(); SwayMaterialReducer.StageResult result = SwayMaterialReducer.stage(bytes(input));
        byte[] original = result.material().toJson(), exposed = result.material().toJson(); exposed[0] = 0;
        assertArrayEquals(original, result.material().toJson());
        input.put("admitted", true); assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(bytes(input)));
        for (String bad : List.of("{\"resolved\":{},\"resolved\":{}}", "{} {}", "null", "[]")) {
            assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(bad.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> SwayMaterialReducer.stage(new byte[] {(byte) 0xc3, 0x28}));
    }
}
