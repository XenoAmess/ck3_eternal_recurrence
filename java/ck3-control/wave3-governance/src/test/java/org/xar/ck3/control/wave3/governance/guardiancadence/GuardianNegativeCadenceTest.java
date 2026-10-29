package org.xar.ck3.control.wave3.governance.guardiancadence;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsCodec;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceModel.*;

class GuardianNegativeCadenceTest {
    @Test void originalCompletedP43ChainAndExplicitDeltasMatchLegacyProducer() throws IOException {
        JsonNode golden = golden(); assertEquals(3, golden.get("bases").size()); assertEquals(19, golden.get("cases").size());
        for (JsonNode sample : golden.get("cases")) {
            Input input = GuardianCadenceCodec.decode(StrictJson.canonical(input(sample, golden)));
            assertEquals(input, GuardianCadenceCodec.projectParsedInput(input(sample, golden)));
            Evaluation result = GuardianNegativeCadence.evaluate(input);
            assertEquals(sample.get("expected"), StrictJson.parse(GuardianCadenceCodec.encodeEvaluation(result)), sample.get("name").textValue());
            assertEquals(result.after().state(), GuardianCadenceCodec.decodeState(GuardianCadenceCodec.encodeState(result.after().state())), sample.get("name").textValue());
        }
    }

    @Test void firstDateOnlyDeduplicatesSameFrameAndSecondDistinctDateStartsBoundedDefer() throws IOException {
        Evaluation first = evaluate("actual-first-date"); NegativeRecord record = first.after().state().records().values().iterator().next();
        assertEquals(1, record.count()); assertTrue(record.cooldownUntilDateRaw().isEmpty()); assertTrue(first.deferredBefore().isEmpty());
        Evaluation same = evaluate("same-frame-no-double-count"); assertEquals(DeferStatus.SAME_FRAME, same.deferredBefore().orElseThrow().status());
        assertTrue(same.after().observation().isEmpty()); assertEquals(first.after().state(), same.after().state());
        Evaluation second = evaluate("actual-second-date"); NegativeObserved observed = second.after().observation().orElseThrow();
        assertEquals(2, observed.consecutiveObservedDates());
        assertEquals(observed.lastObservedDateRaw().add(BigInteger.valueOf(720)), observed.cooldownUntilDateRaw().orElseThrow());
        assertEquals(DeferStatus.POLICY_DEFERRED, evaluate("actual-later-policy-defer").deferredBefore().orElseThrow().status());
        assertTrue(evaluate("expiry-requires-new-query").deferredBefore().isEmpty());
        assertTrue(evaluate("backwards-date-no-reuse").deferredBefore().isEmpty());
    }

    @Test void changedProcessEpisodeHeirAgeAndProviderInvalidateOnlyMatchingReuse() throws IOException {
        for (String name : List.of("scope-change-bridge_pid", "scope-change-connection_generation", "scope-change-actor_character_id",
                "scope-change-episode_run_id", "scope-change-heir", "scope-change-age", "scope-change-provider", "missing-named-source")) {
            Evaluation result = evaluate(name); assertTrue(result.deferredBefore().isEmpty(), name); assertTrue(result.after().observation().isEmpty(), name);
        }
        ObjectNode changedFocus = sampleInput("actual-later-policy-defer");
        ((ObjectNode) changedFocus.at("/needs/focus_management")).put("state", "education_focus_present").put("current_key", "education_martial");
        assertTrue(GuardianNegativeCadence.evaluate(GuardianCadenceCodec.decode(StrictJson.canonical(changedFocus))).deferredBefore().isEmpty());
    }

