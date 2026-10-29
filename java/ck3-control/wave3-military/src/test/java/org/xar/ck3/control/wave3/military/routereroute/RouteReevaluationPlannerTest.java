package org.xar.ck3.control.wave3.military.routereroute;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner.*;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationCodec.Request;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement.FixedPoint;

final class RouteReevaluationPlannerTest {
    private static final Context SAFE = new Context(false, false, false, false);
    private static final String ORIGINAL = """
        import json,sys,textwrap
        data=json.load(sys.stdin)
        body=textwrap.indent(textwrap.dedent(data['excerpt']),'        ')
        prefix='''def original(v):
            preview=v['preview']; province_id=9; candidate_source=v['source']
            stationary_threats=[{}] if v['threatened'] else []
            refuge_lifecycle_active=v['refuge']; active_route_unsafe=v['unsafe']
            exact_siege_rejection={} if v['siege'] else None
            available_steps=v['steps']; route_rejections=[]; war_summary=[]
            for _ in [0]:
        '''
        suffix='''        return {'phase':'AUDIT_CONTINUATION','route_rejections':route_rejections}
            return {'phase':'FALLTHROUGH','route_rejections':route_rejections}
        '''
        namespace={};exec(prefix+body+suffix,namespace)
        print(json.dumps([namespace['original'](v) for v in data['cases']],sort_keys=True,separators=(',',':')))
        """;

