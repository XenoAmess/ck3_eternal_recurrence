package org.xar.ck3.control.planning;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import static org.junit.jupiter.api.Assertions.*;

final class PlanningCoreProjectionCatalogTest {
    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    private static final List<RegisteredProjection> PORTS = new PlanningCoreProjectionCatalog().registrations();

    @Test void standardProviderResourceAndEveryExistingRoleBudgetAreRequired() {
        assertTrue(ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .anyMatch(provider -> provider.type() == PlanningCoreProjectionCatalog.class));
        assertEquals(4, PORTS.size());
        for (RegisteredProjection port : PORTS) {
            boolean cadence = port.operation() == ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT;
            assertEquals(cadence ? 196_608 : 131_072, port.inputMaximumBytes());
            assertEquals(cadence ? 67_584 : 131_072, port.outputMaximumBytes());
        }
    }

    @Test void originalCadenceGoldenRunsThroughDecodeApplicationAndEncodedReply() throws Exception {
        JsonNode golden = resource("/optionalcadence/golden.json", false); int transitions = 0;
        for (JsonNode scenario : golden.get("cases")) {
            String episode = scenario.get("episode").textValue();
            JsonNode state = load(episode, null);
            for (JsonNode step : scenario.get("steps")) {
                String currentEpisode = step.has("episode") ? step.get("episode").textValue() : episode;
                state = load(currentEpisode, state.toString());
                String operation = step.get("operation").textValue();
                ObjectNode input = cadence(operation.equals("requalify") ? "requalify" : operation);
                input.put("state_json", state.toString());
                ObjectNode current = input.putObject("current"); current.put("episode_run_id", currentEpisode);
                current.set("date_raw", step.get("date_raw")); current.set("native_revision", step.get("native_revision"));
                switch (operation) {
                    case "record" -> { input.set("domain", step.get("domain")); input.set("actual_action", step.get("actual_action")); }
                    case "defer_council" -> input.set("evidence_path", step.get("evidence_path"));
                    case "requalify" -> input.set("native_catalogue", step.get("native_catalogue"));
                    case "deferred", "action_recorded" -> input.set("domain", step.get("domain"));
                    default -> fail("unexpected original producer operation");
                }
                JsonNode reply = success(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, input);
                if (!reply.get("state").isNull()) { state = reply.get("state"); }
                if (operation.equals("deferred")) { assertEquals(step.get("expected_deferred"), reply.get("value")); }
                if (operation.equals("action_recorded")) { assertEquals(step.get("expected_action_recorded"), reply.get("value")); }
                if (operation.equals("requalify")) { assertEquals(step.get("expected_changed"), reply.get("write_required")); }
                assertEquals(step.get("expected_state"), state, scenario.get("name").textValue()); transitions++;
            }
        }
        assertEquals(42, transitions);
        for (JsonNode sample : golden.get("snapshot_cases")) {
            ObjectNode input = cadence("frame"); input.put("snapshot_json", sample.get("snapshot").toString());
            assertEquals(sample.get("expected_frame"),
                    success(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, input).get("value"));
        }
    }

    @Test void originalOpportunityCorpusReachesTheRegisteredSelectorAndNormalizer() throws Exception {
        JsonNode golden = resource("/opportunity/producer-golden-v1.json.gz", true); int count = 0;
        for (JsonNode vector : golden.get("cases")) {
            JsonNode request = vector.get("input");
            JsonNode selected = success(ProjectionOperation.PLANNING_OPPORTUNITY_SELECT, request);
            assertEquals(vector.get("expected"), selected, vector.get("name").textValue());
            for (int index = 0; index < request.get("proposals").size(); index++) {
                ObjectNode normalized = JSON.createObjectNode(); normalized.set("frame", selected.get("frame"));
                normalized.set("proposal", request.get("proposals").get(index));
                ObjectNode expected = selected.get("evaluated").get(index).deepCopy(); expected.remove("reason");
                assertEquals(expected, success(ProjectionOperation.PLANNING_OPPORTUNITY_NORMALIZE, normalized));
            }
            count++;
        }
        assertTrue(count >= 24);
    }

