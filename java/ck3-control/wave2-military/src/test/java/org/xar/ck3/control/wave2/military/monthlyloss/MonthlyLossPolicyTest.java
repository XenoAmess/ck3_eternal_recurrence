package org.xar.ck3.control.wave2.military.monthlyloss;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class MonthlyLossPolicyTest {
    @Test void completeBudgetKernelMatchesActualOriginalProducer() throws Exception {
        JsonNode golden = golden();
        for (JsonNode sample : golden.get("monthly")) {
            byte[] input = StrictJson.canonical(sample.get("input"), MonthlyLossCodec.MAX_BYTES);
            Input model = MonthlyLossCodec.decode(input);
            Result value = MonthlyLossPolicy.constructConditionalMonthlyLossBudgets(model);
            SupplyEntry entry = MonthlyLossPolicy.projectSupplyEntry(MonthlyLossCodec.decodeSupplyEntryProjection(sample.get("input")));
            assertJsonEquals(sample.get("expected_kernel"), MonthlyLossCodec.kernelNode(value), sample.get("id").asText());
            assertEquals(value.supplyUpdaterAdmitted(), entry.admitted());
            assertEquals(value.admissionWitnesses(), entry.witnesses());
            assertEquals(value.admissionRejection(), entry.rejection());
            assertEquals(value.conditionalPostSupplyRaw(), entry.postStockRaw());
            assertEquals(value.supplyComponent(), entry.component());
            assertJsonEquals(sample.get("expected_kernel").get("admission_witnesses"), MonthlyLossCodec.admissionWitnessesNode(entry.witnesses()));
            assertJsonEquals(sample.get("input"), StrictJson.parse(input), "caller row remains immutable");
            assertEquals(value.conditionalBudgetsReady(), value.lossSequenceSeed() != null);
            if (value.lossSequenceSeed() != null) {
                assertEquals(value.supplyComponent().soldiers().intValue(), value.lossSequenceSeed().currentSupplyLossBudget());
                assertEquals(value.siegeBudgetSoldiers().intValue(), value.lossSequenceSeed().siegeLossBudget());
                assertEquals(value.raidBudgetSoldiers().intValue(), value.lossSequenceSeed().raidLossBudget());
            }
        }
    }

    @Test void sharedSupplyKernelMatchesOriginalReachedOperandBranches() throws Exception {
        for (JsonNode sample : golden().get("supply")) {
            JsonNode inputs = sample.get("inputs");
            SupplyInputs model = new SupplyInputs(integerList(inputs.get("loaded_supply_state_levels")),
                    longList(inputs.get("loaded_supply_state_fractions_raw")), nullableBool(inputs.get("commander_valid")),
                    nullableLong(inputs.get("commander_supply_modifier_raw")));
            JsonNode count = sample.get("losses").get("supply_eligible_soldiers");
            SupplyComponent result = MonthlyLossPolicy.deriveSupplyComponent(sample.get("stock").longValue(), model,
                    new LossInputs(count.isNull() ? null : count.intValue(), null));
            assertJsonEquals(sample.get("expected"), MonthlyLossCodec.supplyComponentNode(result), sample.get("id").asText());
            StockState state = MonthlyLossPolicy.projectStockState(sample.get("stock").longValue(), model);
            JsonNode expectedState = sample.get("expected_state");
            assertEquals(expectedState.get("ready").booleanValue(), state.ready());
            assertEquals(nullableInt(expectedState.get("stock_integer")), state.stockInteger());
            assertEquals(nullableInt(expectedState.get("state_index")), state.stateIndex());
            assertEquals(nullableLong(expectedState.get("base_fraction_raw")), state.baseFractionRaw());
            java.util.ArrayList<String> missing = new java.util.ArrayList<>(); expectedState.get("missing_inputs").forEach(value -> missing.add(value.textValue()));
            assertEquals(missing, state.missingInputs());
        }
    }

    @Test void sourceFamilyStrictContractAndRoundTripMatchOriginalNormalizer() throws Exception {
        for (JsonNode sample : golden().get("contract")) {
            String raw = sample.get("raw").textValue();
            if (!sample.get("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class,
                        () -> MonthlyLossCodec.decodeFamilyNullable(StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8))),
                        sample.get("id").asText());
            } else {
                BudgetInputs decoded = MonthlyLossCodec.decodeFamilyNullable(StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8)));
                JsonNode encoded = MonthlyLossCodec.encodeFamilyNullable(decoded);
                assertJsonEquals(sample.get("expected"), encoded, sample.get("id").asText());
                assertEquals(decoded, MonthlyLossCodec.decodeFamilyNullable(StrictJson.parse(StrictJson.canonical(encoded))));
            }
        }
        assertThrows(IllegalArgumentException.class, () -> MonthlyLossCodec.decode("{\"status\":\"available\",\"current_supply_raw\":1.0}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MonthlyLossCodec.decode("{\"status\":\"available\",\"status\":\"unavailable\"}".getBytes(StandardCharsets.UTF_8)));
        ObjectNode extended = (ObjectNode) golden().get("monthly").get(0).get("input").deepCopy();
        extended.putObject("unrelated_sdk_extension").put("extra", true);
        assertEquals(MonthlyLossCodec.decodeArmyProjection(golden().get("monthly").get(0).get("input")),
                MonthlyLossCodec.decodeArmyProjection(extended));
    }

    @Test void supplyVectorsAreImmutableAndEmptyIsDistinctFromUnknown() {
        java.util.ArrayList<Integer> levels = new java.util.ArrayList<>(List.of(0));
        SupplyInputs copied = new SupplyInputs(levels, List.of(10_000L), false, null);
        levels.clear(); assertEquals(List.of(0), copied.loadedSupplyStateLevels());
        assertThrows(UnsupportedOperationException.class, () -> copied.loadedSupplyStateLevels().clear());
        assertFalse(MonthlyLossPolicy.deriveSupplyComponent(0, new SupplyInputs(null, null, null, null), new LossInputs(null, null)).ready());
        assertTrue(MonthlyLossPolicy.deriveSupplyComponent(0, new SupplyInputs(List.of(), null, null, null), new LossInputs(null, null)).ready());
    }

    private static JsonNode golden() throws Exception {
        byte[] raw;
        try (InputStream stream = MonthlyLossPolicyTest.class.getResourceAsStream("/monthlyloss/original-producer.json.gz")) {
            assertNotNull(stream, "missing original producer golden: capture is required, never a skip");
            raw = readGzipGolden(stream);
        }
        JsonNode node = StrictJson.parse(raw, 131_072);
        assertEquals("xar.monthlyloss.original-producer-golden/v1", node.get("schema").textValue());
        assertTrue(node.get("original_tests_executed").booleanValue());
        assertTrue(node.get("original_tests").intValue() > 0); assertEquals(0, node.get("original_skipped").intValue());
        assertFalse(node.get("machine_id").textValue().isBlank());
        assertNotEquals("unknown", node.get("machine_id").textValue());
        OffsetDateTime.parse(node.get("observed_at_utc").textValue());
        Path root = repositoryRoot();
        for (JsonNode ref : node.get("source_refs")) {
            byte[] source = Files.readAllBytes(root.resolve(ref.get("path").textValue()));
            assertEquals(ref.get("bytes").longValue(), source.length);
            assertEquals(ref.get("sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(source)), ref.get("path").textValue());
        }
        return node;
    }
    private static Path repositoryRoot() throws IOException {
        String configured = System.getProperty("xar.repo");
        if (configured == null || configured.isBlank()) configured = System.getenv("XAR_REPO_ROOT");
        if (configured != null && !configured.isBlank()) {
            Path explicit = Path.of(configured).toAbsolutePath().normalize();
            if (!Files.isRegularFile(explicit.resolve("AGENTS.md"))) throw new IOException("configured repository root missing");
            return explicit;
        }
        Path current = Path.of("").toAbsolutePath();
        while (current != null && !Files.isRegularFile(current.resolve("AGENTS.md"))) current = current.getParent();
        if (current == null) throw new IOException("repository root not found"); return current;
    }
    private static List<Integer> integerList(JsonNode node) {
        if (node.isNull()) return null;
        java.util.ArrayList<Integer> result = new java.util.ArrayList<>(); node.forEach(value -> result.add(value.intValue())); return List.copyOf(result);
    }
    private static List<Long> longList(JsonNode node) {
        if (node.isNull()) return null;
        java.util.ArrayList<Long> result = new java.util.ArrayList<>(); node.forEach(value -> result.add(value.longValue())); return List.copyOf(result);
    }
    private static Boolean nullableBool(JsonNode node) { return node.isNull() ? null : node.booleanValue(); }
    private static Long nullableLong(JsonNode node) { return node.isNull() ? null : node.longValue(); }
    private static Integer nullableInt(JsonNode node) { return node.isNull() ? null : node.intValue(); }

    @Test void historicalMonthlyGzipExistingIsRejectedAtTheActualCaptureEntry() {
        assertThrows(IllegalArgumentException.class, () -> CaptureMonthlyLossGolden.main(new String[] {"--gzip-existing"}));
    }
    private static byte[] readGzipGolden(java.io.InputStream input) throws IOException {
        byte[] packed = input.readNBytes(16_385);
        if (packed.length == 0 || packed.length > 16_384) throw new IOException("golden gzip exceeds 16KiB profile");
        byte[] raw;
        try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(packed))) {
            raw = gzip.readNBytes(131_073);
        }
        if (raw.length == 0 || raw.length > 131_072) throw new IOException("golden raw exceeds 128KiB profile");
        java.nio.charset.StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(raw));
        return raw;
    }
    @Test void gzipLoaderPreservesOriginalTokenBytesAndEnforcesBounds() throws Exception {
        byte[] raw = "{\"token\":1.0,\"text\":\"供给😀\",\"wide\":9223372036854775807}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] packed = gzipFixture(raw);
        byte[] decoded = readGzipGolden(new java.io.ByteArrayInputStream(packed));
        assertArrayEquals(raw, decoded);
        assertTrue(StrictJson.parse(decoded).get("token").isFloatingPointNumber());
        assertEquals(Long.MAX_VALUE, StrictJson.parse(decoded).get("wide").longValue());
        assertThrows(IOException.class, () -> readGzipGolden(new java.io.ByteArrayInputStream(java.util.Arrays.copyOf(packed, packed.length - 3))));
        assertThrows(IOException.class, () -> readGzipGolden(new java.io.ByteArrayInputStream(new byte[16_385])));
        assertThrows(IOException.class, () -> readGzipGolden(new java.io.ByteArrayInputStream(gzipFixture(new byte[131_073]))));
        assertThrows(IOException.class, () -> readGzipGolden(new java.io.ByteArrayInputStream(gzipFixture(new byte[] {(byte) 0xc3, 0x28}))));
    }
    private static byte[] gzipFixture(byte[] raw) throws IOException {
        java.io.ByteArrayOutputStream packed = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gzip = new java.util.zip.GZIPOutputStream(packed)) { gzip.write(raw); }
        return packed.toByteArray();
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
