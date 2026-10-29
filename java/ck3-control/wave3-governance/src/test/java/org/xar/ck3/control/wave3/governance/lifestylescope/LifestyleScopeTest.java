package org.xar.ck3.control.wave3.governance.lifestylescope;

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
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneModel.RootScopeStatus;
import org.xar.ck3.control.wave3.governance.lifestylescope.LifestyleScopeCodec.*;
import org.xar.ck3.control.wave3.governance.lifestylescope.LifestyleScopePolicy.*;

final class LifestyleScopeTest {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static JsonNode golden() throws IOException {
        try (InputStream input = LifestyleScopeTest.class.getResourceAsStream("/lifestylescope/original-producer-golden-v1.json")) {
            assertNotNull(input, "actual original producer golden is mandatory; no Python invocation or skipped fixture");
            byte[] raw = input.readAllBytes(); assertTrue(raw.length <= 105000); JsonNode node = JSON.readTree(raw);
            assertEquals("lifestyle-scope-original-producer-golden-v1", node.path("schema").textValue());
            assertEquals(6, node.path("sources").size()); assertFalse(node.path("native_business_qualification").booleanValue()); return node;
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) { if (row.path("name").asText().equals(name)) { return (ObjectNode) row.get("request").deepCopy(); } }
        throw new AssertionError("missing sample " + name);
    }
    private static ObjectNode consumer(String name) throws IOException {
        for (JsonNode row : golden().get("consumer_cases")) { if (row.path("name").asText().equals(name)) { return (ObjectNode) row.deepCopy(); } }
        throw new AssertionError("missing consumer sample " + name);
    }
    private static ObjectNode snapshot(ObjectNode request) { return (ObjectNode) request.path("scene").path("snapshot"); }
    private static ObjectNode root(ObjectNode request) { return (ObjectNode) request.path("scene").path("history").get(0).path("result").path("campaign_root_context"); }
    private static Assessment assess(ObjectNode request) {
        WrapperInput input = (WrapperInput) LifestyleScopeCodec.decode(StrictJson.canonical(request));
        return LifestyleScopePolicy.assess(input.scene(), input.mode());
    }
    @TestFactory Stream<DynamicTest> actualThreeWrappersAndServiceCacheProducer() throws IOException {
        JsonNode cases = golden().get("cases"); assertEquals(56, cases.size()); List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : cases) {
            tests.add(DynamicTest.dynamicTest(row.path("name").asText(), () -> {
                byte[] request = StrictJson.canonical(row.get("request"));
                assertEquals(row.get("expected"), StrictJson.parse(LifestyleScopeCodec.evaluate(request)));
                Input typed = LifestyleScopeCodec.decode(request);
                assertEquals(typed, LifestyleScopeCodec.decode(LifestyleScopeCodec.encode(typed)), "declared typed projection round trip");
            }));
        }
        return tests.stream();
    }
    @TestFactory Stream<DynamicTest> actualFormalConsumerAndMinimumPolicyProjection() throws IOException {
        JsonNode rows = golden().get("consumer_cases"); assertEquals(4, rows.size()); List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : rows) {
            tests.add(DynamicTest.dynamicTest("consumer_" + row.path("name").asText(), () -> {
                Assessment observed = assess((ObjectNode) row.get("request"));
                var original = LifestyleMinCodec.decode(StrictJson.canonical(row.get("minimum")));
                var result = LifestyleScopePolicy.choose(original, observed, false, LifestyleMinPolicy.Field.missing());
                assertEquals(row.get("expected_decision"), StrictJson.parse(LifestyleMinCodec.encode(result)));
            }));
        }
        return tests.stream();
    }
    @Test void warPeaceEarlyReturnAndGenericGovernmentDoNotAuthorizeInitialFocus() throws IOException {
        assertEquals(RootScopeStatus.OUTSIDE_SCENE, assess(request("war_missing_other_frame_feudal_peace")).root().status());
        assertEquals(RootScopeStatus.SCOPE_UNAVAILABLE, assess(request("war_missing_other_frame_feudal_lifestyle")).root().status());
        ObjectNode example = consumer("nonfeudal"); Assessment scope = assess((ObjectNode) example.get("request"));
        var current = LifestyleMinCodec.decode(StrictJson.canonical(example.get("minimum")));
        var projected = LifestyleScopePolicy.applyToMinimum(current, scope, false);
        assertTrue(projected.feudalScopeAdmitted().is(true)); assertTrue(projected.focusScopeAdmitted().is(false));
        ObjectNode absent = (ObjectNode) example.get("minimum").deepCopy();
        ((ObjectNode) absent.get("snapshot")).putObject("current_focus").put("presence", "absent");
        ((ObjectNode) absent.get("snapshot")).putObject("current_lifestyle_progress").put("presence", "absent");
        var decision = LifestyleScopePolicy.choose(LifestyleMinCodec.decode(StrictJson.canonical(absent)), scope, false, LifestyleMinPolicy.Field.missing());
        assertEquals(LifestyleMinPolicy.Status.OUTSIDE_ADMITTED_SCENE, decision.status());
        assertNull(((LifestyleMinPolicy.MinimumDecision) decision).decision().selectedAction());
    }
    @Test void serviceOpeningAndCacheSkipQueriesAndUnavailableDoesNotAdvertiseV3() throws IOException {
        ServiceRequest opening = (ServiceRequest) LifestyleScopeCodec.decode(StrictJson.canonical(request("service_opening_keeps_true_cache")));
        ServiceSelection kept = LifestyleScopePolicy.forService(opening.input());
        assertEquals(Cache.ENABLED, kept.nextCache()); assertEquals(Mode.FEUDAL_LIFESTYLE, kept.assessment().mode()); assertFalse(kept.capabilityReadUsed());
        ServiceRequest unavailable = (ServiceRequest) LifestyleScopeCodec.decode(StrictJson.canonical(request("service_fresh_unavailable")));
        assertEquals(Cache.DISABLED, LifestyleScopePolicy.forService(unavailable.input()).nextCache());
        assertThrows(UnsupportedOperationException.class, () -> unavailable.input().capabilityRead().bridgeCapabilities().add("forged"));
        ObjectNode bad = request("service_fresh_advertised"); ((ObjectNode) bad.get("service")).put("initial_focus_required", true);
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(StrictJson.canonical(bad)));
    }
    @Test void rawWrongIntegerTokensAreNeverNormalizedBeforeTheSharedCodec() throws IOException {
        String valid = new String(StrictJson.canonical(request("closed_test_frame_feudal_lifestyle")), StandardCharsets.UTF_8);
        for (String token : List.of("3.0", "true", "\"3\"")) {
            String bad = valid.replace("\"native_revision\":3", "\"native_revision\":" + token); assertNotEquals(valid, bad);
            assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(bad.getBytes(StandardCharsets.UTF_8)), token);
        }
        ObjectNode flags = request("closed_test_frame_feudal_lifestyle"); root(flags).put("government", "feudal_government");
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(StrictJson.canonical(flags)));
    }
    @Test void missingNullAndEmptyWarsRetainDistinctObservationMeaning() throws IOException {
        ObjectNode missing = request("closed_test_frame_feudal_lifestyle"); snapshot(missing).remove("active_wars");
        ObjectNode nil = request("closed_test_frame_feudal_lifestyle"); snapshot(nil).putNull("active_wars");
        assertEquals(RootScopeStatus.SCOPE_UNAVAILABLE, assess(missing).root().status());
        assertEquals(RootScopeStatus.SCOPE_UNAVAILABLE, assess(nil).root().status());
        assertNotEquals(LifestyleScopeCodec.decode(StrictJson.canonical(missing)), LifestyleScopeCodec.decode(StrictJson.canonical(nil)));
        assertEquals(RootScopeStatus.ADMITTED, assess(request("closed_test_frame_feudal_lifestyle")).root().status());
    }
    @Test void uint64RevisionAndScalarBoundariesRemainExact() throws IOException {
        ObjectNode request = request("closed_test_frame_feudal_lifestyle"); BigInteger maximum = new BigInteger("18446744073709551615");
        snapshot(request).put("native_revision", maximum); snapshot(request).put("snapshot_id", "native:" + maximum);
        root(request).put("snapshot_revision", maximum); Assessment scope = assess(request);
        assertEquals(maximum, scope.root().revision());
        assertEquals(maximum, StrictJson.parse(LifestyleScopeCodec.evaluate(StrictJson.canonical(request))).path("snapshot_revision").bigIntegerValue());
        snapshot(request).put("native_revision", maximum.add(BigInteger.ONE));
        assertEquals(RootScopeStatus.SCOPE_UNAVAILABLE, assess(request).root().status());
        ObjectNode actor = request("closed_test_frame_feudal_lifestyle"); ((ObjectNode) snapshot(actor).get("played_character")).put("character_id", 2147483648L);
        assertEquals(RootScopeStatus.SCOPE_UNAVAILABLE, assess(actor).root().status());
    }
    @Test void wrapperFieldsSchemaAndUtf8AreStrict() throws IOException {
        ObjectNode missing = request("closed_test_frame_feudal_lifestyle"); missing.remove("scene");
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(StrictJson.canonical(missing)));
        ObjectNode extra = request("closed_test_frame_feudal_lifestyle"); extra.put("scope_admitted", true);
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(StrictJson.canonical(extra)));
        String valid = new String(StrictJson.canonical(request("closed_test_frame_feudal_lifestyle")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(("{\"schema\":\"duplicate\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
    @Test void unrelatedSdkDecimalDiagnosticDoesNotBypassOrPreemptSharedFieldValidation() throws IOException {
        ObjectNode input = request("closed_test_frame_feudal_lifestyle"); snapshot(input).put("unconsumed_elapsed_seconds", 1.25);
        var parsed = LifestyleScopeCodec.decode(JSON.writeValueAsBytes(input));
        assertInstanceOf(WrapperInput.class, parsed);
        assertEquals(RootScopeStatus.ADMITTED, LifestyleScopePolicy.assess(parsed.scene(), Mode.FEUDAL_LIFESTYLE).root().status());
        snapshot(input).put("native_revision", 3.0);
        assertThrows(ContractViolationException.class, () -> LifestyleScopeCodec.decode(JSON.writeValueAsBytes(input)));
    }
    @Test void consumerRejectsForeignPublicNativeDateOrActorAndKeepsPendingUnknown() throws IOException {
        ObjectNode example = consumer("closed_test_frame"); Assessment scope = assess((ObjectNode) example.get("request"));
        for (String field : List.of("public_revision", "native_revision", "date_raw", "player_character_id")) {
            ObjectNode bad = (ObjectNode) example.get("minimum").deepCopy(); ((ObjectNode) bad.get("snapshot")).put(field, 999);
            var foreign = LifestyleMinCodec.decode(StrictJson.canonical(bad));
            assertThrows(ContractViolationException.class, () -> LifestyleScopePolicy.applyToMinimum(foreign, scope, false), field);
        }
        ObjectNode unknown = (ObjectNode) example.get("minimum").deepCopy(); unknown.putObject("pending_action").put("status", "action_state_unknown");
        var result = LifestyleScopePolicy.choose(LifestyleMinCodec.decode(StrictJson.canonical(unknown)), scope, false, LifestyleMinPolicy.Field.missing());
        assertEquals(LifestyleMinPolicy.Status.ACTION_STATE_UNKNOWN, result.status());
        assertNull(((LifestyleMinPolicy.MinimumDecision) result).decision().selectedAction());
    }
}