    @Test void sourceBoundDeferredOriginalDifferential() throws Exception {
        byte[] fixtureBytes;
        try (var stream = getClass().getResourceAsStream("/routereroute/ordinary-deferred-source01.json")) {
            assertNotNull(stream, "mandatory exact original branch fixture"); fixtureBytes = stream.readNBytes(16_385);
        }
        assertTrue(fixtureBytes.length <= 16_384); JsonNode fixture = StrictJson.parse(fixtureBytes);
        assertEquals("xar.route-reevaluation-original-branch-fixture/v1", fixture.path("schema").textValue());
        byte[] excerpt = fixture.path("excerpt").path("utf8").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(fixture.path("excerpt").path("bytes").intValue(), excerpt.length);
        assertEquals(fixture.path("excerpt").path("sha256").textValue(), StockRouteRuleReader.sha256(excerpt));
        ObjectNode payload = StrictJson.object(); payload.put("excerpt", new String(excerpt, StandardCharsets.UTF_8));
        var vectors = payload.putArray("cases"); List<Result> actual = new ArrayList<>();
        for (int flags = 0; flags < 16; flags++) {
            Context context = new Context((flags & 1) != 0, (flags & 2) != 0, (flags & 4) != 0, (flags & 8) != 0);
            for (CandidateSource source : List.of(CandidateSource.WAR_OBJECTIVE_PROVINCE, CandidateSource.PLAYER_HELD_COUNTY_CAPITAL,
                    CandidateSource.SAME_REALM_VASSAL_CAPITAL)) {
                for (String stage : List.of("other", "move_mode_unavailable")) {
                    List<String> steps = flags % 3 == 0 ? List.of("life-advance", "life-advance-one-day")
                            : flags % 3 == 1 ? List.of("life-advance") : List.of();
                    ObjectNode vector = vectors.addObject(); vector.put("threatened", context.stationaryThreatened());
                    vector.put("refuge", context.refugeLifecycleActive()); vector.put("unsafe", context.activeRouteUnsafe());
                    vector.put("siege", context.exactSiegeRejected()); vector.put("source", source.name().toLowerCase(Locale.ROOT));
                    var stepArray = vector.putArray("steps"); steps.forEach(stepArray::add);
                    ObjectNode receipt = receipt(9, "deferred", stage); vector.set("preview", receipt.path("result").get("route_preview"));
                    actual.add(plan(List.of(receipt), context, List.of(new Objective(9, source, false)), steps));
                }
            }
        }
        JsonNode original = runOriginal(StrictJson.canonical(payload)); assertEquals(96, original.size());
        for (int index = 0; index < original.size(); index++) {
            JsonNode expected = original.get(index); Result value = actual.get(index);
            String phase = value instanceof ReadinessRequired ? "native_war_move_readiness_observation_required"
                    : value instanceof ExistingDateBoundary date ? date.existingCandidateStep().isPresent()
                        ? "native_war_route_preview_deferred" : "native_war_route_preview_deferred_unsupported"
                    : value instanceof Exhausted ? "FALLTHROUGH" : "UNEXPECTED";
            assertEquals(expected.path("phase").textValue(), phase, "actual original branch " + index);
            assertEquals(expected.path("route_rejections").size(), value.rejections().size());
            for (int rejection = 0; rejection < value.rejections().size(); rejection++) {
                assertEquals(expected.path("route_rejections").get(rejection).path("status").textValue(),
                        value.rejections().get(rejection).reason().name().toLowerCase(Locale.ROOT));
            }
            assertRoundTrip(value); assertFalse(value.actionAuthorized());
        }
    }
    @Test void previewQueriesRespectLeaseAvailabilityAndRank() {
        List<Objective> goals = new ArrayList<>();
        for (int index = 0; index < 20; index++) { goals.add(new Objective(index + 20, CandidateSource.WAR_OBJECTIVE_PROVINCE, true)); }
        goals.add(new Objective(9, CandidateSource.WAR_OBJECTIVE_PROVINCE, false));
        PreviewQuery required = assertInstanceOf(PreviewQuery.class, plan(List.of(), SAFE, goals, List.of()));
        assertEquals("preview-move-army-2-to-9", required.requiredStep()); assertFalse(required.stepAvailable()); assertEquals(20, required.rejections().size());
        PreviewQuery available = assertInstanceOf(PreviewQuery.class, plan(List.of(), SAFE, goals, List.of(required.requiredStep())));
        assertTrue(available.stepAvailable());
        ObjectNode stale = receipt(9, "available", null); stale.withObject("/result").put("queried_native_revision", 7);
        assertInstanceOf(PreviewQuery.class, plan(List.of(stale), SAFE, goals, List.of()));
        AuditContinuation audit = assertInstanceOf(AuditContinuation.class, plan(List.of(receipt(9, "available", null)), SAFE, goals, List.of()));
        assertEquals(20, audit.objectiveRank());
    }
    @Test void actualCandidateIntakePreservesOrderingDuplicatesAndReliefSource() {
        List<Objective> goals = RouteReevaluationPlanner.exactSiegeObjectives(List.of(9, 10, 9, 11), Set.of(9, 11), Optional.empty(), Set.of(11));
        assertEquals(List.of(9, 9, 11), goals.stream().map(Objective::targetProvinceId).toList());
        assertTrue(goals.get(2).blocked()); assertEquals(CandidateSource.WAR_OBJECTIVE_PROVINCE, goals.getFirst().source());
        List<Objective> relief = RouteReevaluationPlanner.exactSiegeObjectives(List.of(9, 10), Set.of(9), Optional.of(12), Set.of());
        assertEquals(List.of(new Objective(12, CandidateSource.ENEMY_SIEGE_RELIEF, false)), relief);
    }
    @Test void usablePreviewRequiresIndependentAuditAndRoundTripsOpaqueEvidence() {
        ObjectNode value = receipt(9, "available", null);
        value.withObject("/result/route_preview").set("opaque", parse("{\"null\":null,\"empty\":[],\"u64\":18446744073709551615,\"float\":1.0,\"fraction\":1.25}"));
        assertThrows(IllegalArgumentException.class, () -> StrictJson.canonical(packet(List.of(value))),
                "the shared integer-only emitter cannot serialize original opaque decimal evidence");
        Result result = plan(List.of(value), SAFE, List.of(new Objective(9, CandidateSource.WAR_OBJECTIVE_PROVINCE, false),
                new Objective(10, CandidateSource.WAR_OBJECTIVE_PROVINCE, false)), List.of());
        AuditContinuation audit = assertInstanceOf(AuditContinuation.class, result);
        assertEquals(9, audit.targetProvinceId()); assertEquals(0, audit.objectiveRank()); assertFalse(audit.actionAuthorized());
        assertRoundTrip(result);
        JsonNode encoded = StrictJson.parse(RouteReevaluationCodec.encodeResult(audit));
        assertTrue(encoded.path("preview").path("opaque").has("null"));
        assertEquals("18446744073709551615", encoded.path("preview").path("opaque").path("u64").asText());
        assertTrue(encoded.path("preview").path("opaque").path("float").isFloatingPointNumber());
        assertEquals(new java.math.BigDecimal("1.25"), encoded.path("preview").path("opaque").path("fraction").decimalValue());
        byte[] request = RouteReevaluationCodec.encodeRequest(request(List.of(value), SAFE, goal(), List.of()));
        assertArrayEquals(RouteReevaluationCodec.encodeResult(result), RouteReevaluationCodec.project(request));
        assertFalse(encoded.has("selected_step")); assertFalse(encoded.has("qualified_contact"));
    }
    @Test void currentObjectivePrecedesBlockedCheckAndRetainsStationaryBoundary() {
        List<Objective> current = List.of(new Objective(1, CandidateSource.WAR_OBJECTIVE_PROVINCE, true));
        assertInstanceOf(Arrived.class, plan(List.of(), SAFE, current, List.of()));
        assertInstanceOf(StationaryContinuation.class, plan(List.of(), new Context(true, false, false, false), current, List.of()));
        Exhausted rejected = assertInstanceOf(Exhausted.class, plan(List.of(), new Context(false, false, true, true), current, List.of()));
        assertEquals(RejectionReason.CURRENT_EXACT_SIEGE_REJECTED, rejected.rejections().getFirst().reason());
    }
    @Test void restoreAndMergeInvalidateActualConsumer() {
        ObjectNode valid = receipt(9, "available", null);
        for (String barrier : List.of("{\"command\":\"restore-checkpoint\",\"ok\":true}",
                "{\"command\":\"merge-armies-2-with-4\",\"ok\":true}")) {
            assertInstanceOf(PreviewQuery.class, plan(List.of(valid, object(barrier)), SAFE, goal(), List.of()));
            assertInstanceOf(AuditContinuation.class, plan(List.of(object(barrier), valid), SAFE, goal(), List.of()));
        }
    }
    @Test void strictRequestAndResultContractRejectsCorruption() {
        byte[] input = RouteReevaluationCodec.encodeRequest(request(List.of(), SAFE, goal(), List.of()));
        for (String field : List.of("context", "lookup", "ordered_objectives", "available_steps")) {
            ObjectNode missing = (ObjectNode) StrictJson.parse(input); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> RouteReevaluationCodec.decodeRequest(StrictJson.canonical(missing)));
        }
        ObjectNode wrongBool = (ObjectNode) StrictJson.parse(input); wrongBool.withObject("/context").put("stationary_threatened", 1);
        assertThrows(IllegalArgumentException.class, () -> RouteReevaluationCodec.decodeRequest(StrictJson.canonical(wrongBool)));
        ObjectNode wrongId = (ObjectNode) StrictJson.parse(input); ((ObjectNode) wrongId.withArray("ordered_objectives").get(0)).put("target_province_id", 9.0);
        assertThrows(IllegalArgumentException.class, () -> RouteReevaluationCodec.decodeRequest(wrongId.toString().getBytes(StandardCharsets.UTF_8)));
        ObjectNode authority = (ObjectNode) StrictJson.parse(RouteReevaluationCodec.encodeResult(new Exhausted(List.of()))); authority.put("action_authorized", true);
        assertThrows(IllegalArgumentException.class, () -> RouteReevaluationCodec.decodeResult(StrictJson.canonical(authority)));
        ObjectNode wrongStep = (ObjectNode) StrictJson.parse(RouteReevaluationCodec.project(input)); wrongStep.put("required_step", "move-army-2-to-9");
        assertThrows(IllegalArgumentException.class, () -> RouteReevaluationCodec.decodeResult(StrictJson.canonical(wrongStep)));
    }
    @Test void requestAndAllResultBranchesRoundTrip() {
        for (Context context : List.of(SAFE, new Context(true, false, false, false), new Context(false, true, false, false), new Context(false, false, true, false))) {
            for (String status : List.of("available", "deferred")) {
                Request request = request(List.of(receipt(9, status, null)), context, goal(), List.of("life-advance-one-day"));
                byte[] encoded = RouteReevaluationCodec.encodeRequest(request);
                assertArrayEquals(encoded, RouteReevaluationCodec.encodeRequest(RouteReevaluationCodec.decodeRequest(encoded)));
                Result result = RouteReevaluationCodec.decodeResult(RouteReevaluationCodec.project(encoded)); assertRoundTrip(result);
            }
        }
        assertEquals(new Unavailable(MissingInput.CURRENT_DATE, List.of()), roundTrip(new Unavailable(MissingInput.CURRENT_DATE, List.of())));
        assertEquals(new StationaryContinuation(1, 0, List.of()), roundTrip(new StationaryContinuation(1, 0, List.of())));
        assertEquals(new Arrived(1, 0, List.of()), roundTrip(new Arrived(1, 0, List.of())));
        assertEquals(new Exhausted(List.of()), roundTrip(new Exhausted(List.of())));
    }
    @Test void sourceInputOwnershipAndIntegerTokens() {
        Request request = request(List.of(), SAFE, goal(), List.of()); byte[] original = request.lookupPacket();
        byte[] mutated = request.lookupPacket(); mutated[0] = ' '; assertArrayEquals(original, request.lookupPacket());
        ObjectNode noDate = packet(List.of()); noDate.putNull("date_raw");
        assertEquals(MissingInput.CURRENT_DATE, assertInstanceOf(Unavailable.class,
                RoutePlanningConsumer.planOrdinary(StrictJson.canonical(noDate), SAFE, goal(), List.of())).missing());
        ObjectNode noLease = packet(List.of()); noLease.putNull("snapshot");
        assertEquals(MissingInput.SAME_FRAME_LEASE, assertInstanceOf(Unavailable.class,
                RoutePlanningConsumer.planOrdinary(StrictJson.canonical(noLease), SAFE, goal(), List.of())).missing());
        ObjectNode wrong = packet(List.of()); wrong.withObject("/snapshot").put("native_revision", true);
        assertThrows(IllegalArgumentException.class, () -> RoutePlanningConsumer.planOrdinary(StrictJson.canonical(wrong), SAFE, goal(), List.of()));
    }
    @Test void minedVanillaReevaluationDefinesRetainUnknownPredictionAndSource(@TempDir Path temporary) throws Exception {
        byte[] fixtureBytes;
        try (var stream = getClass().getResourceAsStream("/routereroute/vanilla-reevaluation-source01.json")) {
            assertNotNull(stream, "mandatory exact source excerpt"); fixtureBytes = stream.readNBytes(8_193);
        }
        assertTrue(fixtureBytes.length <= 8_192); JsonNode fixture = StrictJson.parse(fixtureBytes);
        byte[] excerpt = fixture.path("excerpt").path("utf8").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(fixture.path("excerpt").path("bytes").intValue(), excerpt.length);
        String sha = fixture.path("excerpt").path("sha256").textValue(); assertEquals(sha, StockRouteRuleReader.sha256(excerpt));
        Path path = temporary.resolve("source.txt"); Files.write(path, excerpt); RouteReevaluationRules rules = RouteReevaluationRules.read(path, sha);
        assertEquals(List.of(0, 0, 1, 2, 3, 3, 3), rules.goalsPerTier()); assertEquals(250, rules.resupplyInterruptedCooldownDays());
        assertEquals(62_500, rules.badAdjacencyPredictionRatio().raw()); assertEquals(18_000_000, rules.maximumExtraPathCost().raw());
        assertEquals(RouteReevaluationRules.Hint.NATIVE_PREDICTION_REQUIRED, rules.badAdjacencyHint(Optional.empty(), Optional.empty()));
        assertEquals(RouteReevaluationRules.Hint.NO_ALTERNATIVE_HINT, rules.badAdjacencyHint(Optional.of(new FixedPoint(62_500)), Optional.empty()));
        assertEquals(RouteReevaluationRules.Hint.ALTERNATIVE_COST_REQUIRED, rules.badAdjacencyHint(Optional.of(new FixedPoint(62_499)), Optional.empty()));
        assertEquals(RouteReevaluationRules.Hint.ALTERNATIVE_CANDIDATE,
                rules.badAdjacencyHint(Optional.of(new FixedPoint(62_499)), Optional.of(new FixedPoint(18_000_000))));
        assertEquals(RouteReevaluationRules.Hint.NO_ALTERNATIVE_HINT,
                rules.badAdjacencyHint(Optional.of(new FixedPoint(62_499)), Optional.of(new FixedPoint(18_000_001))));
        Files.writeString(path, "changed"); assertThrows(java.io.IOException.class, () -> RouteReevaluationRules.read(path, sha));
    }
    private static Request request(List<ObjectNode> rows, Context context, List<Objective> goals, List<String> steps) {
        return new Request(RoutePreviewConsumerCodec.encodeEnvelope(packet(rows)), context, goals, steps);
    }
    private static Result plan(List<ObjectNode> rows, Context context, List<Objective> goals, List<String> steps) {
        return RoutePlanningConsumer.planOrdinary(RoutePreviewConsumerCodec.encodeEnvelope(packet(rows)), context, goals, steps);
    }
    private static List<Objective> goal() { return List.of(new Objective(9, CandidateSource.WAR_OBJECTIVE_PROVINCE, false)); }
    private static Result roundTrip(Result value) { return RouteReevaluationCodec.decodeResult(RouteReevaluationCodec.encodeResult(value)); }
    private static void assertRoundTrip(Result value) {
        assertArrayEquals(RouteReevaluationCodec.encodeResult(value), RouteReevaluationCodec.encodeResult(roundTrip(value)));
    }
    private static ObjectNode packet(List<ObjectNode> rows) {
        ObjectNode root = object("{\"commands\":[],\"snapshot\":{\"snapshot_id\":\"s1\",\"revision\":7,\"native_revision\":11,\"episode_run_id\":\"ep1\",\"diagnostics\":{\"connection_generation\":3}},\"army_id\":2,\"origin_province_id\":1,\"target_province_id\":9,\"date_raw\":42}");
        rows.forEach(row -> root.withArray("commands").add(row.deepCopy())); return root;
    }
    private static ObjectNode receipt(int target, String status, String stage) {
        ObjectNode value = object("{\"command\":\"preview-move-army-2-to-" + target + "\",\"ok\":true,\"result\":{\"queried_snapshot_id\":\"s1\",\"queried_revision\":7,\"queried_native_revision\":11,\"queried_connection_generation\":3,\"queried_episode_run_id\":\"ep1\",\"route_preview\":{\"status\":\"" + status + "\",\"army_id\":2,\"origin_province_id\":1,\"target_province_id\":" + target + ",\"previewed_date_raw\":42,\"route_province_ids\":[3," + target + "]}}}");
        if (stage != null) { value.withObject("/result/route_preview").put("native_rejection_stage", stage); } return value;
    }
    private static ObjectNode object(String value) { return (ObjectNode) parse(value); }
    private static JsonNode parse(String value) { return StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode runOriginal(byte[] input) throws Exception {
        String python = System.getProperty("xar.python");
        assertNotNull(python, "xar.python must explicitly identify the original-producer interpreter");
        assertFalse(python.isBlank(), "xar.python must not be blank");
        Process child = new ProcessBuilder(python, "-I", "-B", "-X", "utf8", "-c", ORIGINAL)
                .redirectErrorStream(true).start();
        try {
            try (var stdin = child.getOutputStream()) { stdin.write(input); }
            byte[] output = child.getInputStream().readNBytes(262_145);
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "finite original branch differential");
            assertEquals(0, child.exitValue(), new String(output, StandardCharsets.UTF_8)); assertTrue(output.length <= 262_144);
            return StrictJson.parse(output, 262_144);
        } finally { if (child.isAlive()) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); } }
    }
}
