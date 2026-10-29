package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.wave2.military.commander.CommanderQualityCodec;
import org.xar.ck3.control.wave2.military.commander.ArmyCommanderCandidatesCodec;
import static org.junit.jupiter.api.Assertions.*;

final class CombatCommanderProjectionPortsTest {
    private static final int LIMIT = 1_048_576;
    private static final String PREFIX = "military-";
    private static CombatCommanderProjectionPorts.Operations operations() {
        return new CombatCommanderProjectionPorts.Operations(op("combat-roles-normalize"), op("combat-roles-project"),
                op("commander-quality-propose"), op("commander-quality-admit-observed"),
                op("commander-quality-plan"), op("commander-quality-plan-next"));
    }
    private static ProjectionOperation op(String name) { return ProjectionOperation.fromWire(PREFIX + name); }
    private static ProjectionResult execute(String operation, JsonNode input) {
        return executeRaw(operation, input.toString().getBytes(StandardCharsets.UTF_8));
    }
    private static ProjectionResult executeRaw(String operation, byte[] raw) {
        ProjectionOperation identity = op(operation);
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(List.of(new MilitaryProjectionPortCatalog()));
        return dispatcher.dispatch(ProjectionWire.encodeCall(new ProjectionCall(
                new ProjectionCall.Identity("military-production-test", identity),
                ProjectionJson.object(raw, ProjectionJson.MAX_BYTES))));
    }
    private static JsonNode rawToken(String token) {
        JsonNode value=StrictJson.parse(token.getBytes(StandardCharsets.UTF_8));
        return value.isFloatingPointNumber()?new DecimalTokenNode(token):value;
    }
    private static JsonNode success(String operation, JsonNode input) {
        ProjectionResult.Succeeded reply = assertInstanceOf(ProjectionResult.Succeeded.class, execute(operation, input));
        return StrictJson.parse(reply.result().bytes(), LIMIT);
    }
    private static JsonNode commander() throws IOException {
        try (InputStream stream = CombatCommanderProjectionPortsTest.class.getResourceAsStream("/commander/legacy-golden.json")) {
            assertNotNull(stream, "actual original producer resource is mandatory");
            return ArmyCommanderCandidatesCodec.parseJson(stream.readAllBytes());
        }
    }
    private static JsonNode combat() throws IOException {
        try (InputStream stream = CombatCommanderProjectionPortsTest.class.getResourceAsStream("/combatroles/original-producer-golden.json.gz")) {
            assertNotNull(stream, "actual original C++ 14-scene resource is mandatory; no synthetic substitute or skip");
            try (GZIPInputStream zipped = new GZIPInputStream(stream)) {
                byte[] raw = zipped.readNBytes(LIMIT + 1); assertTrue(raw.length <= LIMIT);
                return StrictJson.parse(raw, LIMIT);
            }
        }
    }
    @Test void continuationUsesExactlyTheOriginalQueryOrderAndStopsAtTheOriginalDecision() throws IOException {
        int plans = 0;
        for (JsonNode sample : commander().get("plans")) {
            ObjectNode input = sample.get("input").deepCopy();
            ArrayNode original = (ArrayNode) input.get("queries"); input.putArray("queries");
            int consumed = 0;
            while (true) {
                JsonNode reply = success("commander-quality-plan-next", input);
                assertEquals("xar.java.commander-quality-plan-continuation.v1", reply.path("schema").textValue());
                if ("completed".equals(reply.path("status").textValue())) {
                    assertEquals(original.size(), consumed, sample.path("name").textValue());
                    assertEquals(sample.get("expected"), reply.get("planned"));
                    assertEquals(success("commander-quality-plan", sample.get("input")), reply.get("planned"));
                    break;
                }
                assertEquals("query", reply.path("status").textValue());
                assertTrue(consumed < original.size(), "continuation requested an observation the original consumer never read");
                JsonNode captured = original.get(consumed++);
                assertEquals(captured.get("army_id"), reply.get("army_id"));
                assertEquals(input.get("planned").get("revision"), reply.get("expected_revision"));
                ((ArrayNode) input.get("queries")).add(captured.deepCopy());
            }
            plans++;
        }
        assertEquals(13, plans);
    }
    @Test void originalProposalsAndTargetMetadataKeepCurrentQualitySeparateFromContextualInputs() throws IOException {
        int count = 0;
        for (JsonNode sample : commander().get("cases")) {
            assertEquals(sample.get("expected"), success("commander-quality-propose", sample.get("input"))); count++;
        }
        assertEquals(15, count);
        ObjectNode targeted = commander().get("cases").get(0).get("input").deepCopy();
        ((ObjectNode) targeted.get("candidates")).put("target_province_id", 1);
        byte[] targetRaw=targeted.toString().getBytes(StandardCharsets.UTF_8);
        assertEquals(commander().get("cases").get(0).get("expected"),
                ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.proposeTarget(targetRaw, 1)));
        assertEquals(commander().get("cases").get(0).get("expected"),
                success("commander-quality-propose",targeted));
        assertThrows(IllegalArgumentException.class,()->CommanderQualityCodec.proposeTarget(targetRaw, 2));
        for (String token : List.of("true", "1.0", "\"1\"", "0", "-1")) {
            ObjectNode invalid = targeted.deepCopy();
            ((ObjectNode) invalid.get("candidates")).set("target_province_id", rawToken(token));
            ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-propose", invalid));
            assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
            assertThrows(IllegalArgumentException.class,()->CommanderQualityCodec.proposeTarget(
                    invalid.toString().getBytes(StandardCharsets.UTF_8), 1));
        }
    }
    @Test void continuationRejectsUnusedWrongArmyAndWrongRevisionObservations() throws IOException {
        for (JsonNode sample : commander().get("plans")) {
            if (sample.get("input").get("queries").isEmpty()) continue;
            ObjectNode input = sample.get("input").deepCopy();
            ObjectNode observation = (ObjectNode) input.get("queries").get(0);
            observation.put("army_id", 2147483647);
            assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-plan-next", input));
            ObjectNode stale = sample.get("input").deepCopy();
            JsonNode proposal = stale.get("queries").get(0).get("proposal_input");
            if (proposal != null && proposal.isObject()) {
                ((ObjectNode) proposal.get("snapshot")).put("revision", 2147483647);
                assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-plan-next", stale));
            }
            ObjectNode unused = sample.get("input").deepCopy();
            ((ArrayNode) unused.get("queries")).add(sample.get("input").get("queries").get(0).deepCopy());
            assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-plan-next", unused));
            return;
        }
        fail("original producer plans must include an observed query");
    }
    @Test void allFourteenOriginalCombatInputsPassTheRegisteredCodecAndProjection() throws IOException {
        JsonNode golden = combat(); assertEquals(14, golden.get("cases").size());
        for (JsonNode sample : golden.get("cases")) {
            ObjectNode input = StrictJson.object(); input.set("value", sample.get("input"));
            assertEquals(sample.get("expected_normalized"), success("combat-roles-normalize", input).get("value"));
            input.set("source_provenance", golden.get("source_provenance"));
            assertEquals(sample.get("expected_projection"), success("combat-roles-project", input));
        }
        ObjectNode missing = StrictJson.object();
        assertInstanceOf(ProjectionResult.Rejected.class, execute("combat-roles-normalize", missing));
        missing.putNull("value");
        assertTrue(success("combat-roles-normalize", missing).get("value").isNull());
        missing.set("source_provenance", StrictJson.parse("{\"integer\":1208925819614629174706177,\"decimal\":1.5,\"null\":null}".getBytes(StandardCharsets.UTF_8)));
        JsonNode projected = success("combat-roles-project", missing);
        assertEquals(missing.get("source_provenance"), projected.get("source_provenance"));
        assertFalse(projected.get("ready").booleanValue()); assertEquals(0, projected.get("native_calls_executed").intValue());
        assertFalse(projected.get("future_phase_transition_ready").booleanValue());
    }
    private static String rawResult(String operation, String input) {
        var result = assertInstanceOf(ProjectionResult.Succeeded.class,
                executeRaw(operation, input.getBytes(StandardCharsets.UTF_8)));
        return new String(result.result().bytes(), StandardCharsets.UTF_8);
    }
    @Test void opaqueTokenTypesSurvive() throws IOException {
        String opaque = "{\"one\":1.0,\"exp\":1e0,\"zero\":-0.0,\"integer\":1208925819614629174706177,\"null\":null,\"empty\":[]}";
        assertTrue(rawResult("combat-roles-project", "{\"value\":null,\"source_provenance\":" + opaque + "}")
                .contains("\"source_provenance\":" + opaque));
        ObjectNode input = commander().get("plans").get(1).get("input").deepCopy();
        ((ObjectNode) input.get("planned").get("plan")).put("opaque_keep", "__RAW__");
        String raw = input.toString().replace("\"__RAW__\"", opaque);
        for (String output : List.of(new String(CommanderQualityCodec.plan(raw.getBytes(StandardCharsets.UTF_8)), StandardCharsets.UTF_8),
                rawResult("commander-quality-plan", raw), rawResult("commander-quality-plan-next", raw))) {
            String exact = "\"opaque_keep\":" + opaque;
            assertTrue(output.contains("deferred_commander_baseline_plan"));
            assertTrue(output.indexOf(exact) >= 0 && output.lastIndexOf(exact) > output.indexOf(exact));
        }
        ObjectNode owned = commander().get("cases").get(0).get("input").deepCopy();
        for (String token : List.of("1.0", "1e0", "true")) {
            ((ObjectNode) owned.get("candidates")).set("army_id", rawToken(token));
            assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-propose", owned));
        }
    }

    @Test void rawIntegerDomainAndSourceIdentityRemainEnforcedThroughRegisteredPort() throws IOException {
        ObjectNode original = commander().get("cases").get(0).get("input").deepCopy();
        for (String token : List.of("true", "83886367.0", "\"83886367\"", "null")) {
            ObjectNode bad = original.deepCopy();
            ((ObjectNode) bad.get("candidates")).set("army_id", rawToken(token));
            assertTrue(bad.toString().contains("\"army_id\":" + token),token);
            assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-propose", bad));
        }
        ObjectNode wrongSource = original.deepCopy();
        ((ObjectNode) wrongSource.get("candidates").get("current_commander").get("current_native_ai_base_quality"))
                .put("source_character_id", 30001);
        assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-propose", wrongSource));
        assertEquals(6, CombatCommanderProjectionPorts.registrations(operations()).size());
    }

    @Test void host04OnlyExplicitExpectedValidationCarriesDomainStatus() throws IOException {
        ObjectNode invalid = commander().get("cases").get(0).get("input").deepCopy();
        ((ObjectNode) invalid.get("candidates")).put("eligibility_mode", true);
        var rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-propose", invalid));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
        invalid = commander().get("cases").get(0).get("input").deepCopy();
        ((ObjectNode) invalid.get("candidates").get("current_commander")).put("status", "unexpected");
        rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute("commander-quality-propose", invalid));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
        for (boolean explicit : List.of(false, true)) {
            ProjectionOperation operation = op("commander-quality-plan");
            RegisteredProjection port = RegisteredProjection.of(new ProjectionPort<ProjectionJson, ProjectionJson>() {
                public ProjectionOperation operation() { return operation; }
                public int inputMaximumBytes() { return 131_072; }
                public int outputMaximumBytes() { return 131_072; }
                public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 131_072); }
                public ProjectionJson project(ProjectionJson value) {
                    if (explicit) { throw new ProjectionDomainRejection("expected input guard"); }
                    throw new IllegalArgumentException("unexpected internal failure");
                }
                public byte[] encode(ProjectionJson value) { return value.bytes(); }
            });
            var result = assertInstanceOf(ProjectionResult.Rejected.class, port.execute(new ProjectionCall(
                    new ProjectionCall.Identity("host04-marker-test", operation),
                    ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 131_072))));
            assertEquals(explicit ? ProjectionError.Code.DOMAIN_REJECTED : ProjectionError.Code.PROJECTION_FAILED,
                    result.error().code());
        }
    }
    @Test void actualCatalogDeclaresCommanderTransportBudgetsWithoutChangingNativeFullFrames() {
        var profiles = ProjectionDispatcher.fromCatalogs(List.of(new MilitaryProjectionPortCatalog())).profiles();
        assertEquals(44, profiles.size());
        var commander = profiles.stream().filter(profile -> List.of(op("commander-quality-propose"),
                op("commander-quality-admit-observed"), op("commander-quality-plan"),
                op("commander-quality-plan-next")).contains(profile.operation())).toList();
        assertEquals(4, commander.size());
        for (var profile : commander) {
            assertEquals(ProjectionJson.MAX_BYTES, profile.inputMaximumBytes());
            assertEquals(ProjectionJson.MAX_BYTES, profile.outputMaximumBytes());
        }
        assertEquals(8 * 1024 * 1024, ProjectionJson.MAX_BYTES);
        assertEquals(1_048_576, StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals(64 * 1024 * 1024, CommanderQualityCodec.MAX_BYTES);
    }

    @Test void actualCatalogScoresEveryCandidateBeyondTheReceiptParserBudget() throws IOException {
        ObjectNode input = commander().get("cases").get(0).get("input").deepCopy();
        ObjectNode candidates = (ObjectNode) input.get("candidates");
        ObjectNode template = candidates.get("candidates").get(0).deepCopy();
        ArrayNode rows = candidates.putArray("candidates");
        for (int index = 0; index <= 5_000; index++) {
            ObjectNode row = template.deepCopy();
            row.put("character_id", 100_000 + index);
            row.put("native_ai_base_quality", index == 5_000 ? 99 : 25);
            rows.add(row);
        }
        candidates.put("candidate_source_count", rows.size());
        byte[] raw = ArmyCommanderCandidatesCodec.encodeJson(input);
        assertTrue(raw.length > StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(raw.length < ProjectionJson.MAX_BYTES);
        var direct = CommanderQualityCodec.decodeProposalInput(ArmyCommanderCandidatesCodec.parseJson(raw));
        assertEquals(5_001, direct.context().candidates().size());
        JsonNode result = success("commander-quality-propose", input);
        assertEquals(ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.propose(raw)), result);
        assertEquals(105_000, result.get("proposed_commander_character_id").intValue());
        assertEquals(99, result.get("best_eligible_candidate_native_ai_base_quality").intValue());
        assertEquals(62, result.get("quality_gain").intValue());
        assertFalse(result.get("assignment_executed").booleanValue());
    }

    @Test void oversizedProjectionRemainsRejectedWhileTheNativeCodecRetainsItsFullFrameBudget() throws IOException {
        JsonNode sample = commander().get("cases").get(0);
        ObjectNode input = sample.get("input").deepCopy();
        ((ObjectNode) input.get("snapshot")).put("opaque_sdk_extension", "x".repeat(ProjectionJson.MAX_BYTES));
        byte[] raw = ArmyCommanderCandidatesCodec.encodeJson(input);
        assertTrue(raw.length > ProjectionJson.MAX_BYTES);
        assertTrue(raw.length < CommanderQualityCodec.MAX_BYTES);
        assertEquals(sample.get("expected"),
                ArmyCommanderCandidatesCodec.parseJson(CommanderQualityCodec.propose(raw)));
        assertThrows(IllegalArgumentException.class, () -> executeRaw("commander-quality-propose", raw));
        byte[] envelope = ("{\"schema\":\"" + ProjectionCall.SCHEMA
                + "\",\"schema_version\":1,\"request_id\":\"commander-over-budget\","
                + "\"operation\":\"military-commander-quality-propose\",\"payload\":"
                + new String(raw, StandardCharsets.UTF_8) + "}").getBytes(StandardCharsets.UTF_8);
        var dispatcher = ProjectionDispatcher.fromCatalogs(List.of(new MilitaryProjectionPortCatalog()));
        var rejected = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher.dispatch(envelope));
        assertEquals(ProjectionError.Code.INVALID_ENVELOPE, rejected.error().code());
    }

    @Test void actualCatalogAdmitsTheOriginalObservedQueryThroughTheCommanderEncoder() throws IOException {
        JsonNode sample = commander().get("cases").get(0);
        JsonNode input = sample.get("input");
        ObjectNode packet = StrictJson.object();
        packet.put("schema", "xar.java.commander-quality-observed-query.v1");
        packet.put("army_id", input.get("candidates").get("army_id").intValue());
        packet.set("snapshot_before", input.get("snapshot").deepCopy());
        packet.set("snapshot_after", input.get("snapshot").deepCopy());
        packet.putArray("bridge_capabilities").add(
                org.xar.ck3.control.wave2.military.commander.CommanderQuality.QUERY_CAPABILITY);
        packet.set("expected_revision", input.get("snapshot").get("revision"));
        ObjectNode nativeResult = packet.putObject("native_result");
        nativeResult.put("step", "query-army-commander-candidates-v1-for-army-83886367");
        nativeResult.put("accepted", true); nativeResult.put("status", "completed");
        nativeResult.put("read_only", true); nativeResult.set("query_sequence", input.get("query_sequence"));
        nativeResult.set("snapshot_revision", input.get("snapshot").get("native_revision"));
        nativeResult.set("date_raw", input.get("snapshot").get("date_raw"));
        nativeResult.set("army_commander_candidates", input.get("candidates").deepCopy());
        assertEquals(sample.get("expected"), success("commander-quality-admit-observed", packet));
        ((ObjectNode) nativeResult.get("army_commander_candidates")).put("target_province_id", 1);
        assertInstanceOf(ProjectionResult.Rejected.class,execute("commander-quality-admit-observed",packet));
    }

}

