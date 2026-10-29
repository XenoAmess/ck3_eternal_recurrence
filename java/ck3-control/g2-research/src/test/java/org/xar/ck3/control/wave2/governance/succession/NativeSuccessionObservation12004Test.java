package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativeSuccessionObservation12004.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;
import org.xar.ck3.control.wave2.governance.succession.NativeSuccessionObservation12004.Frame;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.m7.GoalCodec;

/** Synthetic source-owner doubles only; no death, native query, replay or campaign completion. */
final class NativeSuccessionObservation12004Test {
    private static final String MACHINE = "unit-machine";
    private static final String SHA = "a".repeat(64);
    private static final SuccessionLifecycleBinding LIFE = new SuccessionLifecycleBinding(
            SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE,
            "absent_by_verified_xar_mod_not_loaded", SHA);

    @Test void existingProducerFreezesAllTitlesAndReportRoundTrips() {
        Frozen frozen = (Frozen) freeze(frame(1, "before", 1, false, 1, 0, null));
        assertEquals(2, frozen.expectation().titleExpectations().size());
        assertEquals(RiskState.SPLIT_SUCCESSORS, frozen.expectation().riskState());
        byte[] bytes = encode(report(frozen));
        assertArrayEquals(bytes, encode(decodeReport(bytes)));
        JsonNode node = StrictJson.parse(bytes, MAX_REPORT_BYTES);
        assertFalse(node.get("natural_death_proven").booleanValue());
        assertTrue(node.get("expectation_base64").isTextual());
        assertEquals("133000000000000000", node.path("sources").get(0).path("session").path("creation_filetime").textValue());
    }
    @Test void actualSuccessorEstateAndAdditionalTitleRemainDistinct() {
        Transition value = transition();
        assertEquals(Verdict.MATCHED, value.reconciliation().verdict());
        assertEquals(List.of(10), value.reconciliation().matchedInheritedTitleIds());
        assertEquals(List.of(11), value.reconciliation().expectedOtherHeirTitleIds());
        assertEquals(List.of(99), value.reconciliation().observedAdditionalSuccessorTitleIds());
        assertArrayEquals(encode(report(value)), encode(decodeReport(encode(report(value)))));
    }
    @Test void observedNewEpisodeMustRetainOriginalGoal() {
        Transition value = transition();
        Goal old = value.retained().predecessor().goal();
        ProjectionJson last = projection(last(value.reconciliation()));
        Frame current = frame(2, "after", 2, false, 3, 1, last);
        Continued continued = (Continued) observeContinued(value, current);
        assertEquals(old.campaignId(), continued.current().goal().campaignId());
        assertArrayEquals(encode(report(continued)), encode(decodeReport(encode(report(continued)))));
    }
    @Test void changedBirthNeverLooksLikeSameGame() {
        Transition value = transition(); Frame current = frame(2, "after", 2, false, 3, 1, projection(last(value.reconciliation())));
        Session s = current.proof().session();
        Session other = new Session(s.machineId(), s.sessionId(), new GameIdentity(s.game().pid(), "133000000000000001"),
                s.episodeRunId(), s.connectionGeneration(), s.executable(), s.executableFileId(), s.executableMtimeNs());
        Frame changed = new Frame(new Proof(other, current.proof().source(), current.proof().rootResultRef(), current.proof().turnBundleRef()),
                current.snapshot(), current.bundle(), current.lifecycle(), current.goal(), current.government());
        assertEquals(Reason.GAME_IDENTITY_CHANGED, ((Unavailable) observeContinued(value, changed)).reason());
    }
    @Test void oldEpisodeIsNotAlreadyContinued() {
        Transition value = transition();
        assertEquals(Reason.SUCCESSOR_EPISODE_UNOBSERVED, ((Unavailable) observeContinued(value, value.successor())).reason());
    }
    @Test void noGoalCannotBeInvented() {
        Transition value = transition(); Frame current = frame(2, "after", 2, false, 3, 1, projection(last(value.reconciliation())));
        Frame missing = new Frame(current.proof(), current.snapshot(), current.bundle(), current.lifecycle(), null, current.government());
        assertEquals(Reason.GOAL_CONTINUITY_UNOBSERVED, ((Unavailable) observeContinued(value, missing)).reason());
    }
    @Test void changingGoalOriginOrSkippingProgressIsRejected() {
        Transition value = transition(); Frame current = frame(2, "after", 2, false, 3, 2, projection(last(value.reconciliation())));
        assertEquals(Reason.GOAL_CONTINUITY_MISMATCH, ((Unavailable) observeContinued(value, current)).reason());
        Goal changed = new Goal("other-campaign", "dynasty_continuity", 1, 2, BigInteger.ONE, current.goal().lastSuccession());
        Frame other = new Frame(current.proof(), current.snapshot(), current.bundle(), current.lifecycle(), changed, current.government());
        assertEquals(Reason.GOAL_CONTINUITY_MISMATCH, ((Unavailable) observeContinued(value, other)).reason());
    }
    @Test void unknownLifecycleDoesNotBecomeOrdinary() {
        Frame current = frame(1, "before", 1, false, 1, 0, null);
        Frame unknown = new Frame(current.proof(), current.snapshot(), current.bundle(), SuccessionLifecycleBinding.unknown(), current.goal(), current.government());
        assertEquals(Reason.LIFECYCLE_UNSUPPORTED, ((Unavailable) freeze(unknown)).reason());
    }
    @Test void sourceFrameRegressionIsRejected() {
        Frozen frozen = (Frozen) freeze(frame(1, "before", 1, false, 10, 0, null));
        assertEquals(Reason.FRAME_REGRESSED, ((Unavailable) reconcile(frozen, frame(2, "before", 1, true, 2, 0, null))).reason());
    }
    @Test void authorityOrDeathProofCannotBeAddedToReport() {
        ObjectNode value = (ObjectNode) StrictJson.parse(encode(report(transition())), MAX_REPORT_BYTES);
        for (String field : List.of("submission_authorized", "natural_death_proven", "realm_preservation_proven")) {
            value.put(field, true); byte[] raw = StrictJson.canonical(value, MAX_REPORT_BYTES);
            assertThrows(IllegalArgumentException.class, () -> decodeReport(raw)); value.put(field, false);
        }
    }
    @Test void reportRejectsFloatAndNoncanonicalDecimalIdentities() {
        ObjectNode value = (ObjectNode) StrictJson.parse(encode(report(transition())), MAX_REPORT_BYTES);
        ObjectNode session = (ObjectNode) value.path("sources").get(0).get("session");
        session.put("pid_decimal", "04242");
        assertThrows(IllegalArgumentException.class, () -> decodeReport(StrictJson.canonical(value, MAX_REPORT_BYTES)));
        session.put("pid_decimal", "4242"); session.put("creation_filetime", 133000000000000000L);
        assertThrows(IllegalArgumentException.class, () -> decodeReport(StrictJson.canonical(value, MAX_REPORT_BYTES)));
    }
    @Test void retainedRootReaderConsumesRealByteShapeAndCompletePartition() throws IOException {
        MemoryRoot root = new MemoryRoot();
        NativeSuccessionSource12004.Result result = NativeSuccessionSource12004.read(root, root.limits, root.request);
        Frame observed = ((NativeSuccessionSource12004.Observed) result).frame();
        assertEquals(2, ((Frozen) freeze(observed)).expectation().titleExpectations().size());
        assertEquals(0, root.nativeCalls);
    }
    @Test void sourceBytesAndRootPartitionDriftAreRejected() throws IOException {
        MemoryRoot root = new MemoryRoot(); root.bytes.put(root.request.rootResult(), "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertInstanceOf(NativeSuccessionSource12004.Rejected.class, NativeSuccessionSource12004.read(root, root.limits, root.request));
    }
    @Test void absentRootProviderRemainsUnavailable() {
        MemoryRoot root = new MemoryRoot(false);
        assertEquals(Reason.ROOT_SOURCE_UNAVAILABLE,
                ((NativeSuccessionSource12004.Rejected) NativeSuccessionSource12004.read(root, root.limits, root.request)).reason());
    }

    @Test void signedActorIdsPreservedThroughGoalAndReport() {
        int[][] roles = {{2, 0}, {2, -2}, {2, Integer.MIN_VALUE}, {2, Integer.MAX_VALUE},
                {0, 3}, {-2, 3}, {Integer.MIN_VALUE, 3}};
        for (int[] role : roles) {
            var initial = OrdinaryCampaignGoal.newGoal("campaign", role[0]);
            var matched = new OrdinaryCampaignGoal.Reconciliation(OrdinaryCampaignGoal.Verdict.MATCHED,
                    role[0], role[1], List.of(10L), List.of(11L), List.of());
            var advanced = OrdinaryCampaignGoal.continueGoal(initial, matched);
            byte[] producerBytes = GoalCodec.encodeGoal(advanced);
            JsonNode producer = StrictJson.parse(producerBytes);
            Goal observed = goal(producer);
            assertEquals(role[0], observed.originCharacterId());
            assertEquals(role[1], observed.currentCharacterId());
            assertEquals(BigInteger.ONE, observed.reconciledSuccessions());
            assertNotNull(observed.lastSuccession());
            assertArrayEquals(StrictJson.canonical(producer.path("progress").path("last_succession")),
                    observed.lastSuccession().bytes());

            byte[] reportBytes = encode(reportWithGoal(observed));
            Report decoded = decodeReport(reportBytes);
            assertEquals(role[0], decoded.goal().originCharacterId());
            assertEquals(role[1], decoded.goal().currentCharacterId());
            assertEquals(BigInteger.ONE, decoded.goal().reconciledSuccessions());
            assertArrayEquals(observed.lastSuccession().bytes(), decoded.goal().lastSuccession().bytes());
            assertArrayEquals(reportBytes, encode(decoded));
            JsonNode wire = StrictJson.parse(reportBytes);
            for (String field : List.of("native_queries", "game_commands", "ledger_writes")) {
                assertEquals(0L, wire.get(field).longValue());
            }
            for (String field : List.of("submission_authorized", "natural_death_proven", "realm_preservation_proven")) {
                assertTrue(wire.get(field).isBoolean());
                assertFalse(wire.get(field).booleanValue());
            }
        }
    }

    @Test void invalidActorIdsRejectedInGoalAndReport() {
        assertThrows(IllegalArgumentException.class,
                () -> new Goal("campaign", "dynasty_continuity", -1, 2, BigInteger.ZERO, null));
        assertThrows(IllegalArgumentException.class,
                () -> new Goal("campaign", "dynasty_continuity", 2, -1, BigInteger.ZERO, null));
        ObjectNode producer = (ObjectNode) StrictJson.parse(
                GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("campaign", 2)));
        ObjectNode reportWire = (ObjectNode) StrictJson.parse(encode(reportWithGoal(goal(producer))));
        List<String> invalidTokens = List.of("-1", "-2147483649", "2147483648", "4294967294",
                "true", "false", "-2.0", "-2e0", "\"-2\"", "null");
        for (String field : List.of("origin_character_id", "current_character_id")) {
            for (String token : invalidTokens) {
                JsonNode wrong = StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                ObjectNode wrongGoal = producer.deepCopy(); wrongGoal.set(field, wrong);
                assertThrows(IllegalArgumentException.class, () -> goal(wrongGoal), field + ":" + token);
                ObjectNode wrongReport = reportWire.deepCopy();
                ((ObjectNode) wrongReport.get("goal")).set(field, wrong);
                assertThrows(IllegalArgumentException.class,
                        () -> decodeReport(StrictJson.canonical(wrongReport, MAX_REPORT_BYTES)), field + ":" + token);
            }
            ObjectNode missingGoal = producer.deepCopy(); missingGoal.remove(field);
            assertThrows(IllegalArgumentException.class, () -> goal(missingGoal));
            ObjectNode missingReport = reportWire.deepCopy(); ((ObjectNode) missingReport.get("goal")).remove(field);
            assertThrows(IllegalArgumentException.class,
                    () -> decodeReport(StrictJson.canonical(missingReport, MAX_REPORT_BYTES)));
        }
    }

