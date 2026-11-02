package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpServer;
import java.math.BigInteger;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryDecisionSelector;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Pure public DATA scenes and self-owned loopback HTTP; no capture, issuer or Native authority. */
final class RootCouncilDecisionProjectionTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final OperationKey PRIVATE = new OperationKey("private-assign-councillor-v1");
    private static final ExactRef EVIDENCE = new ExactRef("fixture-source", 1, "a".repeat(64));
    private static final JointBudgetSelector.Claims CLAIMS = new JointBudgetSelector.Claims(
            Set.of(), Set.of(), Set.of(BigInteger.valueOf(16777232)), Set.of("council-seat:councillor_steward"));
    private static final String QUERY = "ew0KICAic3RhdHVzIjogImF2YWlsYWJsZSIsDQogICJzdGVwIjogInByaXZhdGUtcXVlcnktY291bmNpbC1maW5hbC1nYXRlcy12MSIsDQogICJwcml2YXRlX2J1aWxkIjogdHJ1ZSwNCiAgInJlYWRfb25seSI6IHRydWUsDQogICJhZHZlcnRpc2VkIjogZmFsc2UsDQogICJxdWVyaWVkX3NuYXBzaG90X2lkIjogInNuYXBzaG90LTEiLA0KICAicXVlcmllZF9yZXZpc2lvbiI6IDEsDQogICJxdWVyaWVkX25hdGl2ZV9yZXZpc2lvbiI6IDEsDQogICJzb3VyY2VfZnJhbWUiOiB7DQogICAgInNuYXBzaG90X2lkIjogInNuYXBzaG90LTEiLA0KICAgICJyZXZpc2lvbiI6IDEsDQogICAgIm5hdGl2ZV9yZXZpc2lvbiI6IDEsDQogICAgImRhdGVfcmF3IjogMjQwMDAsDQogICAgInBsYXllcl9jaGFyYWN0ZXJfaWQiOiAyOTgyOSwNCiAgICAicGF1c2VkIjogdHJ1ZQ0KICB9LA0KICAiY291bmNpbF9jb21wb3NpdGlvbl9jYW5kaWRhdGVzIjogew0KICAgICJzbmFwc2hvdCI6IHsNCiAgICAgICJzbmFwc2hvdF9pZCI6ICJuYXRpdmU6MSIsDQogICAgICAicHVibGljX3JldmlzaW9uIjogMSwNCiAgICAgICJuYXRpdmVfcmV2aXNpb24iOiAxLA0KICAgICAgImRhdGVfcmF3IjogMjQwMDAsDQogICAgICAicGF1c2VkIjogdHJ1ZQ0KICAgIH0sDQogICAgIm93bmVyX2NoYXJhY3Rlcl9pZCI6IDI5ODI5LA0KICAgICJwb3NpdGlvbiI6IHsNCiAgICAgICJwb3NpdGlvbl9rZXkiOiAiY291bmNpbGxvcl9zdGV3YXJkIiwNCiAgICAgICJpbmN1bWJlbnRfY2hhcmFjdGVyX2lkIjogMTY3NzcyMTgsDQogICAgICAiaW5jdW1iZW50X21haW5fc2tpbGwiOiB7DQogICAgICAgICJrZXkiOiAic3Rld2FyZHNoaXAiLA0KICAgICAgICAidmFsdWUiOiA5DQogICAgICB9LA0KICAgICAgInZhY2FudCI6IGZhbHNlLA0KICAgICAgImFjdGlvbl9yb3V0ZSI6ICJyZXBsYWNlIg0KICAgIH0sDQogICAgImNhbmRpZGF0ZV9jb2xsZWN0aW9uX2NvbXBsZXRlIjogdHJ1ZSwNCiAgICAiY2FuZGlkYXRlcyI6IFsNCiAgICAgIHsNCiAgICAgICAgImNoYXJhY3Rlcl9pZCI6IDE2Nzc3MjMyLA0KICAgICAgICAibmF0aXZlX2NvbGxlY3Rpb25fb3JkaW5hbCI6IDEsDQogICAgICAgICJlbGlnaWJsZSI6IHRydWUsDQogICAgICAgICJlbGlnaWJpbGl0eV9yZWFzb24iOiAibmF0aXZlX2NhbmRpZGF0ZV9wcm92aWRlcl9hY2NlcHRlZCIsDQogICAgICAgICJtYWluX3NraWxsIjogew0KICAgICAgICAgICJrZXkiOiAic3Rld2FyZHNoaXAiLA0KICAgICAgICAgICJ2YWx1ZSI6IDIyDQogICAgICAgIH0sDQogICAgICAgICJhY3Rpb25fcm91dGUiOiAicmVwbGFjZSINCiAgICAgIH0sDQogICAgICB7DQogICAgICAgICJjaGFyYWN0ZXJfaWQiOiAxNjc3NzIzMywNCiAgICAgICAgIm5hdGl2ZV9jb2xsZWN0aW9uX29yZGluYWwiOiAwLA0KICAgICAgICAiZWxpZ2libGUiOiB0cnVlLA0KICAgICAgICAiZWxpZ2liaWxpdHlfcmVhc29uIjogIm5hdGl2ZV9jYW5kaWRhdGVfcHJvdmlkZXJfYWNjZXB0ZWQiLA0KICAgICAgICAibWFpbl9za2lsbCI6IHsNCiAgICAgICAgICAia2V5IjogInN0ZXdhcmRzaGlwIiwNCiAgICAgICAgICAidmFsdWUiOiAxNw0KICAgICAgICB9LA0KICAgICAgICAiYWN0aW9uX3JvdXRlIjogInJlcGxhY2UiDQogICAgICB9DQogICAgXSwNCiAgICAicmVhZGluZXNzIjogew0KICAgICAgImlkZW50aXR5X3JlYWR5IjogdHJ1ZSwNCiAgICAgICJjYW5kaWRhdGVfY29sbGVjdGlvbl9yZWFkeSI6IHRydWUsDQogICAgICAiaW5jdW1iZW50X3JlYWR5IjogdHJ1ZSwNCiAgICAgICJpbmN1bWJlbnRfbWFpbl9za2lsbF9yZWFkeSI6IHRydWUsDQogICAgICAiY2FuZGlkYXRlX2xlZ2FsaXR5X3JlYWR5IjogdHJ1ZSwNCiAgICAgICJtYWluX3NraWxsX3JlYWR5IjogdHJ1ZSwNCiAgICAgICJhY3Rpb25fcm91dGVfcmVhZHkiOiB0cnVlLA0KICAgICAgInNhbWVfZnJhbWVfcmVhZHkiOiB0cnVlLA0KICAgICAgInJlYWR5IjogdHJ1ZQ0KICAgIH0NCiAgfSwNCiAgImNvdW5jaWxfZmluYWxfZ2F0ZXMiOiB7DQogICAgInNjaGVtYSI6ICJ4YXIuY2szLnByaXZhdGUuY291bmNpbC1maW5hbC1nYXRlcy92MSIsDQogICAgInN0YXR1cyI6ICJhdmFpbGFibGUiLA0KICAgICJ1bmF2YWlsYWJsZV9yZWFzb24iOiAibm9uZSIsDQogICAgImNhbmRpZGF0ZV9jb3VudCI6IDIsDQogICAgInJvd3MiOiBbDQogICAgICB7DQogICAgICAgICJjaGFyYWN0ZXJfaWQiOiAxNjc3NzIzMiwNCiAgICAgICAgIm5hdGl2ZV9jb2xsZWN0aW9uX29yZGluYWwiOiAxLA0KICAgICAgICAiZmluYWxfZ2F0ZV9hdmFpbGFibGUiOiB0cnVlLA0KICAgICAgICAiY2FuZGlkYXRlX2FscmVhZHlfY291bmNpbGxvciI6IGZhbHNlLA0KICAgICAgICAiY2FuZGlkYXRlX2lzX2d1ZXN0IjogZmFsc2UsDQogICAgICAgICJwZW5kaW5nX2NoYXJhY3Rlcl9pbnRlcmFjdGlvbiI6IGZhbHNlLA0KICAgICAgICAiaW5jdW1iZW50X2ZpcmVhYmlsaXR5X2V2YWx1YXRlZCI6IHRydWUsDQogICAgICAgICJpbmN1bWJlbnRfY2FuX2JlX2ZpcmVkIjogdHJ1ZQ0KICAgICAgfSwNCiAgICAgIHsNCiAgICAgICAgImNoYXJhY3Rlcl9pZCI6IDE2Nzc3MjMzLA0KICAgICAgICAibmF0aXZlX2NvbGxlY3Rpb25fb3JkaW5hbCI6IDAsDQogICAgICAgICJmaW5hbF9nYXRlX2F2YWlsYWJsZSI6IHRydWUsDQogICAgICAgICJjYW5kaWRhdGVfYWxyZWFkeV9jb3VuY2lsbG9yIjogZmFsc2UsDQogICAgICAgICJjYW5kaWRhdGVfaXNfZ3Vlc3QiOiBmYWxzZSwNCiAgICAgICAgInBlbmRpbmdfY2hhcmFjdGVyX2ludGVyYWN0aW9uIjogZmFsc2UsDQogICAgICAgICJpbmN1bWJlbnRfZmlyZWFiaWxpdHlfZXZhbHVhdGVkIjogdHJ1ZSwNCiAgICAgICAgImluY3VtYmVudF9jYW5fYmVfZmlyZWQiOiB0cnVlDQogICAgICB9DQogICAgXSwNCiAgICAiY291bmNpbF9jb21wb3NpdGlvbl9jYW5kaWRhdGVzIjogew0KICAgICAgInNuYXBzaG90Ijogew0KICAgICAgICAic25hcHNob3RfaWQiOiAibmF0aXZlOjEiLA0KICAgICAgICAicHVibGljX3JldmlzaW9uIjogMSwNCiAgICAgICAgIm5hdGl2ZV9yZXZpc2lvbiI6IDEsDQogICAgICAgICJkYXRlX3JhdyI6IDI0MDAwLA0KICAgICAgICAicGF1c2VkIjogdHJ1ZQ0KICAgICAgfSwNCiAgICAgICJvd25lcl9jaGFyYWN0ZXJfaWQiOiAyOTgyOSwNCiAgICAgICJwb3NpdGlvbiI6IHsNCiAgICAgICAgInBvc2l0aW9uX2tleSI6ICJjb3VuY2lsbG9yX3N0ZXdhcmQiLA0KICAgICAgICAiaW5jdW1iZW50X2NoYXJhY3Rlcl9pZCI6IDE2Nzc3MjE4LA0KICAgICAgICAiaW5jdW1iZW50X21haW5fc2tpbGwiOiB7DQogICAgICAgICAgImtleSI6ICJzdGV3YXJkc2hpcCIsDQogICAgICAgICAgInZhbHVlIjogOQ0KICAgICAgICB9LA0KICAgICAgICAidmFjYW50IjogZmFsc2UsDQogICAgICAgICJhY3Rpb25fcm91dGUiOiAicmVwbGFjZSINCiAgICAgIH0sDQogICAgICAiY2FuZGlkYXRlX2NvbGxlY3Rpb25fY29tcGxldGUiOiB0cnVlLA0KICAgICAgImNhbmRpZGF0ZXMiOiBbDQogICAgICAgIHsNCiAgICAgICAgICAiY2hhcmFjdGVyX2lkIjogMTY3NzcyMzIsDQogICAgICAgICAgIm5hdGl2ZV9jb2xsZWN0aW9uX29yZGluYWwiOiAxLA0KICAgICAgICAgICJlbGlnaWJsZSI6IHRydWUsDQogICAgICAgICAgImVsaWdpYmlsaXR5X3JlYXNvbiI6ICJuYXRpdmVfY2FuZGlkYXRlX3Byb3ZpZGVyX2FjY2VwdGVkIiwNCiAgICAgICAgICAibWFpbl9za2lsbCI6IHsNCiAgICAgICAgICAgICJrZXkiOiAic3Rld2FyZHNoaXAiLA0KICAgICAgICAgICAgInZhbHVlIjogMjINCiAgICAgICAgICB9LA0KICAgICAgICAgICJhY3Rpb25fcm91dGUiOiAicmVwbGFjZSINCiAgICAgICAgfSwNCiAgICAgICAgew0KICAgICAgICAgICJjaGFyYWN0ZXJfaWQiOiAxNjc3NzIzMywNCiAgICAgICAgICAibmF0aXZlX2NvbGxlY3Rpb25fb3JkaW5hbCI6IDAsDQogICAgICAgICAgImVsaWdpYmxlIjogdHJ1ZSwNCiAgICAgICAgICAiZWxpZ2liaWxpdHlfcmVhc29uIjogIm5hdGl2ZV9jYW5kaWRhdGVfcHJvdmlkZXJfYWNjZXB0ZWQiLA0KICAgICAgICAgICJtYWluX3NraWxsIjogew0KICAgICAgICAgICAgImtleSI6ICJzdGV3YXJkc2hpcCIsDQogICAgICAgICAgICAidmFsdWUiOiAxNw0KICAgICAgICAgIH0sDQogICAgICAgICAgImFjdGlvbl9yb3V0ZSI6ICJyZXBsYWNlIg0KICAgICAgICB9DQogICAgICBdLA0KICAgICAgInJlYWRpbmVzcyI6IHsNCiAgICAgICAgImlkZW50aXR5X3JlYWR5IjogdHJ1ZSwNCiAgICAgICAgImNhbmRpZGF0ZV9jb2xsZWN0aW9uX3JlYWR5IjogdHJ1ZSwNCiAgICAgICAgImluY3VtYmVudF9yZWFkeSI6IHRydWUsDQogICAgICAgICJpbmN1bWJlbnRfbWFpbl9za2lsbF9yZWFkeSI6IHRydWUsDQogICAgICAgICJjYW5kaWRhdGVfbGVnYWxpdHlfcmVhZHkiOiB0cnVlLA0KICAgICAgICAibWFpbl9za2lsbF9yZWFkeSI6IHRydWUsDQogICAgICAgICJhY3Rpb25fcm91dGVfcmVhZHkiOiB0cnVlLA0KICAgICAgICAic2FtZV9mcmFtZV9yZWFkeSI6IHRydWUsDQogICAgICAgICJyZWFkeSI6IHRydWUNCiAgICAgIH0NCiAgICB9DQogIH0NCn0NCg==";
    private record Scene(PlanningRequest request, ActionCommand command, PlanningResult.ActionSelected proposal) { }

    private static IntegerValue num(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Obj snapshot() {
        return new Obj(Map.ofEntries(
                Map.entry("paused", new Bool(true)), Map.entry("map_ready", new Bool(true)),
                Map.entry("revision", num(1)), Map.entry("native_revision", num(1)), Map.entry("date_raw", num(24000)),
                Map.entry("snapshot_id", new Text("snapshot-1")), Map.entry("episode_run_id", new Text("episode-1")),
                Map.entry("played_character", new Obj(Map.of("character_id", num(29829), "alive", new Bool(true)))),
                Map.entry("active_wars", new Arr(List.of())), Map.entry("player_armies", new Arr(List.of())),
                Map.entry("diagnostics", new Obj(Map.of("connection_generation", num(1), "bridge_pid", num(123)))),
                Map.entry("unknown_fact", new Obj(Map.of("status", new Text("unavailable"), "value", Nil.INSTANCE))),
                Map.entry("unknown_null", Nil.INSTANCE),
                Map.entry("root_cache", new Obj(Map.of("snapshot_id", new Text("old-snapshot"), "revision", num(99))))));
    }
    private static PlanningRequest request(Obj snapshot, List<Obj> history, Set<OperationKey> steps,
            List<ProposalLifecycle.ExternalFact> facts) {
        var before = new ProposalLifecycle.ObservationIdentity("fixture-machine-1",
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(24000)),
                        "snapshot-1", BigInteger.ONE, "episode-1"), 1);
        return new PlanningRequest(before, new G2Source(before.machineId(), NOW.toString(), "fixture-build", EVIDENCE),
                "session-1", NOW.plusSeconds(60), new PlanningObservation(snapshot, history, steps, Set.of("z-cap", "a-cap"),
                Optional.empty(), facts, Optional.empty(), Optional.empty(), false));
    }
    private static ObjectNode query(boolean occupied) {
        ObjectNode q = (ObjectNode) FullJsonTree.parse(Base64.getDecoder().decode(QUERY), 1_048_576);
        ObjectNode payload = (ObjectNode) q.get("council_composition_candidates");
        if (!occupied) {
            ObjectNode seat = (ObjectNode) payload.get("position");
            seat.putNull("incumbent_character_id"); seat.putNull("incumbent_main_skill"); seat.put("vacant", true);
            seat.put("action_route", "assign");
            payload.get("candidates").forEach(row -> ((ObjectNode) row).put("action_route", "assign"));
        }
        ((ObjectNode) q.get("council_final_gates")).set("council_composition_candidates", payload.deepCopy());
        return q;
    }
    private static Obj args(ObjectNode query, boolean occupied, int candidate) {
        return new Obj(Map.of("position_key", new Text("councillor_steward"), "candidate_character_id", num(candidate),
                "original_query", parse(FullJsonTree.encode(query, 1_048_576)), "expected_has_incumbent", new Bool(occupied),
                "expected_incumbent_character_id", num(occupied ? 16777218 : -1)));
    }
    private static Scene scene(PlanningRequest req, Obj args, OperationKey operation) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, req.before(), req.source(),
                "xar.java.governance-independent-effect/v1", List.of(
                new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("council.position_key"), "councillor_steward"),
                new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("council.incumbent_character_id"), BigInteger.valueOf(16777232)),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true)));
        var command = new ActionCommand("council-software-action", req.before(), req.source(), req.sessionId(), operation,
                args, expected, CLAIMS, req.deadline());
        var draft = new OrdinaryPolicy.Draft("java-ordinary-governance-v1", "council_private_typed_submit", "software admission scene",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.WORLD_ACTION, Optional.of(Domain.council), new Obj(Map.of()));
        return new Scene(req, command, new PlanningResult.ActionSelected(command, new PlanTrace(req.before(), List.of(), Optional.of(draft))));
    }
    private static Scene scene(boolean occupied) {
        return scene(request(snapshot(), List.of(), Set.of(PRIVATE, new OperationKey("z-op")), List.of()), args(query(occupied), occupied, 16777232), PRIVATE);
    }
    private static Optional<ObjectNode> project(Scene s) {
        return RootCouncilDecisionProjection.project(s.request(), s.proposal(), ActionCodec.bodySha256(s.command()));
    }
    private static ProposalLifecycle.ExternalFact fact(PlanningRequest req, boolean unresolved) {
        return new ProposalLifecycle.ExternalFact("previous-action", "b".repeat(64), req.before(),
                unresolved ? ProposalLifecycle.ExternalState.UNKNOWN : ProposalLifecycle.ExternalState.SEND_CONFIRMED,
                ProposalLifecycle.UnknownScope.DOMAIN, Domain.council, CLAIMS, EVIDENCE);
    }

    @Test void completeCommandSnapshotRegistriesAndFactsRemainDetached() {
        Scene original = scene(true);
        PlanningRequest req = request(snapshot(), List.of(), original.request().observations().actionSteps(), List.of(fact(original.request(), false)));
        Scene s = scene(req, original.command().arguments(), PRIVATE);
        byte[] command = ActionCodec.encodeCommand(s.command()), state = OpportunityJson.encode(req.observations().snapshot());
        String hash = ActionCodec.bodySha256(s.command());
        ObjectNode data = project(s).orElseThrow();
        assertEquals(FullJsonTree.parse(command, ActionCodec.MAX_COMMAND_BYTES), data.get("proposal"));
        assertEquals(OpportunityJson.toNode(req.observations().snapshot()), data.get("snapshot"));
        assertEquals(hash, data.get("body_sha256").textValue());
        assertEquals(s.command().actionId(), data.get("proposal_id").textValue());
        assertEquals(List.of("a-cap", "z-cap"), java.util.stream.StreamSupport.stream(data.get("capabilities").spliterator(), false).map(JsonNode::textValue).toList());
        assertEquals(List.of(PRIVATE.value(), "z-op"), java.util.stream.StreamSupport.stream(data.get("routable_operations").spliterator(), false).map(JsonNode::textValue).toList());
        JsonNode held = data.get("action_facts").get(0);
        assertEquals("previous-action", held.get("action_id").textValue());
        assertEquals("b".repeat(64), held.get("body_sha256").textValue());
        assertEquals("SEND_CONFIRMED", held.get("state").textValue()); assertFalse(held.get("unresolved").booleanValue());
        assertEquals("DOMAIN", held.get("scope").textValue()); assertEquals("council", held.get("domain").textValue());
        assertEquals(ActionCodec.claims(CLAIMS), held.get("affected_claims"));
        assertFalse(data.has("history")); assertFalse(data.has("root_facts"));
        assertTrue(RootCouncilDecisionProjection.POLICY.contains("NOT lossless"));
        ((ObjectNode) data.get("snapshot")).removeAll(); ((ObjectNode) data.get("proposal")).removeAll();
        assertArrayEquals(command, ActionCodec.encodeCommand(s.command()));
        assertArrayEquals(state, OpportunityJson.encode(req.observations().snapshot()));
        assertEquals(hash, ActionCodec.bodySha256(s.command()));
    }

    @Test void bothAssignmentRoutesAndOnlyExactDuplicateHistoryProject() {
        for (boolean occupied : List.of(true, false)) {
            Scene base = scene(occupied);
            assertTrue(project(base).isPresent());
            assertFalse(project(base).orElseThrow().has("duplicate_snapshot_history_omitted"));
            Obj row = new Obj(Map.of("read", new Text("held-row"), "unknown", Nil.INSTANCE));
            for (boolean same : List.of(true, false)) {
                Obj retained = same ? row : row.with("read", new Text("different-held-row"));
                Obj snapshot = base.request().observations().snapshot().with("native_command_history", new Arr(List.of(retained)));
                var req = request(snapshot, List.of(row), base.request().observations().actionSteps(), List.of());
                Scene s = scene(req, base.command().arguments(), PRIVATE);
                ObjectNode data = project(s).orElseThrow();
                if (same) {
                    assertFalse(data.get("snapshot").has("native_command_history"));
                    assertTrue(data.get("duplicate_snapshot_history_omitted").booleanValue());
                } else {
                    assertEquals(OpportunityJson.toNode(new Arr(List.of(retained))), data.get("snapshot").get("native_command_history"));
                    assertFalse(data.has("duplicate_snapshot_history_omitted"));
                }
                assertEquals(OpportunityJson.toNode(snapshot), OpportunityJson.toNode(req.observations().snapshot()));
            }
        }
    }

    @Test void unsupportedOrChangedProposalFallsBackWithoutInventingAuthority() {
        Scene base = scene(true);
        assertTrue(RootCouncilDecisionProjection.project(base.request(), base.proposal(), "0".repeat(64)).isEmpty());
        for (Obj snapshot : List.of(snapshot().with("paused", new Bool(false)), snapshot().with("map_ready", new Bool(false)),
                snapshot().with("active_event", new Obj(Map.of("status", new Text("present")))))) {
            Scene s = scene(request(snapshot, List.of(), Set.of(PRIVATE), List.of()), base.command().arguments(), PRIVATE);
            assertTrue(project(s).isEmpty());
        }
        assertTrue(project(scene(request(snapshot(), List.of(), Set.of(), List.of()), base.command().arguments(), PRIVATE)).isEmpty());
        assertTrue(project(scene(request(snapshot(), List.of(), Set.of(PRIVATE), List.of(fact(base.request(), true))), base.command().arguments(), PRIVATE)).isEmpty());
        assertTrue(project(scene(base.request(), base.command().arguments(), new OperationKey("other-operation"))).isEmpty());
        ObjectNode badGate = query(true);
        ((ObjectNode) badGate.get("council_final_gates").get("rows").get(0)).put("final_gate_available", false);
        assertTrue(project(scene(base.request(), args(badGate, true, 16777232), PRIVATE)).isEmpty());
        ObjectNode badFrame = query(true); ((ObjectNode) badFrame.get("source_frame")).put("revision", 2);
        assertTrue(project(scene(base.request(), args(badFrame, true, 16777232), PRIVATE)).isEmpty());
        assertTrue(project(scene(base.request(), args(query(true), true, 16777233), PRIVATE)).isEmpty(), "legal lower-skill alternate is outside this deterministic projection");
        Obj callerMismatch = base.command().arguments().with("public_submission_schema", new Text("xar.java.public-council-assignment/v1"))
                .with("caller_request_id", new Text("different-caller-token"));
        assertTrue(project(scene(base.request(), callerMismatch, PRIVATE)).isEmpty());
        var current = new PlanningRequest(base.request().before(), new G2Source(base.request().before().machineId(), NOW.toString(), "other-build", EVIDENCE),
                base.request().sessionId(), base.request().deadline(), base.request().observations());
        assertTrue(RootCouncilDecisionProjection.project(current, base.proposal(), ActionCodec.bodySha256(base.command())).isEmpty());
    }

    @Test void actualSelectorUsesLargeCouncilProjectionAndUnchangedGenericFallback(@TempDir Path root) throws Exception {
        try (MockModel model = new MockModel()) {
            var provider = new RootOrdinaryRuntimeConfiguration.DecisionProvider(model.uri(), "software-model", Duration.ofSeconds(5), 1, Duration.ZERO);
            var selector = new RootOnlineDecisionSelector(provider, Clock.fixed(NOW, ZoneOffset.UTC), raw -> {
                byte[] bytes = raw.bytes(); Path p = root.resolve(java.util.UUID.randomUUID() + ".json");
                Files.write(p, bytes); return new ExactRef(p.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes));
            });
            Scene base = scene(true); Obj row = new Obj(Map.of("history", new Text("retained-complete-row")));
            Obj snapshot = snapshot().with("unknown_padding", new Text("x".repeat(70000)));
            Scene selected = scene(request(snapshot, List.of(row), Set.of(PRIVATE), List.of()), base.command().arguments(), PRIVATE);
            byte[] command = ActionCodec.encodeCommand(selected.command());
            var accepted = selector.select(selected.request(), selected.proposal());
            assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, accepted.choice(), accepted.reason()); assertTrue(accepted.evidence().isPresent());
            JsonNode payload = model.request.get(); JsonNode data = FullJsonTree.parse(payload.get("messages").get(1).get("content").textValue().getBytes(StandardCharsets.UTF_8), 1_048_576);
            assertEquals("private_council_assignment_admission/v1", data.get("decision_scope").textValue());
            assertEquals(70000, data.get("snapshot").get("unknown_padding").textValue().length());
            assertFalse(data.has("history")); assertTrue(payload.get("messages").get(0).get("content").textValue().contains("NOT lossless"));
            assertEquals(FullJsonTree.parse(command, 1_048_576), data.get("proposal"));
            assertArrayEquals(command, ActionCodec.encodeCommand(selected.command())); assertEquals(1, model.calls.get());
            Scene fallback = scene(request(snapshot, List.of(row), Set.of(), List.of()), base.command().arguments(), PRIVATE);
            var generic = selector.select(fallback.request(), fallback.proposal());
            assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT, generic.choice(), "projection unsupported keeps generic selection, not manufactured WAIT");
            JsonNode full = FullJsonTree.parse(model.request.get().get("messages").get(1).get("content").textValue().getBytes(StandardCharsets.UTF_8), 1_048_576);
            assertFalse(full.has("decision_scope")); assertEquals(1, full.get("history").size());
            assertEquals(OpportunityJson.toNode(row), full.get("history").get(0));
            assertEquals(FullJsonTree.parse(ActionCodec.encodeCommand(fallback.command()), 1_048_576), full.get("proposal"));
            model.choice.set("WAIT");
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT, selector.select(selected.request(), selected.proposal()).choice());
            assertEquals(3, model.calls.get());
        }
    }

    private static final class MockModel implements AutoCloseable {
        final HttpServer server;
        final ExecutorService executor = Executors.newSingleThreadExecutor();
        final AtomicInteger calls = new AtomicInteger();
        final AtomicReference<ObjectNode> request = new AtomicReference<>();
        final AtomicReference<String> choice = new AtomicReference<>("SELECT_PROPOSAL");
        MockModel() throws Exception {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.setExecutor(executor);
            server.createContext("/v1/chat/completions", exchange -> {
                try (exchange) {
                    ObjectNode payload = (ObjectNode) FullJsonTree.parse(exchange.getRequestBody().readNBytes(1_048_577), 1_048_576);
                    request.set(payload); calls.incrementAndGet();
                    JsonNode data = FullJsonTree.parse(payload.get("messages").get(1).get("content").textValue().getBytes(StandardCharsets.UTF_8), 1_048_576);
                    ObjectNode inner = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
                    inner.put("decision", choice.get()); inner.put("proposal_id", data.get("proposal_id").textValue());
                    inner.put("body_sha256", data.get("body_sha256").textValue()); inner.put("reason", "software admission");
                    ObjectNode chunk = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
                    ObjectNode value = chunk.putArray("choices").addObject(); value.putObject("delta").put("content", inner.toString()); value.put("finish_reason", "stop");
                    byte[] response = ("data: " + chunk + "\n\ndata: [DONE]\n\n").getBytes(StandardCharsets.UTF_8);
                    exchange.getResponseHeaders().set("Content-Type", "text/event-stream"); exchange.sendResponseHeaders(200, response.length);
                    exchange.getResponseBody().write(response);
                }
            });
            server.start();
        }
        URI uri() { return URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/v1"); }
        @Override public void close() { server.stop(0); executor.shutdownNow(); }
    }
}
