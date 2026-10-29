package org.xar.ck3.control.wave3.governance.crownretry;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
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

final class CrownRetryTest {
    @TestFactory
    Stream<DynamicTest> unchangedPredicateStateReaderAndHorizonConsumerGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals(24, golden.get("cases").size());
        assertEquals(24, golden.get("original_state_reader_cases").intValue());
        assertTrue(golden.get("source_refs_unchanged").booleanValue());
        return stream(golden.get("cases")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            assertTrue(row.get("actual_state_reader_executed").booleanValue());
            assertEquals(row.get("expected_match"), StrictJson.parse(CrownRetryCodec.match(raw(row.get("match_request")))));
            assertEquals(row.get("expected_horizon"), StrictJson.parse(CrownRetryCodec.horizon(raw(row.get("horizon_request")))));
        }));
    }

    @TestFactory
    Stream<DynamicTest> rawBoolFloatAndSourceContextAliasesAreRejected() throws IOException {
        JsonNode golden = golden(); assertEquals(4, golden.get("wire_rejections").size());
        return stream(golden.get("wire_rejections")).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.match(row.get("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8)))));
    }

    @Test
    void nonnullPendingAlwaysBlocksReuseEvenWithAnInvalidCachedHint() throws IOException {
        ObjectNode request = baseMatch(); ObjectNode state = (ObjectNode) request.get("state");
        state.putObject("pending").put("action_id", "existing-unknown-original");
        ((ObjectNode) state.get("retry")).put("retry_date_raw", true);
        assertTrue(StrictJson.parse(CrownRetryCodec.match(raw(request))).isNull());
    }

    @Test
    void extraSourceContextFieldsCannotBeDroppedToManufactureAMatch() throws IOException {
        ObjectNode request = baseMatch();
        ((ObjectNode) request.get("state").get("retry").get("source_context")).put("foreign_generation", "not-this-source");
        assertTrue(StrictJson.parse(CrownRetryCodec.match(raw(request))).isNull());
    }

    @Test
    void ceilAndMinNeverExtendRequestedDaysOrReturnZero() {
        CrownRetryPolicy.ContextKey context = new CrownRetryPolicy.ContextKey(BigInteger.valueOf(881), "same-episode");
        BigInteger date = new BigInteger("53279400");
        CrownRetryPolicy.Frame frame = new CrownRetryPolicy.Frame(context, true, BigInteger.valueOf(29829), date);
        for (int hours : List.of(1, 23, 24, 25, 47, 48, 49)) {
            CrownRetryPolicy.Hint hint = new CrownRetryPolicy.Hint(context, BigInteger.valueOf(29829), date.add(BigInteger.valueOf(hours)), "crown_authority_2", "{}");
            CrownRetryPolicy.State state = new CrownRetryPolicy.State(false, hint);
            for (int requested : List.of(1, 2, 8, 40)) {
                BigInteger actual = CrownRetryPolicy.horizonDays(frame, state, BigInteger.valueOf(requested), true, true);
                assertEquals(BigInteger.valueOf(Math.min(requested, (hours + 23) / 24)), actual);
                assertTrue(actual.signum() > 0 && actual.compareTo(BigInteger.valueOf(requested)) <= 0);
            }
        }
    }

    @Test
    void requestedHorizonRejectsBooleanFloatStringZeroAndNegativeTokens() throws IOException {
        for (String token : List.of("true", "40.0", "\"40\"", "0", "-1")) {
            ObjectNode request = baseHorizon(); request.set("horizon_days", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.horizon(raw(request)));
        }
        ObjectNode wrongOptIn = baseHorizon(); wrongOptIn.put("query_enabled", 1);
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.horizon(raw(wrongOptIn)));
    }

    @Test
    void missingStateAndExplicitNullHaveDifferentWireAdmission() throws IOException {
        ObjectNode absent = baseHorizon(); absent.remove("state");
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.horizon(raw(absent)));
        ObjectNode unavailable = baseHorizon(); unavailable.putNull("state");
        assertEquals(unavailable.get("horizon_days"), StrictJson.parse(CrownRetryCodec.horizon(raw(unavailable))));
    }

    @Test
    void matchingHintAndItsExtensionsRoundTripWithoutMutatingOriginalState() throws IOException {
        JsonNode row = stream(golden().get("cases")).filter(value -> "retry_extension_preserved".equals(value.get("name").textValue())).findFirst().orElseThrow();
        ObjectNode request = (ObjectNode) row.get("match_request").deepCopy(); String before = request.toString();
        JsonNode result = StrictJson.parse(CrownRetryCodec.match(raw(request)));
        assertEquals(request.get("state").get("retry"), result);
        assertEquals(result, StrictJson.parse(StrictJson.canonical(result)));
        assertEquals(before, request.toString());
    }

    @Test
    void malformedBytesDuplicateFieldsUnknownWrapperAndOverflowAreRejected() throws IOException {
        String valid = new String(raw(baseMatch()), StandardCharsets.UTF_8);
        String duplicate = valid.substring(0, valid.length() - 1) + ",\"law_key\":null}";
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.match(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.match((valid + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.match(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.horizon(new byte[65_537]));
        ObjectNode unknown = baseMatch(); unknown.put("retry_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> CrownRetryCodec.match(raw(unknown)));
    }

    private static Stream<JsonNode> stream(JsonNode values) { return StreamSupport.stream(values.spliterator(), false); }
    private static ObjectNode baseMatch() throws IOException { return (ObjectNode) golden().get("cases").get(0).get("match_request").deepCopy(); }
    private static ObjectNode baseHorizon() throws IOException { return (ObjectNode) golden().get("cases").get(0).get("horizon_request").deepCopy(); }
    private static JsonNode golden() throws IOException {
        try (InputStream source = CrownRetryTest.class.getResourceAsStream("/crownretry/original-producer-golden.json")) {
            assertNotNull(source, "committed original predicate/reader/consumer golden is mandatory; no Python fallback");
            return StrictJson.parse(source.readAllBytes());
        }
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
