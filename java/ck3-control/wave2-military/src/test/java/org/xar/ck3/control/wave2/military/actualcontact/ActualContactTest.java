package org.xar.ck3.control.wave2.military.actualcontact;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Query;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel.Scope;

final class ActualContactTest {
    private static final ObjectMapper WIRE = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ActualContactTest.class.getResourceAsStream("/actualcontact/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed actual producer golden required"); }
            return WIRE.readTree(stream);
        }
    }
    private static ObjectNode base(String name) throws IOException { return (ObjectNode) golden().get("bases").get(name).deepCopy(); }
    private static byte[] bytes(JsonNode value) throws IOException { return WIRE.writeValueAsBytes(value); }

    @TestFactory Stream<DynamicTest> unchangedProducerOrdinaryCasesAndExplicitVersionFixes() throws IOException {
        JsonNode fixture = golden(); assertEquals("xar.actual-contact-producer-golden/v1", fixture.get("schema").textValue());
        assertTrue(fixture.get("cases").size() >= 50);
        return java.util.stream.StreamSupport.stream(fixture.get("cases").spliterator(), false).map(item ->
                DynamicTest.dynamicTest(item.get("name").textValue(), () -> {
                    ObjectNode input = (ObjectNode) fixture.get("bases").get(item.get("base").textValue()).deepCopy();
                    for (JsonNode patch : item.get("patches")) { apply(input, patch); }
                    byte[] raw = bytes(input);
                    if (item.has("intentional_type_fix")) {
                        assertEquals("schema_version_must_be_integer_token", item.get("intentional_type_fix").textValue());
                        assertEquals(1, item.get("legacy_expected").get("schema_version").intValue(), "original acceptance must remain recorded");
                        assertTrue(input.get("scope").get("schema_version").isBoolean()
                                || input.get("scope").get("schema_version").isFloatingPointNumber());
                        assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(raw));
                    } else if (item.get("legacy_expected").has("error")) {
                        assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(raw));
                    } else { assertEquals(item.get("legacy_expected"), StrictJson.parse(ActualContactCodec.normalize(raw))); }
                }));
    }
    @TestFactory Stream<DynamicTest> actualProducerQueryBuilderAndParser() throws IOException {
        JsonNode cases = golden().get("query_cases");
        return java.util.stream.StreamSupport.stream(cases.spliterator(), false).map(item ->
                DynamicTest.dynamicTest(item.get("name").textValue(), () -> {
                    byte[] raw = bytes(item.get("input"));
                    if (item.get("expected").has("error")) { assertThrows(ContractViolationException.class, () -> ActualContactCodec.query(raw)); }
                    else { assertEquals(item.get("expected"), StrictJson.parse(ActualContactCodec.query(raw))); }
                }));
    }
    private static void apply(ObjectNode input, JsonNode patch) {
        JsonNode path = patch.get("path"); JsonNode target = input;
        for (int index = 0; index < path.size() - 1; index++) {
            JsonNode key = path.get(index); target = key.isIntegralNumber() ? target.get(key.intValue()) : target.get(key.textValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (target instanceof ObjectNode object) {
            if (patch.get("op").textValue().equals("remove")) { object.remove(key.textValue()); }
            else { object.set(key.textValue(), patch.get("value").deepCopy()); }
        } else if (target instanceof ArrayNode array && key.isIntegralNumber()) {
            if (patch.get("op").textValue().equals("remove")) { array.remove(key.intValue()); }
            else { array.set(key.intValue(), patch.get("value").deepCopy()); }
        } else { throw new IllegalArgumentException("invalid frozen producer patch"); }
    }

    @Test void actualVersionTokenFixReceivesUnmodifiedTrueAndFloatBytes() throws IOException {
        String baseline = new String(bytes(base("new_attacker")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "1e0", "\"1\"")) {
            String raw = baseline.replace("\"schema_version\":1", "\"schema_version\":" + token);
            assertTrue(raw.contains("\"schema_version\":" + token));
            assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(raw.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test void serializedScopeRoundTripPreservesRawDuplicateOpponentEvidence() throws IOException {
        ObjectNode input = base("new_attacker");
        ((ObjectNode) input.get("scope")).putArray("opponent_army_ids").add(31).add(31).add(41);
        Scope scope = ActualContactCodec.decodeScope(input.get("scope"));
        assertEquals(List.of(31, 31, 41), scope.opponentArmyIds());
        assertEquals(scope, ActualContactCodec.decodeScope(StrictJson.parse(StrictJson.canonical(ActualContactCodec.encodeScope(scope)))));
        assertThrows(UnsupportedOperationException.class, () -> scope.opponentArmyIds().add(51));
    }

    @Test void firstSeenFinalInsertionDoesNotSortRawOpponentOrder() throws IOException {
        ObjectNode input = base("new_attacker"); ObjectNode scope = (ObjectNode) input.get("scope");
        scope.putArray("opponent_army_ids").add(41).add(31).add(41); scope.putArray("defender_army_ids").add(41).add(31);
        JsonNode normalized = StrictJson.parse(ActualContactCodec.normalize(bytes(input)));
        assertEquals(41, normalized.get("defender_army_ids").get(0).intValue());
        assertEquals(3, normalized.get("opponent_army_ids").size());
    }

    @Test void uint64MaximumRemainsExactAcrossCodec() throws IOException {
        ObjectNode input = base("new_attacker"); BigInteger value = StrictJson.UINT64_MAX;
        ((ObjectNode) input.get("scope")).put("snapshot_revision", value); ((ObjectNode) input.get("expected")).put("snapshot_revision", value);
        assertEquals(value, StrictJson.parse(ActualContactCodec.normalize(bytes(input))).get("snapshot_revision").bigIntegerValue());
    }

    @Test void requiredNullAndAbsentAreDifferentAndUnknownFieldsReject() throws IOException {
        ObjectNode input = base("new_attacker"); ((ObjectNode) input.get("scope")).remove("selected_combat_id");
        byte[] missing = bytes(input); assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(missing));
        ((ObjectNode) input.get("scope")).putNull("selected_combat_id");
        assertEquals("create_new", StrictJson.parse(ActualContactCodec.normalize(bytes(input))).get("transition_kind").textValue());
        input.put("alias", true); byte[] unknown = bytes(input);
        assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(unknown));
    }

    @Test void rawNativeCarmyAndExpectedRevisionCannotCoerceFloat() throws IOException {
        ObjectNode input = base("new_attacker"); ((ObjectNode) input.get("scope")).set("subject_native_carmy_id", WIRE.readTree("101.0"));
        byte[] nativeFloat = bytes(input); assertTrue(new String(nativeFloat, StandardCharsets.UTF_8).contains("101.0"));
        assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(nativeFloat));
        ObjectNode next = base("new_attacker"); ((ObjectNode) next.get("expected")).set("snapshot_revision", WIRE.readTree("17.0"));
        byte[] revisionFloat = bytes(next); assertThrows(ContractViolationException.class, () -> ActualContactCodec.normalize(revisionFloat));
    }

    @Test void canonicalQueryZeroAndInt32MaximumStayInTheirIdentityLanes() {
        for (int subject : List.of(0, Integer.MAX_VALUE)) {
            Query query = new Query(subject, 2585); assertEquals(query, ActualContactModel.parseStep(query.step()).orElseThrow());
        }
        assertThrows(ContractViolationException.class, () -> new Query(0, 0));
        for (String malformed : List.of("query-actual-contact-scope-v1-00-at-2585", "query-actual-contact-scope-v1-0-at-0",
                "query-actual-contact-scope-v1-2147483648-at-2585", "query-actual-contact-scope-v1-0-at-2585-at-7")) {
            assertTrue(ActualContactModel.parseStep(malformed).isEmpty());
        }
    }
}
