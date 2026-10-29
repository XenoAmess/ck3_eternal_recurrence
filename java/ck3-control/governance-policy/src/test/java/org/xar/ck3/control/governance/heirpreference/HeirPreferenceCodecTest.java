package org.xar.ck3.control.governance.heirpreference;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.CandidateId;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.ComparisonRow;
import org.xar.ck3.control.governance.heirpreference.HeirReproductivePreference.ObservedComparison;

final class HeirPreferenceCodecTest {
    @Test
    void matchesEightCapturedActualProducerCasesAndRoundTripsWithoutPython() throws IOException {
        JsonNode golden;
        try (InputStream input = getClass().getResourceAsStream("/heirpreference/producer-golden.json")) {
            if (input == null) {
                throw new IOException("committed producer golden is required");
            }
            golden = StrictJson.parse(input.readAllBytes());
        }
        assertEquals("e8b7e439e273593b902883b7e412fba05f2bd84aa3e814c831f535bb482ef0a9",
                golden.path("producer").path("sha256").textValue());
        assertEquals(8, golden.path("cases").size());
        for (JsonNode vector : golden.path("cases")) {
            byte[] original = StrictJson.canonical(vector.path("input"));
            byte[] request = original.clone();
            byte[] actual = HeirPreferenceCodec.prioritize(request);
            assertArrayEquals(StrictJson.canonical(vector.path("expected")), actual,
                    vector.path("name").textValue());
            assertEquals(vector.path("expected"), StrictJson.parse(actual));
            assertArrayEquals(actual, StrictJson.canonical(StrictJson.parse(actual)));
            assertArrayEquals(original, request, "producer cannot mutate caller input");
            assertEquals(vector.path("input").path("choices").size(), StrictJson.parse(actual).size());
        }
    }

    @Test
    void pureOrderingIsStableAndNeitherFailureNorMissingObservationExcludesAChoice() {
        CandidateId one = id(1);
        CandidateId two = id(2);
        CandidateId three = id(3);
        List<CandidateId> choices = new ArrayList<>(List.of(one, two, three, one));
        List<ComparisonRow> rows = List.of(
                new ComparisonRow(one, ObservedComparison.FAIL, ObservedComparison.PASS),
                new ComparisonRow(three, ObservedComparison.PASS, ObservedComparison.PASS));
        var result = HeirReproductivePreference.prioritize(choices, rows);
        assertEquals(List.of(2, 1, 0, 3), result.stream().map(
                HeirReproductivePreference.PreferredChoice::originalOrdinal).toList());
        assertEquals(List.of(one, two, three, one), choices);
        assertEquals(4, result.size());
        assertFalse(result.get(2).ageConsidered(), "floor failure skips the unused age branch");
        assertThrows(UnsupportedOperationException.class, result::clear);
    }

    @Test
    void candidateIdentifiersRejectBooleanFloatStringNullMissingZeroAndNegative() {
        for (String wrong : List.of("true", "false", "1.0", "1e0", "\"1\"", "null", "0", "-1")) {
            rejected("{\"choices\":[{\"candidate_character_id\":" + wrong + "}],\"rows\":[]}");
            rejected("{\"choices\":[],\"rows\":[{\"candidate_character_id\":" + wrong + "}]}");
        }
        rejected("{\"choices\":[{}],\"rows\":[]}");
        rejected("{\"choices\":[],\"rows\":[{}]}");
    }

    @Test
    void exactLargeIdentifiersDoNotEnterJavaScriptOrSignedLongDomains() {
        for (String exact : List.of("9007199254740993", "18446744073709551615", "18446744073709551616")) {
            JsonNode output = StrictJson.parse(HeirPreferenceCodec.prioritize(bytes(
                    "{\"choices\":[{\"candidate_character_id\":" + exact + "}],\"rows\":[]}")));
            assertEquals(new BigInteger(exact), output.get(0).get("candidate_character_id").bigIntegerValue());
            assertEquals(new BigInteger(exact), output.get(0).get(HeirReproductivePreference.BASIS)
                    .get("candidate_character_id").bigIntegerValue());
        }
    }

    @Test
    void exactNewWrapperRejectsMissingMisspelledUnknownOrWrongContainerFields() {
        for (String wrong : List.of("{}", "{\"choices\":[]}", "{\"rows\":[]}",
                "{\"choices\":[],\"row\":[]}", "{\"choices\":[],\"rows\":[],\"ready\":true}",
                "{\"choices\":null,\"rows\":[]}", "{\"choices\":{},\"rows\":[]}",
                "{\"choices\":[],\"rows\":null}", "{\"choices\":[1],\"rows\":[]}",
                "{\"choices\":[],\"rows\":[null]}")) {
            rejected(wrong);
        }
    }