    @Test void rawStateFloatingTokensNeverBecomeIntegersAndThePersistedStateCapStaysIndependent() throws Exception {
        JsonNode state = load("e", null);
        for (String token : List.of("true", "1.0", "\"1\"", "null")) {
            String changed = state.toString().replaceFirst("\"consecutive_no_action\":0", "\"consecutive_no_action\":" + token);
            ObjectNode input = cadence("load"); input.put("episode_run_id", "e"); input.put("state_json", changed);
            assertRejected(input);
        }
        ObjectNode oversized = cadence("load"); oversized.put("episode_run_id", "e");
        oversized.put("state_json", " ".repeat(65_536) + state);
        assertRejected(oversized);
    }

    @Test void cadenceMissingExtraWrongSchemaAndCurrentTokenTypesRejectAtTheActualPort() {
        ObjectNode valid = cadence("record"); valid.putNull("state_json"); valid.put("domain", "council"); valid.put("actual_action", false);
        ObjectNode current = valid.putObject("current"); current.put("episode_run_id", "e"); current.put("date_raw", 0); current.put("native_revision", 0);
        for (String field : List.of("schema", "action", "state_json", "domain", "actual_action", "current")) {
            ObjectNode broken = valid.deepCopy(); broken.remove(field); assertRejected(broken);
        }
        ObjectNode extra = valid.deepCopy(); extra.put("alias", "record"); assertRejected(extra);
        ObjectNode schema = valid.deepCopy(); schema.put("schema", "xar.planning.optional-cadence.request.v2"); assertRejected(schema);
        for (String token : List.of("true", "0.0", "\"0\"", "null", "-1")) {
            String broken = valid.toString().replace("\"date_raw\":0", "\"date_raw\":" + token);
            assertInstanceOf(ProjectionResult.Rejected.class, invoke(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, bytes(broken)));
        }
    }

    @Test void duplicateCadenceRecordDoesNotAskTheOriginalWriterToPublishAgain() throws Exception {
        ObjectNode input = cadence("record"); input.putNull("state_json"); input.put("domain", "council"); input.put("actual_action", false);
        ObjectNode frame = input.putObject("current"); frame.put("episode_run_id", "e"); frame.put("date_raw", 0); frame.put("native_revision", 0);
        JsonNode first = success(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, input);
        assertTrue(first.get("write_required").booleanValue()); input.put("state_json", first.get("state").toString());
        JsonNode duplicate = success(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, input);
        assertFalse(duplicate.get("write_required").booleanValue()); assertEquals(first.get("state"), duplicate.get("state"));
    }

    @Test void observedFrameKeepsExactWideIntegersAndOriginalFallbackWhileRejectingTypeAliases() throws Exception {
        String snapshot = "{\"played_character\":{\"character_id\":18446744073709551617},\"native_revision\":2,\"date_raw\":0,\"snapshot_id\":\"s\",\"revision\":2,\"episode_run_id\":\"e\"}";
        JsonNode result = successRaw(ProjectionOperation.PLANNING_OBSERVED_FRAME, bytes(snapshot));
        assertEquals("18446744073709551617", result.get("played_character_id").bigIntegerValue().toString());
        for (String token : List.of("true", "2.0", "\"2\"", "null")) {
            assertInstanceOf(ProjectionResult.Rejected.class, invoke(ProjectionOperation.PLANNING_OBSERVED_FRAME,
                    bytes(snapshot.replace("\"native_revision\":2", "\"native_revision\":" + token))));
        }
    }

