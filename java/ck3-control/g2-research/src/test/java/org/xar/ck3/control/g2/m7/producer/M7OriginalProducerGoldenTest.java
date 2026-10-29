package org.xar.ck3.control.g2.m7.producer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.CheckpointContinuity;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7CreationTimeBoundaryVerification;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.M7Research;

/** Default CI executes every captured goal/refusal and government vector through M7Research. */
final class M7OriginalProducerGoldenTest {
    @TempDir Path temporary;


    @Test void publicGoalNewPreservesSignedActorThroughWireAndEvaluate() {
        G2Source source = signedGoalSource();
        org.junit.jupiter.api.Assertions.assertAll("public goal_new signed int32 actors",
                () -> assertPublicGoalNew(source, Integer.MIN_VALUE),
                () -> assertPublicGoalNew(source, -2L),
                () -> assertPublicGoalNew(source, 0L),
                () -> assertPublicGoalNew(source, Integer.MAX_VALUE));
    }

    @Test void publicGoalNewRejectsOriginalWrongTokensAndAbsentOrUnsignedActors() {
        G2Source source = signedGoalSource();
        for (String token : new String[] {"-1", "-2147483649", "2147483648", "2147483649",
                "4294967295", "true", "1.0", "\"0\"", "null"}) {
            byte[] input = ("{\"campaign_id\":\"synthetic-signed-campaign\",\"character_id\":" + token + "}")
                    .getBytes(StandardCharsets.UTF_8);
            G2Request original = request(source, "synthetic-goal-new-invalid", "goal_new", input);
            G2Request fresh = G2Wire.decodeRequest(G2Wire.encodeRequest(original));
            assertArrayEquals(original.payload().bytes(), fresh.payload().bytes(),
                    "wrong token must reach evaluate without numeric reencoding: " + token);
            assertThrows(IllegalArgumentException.class, () -> new M7Research().evaluate(fresh), token);
        }
    }

    private static G2Source signedGoalSource() {
        return new G2Source("synthetic-m7-signed-machine", "2026-10-29T00:00:00Z", "synthetic-m7-goal-new",
                new ExactRef("D:/synthetic/m7-goal-new-input.json", 1L, "a".repeat(64)));
    }

    private static void assertPublicGoalNew(G2Source source, long actor) {
        byte[] input = ("{\"campaign_id\":\"synthetic-signed-campaign\",\"character_id\":" + actor + "}")
                .getBytes(StandardCharsets.UTF_8);
        G2Request original = request(source, "synthetic-goal-new-signed-" + actor, "goal_new", input);
        G2Request fresh = G2Wire.decodeRequest(G2Wire.encodeRequest(original));
        assertArrayEquals(original.payload().bytes(), fresh.payload().bytes());
        G2Response response = new M7Research().evaluate(fresh);
        G2Response retained = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(source, retained.source()); assertEquals(original.requestId(), retained.requestId());
        var goal = GoalCodec.decodeGoal(retained.result().bytes());
        assertEquals("synthetic-signed-campaign", goal.campaignId());
        assertEquals(actor, goal.originCharacterId()); assertEquals(actor, goal.currentCharacterId());
        assertEquals(0L, goal.progress().reconciledSuccessions());
        assertTrue(goal.progress().lastSuccession().isEmpty());
        assertArrayEquals(retained.result().bytes(), GoalCodec.encodeGoal(goal));
    }

    @Test void actualOriginalProducerCorpusUsesTheRealDomainAndTypedPersistence() throws Exception {
        byte[] raw = golden();
        Path input = temporary.resolve("original-producer-golden-v1.json");
        Files.write(input, raw, StandardOpenOption.CREATE_NEW);
        Path actual = temporary.resolve("actual.json");
        M7GoalProducerVerification.main(new String[] {temporary.toString(), input.toString(), actual.toString()});
        var result = StrictJson.parse(Files.readAllBytes(actual));
        assertEquals("PASS", result.path("status").textValue());
        assertEquals(6, result.path("original_goal_vectors").intValue());
        assertEquals(4, result.path("original_complete_reconciliation_refusals").intValue());
        assertEquals(9, result.path("original_raw_token_refusals").intValue());
        assertEquals(4, result.path("fresh_government_domain_vectors").intValue());
        assertEquals(88, result.path("checks").intValue());
        assertEquals(0, result.path("true_driver_or_save_body_reads").intValue());
        exportVerification("M7.goal.actual.json", Files.readAllBytes(actual));
    }

