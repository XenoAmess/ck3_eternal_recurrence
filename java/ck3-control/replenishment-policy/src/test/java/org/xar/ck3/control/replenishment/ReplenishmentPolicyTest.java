package org.xar.ck3.control.replenishment;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.replenishment.ReplenishmentModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

class ReplenishmentPolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void committedOriginalProducerArithmeticVectors() throws IOException {
        JsonNode corpus = corpus();
        assertEquals("xar.replenishment.python-producer-golden/v1", corpus.path("schema").asText());
        assertEquals(5, corpus.path("original_tests_run").intValue());
        assertEquals(0, corpus.path("original_test_failures").intValue());
        assertEquals(0, corpus.path("original_test_errors").intValue());
        assertTrue(corpus.path("chunks").size() >= 300);
        for (JsonNode vector : corpus.path("chunks")) {
            ChunkInput input = ReplenishmentCodec.decodeChunkInput(JSON.writeValueAsBytes(vector.get("input")));
            ChunkCalculation actual = ReplenishmentPolicy.sameInputChunkQ(input.maximumSoldiers(),
                    input.effectiveCurrentSoldiers(), input.preparedFractionRaw(), input.nativeChunkCanReplenish());
            assertEquals(vector.get("expected"), JSON.readTree(ReplenishmentCodec.encodeCalculation(actual)),
                    vector.path("id").asText());
            assertEquals(vector.get("expected"), JSON.readTree(new ReplenishmentFacade().calculateChunk(
                    JSON.writeValueAsBytes(vector.get("input")))));
        }
    }

    @Test void committedOriginalProducerProjectionVectors() throws IOException {
        JsonNode corpus = corpus();
        assertTrue(corpus.path("projections").size() >= 20);
        for (JsonNode vector : corpus.path("projections")) {
            byte[] originalInput = JSON.writeValueAsBytes(vector.get("input"));
            List<ArmyRow> input = ReplenishmentCodec.decodeObservedInput(originalInput);
            Projection actual = ReplenishmentPolicy.projectObservedReplenishmentV1(input);
            assertEquals(vector.get("expected"), JSON.readTree(ReplenishmentCodec.encodeProjection(actual)),
                    vector.path("id").asText());
            assertEquals(vector.get("input"), JSON.readTree(ReplenishmentCodec.encodeObservedInput(input)));
            assertEquals(input, ReplenishmentCodec.decodeObservedInput(ReplenishmentCodec.encodeObservedInput(input)));
            assertEquals(vector.get("expected"), JSON.readTree(new ReplenishmentFacade().projectObserved(originalInput)));
        }
    }

    @Test void arithmeticNativeWidthsAndQualifiedZero() {
        ChunkCalculation zero = ReplenishmentPolicy.sameInputChunkQ(10, 0, 1, true);
        assertTrue(zero.nativeCoreChunkQualifies());
        assertEquals(0, zero.sameInputQ());
        ChunkCalculation wrapped = ReplenishmentPolicy.sameInputChunkQ(3, 0, 6_148_914_691_236_483_871L, true);
        assertEquals(-100_003L, wrapped.wrappedProduct());
        assertEquals(-1, wrapped.sameInputQ());
        ChunkCalculation narrowed = ReplenishmentPolicy.sameInputChunkQ(Integer.MAX_VALUE,
                Integer.MIN_VALUE, 400_000, true);
        assertEquals(4_294_967_295L, narrowed.effectiveDeficit());
        assertEquals(-1, narrowed.sameInputQ());
    }

    @Test void missingNullAndKnownEmptyAreDistinctInsideBoundary() {
        ArmyRow missing = decodeArmy("{\"army_id\":1}");
        ArmyRow explicitNull = decodeArmy("{\"army_id\":1,\"regiment_replenishment_records_v1\":null}");
        ArmyRow empty = decodeArmy("{\"army_id\":1,\"regiment_replenishment_records_v1\":[]}");
        assertInstanceOf(MissingSnapshots.class, missing.snapshots());
        assertInstanceOf(NullSnapshots.class, explicitNull.snapshots());
        assertInstanceOf(PublishedSnapshots.class, empty.snapshots());
        assertEquals(CoverageStatus.UNAVAILABLE, ReplenishmentPolicy.projectObservedReplenishmentV1(List.of(missing)).status());
        assertEquals(CoverageStatus.UNAVAILABLE, ReplenishmentPolicy.projectObservedReplenishmentV1(List.of(explicitNull)).status());
        assertEquals(CoverageStatus.AVAILABLE, ReplenishmentPolicy.projectObservedReplenishmentV1(List.of(empty)).status());
    }

    @Test void rejectsWrongTokensAndIntegerDomains() {
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "2147483648", "-2147483649")) {
            assertThrows(IllegalArgumentException.class,
                    () -> ReplenishmentCodec.decodeObservedInput(bytes("{\"schema\":\""
                            + ReplenishmentCodec.INPUT_SCHEMA + "\",\"army_rows\":[{\"army_id\":" + token + "}]}")), token);
        }
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null", "9223372036854775808", "-9223372036854775809")) {
            assertThrows(IllegalArgumentException.class, () -> ReplenishmentCodec.decodeChunkInput(
                    bytes(chunkJson(token, "true"))), token);
        }
        for (String predicate : List.of("0", "1", "\"true\"", "null")) {
            assertThrows(IllegalArgumentException.class, () -> ReplenishmentCodec.decodeChunkInput(
                    bytes(chunkJson("1", predicate))), predicate);
        }
        assertDoesNotThrow(() -> ReplenishmentCodec.decodeChunkInput(bytes(chunkJson("-9223372036854775808", "true"))));
        assertDoesNotThrow(() -> ReplenishmentCodec.decodeChunkInput(bytes(chunkJson("9223372036854775807", "true"))));
    }

    @Test void rejectsMalformedDuplicateUnknownAndOversizedInput() {
        String valid = "{\"schema\":\"" + ReplenishmentCodec.INPUT_SCHEMA + "\",\"army_rows\":[]}";
        for (String malformed : List.of(valid + "{}", valid.replace("[]", "null"),
                valid.replace("[]", "[] , \"army_rows\": []"),
                valid.replace("[]", "[] , \"extra\": 0"), valid.replace("/v1", "/v2"))) {
            assertThrows(IllegalArgumentException.class, () -> ReplenishmentCodec.decodeObservedInput(bytes(malformed)));
        }
        assertThrows(IllegalArgumentException.class, () -> ReplenishmentCodec.decodeObservedInput(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class,
                () -> ReplenishmentCodec.decodeObservedInput(new byte[ReplenishmentCodec.MAX_INPUT_BYTES + 1]));
    }

    @Test void recordFieldTokensAndMissingFieldsAreValidatedBeforeDomainConstruction() throws IOException {
        JsonNode original = corpus().path("projections").get(0).get("input");
        for (String field : List.of("record_index", "persistent_regiment_id", "chunk_index", "maximum_soldiers",
                "effective_current_soldiers", "persistent_prepared_replenishment_fraction_raw",
                "persistent_prepared_replenishment_fraction_scale")) {
            for (String token : List.of("true", "1.0", "1e0", "\"1\"")) {
                JsonNode input = original.deepCopy();
                ObjectNode record = (ObjectNode) input.path("army_rows").get(0)
                        .path("regiment_replenishment_records_v1").get(0).path("records").get(0);
                record.set(field, JSON.readTree(token));
                byte[] bytes = JSON.writeValueAsBytes(input);
                assertThrows(IllegalArgumentException.class, () -> ReplenishmentCodec.decodeObservedInput(bytes), field + ":" + token);
            }
        }
        JsonNode missing = original.deepCopy();
        ((ObjectNode) missing.path("army_rows").get(0).path("regiment_replenishment_records_v1")
                .get(0).path("records").get(0)).remove("maximum_soldiers");
        assertThrows(IllegalArgumentException.class,
                () -> ReplenishmentCodec.decodeObservedInput(JSON.writeValueAsBytes(missing)));
    }

    @Test void modelCollectionsAreDefensivelyFrozen() throws IOException {
        JsonNode first = corpus().path("projections").get(0);
        List<ArmyRow> rows = ReplenishmentCodec.decodeObservedInput(JSON.writeValueAsBytes(first.get("input")));
        Projection result = ReplenishmentPolicy.projectObservedReplenishmentV1(rows);
        PersistentOutput group = result.persistentOutputs().getFirst();
        assertThrows(UnsupportedOperationException.class, () -> rows.clear());
        assertThrows(UnsupportedOperationException.class, () -> group.sameInputQByChunk().set(0, 99));
        assertThrows(UnsupportedOperationException.class, () -> group.observationsByChunk().getFirst().clear());
    }

    private static JsonNode corpus() throws IOException {
        try (var input = ReplenishmentPolicyTest.class.getResourceAsStream("/replenishment-golden-v1.json")) {
            if (input == null) throw new IOException("committed original-producer golden is required; no skip or Python fallback");
            return JSON.readTree(input);
        }
    }
    private static ArmyRow decodeArmy(String row) {
        return ReplenishmentCodec.decodeObservedInput(bytes("{\"schema\":\"" + ReplenishmentCodec.INPUT_SCHEMA
                + "\",\"army_rows\":[" + row + "]}")).getFirst();
    }
    private static String chunkJson(String prepared, String predicate) {
        return "{\"schema\":\"" + ReplenishmentCodec.CHUNK_SCHEMA
                + "\",\"maximum_soldiers\":1,\"effective_current_soldiers\":0,\"prepared_fraction_raw\":"
                + prepared + ",\"native_chunk_can_replenish\":" + predicate + "}";
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
