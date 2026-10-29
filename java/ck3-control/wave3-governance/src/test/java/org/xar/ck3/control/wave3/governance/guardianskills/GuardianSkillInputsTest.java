package org.xar.ck3.control.wave3.governance.guardianskills;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsComposer;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.SourceBasis;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsModel.*;

class GuardianSkillInputsTest {
    @Test void actualTypedProfileBindingRefusalRetainsDomainMarker() throws IOException {
        boolean checked = false;
        for (JsonNode sample : golden().get("cases")) {
            Input input = GuardianSkillsCodec.decode(StrictJson.canonical(sample.get("input")));
            if (input.profile().isEmpty() || input.context().isEmpty()) { continue; }
            Context source = input.context().orElseThrow();
            Context changed = new Context("unqualified-build", source.interactionKey(), source.status(),
                    source.frame(), source.secondaryActorId(), source.secondaryRecipientId());
            assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                    () -> GuardianSkillInputs.validateContextBinding(input.profile().orElseThrow(), changed));
            assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class,
                    () -> GuardianSkillInputs.project(new Input(input.needs(), input.profile(), java.util.Optional.empty())));
            checked = true; break;
        }
        assertTrue(checked, "actual retained profile/context pair must be exercised");
    }


    @Test void unchangedOriginalProjectionMatchesRetainedAndSyntheticGoldenAndRoundTrips() throws IOException {
        JsonNode golden = golden(); assertEquals(13, golden.get("cases").size()); int retained = 0;
        for (JsonNode sample : golden.get("cases")) {
            Input input = GuardianSkillsCodec.decode(StrictJson.canonical(sample.get("input")));
            assertEquals(input, GuardianSkillsCodec.projectParsedInput(sample.get("input")));
            assertEquals(sample.get("expected"), StrictJson.parse(GuardianSkillsCodec.encodeProjection(GuardianSkillInputs.project(input))), sample.get("name").textValue());
            assertEquals(input, GuardianSkillsCodec.decode(GuardianSkillsCodec.encodeInput(input)), sample.get("name").textValue());
            if (sample.get("name").textValue().startsWith("retained-P43-")) { retained++; }
        }
        assertEquals(3, retained);
    }

    @Test void completeExistingValidatorDecisionsMatchOnActualProfileAndRoleFrameBuildFailures() throws IOException {
        JsonNode cases = golden().get("validation_cases"); assertEquals(8, cases.size());
        for (JsonNode sample : cases) {
            byte[] profile = StrictJson.canonical(sample.get("profile")), context = StrictJson.canonical(sample.get("context"));
            if (sample.get("accepted").booleanValue()) { assertDoesNotThrow(() -> GuardianSkillsCodec.validate(profile, context), sample.get("name").textValue()); }
            else { assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.validate(profile, context), sample.get("name").textValue()); }
        }
    }

    @Test void rawMartialObservationStaysDistinctFromTotalMartialPreferenceOperand() throws IOException {
        Projection result = project("martial-raw-distinct-from-total");
        assertTrue(result.focusSkill().available()); assertEquals(SourceBasis.RAW, result.focusSourceBasis());
        assertNotEquals(result.profile().orElseThrow().totalMartial().orElseThrow().observation().value(), result.focusSkill().value());
        assertEquals(Integer.valueOf(12345), result.profile().orElseThrow().totalMartial().orElseThrow().observation().value());
        assertEquals(result.profile().orElseThrow().skills().get(org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.Skill.MARTIAL), result.focusSkill());
    }

    @Test void focusJoinFailuresDoNotEraseIndependentlyObservedLearning() throws IOException {
        for (String name : java.util.List.of("focus-child-mismatch-learning-retained", "focus-frame-missing-learning-retained", "focus-frame-mismatch-learning-retained")) {
            Projection result = project(name); assertFalse(result.join().available(), name); assertFalse(result.focusSkill().available(), name);
            assertTrue(result.learningSkill().available(), name); assertEquals(SourceBasis.RAW, result.learningSourceBasis());
        }
        Projection same = project("learning-focus-reuses-observed-operand"); assertEquals(same.focusSkill(), same.learningSkill());
    }

    @Test void absentUnknownNoneducationAndKnownNullRemainDifferent() throws IOException {
        Projection none = project("profile-not-observed"); assertEquals(Join.PROFILE_NOT_OBSERVED, none.join()); assertTrue(none.profile().isEmpty());
        Projection unknown = project("focus-unknown-learning-retained"); assertTrue(unknown.join().available());
        assertEquals("education_focus_not_observed", unknown.focusSkill().unavailableReason()); assertTrue(unknown.learningSkill().available());
        Projection other = project("noneducation-focus-learning-retained"); assertEquals("current_focus_is_not_education", other.focusSkill().unavailableReason());
        Projection guardian = project("known-null-guardian-preserved"); assertTrue(guardian.profile().isPresent()); assertNull(guardian.profile().get().characterId());
        assertEquals("known_null", guardian.profile().get().bindingStatus().wire()); assertFalse(guardian.learningSkill().available());
    }

    @Test void rawBoolFloatAndStringNeverBecomeIdsRevisionsOrSkills() throws IOException {
        for (String bad : java.util.List.of("true", "1.0", "\"1\"")) {
            byte[] input = rawToken(sampleInput("martial-raw-distinct-from-total"), "/context/request_guardian_skill_inputs_v1/skills/martial", "value", bad);
            assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(input), bad);
            byte[] role = rawToken(sampleInput("martial-raw-distinct-from-total"), "/context/effective_roles", "secondary_actor_id", bad);
            assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(role), bad);
            byte[] revision = rawToken(sampleInput("martial-raw-distinct-from-total"), "/context", "snapshot_revision", bad);
            assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(revision), bad);
        }
    }

    @Test void actualTypedNeedsProducerPortFeedsSameFocusSubject() throws IOException {
        ObjectNode input = sampleInput("martial-raw-distinct-from-total"); Input typed = GuardianSkillsCodec.decode(StrictJson.canonical(input));
        ObjectNode needs = (ObjectNode) input.get("needs"); needs.put("character_id", (int) typed.needs().childFullId()); needs.putArray("occurrence_indices").add(0);
        var projection = EducationNeedsComposer.needsRowProjection(StrictJson.canonical(needs));
        assertEquals(typed.needs(), GuardianSkillsCodec.fromNeedsRow(projection));
    }

    @Test void closedWrapperMissingAndDuplicateFieldsTrailingUtf8AndBudgetReject() throws IOException {
        ObjectNode unknown = sampleInput("martial-raw-distinct-from-total"); unknown.put("source_green", true); reject(unknown);
        ObjectNode missing = sampleInput("martial-raw-distinct-from-total"); ((ObjectNode) missing.at("/context/request_guardian_skill_inputs_v1/skills/learning")).remove("value"); reject(missing);
        String text = sampleInput("martial-raw-distinct-from-total").toString();
        assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(text.replaceFirst("\\{", "{\"schema\":\"duplicate\",").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode((text + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(new byte[65_537]));
    }

    private static Projection project(String name) throws IOException { return GuardianSkillInputs.project(GuardianSkillsCodec.decode(StrictJson.canonical(sampleInput(name)))); }
    private static byte[] rawToken(ObjectNode input, String pointer, String field, String token) {
        var sentinel = new java.math.BigInteger("987654321098765432109876543210"); ObjectNode parent = (ObjectNode) input.at(pointer); parent.put(field, sentinel);
        String encoded = input.toString(), needle = sentinel.toString();
        assertTrue(encoded.contains(needle)); assertEquals(encoded.indexOf(needle), encoded.lastIndexOf(needle));
        String expectedParent = parent.toString().replace(needle, token), outgoing = encoded.replace(needle, token);
        assertTrue(outgoing.contains(expectedParent), "actual outgoing raw token retained: " + token); assertFalse(outgoing.contains(needle));
        return outgoing.getBytes(StandardCharsets.UTF_8);
    }
    private static void reject(ObjectNode input) { assertThrows(IllegalArgumentException.class, () -> GuardianSkillsCodec.decode(input.toString().getBytes(StandardCharsets.UTF_8))); }
    private static ObjectNode sampleInput(String name) throws IOException {
        for (JsonNode sample : golden().get("cases")) { if (sample.get("name").textValue().equals(name)) { return (ObjectNode) sample.get("input").deepCopy(); } }
        throw new IllegalStateException("mandatory original producer case missing: " + name);
    }
    private static ObjectMapper mapper() {
        return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = GuardianSkillInputsTest.class.getResourceAsStream("/guardianskills/legacy-golden-v1.json")) {
            assertNotNull(stream, "committed original producer golden is mandatory"); byte[] raw = stream.readNBytes(110_001);
            assertTrue(raw.length <= 110_000, "bounded committed data"); return mapper().readTree(raw);
        }
    }
}