    @Test void normalizationUsesTheSingleStreamingCodecWithoutChangingOpaqueFloatTokens() throws Exception {
        JsonNode vector = resource("/opportunity/producer-golden-v1.json.gz", true).get("cases").get(0);
        JsonNode selected = vector.get("expected"); ObjectNode input = JSON.createObjectNode(); input.set("frame", selected.get("frame"));
        ObjectNode proposal = vector.get("input").get("proposals").get(0).deepCopy();
        ObjectNode evidence = (ObjectNode) proposal.get("evidence"); evidence.put("raw_float", 1.0); evidence.put("negative_zero", -0.0);
        input.set("proposal", proposal); String raw = input.toString().replace("\"raw_float\":1.0", "\"raw_float\":1.2300e+4");
        ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class,
                invoke(ProjectionOperation.PLANNING_OPPORTUNITY_NORMALIZE, bytes(raw)));
        String encoded = new String(result.result().bytes(), StandardCharsets.UTF_8);
        assertTrue(encoded.contains("1.2300e+4")); assertTrue(encoded.contains("-0.0"));
    }

    @Test void onlyExplicitDomainRefusalsKeep422AndInternalArgumentFailuresRemainUnknown() throws Exception {
        ProjectionResult.Rejected frame = assertInstanceOf(ProjectionResult.Rejected.class,
                invoke(ProjectionOperation.PLANNING_OBSERVED_FRAME, bytes("{}")));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, frame.error().code());
        assertRejected(cadence("unknown-action"));
        ObjectNode record = cadence("record"); record.putNull("state_json"); record.put("domain", "council"); record.put("actual_action", false);
        ObjectNode current = record.putObject("current"); current.put("episode_run_id", "e");
        for (int index = 0; index < 3; index++) {
            current.put("date_raw", index); current.put("native_revision", index);
            record.put("state_json", success(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, record).get("state").toString());
        }
        current.put("date_raw", 3); current.put("native_revision", 3);
        ProjectionResult.Rejected cooldown = assertInstanceOf(ProjectionResult.Rejected.class,
                invoke(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, bytes(record.toString())));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, cooldown.error().code());
        ProjectionPort<byte[], byte[]> broken = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return ProjectionOperation.PLANNING_OBSERVED_FRAME; }
            @Override public byte[] decode(byte[] rawPayload) { return rawPayload; }
            @Override public byte[] project(byte[] input) { throw new IllegalArgumentException("internal implementation detail"); }
            @Override public byte[] encode(byte[] result) { return result; }
        };
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("planning-internal-failure", broken.operation()),
                ProjectionJson.object(bytes("{}"), ProjectionJson.MAX_BYTES));
        ProjectionResult.Rejected internal = assertInstanceOf(ProjectionResult.Rejected.class,
                RegisteredProjection.of(broken).execute(call));
        assertEquals(ProjectionError.Code.PROJECTION_FAILED, internal.error().code());
        assertFalse(internal.error().message().contains("internal implementation detail"));
    }

    private static ObjectNode cadence(String action) {
        ObjectNode result = JSON.createObjectNode(); result.put("schema", PlanningCoreProjectionCatalog.CADENCE_REQUEST); result.put("action", action); return result;
    }
    private static JsonNode load(String episode, String state) throws Exception {
        ObjectNode input = cadence("load"); input.put("episode_run_id", episode);
        if (state == null) { input.putNull("state_json"); } else { input.put("state_json", state); }
        return success(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, input).get("state");
    }
    private static ProjectionResult invoke(ProjectionOperation operation, byte[] payload) {
        RegisteredProjection port = PORTS.stream().filter(candidate -> candidate.operation() == operation).findFirst().orElseThrow();
        ProjectionCall original = new ProjectionCall(new ProjectionCall.Identity("planning-core-test", operation),
                ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
        ProjectionCall restored = ProjectionWire.decodeCall(ProjectionWire.encodeCall(original));
        assertArrayEquals(payload, restored.payload().bytes()); return port.execute(restored);
    }
    private static JsonNode success(ProjectionOperation operation, JsonNode input) throws Exception { return successRaw(operation, JSON.writeValueAsBytes(input)); }
    private static JsonNode successRaw(ProjectionOperation operation, byte[] input) throws Exception {
        ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class, invoke(operation, input));
        ProjectionResult.Succeeded restored = assertInstanceOf(ProjectionResult.Succeeded.class,
                ProjectionWire.decodeResult(ProjectionWire.encodeResult(result)));
        assertEquals(result.identity(), restored.identity()); assertArrayEquals(result.result().bytes(), restored.result().bytes());
        return JSON.readTree(restored.result().bytes());
    }
    private static void assertRejected(JsonNode input) {
        ProjectionResult.Rejected result = assertInstanceOf(ProjectionResult.Rejected.class,
                invoke(ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT, bytes(input.toString())));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, result.error().code());
    }
    private static JsonNode resource(String path, boolean compressed) throws IOException {
        try (InputStream source = PlanningCoreProjectionCatalogTest.class.getResourceAsStream(path)) {
            if (source == null) { throw new IOException("mandatory original producer corpus missing: " + path); }
            if (!compressed) { return JSON.readTree(source); }
            try (GZIPInputStream gzip = new GZIPInputStream(source)) { return JSON.readTree(gzip); }
        }
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
