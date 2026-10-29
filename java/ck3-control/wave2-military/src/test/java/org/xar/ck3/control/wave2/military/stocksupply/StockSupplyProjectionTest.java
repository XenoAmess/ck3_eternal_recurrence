package org.xar.ck3.control.wave2.military.stocksupply;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;

class StockSupplyProjectionTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void completeOrderedProducerMatchesOriginalGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.stocksupply.original-producer-golden/v1", golden.path("schema").textValue());
        assertFalse(golden.path("machine_id").asText().isBlank());
        assertFalse(golden.path("observed_at_utc").asText().isBlank());
        assertTrue(golden.path("source_refs").size() >= 9);
        for (JsonNode source : golden.path("source_refs")) {
            assertTrue(source.path("sha256").asText().matches("[a-f0-9]{64}"));
            assertTrue(source.path("bytes").asInt() > 0);
        }
        assertEquals(10, golden.path("vectors").size());
        for (JsonNode vector : golden.path("vectors")) {
            byte[] original = JSON.writeValueAsBytes(vector.get("input"));
            JsonNode expected = vector.get("expected");
            JsonNode actual = JSON.readTree(StockSupplyCodec.project(original));
            assertEquals(expected, actual, vector.path("id").textValue());
            assertEquals(vector.get("input"), JSON.readTree(original));
            assertEquals(actual, JSON.readTree(JSON.writeValueAsBytes(
                    StockSupplyCodec.encode(StockSupplyProjection.project(StockSupplyCodec.decode(original))))));
        }
    }

    @Test void fleetRateBranchesUseTheSharedNativeDivisionKernel() throws IOException {
        for (JsonNode vector : golden().path("rate_vectors")) {
            var input = StockSupplyCodec.decodeRate(JSON.writeValueAsBytes(vector.get("input")));
            assertEquals(vector.get("expected"), JSON.readTree(JSON.writeValueAsBytes(StockSupplyCodec.encodeRate(
                    NextFleetRate.project(input)))), vector.path("id").textValue());
        }
    }

    @Test void everyFleetRateConsumerUsesTheSameProducerWithoutUnrelatedBudgetRequirements() throws IOException {
        JsonNode vectors = golden().path("rate_vectors");
        ObjectNode query = JSON.createObjectNode();
        var rows = query.putArray("army_strengths");
        for (JsonNode vector : vectors) rows.add(vector.get("input"));
        JsonNode actual = JSON.readTree(StockSupplyCodec.projectRateServiceField(JSON.writeValueAsBytes(query)))
                .get(StockSupplyCodec.RATE_SERVICE_FIELD);
        assertEquals(vectors.size(), actual.size());
        for (int index = 0; index < vectors.size(); index++) {
            assertEquals(vectors.get(index).get("expected"), actual.get(index).get("projection"));
        }
        ObjectNode minimal = vectors.get(0).get("input").deepCopy();
        for (String unused : List.of("army_update_clock_v1", "monthly_loss_budget_inputs_v1", "loss_application_inputs_v1",
                "source_derived_next_daily_supply_frame_inputs_v1", "current_supply_capacity_raw", "current_supply_raw")) minimal.remove(unused);
        assertEquals(vectors.get(0).get("expected"), JSON.readTree(StockSupplyCodec.projectRate(JSON.writeValueAsBytes(minimal))));
    }

    @Test void soleServiceJoinPreservesRowsOrderDuplicatesAndUnavailableEntries() throws IOException {
        JsonNode vectors = golden().path("vectors");
        ObjectNode query = JSON.createObjectNode();
        var rows = query.putArray("army_strengths");
        for (int index : List.of(0, 7, 0, 1)) rows.add(vectors.get(index).get("input"));
        query.put("query_sequence", 41);
        JsonNode actual = JSON.readTree(StockSupplyCodec.projectServiceField(JSON.writeValueAsBytes(query)));
        JsonNode joined = actual.get(StockSupplyCodec.SERVICE_FIELD);
        assertEquals(4, joined.size());
        int position = 0;
        for (int index : List.of(0, 7, 0, 1)) {
            assertEquals(vectors.get(index).get("input").get("army_id"), joined.get(position).get("army_id"));
            assertEquals(vectors.get(index).get("expected"), joined.get(position).get("projection"));
            position++;
        }
        query.set("army_strengths", JSON.createArrayNode());
        assertEquals(0, JSON.readTree(StockSupplyCodec.projectServiceField(JSON.writeValueAsBytes(query)))
                .path(StockSupplyCodec.SERVICE_FIELD).size());
    }

    @Test void bothActualOriginalServiceConsumersMatchTheJavaFieldAdapters() throws IOException {
        JsonNode consumer = golden().path("service_consumer");
        assertEquals("GameplayBridgeService.query_army_strengths", consumer.path("actual_service_method").textValue());
        assertEquals(1, consumer.path("execute_step_calls").intValue());
        ObjectNode query = JSON.createObjectNode(); query.putArray("army_strengths").add(consumer.get("input"));
        byte[] raw = JSON.writeValueAsBytes(query);
        assertEquals(consumer.path("expected_fields").get(StockSupplyCodec.SERVICE_FIELD),
                JSON.readTree(StockSupplyCodec.projectServiceField(raw)).get(StockSupplyCodec.SERVICE_FIELD));
        assertEquals(consumer.path("expected_fields").get(StockSupplyCodec.RATE_SERVICE_FIELD),
                JSON.readTree(StockSupplyCodec.projectRateServiceField(raw)).get(StockSupplyCodec.RATE_SERVICE_FIELD));
    }

    @Test void budgetSuppressionDoesNotPretendThatPoststockWasComputed() throws IOException {
        JsonNode actual = projected(3);
        assertFalse(actual.path("ready").booleanValue());
        assertFalse(actual.path("conditional_post_updater_stock").path("ready").booleanValue());
        assertTrue(actual.path("conditional_budget_getter").path("ready").booleanValue());
        assertEquals(0, actual.path("conditional_budget_getter").path("soldiers").intValue());
        assertEquals("conditional_post_updater_stock", actual.path("conditional_budget_getter").path("stock_basis").textValue());
    }

    @Test void wrappedNegativeClampDoesNotRequireCapacityAndLegacyDateDoesNotBecomeFull() throws IOException {
        JsonNode wrapped = projected(4);
        assertEquals(Long.MIN_VALUE, wrapped.path("conditional_post_updater_stock").path("signed64_add_raw").longValue());
        assertEquals(0, wrapped.path("conditional_post_updater_stock").path("raw").longValue());
        assertEquals("negative_wrapped_add_to_zero", wrapped.path("conditional_post_updater_stock").path("clamp_branch").textValue());
        JsonNode legacy = projected(6);
        assertFalse(legacy.path("ordered_pre_rate_writes_ready").booleanValue());
        assertFalse(legacy.path("source_next_date").has("source_derived_full_cdate64_ready"));
        assertTrue(legacy.path("conditional_rate").path("ready").booleanValue());
        assertTrue(legacy.path("conditional_budget_getter").path("ready").booleanValue());
        for (String field : List.of("earlier_stage_effects_reconstructed", "actual_future_date_stage_observed",
                "actual_future_callback_observed", "actual_future_stock_observed", "actual_future_supply_budget_observed",
                "actual_physical_loss_observed", "future_stock_or_strength_ready", "full_daily_supply_transition_ready",
                "full_monthly_ready")) assertFalse(wrapped.path(field).booleanValue(), field);
    }

    @Test void rejectsRawFloatBoolStringAndOutOfWidthInsteadOfNormalizingTokens() throws IOException {
        JsonNode base = golden().path("vectors").get(0).get("input");
        for (String field : List.of("current_supply_raw", "current_supply_capacity_raw", "current_supply_change_monthly_raw")) {
            for (String token : List.of("true", "1.0", "1e0", "\"1\"", "9223372036854775808", "-9223372036854775809")) {
                byte[] raw = replaceRawField(base, field, token);
                assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(raw), field + ":" + token);
            }
        }
        String normal = JSON.writeValueAsString(base);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "2147483648")) {
            byte[] raw = normal.replace("\"current_native_date_low32\":53288448", "\"current_native_date_low32\":" + token)
                    .getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(raw));
        }
    }

    @Test void exactNativeFamiliesRejectUnknownMissingAndMismatchedSourceWhileSdkExtrasRemainLegal() throws IOException {
        ObjectNode base = golden().path("vectors").get(0).get("input").deepCopy();
        base.put("new_sdk_extension", "kept outside declared projection");
        assertEquals(golden().path("vectors").get(0).get("expected"),
                JSON.readTree(StockSupplyCodec.project(JSON.writeValueAsBytes(base))));
        ((ObjectNode) base.get("current_fleet_supply_tick_inputs_v1")).put("unexpected", 0);
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(JSON.writeValueAsBytes(base)));
        ObjectNode missing = golden().path("vectors").get(0).get("input").deepCopy();
        ((ObjectNode) missing.get("current_fleet_supply_tick_inputs_v1")).remove("fleet_day_raw");
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(JSON.writeValueAsBytes(missing)));
        ObjectNode mismatch = golden().path("vectors").get(0).get("input").deepCopy();
        ((ObjectNode) mismatch.get("source_derived_next_daily_supply_frame_inputs_v1")).put("current_date_raw_i32", 53288447);
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.project(JSON.writeValueAsBytes(mismatch)));
        ObjectNode future = golden().path("vectors").get(0).get("input").deepCopy();
        ((ObjectNode) future.get("source_derived_next_daily_supply_frame_inputs_v1")).put("actual_future_callback_observed", true);
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(JSON.writeValueAsBytes(future)));
    }

    @Test void rejectsDuplicateKeysTrailingJsonInvalidUtf8AndOversizeBeforeProjection() throws IOException {
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode("{\"status\":null,\"status\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(new byte[StockSupplyCodec.MAX_BYTES + 1]));
        byte[] trailing = (JSON.writeValueAsString(golden().path("vectors").get(0).get("input")) + "{}")
                .getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> StockSupplyCodec.decode(trailing));
    }

    private static JsonNode projected(int index) throws IOException {
        return JSON.readTree(StockSupplyCodec.project(JSON.writeValueAsBytes(golden().path("vectors").get(index).get("input"))));
    }
    private static byte[] replaceRawField(JsonNode object, String field, String token) throws IOException {
        StringBuilder out = new StringBuilder("{");
        for (var property : object.properties()) {
            if (out.length() > 1) out.append(',');
            out.append(JSON.writeValueAsString(property.getKey())).append(':');
            out.append(property.getKey().equals(field) ? token : JSON.writeValueAsString(property.getValue()));
        }
        return out.append('}').toString().getBytes(StandardCharsets.UTF_8);
    }
    @Test void losslessGzipKeepsEveryActualProducerAndServiceByte() throws IOException, NoSuchAlgorithmException {
        byte[] raw = goldenRaw();
        assertEquals(122_704, raw.length);
        assertEquals("ce67336fb0d481e3f1933c9da619aec9525a08e7ce034a9daac55fef6eafc5f3",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        assertArrayEquals(raw, CaptureStockSupplyGolden.decompressGolden(CaptureStockSupplyGolden.compressGolden(raw)));
        assertThrows(IOException.class, () -> CaptureStockSupplyGolden.compressGolden(new byte[131_073]));
        assertThrows(IOException.class, () -> CaptureStockSupplyGolden.decompressGolden(new byte[16_385]));
        assertThrows(IOException.class, () -> CaptureStockSupplyGolden.decompressGolden(new byte[]{0, 1, 2}));
        assertThrows(IOException.class, () -> CaptureStockSupplyGolden.compressGolden(new byte[]{(byte) 0xc3, 0x28}));
    }

    private static byte[] goldenRaw() throws IOException {
        try (var stream = StockSupplyProjectionTest.class.getResourceAsStream("/stocksupply/original-stock-supply-golden-v1.json.gz")) {
            if (stream == null) throw new IOException("tracked original producer golden required; no runtime Python fallback or skip");
            return CaptureStockSupplyGolden.decompressGolden(stream.readNBytes(CaptureStockSupplyGolden.MAX_GZIP_BYTES + 1));
        }
    }

    private static JsonNode golden() throws IOException { return JSON.readTree(goldenRaw()); }
}
