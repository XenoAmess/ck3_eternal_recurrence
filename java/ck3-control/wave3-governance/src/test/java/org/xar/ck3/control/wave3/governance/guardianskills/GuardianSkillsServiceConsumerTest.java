package org.xar.ck3.control.wave3.governance.guardianskills;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsProjectionPort;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationCandidateProjectionPort;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsComposer;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.NeedsRowProjection;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationNeedsPreferenceAdapter;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceCodec;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationRequestPreference;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceProjectionPort;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceProjectionPort;

/** Original Service output joins the actual Java needs producer to both consuming leaves. */
class GuardianSkillsServiceConsumerTest {
    // Exact retained capture is 11,469 compressed / 164,405 decoded bytes.
    private static final int COMPRESSED_FIXTURE_LIMIT = 12 * 1024;
    private static final int DECODED_FIXTURE_LIMIT = 256 * 1024;
    @Test void typedHostPortsConsumeTheSameActualServiceNeedsCandidatesAndSkillFrames() throws IOException {
        JsonNode golden = golden();
        assertEquals(3, golden.get("cases").size());
        for (JsonNode sample : golden.get("cases")) {
            String name = sample.get("source_ref").textValue();
            JsonNode needs = invoke(new EducationNeedsProjectionPort(), sample.get("needs_request"));
            assertEquals(1, needs.get("rows").size(), name);
            JsonNode row = needs.get("rows").get(0);
            ObjectNode candidateInput = mapper().createObjectNode();
            candidateInput.put("schema", EducationCandidateProjectionPort.SCHEMA);
            candidateInput.set("needs", row); candidateInput.set("context", sample.get("context"));
            JsonNode candidate = invoke(new EducationCandidateProjectionPort(), candidateInput);
            assertEquals(sample.get("expected_candidate"), candidate, name);
            assertTrue(candidate.get("available").booleanValue(), name);
            assertEquals(16_852_037L, candidate.get("child_full_id").longValue(), name);
            assertEquals(31_254L, candidate.get("guardian_full_id").longValue(), name);
            ObjectNode preferenceInput = mapper().createObjectNode(); preferenceInput.put("schema", EducationPreferenceCodec.INPUT_SCHEMA);
            ObjectNode observation = preferenceInput.putArray("observations").addObject();
            ObjectNode intent = observation.putObject("default_request_intent");
            intent.set("child_full_id", candidate.get("child_full_id")); intent.set("guardian_full_id", candidate.get("guardian_full_id"));
            observation.set("needs", row); observation.set("candidate", candidate);
            observation.putObject("default_query").set("character_interaction_ordinary_context", sample.get("context"));
            JsonNode preference = invoke(new EducationPreferenceProjectionPort(), preferenceInput);
            assertEquals(sample.get("expected_preference"), preference, name);
            assertEquals(1, preference.get("candidates").size(), name);
            assertTrue(preference.at("/candidates/0/request_profile_identity_bound").booleanValue(), name);
            assertEquals(0, preference.at("/ordered_observation_indices/0").intValue(), name);
            assertEquals(1, preference.get("ordered_observation_indices").size(), name);
            for (String phase : List.of("default", "selected")) {
                ObjectNode skillInput = mapper().createObjectNode(); skillInput.put("schema", GuardianSkillsCodec.INPUT_SCHEMA);
                skillInput.set("needs", row); skillInput.set("context", sample.get(phase.equals("default") ? "context" : "selected_context"));
                assertEquals(sample.get("expected_" + phase + "_skills"), invoke(new GuardianSkillsProjectionPort(), skillInput), name + " " + phase);
            }
        }
    }