    @Test void twoActualDistinctNegativeQueriesAndCorrectExplicitMaterializationAreMandatory() throws IOException {
        for (String name : List.of("second-query-can-send", "duplicate-query-sequence", "different-definition", "not-selected-option-variant", "wrong-selected-step")) {
            Evaluation result = evaluate(name); assertTrue(result.after().observation().isEmpty(), name); assertTrue(result.after().state().records().isEmpty(), name);
        }
        ObjectNode multiple = sampleInput("actual-first-date");
        ArrayNode attempts = (ArrayNode) multiple.get("attempts"); attempts.add(attempts.get(0).deepCopy());
        assertTrue(GuardianNegativeCadence.evaluate(GuardianCadenceCodec.decode(StrictJson.canonical(multiple))).after().observation().isEmpty());
        ObjectNode material = sampleInput("actual-first-date");
        ((ObjectNode) material.at("/attempts/0/query/character_interaction_ordinary_context/education_request_materialization")).put("guardian_full_id", 1);
        assertTrue(GuardianNegativeCadence.evaluate(GuardianCadenceCodec.decode(StrictJson.canonical(material))).after().state().records().isEmpty());
    }

    @Test void outputsNeverClaimFreshLegalityOrBusinessActionAndColdStartsEmpty() throws IOException {
        JsonNode deferred = StrictJson.parse(GuardianCadenceCodec.encodeEvaluation(evaluate("actual-later-policy-defer"))).get("deferred_before");
        assertEquals("unknown_without_fresh_query", deferred.get("current_native_legal_status").textValue());
        assertFalse(deferred.get("business_action_credit").booleanValue());
        JsonNode observed = StrictJson.parse(GuardianCadenceCodec.encodeEvaluation(evaluate("actual-first-date"))).get("observation");
        assertFalse(observed.get("business_action_credit").booleanValue());
        Input actual = GuardianCadenceCodec.decode(StrictJson.canonical(sampleInput("actual-later-policy-defer")));
        assertTrue(GuardianNegativeCadence.deferred(State.empty(), GuardianNegativeCadence.sourceScope(actual.frame(), actual.materials(), actual.heirId()), actual.frame()).isEmpty());
    }

