package org.xar.ck3.control.wave2.planning.savedcountymembership;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.wave2.planning.scoretarget.ScalarField;

final class SavedCountyMembershipTest {
    private static final String RESOURCE = "/savedcountymembership/membership_python_v1.jsonl";
    private static final Set<String> ORIGINAL_METHODS = Set.of(
            "test_complete_realm_and_explicit_foreign_root_remain_exact_and_source_bound",
            "test_missing_liege_or_cycle_is_unknown_not_false_or_precise_shrinkage",
            "test_true_out_of_realm_chain_is_not_over_rejected",
            "test_unknown_geography_never_counts_dynamic_or_unmapped_county_as_land",
            "test_invalid_mapping_or_duplicate_county_key_is_unknown",
            "test_conflicting_holder_or_liege_cannot_be_treated_as_outside",
            "test_missing_cyclic_or_conflicting_house_path_is_not_zero_or_half_price",
            "test_cached_foreign_house_does_not_hide_parent_dynasty_conflict",
            "test_complete_lowborn_and_real_other_dynasty_are_known_exclusions",
            "test_unknown_decoder_field_or_missing_title_census_never_yields_exact_zero",
            "test_incomplete_T0_known_subset_cannot_become_dynasty_outside_cap");


    @Test void javaMembershipContinuesEveryOriginalSavedReaderConsumerMethod() throws Exception {
        JsonNode result = SavedMembershipGoldenExporter.verifyOriginalConsumers();
        assertEquals("PASS", result.path("status").textValue());
        assertEquals(11, result.path("tests").intValue());
        assertTrue(result.path("complete_consumer_comparisons").intValue() > 0);
    }

