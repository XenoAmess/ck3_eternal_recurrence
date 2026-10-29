package org.xar.ck3.control.wave2.military.exitresult;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation.Receipt;

final class OrdinaryWarExitObservationTest {
    @TestFactory
    Stream<DynamicTest> actualUnmodifiedComposerAndNormalizerVectors() throws IOException {
        JsonNode fixture = fixture();
        assertEquals("xar.ck3.java.exitresult.golden.v1", fixture.get("schema").textValue());
        assertEquals(5, fixture.get("original_unit_tests").intValue());
        assertEquals(0, fixture.get("original_failures").intValue());
        assertEquals(0, fixture.get("original_errors").intValue());
        assertEquals(18, fixture.get("cases").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                JsonNode actual = StrictJson.parse(OrdinaryWarExitObservationCodec.evaluate(bytes(input(vector))));
                assertEquals(vector.get("expected"), actual);
                assertUnknownResultIdentity(actual);
            }));
        }
        return tests.stream();
    }

    @Test
    void largeTargetVectorRendersExactly32AndRetainsOmittedCount() throws IOException, NoSuchAlgorithmException {
        JsonNode large = resource("large-targets-golden-v1.json");
        String mainSha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(resourceBytes("producer-golden-v1.json")));
        assertEquals(mainSha, large.get("main_golden_sha256").textValue());
        JsonNode actual = StrictJson.parse(OrdinaryWarExitObservationCodec.evaluate(bytes(large.get("input"))));
        assertEquals(large.get("expected"), actual);
        assertEquals(32, actual.get("target_title_ids").size());
        assertEquals(4096, actual.get("target_title_count").intValue());
        assertEquals(4064, actual.get("target_titles_omitted").intValue());
        assertUnknownResultIdentity(actual);
    }

    @Test
    void rootAdapterRequiresNullableFieldsAndRejectsAliases() throws IOException {
        for (String field : List.of("before_snapshot", "post_snapshot", "action_result", "claims_result", "title_holder_results", "truce_result")) {
            ObjectNode input = base(); input.remove(field);
            assertThrows(ContractViolationException.class, () -> OrdinaryWarExitObservationCodec.decodeAndCompose(bytes(input)));
        }
        ObjectNode extra = base(); extra.putNull("after_snapshot");
        assertThrows(ContractViolationException.class, () -> OrdinaryWarExitObservationCodec.decodeAndCompose(bytes(extra)));
        ObjectNode noQueries = base(); noQueries.putNull("claims_result"); noQueries.putNull("title_holder_results"); noQueries.putNull("truce_result");
        JsonNode actual = evaluate(noQueries);
        assertEquals("not_observed", actual.get("claims").get("status").textValue());
        assertTrue(actual.get("claims").get("rows").isNull());
        assertEquals(0, actual.get("titles").get("rows").size());
    }

    @Test
    void frameBoolFloatStringAndNullNeverBindAsIntegerIdentity() throws IOException {
        for (String which : List.of("before_snapshot", "post_snapshot")) {
            for (String field : List.of("revision", "native_revision", "date_raw")) {
                String correct = base().get(which).get(field).bigIntegerValue().toString();
                for (String token : List.of("true", correct + ".0", "\"" + correct + "\"", "null")) {
                    ObjectNode input = base();
                    JsonNode result = evaluateRaw(rawField(input, (ObjectNode) input.get(which), field, token));
                    assertEquals("unbound", result.get("status").textValue());
                    assertTrue(result.get("war_absence_observed").isNull());
                    assertEquals(0, result.get("resources").size());
                }
            }
        }
    }

    @Test
    void rawFixedScaleAndIntegerValuesMustRetainActualTypes() throws IOException {
        for (String field : List.of("raw", "scale")) {
            ObjectNode input = base();
            ObjectNode fixed = (ObjectNode) input.get("post_snapshot").get("played_character_gold");
            String value = fixed.get(field).bigIntegerValue().toString();
            JsonNode result = evaluateRaw(rawField(input, fixed, field, value + ".0"));
            assertTrue(result.get("war_absence_observed").booleanValue());
            assertEquals("unavailable", result.get("resources").get("gold").get("status").textValue());
            assertTrue(result.get("resources").get("gold").get("delta_raw").isNull());
        }
        ObjectNode outside = base();
        ((ObjectNode) outside.get("post_snapshot").get("played_character_gold")).put("raw", BigInteger.ONE.shiftLeft(63));
        assertEquals("unavailable", evaluate(outside).get("resources").get("gold").get("status").textValue());
    }

    @Test
    void optionalClaimTypeFailuresDoNotEraseObservedWarAbsence() throws IOException {
        for (String field : List.of("schema_version", "snapshot_revision", "date_raw", "actor_character_id")) {
            ObjectNode input = base();
            ObjectNode claim = (ObjectNode) input.get("claims_result").get("player_claims");
            String value = claim.get(field).bigIntegerValue().toString();
            JsonNode result = evaluateRaw(rawField(input, claim, field, value + ".0"));
            assertTrue(result.get("war_absence_observed").booleanValue());
            assertEquals("unavailable", result.get("claims").get("status").textValue());
            assertTrue(result.get("issues").size() > 0);
            assertUnknownResultIdentity(result);
        }
        ObjectNode unknown = base();
        ((ObjectNode) unknown.get("claims_result").get("player_claims").get("claims").get(0)).put("present", 0);
        assertEquals("unavailable", evaluate(unknown).get("claims").get("status").textValue());
    }

    @Test
    void titleNormalizerRejectsWrongTierKeyAndUnheldIdentityLaundering() throws IOException {
        ObjectNode mismatch = base(); holder(mismatch).put("title_key", "d_wrong_tier");
        assertEquals("unavailable", evaluate(mismatch).get("titles").get("status").textValue());
        ObjectNode missingKey = base(); holder(missingKey).remove("title_key_unavailable_reason");
        assertEquals("unavailable", evaluate(missingKey).get("titles").get("status").textValue());
        ObjectNode unheld = base(); holder(unheld).putNull("holder_character_id");
        assertEquals("unavailable", evaluate(unheld).get("titles").get("status").textValue());
        for (String field : List.of("schema_version", "title_id", "actor_character_id", "title_tier_raw")) {
            ObjectNode input = base(); ObjectNode row = holder(input);
            JsonNode actual = evaluateRaw(rawField(input, row, field, row.get(field).bigIntegerValue() + ".0"));
            assertTrue(actual.get("war_absence_observed").booleanValue());
            assertEquals("unavailable", actual.get("titles").get("status").textValue());
        }
    }

    @Test
    void truceNormalizerPreservesDirectionAbsenceUnknownAndRawIntegerTokenChecks() throws IOException {
        for (String field : List.of("schema_version", "snapshot_revision", "owner_character_id", "toward_character_id", "expiry_date_raw")) {
            ObjectNode input = base();
            ObjectNode truce = (ObjectNode) input.get("truce_result").get("raiktor_actual_truce_expiry");
            String value = truce.get(field).bigIntegerValue().toString();
            JsonNode actual = evaluateRaw(rawField(input, truce, field, value + ".0"));
            assertEquals("unavailable", actual.get("truce").get("status").textValue());
            assertTrue(actual.get("truce").get("expiry_date_raw").isNull());
            assertTrue(actual.get("war_absence_observed").booleanValue());
        }
        ObjectNode unknown = base();
        ((ObjectNode) unknown.get("truce_result").get("raiktor_actual_truce_expiry")).put("status", "unavailable");
        assertEquals("unavailable", evaluate(unknown).get("truce").get("status").textValue());
    }

    @Test
    void optionalQueryBindingTypesAndSequenceMustNotBeLabelsOnly() throws IOException {
        for (String domain : List.of("claims_result", "truce_result")) {
            for (String field : List.of("query_sequence", "queried_revision", "queried_native_revision")) {
                ObjectNode input = base(); ObjectNode result = (ObjectNode) input.get(domain);
                String value = result.get(field).bigIntegerValue().toString();
                JsonNode actual = evaluateRaw(rawField(input, result, field, value + ".0"));
                assertEquals("unavailable", actual.get(domain.equals("claims_result") ? "claims" : "truce").get("status").textValue());
                assertTrue(actual.get("war_absence_observed").booleanValue());
            }
        }
    }

    @Test
    void sdkExtensionsRemainProjectedButFrozenTargetDuplicatesReject() throws IOException {
        ObjectNode extended = base();
        ((ObjectNode) extended.get("before_snapshot")).putObject("future_sdk_container").put("opaque", true);
        ((ObjectNode) extended.get("claims_result").get("player_claims")).put("future_additive_metadata", "ignored");
        assertEquals("war_absent", evaluate(extended).get("status").textValue());
        ObjectNode duplicate = base();
        ((ArrayNode) duplicate.get("before_snapshot").get("active_wars").get(0).get("targeted_title_ids")).add(2132);
        assertEquals("unbound", evaluate(duplicate).get("status").textValue());
        ObjectNode duplicateResults = base();
        ArrayNode results = (ArrayNode) duplicateResults.get("title_holder_results");
        results.add(results.get(0).deepCopy());
        assertEquals("unavailable", evaluate(duplicateResults).get("titles").get("status").textValue());
    }

    @Test
    void resultEncodingIsImmutableAndRoundTripsWithoutAttributionOrIdentityCredit() throws IOException {
        Receipt receipt = OrdinaryWarExitObservationCodec.decodeAndCompose(bytes(base()));
        assertThrows(UnsupportedOperationException.class, () -> receipt.issues().clear());
        assertThrows(UnsupportedOperationException.class, () -> receipt.bound().renderedTitleIds().clear());
        byte[] first = OrdinaryWarExitObservationCodec.encode(receipt);
        assertEquals(new String(first, StandardCharsets.UTF_8), new String(StrictJson.canonical(StrictJson.parse(first)), StandardCharsets.UTF_8));
        assertUnknownResultIdentity(StrictJson.parse(first));
    }

    @Test
    void malformedJsonFailsBeforeAnyObservationConstruction() {
        for (byte[] raw : List.of("{\"action_result\":null,\"action_result\":null}".getBytes(StandardCharsets.UTF_8),
                "{} {}".getBytes(StandardCharsets.UTF_8), new byte[]{(byte) 0xc3, 0x28}, new byte[65_537])) {
            assertThrows(ContractViolationException.class, () -> OrdinaryWarExitObservationCodec.decodeAndCompose(raw));
        }
    }

    private static ObjectNode input(JsonNode vector) throws IOException {
        ObjectNode input = base();
        for (JsonNode patch : vector.get("patches")) {
            JsonNode path = patch.get("path"); JsonNode owner = input;
            for (int index = 0; index < path.size() - 1; index++) {
                owner = path.get(index).isIntegralNumber() ? owner.get(path.get(index).intValue()) : owner.get(path.get(index).textValue());
            }
            JsonNode last = path.get(path.size() - 1);
            if (last.isIntegralNumber()) { ((ArrayNode) owner).set(last.intValue(), patch.get("value").deepCopy()); }
            else { ((ObjectNode) owner).set(last.textValue(), patch.get("value").deepCopy()); }
        }
        return input;
    }
    private static void assertUnknownResultIdentity(JsonNode result) {
        if (result.isNull()) { return; }
        assertTrue(result.get("observed_result_identity").isNull());
        assertEquals("no_independent_result_observer", result.get("result_identity_reason").textValue());
        for (JsonNode resource : result.get("resources")) { assertEquals("unproven", resource.get("action_attribution").textValue()); }
        assertFalse(result.has("action_literal"));
    }
    private static ObjectNode holder(ObjectNode input) { return (ObjectNode) input.get("title_holder_results").get(0).get("title_holder"); }
    private static JsonNode evaluate(ObjectNode input) { return evaluateRaw(bytes(input)); }
    private static JsonNode evaluateRaw(byte[] raw) { return StrictJson.parse(OrdinaryWarExitObservationCodec.evaluate(raw)); }
    private static byte[] rawField(ObjectNode input, ObjectNode owner, String field, String token) {
        owner.put(field, "$exit-result-raw-token$");
        return input.toString().replace("\"$exit-result-raw-token$\"", token).getBytes(StandardCharsets.UTF_8);
    }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode base() throws IOException { return (ObjectNode) fixture().get("base_input").deepCopy(); }
    private static JsonNode fixture() throws IOException { return resource("producer-golden-v1.json"); }
    private static JsonNode resource(String name) throws IOException { return StrictJson.parse(resourceBytes(name)); }
    private static byte[] resourceBytes(String name) throws IOException {
        try (InputStream stream = OrdinaryWarExitObservationTest.class.getResourceAsStream("/exitresult/" + name)) {
            if (stream == null) { throw new IOException("committed actual-producer fixture missing: " + name); }
            return stream.readAllBytes();
        }
    }
}
