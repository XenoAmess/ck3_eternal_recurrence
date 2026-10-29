package org.xar.ck3.control.wave2.military.exitcomparison;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.NativeLegality;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.NotApplicable;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.ObservationRed;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.RedReason;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.Result;

final class DefenderExitObservationTest {
    @TestFactory
    Stream<DynamicTest> actualProducerVectorsAndActualStrategyConsumerHandoffs() throws IOException {
        JsonNode fixture = fixture();
        assertEquals("xar.ck3.java.exit-observation.golden.v1", fixture.get("schema").textValue());
        assertEquals(7, fixture.get("original_unit_tests").intValue());
        assertEquals(0, fixture.get("original_failures").intValue());
        assertEquals(0, fixture.get("original_errors").intValue());
        assertEquals(16, fixture.get("cases").size());
        assertEquals(6, fixture.get("handoffs").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                JsonNode actual = StrictJson.parse(DefenderExitObservationCodec.evaluate(bytes(vector.get("snapshot"))));
                assertEquals(vector.get("expected"), actual);
                assertNoExitAuthority(actual);
            }));
        }
        for (JsonNode vector : fixture.get("handoffs")) {
            String selected = vector.get("selected_step").isNull() ? null : vector.get("selected_step").textValue();
            tests.add(DynamicTest.dynamicTest("consumer-handoff:" + selected, () -> {
                Result observed = DefenderExitObservationCodec.decodeAndObserve(bytes(current()));
                JsonNode actual = StrictJson.parse(DefenderExitObservationCodec.encodeWithContinuationHandoff(observed, selected));
                assertEquals(vector.get("expected"), actual.get("continuation_handoff"));
                assertTrue(vector.get("original_selected_step_preserved").booleanValue());
                assertNoExitAuthority(actual);
                assertFalse(actual.get("continuation_handoff").get("exit_action_authorized").booleanValue());
            }));
        }
        return tests.stream();
    }

    @Test
    void wrongNativeIntegerTokensReachTheActualParserWithoutTreeNormalization() throws IOException {
        for (String field : List.of("war_id", "player_relative_war_score", "war_duration_days")) {
            String actualInteger = query(current()).get(field).bigIntegerValue().toString();
            for (String token : List.of("true", actualInteger + ".0", "\"" + actualInteger + "\"")) {
                ObjectNode input = current();
                ObjectNode row = query(input);
                byte[] raw = replaceRaw(input, row, field, token);
                Result result = DefenderExitObservationCodec.decodeAndObserve(raw);
                // A malformed WarID does not match a strict cached identity and requests a fresh observation.
                if (field.equals("war_id")) { assertFalse(result instanceof NativeLegality); }
                else {
                    assertTrue(result instanceof ObservationRed);
                    assertEquals(RedReason.SCHEMA_INVALID, ((ObservationRed) result).reason());
                }
            }
        }
    }

    @Test
    void queriedFrameIntegersCannotCompareEqualThroughBoolOrFloat() throws IOException {
        for (String field : List.of("queried_revision", "queried_native_revision", "queried_connection_generation")) {
            String actualInteger = query(current()).get(field).bigIntegerValue().toString();
            for (String token : List.of("true", actualInteger + ".0", "\"" + actualInteger + "\"", "null")) {
                ObjectNode input = current();
                Result result = DefenderExitObservationCodec.decodeAndObserve(replaceRaw(input, query(input), field, token));
                assertTrue(result instanceof ObservationRed);
                assertEquals(RedReason.FRAME_OR_CARDINALITY_MISMATCH, ((ObservationRed) result).reason());
            }
        }
    }

    @Test
    void querySequenceMustBeAnActualPositiveUint64NotAnIgnoredCacheField() throws IOException {
        for (String token : List.of("true", "1.0", "\"1\"", "null", "0", "18446744073709551616")) {
            ObjectNode input = current();
            Result result = DefenderExitObservationCodec.decodeAndObserve(replaceRaw(input, query(input), "query_sequence", token));
            assertTrue(result instanceof ObservationRed);
            assertEquals(RedReason.SCHEMA_INVALID, ((ObservationRed) result).reason());
        }
    }

    @Test
    void snapshotProjectionRejectsWrongIntegerTypesWithoutRejectingSdkExtensions() throws IOException {
        for (String field : List.of("revision", "native_revision", "date_raw")) {
            for (String token : List.of("true", "31.0", "\"31\"", "null")) {
                ObjectNode input = current();
                assertTrue(DefenderExitObservationCodec.decodeAndObserve(replaceRaw(input, input, field, token)) instanceof NotApplicable);
            }
        }
        ObjectNode extended = current();
        extended.putObject("future_container").put("unknown", "accepted by declared projection");
        ((ObjectNode) extended.get("played_character")).put("future_player_field", true);
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(extended)) instanceof NativeLegality);
    }

    @Test
    void missingOrEmptyObservationDoesNotTurnIntoCurrentLegality() throws IOException {
        ObjectNode missingSnapshotField = current();
        missingSnapshotField.remove("revision");
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(missingSnapshotField)) instanceof NotApplicable);
        ObjectNode missingQueryField = current();
        query(missingQueryField).remove("query_sequence");
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(missingQueryField)) instanceof ObservationRed);
        ObjectNode missingMaterial = current();
        ((ObjectNode) query(missingMaterial).get("options").get("surrender")).remove("terms");
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(missingMaterial)) instanceof ObservationRed);
        ObjectNode empty = current();
        empty.putArray("war_termination_options");
        JsonNode actual = StrictJson.parse(DefenderExitObservationCodec.evaluate(bytes(empty)));
        assertEquals("current_native_options_required", actual.get("status").textValue());
        assertTrue(actual.get("options").isNull());
    }

    @Test
    void nativeBooleanAndMaterialUnknownContractsCannotBeLaundered() throws IOException {
        ObjectNode notBoolean = current();
        query(notBoolean).put("player_is_primary_war_leader", 1);
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(notBoolean)) instanceof ObservationRed);
        ObjectNode inventedTerms = current();
        ((ObjectNode) query(inventedTerms).get("options").get("surrender")).put("terms_observable", true);
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(inventedTerms)) instanceof ObservationRed);
        ObjectNode inventedSource = current();
        query(inventedSource).put("source", "synthetic");
        assertTrue(DefenderExitObservationCodec.decodeAndObserve(bytes(inventedSource)) instanceof ObservationRed);
    }

    @Test
    void sourceFrameAndEpisodeDriftAreNotRebound() throws IOException {
        for (String field : List.of("queried_snapshot_id", "episode_run_id")) {
            ObjectNode input = current();
            query(input).put(field, "another-native-generation");
            Result result = DefenderExitObservationCodec.decodeAndObserve(bytes(input));
            assertTrue(result instanceof ObservationRed);
            assertEquals(RedReason.FRAME_OR_CARDINALITY_MISMATCH, ((ObservationRed) result).reason());
        }
    }

    @Test
    void typedResultIsImmutableAndEncodingRoundTripsInTheJsonDomain() throws IOException {
        Result observed = DefenderExitObservationCodec.decodeAndObserve(bytes(current()));
        assertTrue(observed instanceof NativeLegality);
        NativeLegality legality = (NativeLegality) observed;
        assertThrows(UnsupportedOperationException.class, () -> legality.options().clear());
        assertThrows(UnsupportedOperationException.class, () -> legality.legalAcceptedOutcomes().clear());
        byte[] first = DefenderExitObservationCodec.encode(observed);
        byte[] second = StrictJson.canonical(StrictJson.parse(first));
        assertEquals(new String(first, StandardCharsets.UTF_8), new String(second, StandardCharsets.UTF_8));
        assertEquals(BigInteger.valueOf(-12), legality.frame().relativeWarScore());
    }

    @Test
    void duplicateKeysInvalidUtf8OversizeAndTrailingTokensFailAtJsonBoundary() {
        for (byte[] raw : List.of("{\"paused\":true,\"paused\":false}".getBytes(StandardCharsets.UTF_8),
                "{} {}".getBytes(StandardCharsets.UTF_8), new byte[]{(byte) 0xc3, 0x28}, new byte[65_537])) {
            assertThrows(ContractViolationException.class, () -> DefenderExitObservationCodec.decodeAndObserve(raw));
        }
    }

    private static void assertNoExitAuthority(JsonNode result) {
        if (result.isNull()) { return; }
        assertTrue(result.get("recommended_outcome").isNull());
        assertTrue(result.get("action_literal").isNull());
        if (result.has("decision_readiness")) {
            assertEquals("exit_selection_blocked", result.get("decision_readiness").get("status").textValue());
            result.get("material_terms").elements().forEachRemaining(value -> assertTrue(value.isNull()));
            assertFalse(result.get("decision_readiness").get("generic_claim_cb_terms_query_applicable").booleanValue());
            assertFalse(result.get("decision_readiness").get("historical_surrender_result_reusable_as_current_terms").booleanValue());
        }
    }
    private static byte[] replaceRaw(ObjectNode request, ObjectNode owner, String field, String token) {
        owner.put(field, "$exit-observation-raw-token$");
        String raw = request.toString().replace("\"$exit-observation-raw-token$\"", token);
        return raw.getBytes(StandardCharsets.UTF_8);
    }
    private static ObjectNode query(ObjectNode snapshot) { return (ObjectNode) snapshot.get("war_termination_options").get(0); }
    private static byte[] bytes(JsonNode node) { return node.toString().getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode current() throws IOException {
        for (JsonNode vector : fixture().get("cases")) {
            if (vector.get("name").textValue().equals("current-native-options")) {
                return (ObjectNode) vector.get("snapshot").deepCopy();
            }
        }
        throw new IOException("actual current-options fixture missing");
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = DefenderExitObservationTest.class.getResourceAsStream("/exitcomparison/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed actual-producer fixture missing"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
}
