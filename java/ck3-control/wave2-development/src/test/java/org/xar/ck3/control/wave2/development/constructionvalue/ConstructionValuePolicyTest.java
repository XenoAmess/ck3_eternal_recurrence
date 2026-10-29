package org.xar.ck3.control.wave2.development.constructionvalue;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.OptionalInt;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.*;

final class ConstructionValuePolicyTest {
    @TestFactory
    Stream<DynamicTest> comparesEveryAuthoredKeyAndExactBuildWithTheUnchangedProducer() throws IOException {
        JsonNode golden = golden();
        return StreamSupport.stream(golden.get("lookup_matrix").spliterator(), false).flatMap(row -> {
            List<DynamicTest> tests = new ArrayList<>();
            for (int index = 0; index < golden.get("builds").size(); index++) {
                String build = golden.get("builds").get(index).textValue();
                for (String kind : List.of("target", "existing")) {
                    JsonNode expected = row.get(kind).get(index);
                    tests.add(DynamicTest.dynamicTest(kind + ":" + build + ":" + row.get("key").textValue(), () -> {
                        String raw = "{\"schema\":\"xar.construction-authored-income-input.v1\",\"kind\":\"" + kind
                                + "\",\"building_key\":\"" + row.get("key").textValue() + "\",\"exact_ck3_build\":\"" + build + "\"}";
                        JsonNode actual = StrictJson.parse(ConstructionValueCodec.lookup(utf8(raw))).get("authored_monthly_income_hundredths");
                        assertEquals(expected, actual);
                    }));
                }
            }
            return tests.stream();
        });
    }