    @Test void goalCountAndTitleDomainsRemainUnchanged() {
        Goal maximum = new Goal("campaign", "dynasty_continuity", Integer.MAX_VALUE, Integer.MAX_VALUE,
                StrictJson.UINT64_MAX, null);
        byte[] encoded = encode(reportWithGoal(maximum));
        assertEquals(StrictJson.UINT64_MAX, decodeReport(encoded).goal().reconciledSuccessions());
        assertArrayEquals(encoded, encode(decodeReport(encoded)));
        assertThrows(IllegalArgumentException.class,
                () -> new Goal("campaign", "dynasty_continuity", 2, 2, BigInteger.valueOf(-1), null));
        assertThrows(IllegalArgumentException.class,
                () -> new Goal("campaign", "dynasty_continuity", 2, 2, StrictJson.UINT64_MAX.add(BigInteger.ONE), null));
        ObjectNode goalWire = (ObjectNode) StrictJson.parse(
                GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("campaign", 2)));
        ((ObjectNode) goalWire.get("progress")).put("reconciled_successions", StrictJson.UINT64_MAX);
        assertEquals(StrictJson.UINT64_MAX, goal(goalWire).reconciledSuccessions());
        ((ObjectNode) goalWire.get("progress")).put("reconciled_successions", StrictJson.UINT64_MAX.add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> goal(goalWire));
        for (String count : List.of("01", "-1", StrictJson.UINT64_MAX.add(BigInteger.ONE).toString())) {
            ObjectNode malformed = (ObjectNode) StrictJson.parse(encoded);
            ((ObjectNode) malformed.get("goal")).put("reconciled_successions_decimal", count);
            assertThrows(IllegalArgumentException.class,
                    () -> decodeReport(StrictJson.canonical(malformed, MAX_REPORT_BYTES)));
        }
        for (long title : new long[]{0L, -2L}) {
            assertThrows(IllegalArgumentException.class,
                    () -> new OrdinaryCampaignGoal.Reconciliation(OrdinaryCampaignGoal.Verdict.MATCHED,
                            2, 3, List.of(title), List.of(), List.of()));
        }
    }

    @Test void actualRootSourcePreservesProducedGoalThroughObservationReport() throws Exception {
        int[][] roles = {{2, 0}, {2, -2}, {2, Integer.MIN_VALUE}, {2, Integer.MAX_VALUE},
                {0, 3}, {-2, 3}, {Integer.MIN_VALUE, 3}};
        for (int[] role : roles) {
            var initial = OrdinaryCampaignGoal.newGoal("source-campaign", role[0]);
            var matched = new OrdinaryCampaignGoal.Reconciliation(OrdinaryCampaignGoal.Verdict.MATCHED,
                    role[0], role[1], List.of(10L), List.of(11L), List.of());
            var advanced = OrdinaryCampaignGoal.continueGoal(initial, matched);
            JsonNode producer = StrictJson.parse(GoalCodec.encodeGoal(advanced));
            Frame actual = NativeSuccessionSourceCharacterIdTest.sourceProducedFrame(role[1], role[0], producer);
            assertEquals(role[1], actual.snapshot().actor().characterId());
            assertEquals(role[0], actual.bundle().primaryHeirCharacterId());
            assertNotNull(actual.goal());
            assertEquals(role[0], actual.goal().originCharacterId());
            assertEquals(role[1], actual.goal().currentCharacterId());
            Frozen retained = assertInstanceOf(Frozen.class, freeze(actual));
            byte[] bytes = encode(report(retained));
            Report restored = decodeReport(bytes);
            assertEquals(actual.proof(), restored.sources().getFirst());
            assertEquals(role[0], restored.goal().originCharacterId());
            assertEquals(role[1], restored.goal().currentCharacterId());
            assertEquals(BigInteger.ONE, restored.goal().reconciledSuccessions());
            assertArrayEquals(StrictJson.canonical(producer.path("progress").path("last_succession")),
                    restored.goal().lastSuccession().bytes());
            assertArrayEquals(bytes, encode(restored));
            JsonNode wire = StrictJson.parse(bytes);
            for (String field : List.of("native_queries", "game_commands", "ledger_writes")) {
                assertEquals(0L, wire.get(field).longValue());
            }
            for (String field : List.of("submission_authorized", "natural_death_proven", "realm_preservation_proven")) {
                assertFalse(wire.get(field).booleanValue());
            }
        }
    }

    private static Report reportWithGoal(Goal value) {
        Report original = report((Frozen) freeze(frame(1, "before", 1, false, 1, 0, null)));
        return new Report(original.state(), original.unavailableReason(), original.sources(), original.expectation(),
                original.reconciliation(), value, original.government());
    }

    private static Transition transition() {
        Frozen frozen = (Frozen) freeze(frame(1, "before", 1, false, 1, 0, null));
        return (Transition) reconcile(frozen, frame(2, "before", 1, true, 2, 0, null));
    }
    private static Frame frame(int actor, String episode, int episodeActor, boolean terminal, int revision, int count, ProjectionJson last) {
        SuccessionModel.Frame binding = new SuccessionModel.Frame("native:" + revision, BigInteger.valueOf(revision), BigInteger.valueOf(revision), 100 + revision);
        List<TitleRow> rows = actor == 1 ? List.of(row(10, 2, true), row(11, 3, false)) : List.of(row(10, 4, true), row(99, 4, false));
        Snapshot snapshot = new Snapshot(binding, episode, episodeActor, true, true, terminal,
                terminal ? "played_character_changed" : null, new Actor(actor, true), false, false, Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION);
        TurnBundle bundle = new TurnBundle(binding, new Actor(actor, true), rows, actor == 1 ? 2 : 4,
                actor == 1 ? RiskState.SPLIT_SUCCESSORS : RiskState.SINGLE_SUCCESSOR);
        Session session = session(episode);
        Proof proof = new Proof(session, new G2Source(MACHINE, "2026-10-23T00:01:00Z", "1.20.0.4@sha256:" + EXECUTABLE_SHA256,
                ref("owner-" + revision)), ref("root-" + revision), ref("bundle-" + revision));
        return new Frame(proof, snapshot, bundle, LIFE, new Goal("campaign", "dynasty_continuity", 1, actor,
                BigInteger.valueOf(count), last), projection(StrictJson.object().put("key", "feudal_government")));
    }
    private static TitleRow row(int title, int heir, boolean primary) {
        ObjectNode metadata = StrictJson.object().put("title_id", title).put("tier_raw", 3);
        return new TitleRow(new Title(title, BigInteger.valueOf(3), new WireObject(StrictJson.canonical(metadata))), heir, primary);
    }
    private static ExactRef ref(String name) { return new ExactRef("C:/unit/" + name + ".json", 1, SHA); }
    private static Session session(String episode) {
        return new Session(MACHINE, "same-root-session", new GameIdentity(4242, "133000000000000000"), episode, "1",
                new ExactRef("C:/unit/ck3.exe", 1, EXECUTABLE_SHA256), "340282366920938463463374607431768211000", "133000000000000000");
    }
    private static ProjectionJson projection(JsonNode node) { return ProjectionJson.object(StrictJson.canonical(node, MAX_REPORT_BYTES), MAX_REPORT_BYTES); }
    private static ObjectNode last(Reconciliation result) {
        JsonNode wire = StrictJson.parse(SuccessionCodec.encodeReconciliation(result), SuccessionCodec.MAX_BYTES);
        ObjectNode out = StrictJson.object();
        for (String key : List.of("predecessor_character_id", "actual_successor_character_id", "matched_inherited_title_ids",
                "expected_other_heir_title_ids", "expected_without_heir_title_ids")) { out.set(key, wire.get(key)); }
        return out;
    }
    private static final class MemoryRoot implements RootOwnedSources {
        private final Map<ExactRef, byte[]> bytes = new HashMap<>();
        private final Session session = session("before");
        private final G2RetainedNativeSourceProvider.Limits limits = new G2RetainedNativeSourceProvider.Limits(1048576, 131072);
        private final NativeSuccessionSource12004.Request request;
        private final RetainedArtifact artifact;
        private int nativeCalls;
        private final boolean available;
        MemoryRoot() throws IOException { this(true); }
        MemoryRoot(boolean available) {
            this.available = available;
            Frame frame = frame(1, "before", 1, false, 1, 0, null);
            ObjectNode snapshot = StrictJson.object().put("snapshot_id", "native:1").put("revision", 1).put("native_revision", 1)
                    .put("date_raw", 101).put("episode_run_id", "before").put("episode_character_id", 1)
                    .put("paused", true).put("map_ready", true).put("one_life_terminal", false).put("backend_id", "native-headless");
            snapshot.putNull("one_life_terminal_reason").putNull("active_event").putNull("pending_character_interaction");
            snapshot.putObject("played_character").put("character_id", 1).put("alive", true);
            snapshot.set("succession_lifecycle", StrictJson.parse(SuccessionLifecycleCodec.encode(LIFE), 16384));
            ObjectNode diagnostics = snapshot.putObject("diagnostics").put("bridge_pid", 4242).put("connection_generation", 1);
            diagnostics.putObject("hello").put("pid", 4242).put("connection_generation", 1).put("ck3_build_match", true)
                    .put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", EXECUTABLE_SHA256);
            ObjectNode binding = StrictJson.object().put("snapshot_id", "native:1").put("revision", 1).put("native_revision", 1).put("date_raw", 101);
            ObjectNode bundle = StrictJson.object().put("schema", "xar.ck3.turn-bundle/v1").put("status", "partial");
            bundle.set("binding", binding);
            ObjectNode ruler = bundle.putObject("ruler_state").put("status", "available").putObject("value").put("character_id", 1).put("alive", true);
            ObjectNode government = StrictJson.object().put("key", "feudal_government");
            ruler.putObject("government").put("status", "available").set("value", government);
            ObjectNode succession = bundle.putObject("succession_state").put("status", "available").putObject("value");
            succession.putObject("primary_title_heir_character_id").put("status", "available").put("value", 2);
            ObjectNode partition = succession.putObject("partition").put("status", "available").putObject("value").put("risk_state", "split_successors");
            var titleRows = partition.putArray("title_heirs");
            for (TitleRow row : frame.bundle().titleRows()) {
                ObjectNode wire = titleRows.addObject().put("first_heir_character_id", row.firstHeirCharacterId()).put("primary", row.primary());
                wire.set("title", StrictJson.parse(row.title().original().bytes()));
            }
            bundle.putObject("source").put("capability", "game.command.query-campaign-root-context-v1").put("query_sequence", 1).put("backend_id", "native-headless");
            ObjectNode rootResult = StrictJson.object().put("status", "available").put("query_sequence", 1); rootResult.set("binding", binding);
            ObjectNode root = rootResult.putObject("campaign_root_context").put("status", "available").put("snapshot_revision", 1)
                    .put("date_raw", 101).put("player_character_id", 1).put("player_character_alive", true);
            root.set("held_title_partition", titleRows); root.putArray("primary_title_succession_character_ids").add(2);
            root.set("government", government); root.putObject("readiness").put("held_title_partition_ready", true);
            request = new NativeSuccessionSource12004.Request(store("root", rootResult), store("bundle", bundle));
            ObjectNode result = StrictJson.object().put("is_error", false).put("result_type", "complete");
            result.putObject("meta"); result.putArray("content"); result.set("structured_content", snapshot);
            ObjectNode owner = StrictJson.object().put("started_at_utc", "2026-10-23T00:00:59Z")
                    .put("ended_at_utc", "2026-10-23T00:01:00Z").put("elapsed_seconds", 1)
                    .put("mcp_result_projection_json_utf8_bytes", StrictJson.canonical(result).length);
            owner.putObject("request").put("sequence", 1).put("tool", "unit-snapshot").putObject("arguments");
            owner.set("result", result);
            ObjectNode measurement = StrictJson.object().put("schema", "xar.resume56-current-game-files-readonly-observation/v1")
                    .put("machine_id", MACHINE).put("observed_at_utc", "2026-10-23T00:00:00Z");
            var observations = measurement.putArray("observations");
            observations.addObject().put("label", "game_exe").put("stable_during_read", true).put("path", session.executable().path())
                    .put("bytes", 1).put("sha256", EXECUTABLE_SHA256).put("file_id_decimal", session.executableFileId()).put("mtime_ns_decimal", session.executableMtimeNs());
            observations.addObject().put("label", "launcher_settings").put("stable_during_read", true).put("raw_version", "1.20.0.4");
            artifact = new RetainedArtifact(session, store("owner", owner), store("measurement", measurement), "unit-snapshot");
        }
        private ExactRef store(String name, JsonNode node) {
            byte[] body = StrictJson.canonical(node, 1048576);
            ExactRef reference = new ExactRef("C:/unit/" + name + ".json", body.length, G2RetainedNativeSourceProvider.sha256(body));
            bytes.put(reference, body); return reference;
        }
        @Override public Optional<Session> currentSession() { return available ? Optional.of(session) : Optional.empty(); }
        @Override public Optional<RetainedArtifact> selectedSource(Milestone milestone, ProjectionJson payload) {
            return available && milestone == Milestone.M3 ? Optional.of(artifact) : Optional.empty();
        }
        @Override public byte[] readExact(ExactRef reference, int maximumBytes) throws IOException {
            byte[] body = bytes.get(reference);
            if (body == null || body.length > maximumBytes) { throw new IOException("unit source missing/oversized"); }
            return body.clone();
        }
    }
}
