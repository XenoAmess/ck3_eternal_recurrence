package org.xar.ck3.control.governance.education;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;

final class EducationDecisionComposerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode golden() throws IOException {
        try (InputStream stream = EducationDecisionComposerTest.class.getResourceAsStream("/education/producer-golden.json")) {
            assertNotNull(stream, "committed old producer golden required; no skip or Python fallback");
            return JSON.readTree(stream);
        }
    }
    private static ObjectNode input() throws IOException { return (ObjectNode) golden().get("cases").get(2).get("input").deepCopy(); }
    private static JsonNode compose(JsonNode input) throws IOException { return JSON.readTree(EducationDecisionComposer.compose(JSON.writeValueAsBytes(input))); }
    private static ObjectNode firstRead(ObjectNode input) { return (ObjectNode) input.get("child_inputs").get("rows").get(0); }

    @Test void actualOldProducerGoldenMatchesCompleteJavaOutputs() throws IOException {
        JsonNode root = golden(); assertEquals(0, root.get("provenance").get("old_producer_exit_code").intValue());
        assertEquals(5, root.get("cases").size());
        for (JsonNode testCase : root.get("cases")) { assertEquals(testCase.get("expected"), compose(testCase.get("input")), testCase.get("name").textValue()); }
    }
    @Test void signedFullIdAndDuplicateOccurrenceOrderRemainExact() throws IOException {
        JsonNode result = compose(input()); JsonNode row = result.get("education_rows").get(0);
        assertEquals(-2147483597, row.get("character_id").intValue()); assertEquals(2147483699L, row.get("raw_character_id").longValue());
        assertEquals(JSON.readTree("[0,1]"), row.get("occurrence_indices")); assertEquals(1, result.get("living_actual_child_count").intValue());
        assertEquals("保留", result.get("children").get("rows").get(0).get("values").get("legacy_extension").textValue());
    }
    @Test void boolFloatAndTextIntegerSubstitutesAreRejectedAtActualCodecBoundary() throws IOException {
        for (String raw : new String[] {"true", "100.0", "\"100\"", "null", "18446744073709551616"}) {
            ObjectNode value = input(); value.set("native_revision", JSON.readTree(raw));
            assertThrows(IllegalArgumentException.class, () -> compose(value), raw);
        }
        ObjectNode value = input(); firstRead(value).put("character_id", true);
        assertThrows(IllegalArgumentException.class, () -> compose(value));
    }
    @Test void uint64RevisionAndRawIdBoundariesDoNotUseDouble() throws IOException {
        ObjectNode value = input(); BigInteger maximum = new BigInteger("18446744073709551615");
        value.put("native_revision", maximum); ((ObjectNode) value.get("child_inputs")).put("native_revision", maximum);
        ((ObjectNode) firstRead(value).get("court_owner_source")).put("native_revision", maximum);
        assertEquals(maximum, compose(value).get("frame").get("native_revision").bigIntegerValue());
        ((ObjectNode) value.get("rows").get(0)).put("raw_character_id", 4294967296L);
        assertThrows(IllegalArgumentException.class, () -> compose(value));
    }
    @Test void missingMandatoryAndDuplicateKeysRejectWithoutInventingDefaults() throws IOException {
        ObjectNode value = input(); value.remove("native_revision"); assertThrows(IllegalArgumentException.class, () -> compose(value));
        ObjectNode another = input(); ((ObjectNode) firstRead(another).get("values")).remove("sex_selector_raw");
        assertThrows(IllegalArgumentException.class, () -> compose(another));
        byte[] duplicate = "{\"native_revision\":1,\"native_revision\":2}".getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EducationDecisionComposer.compose(duplicate));
    }
    @Test void unknownSameQueryFrameNeverRebindsChildReads() throws IOException {
        ObjectNode value = input(); ((ObjectNode) value.get("child_inputs")).put("native_revision", 101);
        JsonNode result = compose(value); JsonNode child = result.get("children").get("rows").get(0);
        assertEquals("child_inputs_frame_mismatch", child.get("leaf_availability").get("values").get("unavailable_reason").textValue());
        assertTrue(child.get("values").isNull()); assertFalse(result.get("education_rows").get(0).get("current_focus").get("available").booleanValue());
    }
    @Test void duplicateChildIdentityAndOccurrenceMismatchRetainUnavailableReasons() throws IOException {
        ObjectNode duplicate = input(); com.fasterxml.jackson.databind.node.ArrayNode rows = (com.fasterxml.jackson.databind.node.ArrayNode) duplicate.get("child_inputs").get("rows"); rows.add(rows.get(0).deepCopy());
        assertEquals("child_input_identity_duplicate", compose(duplicate).get("children").get("rows").get(0).get("leaf_availability").get("values").get("unavailable_reason").textValue());
        ObjectNode mismatch = input(); firstRead(mismatch).putArray("occurrence_indices").add(0);
        assertEquals("child_input_occurrence_group_mismatch", compose(mismatch).get("children").get("rows").get(0).get("leaf_availability").get("values").get("unavailable_reason").textValue());
    }
    @Test void absentOtherAndEducationFocusKeepTheirDistinctMeanings() throws IOException {
        ObjectNode value = input(); JsonNode absent = compose(value).get("education_rows").get(0);
        assertTrue(absent.get("current_focus").get("known_null").booleanValue()); assertTrue(absent.get("current_education_skill_inputs").isNull());
        ObjectNode focus = (ObjectNode) firstRead(value).get("native_focus"); focus.put("presence", "present").put("key", "lifestyle_martial");
        JsonNode other = compose(value).get("education_rows").get(0); assertFalse(other.get("current_focus").get("has_education_focus").booleanValue()); assertTrue(other.get("current_education_skill_inputs").isNull());
        focus.put("key", "education_learning"); JsonNode selected = compose(value).get("education_rows").get(0);
        assertEquals(selected.get("stock_skill_options").get(4), selected.get("current_education_skill_inputs"));
        assertEquals("diplomacy", selected.get("stock_skill_options").get(0).get("skill_parameter").textValue());
    }
    @Test void missingNullAndKnownNullCourtOwnerStayDistinctAcrossRoundTrip() throws IOException {
        ObjectNode value = input(); JsonNode known = compose(value);
        assertTrue(known.get("education_rows").get(0).get("current_court_owner").get("known_null").booleanValue());
        firstRead(value).putNull("court_owner_source"); JsonNode explicitNull = compose(value);
        assertTrue(explicitNull.get("children").get("rows").get(0).has("court_owner_source"));
        firstRead(value).remove("court_owner_source"); JsonNode missing = compose(value);
        assertFalse(missing.get("children").get("rows").get(0).has("court_owner_source"));
        assertEquals(missing, compose(JSON.readTree(JSON.writeValueAsBytes(value))));
    }
    @Test void wrongTraitSubsetAndCourtSourceTypeReject() throws IOException {
        ObjectNode value = input(); ((ObjectNode) firstRead(value).get("education_point_traits")).putArray("present_trait_keys").add("shrewd").add("intellect_bad_2");
        assertThrows(IllegalArgumentException.class, () -> compose(value));
        ObjectNode another = input(); ((ObjectNode) firstRead(another).get("court_owner_source")).put("identity_round_trip", 1);
        assertThrows(IllegalArgumentException.class, () -> compose(another));
    }
    @Test void unusedLegacyDecimalExtensionSurvivesWhileKnownIntegerFieldsStayStrict() throws IOException {
        ObjectNode value = input(); ((ObjectNode) firstRead(value).get("values")).set("legacy_decimal_extension", JSON.readTree("1.25"));
        assertEquals(JSON.readTree("1.25"), compose(value).get("children").get("rows").get(0).get("values").get("legacy_decimal_extension"));
        ((ObjectNode) firstRead(value).get("values")).set("age_measure_raw", JSON.readTree("10.0"));
        assertThrows(IllegalArgumentException.class, () -> compose(value));
    }
    @Test void legacyFloatOnePointZeroRemainsAFloatingTokenAfterPersistenceRoundTrip() throws IOException {
        for (String token : new String[] {"1.0", "1e0", "-0.0"}) {
            ObjectNode value = input(); ((ObjectNode) firstRead(value).get("values")).put("legacy_float_token", 0);
            String raw = JSON.writeValueAsString(value).replace("\"legacy_float_token\":0", "\"legacy_float_token\":" + token);
            JsonNode result = JSON.readTree(EducationDecisionComposer.compose(raw.getBytes(StandardCharsets.UTF_8))).get("children").get("rows").get(0).get("values").get("legacy_float_token");
            assertTrue(result.isFloatingPointNumber(), "unused SDK float must not become integer 1");
            assertEquals(Double.doubleToRawLongBits(JSON.readTree(token).doubleValue()), Double.doubleToRawLongBits(result.doubleValue()));
        }
    }
    @Test void actualMultipleChildProducerOutputExceedsMapLimitAndMatchesEntireCanonicalDigest() throws IOException, NoSuchAlgorithmException {
        JsonNode expected;
        try (InputStream stream = EducationDecisionComposerTest.class.getResourceAsStream("/education/multiple-child-producer-golden.json")) {
            assertNotNull(stream, "committed actual multiple-child producer fixture required"); expected = JSON.readTree(stream);
        }
        assertEquals(0, expected.get("producer_exit_code").intValue()); assertTrue(expected.get("source_before_after_unchanged").booleanValue());
        byte[] actual = JSON.writeValueAsBytes(sorted(compose(expected.get("input"))));
        assertTrue(actual.length > 65_536, "exercise a valid family output beyond the unrelated map byte limit");
        assertEquals(expected.get("expected_bytes").intValue(), actual.length);
        assertEquals(expected.get("expected_sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(actual)));
    }
    @Test void familyInputBudgetRemainsBoundedAndUtf8RemainsStrict() {
        assertThrows(IllegalArgumentException.class, () -> EducationDecisionComposer.compose(new byte[EducationInputCodec.INPUT_MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> EducationDecisionComposer.compose(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }
    private static JsonNode sorted(JsonNode node) {
        if (node.isObject()) {
            ObjectNode result = JSON.createObjectNode(); TreeSet<String> keys = new TreeSet<>(); node.fieldNames().forEachRemaining(keys::add);
            for (String key : keys) { result.set(key, sorted(node.get(key))); } return result;
        }
        if (node.isArray()) { com.fasterxml.jackson.databind.node.ArrayNode result = JSON.createArrayNode(); for (JsonNode child : node) { result.add(sorted(child)); } return result; }
        return node;
    }
}
