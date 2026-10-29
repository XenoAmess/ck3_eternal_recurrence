package org.xar.ck3.control.wave2.military.fleetsupply;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.ArmyRow;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.FleetSupplyBudget;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel.StockBasis;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;

final class FleetSupplyProjectionTest {
    private static JsonNode golden() throws IOException {
        try (var input = FleetSupplyProjectionTest.class.getResourceAsStream("/fleetsupply/original-producer-golden.json.gz")) {
            assertNotNull(input, "original producer golden must be captured; no skip or fabricated expected output");
            JsonNode golden = StrictJson.parse(readGzipGolden(input), 131_072);
            assertEquals("xar.java.fleetsupply.original-producer-golden.v1", golden.path("schema").textValue());
            assertTrue(golden.path("machine_id").isTextual()); assertTrue(golden.path("source_sha256").size() >= 8);
            return golden;
        }
    }

    @Test void directAndExplicitStockMatchWholeOriginalProducerOutputs() throws IOException {
        JsonNode golden = golden(); List<ArmyRow> serviceRows = new ArrayList<>(); List<JsonNode> serviceExpected = new ArrayList<>();
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode source = golden.path("base_row").deepCopy(); merge(source, vector.path("patch"));
            byte[] before = StrictJson.canonical(source); ArmyRow row = FleetSupplyCodec.decodeRow(source);
            FleetSupplyBudget budget = vector.path("explicit_stock").booleanValue()
                    ? FleetSupplyProjection.projectAtStock(row, nullableStock(vector.get("stock")), StockBasis.CONDITIONAL_POST_UPDATER_STOCK)
                    : FleetSupplyProjection.project(row);
            ObjectNode encoded = FleetSupplyCodec.encodeBudget(budget);
            assertArrayEquals(StrictJson.canonical(vector.path("expected")), StrictJson.canonical(encoded), vector.path("name").textValue());
            assertEquals(budget, FleetSupplyCodec.decodeBudget(StrictJson.canonical(encoded)), "receipt JSON round trip");
            assertEquals(new String(before, StandardCharsets.UTF_8), new String(StrictJson.canonical(source), StandardCharsets.UTF_8),
                    "same-query input must remain untouched");
            assertFalse(encoded.path("actual_future_supply_budget_observed").booleanValue());
            assertFalse(encoded.path("full_daily_supply_transition_ready").booleanValue());
            if (!vector.path("explicit_stock").booleanValue()) {
                serviceRows.add(row); ObjectNode joined = StrictJson.object(); joined.put("army_id", row.armyId());
                joined.set("projection", vector.path("expected")); serviceExpected.add(joined);
            }
        }
        JsonNode service = FleetSupplyCodec.encodeServiceRows(FleetSupplyProjection.projectServiceRows(serviceRows));
        assertEquals(serviceExpected.size(), service.size());
        for (int i = 0; i < service.size(); i++) assertArrayEquals(StrictJson.canonical(serviceExpected.get(i)), StrictJson.canonical(service.get(i)));
    }

    @Test void nativeTickAndRowStrictBoundariesRejectWrongTokensAndIdentityDrift() throws IOException {
        ObjectNode row = golden().path("base_row").deepCopy();
        String tick = new String(StrictJson.canonical(row.path("current_fleet_supply_tick_inputs_v1")), StandardCharsets.UTF_8);
        for (String raw : List.of(tick.replace("\"scale\":100000", "\"scale\":100000.0"),
                tick.replace("\"subject_army_id\":11", "\"subject_army_id\":true"),
                tick.replace("\"fleet_day_raw\":53288472", "\"fleet_day_raw\":2147483648"),
                tick.replace("\"terrain_magic_38_raw\":0", "\"terrain_magic_38_raw\":4294967296"),
                tick.replace("\"ready\":true", "\"ready\":null"),
                tick.replace("\"scale\":100000", "\"scale\":100000,\"scale\":100000"))) {
            assertThrows(ContractViolationException.class, () -> FleetSupplyCodec.decodeTick(raw.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode missing = row.path("current_fleet_supply_tick_inputs_v1").deepCopy(); missing.remove("terrain_modifier_772_raw");
        assertThrows(ContractViolationException.class, () -> FleetSupplyCodec.decodeTick(missing));
        ObjectNode unknown = row.path("current_fleet_supply_tick_inputs_v1").deepCopy(); unknown.put("unexpected", 1);
        assertThrows(ContractViolationException.class, () -> FleetSupplyCodec.decodeTick(unknown));
        ObjectNode mismatched = row.deepCopy(); ((ObjectNode) mismatched.path("current_fleet_supply_tick_inputs_v1")).put("subject_army_id", 99);
        assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                () -> FleetSupplyProjection.project(FleetSupplyCodec.decodeRow(mismatched)));
        ArmyRow typed = FleetSupplyCodec.decodeRow(row);
        ObjectNode foreignFrame = row.path("source_derived_next_daily_supply_frame_inputs_v1").deepCopy();
        foreignFrame.put("subject_carmy_id_u32", 99);
        var parsedForeignFrame = SourceNextFrameCodec.decode(foreignFrame);
        assertThrows(ContractViolationException.class, () -> new ArmyRow(typed.status(), typed.armyId(), typed.nativeCarmyId(),
                typed.currentSupplyRaw(), typed.fleetTick(), parsedForeignFrame, typed.supplyInputs(), typed.lossInputs(),
                typed.observedSuppressed(), typed.observedBudget()));
        String rawRow = new String(StrictJson.canonical(row), StandardCharsets.UTF_8);
        for (String raw : List.of(rawRow.replace("\"current_supply_raw\":123450000", "\"current_supply_raw\":123450000.0"),
                rawRow.replace("\"native_carmy_id\":12", "\"native_carmy_id\":false"),
                rawRow.replace("\"supply_eligible_soldiers\":100", "\"supply_eligible_soldiers\":100.0"))) {
            assertThrows(ContractViolationException.class, () -> FleetSupplyCodec.decodeRow(raw.getBytes(StandardCharsets.UTF_8)));
        }
        assertArrayEquals(StrictJson.canonical(row.path("current_fleet_supply_tick_inputs_v1")), StrictJson.canonical(FleetSupplyCodec.encodeTick(
                FleetSupplyCodec.decodeTick(row.path("current_fleet_supply_tick_inputs_v1")))));
    }

    @Test void persistedBudgetCannotClaimFutureExecutionOrContradictStockAndReadiness() throws IOException {
        FleetSupplyBudget budget = FleetSupplyProjection.project(FleetSupplyCodec.decodeRow(golden().path("base_row")));
        for (String field : List.of("actual_future_supply_budget_observed", "actual_future_callback_observed",
                "full_monthly_ready", "post_updater_stock_used")) {
            ObjectNode invalid = FleetSupplyCodec.encodeBudget(budget); invalid.put(field, true);
            assertThrows(ContractViolationException.class, () -> FleetSupplyCodec.decodeBudget(invalid));
        }
        ObjectNode invalid = FleetSupplyCodec.encodeBudget(budget); invalid.put("conditional_supply_budget_ready", false);
        assertThrows(ContractViolationException.class, () -> FleetSupplyCodec.decodeBudget(invalid));
    }

    private static Long nullableStock(JsonNode value) {
        return value == null || value.isNull() ? null : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    private static void merge(ObjectNode target, JsonNode patch) {
        patch.properties().forEach(entry -> {
            JsonNode old = target.get(entry.getKey()); JsonNode replacement = entry.getValue();
            if (old instanceof ObjectNode object && replacement.isObject()) merge(object, replacement);
            else target.set(entry.getKey(), replacement.deepCopy());
        });
    }

    @Test void malformedGzipExistingCliIsRejectedAtTheActualCaptureEntry() {
        assertThrows(IllegalArgumentException.class, () -> CaptureFleetSupplyGolden.main(new String[] {"--gzip-existing"}));
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
