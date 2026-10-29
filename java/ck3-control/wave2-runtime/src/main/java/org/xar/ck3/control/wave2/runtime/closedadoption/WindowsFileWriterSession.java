package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Concrete suspended-before-assignment original writer transport using the shared Win32 Job owner. */
public final class WindowsFileWriterSession implements OriginalWriterTransaction.ManagedProcess {
    /** Preserve the historical writer and cold byte budgets; Root operations use their own finite profile. */
    static final long MAX_WRITER_STREAM_BYTES = 2L * (OriginalWriterTransaction.MAX_PROTOCOL_BYTES + 1);
    static final long MAX_COLD_CONSUMER_STREAM_BYTES = 2L * (RecoveryEvidence.MAX_BYTES + 1);
    /** Root operations permit at most 32 small callbacks plus one separately bounded terminal frame. */
    static final long MAX_ROOT_OPERATION_STREAM_BYTES =
            OriginalColdConsumerSession.MAX_CALLBACKS_PER_OPERATION * (RecoveryEvidence.MAX_BYTES + 1L)
                    + OriginalWriterTransaction.MAX_PROTOCOL_BYTES + 1L;
    public enum Mode {
        WRITER("writer",MAX_WRITER_STREAM_BYTES),
        COLD_CONSUMER("cold_consumer",MAX_COLD_CONSUMER_STREAM_BYTES),
        ROOT_OPERATION("cold_consumer",MAX_ROOT_OPERATION_STREAM_BYTES);
        private final String wire;
        private final long maximumStreamBytes;
        Mode(String wire, long maximumStreamBytes) { this.wire = wire; this.maximumStreamBytes = maximumStreamBytes; }
    }
    public record Settings(Path python, Path repo, Path outputRoot, long memoryLimitBytes, Duration timeout,
            Instant leaseDeadline, Map<String, String> environment, ExactRef mechanicalSource, ExactRef coldOwnerSource,
            Runnable capacityGuard) {
        public Settings {
            Objects.requireNonNull(python); Objects.requireNonNull(repo); Objects.requireNonNull(outputRoot);
            Objects.requireNonNull(timeout); Objects.requireNonNull(leaseDeadline); environment = Map.copyOf(environment);
            Objects.requireNonNull(mechanicalSource); Objects.requireNonNull(coldOwnerSource);
            Objects.requireNonNull(capacityGuard);
            StrictJson.require(python.isAbsolute() && repo.isAbsolute() && outputRoot.isAbsolute()
                    && memoryLimitBytes > 0 && memoryLimitBytes <= 512L * 1024 * 1024
                    && timeout.toMillis() > 0 && timeout.toMillis() <= 120_000, "finite actual Root-owned Python Job settings");
            StrictJson.require(Path.of(mechanicalSource.path()).equals(repo.resolve("tools/g2_saved_campaign/current_saved_continuity_v1.py"))
                    && Path.of(coldOwnerSource.path()).equals(repo.resolve("tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py")), "fixed source-bound existing Python modules");
        }
    }
    private static final String BOOTSTRAP = """
            import sys,types,hashlib
            from pathlib import Path
            def original(name,path,size,sha):
                raw=Path(path).read_bytes()
                if len(raw)!=int(size) or hashlib.sha256(raw).hexdigest()!=sha:
                    raise ValueError('original existing-module source drift')
                module=types.ModuleType(name)
                module.__file__=path
                module.__package__='tools.g2_saved_campaign'
                sys.modules[name]=module
                exec(compile(raw,path,'exec'),module.__dict__)
                return module
            transport=original('tools.g2_saved_campaign.current_saved_continuity_v1',*sys.argv[1:4])
            if sys.argv[8]=='cold_consumer':
                original('tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1',*sys.argv[4:7])
            raise SystemExit(transport.serve_java_closed_partial_file_session_v1(request_path=Path(sys.argv[7]),mode=sys.argv[8],timeout_ms=int(sys.argv[9])))
            """;
    private final WindowsJobProcess job;
    private final Settings settings;
    private final Mode mode;
    private final long maximumStreamBytes;
    private final Path requestPath, stdoutPath, stderrPath, eofPath, terminalPath;
    private final OutputStream requests;
    private final InputStream replies;
    private final long started = System.nanoTime();
    private WindowsJobProcess.CommandResult actual;
    private Throwable terminalFailure;
    private boolean terminalConsumed;
    private boolean inputClosed;

