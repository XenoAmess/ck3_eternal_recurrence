package org.xar.ck3.control.wave2.governance.government;

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
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;

final class GovernmentContextTest {
    @TestFactory
    Stream<DynamicTest> originalProtocolProducerNormalizerAndContextGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals(15, golden.get("cases").size());
        assertTrue(golden.get("source_refs_unchanged").booleanValue());
        assertEquals(3, golden.get("original_unittest").get("tests").intValue());
        assertEquals(0, golden.get("original_unittest").get("skipped").intValue());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(
                row.get("name").textValue(), () -> {
                    ObjectNode request = request(golden, row);
                    ObjectNode expected = (ObjectNode) row.get("expected").deepCopy();
                    JsonNode expectedObservationSha = row.get("expected_observation_sha256");
                    // The immutable old corpus calls this current-only change valid.
                    // An unreconciled current goal must retain its original actor.
                    if ("valid_goal_but_different_current_actor".equals(row.get("name").textValue())) {
                        expected.put("status", "unavailable").put("identity_observation_ready", false)
                                .put("core_adapter_ready", false).put("ordinary_goal_context_ready", false)
                                .put("unavailable_reason", "ordinary campaign goal origin_character_id is malformed");
                        expected.putNull("government_key"); expected.putNull("adapter_family"); expected.putNull("adapter_status");
                        expectedObservationSha = null;
                    }
                    if (expectedObservationSha == null || expectedObservationSha.isNull()) { expected.putNull("government_runtime_adapter"); }
                    else {
                        JsonNode observed = request.get("government_observation");
                        assertEquals(expectedObservationSha.textValue(), sha256(StrictJson.canonical(observed)), "actual original-result payload identity");
                        expected.set("government_runtime_adapter", observed.deepCopy());
                    }
                    assertEquals(expected, StrictJson.parse(GovernmentContextCodec.compose(raw(request))));
                }));
    }

    @TestFactory
    Stream<DynamicTest> originalRawFloatAndBooleanWireNegatives() throws IOException {
        JsonNode golden = golden();
        assertEquals(5, golden.get("wire_rejections").size());
        return StreamSupport.stream(golden.get("wire_rejections").spliterator(), false).map(row -> DynamicTest.dynamicTest(
                row.get("name").textValue(), () -> {
                    // The raw original token goes directly to the decoder. A JSON
                    // tree must not turn legacy 3.0/44.0/0.0 into integer tokens.
                    byte[] body = row.get("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8);
                    assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(body));
                }));
    }

    @Test
    void declaredSdkProjectionAllowsAndPreservesUnconsumedExtensions() throws IOException {
        ObjectNode request = base();
        snapshot(request).put("future_sdk_field", "retained by caller only");
        observation(request).putObject("future_native_metadata").put("fractional_measurement", 1.25);
        JsonNode result = StrictJson.parse(GovernmentContextCodec.compose(raw(request)));
        assertTrue(result.get("ordinary_goal_context_ready").booleanValue());
        assertEquals(StrictJson.parse(raw(observation(request))), result.get("government_runtime_adapter"));
        assertEquals(1.25, result.get("government_runtime_adapter").get("future_native_metadata").get("fractional_measurement").doubleValue());
        assertFalse(result.has("future_sdk_field"));
    }

    @Test
    void sameBuildActorDateAndRevisionAreRequiredBeforeReadiness() throws IOException {
        for (String field : List.of("snapshot_revision", "date_raw", "player_character_id")) {
            ObjectNode request = base();
            ObjectNode observed = observation(request);
            observed.put(field, observed.get(field).bigIntegerValue().add(java.math.BigInteger.ONE));
            JsonNode result = StrictJson.parse(GovernmentContextCodec.compose(raw(request)));
            assertEquals("unavailable", result.get("status").textValue());
            assertFalse(result.get("identity_observation_ready").booleanValue());
            assertFalse(result.get("ordinary_goal_context_ready").booleanValue());
            assertTrue(result.get("government_runtime_adapter").isNull());
        }
    }

    @Test
    void directNativeQueryNormalizerDoesNotRequireAnOrdinaryGoalOrLifecycle() throws IOException {
        ObjectNode context = base();
        ObjectNode request = StrictJson.object();
        request.put("schema", GovernmentContextCodec.NORMALIZE_SCHEMA);
        ObjectNode frame = snapshot(context).deepCopy();
        frame.remove("campaign_goal"); frame.remove("succession_lifecycle");
        request.set("snapshot", frame); request.set("government_observation", observation(context));
        assertEquals(observation(context), StrictJson.parse(GovernmentContextCodec.normalizeAdapter(raw(request))));
        observation(request).put("snapshot_revision", 999);
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.normalizeAdapter(raw(request)));
    }

    @Test
    void readinessCannotBeEnabledByCallerBooleans() throws IOException {
        ObjectNode request = base();
        ((ObjectNode) observation(request).get("adapter")).put("requirements_met", false);
        JsonNode result = StrictJson.parse(GovernmentContextCodec.compose(raw(request)));
        assertEquals("government runtime adapter disagrees with its native core verdict", result.get("unavailable_reason").textValue());
        assertFalse(result.get("core_adapter_ready").booleanValue());
        request.put("identity_observation_ready", true);
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(request)));
    }

    @Test
    void strictWrapperRejectsMissingUnknownAndWrongPrimitiveTokens() throws IOException {
        for (String field : Set.of("schema", "snapshot", "government_observation", "query_permitted")) {
            ObjectNode request = base(); request.remove(field);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(request)), field);
        }
        for (String token : List.of("1", "1.0", "\"true\"", "null")) {
            ObjectNode request = base(); request.set("query_permitted", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(request)));
        }
        ObjectNode unknown = base(); unknown.put("native_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(unknown)));
    }

    @Test
    void missingNullAndUnavailableObservationRemainDistinctFromKnownCore() throws IOException {
        ObjectNode absent = base(); absent.putNull("government_observation");
        JsonNode result = StrictJson.parse(GovernmentContextCodec.compose(raw(absent)));
        assertEquals("government_observation_unavailable", result.get("unavailable_reason").textValue());
        assertTrue(result.get("government_runtime_adapter").isNull());
        assertFalse(result.get("ordinary_goal_context_ready").booleanValue());
        ObjectNode missing = base(); missing.remove("government_observation");
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(missing)));
    }

    @Test
    void outputSerializationRoundTripsWithoutChangingSourceDocument() throws IOException {
        ObjectNode request = base();
        byte[] before = raw(request);
        GovernmentContext.Context context = GovernmentContextCodec.decodeAndBuild(before);
        JsonNode first = StrictJson.parse(GovernmentContextCodec.encode(context));
        JsonNode second = StrictJson.parse(GovernmentContextCodec.encode(context));
        assertEquals(first, second);
        assertEquals(observation(request), first.get("government_runtime_adapter"));
        assertEquals(new String(before, StandardCharsets.UTF_8), new String(raw(request), StandardCharsets.UTF_8));
    }

    @Test
    void duplicateKeysTrailingContentMalformedUtf8AndOversizeAreRejected() throws IOException {
        String valid = new String(raw(base()), StandardCharsets.UTF_8);
        String duplicate = valid.substring(0, valid.length() - 1) + ",\"query_permitted\":true}";
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose((valid + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(new byte[65_537]));
    }

    private static ObjectNode request(JsonNode golden, JsonNode row) {
        ObjectNode request = (ObjectNode) golden.get("base_request").deepCopy();
        for (JsonNode patch : row.get("request_patch")) {
            String pointer = patch.get("path").textValue();
            int last = pointer.lastIndexOf('/');
            JsonNode parent = last == 0 ? request : request.at(pointer.substring(0, last));
            assertTrue(parent.isObject(), "captured patch parent must exist");
            String key = pointer.substring(last + 1).replace("~1", "/").replace("~0", "~");
            if ("remove".equals(patch.get("op").textValue())) { ((ObjectNode) parent).remove(key); }
            else { assertEquals("set", patch.get("op").textValue()); ((ObjectNode) parent).set(key, patch.get("value").deepCopy()); }
        }
        return request;
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = GovernmentContextTest.class.getResourceAsStream("/government/original-producer-golden.json")) {
            assertNotNull(input, "committed original-producer golden is mandatory; no runtime Python fallback");
            return StrictJson.parse(input.readAllBytes());
        }
    }
    private static ObjectNode base() throws IOException { return (ObjectNode) golden().get("base_request").deepCopy(); }
    private static ObjectNode snapshot(ObjectNode request) { return (ObjectNode) request.get("snapshot"); }
    private static ObjectNode observation(ObjectNode request) { return (ObjectNode) request.get("government_observation"); }
    private static byte[] raw(JsonNode row) { return row.toString().getBytes(StandardCharsets.UTF_8); }
    private static String sha256(byte[] raw) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
}
