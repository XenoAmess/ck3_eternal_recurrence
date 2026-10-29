package org.xar.ck3.control.wave2.finance.factionculture;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.wave2.finance.factionculture.FactionCultureModel.*;

final class FactionCulturePolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @TestFactory
    List<DynamicTest> actualOriginalNormalizerProjectionAndConsumerGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java.faction-culture-producer-golden/v1", golden.path("schema").textValue());
        assertEquals(10, golden.path("original_unit_tests_run").intValue());
        assertEquals(0, golden.path("original_unit_tests_skipped").intValue());
        assertEquals(0, golden.path("capture").path("native_rpc_count").intValue());
        assertTrue(golden.path("cases").size() >= 35);
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.path("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.path("name").textValue(), () -> {
                byte[] input = JSON.writeValueAsBytes(vector.path("input"));
                if (!vector.path("accepted").booleanValue()) {
                    assertThrows(IllegalArgumentException.class, () -> FactionCultureCodec.normalizeRelation(input, "county"));
                } else if (vector.path("operation").textValue().equals("normalize")) {
                    Optional<CultureRelation> relation = FactionCultureCodec.normalizeRelation(input, "county");
                    byte[] encoded = FactionCultureCodec.encodeRelation(relation);
                    assertEquals(vector.path("expected"), JSON.readTree(encoded));
                    assertEquals(relation, FactionCultureCodec.normalizeRelation(encoded, "county"));
                } else {
                    Context context = FactionCultureCodec.projectNormalizedAlert(input);
                    byte[] encoded = FactionCultureCodec.encodeContext(context);
                    assertEquals(vector.path("expected"), JSON.readTree(encoded));
                    assertEquals(context.relationInputReady(), context.status() == ContextStatus.AVAILABLE);
                    assertEquals(JSON.readTree(encoded), JSON.readTree(FactionCultureCodec.encodeContext(
                            FactionCultureCodec.projectNormalizedAlert(JSON.writeValueAsBytes(JSON.readTree(input))))));
                }
            }));
        }
        return List.copyOf(tests);
    }

    @Test
    void fullSignedCultureIdentitiesUseEveryBitAndZeroIsNotMissing() {
        assertEquals(Optional.of(new AvailableCulture(0, 0, true)), normalize(
                "{\"county_culture_id\":0,\"target_culture_id\":0,\"same_culture_as_target\":true,\"culture_relation_status\":\"available\"}"));
        assertEquals(Optional.of(new AvailableCulture(Integer.MIN_VALUE, Integer.MAX_VALUE, false)), normalize(
                "{\"county_culture_id\":-2147483648,\"target_culture_id\":2147483647,\"same_culture_as_target\":false,\"culture_relation_status\":\"available\"}"));
        assertThrows(IllegalArgumentException.class, () -> new AvailableCulture(16_777_217, 33_554_433, true));
        assertThrows(IllegalArgumentException.class, () -> new AvailableCulture(-1, 0, false));
        assertThrows(IllegalArgumentException.class, () -> new UnavailableCulture(Optional.of(0), Optional.of(-2)));
    }

    @Test
    void rawFloatBooleanStringAndPartialGroupAreRejectedBeforeModelConstruction() {
        String valid = "{\"county_culture_id\":0,\"target_culture_id\":0,\"same_culture_as_target\":true,\"culture_relation_status\":\"available\"}";
        assertThrows(IllegalArgumentException.class, () -> normalize(valid.replace("\"county_culture_id\":0", "\"county_culture_id\":0.0")));
        assertThrows(IllegalArgumentException.class, () -> normalize(valid.replace("\"county_culture_id\":0", "\"county_culture_id\":false")));
        assertThrows(IllegalArgumentException.class, () -> normalize(valid.replace("\"county_culture_id\":0", "\"county_culture_id\":\"0\"")));
        assertThrows(IllegalArgumentException.class, () -> normalize(valid.replace("\"target_culture_id\":0,", "")));
        assertThrows(IllegalArgumentException.class, () -> normalize(valid.replace("\"county_culture_id\":0", "\"county_culture_id\":2147483648")));
    }

    @Test
    void legacyAbsenceDiffersFromObservedUnavailableAndOtherCountyFieldsRemainOuterContract() throws IOException {
        assertEquals(Optional.empty(), normalize("{\"county_title_id\":50331649,\"unconsumed_extension\":[null,false]}"));
        Optional<CultureRelation> observedUnknown = normalize(
                "{\"county_culture_id\":null,\"target_culture_id\":-2,\"same_culture_as_target\":null,\"culture_relation_status\":\"unavailable\"}");
        assertEquals(Optional.of(new UnavailableCulture(Optional.empty(), Optional.of(-2))), observedUnknown);
        assertEquals(0, JSON.readTree(FactionCultureCodec.encodeRelation(Optional.empty())).size());
        assertEquals(4, JSON.readTree(FactionCultureCodec.encodeRelation(observedUnknown)).size());
    }

    @Test
    void projectionDoesNotMergeOneCountyAcrossFactionsOrExposeMutableSourceBytes() throws IOException {
        JsonNode vector = vector("projection-same-county-distinct-factions-not-merged");
        Context context = FactionCultureCodec.projectNormalizedAlert(JSON.writeValueAsBytes(vector.path("input")));
        assertEquals(2, context.rows().size());
        assertEquals(context.rows().get(0).countyTitleId(), context.rows().get(1).countyTitleId());
        assertFalse(context.rows().get(0).factionId() == context.rows().get(1).factionId());
        byte[] bytes = context.provenance().json();
        bytes[0] = 0;
        assertEquals(vector.path("expected").path("provenance"), JSON.readTree(context.provenance().json()));
        assertThrows(UnsupportedOperationException.class, () -> context.rows().clear());
    }

    @Test
    void duplicateMalformedJsonAndInconsistentTypedReadinessDoNotBecomeAvailable() {
        assertThrows(IllegalArgumentException.class, () -> normalize("{\"county_culture_id\":0,\"county_culture_id\":1}"));
        assertThrows(IllegalArgumentException.class, () -> normalize("{} {}"));
        assertThrows(IllegalArgumentException.class, () -> FactionCultureCodec.normalizeRelation(new byte[]{'{', '"', (byte) 0xC3, '"', ':', '0', '}'}));
        assertThrows(IllegalArgumentException.class, () -> FactionCultureCodec.normalizeRelation(new byte[FactionCultureCodec.MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> new ContextRow(1, "populist_faction", 2, 3,
                Optional.of(new AvailableCulture(0, 0, true)), Optional.of(UnavailableReason.CULTURE_RELATION_UNAVAILABLE)));
    }

    @Test
    void opaqueProvenanceDecimalsKeepExactMagnitudeAndFloatingDomain() throws IOException {
        ObjectNode input = (ObjectNode) vector("projection-same-county-distinct-factions-not-merged").path("input").deepCopy();
        ((ObjectNode) input.path("provenance")).putNull("decimal_extension");
        String wire = JSON.writeValueAsString(input).replace("\"decimal_extension\":null",
                "\"decimal_extension\":{\"zero\":0e0,\"fraction\":0.12345678901234567890123456789,\"huge\":1e400}");
        Context context = FactionCultureCodec.projectNormalizedAlert(wire.getBytes(StandardCharsets.UTF_8));
        ObjectMapper exact = new ObjectMapper().enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
        JsonNode extension = exact.readTree(FactionCultureCodec.encodeContext(context)).path("provenance").path("decimal_extension");
        assertTrue(extension.path("zero").isFloatingPointNumber());
        assertTrue(extension.path("huge").isFloatingPointNumber());
        assertEquals(0, new BigDecimal("0.12345678901234567890123456789").compareTo(extension.path("fraction").decimalValue()));
        assertEquals(0, new BigDecimal("1e400").compareTo(extension.path("huge").decimalValue()));
    }

    private static Optional<CultureRelation> normalize(String json) {
        return FactionCultureCodec.normalizeRelation(json.getBytes(StandardCharsets.UTF_8), "county");
    }

    private static JsonNode vector(String name) throws IOException {
        for (JsonNode vector : golden().path("cases")) if (vector.path("name").textValue().equals(name)) return vector;
        throw new IllegalArgumentException("missing original producer vector " + name);
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = FactionCulturePolicyTest.class.getResourceAsStream("/factionculture/python-golden-v1.json")) {
            assertNotNull(input, "committed actual original producer golden required");
            byte[] bytes = input.readNBytes(70_001);
            assertTrue(bytes.length <= 70_000, "culture golden budget");
            return JSON.readTree(bytes);
        }
    }
}