    @Test void completeGovernmentCorpusAndStrictRawTokenRefusalsRunInDefaultCi() throws Exception {
        Path oldInput = temporary.resolve("government-original.json");
        try (var input = M7OriginalProducerGoldenTest.class.getResourceAsStream("/government/original-producer-golden.json")) {
            assertNotNull(input, "complete original government producer corpus is required; missing is RED");
            Files.write(oldInput, input.readAllBytes(), StandardOpenOption.CREATE_NEW);
        }
        Path freshInput = temporary.resolve("m7-original.json");
        Files.write(freshInput, golden(), StandardOpenOption.CREATE_NEW);
        Path actual = temporary.resolve("government-actual.json");
        M7GovernmentProducerVerification.main(new String[] {oldInput.toString(), freshInput.toString(), actual.toString()});
        var result = StrictJson.parse(Files.readAllBytes(actual));
        assertEquals("PASS", result.path("status").textValue());
        assertEquals(15, result.path("original_government_vectors").intValue());
        assertEquals(5, result.path("original_raw_token_rejections").intValue());
        assertEquals(4, result.path("fresh_government_vectors").intValue());
        assertEquals(215, result.path("checks").intValue());
        assertEquals(0, result.path("true_driver_or_save_body_reads").intValue());
        exportVerification("M7.government.actual.json", Files.readAllBytes(actual));
    }

    @Test void actualProducerExportsHttpVectorsAfterWireDomainAndFreshConsumerRoundtrips() throws Exception {
        byte[] resource = golden();
        String configuredOracle = System.getenv("XAR_M7_HTTP_ORACLE_PATH");
        Path oracle;
        if (configuredOracle == null) {
            oracle = temporary.resolve("original-producer-golden-v1.json");
            Files.write(oracle, resource, StandardOpenOption.CREATE_NEW);
        } else {
            assertFalse(configuredOracle.isBlank(), "configured actual oracle path must be explicit");
            oracle = Path.of(configuredOracle).toRealPath();
            assertEquals("original-producer-golden-v1.json", oracle.getFileName().toString(),
                    "only the retained test oracle may be read, never a Driver or SAVE body");
            assertEquals(resource.length, Files.size(oracle), "actual retained oracle size matches the mandatory resource");
        }
        byte[] original = Files.readAllBytes(oracle);
        assertArrayEquals(resource, original, "actual retained producer capture must equal the adopted original bytes");
        JsonNode captured = StrictJson.parse(original, StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(captured.path("source_refs_unchanged").booleanValue());
        assertTrue(captured.path("original_inputs_unchanged").booleanValue());
        assertEquals(6, captured.path("goal_cases").size());
        JsonNode success = named(captured.path("goal_cases"), "goal_continue_original_complete_reconciliation");
        JsonNode refused = named(captured.path("goal_rejections"), "unknown_transition");
        assertEquals(18, success.path("input").path("reconciliation").size());
        assertEquals(captured.get("complete_reconciliation"), success.path("input").get("reconciliation"));
        assertEquals(18, refused.path("input").path("reconciliation").size());
        assertEquals("unknown", refused.path("input").path("reconciliation").path("verdict").textValue());

        String configuredExport = System.getenv("XAR_M7_HTTP_EXPORT_DIR");
        Path output = configuredExport == null ? temporary.resolve("http-export") : Path.of(configuredExport);
        if (configuredExport != null) { assertFalse(configuredExport.isBlank(), "configured export path must be explicit"); }
        Files.createDirectories(output);
        output = output.toRealPath();
        String fixtureVersion = captured.path("government_cases").get(0).path("input")
                .path("government_observation").path("build").path("version").textValue();
        assertNotNull(fixtureVersion, "retained producer has an explicit original fixture build");
        G2Source source = new G2Source(captured.path("machine_id").textValue(),
                Instant.parse(captured.path("observed_at_utc").textValue()).toString(), fixtureVersion + "-retained-fixture",
                new ExactRef(oracle.toRealPath().toString(), original.length, sha256(original)));
        ArrayNode outputs = StrictJson.object().putArray("outputs");

        G2Request continueRequest = request(source, "m7-http2-original-continue", "goal_continue", rawInput(success));
        ExactRef requestRef = retain(output, "M7.request.json", G2Wire.encodeRequest(continueRequest)); outputs.add(requestRef.toJson());
        G2Request freshRequest = G2Wire.decodeRequest(Files.readAllBytes(Path.of(requestRef.path())));
        assertArrayEquals(continueRequest.payload().bytes(), freshRequest.payload().bytes());
        G2Response continued = new M7Research().evaluate(freshRequest);
        assertEquals(success.get("expected"), StrictJson.parse(continued.result().bytes()));
        ExactRef expectedRef = retain(output, "M7.expected-result.json", continued.result().bytes()); outputs.add(expectedRef.toJson());
        ExactRef responseRef = retain(output, "M7.expected-response.json", G2Wire.encodeResponse(continued)); outputs.add(responseRef.toJson());
        G2Response freshResponse = G2Wire.decodeResponse(Files.readAllBytes(Path.of(responseRef.path())));
        assertEquals(continueRequest.requestId(), freshResponse.requestId()); assertEquals(source, freshResponse.source());
        assertArrayEquals(continued.result().bytes(), freshResponse.result().bytes());
        var freshGoal = GoalCodec.decodeGoal(freshResponse.result().bytes());
        assertArrayEquals(freshResponse.result().bytes(), GoalCodec.encodeGoal(freshGoal));
        assertEquals(100L, freshGoal.originCharacterId()); assertEquals(200L, freshGoal.currentCharacterId());
        assertEquals(1L, freshGoal.progress().reconciledSuccessions());

        G2Request planRequest = request(source, "m7-http2-original-plan", "goal_plan", GoalCodec.encodeGoal(freshGoal));
        outputs.add(retain(output, "M7.plan.request.json", G2Wire.encodeRequest(planRequest)).toJson());
        G2Response planned = new M7Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(planRequest)));
        assertEquals(named(captured.path("goal_cases"), "goal_successor_plan").get("expected"), StrictJson.parse(planned.result().bytes()));
        ExactRef planRef = retain(output, "M7.plan.response.json", G2Wire.encodeResponse(planned)); outputs.add(planRef.toJson());
        var freshPlan = GoalCodec.decodePlan(G2Wire.decodeResponse(Files.readAllBytes(Path.of(planRef.path()))).result().bytes());

