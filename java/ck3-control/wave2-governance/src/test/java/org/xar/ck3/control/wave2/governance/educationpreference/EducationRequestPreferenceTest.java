package org.xar.ck3.control.wave2.governance.educationpreference;

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
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsComposer;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.*;

class EducationRequestPreferenceTest {
    @Test void unchangedProducerGoldensIncludingRetainedActualQueriesMatchAndRoundTrip() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java.education-request-preference-legacy-golden.v1", golden.get("schema").textValue());
        assertTrue(golden.get("projection_not_original").booleanValue());
        assertTrue(golden.get("cases").size() >= 12);
        int actualSamples = 0;
        for (JsonNode sample : golden.get("cases")) {
            Input input = EducationPreferenceCodec.decode(StrictJson.canonical(sample.get("input")));
            Result actual = EducationRequestPreference.order(input);
            assertEquals(sample.get("expected"), StrictJson.parse(EducationPreferenceCodec.encodeResult(actual)),
                    sample.get("name").textValue());
            assertEquals(input, EducationPreferenceCodec.decode(EducationPreferenceCodec.encodeInput(input)), sample.get("name").textValue());
            if (sample.get("name").textValue().startsWith("retained-P43-")) {
                String name = sample.get("name").textValue();
                actualSamples++;
                assertEquals(1, input.observations().size(), name);
                RequestObservation request = assertInstanceOf(RequestObservation.class, input.observations().getFirst(), name);
                assertEquals(16_852_037L, request.intent().childFullId(), name);
                assertEquals(31_254L, request.intent().guardianFullId(), name);
                GuardianProfile profile = request.profile().orElseThrow();
                assertEquals(Long.valueOf(request.intent().childFullId()), profile.childCharacterId(), name);
                assertEquals(Long.valueOf(request.intent().guardianFullId()), profile.characterId(), name);
                assertEquals(request.queryNativeRevision(), profile.owningNativeRevision(), name);
                assertEquals(1, actual.candidates().size(), "retained P43 must produce an actual candidate: " + name);
                CandidateRecord candidate = actual.candidates().getFirst();
                assertTrue(candidate.requestProfileIdentityBound(), name);
                assertEquals(request.intent().childFullId(), candidate.pair().childFullId(), name);
                assertEquals(request.intent().guardianFullId(), candidate.pair().guardianFullId(), name);
                assertEquals(profile, candidate.rawProfile().orElseThrow(), name);
                assertEquals(0, candidate.observationIndex(), name);
                assertEquals(List.of(0), actual.orderedObservationIndices(), name);
            }
        }
        assertEquals(3, actualSamples, "three original completed P43 query projections are mandatory");
    }

    @Test void unequalAvailabilityAndSourcesRetainSlotsInsteadOfGlobalRanking() throws IOException {
        assertEquals(List.of(2, 1, 0, 3), result("availability-slots-retained").orderedObservationIndices());
        assertEquals(List.of(2, 3, 0, 1), result("operand-source-slots-retained").orderedObservationIndices());
        assertEquals(List.of(2, 1, 0), result("full-id-and-occurrence-ties").orderedObservationIndices());
    }

    @Test void martialUsesOnlyNativeTotalAndNeverFallsBackToObservedRawPrefix() throws IOException {
        Result result = result("martial-no-raw-fallback");
        for (CandidateRecord candidate : result.candidates()) {
            assertTrue(candidate.requestProfileIdentityBound()); assertFalse(candidate.focus().available());
            assertEquals(SourceBasis.TOTAL_MARTIAL, candidate.focus().sourceBasis());
            assertEquals(Integer.valueOf(999), candidate.rawProfile().orElseThrow().skills().get(Skill.MARTIAL).value());
            assertEquals(BigInteger.valueOf(candidate.learning().rawValue()), candidate.knownWeightedScore().orElseThrow().numerator());
            assertTrue(candidate.completeWeightedScore().isEmpty());
        }
        assertEquals("request_guardian_total_martial_callback_not_observed", result.candidates().get(0).focus().unavailableReason());
        assertEquals("native_total_unavailable", result.candidates().get(1).focus().unavailableReason());
    }

    @Test void signedDwordExtremaRemainSignedAndWeightedWithoutOverflow() throws IOException {
        Result result = result("exact-signed-dword-extrema");
        assertEquals(new BigInteger("-6442450944"), result.candidates().get(0).completeWeightedScore().orElseThrow().numerator());
        assertEquals(new BigInteger("6442450941"), result.candidates().get(1).completeWeightedScore().orElseThrow().numerator());
        assertEquals(List.of(1, 0), result.orderedObservationIndices());
    }

    @Test void mismatchedIntentAndAbsentProfilePreserveUnknownNotZeroOrRemoval() throws IOException {
        Result result = result("unbound-and-absent-profile"); assertEquals(2, result.candidates().size());
        for (CandidateRecord candidate : result.candidates()) {
            assertFalse(candidate.requestProfileIdentityBound()); assertFalse(candidate.focus().available()); assertFalse(candidate.learning().available());
            assertTrue(candidate.knownWeightedScore().isEmpty()); assertTrue(candidate.completeWeightedScore().isEmpty());
            assertEquals("request_guardian_profile_identity_unavailable", candidate.focus().unavailableReason());
        }
        assertTrue(result.candidates().get(0).rawProfile().isPresent()); assertTrue(result.candidates().get(1).rawProfile().isEmpty());
    }

    @Test void separateFamilyAndGuardianFramesArePreservedAndQueryRevisionOwnsProfileBinding() throws IOException {
        Result result = result("complete-signed-ranking"); CandidateRecord first = result.candidates().getFirst();
        assertTrue(first.requestProfileIdentityBound());
        assertEquals(9, StrictJson.parse(first.focusSourceFrame().canonicalJson().getBytes(StandardCharsets.UTF_8)).get("native_revision").bigIntegerValue().intValueExact());
        assertEquals(11, StrictJson.parse(first.guardianQueryFrame().canonicalJson().getBytes(StandardCharsets.UTF_8)).get("snapshot_revision").bigIntegerValue().intValueExact());
        assertEquals(List.of(1, 0, 2), result.orderedObservationIndices());
    }

    @Test void actualWrongTokensAreRejectedWithoutNormalizerErasingDecimalToken() throws IOException {
        for (String bad : List.of("true", "1.0", "\"1\"", "null", "2147483648", "-2147483649")) {
            ObjectNode input = sampleInput("complete-signed-ranking");
            byte[] outgoing = rawToken(input, "/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1/skills/diplomacy", "value", bad);
            assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(outgoing), bad);
        }
        ObjectNode boolId = sampleInput("complete-signed-ranking");
        ((ObjectNode) boolId.at("/observations/0/default_request_intent")).put("guardian_full_id", true);
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(boolId.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode floatRevision = sampleInput("complete-signed-ranking");
        byte[] revisionWire = rawToken(floatRevision, "/observations/0/default_query/character_interaction_ordinary_context", "snapshot_revision", "11.0");
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(revisionWire));
    }

    @Test void closedFieldsMissingValuesEmptyOccurrencesAndWrongTotalTargetReject() throws IOException {
        ObjectNode missing = sampleInput("complete-signed-ranking");
        ((ObjectNode) missing.at("/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1/skills/learning")).remove("value");
        reject(missing);
        ObjectNode unknown = sampleInput("complete-signed-ranking"); unknown.put("default_to_zero", true); reject(unknown);
        ObjectNode profileUnknown = sampleInput("complete-signed-ranking");
        ((ObjectNode) profileUnknown.at("/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1")).put("ready", true); reject(profileUnknown);
        ObjectNode empty = sampleInput("complete-signed-ranking"); ((ArrayNode) empty.at("/observations/0/needs/occurrence_indices")).removeAll(); reject(empty);
        ObjectNode total = sampleInput("complete-signed-ranking");
        ((ObjectNode) total.at("/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1/total_martial_callback_v1")).put("target_character_id", 99); reject(total);
    }

    @Test void duplicateTrailingUtf8AndEnvelopeBudgetRejectAndNoIntentStillSkips() throws IOException {
        String valid = sampleInput("complete-signed-ranking").toString();
        String duplicate = valid.replaceFirst("\\{", "{\"schema\":\"duplicate\",");
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(new byte[65_537]));
        Result skipped = result("skipped-no-intents"); assertTrue(skipped.candidates().isEmpty()); assertTrue(skipped.orderedObservationIndices().isEmpty());
    }

    @Test void actualNeedsProjectionPortFeedsSameTypedPreferenceWithoutDictionaryBridge() throws IOException {
        ObjectNode input = sampleInput("complete-signed-ranking"); Input typed = EducationPreferenceCodec.decode(StrictJson.canonical(input));
        RequestObservation original = assertInstanceOf(RequestObservation.class, typed.observations().getFirst());
        ObjectNode needs = (ObjectNode) input.at("/observations/0/needs");
        needs.put("character_id", original.intent().childFullId()); needs.put("raw_character_id", original.intent().childFullId());
        var projected = EducationNeedsComposer.needsRowProjection(StrictJson.canonical(needs));
        RequestObservation adapted = EducationNeedsPreferenceAdapter.fromNeedsRow(projected, original.intent().guardianFullId(),
                original.guardianQueryFrame().canonicalJson().getBytes(StandardCharsets.UTF_8), original.queryNativeRevision(), original.profile());
        assertEquals(original, adapted);
        assertEquals(EducationRequestPreference.order(new Input(List.of(original))), EducationRequestPreference.order(new Input(List.of(adapted))));
    }

    @Test void nativeUint64RevisionsRoundTripExactlyAndOverflowRejects() throws IOException {
        ObjectNode input = sampleInput("complete-signed-ranking"); BigInteger maximum = StrictJson.UINT64_MAX;
        ((ObjectNode) input.at("/observations/0/default_query/character_interaction_ordinary_context")).put("snapshot_revision", maximum);
        ((ObjectNode) input.at("/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1")).put("owning_native_revision", maximum);
        ((ObjectNode) input.at("/observations/0/candidate/frame")).put("snapshot_revision", maximum);
        Input decoded = EducationPreferenceCodec.decode(StrictJson.canonical(input));
        assertEquals(maximum, assertInstanceOf(RequestObservation.class, decoded.observations().getFirst()).queryNativeRevision());
        assertTrue(EducationRequestPreference.order(decoded).candidates().getFirst().requestProfileIdentityBound());
        assertEquals(decoded, EducationPreferenceCodec.decode(EducationPreferenceCodec.encodeInput(decoded)));
        ((ObjectNode) input.at("/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1")).put("owning_native_revision", maximum.add(BigInteger.ONE));
        reject(input);
    }

    @Test void unavailableReasonLengthRetainsPythonUnicodeCodePointDomain() throws IOException {
        ObjectNode input = sampleInput("complete-signed-ranking");
        ObjectNode learning = (ObjectNode) input.at("/observations/0/default_query/character_interaction_ordinary_context/request_guardian_skill_inputs_v1/skills/learning");
        String accepted = "\uD83D\uDE80".repeat(512);
        learning.put("available", false); learning.putNull("value"); learning.put("unavailable_reason", accepted);
        Input decoded = EducationPreferenceCodec.decode(StrictJson.canonical(input));
        assertEquals(accepted, EducationRequestPreference.order(decoded).candidates().getFirst().learning().unavailableReason());
        learning.put("unavailable_reason", accepted + "\uD83D\uDE80"); reject(input);
    }

    @Test void ownerParsedProjectionAvoidsMapBudgetAndArbitraryRosterLimit() throws IOException {
        ObjectNode many = StrictJson.object(); many.put("schema", EducationPreferenceCodec.INPUT_SCHEMA); ArrayNode observations = many.putArray("observations");
        for (int index = 0; index < 300; index++) { observations.addObject().putNull("default_request_intent"); }
        Input roster = EducationPreferenceCodec.decode(StrictJson.canonical(many)); assertEquals(300, roster.observations().size());
        assertTrue(EducationRequestPreference.order(roster).candidates().isEmpty());
        ObjectNode large = sampleInput("complete-signed-ranking"); Input expected = EducationPreferenceCodec.decode(StrictJson.canonical(large));
        ((ObjectNode) large.at("/observations/0/default_query/character_interaction_ordinary_context")).put("unused_sdk_extension", "x".repeat(70_000));
        byte[] whole = large.toString().getBytes(StandardCharsets.UTF_8); assertTrue(whole.length > 65_536);
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(whole), "standalone Map-sized boundary stays bounded");
        assertEquals(expected, EducationPreferenceCodec.projectParsedInput(large), "same-JVM owner projects consumed fields without serializing full SDK data");
    }

    private static void reject(ObjectNode input) {
        assertThrows(IllegalArgumentException.class, () -> EducationPreferenceCodec.decode(input.toString().getBytes(StandardCharsets.UTF_8)));
    }
    private static byte[] rawToken(ObjectNode input, String pointer, String field, String token) {
        BigInteger sentinel = new BigInteger("987654321098765432109876543210"); ObjectNode parent = (ObjectNode) input.at(pointer); parent.put(field, sentinel);
        String encoded = input.toString(), needle = sentinel.toString();
        assertTrue(encoded.contains(needle)); assertEquals(encoded.indexOf(needle), encoded.lastIndexOf(needle));
        String expectedParent = parent.toString().replace(needle, token), outgoing = encoded.replace(needle, token);
        assertTrue(outgoing.contains(expectedParent), "actual outgoing raw token retained: " + token); assertFalse(outgoing.contains(needle));
        return outgoing.getBytes(StandardCharsets.UTF_8);
    }
    private static Result result(String name) throws IOException {
        return EducationRequestPreference.order(EducationPreferenceCodec.decode(StrictJson.canonical(sampleInput(name))));
    }
    private static ObjectNode sampleInput(String name) throws IOException {
        for (JsonNode sample : golden().get("cases")) { if (sample.get("name").textValue().equals(name)) { return (ObjectNode) sample.get("input").deepCopy(); } }
        throw new IllegalStateException("mandatory producer sample missing: " + name);
    }
    private static ObjectMapper mapper() {
        return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = EducationRequestPreferenceTest.class.getResourceAsStream("/educationpreference/legacy-golden-v1.json")) {
            assertNotNull(stream, "committed legacy producer golden is mandatory"); byte[] raw = stream.readNBytes(110_001);
            assertTrue(raw.length <= 110_000, "test data budget"); return mapper().readTree(raw);
        }
    }
}