    @Test void cadenceHostPortRetainsEveryOriginalStateAndQueryTransition() throws IOException {
        try (InputStream stream = getClass().getResourceAsStream("/guardiancadence/legacy-golden-v1.json")) {
            assertNotNull(stream, "existing original cadence capture remains mandatory");
            byte[] raw = stream.readNBytes(110_001); assertTrue(raw.length <= 110_000);
            JsonNode golden = mapper().readTree(raw); assertEquals(19, golden.get("cases").size());
            for (JsonNode sample : golden.get("cases")) {
                ObjectNode input = (ObjectNode) golden.get("bases").get(sample.get("base_index").intValue()).get("input").deepCopy();
                input.set("state", sample.get("state").deepCopy());
                for (JsonNode patch : sample.get("patches")) {
                    String path = patch.get("path").textValue(); int split = path.lastIndexOf('/');
                    JsonNode parent = input.at(path.substring(0, split)); String key = path.substring(split + 1);
                    if (parent instanceof ObjectNode object) { object.set(key, patch.get("value").deepCopy()); }
                    else if (parent instanceof ArrayNode array) { array.set(Integer.parseInt(key), patch.get("value").deepCopy()); }
                    else { fail("invalid original fixture patch path"); }
                }
                String name = sample.get("name").textValue();
                ObjectNode evaluate = input.deepCopy();
                evaluate.put("schema", GuardianCadenceProjectionPort.SCHEMA).put("mode", "evaluate");
                assertEquals(sample.get("expected"), invoke(new GuardianCadenceProjectionPort(), evaluate), name);
                ObjectNode scopeInput = cadenceCall("source_scope", input, List.of("frame", "needs", "heir_id"));
                JsonNode scope = invoke(new GuardianCadenceProjectionPort(), scopeInput);
                assertEquals(sample.get("expected").get("scope"), scope, name + " original source_scope");
                ObjectNode deferred = cadenceCall("deferred", input, List.of("frame", "state")); deferred.set("scope", scope);
                assertEquals(sample.get("expected").get("deferred_before"), invoke(new GuardianCadenceProjectionPort(), deferred), name + " original deferred");
                ObjectNode observe = cadenceCall("observe", input, List.of("frame", "state", "default_query", "attempts", "selected_step"));
                observe.set("scope", scope);
                JsonNode observed = invoke(new GuardianCadenceProjectionPort(), observe);
                assertEquals(sample.get("expected").get("state"), observed.get("state"), name + " original observe state");
                assertEquals(sample.get("expected").get("observation"), observed.get("observation"), name + " original observe result");
                assertThrows(IllegalArgumentException.class, () -> new GuardianCadenceProjectionPort().decode(mapper().writeValueAsBytes(input)), "old application schema cannot hide an unmigrated caller");
            }
        }
    }

    private static ObjectNode cadenceCall(String mode, ObjectNode source, List<String> fields) {
        ObjectNode result = mapper().createObjectNode();
        result.put("schema", GuardianCadenceProjectionPort.SCHEMA).put("mode", mode);
        for (String field : fields) { result.set(field, source.get(field).deepCopy()); }
        return result;
    }

    private static JsonNode invoke(ProjectionPort<?, ?> port, JsonNode payload) throws IOException {
        return invokeTyped(port, payload);
    }

    private static <I, O> JsonNode invokeTyped(ProjectionPort<I, O> port, JsonNode payload) throws IOException {
        I input = port.decode(mapper().writeValueAsBytes(payload));
        return mapper().readTree(port.encode(port.project(input)));
    }