        JsonNode binding = success.path("input").path("reconciliation").path("successor_binding");
        var observation = new CheckpointContinuity.Observation(source.machineId(), sha256(original),
                new CheckpointContinuity.GameIdentity(101L, "20261023081234.123456+480", "C:/synthetic/ck3.exe"),
                binding.path("snapshot_id").textValue(), binding.path("revision").bigIntegerValue().longValueExact(),
                binding.path("native_revision").bigIntegerValue().longValueExact(), "synthetic:m7-http2:successor",
                freshGoal.currentCharacterId(), binding.path("date_raw").bigIntegerValue().longValueExact(), freshGoal, null, null);
        ObjectNode consumerInput = StrictJson.object(); consumerInput.put("schema", M7OrdinaryPlanConsumer.INPUT_SCHEMA);
        consumerInput.put("publication", "successor_plan");
        consumerInput.set("observation", StrictJson.parse(CheckpointContinuity.encodeObservation(observation)));
        consumerInput.put("selected_step", "life-advance"); consumerInput.putNull("government_context");
        G2Request consumerRequest = request(source, "m7-http2-original-consumer", "ordinary_plan_consume", raw(consumerInput));
        outputs.add(retain(output, "M7.consumer.request.json", G2Wire.encodeRequest(consumerRequest)).toJson());
        G2Response consumed = new M7Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(consumerRequest)));
        ExactRef consumerRef = retain(output, "M7.consumer.response.json", G2Wire.encodeResponse(consumed)); outputs.add(consumerRef.toJson());
        var freshConsumer = M7OrdinaryPlanConsumer.decode(G2Wire.decodeResponse(
                Files.readAllBytes(Path.of(consumerRef.path()))).result().bytes());
        assertEquals(freshGoal, freshConsumer.observation().goal());
        assertEquals(freshPlan, freshConsumer.campaignGoalPlanUsed());
        assertEquals(observation, freshConsumer.observation());
        assertFalse(freshConsumer.gameActionsSubmitted()); assertFalse(freshConsumer.coldAuthorityGranted());
        assertFalse(freshConsumer.replayAuthorized());

        byte[] originalGoal = raw(refused.path("input").get("goal"));
        G2Request rejectRequest = request(source, "m7-http2-original-unknown", "goal_continue", rawInput(refused));
        ExactRef rejectRef = retain(output, "M7.reject.request.json", G2Wire.encodeRequest(rejectRequest)); outputs.add(rejectRef.toJson());
        G2Request freshReject = G2Wire.decodeRequest(Files.readAllBytes(Path.of(rejectRef.path())));
        IllegalArgumentException rejected = assertThrows(IllegalArgumentException.class, () -> new M7Research().evaluate(freshReject));
        assertArrayEquals(originalGoal, raw(refused.path("input").get("goal")), "UNKNOWN never updates the retained original intent");
        ObjectNode rejection = StrictJson.object(); rejection.put("schema", "xar.m7-http2-local-rejection/v1");
        rejection.put("operation", "goal_continue"); rejection.put("verdict", "unknown");
        rejection.put("actual_domain_rejected", true); rejection.put("exception_class", rejected.getClass().getName());
        rejection.put("message", rejected.getMessage()); rejection.put("http_executed", false);
        rejection.put("unknown_action_replayed", false);
        outputs.add(retain(output, "M7.reject.expected-error.json", StrictJson.canonical(rejection)).toJson());
        assertArrayEquals(original, Files.readAllBytes(oracle), "retained actual oracle remains unchanged");

        var calendar = M7CreationTimeBoundaryVerification.verify();
        assertEquals(10, calendar.negativeCases()); assertEquals(4, calendar.positiveCases());
        assertEquals(1, calendar.equalityCases());
        ObjectNode calendarActual = StrictJson.object();
        calendarActual.put("schema", "xar.g2.m7.creation-time-boundary-test/v1");
        calendarActual.put("machine_id", source.machineId()); calendarActual.put("observed_at_utc", Instant.now().toString());
        calendarActual.put("synthetic", true); calendarActual.put("negative_cases", calendar.negativeCases());
        calendarActual.put("positive_cases", calendar.positiveCases()); calendarActual.put("equality_cases", calendar.equalityCases());
        calendarActual.put("game_calls", 0); calendarActual.put("cold_authority_granted", false);
        outputs.add(retain(output, "M7.calendar.actual.json", StrictJson.canonical(calendarActual)).toJson());

        ObjectNode metadata = StrictJson.object(); metadata.put("schema", "xar.m7-http2-producer-fixture-export/v1");
        metadata.put("machine_id", source.machineId()); metadata.put("observed_at_utc", Instant.now().toString());
        metadata.put("status", "PRODUCER_WIRE_DOMAIN_CONSUMER_PASS_HTTP_NOTRUN");
        metadata.set("source", StrictJson.parse(G2Wire.sourceBytes(source)));
        metadata.put("resource_sha256", sha256(resource)); metadata.put("resource_bytes", resource.length);
        metadata.put("original_producer_case", success.path("name").textValue());
        metadata.put("original_rejection_case", refused.path("name").textValue());
        metadata.put("complete_reconciliation_fields", 18);
        metadata.set("original_producer_source_refs", captured.get("source_refs").deepCopy());
        metadata.set("retained_native_fixture_build", captured.path("government_cases").get(0).path("input")
                .path("government_observation").get("build").deepCopy());
        metadata.putArray("operations").add("goal_continue").add("goal_plan").add("ordinary_plan_consume");
        metadata.set("outputs", outputs); metadata.put("game_calls", 0); metadata.put("actual_driver_or_save_body_reads", 0);
        metadata.put("http_executed", false); metadata.put("new_native_cold_or_business_qualification", false);
        metadata.put("scope", "Exact retained original producer corpus through wire/domain/fresh readers. Observation Game/process/episode fields are explicit software fixtures; exporter machine is bound by the qualified command terminal. No live or recovery authority.");
        retain(output, "M7.metadata.json", StrictJson.canonical(metadata, StrictJson.EXPLICIT_MAX_BYTES));
    }

    private static JsonNode named(JsonNode rows, String name) {
        JsonNode selected = null;
        for (JsonNode row : rows) if (name.equals(row.path("name").textValue())) {
            assertTrue(selected == null, "unique original producer case " + name); selected = row;
        }
        assertNotNull(selected, "required original producer case " + name);
        return selected;
    }
    private static byte[] rawInput(JsonNode row) {
        assertTrue(row.path("raw_input_json").isTextual(), "exact original raw JSON input is required");
        return row.path("raw_input_json").textValue().getBytes(StandardCharsets.UTF_8);
    }
    private static G2Request request(G2Source source, String requestId, String operation, byte[] input) {
        byte[] payload = ("{\"operation\":\"" + operation + "\",\"input\":"
                + new String(input, StandardCharsets.UTF_8) + "}").getBytes(StandardCharsets.UTF_8);
        return new G2Request(requestId, Milestone.M7, source, ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
    }
    private static ExactRef retain(Path output, String filename, byte[] bytes) throws Exception {
        Path file = output.resolve(filename); Files.write(file, bytes, StandardOpenOption.CREATE_NEW);
        return new ExactRef(file.toRealPath().toString(), bytes.length, sha256(bytes));
    }
    private void exportVerification(String filename, byte[] bytes) throws Exception {
        String configured = System.getenv("XAR_M7_HTTP_EXPORT_DIR");
        if (configured == null) { return; }
        assertFalse(configured.isBlank(), "configured export path must be explicit");
        Path output = Path.of(configured); Files.createDirectories(output);
        retain(output.toRealPath(), filename, bytes);
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }

    private static byte[] golden() throws IOException {
        try (var input = M7OriginalProducerGoldenTest.class.getResourceAsStream("/m7/original-producer-golden-v1.json")) {
            assertNotNull(input, "actual original M7 producer capture is required; missing is RED, never skipped");
            return input.readAllBytes();
        }
    }
}
