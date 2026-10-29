package org.xar.ck3.control.wave2.military.losssequence;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class LossSequencePolicyTest {
    @Test void fullOriginalFourPassProducerMatchesIncludingAliasesSkippedWritersAndPartialStages() throws Exception {
        for (JsonNode sample : golden().get("sequences")) {
            byte[] raw = StrictJson.canonical(sample.get("input"), LossSequenceCodec.MAX_BYTES);
            Input input = LossSequenceCodec.decode(raw);
            Result result = LossSequencePolicy.project(input);
            assertJsonEquals(sample.get("expected"), LossSequenceCodec.sequenceNode(result), sample.get("id").textValue());
            assertJsonEquals(sample.get("input"), StrictJson.parse(raw));
            assertEquals(input, LossSequenceCodec.decode(raw), "immutable input frame unchanged");
            assertFalse(result.actualLoss());
        }
    }

    @Test void completeActualMonthlyProducerFlowsThroughSharedBudgetSeedWriterAndRefresh() throws Exception {
        for (JsonNode sample : golden().get("monthly")) {
            ObjectNode observed = LossSequenceCodec.monthlyBudgetsNode(sample.get("input"));
            assertJsonEquals(sample.get("expected"), observed, sample.get("id").textValue());
        }
    }

    @Test void supplyOnlyConsumerDoesNotInventMissingSiegeOrRaidBudgets() throws Exception {
        for (JsonNode sample : golden().get("supply_overrides")) {
            Result result = LossSequencePolicy.project(LossSequenceCodec.decodeArmyProjectionWithSupplyBudget(
                    sample.get("input"), sample.get("supply_budget").intValue()));
            assertJsonEquals(sample.get("expected"), LossSequenceCodec.sequenceNode(result), sample.get("id").textValue());
        }
    }

    @Test void associatedWriterMatchesOriginalPhysicalChunksWritesAndSharedRefresh() throws Exception {
        for (JsonNode sample : golden().get("writers")) {
            Input input = LossSequenceCodec.decodeArmyProjection(sample.get("input"));
            WriterResult result = AssociatedChunkWriter.project(input, LossSequenceCodec.decodeWriterRequest(sample.get("request")));
            assertJsonEquals(sample.get("expected"), LossSequenceCodec.writerNode(result), sample.get("id").textValue());
        }
    }

    @Test void writerSpecificTrappingDivisionMatchesOriginalSignedNativeBranches() throws Exception {
        for (JsonNode sample : golden().get("qdivisions")) verifyDivision(sample, true);
        for (JsonNode sample : golden().get("idivisions")) verifyDivision(sample, false);
    }

    @Test void strictProjectionRejectsRawFloatBooleanAndWidthErrorsAndAcceptsUnrelatedExtensions() throws Exception {
        JsonNode original = golden().get("sequences").get(0).get("input");
        ObjectNode extended = (ObjectNode) original.deepCopy(); extended.putObject("unrelated_native_manager").put("example", "ignored");
        assertEquals(LossSequenceCodec.decodeArmyProjection(original), LossSequenceCodec.decodeArmyProjection(extended));
        String raw = new String(StrictJson.canonical(original), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> LossSequenceCodec.decode(raw.replace("\"current_supply_loss_budget\":8", "\"current_supply_loss_budget\":8.0").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LossSequenceCodec.decode(raw.replace("\"current_supply_loss_budget\":8", "\"current_supply_loss_budget\":true").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LossSequenceCodec.decode(raw.replace("\"current_supply_loss_budget\":8", "\"current_supply_loss_budget\":2147483648").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LossSequenceCodec.decodeWriterRequest(StrictJson.parse(
                "{\"army_regiment_id\":1,\"writer_quantity_raw\":1.0,\"writer_quantity_scale\":100000}".getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class, () -> LossSequenceCodec.decode("{\"status\":\"available\",\"status\":\"unavailable\"}".getBytes(StandardCharsets.UTF_8)));
    }

    private static void verifyDivision(JsonNode node, boolean q) {
        long numerator = node.get("numerator").longValue(), denominator = node.get("denominator").longValue();
        if (node.has("error")) {
            ArithmeticException error = assertThrows(ArithmeticException.class,
                    () -> { if (q) AssociatedChunkWriter.nativeQDivide(numerator, denominator); else AssociatedChunkWriter.signedDivide(numerator, denominator); });
            assertEquals(node.get("error").textValue(), error.getMessage());
        } else assertEquals(node.get("expected").longValue(), q ? AssociatedChunkWriter.nativeQDivide(numerator, denominator)
                : AssociatedChunkWriter.signedDivide(numerator, denominator));
    }
    private static JsonNode golden() throws Exception {
        byte[] raw;
        try (InputStream stream = LossSequencePolicyTest.class.getResourceAsStream("/losssequence/original-producer.json.gz")) {
            assertNotNull(stream, "original producer capture missing; never skip");
            byte[] packed = stream.readNBytes(24 * 1024 + 1);
            assertTrue(packed.length <= 24 * 1024, "compressed golden exceeds leaf budget");
            try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(packed))) { raw = gzip.readNBytes(160 * 1024 + 1); }
        }
        JsonNode node = StrictJson.parse(raw, 160 * 1024);
        assertEquals("xar.losssequence.original-producer-golden/v1", node.get("schema").textValue());
        assertTrue(node.get("original_tests_executed").booleanValue());
        assertTrue(node.get("original_tests").intValue() > 0); assertEquals(0, node.get("original_skipped").intValue());
        assertFalse(node.get("machine_id").textValue().isBlank()); assertNotEquals("unknown", node.get("machine_id").textValue());
        OffsetDateTime.parse(node.get("observed_at_utc").textValue()); Path root = root();
        for (JsonNode ref : node.get("source_refs")) {
            byte[] bytes = Files.readAllBytes(root.resolve(ref.get("path").textValue()));
            assertEquals(ref.get("bytes").longValue(), bytes.length);
            assertEquals(ref.get("sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), ref.get("path").textValue());
        }
        return node;
    }
    private static Path root() throws IOException {
        String configured = System.getProperty("xar.repo");
        if (configured == null || configured.isBlank()) configured = System.getenv("XAR_REPO_ROOT");
        if (configured != null && !configured.isBlank()) {
            Path explicit = Path.of(configured).toAbsolutePath().normalize();
            if (!Files.isRegularFile(explicit.resolve("AGENTS.md"))) throw new IOException("configured repository root missing");
            return explicit;
        }
        Path path = Path.of("").toAbsolutePath();
        while (path != null && !Files.isRegularFile(path.resolve("AGENTS.md"))) path = path.getParent();
        if (path == null) throw new IOException("repository root missing"); return path;
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
