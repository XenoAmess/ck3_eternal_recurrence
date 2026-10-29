package org.xar.ck3.control.wave2.governance.educationneeds;

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
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;

final class EducationNeedsComposerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode fixture() throws IOException {
        try (InputStream input = EducationNeedsComposerTest.class.getResourceAsStream("/educationneeds/producer-consumer-golden.json")) { assertNotNull(input, "committed real producer/consumer golden required"); return JSON.readTree(input); }
    }
    private static ObjectNode request() throws IOException { return (ObjectNode) fixture().get("request").deepCopy(); }
    private static JsonNode compose(JsonNode request) throws IOException { return JSON.readTree(EducationNeedsComposer.compose(JSON.writeValueAsBytes(request))); }
    private static JsonNode firstRow(JsonNode request) throws IOException { return compose(request).get("rows").get(0); }
    private static ObjectNode variant(ObjectNode base, String name) {
        ObjectNode request = base.deepCopy();
        if (name.equals("no_attachments")) { for (String key : List.of("child_relation_materials", "child_education_provider_inputs", "child_education_provider_source")) { request.putNull(key); } }
        else if (name.equals("no_decision")) { request.putNull("decision_inputs"); }
        else if (name.equals("unavailable_provider")) { ObjectNode provider = (ObjectNode) request.get("child_education_provider_inputs"); provider.put("status", "unavailable").put("unavailable_reason", "fixture_provider_unavailable").put("roster_complete", false).put("collection_available", false).put("child_observation_complete", false).putArray("rows"); }
        return request;
    }
    private static ObjectNode noHeirRequest() throws IOException {
        ObjectNode result = request();
        ObjectNode decision = (ObjectNode) result.get("decision_inputs");
        ((ObjectNode) decision.get("frame")).putNull("heir_character_id");
        ((ObjectNode) decision.get("children")).putArray("rows");
        decision.putArray("education_rows"); decision.put("known_empty", true);
        ObjectNode provider = (ObjectNode) result.get("child_education_provider_inputs");
        provider.put("heir_character_full_id", 4_294_967_295L); provider.putArray("rows");
        ((ObjectNode) result.get("child_education_provider_source")).putNull("heir_character_id");
        return result;
    }
    @Test void explicitNoHeirNativeSentinelPreservesNullableProofAndKnownEmptyNeeds() throws IOException {
        ObjectNode request = noHeirRequest(); JsonNode result = compose(request);
        assertEquals(0, result.get("rows").size()); assertTrue(result.get("known_empty").booleanValue());
        assertTrue(result.at("/frame/heir_character_id").isNull());
        assertEquals(request.get("child_education_provider_inputs"), result.get("query_owned_education_provider_inputs_v1"));
        assertEquals(request.get("child_education_provider_source"), result.get("query_owned_education_provider_inputs_source_v1"));
        assertEquals(result, compose(JSON.readTree(JSON.writeValueAsBytes(request))));
    }
    @Test void nullableHeirProofNeverAcceptsMissingBoolFloatStringOrZeroAsNull() throws IOException {
        ObjectNode missing = noHeirRequest(); ((ObjectNode) missing.get("child_education_provider_source")).remove("heir_character_id");
        assertThrows(IllegalArgumentException.class, () -> compose(missing));
        for (String token : List.of("true", "1.0", "\"0\"")) {
            ObjectNode changed = noHeirRequest();
            ((ObjectNode) changed.get("child_education_provider_source")).put("heir_character_id", 987_654_321L);
            String before = JSON.writeValueAsString(changed);
            String wire = before.replace("\"heir_character_id\":987654321", "\"heir_character_id\":" + token);
            assertFalse(before.equals(wire), "actual raw token injection must change the wire");
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                    () -> EducationNeedsComposer.compose(wire.getBytes(StandardCharsets.UTF_8)), token);
            assertTrue(error.getMessage().contains("integer"), error.getMessage());
        }
        ObjectNode zero = noHeirRequest(); ((ObjectNode) zero.get("child_education_provider_source")).put("heir_character_id", 0);
        assertThrows(IllegalArgumentException.class, () -> compose(zero));
        ObjectNode drift = noHeirRequest(); ((ObjectNode) drift.at("/decision_inputs/frame")).put("heir_character_id", 0);
        assertThrows(IllegalArgumentException.class, () -> compose(drift));
        ObjectNode rows = noHeirRequest(); ((ObjectNode) rows.get("child_education_provider_inputs")).set("rows", request().get("child_education_provider_inputs").get("rows"));
        assertThrows(IllegalArgumentException.class, () -> compose(rows));
    }
    @Test void actualRetainedP43ProducerNeedsConsumerEntireOutputMatches() throws IOException, NoSuchAlgorithmException {
        JsonNode root = fixture(); assertEquals(0, root.get("provenance").get("producer_exit_code").intValue()); assertTrue(root.get("provenance").get("source_before_after_unchanged").booleanValue());
        assertTrue(root.get("actual_guardian_scope_consumer").isArray());
        for (JsonNode testCase : root.get("cases")) { assertDigest(testCase.get("expected"), compose(variant(request(), testCase.get("name").textValue()))); }
    }
    @Test void completeJavaUpstreamProducerToNeedsChainMatchesActualOriginalChain() throws IOException, NoSuchAlgorithmException {
        Path baseline = Path.of("..", "governance-policy", "src", "test", "resources", "education", "producer-golden.json");
        assertTrue(Files.isRegularFile(baseline), "tracked shared upstream fixture must be in the reactor source closure"); byte[] original = Files.readAllBytes(baseline);
        String ref = "java/ck3-control/governance-policy/src/test/resources/education/producer-golden.json";
        assertEquals(fixture().get("provenance").get("source_sha256").get(ref).textValue(), digest(original));
        JsonNode input = JSON.readTree(original);
        for (JsonNode testCase : fixture().get("upstream_cases")) {
            JsonNode descendants = input.get("cases").get(testCase.get("index").intValue()).get("input");
            assertDigest(testCase.get("expected"), JSON.readTree(EducationNeedsComposer.composeFromDescendants(JSON.writeValueAsBytes(descendants))));
        }
    }
    @Test void actualNativeFinalPairProjectionAndEveryAvailabilityBranchMatch() throws IOException {
        JsonNode row = firstRow(request()), root = fixture();
        for (JsonNode testCase : root.get("candidate_cases")) {
            ObjectNode context = (ObjectNode) root.get("ordinary_context_projection").deepCopy(); String name = testCase.get("name").textValue();
            if (name.equals("other_child")) { ((ObjectNode) context.get("effective_roles")).put("secondary_recipient_id", 501); }
            else if (name.equals("known_null_guardian")) { ((ObjectNode) context.get("effective_roles")).putNull("secondary_actor_id"); }
            else if (name.equals("other_interaction")) { context.put("interaction_key", "offer_vassalization_interaction"); }
            else if (name.equals("unavailable_context")) { context.put("status", "unavailable").put("unavailable_reason", "fixture_context_unavailable"); }
            assertEquals(testCase.get("expected"), JSON.readTree(EducationNeedsComposer.requestCandidate(JSON.writeValueAsBytes(row), JSON.writeValueAsBytes(context))), name);
        }
    }
    @Test void nativePairObservationRemainsUsefulEvenWhenCanSendIsFalse() throws IOException {
        JsonNode context = fixture().get("ordinary_context_projection"), row = firstRow(request());
        EducationNeedsModel.RequestCandidate result = EducationNeedsComposer.candidateProjection(JSON.writeValueAsBytes(row), JSON.writeValueAsBytes(context));
        assertTrue(result.available()); assertFalse(result.canSend()); assertNotNull(result.guardianFullId());
        assertEquals(row.get("raw_character_id").longValue(), result.childFullId());
    }
    @Test void rawFloatBoolAndStringFullIdTokensReachTheIntegerRejectPath() throws IOException {
        ObjectNode base = request(); long child = base.get("decision_inputs").get("children").get("rows").get(0).get("raw_character_id").longValue();
        String source = JSON.writeValueAsString(base), pattern = "\"raw_character_id\":" + child;
        for (String token : List.of(child + ".0", "true", "\"" + child + "\"")) {
            String changed = source.replaceFirst(pattern, "\"raw_character_id\":" + token); assertFalse(changed.equals(source));
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class, () -> EducationNeedsComposer.compose(changed.getBytes(StandardCharsets.UTF_8)));
            assertTrue(error.getMessage().contains("integer"), error.getMessage());
        }
    }
    @Test void sourceProofIsRequiredAndSameQueryIdentityCannotDrift() throws IOException {
        ObjectNode missing = request(); missing.putNull("child_education_provider_source"); assertThrows(IllegalArgumentException.class, () -> compose(missing));
        ObjectNode changed = request(); ObjectNode source = (ObjectNode) changed.get("child_education_provider_source"); source.put("native_revision", source.get("native_revision").longValue() + 1);
        assertThrows(IllegalArgumentException.class, () -> compose(changed));
    }
    @Test void providerOccurrenceGroupMismatchDoesNotBecomeAnUnobservedOrEmptyChild() throws IOException {
        ObjectNode changed = request(); ((ObjectNode) changed.get("child_education_provider_inputs").get("rows").get(0)).putArray("occurrence_indices").add(99);
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class, () -> compose(changed)); assertTrue(error.getMessage().contains("projection changed"));
    }
    @Test void absentMaterialObservationDoesNotInventGuardianMembership() throws IOException {
        ObjectNode changed = request(); ((ObjectNode) changed.get("child_relation_materials")).putArray("rows"); JsonNode material = firstRow(changed).get("relation_materials");
        assertTrue(material.get("observed").booleanValue()); assertTrue(material.get("collection_available").booleanValue()); assertTrue(material.get("observation").isNull());
        assertEquals("child_material_row_not_observed", material.get("unavailable_reason").textValue());
    }
    @Test void projectionOnlyProviderCannotAcquireM6OrGuardianAuthorityByFlag() throws IOException {
        for (String field : List.of("m6_inputs_complete", "guardian_role_equivalence_qualified")) {
            ObjectNode changed = request(); ((ObjectNode) changed.get("child_education_provider_inputs")).put(field, true); assertThrows(IllegalArgumentException.class, () -> compose(changed));
        }
        JsonNode row = firstRow(request()); assertFalse(row.get("education_provider_inputs").get("m6_inputs_complete").booleanValue()); assertFalse(row.get("education_provider_inputs").get("guardian_role_equivalence_qualified").booleanValue());
    }
    @Test void publicTypedPortRetainsIdentityOccurrenceAndFocusWithoutMutableJson() throws IOException {
        JsonNode row = firstRow(request()); EducationNeedsModel.NeedsRowProjection projection = EducationNeedsComposer.needsRowProjection(JSON.writeValueAsBytes(row));
        assertEquals(row.get("raw_character_id").longValue(), projection.childFullId()); assertEquals(row.get("focus_management").get("state").textValue(), projection.focusManagement().state().wire());
        assertThrows(UnsupportedOperationException.class, () -> projection.occurrenceIndices().add(999));
    }
    @Test void persistenceRoundTripPreservesFullWireDomainAndExplicitNullAttachments() throws IOException {
        ObjectNode initial = request(); JsonNode result = compose(initial); assertEquals(result, compose(JSON.readTree(JSON.writeValueAsBytes(initial))));
        JsonNode noAttachments = compose(variant(initial, "no_attachments")); assertFalse(noAttachments.has("query_owned_education_provider_inputs_v1"));
        assertFalse(noAttachments.get("rows").get(0).has("education_provider_inputs"));
        ((ObjectNode) initial.get("decision_inputs").get("children").get("rows").get(0).get("values")).set("opaque_float", JSON.readTree("1.0"));
        assertTrue(firstRow(initial).get("values").get("opaque_float").isFloatingPointNumber(), "unused SDK float 1.0 must retain its JSON number domain");
    }
    @Test void exactNewWrapperAndBoundedUtf8RejectMissingDuplicateUnknownAndOversize() throws IOException {
        ObjectNode missing = request(); missing.remove("decision_inputs"); assertThrows(IllegalArgumentException.class, () -> compose(missing));
        ObjectNode unknown = request(); unknown.put("legacy_alias", true); assertThrows(IllegalArgumentException.class, () -> compose(unknown));
        assertThrows(IllegalArgumentException.class, () -> EducationNeedsComposer.compose("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EducationNeedsComposer.compose(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> EducationNeedsComposer.compose(new byte[EducationNeedsCodec.MAX_BYTES + 1]));
    }
    private static void assertDigest(JsonNode expected, JsonNode actual) throws IOException, NoSuchAlgorithmException { byte[] bytes = JSON.writeValueAsBytes(sorted(actual)); assertEquals(expected.get("bytes").intValue(), bytes.length); assertEquals(expected.get("sha256").textValue(), digest(bytes)); }
    private static String digest(byte[] bytes) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
    private static JsonNode sorted(JsonNode node) { if (node.isObject()) { ObjectNode result = JSON.createObjectNode(); TreeSet<String> keys = new TreeSet<>(); node.fieldNames().forEachRemaining(keys::add); for (String key : keys) { result.set(key, sorted(node.get(key))); } return result; } if (node.isArray()) { com.fasterxml.jackson.databind.node.ArrayNode result = JSON.createArrayNode(); for (JsonNode value : node) { result.add(sorted(value)); } return result; } return node; }
}
