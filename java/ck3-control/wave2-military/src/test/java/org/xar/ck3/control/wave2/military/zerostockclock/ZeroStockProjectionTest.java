package org.xar.ck3.control.wave2.military.zerostockclock;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterInput;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockModel.Input;

final class ZeroStockProjectionTest {
    private static JsonNode golden() throws IOException {
        try (var input = ZeroStockProjectionTest.class.getResourceAsStream("/zerostockclock/original-producer-golden.json.gz")) {
            assertNotNull(input, "actual original-producer golden required, never skip missing evidence");
            JsonNode value = StrictJson.parse(readGzipGolden(input), 131_072);
            assertEquals("xar.java.zerostockclock.original-producer-golden.v1", value.path("schema").textValue());
            assertTrue(value.path("source_sha256").size() >= 12); assertTrue(value.path("machine_id").isTextual()); return value;
        }
    }

    @Test void originalClockQueueUpdaterAndBudgetCompositionsMatchCompleteProducerOutputs() throws IOException {
        JsonNode golden = golden();
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode row = golden.path("base_row").deepCopy(); apply(row, vector.path("changes"));
            byte[] before = StrictJson.canonical(row);
            var candidate = ZeroStockProjection.projectNextCallbackCandidate(ZeroStockCodec.decode(row));
            JsonNode encoded = ZeroStockCodec.encode(candidate);
            assertArrayEquals(StrictJson.canonical(vector.path("expected")), StrictJson.canonical(encoded), vector.path("name").textValue());
            assertArrayEquals(before, StrictJson.canonical(row), "source row unchanged");
            assertArrayEquals(StrictJson.canonical(encoded), StrictJson.canonical(StrictJson.parse(StrictJson.canonical(encoded))),
                    "JSON integer-domain serialization round trip");
            assertFalse(encoded.path("physical_loss_observed").booleanValue());
            assertFalse(encoded.path("full_monthly_ready").booleanValue());
            assertTrue(encoded.path("successful_updater_count").isNull());
            assertFalse(encoded.path("conditional_next_zero_supply_budget_v1").path("physical_writer_execution_ready").booleanValue());
        }
    }

    @Test void originalSuccessfulOccurrenceCountsPreserveLongBoundariesAndDoNotForecastCalendarDays() throws IOException {
        JsonNode golden = golden();
        for (JsonNode vector : golden.path("opportunities")) {
            JsonNode result = ZeroStockCodec.encodeOpportunities(ZeroStockProjection.successfulOccurrencesToZero(
                    nullableLong(vector.get("stock")), nullableLong(vector.get("capacity")), nullableLong(vector.get("monthly"))));
            assertArrayEquals(StrictJson.canonical(vector.path("expected")), StrictJson.canonical(result));
            if (result.path("ready").booleanValue()) {
                assertTrue(result.path("actual_days").isNull()); assertFalse(result.path("physical_loss_predicted").booleanValue());
            }
        }
        var maximum = ZeroStockProjection.successfulOccurrencesToZero(Long.MAX_VALUE, Long.MAX_VALUE, -1L);
        assertEquals(Long.MAX_VALUE, ((ZeroStockModel.AvailableOpportunities) maximum).successfulBucketOccurrences());
    }

    @Test void strictClockAndRawIntegerBoundariesRejectMalformedTokensAndTypedIdentityDrift() throws IOException {
        ObjectNode row = golden().path("base_row").deepCopy();
        JsonNode rawClock = row.path("army_update_clock_v1");
        ArmyUpdateClock clock = ArmyUpdateClockCodec.decode(rawClock);
        assertEquals(clock, ArmyUpdateClockCodec.decode(ArmyUpdateClockCodec.encode(clock)));
        assertArrayEquals(StrictJson.canonical(rawClock), StrictJson.canonical(ArmyUpdateClockCodec.encode(clock)));
        String clockText = new String(StrictJson.canonical(rawClock), StandardCharsets.UTF_8);
        for (String raw : List.of(clockText.replace("\"native_day_index\":12", "\"native_day_index\":12.0"),
                clockText.replace("\"current_date_raw\":43800000", "\"current_date_raw\":true"),
                clockText.replace("\"selected_bucket_phase\":12", "\"selected_bucket_phase\":30"),
                clockText.replace("\"ready\":true", "\"ready\":true,\"ready\":true"))) {
            assertThrows(ContractViolationException.class, () -> ArmyUpdateClockCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode missing = rawClock.deepCopy(); missing.remove("native_day_index");
        assertThrows(ContractViolationException.class, () -> ArmyUpdateClockCodec.decode(missing));
        ObjectNode extra = rawClock.deepCopy(); extra.put("future_observed", true);
        assertThrows(ContractViolationException.class, () -> ArmyUpdateClockCodec.decode(extra));
        ObjectNode wrongSeed = row.deepCopy(); ((ObjectNode) wrongSeed.path("army_update_clock_v1")).put("native_day_index", 13);
        assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class, () -> ZeroStockProjection.projectNextCallbackCandidate(ZeroStockCodec.decode(wrongSeed)));
        String rowText = new String(StrictJson.canonical(row), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> ZeroStockCodec.decode(rowText.replace("\"current_supply_raw\":1",
                "\"current_supply_raw\":1.0").getBytes(StandardCharsets.UTF_8)));
        Input typed = ZeroStockCodec.decode(row); var old = typed.updater();
        var foreign = new UpdaterInput(old.rowAvailable(), 99, old.nativeCarmyId(), old.gateInputs(), old.clock(), old.caller(), old.sourceNextDate());
        assertThrows(ContractViolationException.class, () -> new Input(typed.available(), typed.armyId(), typed.nativeCarmyId(),
                typed.stockRaw(), typed.capacityRaw(), typed.monthlyRaw(), typed.clock(), typed.schedule(), foreign,
                typed.completeMonthlyFamily(), typed.losses()));
    }

    private static Long nullableLong(JsonNode node) { return node == null || node.isNull() ? null : StrictJson.integer(node, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static void apply(ObjectNode row, JsonNode changes) {
        for (var change : changes.properties()) {
            String[] parts = change.getKey().substring(1).split("/"); JsonNode owner = row;
            for (int i = 0; i < parts.length - 1; i++) owner = owner.isArray() ? owner.get(Integer.parseInt(parts[i])) : owner.get(parts[i]);
            String field = parts[parts.length - 1];
            if (owner instanceof ArrayNode array) array.set(Integer.parseInt(field), change.getValue().deepCopy());
            else ((ObjectNode) owner).set(field, change.getValue().deepCopy());
        }
    }

    @Test void malformedGzipExistingCliIsRejectedAtTheActualCaptureEntry() {
        assertThrows(IllegalArgumentException.class, () -> CaptureZeroStockGolden.main(new String[] {"--gzip-existing"}));
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
}
