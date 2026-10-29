package org.xar.ck3.control.wave3.governance.crowncooldown;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;

final class CrownCooldownTest {
    @TestFactory
    Stream<DynamicTest> originalImulLow32LiteralGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals(23, golden.get("literal_cases").size());
        return stream(golden.get("literal_cases")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertEquals(row.get("expected"), StrictJson.parse(CrownCooldownCodec.scale(raw(row.get("request")))))));
    }

    @TestFactory
    Stream<DynamicTest> originalRaw9AndClockInterpreterGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals(12, golden.get("clock_cases").size());
        assertTrue(golden.get("source_refs_unchanged").booleanValue());
        assertEquals(1, golden.get("original_unit_methods_executed").intValue());
        assertEquals(0, golden.get("original_unit_skips").intValue());
        return stream(golden.get("clock_cases")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertEquals(row.get("expected"), StrictJson.parse(CrownCooldownCodec.interpret(raw(row.get("request")))))));
    }

    @TestFactory
    Stream<DynamicTest> originalProducerRejectsActualRawBooleanFloatAndNativeSemanticNegatives() throws IOException {
        JsonNode golden = golden(); assertEquals(10, golden.get("wire_rejections").size());
        return stream(golden.get("wire_rejections")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            byte[] request = row.get("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8);
            if ("literal".equals(row.get("operation").textValue())) {
                assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.scale(request));
            } else { assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(request)); }
        }));
    }

    @TestFactory
    Stream<DynamicTest> legacyPureHelperUsesNormalizedRawWithoutManufacturingTickProof() throws IOException {
        return stream(golden().get("clock_cases")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            ObjectNode normalized = ((ObjectNode) row.get("request")).deepCopy();
            normalized.put("schema", CrownCooldownCodec.NORMALIZED_CLOCK_SCHEMA);
            normalized.remove("turn_tick_observation");
            String before = normalized.toString();
            byte[] result = CrownCooldownCodec.interpretNormalized(raw(normalized));
            assertEquals(row.get("expected"), StrictJson.parse(result));
            assertEquals(before, normalized.toString());
            assertEquals(StrictJson.parse(result), StrictJson.parse(StrictJson.canonical(StrictJson.parse(result))));
        }));
    }

    @TestFactory
    Stream<DynamicTest> originalRawNormalizerValuesRemainExact() throws IOException {
        return stream(golden().get("clock_cases")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            ObjectNode request = ((ObjectNode) row.get("request")).deepCopy();
            JsonNode expectedRaw = request.get("raw_observation").deepCopy();
            request.remove("turn_tick_observation");
            request.put("schema", "xar.java-crown-cooldown-raw-normalize/v1");
            assertEquals(expectedRaw, StrictJson.parse(CrownCooldownCodec.normalizeRaw(raw(request))));
        }));
    }

    @Test
    void normalizedHelperDoesNotRelaxFullQueryProofOrAcceptUnknownWrapperFields() throws IOException {
        ObjectNode full = projected();
        ObjectNode normalized = full.deepCopy();
        normalized.remove("turn_tick_observation");
        normalized.put("schema", CrownCooldownCodec.NORMALIZED_CLOCK_SCHEMA);
        assertTrue(StrictJson.parse(CrownCooldownCodec.interpretNormalized(raw(normalized))).get("calendar_deadline_ready").booleanValue());
        full.putNull("turn_tick_observation");
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(full)));
        normalized.putNull("turn_tick_observation");
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpretNormalized(raw(normalized)));
    }

    @Test
    void projectedUnitCannotReplaceItsSameQueryNativeContext() throws IOException {
        ObjectNode missing = projected(); missing.putNull("turn_tick_observation");
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(missing)));
        ObjectNode ineligible = projected();
        ObjectNode tick = (ObjectNode) ineligible.get("turn_tick_observation");
        tick.put("scalar_tail_allows_tick", false).put("context_tick_eligible", false);
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(ineligible)));
        ObjectNode wrongCount = projected();
        ((ObjectNode) wrongCount.get("turn_tick_observation")).put("manager_match_count", 2);
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(wrongCount)));
        ObjectNode wrongRetry = projected();
        ObjectNode raw = (ObjectNode) wrongRetry.get("raw_observation");
        raw.put("retry_date_raw", raw.get("retry_date_raw").bigIntegerValue().add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(wrongRetry)));
    }

    @Test
    void turnTickCountsKeepExactUint64RangeAndNoNumberCoercion() throws IOException {
        for (BigInteger count : List.of(BigInteger.valueOf(-1), BigInteger.ONE.shiftLeft(64))) {
            ObjectNode request = projected(); ((ObjectNode) request.get("turn_tick_observation")).put("manager_match_count", count);
            assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(request)));
        }
        for (String token : List.of("true", "1.0", "\"1\"")) {
            ObjectNode request = projected();
            String original = new String(raw(request), StandardCharsets.UTF_8);
            String field = "\"manager_match_count\":" + request.get("turn_tick_observation").get("manager_match_count");
            assertTrue(original.contains(field));
            assertEquals(original.indexOf(field), original.lastIndexOf(field));
            byte[] outgoing = original.replace(field, "\"manager_match_count\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(outgoing));
        }
        ObjectNode zero = projected();
        ((ObjectNode) zero.get("turn_tick_observation")).put("manager_match_count", 0).put("manager_contains_context", false).put("context_tick_eligible", false);
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(zero)));
    }

    @Test
    void timedMinusOneAndAbsentRemainDifferentStates() throws IOException {
        JsonNode timed = caseNamed("signed-remaining--1");
        JsonNode absent = caseNamed("absent_is_not_timed_minus_one");
        JsonNode timedResult = StrictJson.parse(CrownCooldownCodec.interpret(raw(timed.get("request"))));
        JsonNode absentResult = StrictJson.parse(CrownCooldownCodec.interpret(raw(absent.get("request"))));
        assertEquals("timed", timedResult.get("state").textValue());
        assertEquals(-1, timedResult.get("remaining_native_clock_steps").intValue());
        assertFalse(timedResult.get("native_clock_deadline_raw").isNull());
        assertTrue(timedResult.get("query_retry_date_raw").isNull());
        assertEquals("absent", absentResult.get("state").textValue());
        assertTrue(absentResult.get("native_clock_deadline_raw").isNull());
        assertFalse(absentResult.get("query_retry_date_raw").isNull());
    }

    @Test
    void durationResultsPreserveSignedOverflowAndUnknownTokenIdentity() {
        assertEquals(2147483283, CrownCooldown.scale(BigInteger.valueOf(1302), Integer.MAX_VALUE).clockStepsI32().intValue());
        assertEquals(Integer.MIN_VALUE, CrownCooldown.scale(BigInteger.valueOf(1327), Integer.MIN_VALUE).clockStepsI32().intValue());
        BigInteger huge = BigInteger.ONE.shiftLeft(100);
        CrownCooldown.DurationLiteral unknown = CrownCooldown.scale(huge, 20);
        assertFalse(unknown.accepted()); assertEquals(huge, unknown.tokenId());
        assertEquals(0, unknown.multiplierI32()); assertNull(unknown.clockStepsI32());
        assertThrows(UnsupportedOperationException.class, () -> CrownCooldown.FACTORS.clear());
    }

    @Test
    void missingNullAndWrongRawFieldContractsAreActuallyRejected() throws IOException {
        for (String field : List.of("remaining_raw", "present", "retry_date_raw", "remaining_unit")) {
            ObjectNode request = projected(); ((ObjectNode) request.get("raw_observation")).remove(field);
            assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(request)), field);
        }
        ObjectNode unknown = projected(); ((ObjectNode) unknown.get("raw_observation")).put("calendar_ready", true);
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(unknown)));
        ObjectNode nullCurrent = projected(); ((ObjectNode) nullCurrent.get("raw_observation")).putNull("current_clock_raw");
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(raw(nullCurrent)));
    }

    @Test
    void serializationRoundTripAndInputEvidenceRemainStable() throws IOException {
        ObjectNode request = projected(); String before = request.toString();
        byte[] output = CrownCooldownCodec.interpret(raw(request));
        JsonNode decoded = StrictJson.parse(output);
        assertEquals(decoded, StrictJson.parse(StrictJson.canonical(decoded)));
        assertEquals(before, request.toString());
        assertEquals(4, decoded.get("duration_token_factors").size());
        assertFalse(decoded.get("keyword_names_qualified").booleanValue());
        assertTrue(decoded.get("calendar_deadline_ready").booleanValue());
    }

    @Test
    void invalidBytesDuplicateUnknownWrapperFieldsAndOverflowAreRejected() throws IOException {
        String valid = new String(raw(projected()), StandardCharsets.UTF_8);
        String duplicate = valid.substring(0, valid.length() - 1) + ",\"date_raw\":53169072}";
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret((valid + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.interpret(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> CrownCooldownCodec.scale(new byte[65_537]));
    }

    private static Stream<JsonNode> stream(JsonNode rows) { return StreamSupport.stream(rows.spliterator(), false); }
    private static JsonNode caseNamed(String name) throws IOException {
        return stream(golden().get("clock_cases")).filter(row -> name.equals(row.get("name").textValue())).findFirst().orElseThrow();
    }
    private static ObjectNode projected() throws IOException { return (ObjectNode) caseNamed("single_same_query_match").get("request").deepCopy(); }
    private static JsonNode golden() throws IOException {
        try (InputStream source = CrownCooldownTest.class.getResourceAsStream("/crowncooldown/original-producer-golden.json")) {
            assertNotNull(source, "actual original producer golden is mandatory; no Python fallback");
            return StrictJson.parse(source.readAllBytes());
        }
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
