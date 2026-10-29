package org.xar.ck3.control.wave2.development.constructionincome;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

class ConstructionProvinceIncomeTest {
    @Test
    void originalAggregateObserverAndReceiptRetentionMatchAllVectors() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.constructionprovinceincome-golden/v1", golden.path("schema").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.path("machine_id").textValue());
        assertEquals(20, golden.path("cases").size());
        assertEquals("c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e",
                golden.path("source_refs").get(0).path("sha256").textValue());
        assertEquals(983, golden.path("receipt_segment_first_line").intValue());
        assertEquals(992, golden.path("receipt_segment_last_line").intValue());
        for (JsonNode row : golden.path("cases")) {
            assertEquals(row.get("expected"), StrictJson.parse(ConstructionProvinceIncomeJson.project(request(row))),
                    row.path("name").textValue());
        }
    }

    @Test
    void provinceAggregateNeedsUniqueTargetAndDoesNotFilterByBuildingOrSlot() throws IOException {
        JsonNode duplicate = projected("duplicate-matches-are-unavailable");
        assertEquals("unavailable", duplicate.path("status").textValue());
        assertTrue(duplicate.path("native_province_monthly_income_raw").isNull());
        JsonNode otherBuilding = projected("same-province-different-building-still-aggregate");
        assertEquals("observed", otherBuilding.path("status").textValue());
        assertEquals(5115, otherBuilding.path("native_province_monthly_income_raw").intValue());
        assertEquals(0, projected("zero-income-is-observed").path("native_province_monthly_income_raw").intValue());
    }

    @Test
    void strictOriginalTokenTypesCannotForgeObservedIncome() throws IOException {
        String base = new String(request(named("unique-province-aggregate")), StandardCharsets.UTF_8);
        for (String token : new String[]{"5115.0", "true", "\"5115\""}) {
            String changed = base.replace("\"native_province_monthly_income_raw\":5115",
                    "\"native_province_monthly_income_raw\":" + token);
            assertThrows(ContractViolationException.class,
                    () -> ConstructionProvinceIncomeJson.project(utf8(changed)), token);
        }
        assertThrows(ContractViolationException.class, () -> ConstructionProvinceIncomeJson.project(utf8(
                base.replace("\"native_province_monthly_income_observed\":true",
                        "\"native_province_monthly_income_observed\":1"))));
        assertThrows(ContractViolationException.class, () -> ConstructionProvinceIncomeJson.project(utf8(
                base.replace("\"barony_title_id\":2195", "\"barony_title_id\":true"))));
    }

    @Test
    void retainedPriorObjectKeepsItsOldFrameAndExtensionsWithoutInventingNewProof() throws IOException {
        JsonNode row = named("completed-cold-retains-equal-completion-date");
        String raw = new String(request(row), StandardCharsets.UTF_8)
                .replace("\"keep\":true", "\"keep\":true,\"decimal\":1.25");
        JsonNode original = StrictJson.parse(utf8(raw)).path("prior_receipt").path("construction_province_income_observation");
        JsonNode output = StrictJson.parse(ConstructionProvinceIncomeJson.project(utf8(raw)));
        assertEquals(original, output);
        assertEquals("native:2", output.path("snapshot_id").textValue());
        assertFalse(output.has("replay_allowed"));
        assertFalse(output.has("material_postcondition_verified"));
        JsonNode legacy = projected("retention-copies-prior-not-new-qualification");
        assertFalse(legacy.has("native_province_monthly_income_raw"), "do not manufacture missing old evidence");
    }

    @Test
    void wrapperMissingFieldsDuplicatesAndTrailingDataReject() throws IOException {
        String raw = new String(request(named("unique-province-aggregate")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class,
                () -> ConstructionProvinceIncomeJson.project(utf8(raw + " {}")));
        assertThrows(ContractViolationException.class, () -> ConstructionProvinceIncomeJson.project(utf8(
                raw.replaceFirst("\\{", "{\"unexpected\":true,"))));
        assertThrows(ContractViolationException.class, () -> ConstructionProvinceIncomeJson.project(utf8(
                raw.replaceFirst("\\{", "{\"operation\":\"observe\","))));
        ObjectNode missing = (ObjectNode) StrictJson.parse(utf8(raw));
        missing.remove("source_frame");
        assertThrows(ContractViolationException.class,
                () -> ConstructionProvinceIncomeJson.project(StrictJson.canonical(missing)));
        assertThrows(ContractViolationException.class,
                () -> ConstructionProvinceIncomeJson.project(new byte[]{(byte) 0xc3, 0x28}));
    }

    private static JsonNode projected(String name) throws IOException {
        return StrictJson.parse(ConstructionProvinceIncomeJson.project(request(named(name))));
    }
    private static byte[] request(JsonNode row) {
        ObjectNode request = (ObjectNode) row.deepCopy();
        request.remove("name");
        request.remove("expected");
        request.put("schema", ConstructionProvinceIncomeJson.SCHEMA);
        return StrictJson.canonical(request);
    }
    private static JsonNode named(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (name.equals(row.path("name").textValue())) { return row; }
        }
        throw new IllegalStateException("missing province income golden: " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ConstructionProvinceIncomeTest.class.getResourceAsStream("/constructionincome/province-golden.json")) {
            assertNotNull(stream, "original province observer/consumer capture is required");
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