    @Test
    void comparisonFlagsDoNotCoerceIntegerStringArrayOrObjectToBoolean() {
        for (String field : List.of("ready", "passes")) {
            for (String wrong : List.of("1", "0", "1.0", "\"true\"", "[]", "{}")) {
                rejected("{\"choices\":[{\"candidate_character_id\":1}],\"rows\":[{"
                        + "\"candidate_character_id\":1,\"candidate_native_fertility_floor_comparison_v1\":{\""
                        + field + "\":" + wrong + "}}]}");
            }
        }
        rejected("{\"choices\":[],\"rows\":[{\"candidate_character_id\":1,"
                + "\"candidate_native_scorer_age_branch_v1\":true}]}");
    }

    @Test
    void absenceNullAndEmptyComparisonObjectHaveEqualUnknownClassButDistinctEvidence() {
        JsonNode output = StrictJson.parse(HeirPreferenceCodec.prioritize(bytes("""
                {"choices":[{"candidate_character_id":1},{"candidate_character_id":2},{"candidate_character_id":3}],
                 "rows":[{"candidate_character_id":1},
                         {"candidate_character_id":2,"candidate_native_fertility_floor_comparison_v1":null},
                         {"candidate_character_id":3,"candidate_native_fertility_floor_comparison_v1":{}}]}
                """)));
        assertTrue(output.get(0).get(HeirReproductivePreference.BASIS).get("floor_comparison").isNull());
        assertTrue(output.get(1).get(HeirReproductivePreference.BASIS).get("floor_comparison").isNull());
        assertTrue(output.get(2).get(HeirReproductivePreference.BASIS).get("floor_comparison").isObject());
        assertEquals(0, output.get(2).get(HeirReproductivePreference.BASIS).get("floor_comparison").size());
        for (JsonNode choice : output) {
            assertEquals(1, choice.get(HeirReproductivePreference.BASIS).get("preference_class").intValue());
        }
    }

    @Test
    void rejectsMoreThanExistingFiveCandidatesAndUnboundedPayloads() {
        ObjectNode root = StrictJson.object();
        ArrayNode choices = root.putArray("choices");
        root.putArray("rows");
        for (int index = 1; index <= 6; index++) {
            choices.addObject().put("candidate_character_id", index);
        }
        assertThrows(ContractViolationException.class,
                () -> HeirPreferenceCodec.prioritize(StrictJson.canonical(root)));
        root.set("rows", choices);
        root.putArray("choices");
        assertThrows(ContractViolationException.class,
                () -> HeirPreferenceCodec.prioritize(StrictJson.canonical(root)));
        assertThrows(ContractViolationException.class,
                () -> HeirPreferenceCodec.prioritize(new byte[StrictJson.INPUT_MAX_BYTES + 1]));
    }

    @Test
    void rejectsDuplicateKeysTrailingContentInvalidUtf8AndFloatMetadata() {
        rejected("{\"choices\":[],\"choices\":[],\"rows\":[]}");
        rejected("{\"choices\":[],\"rows\":[]} {} ");
        rejected("{\"choices\":[{\"candidate_character_id\":1,\"candidate_character_id\":2}],\"rows\":[]}");
        rejected("{\"choices\":[{\"candidate_character_id\":1,\"ratio\":0.5}],\"rows\":[]}");
        rejected("{\"choices\":[],\"rows\":[{\"candidate_character_id\":1,\"unused_ratio\":0.5}]}");
        assertThrows(ContractViolationException.class,
                () -> HeirPreferenceCodec.prioritize(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void modelConstructorsDoNotAdmitInvalidIdsOrNullComparisonStates() {
        assertThrows(IllegalArgumentException.class, () -> new CandidateId(BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> new CandidateId(BigInteger.valueOf(-1)));
        assertThrows(NullPointerException.class, () -> new CandidateId(null));
        assertThrows(NullPointerException.class, () -> new ComparisonRow(id(1), null, ObservedComparison.PASS));
    }

    private static CandidateId id(long value) { return new CandidateId(BigInteger.valueOf(value)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static void rejected(String input) {
        assertThrows(ContractViolationException.class, () -> HeirPreferenceCodec.prioritize(bytes(input)), input);
    }
}