    private WindowsFileWriterSession(Settings settings, Mode mode) throws IOException {
        this.settings = settings; this.mode = mode;
        maximumStreamBytes = mode.maximumStreamBytes;
        settings.capacityGuard().run(); Files.createDirectories(settings.outputRoot());
        requestPath = Files.createTempFile(settings.outputRoot(), "closed-partial-" + mode.wire + "-", ".request.jsonl");
        stdoutPath = requestPath.resolveSibling(requestPath.getFileName() + ".stdout.jsonl");
        stderrPath = requestPath.resolveSibling(requestPath.getFileName() + ".stderr.log");
        eofPath = requestPath.resolveSibling(requestPath.getFileName() + ".closed");
        terminalPath = requestPath.resolveSibling(requestPath.getFileName() + ".terminal.json");
        requests = Files.newOutputStream(requestPath, StandardOpenOption.APPEND);
        WindowsJobProcess startedJob;
        try {
            startedJob = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(settings.python(),
                    List.of("-B", "-u", "-X", "utf8", "-c", BOOTSTRAP,
                            settings.mechanicalSource().path(),Long.toString(settings.mechanicalSource().bytes()),settings.mechanicalSource().sha256(),
                            settings.coldOwnerSource().path(),Long.toString(settings.coldOwnerSource().bytes()),settings.coldOwnerSource().sha256(),
                            requestPath.toString(), mode.wire, Long.toString(settings.timeout().toMillis())),
                    settings.repo(), settings.environment(), stdoutPath, stderrPath, settings.memoryLimitBytes()));
        } catch (IOException | RuntimeException error) { requests.close(); throw error; }
        job = startedJob;
        try { replies = new ReplyStream(); }
        catch (IOException error) { requests.close(); job.close(); throw error; }
    }
    public static WindowsFileWriterSession start(Settings settings, Mode mode) throws IOException {
        Objects.requireNonNull(settings); Objects.requireNonNull(mode);
        StrictJson.require(Instant.now().isBefore(settings.leaseDeadline()), "actual Root lease has not expired");
        return new WindowsFileWriterSession(settings, mode);
    }
    @Override public InputStream stdout() { return replies; }
    @Override public OutputStream stdin() { return requests; }
    @Override public void closeOwnedInput() throws IOException {
        if (!inputClosed) { inputClosed = true; requests.close(); Files.writeString(eofPath, "EOF\n", StandardOpenOption.CREATE_NEW); }
    }
    @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException, InterruptedException {
        if (!terminalConsumed) {
            terminalConsumed = true;
            Throwable failure = null;
            try {
                actual = job.await(settings.timeout(), settings.leaseDeadline(), this::guard);
                guard();
            } catch (RuntimeException error) {
                failure = new IOException("original writer transport guard failed; actual terminal retained", error);
            } catch (InterruptedException | Error error) {
                failure = error;
            }
            if (actual == null) {
                try { job.terminate(31); }
                catch (RuntimeException | Error cleanup) { failure = retain(failure,cleanup); }
                try { actual = job.await(Duration.ofSeconds(5), Instant.now().plusSeconds(5), () -> { }); }
                catch (InterruptedException cleanup) { Thread.currentThread().interrupt(); failure = retain(failure,cleanup); }
                catch (RuntimeException | Error cleanup) { failure = retain(failure,cleanup); }
            }
            try { if (actual != null) { persistTerminal(actual); } }
            catch (IOException | RuntimeException | Error cleanup) { failure = retain(failure,cleanup); }
            try { replies.close(); }
            catch (IOException | RuntimeException | Error cleanup) { failure = retain(failure,cleanup); }
            try { job.close(); }
            catch (RuntimeException | Error cleanup) { failure = retain(failure,cleanup); }
            terminalFailure = failure;
        }
        rethrowTerminalFailure();
        var result = Objects.requireNonNull(actual);
        if (!result.passed()) {
            terminalFailure = new IOException("original writer actual Job did not pass: exit=" + result.exitCode()
                    + ", stop_reason=" + result.stopReason() + ", active=" + result.accounting().activeProcesses());
            rethrowTerminalFailure();
        }
        if (System.nanoTime() - started >= settings.timeout().toNanos() || !Instant.now().isBefore(settings.leaseDeadline())) {
            terminalFailure = new IOException("actual original writer session deadline expired before successful return");
            rethrowTerminalFailure();
        }
        return new OriginalWriterTransaction.ActualExit(result.identity().pid(), result.identity().creationFiletimeDecimal(),
                result.exitCode(), true);
    }
    private static Throwable retain(Throwable primary, Throwable cleanup) {
        if (primary == null) { return cleanup; }
        if (primary != cleanup) { primary.addSuppressed(cleanup); }
        return primary;
    }
    private void rethrowTerminalFailure() throws IOException, InterruptedException {
        if (terminalFailure instanceof IOException error) { throw error; }
        if (terminalFailure instanceof InterruptedException error) { Thread.currentThread().interrupt(); throw error; }
        if (terminalFailure instanceof RuntimeException error) { throw error; }
        if (terminalFailure instanceof Error error) { throw error; }
    }
    public Optional<WindowsJobProcess.CommandResult> actualCommandResult() { return Optional.ofNullable(actual); }
    public Path stderrPath() { return stderrPath; }
    public Path stdoutPath() { return stdoutPath; }
    public Path terminalPath() { return terminalPath; }
    private void persistTerminal(WindowsJobProcess.CommandResult result) throws IOException {
        var row = StrictJson.object(); row.put("schema","xar.closed-partial-original-process-terminal/v1");
        row.put("machine_id",WindowsJobProcess.currentMachineId()); row.put("observed_at_utc",Instant.now().toString());
        row.put("pid",result.identity().pid()); row.put("creation_filetime",result.identity().creationFiletimeDecimal());
        row.put("executable",result.identity().executable()); row.put("exit_code",result.exitCode());
        row.put("elapsed_seconds",result.elapsedSeconds()); row.put("active_processes",result.accounting().activeProcesses());
        row.put("peak_job_memory_bytes",result.accounting().peakJobMemoryBytes()); row.put("memory_limit_bytes",result.accounting().memoryLimitBytes());
        row.put("protocol_profile",mode.name()); row.put("protocol_stream_limit_bytes",maximumStreamBytes);
        row.put("limit_flags",result.accounting().limitFlags());
        if (result.stopReason()==null) { row.putNull("stop_reason"); } else { row.put("stop_reason",result.stopReason()); }
        row.set("mechanical_source",settings.mechanicalSource().toJson()); row.set("cold_owner_source",settings.coldOwnerSource().toJson());
        if (!Files.exists(terminalPath)) { Files.write(terminalPath,ClosedAdoptionJson.encode(row),StandardOpenOption.CREATE_NEW); }
    }
    private void guard() {
        try {
            settings.capacityGuard().run();
            StrictJson.require(Files.size(requestPath) <= maximumStreamBytes && Files.size(stdoutPath) <= maximumStreamBytes
                    && Files.size(stderrPath) <= 1_048_576, "finite original-writer transport files");
        } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
    }
    private final class ReplyStream extends InputStream {
        private final RandomAccessFile file = new RandomAccessFile(stdoutPath.toFile(), "r");
        private final byte[] buffer = new byte[8192];
        private int offset, length;
        ReplyStream() throws IOException { }
        @Override public int read() throws IOException {
            while (true) {
                if (offset < length) { return Byte.toUnsignedInt(buffer[offset++]); }
                guard();
                length = file.read(buffer); offset = 0;
                if (length > 0) { continue; }
                if (!job.isRunning()) { return -1; }
                if (System.nanoTime() - started >= settings.timeout().toNanos() || !Instant.now().isBefore(settings.leaseDeadline())) {
                    job.terminate(31); throw new IOException("actual original writer session deadline expired");
                }
                try { Thread.sleep(10); }
                catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new IOException("original writer session interrupted", error); }
            }
        }
        @Override public void close() throws IOException { file.close(); }
    }
}
