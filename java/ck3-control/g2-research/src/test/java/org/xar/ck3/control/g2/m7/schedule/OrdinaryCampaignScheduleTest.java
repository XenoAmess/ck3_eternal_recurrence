package org.xar.ck3.control.g2.m7.schedule;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.CheckpointContinuity;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule.Plan;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule.State;

/** Original producers -> single M7 provider -> ordinary consumer -> fresh durable-state reader. */
final class OrdinaryCampaignScheduleTest {
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    @TempDir Path temporary;

    @Test void exactOriginalGoalOutputsRemainTheOnlyGoalPolicyInTheSchedulingProvider() throws IOException {
        JsonNode captured = resource("/m7/original-producer-golden-v1.json");
        int originalCases = 0;
        for (JsonNode row : captured.path("goal_cases")) {
            var request = request(row.path("operation").textValue(),
                    row.path("raw_input_json").textValue().getBytes(StandardCharsets.UTF_8), MACHINE);
            byte[] actual = new M7SchedulingDomain().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request))).result().bytes();
            assertEquals(row.get("expected"), parse(actual), row.path("name").textValue()); originalCases++;
        }
        assertEquals(6, originalCases);
        int freshGovernment = 0;
        for (JsonNode row : captured.path("government_cases")) {
            assertEquals(row.get("expected"), parse(evaluate("government_context", row.get("input"))), row.path("name").textValue());
            freshGovernment++;
        }
        assertEquals(4, freshGovernment);
        int originalGovernment = 0;
        JsonNode government = resource("/government/original-producer-golden.json");
        for (JsonNode row : government.path("cases")) {
            ObjectNode input = (ObjectNode) government.path("base_request").deepCopy();
            for (JsonNode patch : row.path("request_patch")) {
                String pointer = patch.path("path").textValue(); int last = pointer.lastIndexOf('/');
                JsonNode parent = last == 0 ? input : input.at(pointer.substring(0, last));
                assertTrue(parent.isObject(), "original patch parent exists");
                String field = pointer.substring(last + 1).replace("~1", "/").replace("~0", "~");
                if ("remove".equals(patch.path("op").textValue())) { ((ObjectNode) parent).remove(field); }
                else {
                    assertEquals("set", patch.path("op").textValue());
                    ((ObjectNode) parent).set(field, patch.get("value").deepCopy());
                }
            }
            ObjectNode expected = (ObjectNode) row.path("expected").deepCopy();
            if (row.path("expected_observation_sha256").isNull()) { expected.putNull("government_runtime_adapter"); }
            else { expected.set("government_runtime_adapter", input.get("government_observation")); }
            assertEquals(expected, parse(evaluate("government_context", input)), row.path("name").textValue());
            originalGovernment++;
        }
        assertEquals(15, originalGovernment);
        int rejectedOriginal = 0;
        for (String collection : List.of("goal_rejections", "strict_token_rejections")) {
            for (JsonNode row : captured.path(collection)) {
                byte[] rawInput = row.path("raw_input_json").textValue().getBytes(StandardCharsets.UTF_8);
                var originalRequest = request(row.path("operation").textValue(), rawInput, MACHINE);
                assertThrows(IllegalArgumentException.class, () -> new M7SchedulingDomain().evaluate(originalRequest), row.path("name").textValue());
                rejectedOriginal++;
            }
        }
        for (JsonNode row : government.path("wire_rejections")) {
            var originalRequest = request("government_context", row.path("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8), MACHINE);
            assertThrows(IllegalArgumentException.class, () -> new M7SchedulingDomain().evaluate(originalRequest)); rejectedOriginal++;
        }
        assertEquals(18, rejectedOriginal);
        var initial = GoalCodec.parseGoal(named(captured.path("goal_cases"), "goal_new").get("expected"));
        State before = new State(initial, Optional.empty());
        ObjectNode continuation = StrictJson.object(); continuation.set("state", parse(OrdinaryCampaignScheduleCodec.encodeState(before)));
        continuation.set("reconciliation", captured.get("complete_reconciliation"));
        byte[] continued = evaluate("ordinary_schedule_continue", continuation);
        State after = OrdinaryCampaignScheduleCodec.decodeState(continued);
        assertEquals(named(captured.path("goal_cases"), "goal_continue_original_complete_reconciliation").get("expected"),
                parse(GoalCodec.encodeGoal(after.goal())));
        assertTrue(after.deadline().isEmpty());
        assertArrayEquals(continued, OrdinaryCampaignScheduleCodec.encodeState(OrdinaryCampaignScheduleCodec.decodeState(continued)));
        assertEquals(initial.originCharacterId(), after.goal().originCharacterId());
        assertEquals(200L, after.goal().currentCharacterId());
    }

    @Test void everyOriginalClockDeadlineCaseRunsThroughTheRealOrdinaryConsumerAndFreshPersistence() throws IOException {
        JsonNode captured = resource("/schedule/deadline-original-producer.json");
        assertEquals(MACHINE, captured.path("machine_id").textValue());
        int returned = 0; int refused = 0;
        for (JsonNode row : captured.path("cases")) {
            if (!"deadline".equals(row.path("operation").textValue())) { continue; }
            var configuration = configuration(captured.path("configurations").path(row.path("configuration_id").textValue()).get("configuration"));
            State state = new State(OrdinaryCampaignGoal.newGoal(configuration.founding().campaignId(), 100), Optional.of(configuration));
            long current = row.path("starting").path("date_raw").longValue();
            BigInteger requested = row.path("proposed_target_raw").bigIntegerValue();
            if ("rejected".equals(row.path("outcome").path("status").textValue())) {
                assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignSchedule.consume(state,
                        ordinary(state, current, "life-advance", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN), Optional.of(requested)),
                        row.path("name").textValue()); refused++;
            } else {
                Plan actual = OrdinaryCampaignSchedule.consume(state,
                        ordinary(state, current, "life-advance", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN), Optional.of(requested));
                assertEquals(row.path("outcome").get("value"), parse(CampaignDeadlineCodec.encodeCap(actual.clockDeadline().orElseThrow())),
                        row.path("name").textValue());
                byte[] persisted = OrdinaryCampaignScheduleCodec.encodePlan(actual);
                Plan fresh = OrdinaryCampaignScheduleCodec.decodePlan(persisted);
                assertEquals(actual, fresh); assertArrayEquals(persisted, OrdinaryCampaignScheduleCodec.encodePlan(fresh));
                assertEquals("life-advance", fresh.ordinaryPlan().selectedStep());
                assertFalse(fresh.gameActionsSubmitted()); assertFalse(fresh.replayAuthorized()); assertEquals(0, fresh.savedDayCredit());
                returned++;
            }
        }
        assertEquals(10, returned, "all original successful deadline vectors, including beyond-long target");
        assertEquals(5, refused, "all original deadline failure paths");
    }

    @Test void ordinarySuccessorAndCheckpointReadersRetainFullPlannerStepAndTheExactFoundingClock() throws IOException {
        State state = clockState();
        var reconciliation = new OrdinaryCampaignGoal.Reconciliation(OrdinaryCampaignGoal.Verdict.MATCHED, 100, 200,
                List.of(10L), List.of(20L), List.of());
        State successor = OrdinaryCampaignSchedule.continueAfterReconciliation(state, reconciliation);
        assertEquals(state.deadline(), successor.deadline());
        for (M7OrdinaryPlanConsumer.Publication publication : M7OrdinaryPlanConsumer.Publication.values()) {
            var consumer = ordinary(successor, 53144328, "declare-war-v1", publication);
            Plan actual = OrdinaryCampaignSchedule.consume(successor, consumer, Optional.empty());
            Plan fresh = OrdinaryCampaignScheduleCodec.decodePlan(OrdinaryCampaignScheduleCodec.encodePlan(actual));
            assertEquals("declare-war-v1", fresh.ordinaryPlan().selectedStep());
            assertEquals("marriage", fresh.ordinaryPlan().campaignGoalPlanUsed().focus());
            assertEquals(publication, fresh.ordinaryPlan().publication());
            assertEquals(OrdinaryCampaignSchedule.ClockStatus.NO_CLOCK_REQUEST, fresh.clockStatus());
            assertTrue(fresh.effectiveClockTargetRaw().isEmpty());
            assertFalse(fresh.coldAuthorityGranted()); assertFalse(fresh.ordinaryPlan().replayAuthorized());
        }
    }

    @Test void unknownSuccessionRefusesTransitionAndRetainsBothOriginalStateAndTheFoundingClock() throws IOException {
        JsonNode captured = resource("/m7/original-producer-golden-v1.json");
        State original = new State(GoalCodec.parseGoal(named(captured.path("goal_cases"), "goal_new").get("expected")), Optional.empty());
        byte[] untouched = OrdinaryCampaignScheduleCodec.encodeState(original);
        JsonNode unknown = named(captured.path("goal_rejections"), "unknown_transition");
        ObjectNode input = StrictJson.object(); input.set("state", parse(untouched));
        input.set("reconciliation", unknown.path("input").get("reconciliation"));
        assertThrows(IllegalArgumentException.class, () -> evaluate("ordinary_schedule_continue", input));
        assertArrayEquals(untouched, OrdinaryCampaignScheduleCodec.encodeState(original));
        assertArrayEquals(untouched, evaluate("ordinary_schedule_read", parse(untouched)));
    }

    @Test void distinctGoalLineageAndConfiguredClockSurviveTheActualProviderAndContinuation() throws IOException {
        State original = clockState();
        State independent = new State(OrdinaryCampaignGoal.newGoal("native-goal-lineage", 100), original.deadline());
        String clockId = independent.deadline().orElseThrow().founding().campaignId();
        assertFalse(independent.goal().campaignId().equals(clockId));

        byte[] created = evaluate("ordinary_schedule_new", parse(OrdinaryCampaignScheduleCodec.encodeState(independent)));
        byte[] read = evaluate("ordinary_schedule_read", parse(created));
        assertArrayEquals(created, read);
        State restored = OrdinaryCampaignScheduleCodec.decodeState(read);
        assertEquals("native-goal-lineage", restored.goal().campaignId());
        assertEquals(original.deadline(), restored.deadline());

        ObjectNode continuation = StrictJson.object(); continuation.set("state", parse(read));
        continuation.set("reconciliation", resource("/m7/original-producer-golden-v1.json").get("complete_reconciliation"));
        byte[] continued = evaluate("ordinary_schedule_continue", continuation);
        State successor = OrdinaryCampaignScheduleCodec.decodeState(continued);
        assertEquals("native-goal-lineage", successor.goal().campaignId());
        assertEquals(100L, successor.goal().originCharacterId());
        assertEquals(200L, successor.goal().currentCharacterId());
        assertEquals(original.deadline(), successor.deadline());

        ObjectNode input = planningInput(successor, 53144328, Optional.of(BigInteger.valueOf(53145168)));
        var wire = G2Wire.decodeRequest(G2Wire.encodeRequest(request("ordinary_schedule_plan", raw(input), MACHINE)));
        var response = new M7SchedulingDomain().evaluate(wire);
        var freshResponse = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        Plan planned = OrdinaryCampaignScheduleCodec.decodePlan(freshResponse.result().bytes());
        assertArrayEquals(continued, OrdinaryCampaignScheduleCodec.encodeState(planned.state()));
        assertEquals("native-goal-lineage", planned.ordinaryPlan().campaignGoalPlanUsed().campaignId());
        assertEquals(clockId, planned.clockDeadline().orElseThrow().campaignId());
        assertEquals(BigInteger.valueOf(53145048), planned.effectiveClockTargetRaw().orElseThrow());
        assertArrayEquals(freshResponse.result().bytes(), OrdinaryCampaignScheduleCodec.encodePlan(planned));
        assertFalse(planned.gameActionsSubmitted()); assertFalse(planned.coldAuthorityGranted());
        assertFalse(planned.replayAuthorized()); assertEquals(0, planned.savedDayCredit());
    }

    @Test void malformedStateAndAlteredCalendarAreRejectedAtTheSharedReader() throws IOException {
        ObjectNode state = (ObjectNode) parse(OrdinaryCampaignScheduleCodec.encodeState(clockState()));
        for (String field : List.of("schema", "goal", "deadline_configuration")) {
            ObjectNode missing = state.deepCopy(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodeState(raw(missing)));
        }
        for (String token : List.of("true", "100.0", "\"100\"", "null")) {
            ObjectNode malformed = state.deepCopy(); ((ObjectNode) malformed.get("goal")).set("current_character_id", parse(bytes(token)));
            assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodeState(raw(malformed)));
        }
        ObjectNode unknown = state.deepCopy(); unknown.put("nonwar_only", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodeState(raw(unknown)));
        ObjectNode drift = state.deepCopy(); var boundaries = (com.fasterxml.jackson.databind.node.ArrayNode) drift.path("deadline_configuration").get("boundary_raws");
        boundaries.set(1, parse(bytes("53145072")));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodeState(raw(drift)));
        String stateWire = new String(OrdinaryCampaignScheduleCodec.encodeState(clockState()), StandardCharsets.UTF_8);
        byte[] floatMonth = bytes(stateWire.replace("\"months\":360", "\"months\":360.0"));
        assertTrue(parse(floatMonth).path("deadline_configuration").path("months").isFloatingPointNumber());
        assertThrows(IllegalArgumentException.class, () -> new M7SchedulingDomain().evaluate(request("ordinary_schedule_new", floatMonth, MACHINE)),
                "new state must reject the original nested floating token before reserializing a tree");
    }

    @Test void projectionTamperingAndAuthorityClaimsFailEvenWhenTheStoredGoalIsWellFormed() throws IOException {
        State state = clockState(); Plan plan = OrdinaryCampaignSchedule.consume(state,
                ordinary(state, 53144328, "battle-decision-epoch-advance-v1", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN),
                Optional.of(BigInteger.valueOf(53145168)));
        ObjectNode value = (ObjectNode) parse(OrdinaryCampaignScheduleCodec.encodePlan(plan));
        for (String authority : List.of("game_actions_submitted", "cold_authority_granted", "replay_authorized")) {
            ObjectNode forged = value.deepCopy(); forged.put(authority, true);
            assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodePlan(raw(forged)));
        }
        ObjectNode credit = value.deepCopy(); credit.put("saved_day_credit", 1);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodePlan(raw(credit)));
        ObjectNode step = value.deepCopy(); step.put("planner_route", "nonwar_only");
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodePlan(raw(step)));
        ObjectNode drift = value.deepCopy(); drift.put("effective_clock_target_raw", 53145168);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodePlan(raw(drift)));
        ObjectNode cap = value.deepCopy(); ((ObjectNode) cap.get("clock_deadline")).put("target_date_raw", 53145168);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodePlan(raw(cap)));
        String persisted = new String(OrdinaryCampaignScheduleCodec.encodePlan(plan), StandardCharsets.UTF_8);
        byte[] floatBoundary = bytes(persisted.replace("\"boundary_date_raw\":53145048", "\"boundary_date_raw\":53145048.0"));
        assertTrue(parse(floatBoundary).path("clock_deadline").path("boundary_date_raw").isFloatingPointNumber());
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignScheduleCodec.decodePlan(floatBoundary));
    }

    @Test void singleProviderWireRoundtripBindsTheActualObservationMachineAndNeverAddsASecondAuthority() throws Exception {
        byte[] descriptor = resourceRaw("/META-INF/services/org.xar.ck3.control.g2.common.G2Domain");
        assertEquals("22ce86c8ae7bad5487d0b10e7e82fbfc6c567ca2c02a6342027aa3828f8f21b3", sha(descriptor),
                "the actual final eight-domain production provider descriptor is mandatory");
        List<String> providers = new String(descriptor, StandardCharsets.UTF_8).lines()
                .map(String::strip).filter(line -> !line.isEmpty() && !line.startsWith("#")).toList();
        assertEquals(8, providers.size());
        assertEquals(List.of(M7SchedulingDomain.class.getName()), providers.stream().filter(line -> line.contains(".m7.")).toList());
        State state = clockState();
        ObjectNode input = planningInput(state, 53144328, Optional.of(BigInteger.valueOf(53145168)));
        var request = request("ordinary_schedule_plan", raw(input), MACHINE);
        var response = new M7SchedulingDomain().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        var freshResponse = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(request.requestId(), freshResponse.requestId()); assertEquals(request.source(), freshResponse.source());
        Plan fresh = OrdinaryCampaignScheduleCodec.decodePlan(freshResponse.result().bytes());
        assertEquals(BigInteger.valueOf(53145048), fresh.effectiveClockTargetRaw().orElseThrow());
        assertEquals("life-advance", fresh.ordinaryPlan().selectedStep());
        assertThrows(IllegalArgumentException.class, () -> new M7SchedulingDomain().evaluate(request("ordinary_schedule_plan", raw(input), "foreign-machine")));
        ObjectNode missing = input.deepCopy(); missing.remove("requested_clock_target_raw");
        assertThrows(IllegalArgumentException.class, () -> evaluate("ordinary_schedule_plan", missing));
        for (String token : List.of("true", "53145168.0", "\"53145168\"")) {
            byte[] wrong = bytes(new String(raw(input), StandardCharsets.UTF_8).replace(
                    "\"requested_clock_target_raw\":53145168", "\"requested_clock_target_raw\":" + token));
            assertFalse(parse(wrong).path("requested_clock_target_raw").isIntegralNumber(),
                    "the submitted original wrong token must not be erased by a fixture tree roundtrip");
            assertThrows(IllegalArgumentException.class,
                    () -> new M7SchedulingDomain().evaluate(request("ordinary_schedule_plan", wrong, MACHINE)));
        }
        byte[] nestedFloat = bytes(new String(raw(input), StandardCharsets.UTF_8).replace("\"native_revision\":24", "\"native_revision\":24.0"));
        assertTrue(parse(nestedFloat).path("ordinary_plan").path("observation").path("native_revision").isFloatingPointNumber());
        assertThrows(IllegalArgumentException.class, () -> new M7SchedulingDomain().evaluate(request("ordinary_schedule_plan", nestedFloat, MACHINE)),
                "actual ordinary reader receives the original nested float token, not a reconstructed tree");
        var originalRequest = request("goal_normalize", bytes("{\"unused\":\"" + "x".repeat(300_000) + "\"}"), MACHINE);
        IllegalArgumentException originalFailure = assertThrows(IllegalArgumentException.class,
                () -> new org.xar.ck3.control.g2.m7.M7Research().evaluate(originalRequest));
        IllegalArgumentException wrapperFailure = assertThrows(IllegalArgumentException.class,
                () -> new M7SchedulingDomain().evaluate(originalRequest));
        assertEquals(originalFailure.getClass(), wrapperFailure.getClass());
        assertEquals(originalFailure.getMessage(), wrapperFailure.getMessage(),
                "an established operation keeps its original domain budget and raw bytes");
        exportActualScheduleFixtures();
    }

    @Test void endpointAndExplicitAbsentDeadlineRemainDistinctWithoutAwardingCalendarProgress() throws IOException {
        State state = clockState(); long endpoint = state.deadline().orElseThrow().endpointDateRaw().longValueExact();
        for (long current : List.of(endpoint, endpoint + 24)) {
            Plan plan = OrdinaryCampaignSchedule.consume(state,
                    ordinary(state, current, "life-advance", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN),
                    Optional.of(BigInteger.valueOf(current + 24)));
            assertTrue(plan.effectiveClockTargetRaw().isEmpty()); assertEquals(0, plan.savedDayCredit());
            assertEquals(current == endpoint ? OrdinaryCampaignSchedule.ClockStatus.ENDPOINT_REACHED : OrdinaryCampaignSchedule.ClockStatus.ENDPOINT_OVERSHOT,
                    OrdinaryCampaignScheduleCodec.decodePlan(OrdinaryCampaignScheduleCodec.encodePlan(plan)).clockStatus());
        }
        State noDeadline = new State(state.goal(), Optional.empty());
        Plan unbounded = OrdinaryCampaignSchedule.consume(noDeadline,
                ordinary(noDeadline, 53144328, "life-advance", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN), Optional.of(BigInteger.valueOf(53144352)));
        assertEquals(OrdinaryCampaignSchedule.ClockStatus.NO_DEADLINE, unbounded.clockStatus());
        assertEquals(unbounded.requestedClockTargetRaw(), unbounded.effectiveClockTargetRaw());
        assertTrue(unbounded.clockDeadline().isEmpty());
        assertArrayEquals(OrdinaryCampaignScheduleCodec.encodeState(noDeadline), evaluate("ordinary_schedule_new", parse(OrdinaryCampaignScheduleCodec.encodeState(noDeadline))));
    }

    private static ObjectNode planningInput(State state, long current, Optional<BigInteger> target) {
        ObjectNode input = StrictJson.object(); input.set("state", parse(OrdinaryCampaignScheduleCodec.encodeState(state)));
        input.set("ordinary_plan", parse(M7OrdinaryPlanConsumer.encode(ordinary(state, current, "life-advance", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN))));
        if (target.isPresent()) { input.put("requested_clock_target_raw", target.orElseThrow()); } else { input.putNull("requested_clock_target_raw"); }
        return input;
    }
    private static M7OrdinaryPlanConsumer.Consumed ordinary(State state, long current, String step, M7OrdinaryPlanConsumer.Publication publication) {
        return M7OrdinaryPlanConsumer.consume(publication, observation(state, current), step, Optional.empty());
    }
    private static CheckpointContinuity.Observation observation(State state, long current) {
        return new CheckpointContinuity.Observation(MACHINE, "a".repeat(64),
                new CheckpointContinuity.GameIdentity(101, "20261023123045.123456+480", "D:/synthetic/ck3.exe"),
                "synthetic:schedule", 8, 24, "synthetic:episode", state.goal().currentCharacterId(), current, state.goal(), null, null);
    }
    private static State clockState() throws IOException {
        var configuration = configuration(resource("/schedule/deadline-original-producer.json").path("configurations").path("main").get("configuration"));
        return new State(OrdinaryCampaignGoal.newGoal(configuration.founding().campaignId(), 100), Optional.of(configuration));
    }
    private static CampaignDeadline.Configuration configuration(JsonNode row) {
        return CampaignDeadlineCodec.decodeConfiguration(raw(row), OrdinaryCampaignSchedule::calendar);
    }
    private static G2Request request(String operation, byte[] input, String machineId) {
        G2Source source = new G2Source(machineId, Instant.parse("2026-10-22T22:54:34Z").toString(), "1.20.0.4-retained-fixture",
                new ExactRef("D:/synthetic/schedule-test-input.json", 1, "a".repeat(64)));
        return request(operation, input, source);
    }
    private static G2Request request(String operation, byte[] input, G2Source source) {
        byte[] payload = bytes("{\"operation\":\"" + operation + "\",\"input\":" + new String(input, StandardCharsets.UTF_8) + "}");
        return new G2Request("schedule-software-fixture", Milestone.M7, source, ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
    }
    private static byte[] evaluate(String operation, JsonNode input) {
        return new M7SchedulingDomain().evaluate(request(operation, raw(input), MACHINE)).result().bytes();
    }
    private static JsonNode named(JsonNode rows, String name) {
        for (JsonNode row : rows) { if (name.equals(row.path("name").textValue())) { return row; } }
        throw new IllegalArgumentException("mandatory original producer case missing: " + name);
    }
    private static JsonNode resource(String name) throws IOException {
        return StrictJson.parse(resourceRaw(name), StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static byte[] resourceRaw(String name) throws IOException {
        try (var stream = OrdinaryCampaignScheduleTest.class.getResourceAsStream(name)) {
            assertNotNull(stream, "mandatory original producer resource; missing is RED");
            return stream.readAllBytes();
        }
    }
    /** Actual domain exports use the retained original oracle file, never an invented source identity. */
    private void exportActualScheduleFixtures() throws Exception {
        byte[] resourceBytes = resourceRaw("/schedule/deadline-original-producer.json");
        String configuredOracle = System.getenv("XAR_M7_SCHEDULE_ORACLE_PATH");
        Path oracle;
        if (configuredOracle == null) {
            oracle = temporary.resolve("deadline-original-producer.json");
            Files.write(oracle, resourceBytes, StandardOpenOption.CREATE_NEW);
        } else {
            assertFalse(configuredOracle.isBlank()); oracle = Path.of(configuredOracle).toRealPath();
            assertTrue(List.of("producer-golden.json", "deadline-original-producer.json").contains(oracle.getFileName().toString()),
                    "exporter accepts only the retained pure deadline oracle, never actual Driver/SAVE bodies");
        }
        byte[] original = Files.readAllBytes(oracle);
        assertArrayEquals(resourceBytes, original, "export source is the exact original deadline capture");
        JsonNode capture = parse(original);
        G2Source source = new G2Source(capture.path("machine_id").textValue(),
                Instant.parse(capture.path("captured_at_utc").textValue()).toString(), "1.20.0.4-retained-fixture",
                new ExactRef(oracle.toRealPath().toString(), original.length, sha(original)));
        String configuredOutput = System.getenv("XAR_M7_SCHEDULE_EXPORT_DIR");
        Path output = configuredOutput == null ? temporary.resolve("schedule-export") : Path.of(configuredOutput);
        if (configuredOutput != null) { assertFalse(configuredOutput.isBlank()); }
        Files.createDirectories(output); output = output.toRealPath();
        var outputs = StrictJson.object().putArray("outputs");
        var clock = clockState().deadline().orElseThrow();
        ObjectNode goalInput = StrictJson.object(); goalInput.put("campaign_id", clock.founding().campaignId()); goalInput.put("character_id", 100);
        byte[] goalBytes = export(output, outputs, "goal-new", request("goal_new", raw(goalInput), source));
        var actualGoal = GoalCodec.decodeGoal(goalBytes);
        byte[] actualGoalPlan = export(output, outputs, "goal-plan", request("goal_plan", goalBytes, source));
        var goalPlan = GoalCodec.decodePlan(actualGoalPlan);
        assertEquals(actualGoal.campaignId(), goalPlan.campaignId()); assertEquals(actualGoal.currentCharacterId(), goalPlan.currentCharacterId());
        State state = new State(actualGoal, Optional.of(clock));
        byte[] stateBytes = OrdinaryCampaignScheduleCodec.encodeState(state);
        outputs.add(retain(output, "M7.schedule.state.json", stateBytes).toJson());
        byte[] created = export(output, outputs, "new", request("ordinary_schedule_new", stateBytes, source));
        assertEquals(state, OrdinaryCampaignScheduleCodec.decodeState(created));
        byte[] restored = export(output, outputs, "read", request("ordinary_schedule_read", created, source));
        assertArrayEquals(created, restored);
        JsonNode originalCase = named(capture.path("cases"), "clip-first-month");
        long current = originalCase.path("starting").path("date_raw").longValue();
        ObjectNode ordinaryInput = StrictJson.object(); ordinaryInput.put("schema", M7OrdinaryPlanConsumer.INPUT_SCHEMA);
        ordinaryInput.put("publication", M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN.wire());
        ordinaryInput.set("observation", parse(CheckpointContinuity.encodeObservation(observation(state, current))));
        ordinaryInput.put("selected_step", "life-advance"); ordinaryInput.putNull("government_context");
        byte[] consumedBytes = export(output, outputs, "ordinary-consume", request("ordinary_plan_consume", raw(ordinaryInput), source));
        var consumed = M7OrdinaryPlanConsumer.decode(consumedBytes);
        assertArrayEquals(actualGoalPlan, GoalCodec.encodePlan(consumed.campaignGoalPlanUsed()),
                "actual goal_plan bytes must be consumed by the actual ordinary_plan_consume producer");
        ObjectNode planInput = StrictJson.object(); planInput.set("state", parse(restored));
        planInput.set("ordinary_plan", parse(consumedBytes));
        planInput.put("requested_clock_target_raw", originalCase.path("proposed_target_raw").bigIntegerValue());
        byte[] planned = export(output, outputs, "plan", request("ordinary_schedule_plan", raw(planInput), source));
        Plan fresh = OrdinaryCampaignScheduleCodec.decodePlan(planned);
        assertEquals(consumed, fresh.ordinaryPlan());
        assertArrayEquals(actualGoalPlan, GoalCodec.encodePlan(fresh.ordinaryPlan().campaignGoalPlanUsed()));
        assertEquals(originalCase.path("outcome").get("value"), parse(CampaignDeadlineCodec.encodeCap(fresh.clockDeadline().orElseThrow())));
        assertArrayEquals(planned, OrdinaryCampaignScheduleCodec.encodePlan(fresh));
        outputs.add(retain(output, "M7.schedule.plan.json", planned).toJson());
        ObjectNode metadata = StrictJson.object(); metadata.put("schema", "xar.m7-ordinary-schedule-producer-export/v1");
        metadata.put("machine_id", MACHINE); metadata.put("observed_at_utc", Instant.now().toString());
        metadata.put("status", "ORIGINAL_DEADLINE_DOMAIN_WIRE_FRESH_CONSUMER_PASS_HTTP_NOTRUN");
        metadata.set("source", parse(G2Wire.sourceBytes(source))); metadata.set("original_producer_sources", capture.get("sources"));
        metadata.put("original_deadline_case", "clip-first-month"); metadata.set("outputs", outputs);
        metadata.putArray("actual_production_chain").add("goal_new").add("goal_plan").add("ordinary_plan_consume")
                .add("ordinary_schedule_new").add("ordinary_schedule_read").add("ordinary_schedule_plan");
        metadata.put("observation_is_explicit_software_fixture", true); metadata.put("game_calls", 0);
        metadata.put("actual_driver_or_save_body_reads", 0); metadata.put("http_executed", false);
        metadata.put("scope", "Exact original pure deadline configuration and request, composed with typed goal and a synthetic ordinary observation; actual domain/wire/fresh readers, no live/recovery/action authority.");
        retain(output, "M7.schedule.metadata.json", StrictJson.canonical(metadata, StrictJson.EXPLICIT_MAX_BYTES));
        assertArrayEquals(original, Files.readAllBytes(oracle));
    }
    private static byte[] export(Path output, com.fasterxml.jackson.databind.node.ArrayNode outputs, String name, G2Request request) throws Exception {
        byte[] requestBytes = G2Wire.encodeRequest(request);
        ExactRef requestRef = retain(output, "M7.schedule." + name + ".request.json", requestBytes); outputs.add(requestRef.toJson());
        var response = new M7SchedulingDomain().evaluate(G2Wire.decodeRequest(Files.readAllBytes(Path.of(requestRef.path()))));
        outputs.add(retain(output, "M7.schedule." + name + ".result.json", response.result().bytes()).toJson());
        ExactRef responseRef = retain(output, "M7.schedule." + name + ".response.json", G2Wire.encodeResponse(response)); outputs.add(responseRef.toJson());
        var fresh = G2Wire.decodeResponse(Files.readAllBytes(Path.of(responseRef.path())));
        assertEquals(request.source(), fresh.source()); assertArrayEquals(response.result().bytes(), fresh.result().bytes());
        return fresh.result().bytes();
    }
    private static ExactRef retain(Path output, String filename, byte[] bytes) throws Exception {
        Path file = output.resolve(filename); Files.write(file, bytes, StandardOpenOption.CREATE_NEW);
        return new ExactRef(file.toRealPath().toString(), bytes.length, sha(bytes));
    }
    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static JsonNode parse(byte[] value) { return StrictJson.parse(value, M7OrdinaryPlanConsumer.MAX_BYTES); }
}
