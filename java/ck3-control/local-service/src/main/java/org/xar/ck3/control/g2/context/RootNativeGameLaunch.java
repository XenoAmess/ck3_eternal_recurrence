package org.xar.ck3.control.g2.context;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;
import org.xar.ck3.control.platform.NativeLaunchPolicy;

/** The Root-only new Java Game creator. Constructing a request never starts a process. */
public final class RootNativeGameLaunch {
    public enum Submission { NOT_SUBMITTED, SUBMITTED, EXIT_ZERO_JOB_EMPTY, UNKNOWN }
    public record Request(WindowsJobProcess.CommandSpec game, String pipeName, Path injectorEvidenceRoot,
            Map<String, String> injectorEnvironment, long injectorMemoryBytes, Duration injectorTimeout,
            Instant deadline, RootSteamOfflineGate.Plan steamOfflinePlan) {
        public Request {
            Objects.requireNonNull(game); Objects.requireNonNull(pipeName); Objects.requireNonNull(injectorEvidenceRoot);
            injectorEnvironment = Map.copyOf(injectorEnvironment); Objects.requireNonNull(injectorTimeout); Objects.requireNonNull(deadline);
            if (!pipeName.startsWith("\\\\.\\pipe\\") || pipeName.length() <= 9 || pipeName.length() >= 256
                    || pipeName.chars().anyMatch(c -> c == 0 || Character.isISOControl(c))
                    || !injectorEvidenceRoot.isAbsolute() || !injectorEvidenceRoot.normalize().equals(injectorEvidenceRoot)
                    || injectorMemoryBytes < (64L << 20) || injectorTimeout.isNegative() || injectorTimeout.isZero()
                    || injectorTimeout.compareTo(Duration.ofSeconds(60)) > 0
                    || !pipeName.equals(game.environment().get("XAR_CK3_BRIDGE_PIPE"))
                    || !"native-headless".equals(game.environment().get("XAR_CK3_BRIDGE_MODE"))) {
                throw new IllegalArgumentException("Exact inherited Native pipe and finite original startup injector limits required");
            }
            Objects.requireNonNull(steamOfflinePlan);
        }
    }
    public record LoaderActual(Submission submission, WindowsJobProcess.CommandResult terminal,
            ControlBuild.FileRef stdout, ControlBuild.FileRef stderr) { }
    /** One original attempt; returned terminal survives failures while publishing its evidence. */
    static final class LoaderAttempt {
        private volatile LoaderActual actual = new LoaderActual(Submission.NOT_SUBMITTED, null, null, null);
        LoaderActual current() { return actual; }
        void submit() throws IOException {
            if (actual.submission() != Submission.NOT_SUBMITTED) throw new IOException("Native loader attempt already consumed");
            actual = new LoaderActual(Submission.SUBMITTED, null, null, null);
        }
        void unknown() {
            actual = new LoaderActual(Submission.UNKNOWN, actual.terminal(), actual.stdout(), actual.stderr());
        }
        /** The live await consumer and physical evidence-failure regressions use this same path. */
        void complete(WindowsJobProcess.CommandResult terminal, Path receipt, Path stdout, Path stderr) throws IOException {
            if (actual.submission() != Submission.SUBMITTED || actual.terminal() != null)
                throw new IOException("One returned terminal for the original submitted loader required");
            // Keep original exit/timeout/whole-Job observation before any fallible disk operation.
            actual = new LoaderActual(Submission.UNKNOWN, Objects.requireNonNull(terminal), null, null);
            Files.write(receipt, ControlBuild.strictMapper().writeValueAsBytes(terminal), StandardOpenOption.CREATE_NEW);
            ControlBuild.FileRef out = ControlBuild.FileRef.measure(stdout);
            actual = new LoaderActual(Submission.UNKNOWN, terminal, out, null);
            ControlBuild.FileRef err = ControlBuild.FileRef.measure(stderr);
            actual = new LoaderActual(terminal.passed() ? Submission.EXIT_ZERO_JOB_EMPTY : Submission.UNKNOWN, terminal, out, err);
            if (!terminal.passed()) throw new IOException("Native loader terminal is unsuccessful/UNKNOWN; no repeated submission");
        }
    }
    /** Genuine retained resources, not a reconstructible Game DTO or an adopted Python SessionHandle. */
    public static final class OwnedGame implements AutoCloseable {
        private final RootNativeRuntimeBinding runtime;
        private final Request request;
        private final WindowsJobProcess creator;
        private final WindowsPreloadCustody.Lease custody;
        private final LoaderActual loader;
        private boolean closed;
        private OwnedGame(RootNativeRuntimeBinding runtime, Request request, WindowsJobProcess creator,
                WindowsPreloadCustody.Lease custody, LoaderActual loader) {
            this.runtime = runtime; this.request = request; this.creator = creator; this.custody = custody; this.loader = loader;
        }
        public WindowsJobProcess.ProcessIdentity identity() { return creator.identity(); }
        public LoaderActual loader() { return loader; }
        public String pipeName() { return request.pipeName(); }
        public Instant deadline() { return request.deadline(); }
        public WindowsPreloadCustody.Lease custody() { return custody; }
        public RootNativeRuntimeBinding runtime() { return runtime; }
        public synchronized void verify() throws IOException {
            if (closed || !Instant.now().isBefore(request.deadline())) throw new IOException("Original Java Game custody closed or expired");
            runtime.verify(); custody.verify();
            if (!creator.identity().equals(custody.targetIdentity()) || !creator.isRunning()) throw new IOException("Original held Game process differs or exited");
        }
        /** Closing is an explicit owner operation on the original Job; it is never used to retry loading. */
        @Override public synchronized void close() { if (!closed) { closed = true; creator.close(); } }
    }
    private final RootNativeRuntimeBinding runtime;
    private final Request request;
    private final AtomicBoolean submitted = new AtomicBoolean();
    private final LoaderAttempt loader = new LoaderAttempt();
    public RootNativeGameLaunch(RootNativeRuntimeBinding runtime, Request request) {
        this.runtime = Objects.requireNonNull(runtime); this.request = Objects.requireNonNull(request);
    }
    public LoaderActual loaderActual() { return loader.current(); }

