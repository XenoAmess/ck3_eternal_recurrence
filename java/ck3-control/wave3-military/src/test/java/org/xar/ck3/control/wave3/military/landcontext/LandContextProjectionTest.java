package org.xar.ck3.control.wave3.military.landcontext;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class LandContextProjectionTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void completeOriginalFullRateProducerDifferential() throws IOException {
        JsonNode golden = golden(); assertTrue(golden.path("rates").size() >= 7);
        for (JsonNode vector : golden.path("rates")) {
            ObjectNode row = merge(golden.path("base_row").deepCopy(), vector.path("patch"));
            JsonNode before = row.deepCopy();
            var result = FullLandRatePolicy.project(LandContextCodec.decodeRow(JSON.writeValueAsBytes(row)), vector.path("selected_usage").intValue());
            assertEquals(vector.get("expected"), JSON.readTree(JSON.writeValueAsBytes(LandContextCodec.encodeProjection(result))), vector.path("id").asText());
            assertEquals(before, row);
        }
    }

    @Test void completeOriginalOuterLandProducerDifferentialUsesSharedBudgetGetter() throws IOException {
        JsonNode golden = golden(); assertTrue(golden.path("stocks").size() >= 7);
        for (JsonNode vector : golden.path("stocks")) {
            ObjectNode row = merge(golden.path("base_row").deepCopy(), vector.path("patch")); JsonNode before = row.deepCopy();
            var result = FullLandStockPolicy.project(LandContextCodec.decodeStockInput(JSON.writeValueAsBytes(row)));
            assertEquals(vector.get("expected"), JSON.readTree(JSON.writeValueAsBytes(LandContextCodec.encodeStockProjection(result))), vector.path("id").asText());
            assertEquals(before, row);
            assertFalse(LandContextCodec.encodeStockProjection(result).path("actual_future_callback_observed").booleanValue());
        }
    }

    @Test void completeNativeNormalizersIncludeNestedDataAndCharacterRole() throws IOException {
        for (JsonNode vector : golden().path("normalizers")) {
            JsonNode original = vector.get("input");
            JsonNode actual = switch (vector.path("kind").textValue()) {
                case "rate" -> LandContextCodec.encodeRate(LandContextCodec.decodeRate(original));
                case "resupply" -> LandContextCodec.encodeResupply(LandContextCodec.decodeResupply(original));
                case "province" -> LandContextCodec.encodeProvince(LandContextCodec.decodeProvince(original));
                default -> throw new AssertionError("unknown persisted vector kind");
            };
            assertEquals(vector.get("expected"), JSON.readTree(JSON.writeValueAsBytes(actual)), vector.path("id").asText());
        }
    }

    @Test void orderedDuplicateOccurrencesAreNotDeduplicatedAndListsAreImmutable() throws IOException {
        ProvinceContributors province = LandContextCodec.decodeProvince(golden().path("normalizers").get(3).get("input"));
        assertEquals(2, province.occurrences().size());
        assertEquals(province.occurrences().getFirst().armyId(), province.occurrences().getLast().armyId());
        assertNotEquals(province.occurrences().getFirst().storedIndex(), province.occurrences().getLast().storedIndex());
        assertThrows(UnsupportedOperationException.class, () -> province.occurrences().clear());
        assertThrows(UnsupportedOperationException.class, () -> province.occurrences().getFirst().regiments().clear());
        assertThrows(UnsupportedOperationException.class, () -> province.occurrences().getFirst().regiments().getFirst().replenishmentRecords().records().clear());
        assertTrue(province.contributorsReady());
    }

    @Test void contextDriftRejectsOnlyAfterReachedMissingChecks() throws IOException {
        ObjectNode row = golden().path("base_row").deepCopy();
        ((ObjectNode) row.get("current_province_supply_contributors_v1")).put("owner_character_id", 33389);
        assertThrows(IllegalArgumentException.class, () -> FullLandRatePolicy.project(LandContextCodec.decodeRow(row), 80));
        row.putNull("current_land_supply_rate_inputs_v1");
        var missing = FullLandRatePolicy.project(LandContextCodec.decodeRow(row), 80);
        assertFalse(missing.ready()); assertEquals(java.util.List.of("current_land_supply_rate_inputs_v1"), missing.missingInputs());
    }

    @Test void unavailableNullAndKnownEmptyRosterRemainIndependent() throws IOException {
        JsonNode base = golden().path("base_row");
        assertNull(LandContextCodec.decodeProvince(com.fasterxml.jackson.databind.node.NullNode.getInstance()));
        ProvinceContributors empty = LandContextCodec.decodeProvince(base.get("current_province_supply_contributors_v1"));
        assertTrue(empty.contributorsReady()); assertTrue(empty.occurrences().isEmpty());
        ObjectNode partial = base.get("current_province_supply_contributors_v1").deepCopy();
        partial.put("status", "partial"); partial.put("contributors_ready", false); partial.putNull("native_province_unit_count");
        assertTrue(LandContextCodec.decodeProvince(partial).currentUsageReady());
        assertFalse(LandContextCodec.decodeProvince(partial).contributorsReady());
        LandResupply unavailable = LandContextCodec.decodeResupply(golden().path("normalizers").get(2).get("input"));
        assertNull(unavailable.unavailableReason()); assertFalse(unavailable.currentObservationReady());
    }

    @Test void strictActualIntegerTokensAndCompleteClosedFields() throws IOException {
        String raw = JSON.writeValueAsString(golden().path("base_row"));
        for (String token : java.util.List.of("true", "100000.0", "1e5", "\"100000\"")) {
            String changed = raw.replaceFirst("\"scale\":100000", "\"scale\":" + token);
            assertNotEquals(raw, changed);
            assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeRow(changed.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode row = golden().path("base_row").deepCopy();
        ObjectNode rate = (ObjectNode) row.get("current_land_supply_rate_inputs_v1"); rate.remove("province_component_raw");
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeRow(row));
        rate.put("province_component_raw", -600000); rate.put("unexpected", 0);
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeRow(row));
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeRow((raw + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeRow("{\"status\":null,\"status\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.parse(new byte[] {(byte) 0xc3, 0x28}));
    }

    @Test void nestedDataScalesAndCharacterMagicCannotExploitNumericEquality() throws IOException {
        ObjectNode province = golden().path("normalizers").get(3).get("input").deepCopy();
        ObjectNode data = (ObjectNode) province.path("occurrences").get(0).path("regiments").get(0).get("replenishment_records_v1");
        ObjectNode record = (ObjectNode) data.path("records").get(0);
        record.put("persistent_prepared_replenishment_fraction_scale", 100000.0);
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeProvince(province));
        record.put("persistent_prepared_replenishment_fraction_scale", 100000);
        ((ObjectNode) data.get("native_character_role_v1")).put("character_magic_1c", 0x1_0000_0000L);
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeProvince(province));
        data.putNull("native_character_role_v1");
        assertThrows(IllegalArgumentException.class, () -> LandContextCodec.decodeProvince(province));
    }

    @Test void admittedFullCdateValueIsOpaqueAndRejectedZeroStockIsKnown() throws IOException {
        JsonNode golden = golden();
        var admitted = FullLandStockPolicy.project(LandContextCodec.decodeStockInput(golden.get("base_row")));
        assertEquals(1234567890123456789L, admitted.updater().sourceNextDate().nextDateStorageRaw64());
        JsonNode rejectedVector = golden.path("stocks").get(1);
        var rejected = FullLandStockPolicy.project(LandContextCodec.decodeStockInput(merge(golden.path("base_row").deepCopy(), rejectedVector.get("patch"))));
        assertTrue(rejected.stock().ready()); assertEquals(0L, rejected.stock().raw());
        assertTrue(rejected.budget().ready()); assertEquals(0, rejected.budget().soldiers());
        assertEquals(FullLandStockProjection.ClampBranch.CAPTURED_STOCK_RETAINED_REJECTED_UPDATER, rejected.stock().clampBranch());
    }

    private static ObjectNode merge(ObjectNode target, JsonNode patch) {
        for (var property : patch.properties()) {
            JsonNode value = property.getValue(); JsonNode current = target.get(property.getKey());
            if (value.isObject() && current != null && current.isObject()) merge((ObjectNode) current, value);
            else target.set(property.getKey(), value.deepCopy());
        }
        return target;
    }
    private static JsonNode golden() throws IOException {
        try (var input = LandContextProjectionTest.class.getResourceAsStream("/landcontext/full-land-context-golden-v1.json")) {
            if (input == null) throw new IOException("tracked original complete producer golden required; no skip or runtime Python oracle");
            return JSON.readTree(input);
        }
    }
}