    @Test void completeOriginalServiceP43NeedsCandidatesPreferenceAndBothSkillReadsMatch() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java.education-service-consumers-legacy-golden.v1", golden.get("schema").textValue());
        assertTrue(golden.get("projection_not_original").booleanValue());
        assertEquals(4, golden.at("/original_tests/tests_run").intValue());
        for (String field : List.of("failures", "errors", "skips")) {
            assertEquals(0, golden.get("original_tests").get(field).intValue(), field);
        }
        assertEquals(3, golden.get("cases").size());
        for (JsonNode sample : golden.get("cases")) {
            String name = sample.get("source_ref").textValue();
            byte[] needsBytes = EducationNeedsComposer.compose(StrictJson.canonical(sample.get("needs_request")));
            JsonNode needs = mapper().readTree(needsBytes);
            assertEquals(1, needs.get("rows").size(), name);
            JsonNode row = needs.get("rows").get(0);
            ObjectNode projection = mapper().createObjectNode();
            for (String field : List.of("character_id", "raw_character_id", "occurrence_indices", "frame", "focus_management")) {
                projection.set(field, row.get(field));
            }
            assertEquals(sample.get("expected_needs_row"), projection, name);
            NeedsRowProjection typedNeeds = EducationNeedsComposer.needsRowProjection(StrictJson.canonical(row));
            assertEquals(16_852_037L, typedNeeds.childFullId(), name);
            byte[] context = StrictJson.canonical(sample.get("context"));
            JsonNode candidate = StrictJson.parse(EducationNeedsComposer.requestCandidate(StrictJson.canonical(row), context));
            assertEquals(sample.get("expected_candidate"), candidate, name);
            var typedCandidate = EducationNeedsComposer.candidateProjection(StrictJson.canonical(row), context);
            assertTrue(typedCandidate.available(), name);
            assertEquals(Long.valueOf(31_254L), typedCandidate.guardianFullId(), name);
            EducationPreferenceModel.GuardianProfile profile = EducationPreferenceCodec.decodeGuardianProfile(
                    StrictJson.canonical(sample.at("/context/request_guardian_skill_inputs_v1")));
            var request = EducationNeedsPreferenceAdapter.fromNeedsRow(typedNeeds, typedCandidate.guardianFullId(),
                    StrictJson.canonical(candidate.get("frame")), sample.at("/context/snapshot_revision").bigIntegerValue(), Optional.of(profile));
            var ordered = EducationRequestPreference.order(new EducationPreferenceModel.Input(List.of(request)));
            assertEquals(sample.get("expected_preference"), StrictJson.parse(EducationPreferenceCodec.encodeResult(ordered)), name);
            assertEquals(List.of(0), ordered.orderedObservationIndices(), name);
            assertEquals(1, ordered.candidates().size(), name);
            assertTrue(ordered.candidates().getFirst().requestProfileIdentityBound(), name);
            assertEquals(typedNeeds.childFullId(), ordered.candidates().getFirst().pair().childFullId(), name);
            assertEquals(31_254L, ordered.candidates().getFirst().pair().guardianFullId(), name);
            assertSkillRead(sample.get("context"), row, typedNeeds, sample.get("expected_default_skills"), name);
            JsonNode selected = sample.get("selected_context");
            assertEquals(sample.get("expected_selected_candidate"), StrictJson.parse(EducationNeedsComposer.requestCandidate(
                    StrictJson.canonical(row), StrictJson.canonical(selected))), name);
            assertSkillRead(selected, row, typedNeeds, sample.get("expected_selected_skills"), name);
            assertFalse(selected.get("can_send").booleanValue(), name);
            assertFalse(selected.get("ready_to_initiate").booleanValue(), name);
            assertEquals("life-advance", sample.get("selected_step").textValue(), name);
            assertEquals(1, sample.get("negative_observed_dates").intValue(), name);
            JsonNode calls = sample.get("service_query_calls");
            assertEquals(2, calls.size(), name);
            assertEquals(16_852_037L, calls.get(0).get("recipient_id").longValue(), name);
            assertEquals(16_852_037L, calls.get(1).at("/arguments/child_full_id").longValue(), name);
            assertEquals(31_254L, calls.get(1).at("/arguments/guardian_full_id").longValue(), name);
        }
    }

    private static void assertSkillRead(JsonNode context, JsonNode row, NeedsRowProjection needs, JsonNode expected, String name) {
        ObjectNode wrapper = mapper().createObjectNode();
        wrapper.put("schema", GuardianSkillsCodec.INPUT_SCHEMA); wrapper.set("needs", row); wrapper.set("context", context);
        GuardianSkillsModel.Input input = GuardianSkillsCodec.decode(StrictJson.canonical(wrapper));
        assertEquals(GuardianSkillsCodec.fromNeedsRow(needs), input.needs(), name);
        assertEquals(Long.valueOf(needs.childFullId()), input.profile().orElseThrow().childCharacterId(), name);
        assertEquals(Long.valueOf(31_254L), input.profile().orElseThrow().characterId(), name);
        GuardianSkillsModel.Projection result = GuardianSkillInputs.project(input);
        assertTrue(result.join().available(), name);
        assertEquals(expected, StrictJson.parse(GuardianSkillsCodec.encodeProjection(result)), name);
        assertEquals(input.profile().orElseThrow().skills().get(EducationPreferenceModel.Skill.LEARNING), result.learningSkill(), name);
        assertEquals(EducationPreferenceModel.SourceBasis.RAW, result.learningSourceBasis(), name);
        assertEquals(input, GuardianSkillsCodec.decode(GuardianSkillsCodec.encodeInput(input)), name);
    }

    private static ObjectMapper mapper() {
        return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    }

    @Test void eachFixtureLayerReadsItsExactLimitAndRejectsTheNextByte() throws IOException {
        for (int limit : List.of(COMPRESSED_FIXTURE_LIMIT, DECODED_FIXTURE_LIMIT)) {
            assertEquals(limit, readBounded(new ByteArrayInputStream(new byte[limit]), limit, "fixture budget").length);
            assertThrows(IOException.class, () -> readBounded(new ByteArrayInputStream(new byte[limit + 1]), limit, "fixture budget"));
        }
    }

    private static byte[] readBounded(InputStream source, int limit, String label) throws IOException {
        byte[] bytes = source.readNBytes(limit + 1);
        if (bytes.length > limit) { throw new IOException(label + ": exceeded " + limit + " bytes"); }
        return bytes;
    }

    private static JsonNode golden() throws IOException {
        try (InputStream source = GuardianSkillsServiceConsumerTest.class.getResourceAsStream("/guardianskills/service-consumer-golden-v1.json.gz")) {
            assertNotNull(source, "committed actual original Service consumer capture is mandatory");
            byte[] compressed = readBounded(source, COMPRESSED_FIXTURE_LIMIT, "compressed fixture budget");
            try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                byte[] raw = readBounded(gzip, DECODED_FIXTURE_LIMIT, "aggregate fixture budget");
                return mapper().readTree(raw);
            }
        }
    }
}