    /** Explicit Root execution point; no agent calls this during source/software qualification. */
    public OwnedGame launch() throws IOException {
        if (!submitted.compareAndSet(false, true)) throw new IOException("Root Game launch is one-shot; UNKNOWN is never replayed");
        runtime.verify();
        if (!request.game().executable().toRealPath().equals(Path.of(runtime.request().gameExecutable().path()).toRealPath())
                || !request.deadline().isAfter(Instant.now()) || request.deadline().isAfter(runtime.request().reviewAt())) {
            throw new IOException("New Game creation differs from exact accepted Root launch binding");
        }
        runtime.request().gameExecutable().verify();
        NativeLaunchPolicy.requireGameCommand(request.game(), request.pipeName(),
                List.of(request.injectorEvidenceRoot()), request.deadline());
        NativeLaunchPolicy.requireOutputLocations(List.of(request.injectorEvidenceRoot()),
                request.injectorEnvironment(), request.deadline());
        SharedSourceFiles.plainAncestors(request.injectorEvidenceRoot()); Files.createDirectory(request.injectorEvidenceRoot());
        RootSteamOfflineGate.QualifiedOffline offline = RootSteamOfflineGate.observe(runtime, request.steamOfflinePlan());
        offline.consumeBeforeGameCreate(runtime);
        NativeLaunchPolicy.requireGameCommand(request.game(), request.pipeName(),
                List.of(request.injectorEvidenceRoot()), request.deadline());
        AtomicReference<WindowsPreloadCustody.Lease> retained = new AtomicReference<>();
        WindowsJobProcess creator = WindowsJobProcess.start(request.game(), WindowsJobProcess.ConsoleMode.NO_WINDOW, target -> {
            WindowsPreloadCustody.Lease lease = WindowsPreloadCustody.prepare(target,
                    new WindowsPreloadCustody.DllRef(runtime.request().nativeDll(), request.deadline(), runtime::verify));
            if (!retained.compareAndSet(null, lease)) { lease.close(); throw new IOException("Original Game pre-resume callback repeated"); }
            try {
                // This is the ORIGINAL cold path: no --pipe means PrepareStartup BEFORE primary resume.
                loadStartupOnce(lease); lease.observeLoaded(); return lease;
            } catch (IOException | RuntimeException failure) {
                try { lease.close(); } catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
                throw failure;
            }
        });
        WindowsPreloadCustody.Lease lease = retained.get();
        if (lease == null || loader.current().submission() != Submission.EXIT_ZERO_JOB_EMPTY) {
            creator.close(); throw new IOException("Original Game did not retain successful preload resources");
        }
        OwnedGame result = new OwnedGame(runtime, request, creator, lease, loader.current());
        try { result.verify(); return result; } catch (IOException | RuntimeException failure) { result.close(); throw failure; }
    }
    private void loadStartupOnce(WindowsPreloadCustody.Lease lease) throws IOException {
        if (loader.current().submission() != Submission.NOT_SUBMITTED) throw new IOException("Native loader attempt already consumed");
        runtime.verify(); lease.verify();
        Path root = request.injectorEvidenceRoot(), stdout = root.resolve("stdout.log"), stderr = root.resolve("stderr.log");
        NativeLaunchPolicy.requireOutputLocations(List.of(root, stdout, stderr),
                request.injectorEnvironment(), request.deadline());
        List<String> arguments = List.of(Long.toString(lease.targetIdentity().pid()), runtime.request().nativeDll().path());
        WindowsJobProcess.CommandSpec command = new WindowsJobProcess.CommandSpec(Path.of(runtime.request().injector().path()),
                arguments, root, request.injectorEnvironment(), stdout, stderr, request.injectorMemoryBytes());
        Files.write(root.resolve("argv.json"), ControlBuild.strictMapper().writeValueAsBytes(command), StandardOpenOption.CREATE_NEW);
        loader.submit();
        try (WindowsJobProcess injector = WindowsJobProcess.start(command)) {
            WindowsJobProcess.CommandResult actual = injector.await(request.injectorTimeout(), request.deadline(), () -> {
                try { runtime.verify(); lease.verify(); } catch (IOException failure) { throw new IllegalStateException(failure); }
            });
            loader.complete(actual, root.resolve("terminal.json"), stdout, stderr);
            runtime.verify(); lease.verify();
        } catch (InterruptedException failure) {
            Thread.currentThread().interrupt(); loader.unknown();
            throw new IOException("Native loader wait interrupted after submission; no retry", failure);
        } catch (IOException | RuntimeException failure) {
            loader.unknown(); throw failure;
        }
    }
}