    @TestFactory
    Stream<DynamicTest> completeOriginalMembershipProducerAndConsumerLineages() throws IOException {
        return corpus().rows().stream().map(row -> DynamicTest.dynamicTest(row.path("ordinal").asText() + ":" + row.path("captured_in"), () -> {
            JsonNode input = row.get("input_json"); assertTrue(input != null && input.isTextual());
            byte[] raw = bytes(input.textValue()); assertTrue(raw.length > 0 && raw.length <= 65536);
            byte[] expected = StrictJson.canonical(row.get("expected"));
            assertArrayEquals(expected, SavedMembershipCodec.evaluate(raw));
            ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class,
                    org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.registeredResult(
                            new org.xar.ck3.control.wave2.planning.scoretarget.SavedScoreProjectionPortCatalog().registrations().stream()
                                    .filter(port -> port.operation() == org.xar.ck3.control.contracts.projection.ProjectionOperation.SAVED_COUNTY_MEMBERSHIP_AUDIT)
                                    .findFirst().orElseThrow(), raw));
            assertArrayEquals(expected, succeeded.result().bytes());
        }));
    }

    @Test
    void originalElevenMethodsAndBothOrderedCycleProofsArePresent() throws IOException {
        Corpus corpus = corpus(); JsonNode header = corpus.header();
        assertEquals("g2.saved-county-membership-python-golden/v1", header.path("schema").textValue());
        assertEquals(11, header.path("original_tests_run").intValue());
        assertEquals(0, header.path("original_skips").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertFalse(header.path("production_consumer_switched").booleanValue());
        StrictJson.utc(StrictJson.text(header.get("observed_at_utc"))); StrictJson.text(header.get("machine_id"));
        assertEquals("ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e",
                header.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py").textValue());
        assertEquals("db3c8595021908f58162b51eb0c4b9324a1f98ed8d0e19461741c13e3cd2acf7",
                header.path("source_sha256").path("ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py").textValue());
        Set<String> captured = new HashSet<>(); int ordinal = 0;
        for (JsonNode row : corpus.rows()) {
            assertEquals(++ordinal, row.path("ordinal").intValue());
            row.path("captured_in").forEach(value -> captured.add(StrictJson.text(value)));
        }
        assertEquals(ordinal, header.path("unique_vector_count").intValue());
        assertTrue(captured.containsAll(ORIGINAL_METHODS));
        assertTrue(captured.containsAll(Set.of("cycle-terminal-stream-order-forward", "cycle-terminal-stream-order-reverse",
                "province-type-or-range-bool", "province-type-or-range-float", "null-liege-is-present-invalid")));
    }

    @Test
    void explicitSourceOrderSurvivesJsonObjectCanonicalization() throws IOException {
        for (String label : List.of("cycle-terminal-stream-order-forward", "cycle-terminal-stream-order-reverse")) {
            JsonNode row = vector(label); byte[] original = bytes(row.path("input_json").textValue());
            byte[] reorderedObjects = StrictJson.canonical(StrictJson.parse(original));
            assertArrayEquals(SavedMembershipCodec.evaluate(original), SavedMembershipCodec.evaluate(reorderedObjects));
        }
        JsonNode forward = StrictJson.parse(SavedMembershipCodec.evaluate(bytes(vector("cycle-terminal-stream-order-forward").path("input_json").textValue())));
        JsonNode reverse = StrictJson.parse(SavedMembershipCodec.evaluate(bytes(vector("cycle-terminal-stream-order-reverse").path("input_json").textValue())));
        assertEquals(BigInteger.valueOf(100), forward.path("states").path("100").path("realm_terminal_title_id").bigIntegerValue());
        assertEquals(BigInteger.valueOf(101), reverse.path("states").path("100").path("realm_terminal_title_id").bigIntegerValue());
    }

    @Test
    void missingNullAndEmptyArePreservedWithoutTurningUnknownIntoForeign() throws IOException {
        ObjectNode input = base(); ObjectNode title = object(object(input, "projection"), "titles");
        ObjectNode row = object(title, "101"); row.remove("de_facto_liege");
        SavedMembershipInput missing = SavedMembershipCodec.decode(wire(input));
        assertTrue(missing.projection().titles().get(BigInteger.valueOf(101)).liege() instanceof ScalarField.Missing);
        assertEquals(SavedMembershipResult.Truth.NO, SavedCountyMembership.audit(missing).states().get(BigInteger.valueOf(101)).realm().membership());
        row.putNull("de_facto_liege"); SavedMembershipInput explicitNull = SavedMembershipCodec.decode(wire(input));
        assertTrue(explicitNull.projection().titles().get(BigInteger.valueOf(101)).liege() instanceof ScalarField.NullValue);
        assertEquals(SavedMembershipResult.Truth.UNKNOWN, SavedCountyMembership.audit(explicitNull).states().get(BigInteger.valueOf(101)).realm().membership());
        row.remove("key"); assertTrue(SavedMembershipCodec.decode(wire(input)).projection().titles().get(BigInteger.valueOf(101)).key() instanceof ScalarField.Missing);
        row.putNull("key"); assertTrue(SavedMembershipCodec.decode(wire(input)).projection().titles().get(BigInteger.valueOf(101)).key() instanceof ScalarField.NullValue);
        ObjectNode metadata = object(object(input, "projection"), "metadata");
        metadata.remove("date"); assertTrue(SavedMembershipCodec.decode(wire(input)).projection().date() instanceof ScalarField.Missing);
        metadata.putNull("date"); assertTrue(SavedMembershipCodec.decode(wire(input)).projection().date() instanceof ScalarField.NullValue);
    }

    @Test
    void rawFractionAndBooleanNeverBecomeValidProvinceOrActorIds() throws IOException {
        String raw = new String(wire(base()), StandardCharsets.UTF_8);
        assertTrue(raw.contains("\"b_a\":12"));
        for (String token : List.of("12.0", "true", "\"12\"", "0", "-1")) {
            JsonNode result = StrictJson.parse(SavedMembershipCodec.evaluate(bytes(raw.replace("\"b_a\":12", "\"b_a\":" + token))));
            assertTrue(result.path("states").path("100").path("geographic").isNull());
            assertFalse(result.path("realm").path("complete").booleanValue());
        }
        assertTrue(raw.contains("\"actor\":1"));
        for (String token : List.of("1.0", "true", "\"1\"", "null")) {
            byte[] wrong = bytes(raw.replace("\"actor\":1", "\"actor\":" + token));
            assertThrows(ContractViolationException.class, () -> SavedMembershipCodec.evaluate(wrong));
            ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                    org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.registeredResult(
                            new org.xar.ck3.control.wave2.planning.scoretarget.SavedScoreProjectionPortCatalog().registrations().stream()
                                    .filter(port -> port.operation() == org.xar.ck3.control.contracts.projection.ProjectionOperation.SAVED_COUNTY_MEMBERSHIP_AUDIT)
                                    .findFirst().orElseThrow(), wrong));
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
        }
    }

    @Test
    void declaredProjectionAcceptsExtensionsButOrderClosureAndTypesAreStrict() throws IOException {
        ObjectNode input = base(); ObjectNode projection = object(input, "projection");
        projection.putObject("future_sdk_extension").put("enabled", true);
        object(object(projection, "titles"), "100").put("future_title_field", "unused");
        SavedMembershipInput decoded = SavedMembershipCodec.decode(wire(input));
        assertThrows(UnsupportedOperationException.class, () -> decoded.projection().titles().clear());
        assertThrows(UnsupportedOperationException.class, () -> decoded.projection().rootKeys().clear());
        projection.putArray("title_order").add(100).add(100);
        byte[] duplicateOrder = wire(input);
        assertThrows(ContractViolationException.class, () -> SavedMembershipCodec.decode(duplicateOrder));
        input = base(); object(input, "projection").remove("title_order"); byte[] missingOrder = wire(input);
        assertThrows(ContractViolationException.class, () -> SavedMembershipCodec.decode(missingOrder));
        input = base(); object(input, "projection").put("stream_complete", 1); byte[] wrongBoolean = wire(input);
        assertThrows(ContractViolationException.class, () -> SavedMembershipCodec.decode(wrongBoolean));
    }

    private static ObjectNode base() throws IOException {
        return (ObjectNode) StrictJson.parse(bytes(vector("test_complete_realm_and_explicit_foreign_root_remain_exact_and_source_bound").path("input_json").textValue()));
    }
    private static JsonNode vector(String label) throws IOException {
        return corpus().rows().stream().filter(row -> {
            for (JsonNode name : row.path("captured_in")) { if (label.equals(name.textValue())) { return true; } }
            return false;
        }).findFirst().orElseThrow(() -> new AssertionError("real oracle vector absent: " + label));
    }
    private static ObjectNode object(ObjectNode row, String name) { assertTrue(row.get(name) instanceof ObjectNode); return (ObjectNode) row.get(name); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] wire(ObjectNode value) { return bytes(value.toString()); }
    private record Corpus(JsonNode header, List<JsonNode> rows) { }
    private static Corpus corpus() throws IOException {
        try (InputStream stream = SavedCountyMembershipTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) { throw new AssertionError("committed whole original membership suite golden required; never skip"); }
            byte[] raw = stream.readNBytes(96 * 1024 + 1); assertTrue(raw.length > 0 && raw.length <= 96 * 1024);
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]);
            List<JsonNode> rows = new ArrayList<>();
            for (int index = 1; index < lines.length - 1; index++) { rows.add(StrictJson.parse(bytes(lines[index]))); }
            return new Corpus(StrictJson.parse(bytes(lines[0])), List.copyOf(rows));
        }
    }
}
