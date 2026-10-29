package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Consumer;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Independent physical owner JVM. Start it outside every business worker Job.
 * Worker exits and pipe disconnects are not owner STOP commands.
 */
public final class GameSupervisor {
    record Terminal(WindowsJobProcess.CommandResult actual, boolean cleanupProven,
            GameLifecycle.TerminalKind kind, Optional<ExactRef> evidence) {
        Terminal {
            Objects.requireNonNull(actual); Objects.requireNonNull(kind); evidence = Objects.requireNonNull(evidence);
        }
    }
    record Completed(String requestId, Terminal terminal) { }
    record TerminalWire(WindowsJobProcess.ProcessIdentity identity, int exitCode, String elapsedSecondsDecimal,
            WindowsJobProcess.Accounting accounting, String stopReason) { }

    /** The same owner loop is exercised with real ordinary software Job resources in tests. */
    interface Owner {
        String sessionId();
        WindowsJobProcess.ProcessIdentity identity();
        boolean running() throws IOException;
        Terminal stop(Instant deadline, GameLifecycle.TerminalKind kind) throws IOException, InterruptedException;
    }

    private GameSupervisor() { }

    /** Start: configuration owner-directory. STOP: stop owner.json request-id timeout-seconds. */
    public static void main(String... args) throws Exception {
        if (args.length == 4 && args[0].equals("stop")) {
            var descriptor = GameSupervisorControl.readDescriptor(Path.of(args[1]));
            long seconds = Long.parseLong(args[3]);
            if (seconds < 1 || seconds > 300) throw new IllegalArgumentException("finite STOP timeout 1..300 seconds required");
            GameSupervisorControl.writeStop(descriptor.stopRequestPath(), new GameSupervisorControl.StopRequest(
                    args[2], descriptor.sessionId(), descriptor.gameIdentity(), Instant.now().plusSeconds(seconds)));
            System.out.println("STOP_REQUEST_PUBLISHED");
            return;
        }
        if (args.length != 2) throw new IllegalArgumentException(
                "GameSupervisor requires ordinary-configuration and absent-owner-directory, or stop owner.json request-id timeout-seconds");
        int status = run(Path.of(args[0]), Path.of(args[1]));
        if (status != 0) System.exit(status);
    }

    public static int run(Path configuration, Path ownerDirectory) throws IOException, InterruptedException {
        Path directory = ownerDirectory.toAbsolutePath().normalize();
        Files.createDirectory(directory);
        var document = StrictJson.parse(GameSupervisorControl.readBounded(configuration, NativeLaunchPlanCodec.MAXIMUM_BYTES),
                NativeLaunchPlanCodec.MAXIMUM_BYTES);
        var body = document.has("configuration") ? document.get("configuration") : document;
        NativeLaunchPlan plan = NativeLaunchPlanCodec.fromJson(body).accept();
        JavaGameLifecycle lifecycle = new JavaGameLifecycle(List.of());
        var launched = plan.load() instanceof NativeLaunchPlan.SavedGame
                ? lifecycle.launchSaved(plan) : lifecycle.launchNew(plan);
        if (!(launched instanceof JavaGameLifecycle.Started started)) {
            ObjectNode failure = base(plan, "LAUNCH_NOT_STARTED");
            failure.put("detail", bounded(launched.toString()));
            GameSupervisorControl.publish(directory.resolve(GameSupervisorControl.TERMINAL_FILE),
                    StrictJson.canonical(failure, 65536), false);
            emit(failure);
            return launched instanceof JavaGameLifecycle.Unknown ? 3 : 2;
        }
        ManagedGameSession session = started.session();
        // This closes only the startup communication endpoint. The original Game Job stays owned here.
        session.nativeTransport().close();
        var supervisorIdentity = selfIdentity();
        Path stop = directory.resolve(GameSupervisorControl.STOP_FILE);
        Path terminalPath = directory.resolve(GameSupervisorControl.TERMINAL_FILE);
        try (var observed = WindowsJobProcess.retainReadOnlyProcess(session.identity().pid())) {
            if (!session.identity().equals(observed.identity())) throw new IOException("observer acquired a different Game generation");
            var descriptor = new GameSupervisorControl.Descriptor(session.machineId(), session.sessionId(),
                    supervisorIdentity, session.identity(), NativeLaunchPlanCodec.describe(plan),
                    started.nativeHello(), started.launchEvidence(), stop, terminalPath);
            GameSupervisorControl.writeDescriptor(directory.resolve(GameSupervisorControl.DESCRIPTOR_FILE), descriptor);
            ObjectNode ready = base(plan, "GAME_OWNER_READY");
            ready.set("game", GameSupervisorControl.identity(session.identity()));
            ready.put("descriptor_path", directory.resolve(GameSupervisorControl.DESCRIPTOR_FILE).toString());
            ready.put("launch_pipe_released", true);
            emit(ready);
            Owner owner = new Owner() {
                @Override public String sessionId() { return session.sessionId(); }
                @Override public WindowsJobProcess.ProcessIdentity identity() { return session.identity(); }
                @Override public boolean running() throws IOException {
                    long wait = observed.waitZero();
                    if (wait == 258) return true;
                    if (wait == 0) return false;
                    throw new IOException("unexpected held Game wait state " + wait);
                }
                @Override public Terminal stop(Instant deadline, GameLifecycle.TerminalKind kind)
                        throws IOException, InterruptedException {
                    var actual = session.stop(session.generation(), deadline, false, kind);
                    return new Terminal(actual.terminal(), actual.cleanupProven(), actual.kind(), Optional.of(actual.evidence()));
                }
            };
            try {
                Completed completed = awaitOwner(owner, stop, GameSupervisor::reject);
                Terminal actual = completed.terminal();
                byte[] terminalBytes = encodeTerminal(plan.sources().review().machineId(),
                        plan.sessionId(), session.identity(), completed);
                GameSupervisorControl.publish(terminalPath, terminalBytes, false);
                emit(terminalBytes);
                if (!actual.cleanupProven()) return 1;
                return actual.kind() == GameLifecycle.TerminalKind.NATURAL_EXIT && actual.actual().exitCode() != 0 ? 1 : 0;
            } catch (IOException | RuntimeException failure) {
                ObjectNode unknown = base(plan, "OWNER_TERMINAL_UNKNOWN");
                unknown.set("game", GameSupervisorControl.identity(session.identity()));
                unknown.put("detail", bounded(failure.toString()));
                GameSupervisorControl.publish(terminalPath, StrictJson.canonical(unknown, 65536), false);
                emit(unknown);
                throw failure;
            }
        }
    }

