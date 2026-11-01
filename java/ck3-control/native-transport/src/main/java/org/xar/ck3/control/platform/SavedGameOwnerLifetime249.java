package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.GameLifecycle;

/**
 * Bridges a genuine original {@code JavaGameLifecycle.Started} session to the existing
 * {@code GameSupervisor} owner loop without launching or admitting the Game; only the existing explicit STOP/natural-exit path may stop it.
 * The retained handle is closed only after the owner loop completes; the original
 * ManagedGameSession and its resources remain untouched by this adapter.
 */
public final class SavedGameOwnerLifetime249 {
    private SavedGameOwnerLifetime249() { }
    private static void reject(String detail) {
        System.err.println("Game owner observation/request rejected: "+detail.substring(0,Math.min(2048,detail.length())));
    }

    public static Retained retain(JavaGameLifecycle creator, JavaGameLifecycle.Started original, Path freshOwnerDirectory) throws IOException {
        Objects.requireNonNull(creator);
        Objects.requireNonNull(original);
        Objects.requireNonNull(freshOwnerDirectory);

        // Validate that the creator actually owns this exact Started result.
        if (creator.query(original.session().launchPlan().requestId()) != original) {
            throw new IOException("Creator does not retain this exact Started result");
        }
        if (creator.currentSession().orElse(null) != original.session()) {
            throw new IOException("Creator current session is not this Started session");
        }

        ManagedGameSession session = original.session();
        if (session.mode() != ManagedGameSession.Mode.OWNED) {
            throw new IOException("Started session must be OWNED");
        }
        if (!(session.launchPlan().load() instanceof NativeLaunchPlan.SavedGame)) {
            throw new IOException("Started session must be a SavedGame launch");
        }

        // Verify the session is still live and valid.
        session.verify();

        // Ensure the owner directory is fresh (absent).
        Path directory = freshOwnerDirectory;
        if(!directory.isAbsolute()||!directory.normalize().equals(directory))throw new IOException("absolute normalized owner directory required");
        if (Files.exists(directory)) {
            throw new IOException("Owner directory must be absent");
        }
        Files.createDirectory(directory);

        // Acquire a read-only process handle for the Game PID to bind identity.
        WindowsJobProcess.ReadOnlyProcessHandle observed = WindowsJobProcess.retainReadOnlyProcess(session.identity().pid());
        try {
            if (!session.identity().equals(observed.identity())) {
                throw new IOException("Observer acquired a different Game generation");
            }

            // Get the supervisor's own identity for the descriptor.
            WindowsJobProcess.ProcessIdentity supervisorIdentity = selfIdentity();

            // Build and write the owner descriptor using existing GameSupervisorControl.
            Path stopPath = directory.resolve(GameSupervisorControl.STOP_FILE);
            Path terminalPath = directory.resolve(GameSupervisorControl.TERMINAL_FILE);

            GameSupervisorControl.Descriptor descriptor = new GameSupervisorControl.Descriptor(
                    session.machineId(),
                    session.sessionId(),
                    supervisorIdentity,
                    session.identity(),
                    NativeLaunchPlanCodec.describe(session.launchPlan()),
                    original.nativeHello(),
                    original.launchEvidence(),
                    stopPath,
                    terminalPath
            );
            GameSupervisorControl.writeDescriptor(directory.resolve(GameSupervisorControl.DESCRIPTOR_FILE), descriptor);

            // Create the Owner interface implementation that delegates to the session.
            GameSupervisor.Owner owner = new GameSupervisor.Owner() {
                @Override public String sessionId() { return session.sessionId(); }
                @Override public WindowsJobProcess.ProcessIdentity identity() { return session.identity(); }
                @Override public boolean running() throws IOException {
                    long wait = observed.waitZero();
                    if (wait == 258) return true;
                    if (wait == 0) return false;
                    throw new IOException("unexpected held Game wait state " + wait);
                }
                @Override public GameSupervisor.Terminal stop(Instant deadline, GameLifecycle.TerminalKind kind) throws IOException, InterruptedException {
                    var actual = session.stop(session.generation(), deadline, false, kind);
                    return new GameSupervisor.Terminal(actual.terminal(), actual.cleanupProven(), actual.kind(), Optional.of(actual.evidence()));
                }
            };

            return new Retained(creator, original, observed, owner, directory);
        } catch (IOException | RuntimeException failure) {
            // On failure, close only the newly acquired read-only handle.
            try { observed.close(); } catch (RuntimeException cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        }
    }

    private static WindowsJobProcess.ProcessIdentity selfIdentity() {
        try (var actual = WindowsJobProcess.retainReadOnlyProcess(ProcessHandle.current().pid())) {
            return actual.identity();
        }
    }

    public static final class Retained {
        private final JavaGameLifecycle creator;
        private final JavaGameLifecycle.Started original;
        private final WindowsJobProcess.ReadOnlyProcessHandle observed;
        private final GameSupervisor.Owner owner;
        private final Path directory;
        private boolean awaited = false;

        private Retained(JavaGameLifecycle creator, JavaGameLifecycle.Started original,
                       WindowsJobProcess.ReadOnlyProcessHandle observed,
                       GameSupervisor.Owner owner, Path directory) {
            this.creator = creator;
            this.original = original;
            this.observed = observed;
            this.owner = owner;
            this.directory = directory;
        }

        public synchronized int awaitExit() throws IOException, InterruptedException {
            if (awaited) throw new IllegalStateException("awaitExit is single-use");
            awaited = true;

            Path stopPath = directory.resolve(GameSupervisorControl.STOP_FILE);
            Path terminalPath = directory.resolve(GameSupervisorControl.TERMINAL_FILE);
            ManagedGameSession session = original.session();
            NativeLaunchPlan plan = session.launchPlan();

            try (observed) {
                if(creator.query(plan.requestId())!=original||creator.currentSession().orElse(null)!=session)
                    throw new IOException("original Saved creator changed before owner wait");
                // Reuse the exact existing GameSupervisor.awaitOwner loop.
                var completed = GameSupervisor.awaitOwner(owner, stopPath, SavedGameOwnerLifetime249::reject);
                var actual = completed.terminal();

                // Encode and publish the terminal using existing GameSupervisor helpers.
                byte[] terminalBytes = GameSupervisor.encodeTerminal(
                        plan.sources().review().machineId(),
                        plan.sessionId(),
                        session.identity(),
                        completed
                );
                GameSupervisorControl.publish(terminalPath, terminalBytes, false);

                // Mirror existing return semantics from GameSupervisor.run.
                if (!actual.cleanupProven()) return 1;
                return actual.kind() == GameLifecycle.TerminalKind.NATURAL_EXIT && actual.actual().exitCode() != 0 ? 1 : 0;
            } catch (IOException | RuntimeException failure) {
                // Publish unknown terminal on failure, mirroring GameSupervisor.run.
                var unknown = StrictJson.object().put("schema","xar.java-game-supervisor-result/v1")
                        .put("machine_id",plan.sources().review().machineId()).put("session_id",plan.sessionId())
                        .put("observed_at_utc",Instant.now().toString()).put("status","OWNER_TERMINAL_UNKNOWN");
                unknown.set("game", GameSupervisorControl.identity(session.identity()));
                String detail=failure.toString();unknown.put("detail",detail.substring(0,Math.min(2048,detail.length())));
                try {GameSupervisorControl.publish(terminalPath, StrictJson.canonical(unknown, 65536), false);}
                catch(IOException|RuntimeException recordingFailure) {
                    if(recordingFailure!=failure)failure.addSuppressed(recordingFailure);
                }
                throw failure;
            }
        }
    }
}