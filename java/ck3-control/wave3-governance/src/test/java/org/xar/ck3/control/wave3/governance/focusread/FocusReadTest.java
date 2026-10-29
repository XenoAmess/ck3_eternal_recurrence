package org.xar.ck3.control.wave3.governance.focusread;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.wave3.governance.focusread.FocusReadCodec.Request;
import org.xar.ck3.control.wave3.governance.focusread.FocusReadPolicy.*;

final class FocusReadTest {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static JsonNode golden() throws IOException {
        try (InputStream input = FocusReadTest.class.getResourceAsStream("/focusread/original-producer-golden-v1.json")) {
            assertNotNull(input, "actual original producer/consumer corpus is mandatory; no Python fallback or skipped fixture");
            byte[] raw = input.readAllBytes(); assertTrue(raw.length <= 105000); JsonNode node = JSON.readTree(raw);
            assertEquals("fixed-focus-read-original-producer-golden-v1", node.path("schema").textValue());
            assertEquals(6, node.path("sources").size()); assertFalse(node.path("native_business_qualification").booleanValue()); return node;
        }
    }
    private static byte[] callTypedPort(byte[] raw) {
        var port = new FocusReadProjectionPort();
        return port.encode(port.project(port.decode(raw)));
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode sample : golden().get("cases")) { if (sample.path("name").asText().equals(name)) { return (ObjectNode) sample.get("request").deepCopy(); } }
        throw new AssertionError("missing original sample " + name);
    }
    private static Outcome parse(JsonNode node) { return FocusReadPolicy.parse(FocusReadCodec.decode(StrictJson.canonical(node)).input()); }
    private static ObjectNode response(ObjectNode request) throws IOException { return (ObjectNode) JSON.readTree(request.path("response_json").textValue()); }
    private static void setResponse(ObjectNode request, ObjectNode response) throws IOException { request.put("response_json", JSON.writeValueAsString(response)); }
    @TestFactory Stream<DynamicTest> originalParserAndAllRealConsumerSeams() throws IOException {
        JsonNode samples = golden().get("cases"); assertEquals(44, samples.size()); List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode sample : samples) {
            tests.add(DynamicTest.dynamicTest(sample.path("name").asText(), () -> {
                byte[] input = StrictJson.canonical(sample.get("request"));
                if (sample.path("name").asText().equals("wealth_protocol_float_old_accepts")) {
                    assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(input));
                } else {
                    assertEquals(sample.get("expected"), JSON.readTree(callTypedPort(input)));
                    Request decoded = FocusReadCodec.decode(input);
                    assertEquals(decoded, FocusReadCodec.decode(FocusReadCodec.encode(decoded)), "typed projection and complete response JSON round trip");
                }
            }));
        }
        return tests.stream();
    }
    @TestFactory Stream<DynamicTest> actualParserOutputFeedsTheUniqueFirstFocusPolicy() throws IOException {
        JsonNode samples = golden().get("first_focus_cases"); assertEquals(4, samples.size()); List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode sample : samples) {
            tests.add(DynamicTest.dynamicTest(sample.path("name").asText(), () -> {
                List<String> keys = new ArrayList<>(); for (JsonNode key : sample.path("traits").path("observed_keys")) { keys.add(StrictJson.text(key)); }
                var traits = Field.of(new LifestyleMinPolicy.Traits(Field.of("available"), Field.of(keys)));
                var result = FocusReadPolicy.chooseFirstFocus(parse(sample.get("wealth")), parse(sample.get("martial")), traits, sample.path("at_peace").booleanValue());
                assertEquals(sample.get("expected"), StrictJson.parse(LifestyleMinCodec.encode(result)));
            }));
        }
        return tests.stream();
    }
    @Test void unavailableCannotAcquireZeroAndPresenceOfNullStillCountsAsPromotion() throws IOException {
        Outcome unavailable = parse(request("wealth_progress_unavailable")); assertInstanceOf(ProgressUnavailable.class, unavailable);
        assertFalse(FocusReadCodec.outcomeNode(unavailable).has("target_lifestyle_progress"));
        assertFalse(FocusReadPolicy.forFirstFocus(unavailable).value().progress().present());
        Red unknown = (Red) parse(request("wealth_unknown_progress_with_null_numeric")); assertEquals(Issue.TARGET_PROGRESS_UNKNOWN_PROMOTED, unknown.issue());
        Red nativeNull = (Red) parse(request("wealth_unavailable_promoted_null")); assertEquals(Issue.NATIVE_FOCUS_UNAVAILABLE_PROMOTED, nativeNull.issue());
        assertTrue(FocusReadPolicy.forFirstFocus(nativeNull).state() == LifestyleMinPolicy.FieldState.NULL);
    }
    @Test void zeroIllegalAndUnknownRemainDifferentTypedResults() throws IOException {
        Observed zero = (Observed) parse(request("wealth_exact_baseline")); assertTrue(zero.nativeLegal()); assertEquals(BigInteger.ZERO, zero.progress().xpTotalRaw());
        Observed illegal = (Observed) parse(request("martial_exact_baseline")); assertFalse(illegal.nativeLegal()); assertEquals(BigInteger.valueOf(700000), illegal.progress().xpTotalRaw());
        Red missing = (Red) parse(request("wealth_missing_xp")); assertEquals(Issue.TARGET_PROGRESS_VALUES_INVALID, missing.issue());
        Red nullValue = (Red) parse(request("wealth_null_xp")); assertEquals(Issue.TARGET_PROGRESS_VALUES_INVALID, nullValue.issue());
    }
    @Test void fullOpaqueProgressExtensionsRemainJsonAndImmutable() throws IOException {
        ObjectNode input = request("wealth_opaque_progress_extensions"); Observed observed = (Observed) parse(input);
        JsonNode expected = response(input).path("result").get("target_lifestyle_progress");
        assertEquals(expected, JSON.readTree(FocusReadCodec.encode(observed)).get("target_lifestyle_progress"));
        byte[] original = observed.originalProgress().bytes(); byte[] changed = observed.originalProgress().bytes(); changed[0] = '[';
        assertArrayEquals(original, observed.originalProgress().bytes());
        assertTrue(JSON.readTree(original).path("future_details").path("seconds").isFloatingPointNumber());
        Request decoded = FocusReadCodec.decode(StrictJson.canonical(input)); byte[] raw = decoded.input().response().original().bytes();
        assertArrayEquals(raw, FocusReadCodec.decode(FocusReadCodec.encode(decoded)).input().response().original().bytes());
    }
    @Test void originalMalformedGetterRedIsTypedAndPreservesItsOriginalReason() throws IOException {
        for (String name : List.of("wealth_wrong_xp_bool", "wealth_wrong_xp_float", "wealth_wrong_xp_string")) {
            Request input = FocusReadCodec.decode(StrictJson.canonical(request(name)));
            assertInstanceOf(InvalidProgress.class, input.input().response().response().result().progress().value());
            Red result = (Red) FocusReadPolicy.parse(input.input());
            assertEquals(Issue.TARGET_PROGRESS_VALUES_INVALID, result.issue());
            assertEquals("target_progress_values_invalid", JSON.readTree(FocusReadCodec.evaluate(FocusReadCodec.encode(input))).path("issue").asText());
        }
    }
    @Test void strictRawIntegerTokensRejectOldProtocolFloatAcceptance() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            if (row.path("name").asText().equals("wealth_protocol_float_old_accepts")) {
                assertEquals("observed", row.path("expected").path("status").textValue());
                assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(row.get("request"))));
            }
        }
        ObjectNode request = request("wealth_exact_baseline"); String raw = new String(StrictJson.canonical(request), StandardCharsets.UTF_8);
        for (String token : List.of("3.0", "true", "\"3\"")) {
            String invalid = raw.replace("\"native_revision\":3", "\"native_revision\":" + token); assertNotEquals(raw, invalid);
            assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(invalid.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test void arbitrarilyPreciseOriginalIntegerDomainAndWithinLevelBoundaryAreKept() throws IOException {
        ObjectNode request = request("wealth_exact_baseline"); ObjectNode response = response(request);
        BigInteger exact = new BigInteger("18446744073709551615");
        ((ObjectNode) request.get("source_frame")).put("native_revision", exact).put("snapshot_id", "native:" + exact);
        ((ObjectNode) request.get("independent_after_frame")).put("native_revision", exact).put("snapshot_id", "native:" + exact);
        ((ObjectNode) response.get("result")).put("snapshot_id", "native:" + exact);
        ObjectNode progress = (ObjectNode) response.path("result").get("target_lifestyle_progress"); progress.put("xp_total_raw", exact);
        setResponse(request, response); Observed result = (Observed) parse(request);
        assertEquals(exact, result.sourceFrame().nativeRevision()); assertEquals(exact, result.progress().xpTotalRaw());
        assertEquals(Issue.TARGET_PROGRESS_VALUES_INVALID, ((Red) parse(request("wealth_within_equal_limit"))).issue());
    }
    @Test void noFrameAliasesAndNoCrossActorFocusComparison() throws IOException {
        ObjectNode alias = request("wealth_exact_baseline"); ObjectNode source = (ObjectNode) alias.get("source_frame");
        source.put("controller_full_id", source.get("played_character_id").bigIntegerValue()); source.remove("played_character_id");
        assertEquals(Issue.PAUSED_FOCUS_FRAME_DRIFT_OR_INVALID, ((Red) parse(alias)).issue());
        Outcome wealth = parse(request("wealth_exact_baseline")); Outcome martial = parse(request("martial_exact_baseline"));
        assertThrows(ContractViolationException.class, () -> FocusReadPolicy.chooseFirstFocus(wealth, martial, Field.nullValue(), true));
    }
    @Test void actualQueryPostGuardRetainsPublicAndNativeRevisionDifference() throws IOException {
        JsonNode accepted = JSON.readTree(FocusReadCodec.evaluate(StrictJson.canonical(request("actual_query_wealth_None"))));
        assertEquals("observed", accepted.path("status").textValue()); assertEquals(BigInteger.valueOf(3), accepted.path("source_frame").path("native_revision").bigIntegerValue());
        assertEquals("paused_focus_public_frame_drift", JSON.readTree(FocusReadCodec.evaluate(StrictJson.canonical(request("actual_query_wealth_public")))).path("issue").textValue());
        JsonNode map = JSON.readTree(FocusReadCodec.evaluate(StrictJson.canonical(request("actual_query_martial_map"))));
        assertFalse(map.has("step")); assertFalse(map.has("request_id"));
    }
    @Test void opaqueUnknownStringsCannotContainLoneSurrogatesOrUnboundedNesting() throws IOException {
        ObjectNode input = request("wealth_exact_baseline"); String valid = input.path("response_json").textValue();
        String loneEscape = "\\" + "uD800";
        for (String extension : List.of("\"future\":\"" + loneEscape + "\",", "\"" + loneEscape + "\":0,",
                "\"future\":" + "[".repeat(130) + "null" + "]".repeat(130) + ",")) {
            String invalid = valid.replace("\"presence\":\"present\"", extension + "\"presence\":\"present\"");
            assertNotEquals(valid, invalid); ObjectNode changed = input.deepCopy(); changed.put("response_json", invalid);
            assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(changed)));
        }
    }
    @Test void wrapperMissingDuplicateMalformedJsonAndWrongScalarTypesAreRejected() throws IOException {
        ObjectNode missing = request("wealth_exact_baseline"); missing.remove("response_json");
        assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(missing)));
        ObjectNode extra = request("wealth_exact_baseline"); extra.put("action_admitted", true);
        assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(extra)));
        ObjectNode duplicate = request("wealth_exact_baseline"); String original = duplicate.path("response_json").textValue();
        duplicate.put("response_json", "{\"protocol_version\":1," + original.substring(1));
        assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(duplicate)));
        duplicate.put("response_json", original + " {}"); assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(duplicate)));
        ObjectNode bad = request("wealth_exact_baseline"); ObjectNode response = response(bad); ((ObjectNode) response.get("result")).put("native_legal", 1); setResponse(bad, response);
        assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(StrictJson.canonical(bad)));
        assertThrows(ContractViolationException.class, () -> FocusReadCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
}
