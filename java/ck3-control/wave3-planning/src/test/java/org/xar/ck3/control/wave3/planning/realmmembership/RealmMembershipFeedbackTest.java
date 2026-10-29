package org.xar.ck3.control.wave3.planning.realmmembership;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;
import static org.junit.jupiter.api.Assertions.*;

class RealmMembershipFeedbackTest {
    @Test void unchangedProducerToCompleteJavaFactoryAndExistingComparison() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java.realm-membership-producer-golden/v1", golden.path("schema").textValue());
        assertFalse(golden.path("capture").path("machine_id").textValue().isBlank());
        assertFalse(golden.path("capture").path("observed_at_utc").textValue().isBlank());
        assertEquals(0, golden.path("capture").path("native_rpc_count").intValue());
        assertEquals(0, golden.path("capture").path("ledger_writes").intValue());
        assertEquals("d865ab4061d750c6e9174fa8e585705b5a44a11a990d160a6c1db14d0ba67a64", golden.path("sources").get(0).path("sha256").textValue());
        assertTrue(golden.path("cases").size() >= 29);
        JsonNode consumers = golden.path("consumer_tests"); assertTrue(consumers.path("tests_run").intValue() >= 20);
        assertEquals(0, consumers.path("failures").intValue()); assertEquals(0, consumers.path("errors").intValue()); assertEquals(0, consumers.path("skipped").intValue());
        for (JsonNode vector : golden.path("cases")) {
            String name = vector.path("name").textValue(); ObjectNode request = materialize(golden, vector); byte[] original = bytes(request);
            RealmMembershipFeedback.Result result = RealmMembershipFeedback.project(original);
            if (name.equals("nonobject-binding-keeps-original-envelope-semantics")) {
                // Preserve the original producer's accepted bad shape as evidence; the Java strict boundary closes it.
                assertEquals("available", vector.path("expected").path("status").textValue());
                assertEquals("faction_result_binding_invalid", assertInstanceOf(RealmMembershipFeedback.Unavailable.class, result).reason());
                continue;
            }
            assertEquals(vector.get("expected"), StrictJson.parse(result.wireJson(), RealmMembershipFeedback.MAX_BYTES), name);
            assertArrayEquals(original, bytes(request), name);
            if (vector.path("expected").path("status").textValue().equals("available")) {
                var verified = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class, result, name);
                assertNotNull(verified.observation(), name); assertNotNull(verified.difference(), name);
                assertEquals(vector.path("expected").path("observation").path("component").path("county_title_ids").size(), verified.realmCountyCount(), name);
                assertEquals(vector.path("expected").get("difference"), RealmDifferenceCodec.parsedResult(verified.difference()), name);
                byte[] returned = verified.wireJson(); returned[0] = 0;
                assertEquals(vector.get("expected"), StrictJson.parse(verified.wireJson(), RealmMembershipFeedback.MAX_BYTES), name);
            } else assertInstanceOf(RealmMembershipFeedback.Unavailable.class, result, name);
        }
    }
    @Test void validatedFeedbackIsPrivatelyConstructedAndFirstDifferenceStaysUnknown() throws IOException {
        assertEquals(1, RealmMembershipFeedback.VerifiedFeedback.class.getDeclaredConstructors().length);
        assertTrue(Modifier.isPrivate(RealmMembershipFeedback.VerifiedFeedback.class.getDeclaredConstructors()[0].getModifiers()));
        var first = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class,
                RealmMembershipFeedback.project(bytes(golden().path("bases").path("first"))));
        var difference = assertInstanceOf(RealmDifference.Unavailable.class, first.difference());
        assertEquals("previous_complete_observation_missing", difference.reason());
        assertEquals(3, first.realmCountyCount());
        var empty = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class,
                RealmMembershipFeedback.project(bytes(golden().path("bases").path("zero"))));
        assertEquals(0, empty.realmCountyCount());
        assertEquals("0", StrictJson.parse(empty.wireJson(), RealmMembershipFeedback.MAX_BYTES).path("raw_metrics").path("realm_county_count").path("value").textValue());
    }
    @Test void wrongRawFrameAndSequenceTokensNeverCreateVerifiedFeedback() throws IOException {
        String wire = new String(bytes(golden().path("bases").path("first")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"")) {
            String changed = wire.replace("\"query_sequence\":1", "\"query_sequence\":" + token);
            assertNotEquals(wire, changed);
            var result = assertInstanceOf(RealmMembershipFeedback.Unavailable.class, RealmMembershipFeedback.project(utf8(changed)));
            assertEquals("faction_original_query_sequence_unavailable", result.reason());
        }
        String floatFrame = wire.replace("\"native_revision\":41", "\"native_revision\":41.0");
        assertNotEquals(wire, floatFrame);
        assertInstanceOf(RealmMembershipFeedback.Unavailable.class, RealmMembershipFeedback.project(utf8(floatFrame)));
        assertThrows(IllegalArgumentException.class, () -> RealmMembershipFeedback.project(utf8(wire + " {}")));
        assertThrows(IllegalArgumentException.class, () -> RealmMembershipFeedback.project(utf8("{\"snapshot\":{},\"extra\":true}")));
        assertThrows(IllegalArgumentException.class, () -> RealmMembershipFeedback.project(utf8("{\"snapshot\":{},\"snapshot\":{}}")));
    }
    @Test void unavailableInputDoesNotPublishAZeroCountOrObservation() {
        RealmMembershipFeedback.Result result = RealmMembershipFeedback.project(utf8("{\"snapshot\":{}}"));
        JsonNode wire = StrictJson.parse(result.wireJson(), RealmMembershipFeedback.MAX_BYTES);
        assertInstanceOf(RealmMembershipFeedback.Unavailable.class, result);
        assertTrue(wire.path("observation").isNull()); assertTrue(wire.path("difference").isNull());
        assertTrue(wire.path("raw_metrics").path("realm_county_count").path("value").isNull());
        assertEquals("unknown", wire.path("raw_metrics").path("realm_county_count").path("availability").textValue());
        assertEquals(0, wire.path("new_RPC_calls").intValue()); assertEquals(0, wire.path("new_SAVE_exports").intValue());
        assertFalse(wire.path("same_native_capture_with_MET").booleanValue());
    }
    @Test void originalSdkSourceFrameExtensionsRetainTheirJsonType() throws IOException {
        ObjectNode input = (ObjectNode) golden().path("bases").path("first").deepCopy();
        ((ObjectNode) input.get("source_frame")).set("sdk_extension", new com.fasterxml.jackson.databind.node.DecimalNode(new java.math.BigDecimal("1.0")));
        byte[] raw = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(input);
        var feedback = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class, RealmMembershipFeedback.project(raw));
        JsonNode output = StrictJson.parse(feedback.wireJson(), RealmMembershipFeedback.MAX_BYTES);
        assertTrue(output.path("observation").path("source_frame").path("sdk_extension").isFloatingPointNumber());
        assertEquals(3, feedback.realmCountyCount());
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = RealmMembershipFeedbackTest.class.getResourceAsStream("/realmmembership/original-producer-golden.json")) {
            assertNotNull(stream, "required original producer capture missing; no skip is counted as pass");
            return StrictJson.parse(stream.readAllBytes(), RealmMembershipFeedback.MAX_BYTES);
        }
    }
    private static ObjectNode materialize(JsonNode golden, JsonNode vector) {
        ObjectNode root = (ObjectNode) golden.path("bases").get(vector.path("base").textValue()).deepCopy();
        for (JsonNode operation : vector.path("operations")) {
            String path = operation.path("path").textValue(); int split = path.lastIndexOf('/'); JsonNode parent = root.at(path.substring(0, split)); String key = path.substring(split + 1);
            if (parent instanceof ObjectNode object) {
                if (operation.path("remove").asBoolean()) object.remove(key); else object.set(key, operation.get("value").deepCopy());
            } else if (parent instanceof ArrayNode array) {
                int index = Integer.parseInt(key); if (operation.path("remove").asBoolean()) array.remove(index); else array.set(index, operation.get("value").deepCopy());
            } else fail("invalid golden operation " + path);
        }
        return root;
    }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value, RealmMembershipFeedback.MAX_BYTES); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

