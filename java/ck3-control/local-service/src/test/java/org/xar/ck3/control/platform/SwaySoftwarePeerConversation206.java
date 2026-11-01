package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.planning.sway.SwayNativeWire;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Owned software peer only. Direct dynamic packets are DATA, never transport action custody or Root authority. */
public final class SwaySoftwarePeerConversation206 {
    private SwaySoftwarePeerConversation206() { }
    private static final int PACKET_LIMIT = 1024 * 1024 + 4;
    private static final Set<String> SETTINGS = Set.of("executable", "software_executable_sha256", "work_directory",
            "evidence_root", "environment", "actor", "target", "bridge_version", "hello_executable_sha256", "adapter_id",
            "memory_limit_bytes", "lifetime_ms", "max_requests");

    public static SwayPeer206Contract.Settings readSettings(Path path) throws Exception {
        require(path.isAbsolute() && Files.isRegularFile(path), "explicit absolute settings file required");
        require(Files.size(path) > 0 && Files.size(path) <= 65536, "bounded settings file required");
        ObjectNode row = StrictJson.object(StrictJson.parse(Files.readAllBytes(path)), SETTINGS);
        Path executable = Path.of(StrictJson.text(row.get("executable"))).toRealPath();
        Path cwd = Path.of(StrictJson.text(row.get("work_directory"))).toRealPath();
        Path evidence = Path.of(StrictJson.text(row.get("evidence_root"))).toRealPath();
        require(Files.isRegularFile(executable) && Files.isDirectory(cwd) && Files.isDirectory(evidence), "software paths required");
        require(executable.getFileName().toString().equalsIgnoreCase("sameworld_live_peer.exe"), "only the explicit software peer is permitted");
        String softwareSha = shaText(row.get("software_executable_sha256"));
        String helloSha = shaText(row.get("hello_executable_sha256"));
        require(row.get("environment").isObject(), "environment object required");
        Map<String, String> environment = new HashMap<>();
        for (var entry : row.get("environment").properties()) environment.put(entry.getKey(), StrictJson.text(entry.getValue()));
        long actor = StrictJson.integer(row.get("actor"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        long target = StrictJson.integer(row.get("target"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        require(actor != -1 && target != -1 && actor != target, "distinct actual signed character IDs required");
        return new SwayPeer206Contract.Settings(executable, softwareSha, cwd, evidence, environment, actor, target,
                StrictJson.text(row.get("bridge_version")), helloSha, StrictJson.text(row.get("adapter_id")),
                StrictJson.integer(row.get("memory_limit_bytes"), 1, 128L * 1024 * 1024),
                StrictJson.integer(row.get("lifetime_ms"), 1, 60000),
                Math.toIntExact(StrictJson.integer(row.get("max_requests"), 1, 32)));
    }

    public static SwayPeer206Contract.Result run(SwayPeer206Contract.Settings settings,
            SwayPeer206Contract.Scenario scenario) throws Exception {
        Objects.requireNonNull(settings); Objects.requireNonNull(scenario);
        // Revalidate even if a test constructs Settings directly; never use this helper to launch an arbitrary process.
        Path executable = settings.executable().toRealPath();
        require(executable.getFileName().toString().equalsIgnoreCase("sameworld_live_peer.exe"), "software peer basename required");
        require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(executable)))
                .equalsIgnoreCase(settings.softwareExecutableSha256()), "software executable SHA differs");
        require(settings.memoryLimitBytes() > 0 && settings.memoryLimitBytes() <= 128L * 1024 * 1024
                && settings.lifetimeMillis() > 0 && settings.lifetimeMillis() <= 60000
                && settings.maximumRequests() > 0 && settings.maximumRequests() <= 32, "finite software bounds required");
        String runId = UUID.randomUUID().toString();
        Path evidence = Files.createDirectory(settings.evidenceRoot().resolve(runId));
        Path originals = Files.createDirectory(evidence.resolve("native-originals"));
        Path packets = Files.createDirectory(evidence.resolve("java-original-packets"));
        String pipeName = "\\\\.\\pipe\\m6-software206-" + runId;
        Map<String, String> environment = new HashMap<>(System.getenv()); environment.putAll(settings.environment());
        var spec = new WindowsJobProcess.CommandSpec(executable,
                List.of(pipeName, originals.toString(), Long.toString(settings.actor()), Long.toString(settings.target()),
                        Long.toString(settings.lifetimeMillis()), Integer.toString(settings.maximumRequests())),
                settings.workDirectory(), environment, evidence.resolve("peer.stdout.raw"), evidence.resolve("peer.stderr.raw"),
                settings.memoryLimitBytes());
        Instant deadline = Instant.now().plusMillis(Math.min(settings.lifetimeMillis(), 30000));
        try (WindowsJobProcess job = WindowsJobProcess.start(spec)) {
            var identity = job.identity();
            require(Path.of(identity.executable()).toRealPath().equals(executable), "owned software process image differs");
            try (var handle = WindowsJobProcess.retainReadOnlyProcess(identity.pid())) {
                var generation = ManagedGameSession.generation(identity);
                NativeProcessGuard guard = expected -> {
                    require(expected.equals(generation), "owned generation differs");
                    require(handle.waitZero() == 258L && job.isRunning(), "owned software peer is not live");
                    var current = handle.identity();
                    require(current.pid() == identity.pid() && current.creationFiletimeDecimal().equals(identity.creationFiletimeDecimal())
                            && Path.of(current.executable()).toRealPath().equals(executable), "owned process identity changed");
                };
                var config = new NativePipeEndpoint.Config(pipeName, WindowsJobProcess.currentMachineId(), generation, runId,
                        settings.bridgeVersion(), settings.helloExecutableSha256(), settings.adapterId());
                List<SwayPeer206Contract.Exchange> exchanges = new ArrayList<>();
                TransportSession session;
                NativeFreshSnapshotPort.Received before;
                NativeFreshSnapshotPort.Received after;
                try (var endpoint = NativePipeEndpoint.create(config, guard);
                        var transport = new NativeGameTransport(endpoint, 64, 32)) {
                    session = transport.awaitHello(deadline);
                    var hello = transport.originalHello();
                    require(hello.pid() == identity.pid() && hello.connectionGeneration().equals(session.connectionGeneration()), "HELLO actual process/session differs");
                    save(packets, "hello.packet", hello.packet().value());
                    before = fresh(transport, deadline); saveFresh(packets, "before", before);
                    require(before.originalFrame().session().equals(session), "fresh before crossed session");
                    BigInteger revision = before.originalFrame().nativeRevision();
                    if (scenario == SwayPeer206Contract.Scenario.DYNAMIC_CHAIN) {
                        dynamic(settings, endpoint, packets, exchanges, revision, deadline);
                    } else {
                        require(revision.compareTo(NativeWire.UINT64_MAX) < 0, "stale revision would overflow");
                        var stale = exchange(endpoint, packets, exchanges, "stale-query", SwayNativeWire.TARGET + settings.target(),
                                revision.add(BigInteger.ONE), StrictJson.object(), deadline, false);
                        require(!stale.nativeOk() && "stale_snapshot_revision".equals(StrictJson.text(
                                StrictJson.parse(stale.error().token().orElseThrow().value()))), "actual stale error differs");
                    }
                    after = fresh(transport, deadline); saveFresh(packets, "after", after);
                    NativeFreshSnapshotPort.verifyAfter(before.acknowledgement(), after);
                    require(after.originalFrame().session().equals(session), "fresh after crossed session");
                }
                // Closing the one owned pipe lets this peer exit; this never queries or stops another process.
                var terminal = job.await(Duration.ofSeconds(8), Instant.now().plusSeconds(9), () -> { });
                save(evidence, "terminal.json", StrictJson.canonical(terminalJson(terminal)));
                require(terminal.passed(), "owned software peer failed to exit naturally: " + terminal.stopReason());
                return new SwayPeer206Contract.Result(scenario, identity, session, before, after, exchanges, terminal, evidence);
            }
        }
    }

    private static void dynamic(SwayPeer206Contract.Settings settings, NativePipeEndpoint endpoint, Path packets,
            List<SwayPeer206Contract.Exchange> exchanges, BigInteger revision, Instant deadline) throws Exception {
        String target = SwayNativeWire.TARGET + settings.target();
        var query = exchange(endpoint, packets, exchanges, "query0", target, revision, StrictJson.object(), deadline, true);
        ObjectNode initial = body(query, "active_scheme_sway");
        String action = "sway-live206-" + UUID.randomUUID();
        ObjectNode start = StrictJson.object().put("action_id", action)
                .put("expected_capture_epoch", StrictJson.integer(initial.get("capture_epoch"), BigInteger.ONE, NativeWire.UINT64_MAX))
                .put("expected_container_generation", StrictJson.integer(initial.get("container_generation"), BigInteger.ONE, NativeWire.UINT64_MAX))
                .put("expected_target_opinion_of_actor", Long.toString(StrictJson.integer(initial.get("target_opinion_of_actor"), -100, 100)));
        exchange(endpoint, packets, exchanges, "start", SwayNativeWire.START + settings.target(), revision, start, deadline, true);
        var receipt = exchange(endpoint, packets, exchanges, "receipt", SwayNativeWire.RECEIPT + settings.target(), revision,
                StrictJson.object().put("action_id", action), deadline, true);
        ObjectNode applied = body(receipt, "active_scheme_sway_formal");
        long instance = StrictJson.integer(applied.get("scheme_instance_id"), 0, 0xffff_fffeL);
        long generation = StrictJson.integer(applied.get("scheme_instance_generation"), 0, 255);
        exchange(endpoint, packets, exchanges, "post-start", target, revision, StrictJson.object(), deadline, true);
        exchange(endpoint, packets, exchanges, "finish-target", target, revision, StrictJson.object(), deadline, true);
        ObjectNode completion = pair(settings).put("scheme_instance_id", instance);
        exchange(endpoint, packets, exchanges, "finish-completion", "query-sway-completion-v1-private", revision, completion, deadline, true);
        exchange(endpoint, packets, exchanges, "finish-opinion", "query-sway-outcome-opinion-v1-private", revision, pair(settings), deadline, true);
        ObjectNode stop = pair(settings).put("action_id", "stop-sway-live206-" + UUID.randomUUID())
                .put("scheme_instance_id", instance).put("scheme_instance_generation", generation);
        exchange(endpoint, packets, exchanges, "stop", SwayNativeWire.STOP, revision, stop, deadline, true);
        exchange(endpoint, packets, exchanges, "post-stop", "query-sway-completion-v1-private", revision, completion, deadline, true);
    }

    private static NativeWire.CommandResult exchange(NativePipeEndpoint endpoint, Path packets,
            List<SwayPeer206Contract.Exchange> exchanges, String label, String step, BigInteger revision,
            ObjectNode additional, Instant deadline, boolean successRequired) throws Exception {
        String id = "request206-" + UUID.randomUUID();
        byte[] outgoing = NativeWire.execute(id, step, revision, StrictJson.canonical(additional));
        var decoded = NativeWire.decodeExecuteRequest(outgoing);
        require(decoded.requestId().equals(id) && decoded.step().equals(step) && decoded.expectedRevision().orElseThrow().equals(revision), "outgoing exact request differs");
        require(java.util.Arrays.equals(StrictJson.canonical(additional), StrictJson.canonical(
                StrictJson.parse(decoded.normalizedAdditionalFields().value()))), "outgoing domain fields differ");
        save(packets, label + ".outgoing.packet", outgoing);
        endpoint.writePacket(outgoing, deadline);
        for (int index = 0; index < 16; index++) {
            byte[] incoming = endpoint.readPacket(deadline);
            require(incoming.length <= PACKET_LIMIT, "software response packet exceeds scope");
            save(packets, label + ".incoming-" + index + ".packet", incoming);
            var frame = NativeWire.decode(incoming);
            if (frame instanceof NativeWire.Notice) continue;
            require(frame instanceof NativeWire.CommandResult, "unexpected software frame during direct exchange");
            var result = (NativeWire.CommandResult) frame;
            require(result.requestId().equals(id), "different response request ID; no resend permitted");
            exchanges.add(new SwayPeer206Contract.Exchange(label, outgoing, result));
            require(!successRequired || result.nativeOk(), "dynamic software request failed: " + label);
            return result;
        }
        throw new IOException("finite software response frame budget exhausted");
    }

    private static NativeFreshSnapshotPort.Received fresh(NativeGameTransport transport, Instant deadline) throws Exception {
        var result = transport.readFreshFullState(deadline);
        require(result instanceof NativeFreshSnapshotPort.Received, "actual fresh response unavailable: " + result);
        var received = (NativeFreshSnapshotPort.Received) result;
        NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(), received.originalFrame(), received.snapshotReceived());
        return received;
    }
    private static void saveFresh(Path dir, String label, NativeFreshSnapshotPort.Received value) throws IOException {
        save(dir, label + ".outgoing.packet", value.acknowledgement().outbound().orElseThrow().originalPacket());
        save(dir, label + ".snapshot.packet", value.originalFrame().originalPacket());
        save(dir, label + ".ack.packet", value.acknowledgement().originalPacket());
    }
    private static ObjectNode body(NativeWire.CommandResult value, String name) throws IOException {
        JsonNode result = StrictJson.parse(value.result().token().orElseThrow().value(), 1024 * 1024);
        require(result.isObject() && result.path(name).isObject(), "actual software result body missing: " + name);
        return (ObjectNode) result.get(name);
    }
    private static ObjectNode pair(SwayPeer206Contract.Settings settings) {
        return StrictJson.object().put("actor_character_id", settings.actor()).put("target_character_id", settings.target());
    }
    private static ObjectNode terminalJson(WindowsJobProcess.CommandResult value) {
        return StrictJson.object().put("pid", value.identity().pid()).put("creation_filetime", value.identity().creationFiletimeDecimal())
                .put("exit_code", value.exitCode()).put("passed", value.passed()).put("stop_reason", value.stopReason());
    }
    private static void save(Path dir, String name, byte[] bytes) throws IOException {
        Files.write(dir.resolve(name), bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }
    private static String shaText(JsonNode value) throws IOException {
        String text = StrictJson.text(value); require(text.matches("[0-9a-fA-F]{64}"), "SHA-256 text required"); return text;
    }
    private static void require(boolean value, String reason) throws IOException { if (!value) throw new IOException(reason); }
}