    @TestFactory
    Stream<DynamicTest> preservesDefaultBuildUnknownKeyAndMissingNullLookupResults() throws IOException {
        return StreamSupport.stream(golden().get("lookup_cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertEquals(row.get("expected"), StrictJson.parse(ConstructionValueCodec.lookup(utf8(row.get("input_json").textValue()))))));
    }

    @TestFactory
    Stream<DynamicTest> comparesTheCompleteCandidateSelectorAndOutputRoundTrip() throws IOException {
        JsonNode root = golden(); assertEquals(34, root.get("cases").size());
        return StreamSupport.stream(root.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            byte[] raw = utf8(row.get("input_json").textValue());
            if (row.get("java_strict_reject").booleanValue()) { assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.select(raw)); return; }
            byte[] actual = ConstructionValueCodec.select(raw); assertEquals(row.get("expected"), StrictJson.parse(actual));
            assertEquals(ConstructionValuePolicy.select(ConstructionValueCodec.decodeSelection(raw)), ConstructionValueCodec.decodeSelectionResult(actual));
        }));
    }

    @TestFactory
    Stream<DynamicTest> comparesActualOriginalQueryConsumersIncludingCoverageAndPositiveUpgrades() throws IOException {
        return StreamSupport.stream(golden().get("consumer_cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertEquals(row.get("expected"), StrictJson.parse(ConstructionValueCodec.consumeSelection(utf8(row.get("input_json").textValue()))))));
    }

    @Test
    void bindsSourceIdentityExistingDowngradeRegressionAndHistoricalMaterialScope() throws IOException {
        JsonNode root = golden();
        boolean referenceV2 = referenceCaptureV2(root, "xar.construction-value-original-producer-golden");
        assertEquals("xenoamess-full-tower-eb9d2c1186", root.get("machine_id").textValue()); StrictJson.utc(root.get("observed_at_utc").textValue());
        assertEquals("c735cc676756563db9a4e72d85c217f50d3e8b1fdaac33047d0a88f9b9b42a10", root.get("source_refs").get(0).get("sha256").textValue());
        assertEquals("c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e", root.get("source_refs").get(1).get("sha256").textValue());
        if (referenceV2) { requiresActualHostModule(root, "existing_tests", "test_construction_same_slot_value_v1.py"); }
        else {
            assertEquals(5, root.get("existing_tests").get("run").intValue());
            for (String field : List.of("failures", "errors", "skipped")) { assertEquals(0, root.get("existing_tests").get(field).intValue()); }
        }
        assertEquals("unknown", root.get("actual_material_provenance").get("machine_id").textValue());
        assertEquals("4fd9fa8b7fb971b6473fd80f2beb3abccf12edfc63bb38f5f56dcc3360fcb662", root.get("actual_material_provenance").get("sha256").textValue());
        assertTrue(root.get("actual_material_provenance").get("available_original_not_reverified").booleanValue());
        assertTrue(root.get("consumer_cases").size() >= 15);
        assertTrue(root.get("lookup_matrix").size() >= 155);
    }

    @Test
    void preservesAuthoredGrossDeltaAndActualNativeQuoteAsDifferentValues() throws IOException {
        Candidate positive = selectedCase("separate_gross_and_positive_delta");
        assertEquals(50, positive.authoredIncomeHundredths()); assertEquals(15, positive.authoredIncomeDeltaHundredths());
        assertEquals(35, positive.oldAuthoredIncomeHundredths()); assertEquals("pastures_01", positive.oldBuildingKey()); assertFalse(positive.slotWasEmpty());
        Candidate actual = selectedCase("actual_downgrade_yields_to_empty_cereal");
        assertEquals("cereal_fields_01", actual.buildingKey()); assertEquals(new BigInteger("14250000"), actual.stockGoldCost());
        assertEquals(new BigInteger("120659426"), actual.goldBefore()); assertTrue(actual.slotWasEmpty());
        assertNotEquals(actual.stockGoldCost(), BigInteger.valueOf(actual.authoredIncomeHundredths()));
    }

    @Test
    void keepsUnsupportedBuildsAndHigherTiersOutWithoutExtrapolatingValues() {
        assertEquals(OptionalInt.empty(), AuthoredConstructionIncome.target(Field.of("farm_estates_08"), Build.V12003));
        assertEquals(OptionalInt.of(385), AuthoredConstructionIncome.target(Field.of("farm_estates_08"), Build.V12004));
        assertEquals(OptionalInt.empty(), AuthoredConstructionIncome.target(Field.of("farm_estates_09"), Build.V12004));
        assertEquals(OptionalInt.of(0), AuthoredConstructionIncome.existing(Field.of("military_camps_01"), Build.V12003));
        assertEquals(OptionalInt.empty(), AuthoredConstructionIncome.target(Field.of("military_camps_01"), Build.V12004));
        assertEquals(OptionalInt.empty(), AuthoredConstructionIncome.existing(Field.of("farm_estates_01"), Build.UNSUPPORTED));
    }

    @Test
    void rejectsOriginalFloatExponentBooleanAndStringIdentityAndCashTokens() throws IOException {
        String original = caseRow("actual_downgrade_yields_to_empty_cereal").get("input_json").textValue();
        for (String token : List.of("604.0", "604e0", "true", "\"604\"")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.select(utf8(original.replace("\"building_type_id\":604", "\"building_type_id\":" + token))), token);
        }
        for (String token : List.of("120659426.0", "120659426e0", "true", "\"120659426\"", "9223372036854775808")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.select(utf8(original.replace("\"player_gold_raw\":120659426", "\"player_gold_raw\":" + token))), token);
        }
        for (String token : List.of("true", "4.0", "4e0", "\"4\"")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.select(utf8(original.replace("\"slot_index\":4", "\"slot_index\":" + token))), token);
        }
    }

    @Test
    void preservesMissingNullEmptyAndCopiesQuoteCollections() {
        SelectionInput missing = ConstructionValueCodec.decodeSelection(utf8("{\"schema\":\"xar.construction-value-selection-input.v1\",\"world\":{}}"));
        SelectionInput nil = ConstructionValueCodec.decodeSelection(utf8("{\"schema\":\"xar.construction-value-selection-input.v1\",\"world\":{\"completed_buildings\":null}}"));
        SelectionInput empty = ConstructionValueCodec.decodeSelection(utf8("{\"schema\":\"xar.construction-value-selection-input.v1\",\"world\":{\"completed_buildings\":[]}}"));
        assertEquals(Presence.MISSING, missing.world().completed().presence()); assertEquals(Presence.NULL, nil.world().completed().presence());
        assertEquals(List.of(), empty.world().completed().value()); assertNotEquals(missing, nil); assertNotEquals(nil, empty);
        ArrayList<Sample> mutable = new ArrayList<>();
        World world = new World(Field.of(BigInteger.valueOf(50_000_000)), Field.of(List.of()), Field.of(mutable), Field.of(true), Field.of(List.of()), Field.of(true));
        mutable.clear(); assertThrows(UnsupportedOperationException.class, () -> world.samples().value().clear());
        assertInstanceOf(NoCandidate.class, ConstructionValuePolicy.select(new SelectionInput(world, Build.V12004)));
    }

    @Test
    void rejectsMalformedWrapperDuplicateKeysTrailingBytesAndInventedCandidateGain() throws IOException {
        String raw = caseRow("actual_downgrade_yields_to_empty_cereal").get("input_json").textValue();
        assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.decodeSelection(utf8(raw + " {}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.decodeSelection(utf8(raw.replace("\"schema\":", "\"schema\":\"duplicate\",\"schema\":"))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.decodeSelection(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.decodeSelection(new byte[ConstructionValueCodec.MAX_BYTES + 1]));
        String output = new String(ConstructionValueCodec.select(utf8(raw)), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.decodeSelectionResult(utf8(output.replace("\"authored_monthly_income_delta_hundredths\":50", "\"authored_monthly_income_delta_hundredths\":49"))));
        assertThrows(IllegalArgumentException.class, () -> ConstructionValueCodec.decodeSelectionResult(utf8(output.substring(0, output.length() - 1) + ",\"extra\":true}")));
    }

    private static Candidate selectedCase(String name) throws IOException {
        return assertInstanceOf(Selected.class, ConstructionValuePolicy.select(ConstructionValueCodec.decodeSelection(utf8(caseRow(name).get("input_json").textValue())))).candidate();
    }
    private static JsonNode caseRow(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return row; } }
        throw new IOException("missing required actual producer case " + name);
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = ConstructionValuePolicyTest.class.getResourceAsStream("/constructionvalue/original-producer-golden-v1.json")) {
            if (input == null) { throw new IOException("required actual producer golden unavailable; capture is never a default test fallback"); }
            return StrictJson.parse(input.readAllBytes(), 90_000);
        }
    }
    private static boolean referenceCaptureV2(JsonNode root, String baseSchema) {
        String schema = root.path("schema").asText();
        if ((baseSchema + ".v1").equals(schema)) { return false; }
        assertEquals(baseSchema + ".v2", schema, "unsupported reference capture version");
        assertEquals("REFERENCE_ORACLE", root.path("producer_role").asText());
        assertEquals("REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE", root.path("current_consumer_validation").asText());
        return true;
    }

    private static void requiresActualHostModule(JsonNode root, String field, String module) {
        JsonNode evidence = root.path(field);
        assertTrue(evidence.isObject());
        assertEquals("NOT_EXECUTED_REFERENCE_CAPTURE", evidence.path("status").asText());
        assertEquals(1, evidence.path("required_actual_host_modules").size());
        assertEquals(module, evidence.path("required_actual_host_modules").get(0).asText());
        for (String oldCredit : new String[]{"completed", "run", "failures", "errors", "skipped"}) {
            assertFalse(evidence.has(oldCredit), "reference producer cannot claim a current consumer run");
        }
    }

}
