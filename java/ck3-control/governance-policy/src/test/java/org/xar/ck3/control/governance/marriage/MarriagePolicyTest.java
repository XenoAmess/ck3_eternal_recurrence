package org.xar.ck3.control.governance.marriage;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.governance.marriage.MarriageModel.*;

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
import org.xar.ck3.control.contracts.StrictJson;

class MarriagePolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = MarriagePolicyTest.class.getResourceAsStream("/marriage/python-golden-v1.json")) {
            assertNotNull(input, "committed original producer golden is mandatory");
            JsonNode golden = StrictJson.parse(input.readAllBytes());
            assertEquals("xar.ck3.marriage-policy-python-golden.v1", golden.get("schema").textValue());
            assertEquals(5, golden.get("original_tests_run").intValue());
            assertEquals(0, golden.get("original_failures").intValue());
            assertEquals(0, golden.get("original_errors").intValue());
            assertEquals(31, golden.get("cases").size());
            return golden;
        }
    }

    private static ObjectNode request(JsonNode golden, JsonNode testCase) {
        ObjectNode request = (ObjectNode) golden.get("base_request").deepCopy();
        for (JsonNode patch : testCase.get("patches")) {
            JsonNode path = patch.get("path");
            JsonNode parent = request;
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode key = path.get(index);
                parent = key.isIntegralNumber() ? parent.get(key.intValue()) : parent.get(key.textValue());
            }
            JsonNode key = path.get(path.size() - 1);
            if (parent instanceof ArrayNode array) {
                if (patch.path("remove").asBoolean(false)) { array.remove(key.intValue()); }
                else { array.set(key.intValue(), patch.get("value").deepCopy()); }
            } else if (parent instanceof ObjectNode object) {
                if (patch.path("remove").asBoolean(false)) { object.remove(key.textValue()); }
                else { object.set(key.textValue(), patch.get("value").deepCopy()); }
            } else { fail("invalid committed golden patch"); }
        }
        return request;
    }

    private static byte[] rawToken(ObjectNode request, ObjectNode owner, String field, String token) {
        String marker = "\"__marriage_raw_token__\"";
        owner.put(field, "__marriage_raw_token__");
        String template = request.toString();
        int at = template.indexOf(marker);
        assertTrue(at >= 0, "raw token marker is mandatory");
        assertEquals(at, template.lastIndexOf(marker), "raw token marker must be unique");
        String raw = template.substring(0, at) + token + template.substring(at + marker.length());
        assertTrue(raw.contains("\"" + field + "\":" + token), "outbound JSON must retain the exact invalid token");
        assertFalse(raw.contains(marker), "raw token marker must be removed");
        return raw.getBytes(StandardCharsets.UTF_8);
    }

    @Test
    void originalPythonProducerDecisionsAndOrderingMatch() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("cases")) {
            String name = testCase.get("name").textValue();
            Request input = MarriageCodec.decode(StrictJson.canonical(request(golden, testCase)));
            List<BigInteger> expected = new ArrayList<>();
            testCase.get("expected_shortlist").forEach(id -> expected.add(id.bigIntegerValue()));
            assertEquals(expected, MarriagePolicy.shortlist(input), name + " shortlist");
            assertEquals(testCase.get("expected_decision"), MarriageCodec.decisionNode(MarriagePolicy.choose(input)), name + " decision");
        }
    }

    @Test
    void all189HistoricalCompactCandidatesPreserveExclusionBeforeLimit() throws IOException {
        try (InputStream input = MarriagePolicyTest.class.getResourceAsStream("/marriage/history-golden-v1.json")) {
            assertNotNull(input, "committed original 189-candidate projection is mandatory");
            JsonNode history = StrictJson.parse(input.readAllBytes());
            assertEquals(189, history.get("original_candidates").intValue());
            Request request = MarriageCodec.decode(history.get("request").toString().getBytes(StandardCharsets.UTF_8));
            assertEquals(189, request.legality().candidates().value().size());
            assertEquals(List.of(BigInteger.valueOf(37689), BigInteger.valueOf(37513)), MarriagePolicy.shortlist(request));
            assertEquals(history.get("expected_decision"), MarriageCodec.decisionNode(MarriagePolicy.choose(request)));
            assertEquals(Reason.INCOMPLETE_TOP_TWO_FULL_VALUE_COMPARISON, MarriagePolicy.choose(request).reason());
            assertEquals(request, MarriageCodec.decode(MarriageCodec.encode(request)));
        }
    }

    @Test
    void completeTypedProjectionRoundTripsIncludingMissingNullAndEmpty() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("cases")) {
            Request input = MarriageCodec.decode(StrictJson.canonical(request(golden, testCase)));
            byte[] canonical = MarriageCodec.encode(input);
            Request roundTrip = MarriageCodec.decode(canonical);
            assertEquals(input, roundTrip, testCase.get("name").textValue());
            assertArrayEquals(canonical, MarriageCodec.encode(roundTrip));
        }
        ObjectNode missing = (ObjectNode) golden.get("base_request").deepCopy();
        ((ObjectNode) missing.get("legality")).remove("betrothed_character_id");
        assertEquals(Presence.MISSING, MarriageCodec.decode(StrictJson.canonical(missing)).legality().relationship().betrothed().presence());
        ObjectNode explicitNull = (ObjectNode) golden.get("base_request").deepCopy();
        assertEquals(Presence.NULL, MarriageCodec.decode(StrictJson.canonical(explicitNull)).legality().relationship().betrothed().presence());
        assertEquals(Presence.VALUE, MarriageCodec.decode(StrictJson.canonical(explicitNull)).legality().relationship().spouses().presence());
    }

    @Test
    void everyEnvelopeFieldIsRequiredAndUnknownFieldsAreRejected() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request");
        List<String> fields = new ArrayList<>();
        base.fieldNames().forEachRemaining(fields::add);
        for (String key : fields) {
            ObjectNode missing = base.deepCopy();
            missing.remove(key);
            assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(StrictJson.canonical(missing)), key);
        }
        ObjectNode unknown = base.deepCopy();
        unknown.put("python_fallback", true);
        assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(StrictJson.canonical(unknown)));
    }

    @Test
    void integerAndBooleanTokensNeverCoerce() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request");
        for (String token : List.of("true", "false", "29829.0", "\"29829\"", "[]", "{}")) {
            ObjectNode changed = base.deepCopy();
            byte[] raw = rawToken(changed, (ObjectNode) changed.get("legality"), "played_character_id", token);
            assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(raw), token);
        }
        for (String token : List.of("0", "1", "\"true\"", "[]", "{}")) {
            ObjectNode changed = base.deepCopy();
            byte[] raw = rawToken(changed, changed, "split_successor_verified", token);
            assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(raw), token);
        }
    }

    @Test
    void duplicateKeysTrailingTokensInvalidUtf8AndInvalidLimitsReject() throws IOException {
        String base = golden().get("base_request").toString();
        byte[] duplicate = ("{\"shortlist_limit\":2," + base.substring(1)).getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(duplicate));
        assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode((base + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        for (int limit : List.of(0, 6, -1)) {
            ObjectNode changed = (ObjectNode) golden().get("base_request").deepCopy();
            changed.put("shortlist_limit", limit);
            assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(StrictJson.canonical(changed)));
        }
    }

    @Test
    void excludedCandidateIdentityIsExactAndUnique() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request");
        for (String exclusions : List.of("[true]", "[37909.0]", "[\"37909\"]", "[0]", "[-1]", "[2147483648]", "[37909,37909]")) {
            ObjectNode changed = base.deepCopy();
            byte[] raw = rawToken(changed, changed, "excluded_candidate_ids", exclusions);
            assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(raw), exclusions);
        }
    }

    @Test
    void nativeExtensionsAreProjectedWithoutGrantingAdditionalAuthority() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request").deepCopy();
        Request original = MarriageCodec.decode(StrictJson.canonical(base));
        ((ObjectNode) base.get("legality")).put("exact_ck3_build", "fixture-source");
        ((ObjectNode) base.get("values").get(0).get("row")).put("unread_native_extension", 123);
        Request projected = MarriageCodec.decode(StrictJson.canonical(base));
        assertEquals(original, projected);
        assertEquals(MarriagePolicy.choose(original), MarriagePolicy.choose(projected));
        assertFalse(new String(MarriageCodec.encode(projected), StandardCharsets.UTF_8).contains("unread_native_extension"));
    }

    @Test
    void boundedNativeEnvelopeMayExceedMapBudgetButCannotBeUnbounded() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request").deepCopy();
        Request original = MarriageCodec.decode(StrictJson.canonical(base));
        ((ObjectNode) base.get("legality")).put("unread_native_extension", "x".repeat(80_000));
        byte[] largerNativeEnvelope = base.toString().getBytes(StandardCharsets.UTF_8);
        assertTrue(largerNativeEnvelope.length > StrictJson.INPUT_MAX_BYTES);
        assertEquals(original, MarriageCodec.decode(largerNativeEnvelope));
        ((ObjectNode) base.get("legality")).put("unread_native_extension", "x".repeat(MarriageCodec.MAX_BYTES));
        assertThrows(IllegalArgumentException.class, () -> MarriageCodec.decode(base.toString().getBytes(StandardCharsets.UTF_8)));
    }
}
