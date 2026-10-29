package org.xar.ck3.control.planning.swayreuse;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.core.JsonGenerator;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class ReusedSwayOpportunityTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ReusedSwayOpportunityTest.class.getResourceAsStream("/swayreuse/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed real producer golden is required; no runtime Python fallback"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }

    private static ObjectNode request(JsonNode sample, String operation) {
        ObjectNode result = StrictJson.object();
        result.set("resolved", sample.get("resolved"));
        if (operation.equals("gap")) {
            result.set("actor_character_id", sample.get("actor_character_id"));
            result.set("date_raw", sample.get("date_raw"));
        } else {
            assertEquals("fresh", operation);
            result.set("readback", sample.get("readback"));
        }
        return result;
    }

    private static Optional<ReusedSwayOpportunity.ObservationGap> invoke(ObjectNode sample, String operation) {
        try {
            // Preserve deliberately malformed float tokens in negative vectors.
            // The production codec, rather than the fixture serializer, must reject them.
            byte[] raw = fixtureBytes(request(sample, operation));
            return operation.equals("gap") ? ReusedSwayOpportunity.decodeObservationGap(raw)
                    : ReusedSwayOpportunity.decodeFreshEmptySlot(raw);
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }

    private static byte[] fixtureBytes(JsonNode value) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (JsonGenerator generator = new ObjectMapper().getFactory().createGenerator(output)) { fixtureToken(value, generator); }
        return output.toByteArray();
    }

    private static void fixtureToken(JsonNode value, JsonGenerator generator) throws IOException {
        if (value.isObject()) {
            generator.writeStartObject();
            for (var field : value.properties()) { generator.writeFieldName(field.getKey()); fixtureToken(field.getValue(), generator); }
            generator.writeEndObject();
        } else if (value.isArray()) {
            generator.writeStartArray(); for (JsonNode item : value) { fixtureToken(item, generator); } generator.writeEndArray();
        } else if (value.isFloatingPointNumber()) {
            String token = value.decimalValue().toString();
            if (!token.contains(".") && !token.contains("E") && !token.contains("e")) { token += ".0"; }
            generator.writeNumber(token);
        } else { generator.writeTree(value); }
    }

    @Test
    void actualLegacyProducerVectorsMatchAndRoundTripWithoutOracle() throws IOException {
        JsonNode vectors = golden();
        assertEquals("xar.java.sway-reuse-producer-golden.v1", vectors.get("schema").textValue());
        assertTrue(vectors.get("full_ledger_gap_equal_to_projection").booleanValue());
        assertFalse(vectors.get("production_consumer_cutover").booleanValue());
        assertEquals(0, vectors.get("game_rpc_count").intValue());
        assertEquals(0, vectors.get("ledger_write_count").intValue());
        assertEquals(32, vectors.get("cases").size());
        for (JsonNode vector : vectors.get("cases")) {
            ObjectNode sample = vectors.get("base").deepCopy();
            mutate(sample, vector.get("mutations"));
            String operation = vector.get("operation").textValue();
            if (vector.get("id").textValue().equals("latest-generation-float")) {
                assertTrue(new String(fixtureBytes(request(sample, operation)), StandardCharsets.UTF_8)
                        .contains("\"scheme_instance_generation\":5.0"));
            }
            byte[] actual = ReusedSwayOpportunity.encode(invoke(sample, operation));
            assertEquals(vector.get("expected"), StrictJson.parse(actual), vector.get("id").textValue());
            assertArrayEquals(actual, ReusedSwayOpportunity.encode(ReusedSwayOpportunity.decodeResult(actual)),
                    vector.get("id").textValue());
        }
    }

    private static void mutate(ObjectNode sample, JsonNode mutations) {
        for (JsonNode change : mutations) {
            JsonNode path = change.get("path");
            ObjectNode parent = sample;
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode nested = parent.get(path.get(index).textValue());
                if (!(nested instanceof ObjectNode object)) { throw new IllegalArgumentException("golden path is not an object"); }
                parent = object;
            }
            String key = path.get(path.size() - 1).textValue();
            if (change.has("remove") && change.get("remove").isBoolean() && change.get("remove").booleanValue()) {
                parent.remove(key);
            } else { parent.set(key, change.get("value")); }
        }
    }

    @Test
    void freshGapKeepsTerminalAndGainUnknownAndCannotSubmit() throws IOException {
        ObjectNode sample = golden().get("base").deepCopy();
        ReusedSwayOpportunity.ObservationGap gap = invoke(sample, "fresh").orElseThrow();
        assertEquals(ReusedSwayOpportunity.TerminalCause.UNKNOWN, gap.terminalCause());
        assertTrue(gap.storageSlotReused());
        assertFalse(gap.instanceTerminalOutcomeObserved());
        assertFalse(gap.submissionAuthorized());
        assertFalse(gap.previousGainCredited());
        // Input observation and ledger are immutable from the pure leaf's view.
        byte[] before = StrictJson.canonical(sample);
        invoke(sample, "gap");
        invoke(sample, "fresh");
        assertArrayEquals(before, StrictJson.canonical(sample));
    }

    @Test
    void outerEnvelopeRejectsUnknownMissingDuplicateAndMalformedJson() throws IOException {
        ObjectNode request = request(golden().get("base"), "gap");
        request.put("foreign_field", true);
        assertThrows(ContractViolationException.class,
                () -> ReusedSwayOpportunity.decodeObservationGap(StrictJson.canonical(request)));
        request.remove("foreign_field");
        request.remove("actor_character_id");
        assertThrows(ContractViolationException.class,
                () -> ReusedSwayOpportunity.decodeObservationGap(StrictJson.canonical(request)));
        for (String invalid : new String[] {"{\"resolved\":{},\"resolved\":{}}", "{} {}", "[]", "null"}) {
            assertThrows(ContractViolationException.class,
                    () -> ReusedSwayOpportunity.decodeObservationGap(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class,
                () -> ReusedSwayOpportunity.decodeObservationGap(new byte[] {(byte) 0xc3, 0x28}));
    }

    @Test
    void retainedContainersAllowUnrelatedFieldsWithoutForgingSource() throws IOException {
        ObjectNode sample = golden().get("base").deepCopy();
        Optional<ReusedSwayOpportunity.ObservationGap> before = invoke(sample, "gap");
        ((ObjectNode) sample.get("resolved")).put("unrelated_legacy_extension", "retained");
        ((ObjectNode) sample.get("resolved").get("latest_instance_observation"))
                .put("unrelated_material_extension", true);
        assertEquals(before, invoke(sample, "gap"));
    }

    @Test
    void freshIdentityRejectsFloatAndBooleanEqualityAliases() throws IOException {
        ObjectNode sample = golden().get("base").deepCopy();
        ObjectNode readback = (ObjectNode) sample.get("readback");
        readback.put("target_character_id", 34973.0);
        assertTrue(invoke(sample, "fresh").isEmpty());
        readback.put("target_character_id", true);
        assertTrue(invoke(sample, "fresh").isEmpty());
        readback.put("target_character_id", 34973);
        readback.put("active_scheme_count", 0.0);
        assertTrue(invoke(sample, "fresh").isEmpty());
    }

    @Test
    void exactIntegerDomainDoesNotRoundDatesOrRevisionsThroughDouble() throws IOException {
        ObjectNode sample = golden().get("base").deepCopy();
        BigInteger huge = new BigInteger("18446744073709551616000000000000000000001");
        sample.put("date_raw", huge);
        ObjectNode observation = (ObjectNode) sample.get("resolved").get("latest_instance_observation");
        observation.put("source_native_revision", huge);
        observation.put("source_date_raw", huge);
        ObjectNode nativeObservation = (ObjectNode) observation.get("native_observation");
        nativeObservation.put("snapshot_revision", huge);
        nativeObservation.put("date_raw", huge);
        ReusedSwayOpportunity.ObservationGap gap = invoke(sample, "gap").orElseThrow();
        assertEquals(huge, gap.sourceNativeRevision());
        assertEquals(huge, gap.sourceDateRaw());
        assertEquals(Optional.of(gap), ReusedSwayOpportunity.decodeResult(ReusedSwayOpportunity.encode(Optional.of(gap))));
    }

    @Test
    void persistedResultRequiresAllFieldsAndLiteralUnknownFlags() throws IOException {
        ObjectNode sample = golden().get("base").deepCopy();
        ObjectNode result = (ObjectNode) StrictJson.parse(ReusedSwayOpportunity.encode(invoke(sample, "gap")));
        result.put("storage_slot_reused", false);
        assertThrows(ContractViolationException.class, () -> ReusedSwayOpportunity.decodeResult(StrictJson.canonical(result)));
        result.put("storage_slot_reused", true);
        result.put("source_native_revision", true);
        assertThrows(ContractViolationException.class, () -> ReusedSwayOpportunity.decodeResult(StrictJson.canonical(result)));
        result.remove("source_native_revision");
        assertThrows(ContractViolationException.class, () -> ReusedSwayOpportunity.decodeResult(StrictJson.canonical(result)));
    }

    @Test
    void valueObjectRejectsReservedIdsAndImpossibleInstanceGeneration() {
        assertThrows(ContractViolationException.class, () -> new ReusedSwayOpportunity.ObservationGap(
                "action", 1, 2, 0xffff_ffffL, 255, BigInteger.ONE, BigInteger.ZERO,
                ReusedSwayOpportunity.TerminalCause.UNKNOWN));
        assertThrows(ContractViolationException.class, () -> new ReusedSwayOpportunity.ObservationGap(
                "action", 1, 1, 1, 0, BigInteger.ONE, BigInteger.ZERO,
                ReusedSwayOpportunity.TerminalCause.UNKNOWN));
        assertThrows(ContractViolationException.class, () -> new ReusedSwayOpportunity.ObservationGap(
                "action", 1, 2, 1, 1, BigInteger.ONE, BigInteger.ZERO,
                ReusedSwayOpportunity.TerminalCause.UNKNOWN));
    }
}
