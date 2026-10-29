package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software producer-to-consumer regressions; these fixtures grant no actual Game or runtime qualification. */
final class NativeReadinessRegressionTest {
    private static final String MACHINE = "test-machine";
    private static final Instant AT = Instant.parse("2026-10-24T00:00:00Z");
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
        "last_checkpoint":null,"command_history":[{"index":1,"command":"query-armies","ok":true,"result":{"optional":null,"armies":[]}}],
        "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,"campaign_goal":null}
        """;
    static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
        "played_character":{"character_id":73,"alive":true},"active_event":null,
        "pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
        "episode_identity_pending":false,"active_wars":[],"player_armies":[],
        "diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """;
    private static final String CAPS = """
        {"mode":"native-headless","backend_id":"native-headless","visual_fallback":false,
        "transport_ready":true,"snapshot":true,"diagnostics":{"connected":true,"semantic_state_available":true,
        "bridge_pid":42,"connection_generation":5,"transport_fatal_error":null,
        "hello":{"ck3_build_match":true,"game_adapter_status":"ready"},
        "last_heartbeat":{"sequence":1,"startup_failure_containment_enabled":false,"startup_particle2_stage_recorder_enabled":false,
        "main_thread_query_mailbox_v1":{"installed":true,"stop":false,"failure":0,"ready":true,
        "executor_submission_enabled":true,"date_raw":53144328,"paused":true,"pump_epochs":8}}},
        "native_session_control":{"episode_binding_state":"active_new","driver_state_restored":false,
        "driver_state_restore_kind":null,"cold_candidate_rejection":null}}
        """;
    record Fixture(DriverObservationAssembler.Complete frame, DriverSnapshotFacts.Known driver,
            SessionPorts.SemanticEvidence evidence, Map<ExactRef, byte[]> originals) { }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String name, byte[] raw) {
        return new ExactRef(java.nio.file.Path.of("target", "readiness-software-fixture", name).toAbsolutePath().toString(), raw.length, DriverJson.sha256(raw));
    }
    private static OpportunityJson.Obj object(String text) { return DriverJson.object(bytes(text), DriverJson.MAX_NATIVE_BYTES); }
    static Fixture fixture(String state) { return fixture(state, DRIVER); }
    static Fixture fixture(String state, String fullDriver) {
        var driver = DriverStateSnapshot.decodeComplete(bytes(fullDriver));
        byte[] payload = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(payload.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var transport = new NativeObservationPort.TransportSession(MACHINE, GAME, BigInteger.valueOf(5), "held-session");
        var nativeFrame = new NativeObservationPort.ObservedFrame(transport, "snapshot-9", BigInteger.valueOf(9), new RawJson(bytes(state)), packet, AT);
        var source = new G2Source(MACHINE, AT.toString(), "test-source", ref("source", bytes("source-only software input")));
        var facts = new DriverObservationFacts(driver, 3, 7, transport, nativeFrame.snapshotId(), nativeFrame.nativeRevision(),
                DriverJson.sha256(nativeFrame.state().bytes()), BigInteger.valueOf(2), 1, source, object("{}"), ref("facts", bytes("actual software facts")));
        var stamp = new DriverSnapshotFacts.Stamp(3, 7, GAME, driver.session().episodeRunId(), DriverJson.sha256(driver.encode()));
        var known = new DriverSnapshotFacts.Known(driver, stamp, ref("history", driver.encode()), List.of(), object("{}"), Optional.empty(), Optional.of(facts));
        var complete = assertInstanceOf(DriverObservationAssembler.Complete.class,
                new DriverObservationAssembler().assemble(nativeFrame, facts, ref("native", packet)));
        Map<ExactRef, byte[]> originals = new HashMap<>();
        byte[] semantic = DriverJson.encode(complete.semantic()), wire = driver.encode(), boundStamp = NativeDriverStamp.encode(complete, known);
        ExactRef semRef = ref("semantic", semantic), driverRef = ref("driver", wire), stampRef = ref("stamp", boundStamp);
        originals.put(semRef, semantic); originals.put(driverRef, wire); originals.put(stampRef, boundStamp); originals.put(complete.originalEvidence(), packet);
        return new Fixture(complete, known, new SessionPorts.SemanticEvidence(complete.identity(), semRef, complete.originalEvidence(), stampRef, driverRef, AT), originals);
    }
    private static NativeReadiness.Policy policy(boolean cold, boolean pump, Duration stable) {
        return new NativeReadiness.Policy(cold, false, Optional.of(BigInteger.valueOf(73)), stable, pump);
    }
    @Test void actualAssemblerFullDriverAndStampedOriginalsRoundTripThroughIndependentVerifier() throws IOException {
        Fixture f = fixture(STATE); Session session = new Session(); List<ExactRef> actualReads = new ArrayList<>();
        var verifier = new NativeSemanticEvidenceVerifier((borrowed, ref, maximum) -> {
            assertSame(session, borrowed); assertTrue(ref.bytes() <= maximum); actualReads.add(ref); return f.originals().get(ref).clone();
        });
        var verified = verifier.verify(session, new SessionPorts.SessionIdentity(MACHINE, GAME, "held-session"), f.evidence());
        assertEquals(f.frame().identity(), verified.frame()); assertEquals(4, actualReads.size());
        assertTrue(verified.semanticEvidenceId().startsWith("semantic-")); assertEquals(64, verified.materialDigest().length());
        assertEquals("9007199254740993", OpportunityJson.text(DriverJson.object(f.originals().get(f.evidence().driverStamp()), 16384).get("game_creation_filetime"), "birth"));
    }
    @Test void tamperedOriginalBytesMissingFullHistoryAndBooleanStampCannotBeCertified() {
        for (String caseName : List.of("tamper", "omitted-history", "wrong-stamp-type", "raw-state-drift")) {
            Fixture f = fixture(STATE); Map<ExactRef, byte[]> changed = new HashMap<>(f.originals());
            SessionPorts.SemanticEvidence evidence = f.evidence();
            if (caseName.equals("tamper")) changed.put(evidence.originalNativePacket(), bytes("bad original"));
            else {
                boolean stamp = caseName.equals("wrong-stamp-type"); ExactRef old = stamp ? evidence.driverStamp() : evidence.semantic();
                OpportunityJson.Obj document = DriverJson.object(changed.remove(old), DriverJson.MAX_NATIVE_BYTES);
                OpportunityJson.Obj replacement = stamp ? document.with("connection_generation", new OpportunityJson.Bool(true))
                        : caseName.equals("omitted-history") ? document.with("native_command_history", new OpportunityJson.Arr(List.of()))
                        : document.with("paused", new OpportunityJson.Bool(false));
                byte[] raw = DriverJson.encode(replacement); ExactRef updated = ref(caseName, raw); changed.put(updated, raw);
                evidence = new SessionPorts.SemanticEvidence(evidence.frame(), stamp ? evidence.semantic() : updated, evidence.originalNativePacket(),
                        stamp ? updated : evidence.driverStamp(), evidence.originalDriver(), evidence.observedAt());
            }
            var verifier = new NativeSemanticEvidenceVerifier((session, ref, maximum) -> changed.get(ref).clone());
            SessionPorts.SemanticEvidence actualEvidence = evidence;
            assertThrows(IOException.class, () -> verifier.verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, GAME, "held-session"), actualEvidence), caseName);
        }
    }
    @Test void mismatchSessionBirthAndObservedTimeNeverPassOnReferenceShape() {
        Fixture f = fixture(STATE); var verifier = new NativeSemanticEvidenceVerifier((session, ref, maximum) -> f.originals().get(ref).clone());
        assertThrows(IOException.class, () -> verifier.verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, GAME, "other-session"), f.evidence()));
        var otherGame = new GameGeneration(GAME.pid(), new PythonOnlyUInt64(GAME.creationFiletime().value().add(BigInteger.ONE)));
        assertThrows(IOException.class, () -> verifier.verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, otherGame, "held-session"), f.evidence()));
        var late = new SessionPorts.SemanticEvidence(f.evidence().frame(), f.evidence().semantic(), f.evidence().originalNativePacket(),
                f.evidence().driverStamp(), f.evidence().originalDriver(), AT.plusNanos(1));
        assertThrows(IOException.class, () -> verifier.verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, GAME, "held-session"), late));
    }
    @Test void archivedStampCannotRelabelObservationContractOrRewriteRetainedDriverSlots() {
        for (String field : List.of("observation-version", "binding", "campaign_goal", "succession_lifecycle", "native_rollback_war_failure", "native_rollback_war_failures")) {
            Fixture original = fixture(STATE); Map<ExactRef, byte[]> changed = new HashMap<>(original.originals());
            boolean stampField = field.equals("observation-version") || field.equals("binding");
            ExactRef prior = stampField ? original.evidence().driverStamp() : original.evidence().semantic();
            OpportunityJson.Obj document = DriverJson.object(changed.remove(prior), DriverJson.MAX_NATIVE_BYTES);
            OpportunityJson.Obj altered = field.equals("observation-version")
                    ? document.with("observation_version", new OpportunityJson.IntegerValue(BigInteger.valueOf(99)))
                    : field.equals("binding") ? document.with("full_binding_sha256", new OpportunityJson.Text("0".repeat(64)))
                    : document.with(field, new OpportunityJson.Obj(Map.of("invented", new OpportunityJson.Bool(true))));
            byte[] bytes = DriverJson.encode(altered); ExactRef updated = ref(field, bytes); changed.put(updated, bytes);
            SessionPorts.SemanticEvidence old = original.evidence();
            var evidence = new SessionPorts.SemanticEvidence(old.frame(), stampField ? old.semantic() : updated,
                    old.originalNativePacket(), stampField ? updated : old.driverStamp(), old.originalDriver(), old.observedAt());
            var verifier = new NativeSemanticEvidenceVerifier((session, ref, maximum) -> changed.get(ref).clone());
            assertThrows(IOException.class, () -> verifier.verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, GAME, "held-session"), evidence), field);
        }
    }
    @Test void completeDriverSlotsRoundTripThroughRealSemanticProducerWithPresenceAndJsonValues() throws IOException {
        String retained = DRIVER.replace("\"campaign_goal\":null", "\"campaign_goal\":{\"ordered\":[1,null,{\"flag\":true}],\"empty\":[]},"
                + "\"succession_lifecycle\":null,\"rollback_war_failures\":[{\"branch\":\"original\",\"score\":1.25}]");
        Fixture f = fixture(STATE, retained);
        var verifier = new NativeSemanticEvidenceVerifier((session, ref, maximum) -> f.originals().get(ref).clone());
        assertEquals(f.frame().identity(), verifier.verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, GAME, "held-session"), f.evidence()).frame());
        assertInstanceOf(OpportunityJson.Obj.class, f.frame().semantic().get("campaign_goal"));
        assertSame(OpportunityJson.Nil.INSTANCE, f.frame().semantic().get("succession_lifecycle"));
        assertInstanceOf(OpportunityJson.Arr.class, f.frame().semantic().get("native_rollback_war_failures"));
    }
    @Test void oldStampAndMissingNewVersionFieldsDoNotSilentlyAcquireCurrentQualification() {
        for (String mode : List.of("old-schema", "missing-version", "boolean-version", "float-version", "out-of-range-driver-version", "invalid-time")) {
            Fixture f = fixture(STATE); Map<ExactRef, byte[]> changed = new HashMap<>(f.originals());
            var stamp = DriverJson.object(changed.remove(f.evidence().driverStamp()), 16384);
            Map<String, OpportunityJson.Value> members = new HashMap<>(stamp.members());
            if (mode.equals("old-schema")) members.put("schema", new OpportunityJson.Text("xar.native-semantic-driver-stamp/v1"));
            else if (mode.equals("missing-version")) members.remove("observation_version");
            else if (mode.equals("out-of-range-driver-version")) members.put("driver_version", new OpportunityJson.IntegerValue(BigInteger.ONE.shiftLeft(63)));
            else if (mode.equals("invalid-time")) members.put("observed_at", new OpportunityJson.Text("not-an-instant"));
            else members.put("observation_version", mode.equals("boolean-version") ? new OpportunityJson.Bool(true)
                    : object("{\"value\":1.0}").get("value"));
            byte[] raw = DriverJson.encode(new OpportunityJson.Obj(members)); ExactRef updated = ref(mode, raw); changed.put(updated, raw);
            var evidence = new SessionPorts.SemanticEvidence(f.evidence().frame(), f.evidence().semantic(), f.evidence().originalNativePacket(),
                    updated, f.evidence().originalDriver(), f.evidence().observedAt());
            assertThrows(IOException.class, () -> new NativeSemanticEvidenceVerifier((session, ref, maximum) -> changed.get(ref).clone())
                    .verify(new Session(), new SessionPorts.SessionIdentity(MACHINE, GAME, "held-session"), evidence), mode);
        }
    }
    @Test void readinessRejectsWrongTokenMissingAndDifferentActorButAcceptsActualColdRestore() {
        Fixture f = fixture(STATE);
        assertTrue(NativeReadiness.assess(f.frame(), object(CAPS), policy(false, false, Duration.ZERO)).ready());
        for (String malformed : List.of(CAPS.replace("\"failure\":0", "\"failure\":false"), CAPS.replace("\"failure\":0,", ""), CAPS.replace("\"failure\":0", "\"failure\":0.0")))
            assertEquals(NativeReadiness.Status.INCOMPLETE, NativeReadiness.assess(f.frame(), object(malformed), policy(false, false, Duration.ZERO)).status());
        assertFalse(NativeReadiness.assess(f.frame(), object(CAPS), policy(true, false, Duration.ZERO)).ready());
        String cold = CAPS.replace("active_new", "active_resumed").replace("\"driver_state_restored\":false", "\"driver_state_restored\":true")
                .replace("\"driver_state_restore_kind\":null", "\"driver_state_restore_kind\":\"cold_checkpoint\"");
        assertTrue(NativeReadiness.assess(f.frame(), object(cold), policy(true, false, Duration.ZERO)).ready());
        var wrongActor = new DriverObservationAssembler.Complete(f.frame().identity(), f.frame().source(), f.frame().sessionId(), f.frame().connectionGeneration(),
                f.frame().semantic().with("episode_character_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(74))), f.frame().originalEvidence(), AT, f.frame().fullBindingSha256());
        assertFalse(NativeReadiness.assess(wrongActor, object(CAPS), policy(false, false, Duration.ZERO)).ready());
    }
    @Test void stableReadinessRequiresLaterSameFramePumpAndResetsAfterGap() {
        Fixture f = fixture(STATE); var policy = policy(false, true, Duration.ofSeconds(2)); AtomicLong ticks = new AtomicLong(10);
        var gate = new NativeReadiness.StableGate(policy, ticks::get);
        assertFalse(gate.observe(NativeReadiness.assess(f.frame(), object(CAPS), policy)).ready());
        ticks.addAndGet(Duration.ofSeconds(3).toNanos());
        assertFalse(gate.observe(NativeReadiness.assess(f.frame(), object(CAPS), policy)).ready());
        var later = object(CAPS.replace("\"pump_epochs\":8", "\"pump_epochs\":9"));
        assertTrue(gate.observe(NativeReadiness.assess(f.frame(), later, policy)).ready());
        var missing = object(CAPS.replace("\"snapshot\":true", "\"snapshot\":false"));
        assertFalse(gate.observe(NativeReadiness.assess(f.frame(), missing, policy)).ready());
        assertFalse(gate.observe(NativeReadiness.assess(f.frame(), later, policy)).ready());
    }
    private static final class Session implements ContinuityStorePort.Session {
        private final WriterContracts.Head head;
        Session() {
            byte[] raw = bytes("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"test-machine\",\"sequence\":0,\"window_id\":1,\"start_date_raw\":0,\"target_date_raw\":24,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":0}");
            head = new WriterContracts.Head(ContinuityState.fromJson(ContinuityJson.parseObject(raw, 65536), MACHINE), List.of(), List.of(), List.of(), false);
        }
        @Override public WriterContracts.Head head() { return head; }
        @Override public void requireWriter(Path originalWriterLock) { throw new AssertionError("pure fixture has no physical writer authority"); }
        @Override public WriterContracts.Pin capturePin(ExactRef reference, int maximumBytes) { throw new AssertionError("pure fixture has no physical pin authority"); }
        @Override public void verifyPin(WriterContracts.Pin pin) { throw new AssertionError("pure fixture has no physical pin authority"); }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) { throw new AssertionError("verifier must not preview a mutation"); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { throw new AssertionError("verifier must not commit"); }
        @Override public ExactRef persistedHead() { throw new AssertionError("software verifier needs no fabricated persisted head"); }
    }
}