    @Test void boolFloatStringNullIdentifiersAndNativeSequenceTokensReject() throws IOException {
        for (String bad : List.of("true", "1.0", "\"1\"", "null")) {
            byte[] input = rawToken(sampleInput("actual-first-date"), "/frame", "actor_character_id", bad);
            assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(input), bad);
            byte[] sequence = rawToken(sampleInput("actual-first-date"), "/default_query", "query_sequence", bad);
            assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(sequence), bad);
        }
        ObjectNode flag = sampleInput("actual-first-date");
        ((ObjectNode) flag.at("/attempts/0/query/character_interaction_ordinary_context")).put("frame_verified", 1); reject(flag);
        ObjectNode boolScope = sampleInput("actual-first-date");
        ((ObjectNode) boolScope.at("/needs/current_court_owner")).put("owner_character_id_raw", true); reject(boolScope);
    }

    @Test void stateTupleRoundTripUsesExactJsonDomainAndNeverAliasesMutableMaps() throws IOException {
        State state = evaluate("actual-second-date").after().state(); byte[] encoded = GuardianCadenceCodec.encodeState(state);
        assertEquals(state, GuardianCadenceCodec.decodeState(encoded)); assertThrows(UnsupportedOperationException.class, () -> state.records().clear());
        ObjectNode malformed = (ObjectNode) StrictJson.parse(encoded); String child = malformed.fieldNames().next();
        ((ObjectNode) malformed.get(child)).put("count", true);
        assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decodeState(malformed.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode tuple = (ObjectNode) StrictJson.parse(encoded);
        byte[] tupleWire = rawToken(tuple, "/" + child + "/scope", "1", "1.0");
        assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decodeState(tupleWire));
    }

    @Test void wrapperUnknownDuplicateMissingTrailingUtf8AndBudgetReject() throws IOException {
        ObjectNode unknown = sampleInput("actual-first-date"); unknown.put("source_qualified", true); reject(unknown);
        ObjectNode missing = sampleInput("actual-first-date"); missing.remove("state"); reject(missing);
        String text = sampleInput("actual-first-date").toString();
        assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(text.replaceFirst("\\{", "{\"schema\":\"duplicate\",").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode((text + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(new byte[65_537]));
    }


    @Test void originalDefaultAndSelectedMaterializationRetainSharedWireAndTypedCadenceStages() throws IOException {
        JsonNode golden = golden();
        for (JsonNode sample : golden.get("cases")) {
            ObjectNode raw = input(sample, golden);
            Input input = GuardianCadenceCodec.decode(StrictJson.canonical(raw));
            Materialization first = ((ObservedQuery) input.defaultQuery()).context().materialization().orElseThrow();
            Materialization second = ((ObservedQuery) input.attempts().getFirst().query()).context().materialization().orElseThrow();
            assertInstanceOf(IncompleteMaterialization.class, first);
            assertInstanceOf(CompleteMaterialization.class, second);
            assertEquals(raw.at("/default_query/character_interaction_ordinary_context/education_request_materialization"),
                    StrictJson.parse(EducationOptionsCodec.encodeMaterialization(first.observation())));
            assertEquals(raw.at("/attempts/0/query/character_interaction_ordinary_context/education_request_materialization"),
                    StrictJson.parse(EducationOptionsCodec.encodeMaterialization(second.observation())));
            assertEquals(first.observation(), EducationOptionsCodec.decodeMaterialization(EducationOptionsCodec.encodeMaterialization(first.observation())));
            assertEquals(second.observation(), EducationOptionsCodec.decodeMaterialization(EducationOptionsCodec.encodeMaterialization(second.observation())));
        }
    }

    @Test void legalPartialIntentRetainsNullVersusEmptyWithoutGainingCadenceEligibility() throws IOException {
        for (boolean retainPair : List.of(true, false)) {
            ObjectNode raw = sampleInput("actual-first-date");
            ObjectNode leaf = (ObjectNode) raw.at("/attempts/0/query/character_interaction_ordinary_context/education_request_materialization");
            if (retainPair) { leaf.putNull("requested_option_keys"); leaf.putNull("option_keys_match"); }
            else { leaf.putNull("child_full_id"); leaf.putNull("guardian_full_id"); leaf.putNull("pair_matches"); }
            Input input = GuardianCadenceCodec.decode(StrictJson.canonical(raw));
            Materialization stage = ((ObservedQuery) input.attempts().getFirst().query()).context().materialization().orElseThrow();
            assertInstanceOf(IncompleteMaterialization.class, stage);
            assertEquals(leaf, StrictJson.parse(EducationOptionsCodec.encodeMaterialization(stage.observation())));
            assertTrue(GuardianNegativeCadence.evaluate(input).after().state().records().isEmpty());
        }
        ObjectNode unavailable = sampleInput("actual-first-date");
        ObjectNode leaf = (ObjectNode) unavailable.at("/attempts/0/query/character_interaction_ordinary_context/education_request_materialization");
        leaf.put("status", "unavailable"); leaf.put("pair_matches", false); leaf.putNull("option_keys_match");
        leaf.put("unavailable_reason", "native_materialization_unavailable");
        Input input = GuardianCadenceCodec.decode(StrictJson.canonical(unavailable));
        Materialization stage = ((ObservedQuery) input.attempts().getFirst().query()).context().materialization().orElseThrow();
        assertInstanceOf(IncompleteMaterialization.class, stage);
        assertEquals(leaf, StrictJson.parse(EducationOptionsCodec.encodeMaterialization(stage.observation())));
        assertTrue(GuardianNegativeCadence.evaluate(input).after().state().records().isEmpty());
    }

    @Test void sharedMaterializationRejectsHalfPairsInconsistentMatchesAndWrongRawTokens() throws IOException {
        String pointer = "/attempts/0/query/character_interaction_ordinary_context/education_request_materialization";
        for (String bad : List.of("true", "1.0", "\"1\"")) {
            assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(
                    rawToken(sampleInput("actual-first-date"), pointer, "child_full_id", bad)), bad);
        }
        for (String field : List.of("child_full_id", "guardian_full_id", "pair_matches", "option_keys_match")) {
            ObjectNode half = sampleInput("actual-first-date"); ((ObjectNode) half.at(pointer)).putNull(field); reject(half);
        }
        for (String field : List.of("pair_matches", "option_keys_match")) {
            for (String bad : List.of("1", "1.0", "\"true\"")) {
                assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(
                        rawToken(sampleInput("actual-first-date"), pointer, field, bad)), field + bad);
            }
            ObjectNode mismatch = sampleInput("actual-first-date"); ((ObjectNode) mismatch.at(pointer)).put(field, false); reject(mismatch);
        }
        ObjectNode missing = sampleInput("actual-first-date"); ((ObjectNode) missing.at(pointer)).remove("requested_option_keys"); reject(missing);
        ObjectNode unknown = sampleInput("actual-first-date"); ((ObjectNode) unknown.at(pointer)).put("qualified_alias", true); reject(unknown);
    }

    private static void reject(ObjectNode input) { assertThrows(IllegalArgumentException.class, () -> GuardianCadenceCodec.decode(input.toString().getBytes(StandardCharsets.UTF_8))); }
    private static byte[] rawToken(ObjectNode input, String pointer, String field, String token) {
        BigInteger sentinel = new BigInteger("987654321098765432109876543210"); JsonNode parent = input.at(pointer);
        if (parent instanceof ObjectNode object) { object.put(field, sentinel); }
        else if (parent instanceof ArrayNode array) { array.set(Integer.parseInt(field), StrictJson.object().numberNode(sentinel)); }
        else { throw new IllegalStateException("test raw injection parent"); }
        String encoded = input.toString(), needle = sentinel.toString();
        assertTrue(encoded.contains(needle)); assertEquals(encoded.indexOf(needle), encoded.lastIndexOf(needle));
        String expectedParent = parent.toString().replace(needle, token), outgoing = encoded.replace(needle, token);
        assertTrue(outgoing.contains(expectedParent), "actual outgoing raw token retained: " + token); assertFalse(outgoing.contains(needle));
        return outgoing.getBytes(StandardCharsets.UTF_8);
    }
    private static Evaluation evaluate(String name) throws IOException { return GuardianNegativeCadence.evaluate(GuardianCadenceCodec.decode(StrictJson.canonical(sampleInput(name)))); }
    private static ObjectNode sampleInput(String name) throws IOException {
        JsonNode golden = golden(); for (JsonNode sample : golden.get("cases")) { if (sample.get("name").textValue().equals(name)) { return input(sample, golden); } }
        throw new IllegalStateException("mandatory original producer case missing: " + name);
    }
    /** Data-only fixture table expansion; no policy or qualification logic. */
    private static ObjectNode input(JsonNode sample, JsonNode golden) {
        ObjectNode input = (ObjectNode) golden.get("bases").get(sample.get("base_index").intValue()).get("input").deepCopy(); input.set("state", sample.get("state").deepCopy());
        for (JsonNode patch : sample.get("patches")) {
            String path = patch.get("path").textValue(); int split = path.lastIndexOf('/'); JsonNode parent = input.at(path.substring(0, split));
            String key = path.substring(split + 1); JsonNode value = patch.get("value").deepCopy();
            if (parent instanceof ObjectNode object) { object.set(key, value); } else if (parent instanceof ArrayNode array) { array.set(Integer.parseInt(key), value); }
            else { throw new IllegalStateException("invalid captured fixture delta"); }
        }
        return input;
    }
    private static ObjectMapper mapper() {
        return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = GuardianNegativeCadenceTest.class.getResourceAsStream("/guardiancadence/legacy-golden-v1.json")) {
            assertNotNull(stream, "committed original producer data is mandatory"); byte[] raw = stream.readNBytes(110_001);
            assertTrue(raw.length <= 110_000, "bounded fixture table"); return mapper().readTree(raw);
        }
    }
}
