package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;

/** Real ordinary child/Job resources. No Steam, Game, injection, or native frames are simulated. */
final class GameSupervisorTest {
    @TempDir Path temporary;

    private WindowsJobProcess child(String mode) throws IOException {
        Path root = Files.createTempDirectory(temporary, "supervisor-peer-");
        String cp = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        var arguments = new ArrayList<>(List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC",
                "-XX:ActiveProcessorCount=1", "-XX:MaxMetaspaceSize=32m", "-XX:ReservedCodeCacheSize=16m", "-Xss256k",
                "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", cp, LifecycleSoftwarePeer.class.getName(), mode));
        var environment = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv()); environment.remove("JAVA_TOOL_OPTIONS");
        return WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"), "bin/java.exe"),
                arguments, root, environment, root.resolve("stdout.raw"), root.resolve("stderr.raw"), 128L << 20));
    }

    private final class RunningOwner implements AutoCloseable {
        final WindowsJobProcess process;
        final Path stopPath = temporary.resolve("stop-" + java.util.UUID.randomUUID() + ".json");
        final AtomicInteger rejected = new AtomicInteger(), stops = new AtomicInteger();
        final FutureTask<GameSupervisor.Completed> result;
        final Thread monitor;
        RunningOwner(String mode) throws IOException {
            process = child(mode);
            GameSupervisor.Owner actual = new GameSupervisor.Owner() {
                @Override public String sessionId() { return "software-owner"; }
                @Override public WindowsJobProcess.ProcessIdentity identity() { return process.identity(); }
                @Override public boolean running() { return process.isRunning(); }
                @Override public GameSupervisor.Terminal stop(Instant until, GameLifecycle.TerminalKind kind)
                        throws IOException, InterruptedException {
                    stops.incrementAndGet();
                    if (process.isRunning()) process.terminate(125);
                    var terminal = process.await(Duration.ofSeconds(3), until, () -> { });
                    return new GameSupervisor.Terminal(terminal, ManagedGameSession.cleanupProven(process, terminal), kind, Optional.empty());
                }
            };
            result = new FutureTask<>(() -> GameSupervisor.awaitOwner(actual, stopPath, detail -> rejected.incrementAndGet()));
            monitor = new Thread(result, "software-physical-owner");
            monitor.setDaemon(true); monitor.start();
        }
        @Override public void close() throws IOException {
            try {
                if (process.isRunning()) process.terminate(125);
                process.await(Duration.ofSeconds(3), Instant.now().plusSeconds(4), () -> { });
                monitor.join(5000);
                if (monitor.isAlive()) throw new IOException("software owner did not consume the actual child exit");
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("software owner cleanup interrupted", interrupted);
            } finally { process.close(); }
        }
    }

    private static void awaitCount(AtomicInteger count, int expected) throws InterruptedException {
        Instant until = Instant.now().plusSeconds(5);
        while (count.get() < expected && Instant.now().isBefore(until)) Thread.sleep(10);
        assertTrue(count.get() >= expected, "actual owner loop did not consume the request");
    }

    @Test void workerExitMalformedAndExpiredStopsDoNotCloseTheIndependentOwnerButMatchingStopDoes() throws Exception {
        try (var owner = new RunningOwner("wait")) {
            try (var worker = child("exit0")) {
                var exited = worker.await(Duration.ofSeconds(5), Instant.now().plusSeconds(6), () -> { });
                assertEquals(0, exited.exitCode()); assertEquals(0, exited.accounting().activeProcesses());
            }
            assertTrue(owner.process.isRunning()); assertFalse(owner.result.isDone());
            Files.writeString(owner.stopPath, "{broken");
            awaitCount(owner.rejected, 1);
            assertTrue(owner.process.isRunning()); assertEquals(0, owner.stops.get());
            var expired = new GameSupervisorControl.StopRequest("expired", "software-owner", owner.process.identity(), Instant.now().minusSeconds(1));
            GameSupervisorControl.writeStop(owner.stopPath, expired);
            awaitCount(owner.rejected, 2);
            assertTrue(owner.process.isRunning()); assertEquals(0, owner.stops.get());
            var original = owner.process.identity();
            var different = new WindowsJobProcess.ProcessIdentity(original.pid(),
                    new java.math.BigInteger(original.creationFiletimeDecimal()).add(java.math.BigInteger.ONE).toString(), original.executable());
            GameSupervisorControl.writeStop(owner.stopPath, new GameSupervisorControl.StopRequest(
                    "wrong-generation", "software-owner", different, Instant.now().plusSeconds(5)));
            awaitCount(owner.rejected, 3);
            assertTrue(owner.process.isRunning()); assertFalse(owner.result.isDone()); assertEquals(0, owner.stops.get());
            GameSupervisorControl.writeStop(owner.stopPath, new GameSupervisorControl.StopRequest(
                    "explicit-stop", "software-owner", original, Instant.now().plusSeconds(5)));
            var completed = owner.result.get(8, TimeUnit.SECONDS);
            assertEquals("explicit-stop", completed.requestId()); assertEquals(1, owner.stops.get());
            assertEquals(GameLifecycle.TerminalKind.OWNER_STOP, completed.terminal().kind());
            assertTrue(completed.terminal().cleanupProven()); assertEquals(0, completed.terminal().actual().accounting().activeProcesses());
            assertEquals(125, completed.terminal().actual().exitCode()); assertFalse(completed.terminal().actual().passed());
            assertEquals(original, completed.terminal().actual().identity()); assertTrue(completed.terminal().evidence().isEmpty());
            var parsed = publishActualTerminal(completed);
            assertEquals("OWNER_STOP_COMPLETED", parsed.get("status").asText());
            assertEquals("explicit-stop", parsed.get("stop_request_id").asText());
            assertTrue(parsed.get("cleanup_proven").asBoolean());
            assertEquals(125, parsed.get("actual_terminal").get("exit_code").asInt());
            assertEquals(java.math.BigDecimal.valueOf(completed.terminal().actual().elapsedSeconds()).toPlainString(),
                    parsed.get("actual_terminal").get("elapsed_seconds_decimal").asText());
            assertFalse(parsed.get("actual_terminal").has("elapsed_seconds"));
        }
    }

    @Test void actualNaturalExit259StaysNonzeroAndConsumesTheHeldJobWithoutAnExplicitStop() throws Exception {
        try (var owner = new RunningOwner("exit259")) {
            var completed = owner.result.get(8, TimeUnit.SECONDS);
            assertEquals("", completed.requestId());
            assertEquals(GameLifecycle.TerminalKind.NATURAL_EXIT, completed.terminal().kind());
            assertEquals(259, completed.terminal().actual().exitCode()); assertFalse(completed.terminal().actual().passed());
            assertTrue(completed.terminal().cleanupProven()); assertEquals(0, completed.terminal().actual().accounting().activeProcesses());
            assertEquals(1, owner.stops.get()); assertFalse(Files.exists(owner.stopPath));
            var parsed = publishActualTerminal(completed);
            assertEquals("GAME_EXITED", parsed.get("status").asText());
            assertEquals(259, parsed.get("actual_terminal").get("exit_code").asInt());
            assertEquals(java.math.BigDecimal.valueOf(completed.terminal().actual().elapsedSeconds()).toPlainString(),
                    parsed.get("actual_terminal").get("elapsed_seconds_decimal").asText());
            assertFalse(parsed.get("actual_terminal").has("elapsed_seconds"));
        }
    }

    @Test void stopProducerConsumerKeepsExactFiletimeAndRejectsWrongJsonTypes() throws Exception {
        var identity = new WindowsJobProcess.ProcessIdentity(42, "134376718582643410", temporary.resolve("software.exe").toString());
        var request = new GameSupervisorControl.StopRequest("stop", "session", identity, Instant.now().plusSeconds(10));
        Path target = temporary.resolve("stop.json");
        GameSupervisorControl.writeStop(target, request);
        assertEquals(request, GameSupervisorControl.readStop(target));
        var encoded = StrictJson.parse(GameSupervisorControl.encodeStop(request), 16384);
        assertTrue(encoded.path("game").path("creation_filetime").isTextual());
        for (var wrong : List.of(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(134376718582643410L),
                com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.booleanNode(true))) {
            var changed = ((com.fasterxml.jackson.databind.node.ObjectNode) encoded).deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode) changed.get("game")).set("creation_filetime", wrong);
            assertThrows(IOException.class, () -> GameSupervisorControl.decodeStop(ControlBuild.strictMapper().writeValueAsBytes(changed)));
        }
        for (var wrong : List.of(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(42.0),
                com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.booleanNode(true))) {
            var changed = ((com.fasterxml.jackson.databind.node.ObjectNode) encoded).deepCopy();
            ((com.fasterxml.jackson.databind.node.ObjectNode) changed.get("game")).set("pid", wrong);
            assertThrows(IOException.class, () -> GameSupervisorControl.decodeStop(ControlBuild.strictMapper().writeValueAsBytes(changed)));
        }
    }

    private com.fasterxml.jackson.databind.JsonNode publishActualTerminal(GameSupervisor.Completed completed) throws IOException {
        var actual = completed.terminal().actual();
        byte[] raw = GameSupervisor.encodeTerminal(WindowsJobProcess.currentMachineId(), "software-owner", actual.identity(), completed);
        Path file = temporary.resolve("actual-terminal-" + java.util.UUID.randomUUID() + ".json");
        GameSupervisorControl.publish(file, raw, false);
        assertArrayEquals(raw, Files.readAllBytes(file));
        var parsed = StrictJson.parse(Files.readAllBytes(file), 262144);
        var terminal = parsed.get("actual_terminal");
        assertTrue(terminal.get("elapsed_seconds_decimal").isTextual());
        assertEquals(java.math.BigDecimal.valueOf(actual.elapsedSeconds()).toPlainString(), terminal.get("elapsed_seconds_decimal").textValue());
        assertFalse(terminal.has("elapsed_seconds"));
        assertEquals(actual.identity().creationFiletimeDecimal(), terminal.path("identity").path("creation_filetime_decimal").textValue());
        assertEquals(actual.identity().pid(), terminal.path("identity").path("pid").longValue());
        assertEquals(actual.exitCode(), terminal.path("exit_code").intValue());
        var accounting = terminal.get("accounting");
        for(String field : List.of("peak_job_memory_bytes", "active_processes", "memory_limit_bytes", "limit_flags"))
            assertTrue(accounting.get(field).isIntegralNumber());
        assertEquals(actual.accounting().peakJobMemoryBytes(), accounting.get("peak_job_memory_bytes").longValue());
        assertEquals(actual.accounting().activeProcesses(), accounting.get("active_processes").intValue());
        assertEquals(actual.accounting().memoryLimitBytes(), accounting.get("memory_limit_bytes").longValue());
        assertEquals(actual.accounting().limitFlags(), accounting.get("limit_flags").intValue());
        assertEquals(completed.terminal().cleanupProven(), parsed.get("cleanup_proven").booleanValue());
        assertTrue(terminal.has("stop_reason"));
        if(actual.stopReason()==null) assertTrue(terminal.get("stop_reason").isNull());
        else {
            assertTrue(terminal.get("stop_reason").isTextual());
            assertEquals(actual.stopReason(), terminal.get("stop_reason").textValue());
        }
        return parsed;
    }

    @Test void actualTimeoutReasonAndFailedCommandSurviveTheProductionTerminalPublication() throws Exception {
        try(var process=child("wait")) {
            var actual=process.await(Duration.ofMillis(100), Instant.now().plusSeconds(3), () -> { });
            assertEquals(124, actual.exitCode()); assertFalse(actual.passed()); assertNotNull(actual.stopReason());
            boolean cleanup=ManagedGameSession.cleanupProven(process, actual);
            assertTrue(cleanup); assertEquals(0, actual.accounting().activeProcesses());
            var completed=new GameSupervisor.Completed("software-operation-timeout", new GameSupervisor.Terminal(
                    actual,cleanup,GameLifecycle.TerminalKind.DEADLINE,Optional.empty()));
            var parsed=publishActualTerminal(completed);
            assertEquals("DEADLINE", parsed.get("terminal_kind").textValue());
            assertEquals(actual.stopReason(), parsed.get("actual_terminal").get("stop_reason").textValue());
            assertEquals(124, parsed.get("actual_terminal").get("exit_code").intValue());
        }
    }

    private ControlBuild.FileRef ref(String name) {
        return new ControlBuild.FileRef(temporary.resolve(name).toAbsolutePath().toString(), 1, "a".repeat(64));
    }
    @Test void descriptorRoundTripsOriginalConfigurationAndReferencesAsDataWithoutInventingAdmission() throws Exception {
        Instant deadline = Instant.parse("2030-01-01T00:00:00Z");
        var review = new LaunchSourceBinding.Review("software-only", deadline, ref("ck3.exe"), ref("bridge.dll"), ref("injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("env.json"), ref("build.json"), ref("register.json")), temporary, List.of(ref("classes.jar")));
        var profile = new NativeLaunchPlan.PreparedProfile(ref("manifest.json"), temporary.resolve("mod"), "mod/example.mod",
                List.of(ref("input")), List.of(ref("mod/descriptor.mod")));
        var configuration = new NativeLaunchPlanCodec.Configuration("request", "session", review, temporary, temporary.resolve("state"),
                temporary.resolve("evidence"), "\\\\.\\pipe\\software-only", "bridge-v1", "adapter-v1", new NativeLaunchPlan.NewGame(), false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of("SOFTWARE_TEST", "a=b"), 9L << 30, 128L << 20,
                deadline, Duration.ofSeconds(10), Duration.ofMinutes(2), new SteamOfflineProbe.Plan("software-only", ref("steam.exe"), deadline), profile, 128);
        var identity = new WindowsJobProcess.ProcessIdentity(42, "134376718582643410", temporary.resolve("software.exe").toString());
        var actual = new GameSupervisorControl.Descriptor("software-only", "session", identity, identity, configuration,
                new ExactRef(ref("hello.json").path(), 1, "a".repeat(64)), new ExactRef(ref("launch.json").path(), 1, "b".repeat(64)),
                temporary.resolve(GameSupervisorControl.STOP_FILE), temporary.resolve(GameSupervisorControl.TERMINAL_FILE));
        Path file = temporary.resolve(GameSupervisorControl.DESCRIPTOR_FILE);
        GameSupervisorControl.writeDescriptor(file, actual);
        assertEquals(actual, GameSupervisorControl.readDescriptor(file));
        assertEquals("134376718582643410", GameSupervisorControl.readDescriptor(file).generation().creationFiletime().value().toString());
        assertFalse(Files.exists(temporary.resolve("ck3.exe")));
    }
}
