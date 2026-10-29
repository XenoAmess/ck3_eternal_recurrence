package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Pure replay of decoded original packet custody. Execution grants and actual Game qualification remain Root-owned. */
final class RootNativeCapabilitiesRegressionTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final Duration FRESH = Duration.ofSeconds(5);
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String STATE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
        "episode_identity_pending":false,"active_wars":[],"player_armies":[],"diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """;
    record Fixture(DriverObservationAssembler.Complete frame, DriverSnapshotFacts.Known driver,
            NativeObservationPort.TransportSession transport, NativeWire.Hello hello, NativeWire.Notice heartbeat) { }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String role, byte[] value) {
        return new ExactRef(Path.of("target", "source-only-readiness-fixture", role).toAbsolutePath().toString(), value.length, DriverJson.sha256(value));
    }
    private static Fixture fixture() throws IOException {
        var driver = DriverStateSnapshot.decodeComplete(bytes("""
            {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-1",
            "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,
            "succession_expectation":null,"campaign_goal":null}
            """));
        var session = new NativeObservationPort.TransportSession("test-machine", GAME, BigInteger.valueOf(5), "held-session");
        byte[] packet = NativeWire.packet(bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + STATE + "}"));
        var actual = new NativeObservationPort.ObservedFrame(session, "snapshot-9", BigInteger.valueOf(9), new RawJson(bytes(STATE)), packet, NOW);
        var source = new G2Source("test-machine", NOW.toString(), "source-only-fixture", ref("source", bytes("software input")));
        var facts = new DriverObservationFacts(driver, 3, 7, session, actual.snapshotId(), actual.nativeRevision(),
                DriverJson.sha256(actual.state().bytes()), BigInteger.valueOf(2), 1, source,
                DriverJson.object(bytes("{}"), 65536), ref("facts", bytes("software facts")));
        var stamp = new DriverSnapshotFacts.Stamp(3, 7, GAME, driver.session().episodeRunId(), DriverJson.sha256(driver.encode()));
        var auxiliary = DriverJson.object(bytes("""
            {"episode_binding_state":"active_new","driver_state_restored":false,"restore_kind":"new_episode",
            "driver_state_error":null,"cold_candidate_rejection":null,"episode_transition_error":null,
            "capability_session_paths":{"queue_dir":null,"driver_state_path":null}}
            """), 65536);
        var known = new DriverSnapshotFacts.Known(driver, stamp, ref("driver", driver.encode()), List.of(), auxiliary, Optional.empty(), Optional.of(facts));
        var complete = assertInstanceOf(DriverObservationAssembler.Complete.class,
                new DriverObservationAssembler().assemble(actual, facts, ref("native", packet)));
        var hello = assertInstanceOf(NativeWire.Hello.class, NativeWire.decode(NativeWire.packet(bytes("""
            {"type":"hello","protocol_version":1,"pid":42,"connection_generation":5,"bridge_version":"fixture",
            "expected_ck3_sha256":"0000000000000000000000000000000000000000000000000000000000000000",
            "game_adapter_id":"fixture-adapter","game_adapter_status":"ready","ck3_build_match":true,"capabilities":["game.state.snapshot"]}
            """))));
        var heartbeat = assertInstanceOf(NativeWire.Notice.class, NativeWire.decode(NativeWire.packet(bytes("""
            {"type":"heartbeat","protocol_version":1,"sequence":1,"startup_failure_containment_enabled":false,
            "startup_particle2_stage_recorder_enabled":false,"main_thread_query_mailbox_v1":{"installed":true,"stop":false,
            "failure":0,"ready":true,"executor_submission_enabled":true,"date_raw":53144328,"paused":true,"pump_epochs":8}}
            """))));
        return new Fixture(complete, known, session, hello, heartbeat);
    }
    private static NativeGameTransport.TransportDiagnostics received(Fixture f, Instant helloAt, Instant heartbeatAt) {
        return new NativeGameTransport.TransportDiagnostics(NativeGameTransport.ReceivedState.HELLO_VERIFIED, Optional.of(f.transport()),
                Optional.of(new NativeGameTransport.ReceivedHello(f.hello(), helloAt)), Optional.of(new NativeGameTransport.ReceivedNotice(f.heartbeat(), heartbeatAt)),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), new NativeWire.Bytes(f.heartbeat().packet().value()));
    }
    private static RootNativeCapabilities.Projection project(Fixture f, NativeGameTransport.TransportDiagnostics diagnostics) {
        return RootNativeCapabilities.project(f.frame(), f.driver(), diagnostics, new GameLifecycle.Running(GAME, ref("live", bytes("software process measurement"))),
                NOW, NOW.plusSeconds(2), FRESH);
    }
    @Test void decodedOriginalNoticesAndActualFrozenDriverJoinWithoutInventingAbsentFields() throws IOException {
        Fixture f = fixture(); var projection = project(f, received(f, NOW.minusSeconds(60), NOW.minusSeconds(1)));
        assertEquals(f.driver().stamp(), projection.driverStamp());
        assertEquals(RootNativeCapabilities.framedObject(f.hello().packet().value()), projection.originalHello());
        assertEquals(RootNativeCapabilities.framedObject(f.heartbeat().packet().value()), projection.originalHeartbeat());
        assertTrue(NativeReadiness.assess(f.frame(), projection.capabilities(),
                new NativeReadiness.Policy(false, false, Optional.of(BigInteger.valueOf(73)), Duration.ZERO, false)).ready());
        assertFalse(projection.originalHello().members().containsKey("unmeasured_source_qualified"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true), projection.capabilities().get("snapshot"));
        assertEquals(projection.capabilities().get("snapshot"), projection.capabilities().get("wait_for_change"));
        var control = NativeReadiness.objectField(projection.capabilities(), "native_session_control");
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("new_episode"), control.get("driver_state_restore_kind"));
    }
    @Test void absentActualSnapshotSupportDisablesWaitForChange() throws IOException {
        Fixture f = fixture();
        byte[] packet = f.hello().packet().value();
        String original = new String(Arrays.copyOfRange(packet, 4, packet.length), StandardCharsets.UTF_8);
        var hello = assertInstanceOf(NativeWire.Hello.class, NativeWire.decode(NativeWire.packet(bytes(original.replace("[\"game.state.snapshot\"]", "[]")))));
        Fixture withoutSnapshot = new Fixture(f.frame(), f.driver(), f.transport(), hello, f.heartbeat());
        var capabilities = project(withoutSnapshot, received(withoutSnapshot, NOW.minusSeconds(60), NOW.minusSeconds(1))).capabilities();
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(false), capabilities.get("snapshot"));
        assertEquals(capabilities.get("snapshot"), capabilities.get("wait_for_change"));
    }
    @Test void futureAndPreHelloHeartbeatCannotGrantReadiness() throws IOException {
        Fixture f = fixture();
        assertThrows(IllegalArgumentException.class, () -> project(f, received(f, NOW.minusSeconds(60), NOW.plusNanos(1))));
        assertThrows(IllegalArgumentException.class, () -> project(f, received(f, NOW.minusSeconds(1), NOW.minusSeconds(2))));
    }

    @Test void processingBeyondCacheAgeRetainsOriginalTimeWithinCallerDeadline() throws IOException {
        Fixture f = fixture();
        Instant originalAt = f.frame().observedAt();
        var projection = RootNativeCapabilities.project(f.frame(), f.driver(), received(f, NOW.minusSeconds(60), NOW.minusSeconds(1)),
                new GameLifecycle.Running(GAME, ref("live", bytes("software process measurement"))),
                NOW.plusSeconds(8), NOW.plusSeconds(20), FRESH);
        assertEquals(originalAt, f.frame().observedAt());
        assertEquals(f.driver().stamp(), projection.driverStamp());
    }

    @Test void deadlineAlreadyExpiredNegative() throws IOException {
        Fixture f = fixture();
        assertThrows(IllegalArgumentException.class, () -> RootNativeCapabilities.project(f.frame(), f.driver(), received(f, NOW.minusSeconds(60), NOW.minusSeconds(1)),
                new GameLifecycle.Running(GAME, ref("live", bytes("software process measurement"))), NOW, NOW.minusSeconds(1), FRESH));
    }
    @Test void measuredOtherGameAndMissingOriginalHeartbeatCannotBeReplacedByTransportState() throws IOException {
        Fixture f = fixture(); var diagnostics = received(f, NOW.minusSeconds(60), NOW);
        GameGeneration replacement = new GameGeneration(GAME.pid(), new PythonOnlyUInt64(GAME.creationFiletime().value().add(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class, () -> RootNativeCapabilities.project(f.frame(), f.driver(), diagnostics,
                new GameLifecycle.Running(replacement, ref("other", bytes("other process"))), NOW, NOW.plusSeconds(2), FRESH));
        var missing = new NativeGameTransport.TransportDiagnostics(diagnostics.receivedState(), diagnostics.session(), diagnostics.originalHello(), Optional.empty(),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), diagnostics.lastOriginalPacket());
        assertThrows(IllegalStateException.class, () -> project(f, missing));
    }
}