    /** No launch deadline, worker liveness test, native pipe call, or process-tree scan exists in this loop. */
    static Completed awaitOwner(Owner owner, Path stopPath, Consumer<String> rejected)
            throws IOException, InterruptedException {
        Objects.requireNonNull(owner); Objects.requireNonNull(stopPath); Objects.requireNonNull(rejected);
        byte[] previouslyRead = null;
        String previousObservationFailure = null;
        for (;;) {
            GameSupervisorControl.StopRequest command = null;
            try {
                byte[] raw = GameSupervisorControl.readBounded(stopPath, GameSupervisorControl.MAXIMUM_STOP_BYTES);
                if (!Arrays.equals(previouslyRead, raw)) {
                    previouslyRead = raw;
                    command = GameSupervisorControl.decodeStop(raw);
                    command.requireTarget(owner.sessionId(), owner.identity(), Instant.now());
                }
            } catch (NoSuchFileException absent) {
                previouslyRead = null;
            } catch (IOException | RuntimeException invalid) {
                command = null;
                rejected.accept(bounded(invalid.toString()));
            }
            if (command != null) {
                // Preserve the caller's operation deadline; a STOP failure never becomes a successful terminal.
                return new Completed(command.requestId(), owner.stop(command.deadline(), GameLifecycle.TerminalKind.OWNER_STOP));
            }
            Boolean running = null;
            try {
                running = owner.running();
                previousObservationFailure = null;
            } catch (IOException | RuntimeException unavailable) {
                String message = bounded(unavailable.toString());
                if (!message.equals(previousObservationFailure)) rejected.accept(message);
                previousObservationFailure = message;
            }
            if (Boolean.FALSE.equals(running))
                return new Completed("", owner.stop(Instant.now().plusSeconds(25), GameLifecycle.TerminalKind.NATURAL_EXIT));
            // An interrupted wait is not a business-worker STOP request either.
            try { Thread.sleep(250); }
            catch (InterruptedException interrupted) { rejected.accept("owner polling interrupted; no STOP was requested"); }
        }
    }

    private static WindowsJobProcess.ProcessIdentity selfIdentity() {
        try (var actual = WindowsJobProcess.retainReadOnlyProcess(ProcessHandle.current().pid())) { return actual.identity(); }
    }
    private static ObjectNode base(NativeLaunchPlan plan, String status) {
        return base(plan.sources().review().machineId(), plan.sessionId(), status);
    }
    private static ObjectNode base(String machineId, String sessionId, String status) {
        return StrictJson.object().put("schema", "xar.java-game-supervisor-result/v1")
                .put("machine_id", machineId).put("session_id", sessionId)
                .put("observed_at_utc", Instant.now().toString()).put("status", status);
    }
    private static String bounded(String detail) { return detail.substring(0, Math.min(2048, detail.length())); }
    private static void reject(String detail) { System.err.println("Game owner observation/request rejected: " + bounded(detail)); }
    private static void emit(ObjectNode value) throws IOException {
        emit(StrictJson.canonical(value, 262144));
    }
    private static void emit(byte[] value) throws IOException {
        System.out.write(value); System.out.write(10); System.out.flush();
        // The independently retained owner files carry the result even if an observer closes stdout.
    }

    static byte[] encodeTerminal(String machineId, String sessionId, WindowsJobProcess.ProcessIdentity actualGame, Completed completed) {
        var result = base(machineId, sessionId, completed.terminal().kind() == GameLifecycle.TerminalKind.NATURAL_EXIT
                ? "GAME_EXITED" : "OWNER_STOP_COMPLETED");
        result.put("stop_request_id", completed.requestId());
        result.put("cleanup_proven", completed.terminal().cleanupProven());
        result.put("terminal_kind", completed.terminal().kind().name());
        result.set("game", GameSupervisorControl.identity(actualGame));
        var wire = new TerminalWire(completed.terminal().actual().identity(), completed.terminal().actual().exitCode(),
                java.math.BigDecimal.valueOf(completed.terminal().actual().elapsedSeconds()).toPlainString(),
                completed.terminal().actual().accounting(), completed.terminal().actual().stopReason());
        result.set("actual_terminal", ControlBuild.strictMapper().valueToTree(wire));
        result.set("evidence", ExactRef.optionalToJson(completed.terminal().evidence()));
        return StrictJson.canonical(result, 262144);
    }
}
