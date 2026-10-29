package org.xar.ck3.control.application.readiness;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.time.Duration;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Original ProtocolState diagnostics joined to an independently measured live Game and frozen Driver lifecycle. */
public final class RootNativeCapabilities {
    private RootNativeCapabilities() { }
    public record Projection(Obj capabilities, Obj originalHello, Obj originalHeartbeat,
            List<RawJson> originalMaterials, DriverSnapshotFacts.Stamp driverStamp) {
        public Projection {
            Objects.requireNonNull(capabilities); Objects.requireNonNull(originalHello); Objects.requireNonNull(originalHeartbeat);
            originalMaterials = List.copyOf(originalMaterials); Objects.requireNonNull(driverStamp);
        }
    }
    public static Projection project(Complete frame, DriverSnapshotFacts.Known driver,
            NativeGameTransport.TransportDiagnostics received, GameLifecycle.Running actualProcess,
            Instant now, Instant deadline, Duration maximumAge) {
        Objects.requireNonNull(frame);
        return projectReceived(new ProjectionFrame(frame.identity().machineId(), frame.identity().game(), frame.sessionId(),
                frame.connectionGeneration(), frame.identity().frame().snapshotId(), frame.identity().frame().identity().nativeRevision(),
                frame.identity().frame().revision(), frame.identity().frame().episodeRunId(), frame.observedAt()),
                driver, received, actualProcess, now, deadline, maximumAge);
    }
    /** Actual raw terminal DATA has no fabricated player identity, Complete, ordinary lease or action authority. */
    public static Projection projectPublicFull(DriverObservationAssembler.FullSnapshot full, DriverSnapshotFacts.Known driver,
            NativeGameTransport.TransportDiagnostics received, GameLifecycle.Running actualProcess,
            Instant now, Instant deadline, Duration maximumAge) {
        Objects.requireNonNull(full); Objects.requireNonNull(driver);
        var rebuilt = new DriverObservationAssembler().projectFull(full.actual(), full.facts(), full.originalEvidence());
        require(rebuilt.semantic().equals(full.semantic()) && rebuilt.fullBindingSha256().equals(full.fullBindingSha256()),
                "public raw capabilities require the exact original full semantic projection");
        require(driver.observation().filter(full.facts()::equals).isPresent()
                && driver.stamp().driverVersion() == full.facts().driverVersion()
                && driver.stamp().episodeEpoch() == full.facts().episodeEpoch()
                && Arrays.equals(driver.driver().encode(), full.facts().driver().encode()),
                "public raw capabilities crossed the actual complete Driver facts/version");
        var actual = full.actual();
        return projectReceived(new ProjectionFrame(actual.session().machineId(), actual.session().game(), actual.session().sessionId(),
                actual.session().connectionGeneration(), actual.snapshotId(), actual.nativeRevision(), full.facts().publicRevision(),
                driver.driver().session().episodeRunId(), actual.observedAt()), driver, received, actualProcess, now, deadline, maximumAge);
    }
    private record ProjectionFrame(String machineId, GameGeneration game, String sessionId, BigInteger connectionGeneration,
            String snapshotId, BigInteger nativeRevision, BigInteger publicRevision, String episodeRunId, Instant observedAt) { }
    /** Common original HELLO/heartbeat/Driver/current-process checks for Complete and raw full DATA. */
    private static Projection projectReceived(ProjectionFrame frame, DriverSnapshotFacts.Known driver,
            NativeGameTransport.TransportDiagnostics received, GameLifecycle.Running actualProcess,
            Instant now, Instant deadline, Duration maximumAge) {
        Objects.requireNonNull(frame); Objects.requireNonNull(driver); Objects.requireNonNull(received);
        Objects.requireNonNull(actualProcess); Objects.requireNonNull(now); Objects.requireNonNull(deadline); Objects.requireNonNull(maximumAge);
        require(!maximumAge.isNegative() && !maximumAge.isZero() && maximumAge.compareTo(Duration.ofMinutes(1)) <= 0,
                "explicit finite current native freshness boundary required");
        require(now.isBefore(deadline) && !frame.observedAt().isAfter(now), "actual semantic native frame is future-dated or its caller deadline expired");
        require(actualProcess.measured().equals(frame.game()), "measured live process differs from actual semantic Game");
        require(received.receivedState() == NativeGameTransport.ReceivedState.HELLO_VERIFIED && received.terminalFailure().isEmpty(),
                "held transport is not in its received hello state");
        var transport = received.session().orElseThrow(() -> new IllegalStateException("actual held transport session absent"));
        require(transport.machineId().equals(frame.machineId()) && transport.game().equals(frame.game())
                && transport.sessionId().equals(frame.sessionId()) && transport.connectionGeneration().equals(frame.connectionGeneration()),
                "capability transport crossed the actual semantic session");
        var helloReceived = received.originalHello().orElseThrow(() -> new IllegalStateException("actual original hello absent"));
        var heartbeatReceived = received.latestHeartbeat().orElseThrow(() -> new IllegalStateException("actual original heartbeat absent"));
        require(!helloReceived.observedAt().isAfter(frame.observedAt()) && !heartbeatReceived.observedAt().isBefore(helloReceived.observedAt())
                && !heartbeatReceived.observedAt().isAfter(now) && !heartbeatReceived.observedAt().isAfter(deadline), "actual heartbeat is future-dated, pre-hello or crossed the semantic observation deadline");
        require(heartbeatReceived.original().kind() == NativeWire.NoticeKind.HEARTBEAT, "actual heartbeat notice kind required");
        Obj hello = framedObject(helloReceived.original().packet().value());
        Obj heartbeat = framedObject(heartbeatReceived.original().packet().value());
        require(new Text("hello").equals(hello.get("type")) && new Text("heartbeat").equals(heartbeat.get("type")), "actual original notice type differs");
        require(BigInteger.ONE.equals(integer(hello.get("protocol_version"), "protocol_version"))
                && BigInteger.ONE.equals(integer(heartbeat.get("protocol_version"), "protocol_version")), "protocol-v1 notice required");
        require(integer(hello.get("pid"), "pid").equals(BigInteger.valueOf(frame.game().pid()))
                && integer(hello.get("connection_generation"), "connection_generation").equals(frame.connectionGeneration()), "original hello process/generation differs");
        require(driver.stamp().game().equals(frame.game()) && driver.stamp().episodeRunId().equals(frame.episodeRunId()),
                "actual Driver stamp crossed the observed Game/episode");
        require(driver.observation().isPresent(), "same-version actual Driver observation absent");
        var observed = driver.observation().orElseThrow();
        require(observed.driverVersion() == driver.stamp().driverVersion() && observed.episodeEpoch() == driver.stamp().episodeEpoch()
                && observed.transport().equals(transport) && observed.snapshotId().equals(frame.snapshotId())
                && observed.nativeRevision().equals(frame.nativeRevision())
                && observed.publicRevision().equals(frame.publicRevision()), "capability projection crossed frozen Driver observation");
        // These lifecycle fields are published by the existing Driver owner, never inferred from map_ready.
        Obj control = DriverCapabilityStateProducer.sessionPresentation(driver.auxiliary()).original();
        NativeReadiness.string(control, "episode_binding_state");
        NativeReadiness.flag(control, "driver_state_restored");
        Value restoreKind = NativeReadiness.present(control, "driver_state_restore_kind");
        require(restoreKind == Nil.INSTANCE || restoreKind instanceof Text, "restore kind must retain explicit null/string");
        NativeReadiness.present(control, "cold_candidate_rejection");
        Map<String, Value> diagnostics = new LinkedHashMap<>();
        diagnostics.put("connected", new Bool(true)); // Measured live Game plus this same held, nonterminal transport above.
        diagnostics.put("semantic_state_available", new Bool(true)); // Actual full native/Driver semantic DATA, never an ordinary readiness claim.
        diagnostics.put("bridge_pid", new IntegerValue(BigInteger.valueOf(transport.game().pid())));
        diagnostics.put("connection_generation", new IntegerValue(transport.connectionGeneration()));
        diagnostics.put("hello", hello); diagnostics.put("last_heartbeat", heartbeat);
        diagnostics.put("transport_fatal_error", Nil.INSTANCE);
        boolean snapshotSupported = helloReceived.original().capabilities().contains("game.state.snapshot");
        Obj capabilities = new Obj(Map.of("mode", new Text("native-headless"), "backend_id", new Text("native-headless"),
                "visual_fallback", new Bool(false), "transport_ready", new Bool(true),
                "snapshot", new Bool(snapshotSupported), "wait_for_change", new Bool(snapshotSupported),
                "diagnostics", new Obj(diagnostics), "native_session_control", control));
        return new Projection(capabilities, hello, heartbeat, List.of(new RawJson(encode(hello)), new RawJson(encode(heartbeat))), driver.stamp());
    }
    /** Full framed bytes are validated; JSON parsing cannot silently consume the four-byte native length prefix. */
    public static Obj framedObject(byte[] packet) {
        Objects.requireNonNull(packet);
        require(packet.length >= 5 && packet.length <= NativeWire.MAXIMUM_FRAME_BYTES + 4, "bounded original framed native packet required");
        int declared = ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        require(declared == packet.length - 4 && declared > 0, "original native packet length differs from its header");
        return DriverJson.object(Arrays.copyOfRange(packet, 4, packet.length), NativeWire.MAXIMUM_FRAME_BYTES);
    }
}
