package org.xar.ck3.control.wave2.governance.focusscope;

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
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScope.*;

final class EducationFocusScopeTest {
    private static final EducationFocusScopeProjectionPort PORT = new EducationFocusScopeProjectionPort();
    private static final ObjectMapper FIXTURE_JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static JsonNode golden() throws IOException {
        try (InputStream input = EducationFocusScopeTest.class.getResourceAsStream("/focusscope/original-producer-golden-v1.json")) {
            assertNotNull(input, "committed actual original-producer and all-consumer golden required; never skip or execute Python");
            byte[] raw = input.readAllBytes(); assertTrue(raw.length <= 105_000);
            JsonNode root = FIXTURE_JSON.readTree(raw);
            assertEquals("education-focus-scope-original-producer-golden-v1", root.path("schema").textValue());
            assertFalse(root.path("native_business_qualification").booleanValue());
            assertFalse(root.path("machine_id").textValue().isEmpty()); assertFalse(root.path("observed_at_utc").textValue().isEmpty());
            assertEquals(3, root.path("consumer_seams").size()); assertEquals(8, root.path("sources").size()); return root;
        }
    }
    @TestFactory Stream<DynamicTest> actualOriginalProducerAndAllConsumers() throws IOException {
        List<DynamicTest> cases = new ArrayList<>(); JsonNode original = golden().path("cases"); assertTrue(original.size() >= 30);
        for (JsonNode row : original) {
            cases.add(DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
                byte[] request = StrictJson.canonical(row.get("request"));
                assertEquals(row.get("expected"), StrictJson.parse(PORT.encode(PORT.project(PORT.decode(request)))));
                var decoded = EducationFocusScopeCodec.decode(request);
                assertEquals(decoded, EducationFocusScopeCodec.decode(EducationFocusScopeCodec.encode(decoded)), "declared projection/domain round trip");
            }));
        }
        return cases.stream();
    }
    @Test void hostPhasesPreserveKnownDomainRefusalAndRawDecodeRejection() throws IOException {
        assertEquals(org.xar.ck3.control.contracts.projection.ProjectionOperation.GOVERNANCE_EDUCATION_FOCUS_SCOPE, PORT.operation());
        assertEquals(65_536, PORT.inputMaximumBytes()); assertEquals(65_536, PORT.outputMaximumBytes());
        String valid = new String(StrictJson.canonical(sample("closed_4106_4107")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> PORT.decode(valid.replace("\"expected_revision\":2", "\"expected_revision\":2.0").getBytes(StandardCharsets.UTF_8)));
        assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                () -> PORT.project(new EducationFocusScopeCodec.CombineRequest(new StateQuery("available", null), null, null, null, null)));
    }
    private static ObjectNode sample(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) { if (name.equals(row.path("name").textValue())) { return (ObjectNode) row.get("request").deepCopy(); } }
        throw new AssertionError("missing original producer case " + name);
    }
    @Test void rawFloatBoolAndStringIdentityTokensActuallyReachStrictBoundary() throws IOException {
        String valid = new String(StrictJson.canonical(sample("closed_4106_4107")), StandardCharsets.UTF_8);
        for (String bad : List.of("2.0", "true", "\"2\"", "[]")) {
            String raw = valid.replace("\"expected_revision\":2", "\"expected_revision\":" + bad);
            assertNotEquals(valid, raw);
            assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(raw.getBytes(StandardCharsets.UTF_8)), bad);
        }
        // Python == accepts these floating public revisions; the current project integer contract does not.
        for (String field : List.of("revision", "public_revision", "source_public_revision")) {
            String raw = valid.replace("\"" + field + "\":2", "\"" + field + "\":2.0");
            assertNotEquals(valid, raw);
            assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(raw.getBytes(StandardCharsets.UTF_8)), field);
        }
        ObjectNode booleanActor = sample("closed_4106_4107"); ((ObjectNode) booleanActor.at("/input/frame")).put("player_character_id", true);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(booleanActor)));
        ObjectNode booleanNative = sample("closed_4106_4107"); ((ObjectNode) booleanNative.at("/input/query/source_frame")).put("native_revision", true);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(booleanNative)));
    }
    @Test void duplicateUnknownRequiredTrailingAndUtf8GuardAreReal() throws IOException {
        ObjectNode extra = sample("closed_4106_4107"); extra.put("already_qualified", true);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(extra)));
        ObjectNode missing = sample("closed_4106_4107"); ((ObjectNode) missing.get("input")).remove("expected_revision");
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(missing)));
        String valid = new String(StrictJson.canonical(sample("closed_4106_4107")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(valid.replaceFirst("\\{", "{\"schema\":\"duplicate\",").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
    @Test void nativeExtensionsAreProjectedButSourceFrameAndContextRemainExact() throws IOException {
        ObjectNode extended = sample("closed_4106_4107"); ((ObjectNode) extended.at("/input/query")).putObject("future_native_detail").put("unused", true);
        ((ObjectNode) extended.at("/input/query/current_focus")).put("native_debug", "opaque");
        assertFalse(StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(extended))).isNull());
        ObjectNode extraSource = sample("closed_4106_4107"); ((ObjectNode) extraSource.at("/input/query/source_frame")).put("public_revision", 2);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(extraSource)));
        ObjectNode extraContext = sample("closed_4106_4107"); ((ObjectNode) extraContext.at("/input/query/source_context")).put("query_accepted", true);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(extraContext)));
    }
    @Test void projectionNullsAreNotInventedIdentityOrAgeAndMissingFrameFieldRejects() throws IOException {
        ObjectNode request = sample("project_missing_played");
        JsonNode projected = StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(request)));
        assertTrue(projected.path("player_character_id").isNull()); assertTrue(projected.path("actor_alive").isNull());
        ObjectNode nullable = sample("closed_4106_4107"); ((ObjectNode) nullable.at("/input/frame")).putNull("actor_alive");
        assertTrue(StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(nullable))).isNull());
        ObjectNode absent = sample("closed_4106_4107"); ((ObjectNode) absent.at("/input/frame")).remove("actor_alive");
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(absent)));
    }
    @Test void definitionUnavailabilityNeverBecomesAgeOrFocusActionLegality() throws IOException {
        JsonNode fact = StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(sample("closed_4106_4107"))));
        assertEquals("education_intrigue", fact.path("current_focus_key").textValue());
        assertFalse(fact.path("age_observed").booleanValue()); assertTrue(fact.path("lifestyle_action_legal").isNull());
        assertEquals(EducationFocusScope.SOURCE_REVIEW.readerSha256(), fact.path("source_review").path("reader_sha256").textValue());
        ObjectNode forged = sample("formal_closed"); ((ObjectNode) forged.at("/input/combined/education_focus_scope")).put("lifestyle_action_legal", true);
        assertThrows(ContractViolationException.class, () -> EducationFocusScopeCodec.decode(StrictJson.canonical(forged)));
    }
    @Test void recognizedErrorsOnlyRouteToExistingReadOnlyProbe() {
        assertEquals(CurrentStateRoute.CONTINUE_STOCK_FOCUS_PATH, EducationFocusScope.routeCurrentState(new StateQuery("available", null)));
        assertEquals(CurrentStateRoute.RETAIN_CURRENT_UNAVAILABLE, EducationFocusScope.routeCurrentState(new StateQuery("native_query_unavailable", null)));
        assertEquals(CurrentStateRoute.RETAIN_CURRENT_UNAVAILABLE, EducationFocusScope.routeCurrentState(new StateQuery("native_query_unavailable", "native_sample_drift")));
        for (String error : EducationFocusScope.BINDING_ERRORS) {
            assertEquals(CurrentStateRoute.PROBE_EDUCATION_FOCUS, EducationFocusScope.routeCurrentState(new StateQuery("native_query_unavailable", error)));
        }
    }
    @Test void pendingEmptyObjectAlsoBlocksAndRetainedSourceReviewIsRecomputed() throws IOException {
        ObjectNode pending = sample("opening_closed"); ((ObjectNode) pending.get("input")).putObject("pending_action");
        assertTrue(StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(pending))).isNull());
        ObjectNode drift = sample("opening_closed"); ((ObjectNode) drift.at("/input/combined/education_focus_scope/source_review")).put("reader_sha256", "0".repeat(64));
        assertTrue(StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(drift))).isNull());
    }
    @Test void opaquePythonIntegerIdentityIsNeverJavascriptRounded() throws IOException {
        ObjectNode sample = sample("closed_4106_4107"); BigInteger actor = new BigInteger("18446744073709551615");
        String episode = "native-" + actor + "-exact";
        ((ObjectNode) sample.at("/input/frame")).put("player_character_id", actor).put("episode_run_id", episode);
        ((ObjectNode) sample.at("/input/query")).put("child_full_id", actor);
        for (String pointer : List.of("/input/query/source_frame", "/input/query/source_context")) {
            ((ObjectNode) sample.at(pointer)).put("controller_full_id", actor).put("episode_run_id", episode);
        }
        JsonNode result = StrictJson.parse(EducationFocusScopeCodec.evaluate(StrictJson.canonical(sample)));
        assertEquals(actor, result.at("/source_frame/player_character_id").bigIntegerValue());
        var decoded = EducationFocusScopeCodec.decode(StrictJson.canonical(sample));
        assertEquals(decoded, EducationFocusScopeCodec.decode(EducationFocusScopeCodec.encode(decoded)));
    }
}
