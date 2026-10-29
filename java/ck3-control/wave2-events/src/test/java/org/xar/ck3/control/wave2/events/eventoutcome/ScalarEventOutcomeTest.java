package org.xar.ck3.control.wave2.events.eventoutcome;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection;
import org.xar.ck3.control.wave2.events.eventoutcome.EventOutcomeConsumerPort.EpisodeSource;
import org.xar.ck3.control.wave2.events.eventoutcome.EventOutcomeConsumerPort.Evaluated;
import org.xar.ck3.control.wave2.events.eventoutcome.EventOutcomeConsumerPort.Rejected;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Evaluation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Expectation;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.PlanInput;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.ResultStatus;
import org.xar.ck3.control.wave2.events.eventoutcome.ScalarEventOutcome.Selection;

final class ScalarEventOutcomeTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ScalarEventOutcomeTest.class.getResourceAsStream("/eventoutcome/scalar-event-outcome-golden-v1.json.gz")) {
            assertNotNull(stream, "committed actual producer capture is required; do not skip");
            try (GZIPInputStream uncompressed = new GZIPInputStream(stream)) { return JSON.readTree(uncompressed); }
        }
    }
    private static PlanInput planInput(JsonNode row) throws IOException {
        return ScalarOutcomeCodec.decodePlanInput(JSON.writeValueAsBytes(row.get("plan_input")));
    }
    private static Selection selection(JsonNode row) throws IOException {
        return ScalarOutcomeCodec.decodeSelection(JSON.writeValueAsBytes(row.get("event_selection")));
    }
    private static ObjectNode baseline() throws IOException { return golden().get("cases").get(0).get("plan_input").deepCopy(); }

    @Test void matchesActualOldPlanEvaluateAndRunnerConsumerForEveryCapturedCase() throws IOException {
        JsonNode corpus = golden();
        assertEquals("xar.ck3.scalar-event-outcome-golden/v1", corpus.get("schema").textValue());
        assertEquals(43, corpus.get("cases").size());
        assertTrue(corpus.get("producer_refs").size() >= 4);
        for (JsonNode row : corpus.get("cases")) {
            String name = row.get("name").textValue();
            Optional<Expectation> planned = ScalarEventOutcome.plan(planInput(row));
            assertEquals(row.get("expected_plan"), JSON.readTree(ScalarOutcomeCodec.encode(planned)), name);
            Evaluation result = planned.isPresent() ? ScalarEventOutcome.evaluate(planned.orElseThrow(), selection(row)) : null;
            assertEquals(row.get("expected_evaluation"), result == null ? JSON.getNodeFactory().nullNode()
                : JSON.readTree(ScalarOutcomeCodec.encode(result)), name);
            String issue = ScalarEventOutcome.runnerIssue(planned.orElse(null), result).map(value -> switch (value) {
                case FAILED -> "failed"; case UNAVAILABLE -> "unavailable"; case NO_MATERIAL_CHANGE -> "no_material_change";
            }).orElse(null);
            assertEquals(row.get("expected_runner_issue"), JSON.valueToTree(issue), name);
        }
    }

    @Test void typedProjectionAndExpectationSerializeWithoutChangingMeaning() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            PlanInput input = planInput(row);
            assertEquals(input, ScalarOutcomeCodec.decodePlanInput(ScalarOutcomeCodec.encodePlanInput(input)));
            Selection observed = selection(row);
            assertEquals(observed, ScalarOutcomeCodec.decodeSelection(ScalarOutcomeCodec.encodeSelection(observed)));
            Optional<Expectation> expectation = ScalarEventOutcome.plan(input);
            if (expectation.isPresent()) assertEquals(expectation.orElseThrow(), ScalarOutcomeCodec.decodeExpectation(ScalarOutcomeCodec.encode(expectation)));
        }
    }

    @Test void rawFloatBooleanAndStringTokensDoNotBecomeIntegerIdentities() throws IOException {
        String raw = new String(JSON.writeValueAsBytes(baseline()), StandardCharsets.UTF_8);
        assertTrue(raw.contains("\"revision\":33"));
        for (String wrong : List.of("1.0", "true", "\"33\"")) {
            byte[] bytes = raw.replace("\"revision\":33", "\"revision\":" + wrong).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput(bytes));
        }
        String nativeFloat = raw.replace("\"selected_native_option_index\":1", "\"selected_native_option_index\":1.0");
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput(nativeFloat.getBytes(StandardCharsets.UTF_8)));
        String scaleFloat = raw.replace("\"schema_version\":1", "\"schema_version\":1.0");
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput(scaleFloat.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodeSelection("{\"starting_revision\":true}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodeSelection("{\"postcondition_verified\":1}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void exactWrapperAndDeclaredExtensibleProducerContainersHaveDifferentBoundaries() throws IOException {
        ObjectNode unknown = baseline(); unknown.put("unsafe_override", true);
        byte[] unknownBytes = JSON.writeValueAsBytes(unknown);
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput(unknownBytes));
        ObjectNode missing = baseline(); missing.remove("played_character_gold");
        byte[] missingBytes = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput(missingBytes));
        ObjectNode extension = baseline();
        ((ObjectNode) extension.get("decision")).put("existing_registry_source_annotation", "preserved outside scalar projection");
        assertEquals(ScalarEventOutcome.plan(ScalarOutcomeCodec.decodePlanInput(JSON.writeValueAsBytes(baseline()))),
            ScalarEventOutcome.plan(ScalarOutcomeCodec.decodePlanInput(JSON.writeValueAsBytes(extension))));
        String json = new String(JSON.writeValueAsBytes(baseline()), StandardCharsets.UTF_8);
        String duplicate = json.replace("\"revision\":33", "\"revision\":33,\"revision\":33");
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodePlanInput((json + " {}").getBytes(StandardCharsets.UTF_8)));
        ObjectNode expected = (ObjectNode) JSON.readTree(ScalarOutcomeCodec.encode(ScalarEventOutcome.plan(planInput(golden().get("cases").get(0)))));
        expected.remove("unavailable_reason");
        byte[] missingReason = JSON.writeValueAsBytes(expected);
        assertThrows(IllegalArgumentException.class, () -> ScalarOutcomeCodec.decodeExpectation(missingReason));
    }

    @Test void exactSigned64ValuesCanProduceA65BitDeltaLikePython() throws IOException {
        boolean found = false;
        for (JsonNode row : golden().get("cases")) {
            JsonNode expected = row.get("expected_evaluation");
            if (!expected.isNull() && expected.get("delta") != null && expected.get("delta").isIntegralNumber()
                    && expected.get("delta").bigIntegerValue().equals(new BigInteger("18446744073709551615"))) {
                Evaluation result = ScalarEventOutcome.evaluate(ScalarEventOutcome.plan(planInput(row)).orElseThrow(), selection(row));
                assertEquals(new BigInteger("18446744073709551615"), result.delta());
                assertEquals(ResultStatus.VERIFIED_CHANGE, result.status());
                found = true;
            }
        }
        assertTrue(found, "the original producer's long-boundary case must execute");
    }

    @Test void acceptedAckRetainsUnavailableIndependentMaterialEvidence() throws IOException {
        JsonNode ack = null;
        for (JsonNode row : golden().get("cases")) if (row.get("name").textValue().contains(":ack_only:")) ack = row;
        assertNotNull(ack);
        Expectation expected = ScalarEventOutcome.plan(planInput(ack)).orElseThrow();
        Evaluation result = ScalarEventOutcome.evaluate(expected, selection(ack));
        assertEquals(ResultStatus.UNAVAILABLE, result.status());
        assertEquals(null, result.delta());
        assertEquals(Optional.of(ScalarEventOutcome.RunnerIssue.UNAVAILABLE), ScalarEventOutcome.runnerIssue(expected, result));
    }

    @Test void consumerPortReusesRealOptionProjectionAndBindsEpisodeSourceAndRenderedIdentity() throws IOException {
        JsonNode corpus = golden();
        JsonNode first = corpus.get("cases").get(0);
        PlanInput input = planInput(first);
        JsonNode knowledge = corpus.get("knowledge_refs").get(0);
        JsonNode hashes = knowledge.get("source_sha256");
        String path = null;
        var names = hashes.fieldNames();
        while (names.hasNext()) { String next = names.next(); if (next.startsWith("events/")) { path = next; break; } }
        assertNotNull(path);
        String hash = hashes.get(path).textValue();
        VanillaOptionProjection.RegistryBinding binding = new VanillaOptionProjection.RegistryBinding(input.decision().eventDefinitionKey(),
            input.decision().ck3Build(), knowledge.get("ck3_exe_sha256").textValue(), VanillaOptionProjection.RegistryState.AVAILABLE,
            List.of(new VanillaOptionProjection.SourceAnchor(path, hash, hash)));
        VanillaOptionProjection.Result projection = VanillaOptionProjection.project(new VanillaOptionProjection.Request(binding,
            new VanillaOptionProjection.OptionContract(2, List.of(0, 1), 1, 2, List.of(), List.of(2)),
            List.of(new VanillaOptionProjection.RenderedOption(0, 0, true, true, false, false),
                new VanillaOptionProjection.RenderedOption(1, 1, true, true, false, false)), 2));
        EpisodeSource episode = new EpisodeSource(corpus.get("machine_id").textValue(), "fixture-episode", "fixture-generation", 91, hash);
        Evaluated attached = assertInstanceOf(Evaluated.class, EventOutcomeConsumerPort.attach(episode, episode, projection, input, true, selection(first)));
        assertEquals(episode, attached.episodeSource());
        assertEquals(projection, attached.optionProjection());
        assertEquals(ResultStatus.VERIFIED_CHANGE, attached.materialResult().status());
        assertFalse(attached.actionAuthorized()); assertFalse(attached.replayAuthorized()); assertFalse(attached.saveCreditGranted());
        EpisodeSource wrongEpisode = new EpisodeSource(episode.machineId(), "different-episode", episode.gameGeneration(), 91, hash);
        assertInstanceOf(Rejected.class, EventOutcomeConsumerPort.attach(episode, wrongEpisode, projection, input, true, selection(first)));
        EpisodeSource wrongSource = new EpisodeSource(episode.machineId(), episode.episodeId(), episode.gameGeneration(), 91, "A".repeat(64));
        assertInstanceOf(Rejected.class, EventOutcomeConsumerPort.attach(wrongSource, wrongSource, projection, input, true, selection(first)));
        assertThrows(IllegalArgumentException.class, () -> new EpisodeSource(episode.machineId(), episode.episodeId(), episode.gameGeneration(), 0, hash));
    }
}
