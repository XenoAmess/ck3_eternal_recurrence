package org.xar.ck3.control.build;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.Pointer;
import com.sun.jna.Structure;
import com.sun.jna.WString;
import com.sun.jna.platform.win32.Advapi32Util;
import com.sun.jna.platform.win32.BaseTSD.SIZE_T;
import com.sun.jna.platform.win32.BaseTSD.ULONG_PTR;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinDef.DWORD;
import com.sun.jna.platform.win32.WinDef.WORD;
import com.sun.jna.platform.win32.WinNT;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.platform.win32.WinReg;
import com.sun.jna.platform.win32.Win32Exception;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Owns a suspended child and its entire Windows Job before any child code runs. */
public final class WindowsJobProcess implements AutoCloseable {
    public static final int REQUIRED_FLAGS = 0x2000 | 0x200;
    private static final int STILL_ACTIVE = 259;
    private static final int WAIT_TIMEOUT = 258;
    private static final int WAIT_FAILED = -1;
    public static final int JOB_DIAGNOSTIC_MAX_MEMBERS = 256;
    public static final int JOB_DIAGNOSTIC_MAX_BYTES = 65_536;

    public record CommandSpec(Path executable, List<String> arguments, Path cwd,
            Map<String, String> environment, Path stdout, Path stderr, long memoryLimitBytes) {
        public CommandSpec {
            Objects.requireNonNull(executable); Objects.requireNonNull(cwd);
            Objects.requireNonNull(stdout); Objects.requireNonNull(stderr);
            arguments = List.copyOf(arguments); environment = Map.copyOf(environment);
            if (!executable.isAbsolute() || !cwd.isAbsolute() || !stdout.isAbsolute()
                    || !stderr.isAbsolute() || memoryLimitBytes <= 0 || stdout.equals(stderr)) {
                throw new IllegalArgumentException("Absolute distinct paths and positive Job memory are required");
            }
            for (String argument : arguments) requireNoNul(argument);
            environment.forEach((key, value) -> {
                requireNoNul(key); requireNoNul(value);
                // GetEnvironmentStringsW also carries hidden names such as =C: and
                // =ExitCode. Their leading '=' is part of the name; a later one is not.
                int separator = key.indexOf('=');
                if (key.isEmpty() || (separator >= 0 && (separator != 0 || key.length() == 1 || key.indexOf('=', 1) >= 0))) {
                    throw new IllegalArgumentException("Invalid environment key: " + key);
                }
            });
        }
    }

    public record ProcessIdentity(long pid, String creationFiletimeDecimal, String executable) {
        public ProcessIdentity {
            if (pid <= 0 || pid > 0xffff_ffffL || creationFiletimeDecimal == null
                    || !creationFiletimeDecimal.matches("[1-9][0-9]{0,19}")
                    || new BigInteger(creationFiletimeDecimal).bitLength() > 64
                    || executable == null || !Path.of(executable).isAbsolute()) {
                throw new IllegalArgumentException("Exact process identity required");
            }
        }
    }
    /** uptimeMillisDecimal is the unsigned system GetTickCount64 observation, not process age. */
    public record LiveProcessObservation(ProcessIdentity identity, String uptimeMillisDecimal) {
        public LiveProcessObservation {
            Objects.requireNonNull(identity);
            if (uptimeMillisDecimal == null || !uptimeMillisDecimal.matches("0|[1-9][0-9]{0,19}")
                    || new BigInteger(uptimeMillisDecimal).bitLength() > 64) throw new IllegalArgumentException("Canonical unsigned system uptime required");
        }
    }
    public record Accounting(long peakJobMemoryBytes, int activeProcesses, long memoryLimitBytes, int limitFlags) {
        public Accounting {
            if (peakJobMemoryBytes < 0 || activeProcesses < 0 || memoryLimitBytes <= 0 || limitFlags < 0) {
                throw new IllegalArgumentException("Invalid actual Job accounting");
            }
        }
    }
    public record CommandResult(ProcessIdentity identity, int exitCode, double elapsedSeconds,
            Accounting accounting, String stopReason) {
        public CommandResult {
            Objects.requireNonNull(identity); Objects.requireNonNull(accounting);
            if (!Double.isFinite(elapsedSeconds) || elapsedSeconds < 0
                    || (stopReason != null && (stopReason.isBlank() || stopReason.length() > 2048))) {
                throw new IllegalArgumentException("Invalid actual command terminal state");
            }
        }
        public boolean passed() {
            return exitCode == 0 && stopReason == null && accounting.activeProcesses() == 0
                    && accounting.peakJobMemoryBytes() <= accounting.memoryLimitBytes()
                    && accounting.limitFlags() == REQUIRED_FLAGS;
        }
    }

    public enum ConsoleMode { NO_WINDOW, DETACHED, GUI_MINIMIZED_NO_ACTIVATE, GUI_SHOWN_NO_ACTIVATE }
    public enum RootExitDrainPolicy { DEFAULT_FIVE_SECONDS, UNTIL_COMMAND_DEADLINE }
    public enum DiagnosticWriteState { NOT_REQUESTED, NOT_NEEDED, WRITTEN, UNAVAILABLE }
    public enum JobListState { COMPLETE, TRUNCATED, UNAVAILABLE }
    public enum MemberState { OBSERVED, UNAVAILABLE }

    /** Independent sidecar outcome; it never changes CommandResult or grants command success. */
    public record JobDiagnosticOutcome(DiagnosticWriteState state, String requestedPath,
            ControlBuild.FileRef sidecarRef, String error) {
        public JobDiagnosticOutcome {
            Objects.requireNonNull(state); checkDiagnosticError(error);
            if ((state == DiagnosticWriteState.NOT_REQUESTED && (requestedPath != null || sidecarRef != null || error != null))
                    || (state != DiagnosticWriteState.NOT_REQUESTED && (requestedPath == null || requestedPath.isBlank()))
                    || (state == DiagnosticWriteState.WRITTEN && (sidecarRef == null || error != null
                        || sidecarRef.bytes() < 1 || sidecarRef.bytes() > JOB_DIAGNOSTIC_MAX_BYTES
                        || !Path.of(requestedPath).toAbsolutePath().normalize().equals(Path.of(sidecarRef.path()).toAbsolutePath().normalize())))
                    || (state != DiagnosticWriteState.WRITTEN && sidecarRef != null)
                    || (state == DiagnosticWriteState.UNAVAILABLE ? error == null : error != null)) {
                throw new IllegalArgumentException("Exact bounded diagnostic outcome required");
            }
        }
    }
    public record AwaitResult(CommandResult commandResult, JobDiagnosticOutcome diagnostic) {
        public AwaitResult { Objects.requireNonNull(commandResult); Objects.requireNonNull(diagnostic); }
    }
    public record RootDiagnostic(ProcessIdentity identity, Long waitZero, Long exitCode, Long win32Error, String error) {
        public RootDiagnostic {
            Objects.requireNonNull(identity); checkDword(waitZero); checkDword(exitCode); checkDword(win32Error); checkDiagnosticError(error);
            if (error == null && (waitZero == null || exitCode == null || win32Error != null)) {
                throw new IllegalArgumentException("Independent actual root wait and exit required");
            }
        }
    }
    public record JobMember(String pidDecimal, MemberState state, ProcessIdentity identity, Boolean inOwnedJob,
            Long waitZero, Long exitCode, Long win32Error, String error) {
        public JobMember {
            if (pidDecimal == null || !pidDecimal.matches("[1-9][0-9]{0,9}")
                    || Long.parseLong(pidDecimal) > 0xffff_ffffL) throw new IllegalArgumentException("Canonical DWORD PID text required");
            Objects.requireNonNull(state); checkDword(waitZero); checkDword(exitCode); checkDword(win32Error); checkDiagnosticError(error);
            if (identity != null && !pidDecimal.equals(Long.toString(identity.pid()))) throw new IllegalArgumentException("Same-handle PID differs");
            if (state == MemberState.OBSERVED && (identity == null || !Boolean.TRUE.equals(inOwnedJob)
                    || waitZero == null || exitCode == null || win32Error != null || error != null)) {
                throw new IllegalArgumentException("Actual same-owned-Job handle observation required");
            }
            if (state == MemberState.UNAVAILABLE && error == null) throw new IllegalArgumentException("Explicit race/query failure required");
        }
    }
    public record JobDiagnostic(String schema, String machineId, String observedAtUtc, String scope, String trigger,
            RootDiagnostic root, Accounting accounting, String accountingError, JobListState listState,
            Long assignedProcesses, Long listedProcesses, List<JobMember> members, Long win32Error, String error) {
        public JobDiagnostic {
            if (!"xar.windows-owned-job-before-cleanup/v1".equals(schema) || !"OWNED_JOB_BEFORE_CLEANUP".equals(scope)
                    || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,63}") || machineId.equals("unknown")
                    || trigger == null || trigger.isBlank() || trigger.length() > 512) throw new IllegalArgumentException("Exact owned-Job diagnostic scope required");
            Instant.parse(observedAtUtc); Objects.requireNonNull(root); Objects.requireNonNull(listState);
            members = List.copyOf(members); checkDiagnosticError(accountingError); checkDiagnosticError(error); checkDword(win32Error);
            checkDword(assignedProcesses); checkDword(listedProcesses);
            if ((accounting == null) != (accountingError != null) || members.size() > JOB_DIAGNOSTIC_MAX_MEMBERS
                    || members.stream().map(JobMember::pidDecimal).distinct().count() != members.size()
                    || (listState == JobListState.COMPLETE && (assignedProcesses == null || listedProcesses == null
                        || !assignedProcesses.equals(listedProcesses) || listedProcesses != members.size()
                        || win32Error != null || error != null))) {
                throw new IllegalArgumentException("Bounded actual Job list and explicit partial state required");
            }
        }
    }

    /** JNA 5.19.1 does not map Job APIs; these signatures use the Windows SDK ABI. */
    public interface JobKernel32 extends Kernel32 {
        HANDLE CreateJobObjectW(WinBase.SECURITY_ATTRIBUTES attributes, WString name);
        boolean SetInformationJobObject(HANDLE job, int kind, Pointer data, int length);
        boolean QueryInformationJobObject(HANDLE job, int kind, Pointer data, int length, IntByReference returned);
        boolean AssignProcessToJobObject(HANDLE job, HANDLE process);
        boolean IsProcessInJob(HANDLE process, HANDLE job, IntByReference result);
        boolean TerminateJobObject(HANDLE job, int exitCode);
        int ResumeThread(HANDLE thread);
    }

    @Structure.FieldOrder({"PerProcessUserTimeLimit", "PerJobUserTimeLimit", "LimitFlags",
            "MinimumWorkingSetSize", "MaximumWorkingSetSize", "ActiveProcessLimit", "Affinity",
            "PriorityClass", "SchedulingClass"})
    public static final class BasicLimits extends Structure {
        public long PerProcessUserTimeLimit, PerJobUserTimeLimit;
        public int LimitFlags;
        public SIZE_T MinimumWorkingSetSize = new SIZE_T(), MaximumWorkingSetSize = new SIZE_T();
        public int ActiveProcessLimit;
        public ULONG_PTR Affinity = new ULONG_PTR();
        public int PriorityClass, SchedulingClass;
    }

    @Structure.FieldOrder({"BasicLimitInformation", "IoInfo", "ProcessMemoryLimit", "JobMemoryLimit",
            "PeakProcessMemoryUsed", "PeakJobMemoryUsed"})
    public static final class ExtendedLimits extends Structure {
        public BasicLimits BasicLimitInformation = new BasicLimits();
        public WinNT.IO_COUNTERS IoInfo = new WinNT.IO_COUNTERS();
        public SIZE_T ProcessMemoryLimit = new SIZE_T(), JobMemoryLimit = new SIZE_T();
        public SIZE_T PeakProcessMemoryUsed = new SIZE_T(), PeakJobMemoryUsed = new SIZE_T();
    }

    @Structure.FieldOrder({"TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime", "ThisPeriodTotalKernelTime",
            "TotalPageFaultCount", "TotalProcesses", "ActiveProcesses", "TotalTerminatedProcesses"})
    public static final class BasicAccounting extends Structure {
        public long TotalUserTime, TotalKernelTime, ThisPeriodTotalUserTime, ThisPeriodTotalKernelTime;
        public int TotalPageFaultCount, TotalProcesses, ActiveProcesses, TotalTerminatedProcesses;
    }

    private final JobKernel32 nativeApi;
    private final HANDLE job;
    private final WinBase.PROCESS_INFORMATION process = new WinBase.PROCESS_INFORMATION();
    private final List<HANDLE> streams = new ArrayList<>();
    private final long started = System.nanoTime();
    private ProcessIdentity identity;
    private boolean closed;
    private final List<WindowsPreloadCustody.Lease> preloadLeases = new ArrayList<>();

    @FunctionalInterface public interface PreResumeHook {
        WindowsPreloadCustody.Lease beforeResume(SuspendedTarget target) throws IOException;
    }
    /** Minted only between actual CREATE_SUSPENDED/AssignJob and the one ResumeThread. */
    public static final class SuspendedTarget {
        private final WindowsJobProcess owner;
        private boolean active = true;
        private SuspendedTarget(WindowsJobProcess owner) { this.owner = owner; }
        public ProcessIdentity identity() throws IOException { requireActive(); return owner.identity(); }
        void requireActive() throws IOException {
            if (!active || owner.closed || !owner.isRunning()) throw new IOException("original suspended target is no longer available");
        }
        HANDLE duplicateRead() throws IOException {
            requireActive();
            var out = new WinNT.HANDLEByReference();
            HANDLE current = owner.nativeApi.GetCurrentProcess();
            require(owner.nativeApi.DuplicateHandle(current, owner.process.hProcess, current, out,
                    0x0400 | 0x0010 | 0x100000, false, 0));
            return requireHandle(out.getValue());
        }
        void retain(WindowsPreloadCustody.Lease lease) throws IOException {
            requireActive();
            if (!owner.preloadLeases.isEmpty()) throw new IOException("pre-resume custody already acquired");
            owner.preloadLeases.add(Objects.requireNonNull(lease));
        }
    }

    @FunctionalInterface public interface StdioGuard { void verify() throws IOException; }
    public record OwnedStdioSpec(CommandSpec command, ConsoleMode consoleMode,
            ControlBuild.FileRef executableRef, List<ControlBuild.FileRef> programSourceRefs,
            Instant deadline, int maxFrameBytes, long maxSentBytes, long maxReceivedBytes, StdioGuard guard) {
        public OwnedStdioSpec {
            Objects.requireNonNull(command); Objects.requireNonNull(consoleMode); Objects.requireNonNull(executableRef);
            Objects.requireNonNull(deadline); Objects.requireNonNull(guard); programSourceRefs = List.copyOf(programSourceRefs);
            if (programSourceRefs.isEmpty() || programSourceRefs.size() > 2048 || maxFrameBytes < 1
                    || maxFrameBytes > (32 << 20) || maxSentBytes < 1 || maxSentBytes > (64L << 20)
                    || maxReceivedBytes < maxFrameBytes || maxReceivedBytes > (64L << 20)
                    || !Path.of(executableRef.path()).toAbsolutePath().normalize().equals(command.executable().toAbsolutePath().normalize())) {
                throw new IllegalArgumentException("finite exact program/source stdio limits required");
            }
            if (command.executable().getFileName().toString().matches("(?i)(cmd|powershell|pwsh)\\.exe"))
                throw new IllegalArgumentException("owned stdio accepts a direct pinned program, not a shell");
            for (ControlBuild.FileRef ref : programSourceRefs) {
                Path path = Path.of(ref.path()).toAbsolutePath().normalize();
                if (path.equals(command.stdout()) || path.equals(command.stderr()))
                    throw new IllegalArgumentException("stdio outputs cannot alias program sources");
            }
        }
    }
    /** Actual in-memory pipe completion only. This type grants no Native/Game classification. */
    public static final class Arrival {
        private final byte[] raw;
        private final long sequence;
        private final String nonce;
        private final ProcessIdentity identity;
        private final Instant deadline;
        private Arrival(byte[] raw, long sequence, String nonce, ProcessIdentity identity, Instant deadline) {
            this.raw = raw.clone(); this.sequence = sequence; this.nonce = nonce; this.identity = identity; this.deadline = deadline;
        }
        public byte[] rawBytes() { return raw.clone(); }
        public long sequence() { return sequence; }
        public String sessionNonce() { return nonce; }
        public ProcessIdentity identity() { return identity; }
        public Instant deadline() { return deadline; }
    }
    public static final class WriteReceipt {
        private final long bytesWritten;
        private final ProcessIdentity identity;
        private final String nonce;
        private WriteReceipt(long bytesWritten, ProcessIdentity identity, String nonce) {
            this.bytesWritten = bytesWritten; this.identity = identity; this.nonce = nonce;
        }
        public long bytesWritten() { return bytesWritten; }
        public ProcessIdentity identity() { return identity; }
        public String sessionNonce() { return nonce; }
    }
    private record RedirectedStdio(HANDLE input, HANDLE output, StdioGuard beforeResume) { }

    /** Finite real stdio resource using this class's original suspended child/Job/await producer. */
    public static final class OwnedStdio implements AutoCloseable {
        private final OwnedStdioSpec spec;
        private final WindowsJobProcess owner;
        private final Win32StdioPipes pipes;
        private final List<SharedSourceFiles.Witness> sources;
        private final java.io.OutputStream audit;
        private final String nonce = java.util.UUID.randomUUID().toString().replace("-", "")
                + java.util.UUID.randomUUID().toString().replace("-", "");
        private final java.io.ByteArrayOutputStream partial = new java.io.ByteArrayOutputStream();
        private final java.util.ArrayDeque<byte[]> frames = new java.util.ArrayDeque<>();
        private long received, sent, sequence;
        private String failed;
        private boolean inputClosed, closed, awaitEntered;
        private AwaitResult terminal;
        private OwnedStdio(OwnedStdioSpec spec, WindowsJobProcess owner, Win32StdioPipes pipes,
                List<SharedSourceFiles.Witness> sources, java.io.OutputStream audit) {
            this.spec = spec; this.owner = owner; this.pipes = pipes; this.sources = List.copyOf(sources); this.audit = audit;
        }
        public OwnedStdioSpec spec() { return spec; }
        public ProcessIdentity identity() { return owner.identity(); }
        public String sessionNonce() { return nonce; }
        public Instant deadline() { return spec.deadline(); }
        synchronized void verifyLiveOwner() throws IOException {
            verifyActualIdentityAndSources();
            if (!owner.isRunning()) throw new IOException("actual owned server process is no longer live");
        }
        HANDLE duplicateOwnedHandle(String location) throws IOException {
            synchronized (this) {
                verifyLiveOwner();
                if (location == null || !location.matches("[1-9][0-9]{0,19}")
                        || new BigInteger(location).bitLength() > 64 || location.equals("18446744073709551615"))
                    throw new IOException("canonical unsigned handle locator required");
                var out = new WinNT.HANDLEByReference();
                if (!owner.nativeApi.DuplicateHandle(owner.process.hProcess,
                        new HANDLE(new Pointer(Long.parseUnsignedLong(location))), owner.nativeApi.GetCurrentProcess(),
                        out, 0, false, 2))
                    throw new IOException("duplicate actual owner handle Win32=" + Native.getLastError());
                HANDLE result = out.getValue();
                if (result == null || WinBase.INVALID_HANDLE_VALUE.equals(result))
                    throw new IOException("actual owner handle duplication returned no retained handle");
                try { verifyActualIdentityAndSources(); return result; }
                catch (IOException | RuntimeException failure) { owner.nativeApi.CloseHandle(result); throw failure; }
            }
        }
        public synchronized void verifyActualIdentityAndSources() throws IOException {
            try { verifyPinnedResource(); }
            catch (IOException failure) { fail(failure); throw failure; }
            catch (RuntimeException failure) {
                IOException invalid = new IOException("owned stdio native/source guard failed: " + failure, failure);
                fail(invalid); throw invalid;
            }
        }
        private void verifyPinnedResource() throws IOException {
            if (closed) throw new IOException("owned stdio resource closed");
            if (failed != null) throw new IOException("owned stdio outcome unknown: " + failed);
            verifyHeldProcess();
            Accounting accounting = owner.accounting();
            if (accounting.limitFlags() != REQUIRED_FLAGS || accounting.memoryLimitBytes() != spec.command().memoryLimitBytes()
                    || accounting.peakJobMemoryBytes() > accounting.memoryLimitBytes()) throw new IOException("owned stdio Job limits drift");
            for (SharedSourceFiles.Witness source : sources) SharedSourceFiles.assertUnchanged(source);
            spec.guard().verify();
        }
        private void verifyHeldProcess() throws IOException {
            int signal = owner.nativeApi.WaitForSingleObject(owner.process.hProcess, 0);
            if (signal == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
            if (signal == WAIT_TIMEOUT) {
                try {
                    ProcessIdentity actual = WindowsJobProcess.identity(owner.nativeApi, owner.process.hProcess, owner.identity().pid());
                    if (!actual.equals(owner.identity())) throw new IOException("owned stdio child identity drift");
                    IntByReference belongs = new IntByReference();
                    require(owner.nativeApi.IsProcessInJob(owner.process.hProcess, owner.job, belongs));
                    if (belongs.getValue() == 0) throw new IOException("live stdio child is outside its owned Job");
                    return;
                } catch (IOException | RuntimeException racedExit) {
                    if (owner.nativeApi.WaitForSingleObject(owner.process.hProcess, 0) != 0) throw racedExit;
                }
            } else if (signal != 0) throw new IOException("unexpected owned process signal");
            // The original held handle still binds its process object after exit. Live-only
            // image/membership queries can then fail. PID and birth use that same handle;
            // pre-resume/live membership and the unchanged no-breakaway Job remain mandatory.
            long pid = Integer.toUnsignedLong(owner.nativeApi.GetProcessId(owner.process.hProcess));
            String birth = creationFiletime(owner.nativeApi, owner.process.hProcess);
            if (pid != owner.identity().pid() || !birth.equals(owner.identity().creationFiletimeDecimal()))
                throw new IOException("signalled owned process handle identity differs");
        }
        private Instant operationDeadline(Instant requested) throws IOException {
            Objects.requireNonNull(requested);
            Instant effective = requested.isBefore(deadline()) ? requested : deadline();
            Win32StdioPipes.check(effective, this::verifyActualIdentityAndSources); return effective;
        }
        private void fail(IOException failure) {
            if (failed == null) {
                String reason = failure.getClass().getSimpleName() + ": " + failure.getMessage();
                failed = reason.substring(0, Math.min(1024, reason.length()));
            }
            if (!closed) try { owner.terminate(124); }
            catch (RuntimeException cleanup) { failure.addSuppressed(cleanup); }
        }
        public synchronized WriteReceipt write(byte[] bytes, Instant requestedDeadline) throws IOException, InterruptedException {
            Objects.requireNonNull(bytes); byte[] original = bytes.clone();
            try {
                Instant until = operationDeadline(requestedDeadline);
                if (inputClosed || awaitEntered || !owner.isRunning()) throw new IOException("owned stdin is no longer writable");
                if (original.length == 0 || original.length > spec.maxSentBytes() - sent) throw new IOException("owned stdin aggregate byte limit exceeded");
                int offset = 0;
                while (offset < original.length) {
                    int count = pipes.write(original, offset, original.length - offset, until, this::verifyActualIdentityAndSources);
                    if (count <= 0) throw new IOException("owned stdin made no write progress");
                    offset += count; sent += count;
                }
                Win32StdioPipes.check(until, this::verifyActualIdentityAndSources);
                return new WriteReceipt(offset, identity(), nonce);
            } catch (IOException failure) { fail(failure); throw failure; }
            catch (InterruptedException interrupted) {
                fail(new IOException("owned stdin interrupted", interrupted)); Thread.currentThread().interrupt(); throw interrupted;
            }
        }
        public synchronized Arrival readLine(Instant requestedDeadline) throws IOException, InterruptedException {
            try {
                Instant until = operationDeadline(requestedDeadline);
                if (awaitEntered) throw new IOException("owned stdout terminal was already requested");
                while (frames.isEmpty()) {
                    byte[] chunk = pipes.read(until, this::verifyActualIdentityAndSources);
                    if (chunk == null) throw new IOException(partial.size() == 0 ? "owned stdout EOF before next line" : "owned stdout EOF inside line");
                    if (chunk.length > spec.maxReceivedBytes() - received) throw new IOException("owned stdout aggregate byte limit exceeded");
                    received += chunk.length; audit.write(chunk); audit.flush();
                    for (byte value : chunk) {
                        if (partial.size() >= spec.maxFrameBytes()) throw new IOException("owned stdout line byte limit exceeded");
                        partial.write(value);
                        if (value == '\n') {
                            if (frames.size() >= 256) throw new IOException("owned stdout queued line limit exceeded");
                            frames.addLast(partial.toByteArray()); partial.reset();
                        }
                    }
                }
                Win32StdioPipes.check(until, this::verifyActualIdentityAndSources);
                sequence = Math.addExact(sequence, 1);
                return new Arrival(frames.removeFirst(), sequence, nonce, identity(), until);
            } catch (IOException failure) { fail(failure); throw failure; }
            catch (InterruptedException interrupted) {
                fail(new IOException("owned stdout interrupted", interrupted)); Thread.currentThread().interrupt(); throw interrupted;
            }
        }
        public synchronized void closeInput() {
            if (!inputClosed) { pipes.closeInput(); inputClosed = true; }
        }
        public synchronized AwaitResult awaitExit(Path diagnosticSidecar) throws IOException, InterruptedException {
            if (terminal != null) return terminal;
            if (awaitEntered) throw new IOException("previous owned stdio terminal is unavailable; no repeated wait authority");
            awaitEntered = true; closeInput();
            Duration remaining = Duration.between(Instant.now(), deadline());
            if (remaining.isNegative() || remaining.isZero()) remaining = Duration.ofNanos(1);
            AwaitResult actual = owner.await(remaining, deadline(), () -> {
                if (failed != null) throw new IllegalStateException(failed);
                try { verifyActualIdentityAndSources(); }
                catch (IOException failure) { throw new IllegalStateException(failure.getMessage(), failure); }
            }, diagnosticSidecar, RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE);
            if (!pipes.settled()) throw new IOException("stdio I/O cancellation remains unobserved");
            if (failed == null) Win32StdioPipes.check(deadline(), this::verifyActualIdentityAndSources);
            // A completed root and a zero-member Job correctly skip the live
            // guard. They cannot clear a protocol failure latched before await.
            if (failed != null && actual.commandResult().stopReason() == null) {
                CommandResult observed = actual.commandResult();
                actual = new AwaitResult(new CommandResult(observed.identity(), observed.exitCode(),
                        observed.elapsedSeconds(), observed.accounting(), "owned_stdio_unknown: " + failed),
                        actual.diagnostic());
            }
            terminal = actual; return terminal;
        }
        @Override public synchronized void close() {
            if (closed) return;
            try { closeInput(); owner.close(); }
            finally {
                pipes.close();
                try { audit.close(); } catch (IOException failure) { if (failed == null) failed = failure.toString(); }
                closed = true;
            }
        }
    }

    public static synchronized OwnedStdio startOwnedStdio(OwnedStdioSpec spec) throws IOException {
        Objects.requireNonNull(spec); requireWindows();
        List<SharedSourceFiles.Witness> sources = new ArrayList<>();
        for (ControlBuild.FileRef ref : java.util.stream.Stream.concat(java.util.stream.Stream.of(spec.executableRef()),
                spec.programSourceRefs().stream()).toList()) {
            ref.verify(); SharedSourceFiles.Witness witness = SharedSourceFiles.observe(Path.of(ref.path()));
            if (witness.source().bytes() != ref.bytes() || !witness.source().sha256().equals(ref.sha256()))
                throw new IOException("owned stdio program source differs from pinned bytes");
            sources.add(witness);
        }
        StdioGuard programGuard = () -> {
            for (SharedSourceFiles.Witness source : sources) SharedSourceFiles.assertUnchanged(source);
            spec.guard().verify();
        };
        Win32StdioPipes.check(spec.deadline(), programGuard);
        SharedSourceFiles.plainAncestors(spec.command().stdout().getParent());
        SharedSourceFiles.plainAncestors(spec.command().stderr().getParent());
        SharedSourceFiles.plainAncestors(spec.command().cwd());
        java.io.OutputStream audit = Files.newOutputStream(spec.command().stdout(), java.nio.file.StandardOpenOption.CREATE_NEW,
                java.nio.file.StandardOpenOption.WRITE);
        Win32StdioPipes pipes = null;
        WindowsJobProcess owner = null;
        try {
            pipes = Win32StdioPipes.create(spec.deadline(), programGuard);
            owner = start(spec.command(), spec.consoleMode(), pipes.api(),
                    new RedirectedStdio(pipes.childInput(), pipes.childOutput(),
                            () -> Win32StdioPipes.check(spec.deadline(), programGuard)));
            pipes.closeInheritedCopies();
            OwnedStdio result = new OwnedStdio(spec, owner, pipes, sources, audit);
            Win32StdioPipes.check(spec.deadline(), result::verifyActualIdentityAndSources); return result;
        } catch (IOException | RuntimeException failure) {
            if (owner != null) owner.close();
            if (pipes != null) pipes.close();
            try { audit.close(); } catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
            throw failure;
        }
    }

    private WindowsJobProcess(JobKernel32 nativeApi, HANDLE job) {
        this.nativeApi = nativeApi; this.job = job;
    }

    public static WindowsJobProcess start(CommandSpec spec) throws IOException {
        return start(spec, ConsoleMode.NO_WINDOW);
    }

    /** Per-call console creation choice; CommandSpec and the existing default remain unchanged. */
    public static synchronized WindowsJobProcess start(CommandSpec spec, ConsoleMode consoleMode) throws IOException {
        requireWindows();
        return start(spec, consoleMode, Native.load("kernel32", JobKernel32.class, W32APIOptions.UNICODE_OPTIONS), null);
    }
    public static synchronized WindowsJobProcess start(CommandSpec spec, ConsoleMode consoleMode,
            PreResumeHook hook) throws IOException {
        requireWindows(); Objects.requireNonNull(hook);
        return start(spec, consoleMode, Native.load("kernel32", JobKernel32.class, W32APIOptions.UNICODE_OPTIONS), null, hook);
    }
    private static WindowsJobProcess start(CommandSpec spec, ConsoleMode consoleMode, JobKernel32 api,
            RedirectedStdio redirected) throws IOException {
        return start(spec, consoleMode, api, redirected, null);
    }
    private static WindowsJobProcess start(CommandSpec spec, ConsoleMode consoleMode, JobKernel32 api,
            RedirectedStdio redirected, PreResumeHook hook) throws IOException {
        Objects.requireNonNull(consoleMode);
        requireWindows();
        if (!Files.isRegularFile(spec.executable()) || !Files.isDirectory(spec.cwd())) {
            throw new IllegalArgumentException("Actual executable and working directory must exist");
        }
        HANDLE job = requireHandle(api.CreateJobObjectW(null, null));
        WindowsJobProcess owner = new WindowsJobProcess(api, job);
        try {
            ExtendedLimits limits = new ExtendedLimits();
            limits.BasicLimitInformation.LimitFlags = REQUIRED_FLAGS;
            limits.JobMemoryLimit = new SIZE_T(spec.memoryLimitBytes()); limits.write();
            require(api.SetInformationJobObject(job, 9, limits.getPointer(), limits.size()));
            Accounting actual = owner.accounting();
            if (actual.memoryLimitBytes() != spec.memoryLimitBytes() || actual.limitFlags() != REQUIRED_FLAGS) {
                throw new IllegalStateException("Windows Job limit readback differs");
            }
            WinBase.SECURITY_ATTRIBUTES inheritable = new WinBase.SECURITY_ATTRIBUTES();
            inheritable.bInheritHandle = true;
            WinBase.STARTUPINFO startup = new WinBase.STARTUPINFO();
            startup.dwFlags = 0x100 | 0x1;
            startup.wShowWindow = new WORD(switch (consoleMode) {
                case NO_WINDOW, DETACHED -> 0;
                case GUI_MINIMIZED_NO_ACTIVATE -> 7; // SW_SHOWMINNOACTIVE.
                case GUI_SHOWN_NO_ACTIVATE -> 4; // SW_SHOWNOACTIVATE.
            });
            startup.hStdInput = redirected == null ? owner.openStream("NUL", WinNT.GENERIC_READ, 3, inheritable) : redirected.input();
            startup.hStdOutput = redirected == null ? owner.openStream(spec.stdout().toString(), WinNT.GENERIC_WRITE, 1, inheritable) : redirected.output();
            startup.hStdError = owner.openStream(spec.stderr().toString(), WinNT.GENERIC_WRITE, 1, inheritable);
            String command = commandLine(spec);
            int consoleFlag = switch (consoleMode) {
                case NO_WINDOW, GUI_MINIMIZED_NO_ACTIVATE, GUI_SHOWN_NO_ACTIVATE -> 0x08000000; // CREATE_NO_WINDOW.
                case DETACHED -> 0x00000008; // DETACHED_PROCESS: never combine CREATE_NO_WINDOW.
            };
            try (Memory environment = environmentBlock(spec.environment())) {
                require(api.CreateProcessW(spec.executable().toString(), Native.toCharArray(command),
                        null, null, true, new DWORD(0x4 | 0x400 | consoleFlag), environment,
                        spec.cwd().toString(), startup, owner.process));
            }
            require(api.AssignProcessToJobObject(job, owner.process.hProcess));
            owner.identity = identity(api, owner.process.hProcess, Integer.toUnsignedLong(owner.process.dwProcessId.intValue()));
            if (!Files.isSameFile(Path.of(owner.identity.executable()), spec.executable())) {
                throw new IllegalStateException("Actual process image differs before resume");
            }
            if (redirected != null) {
                IntByReference belongs = new IntByReference(); require(api.IsProcessInJob(owner.process.hProcess, job, belongs));
                if (belongs.getValue() == 0) throw new IOException("stdio child Job assignment not observed before resume");
                redirected.beforeResume().verify();
            }
            if (hook != null) {
                SuspendedTarget target = new SuspendedTarget(owner);
                try {
                    WindowsPreloadCustody.Lease lease = hook.beforeResume(target);
                    if (lease == null || !owner.preloadLeases.contains(lease) || !lease.from(target))
                        throw new IOException("hook did not return its original retained preload custody");
                    lease.verify();
                } finally { target.active = false; }
            }
            int previousSuspendCount = api.ResumeThread(owner.process.hThread);
            if (previousSuspendCount == -1) throw new Win32Exception(Native.getLastError());
            if (previousSuspendCount != 1) throw new IOException("original primary thread suspend count differs from one");
            return owner;
        } catch (IOException | RuntimeException error) {
            if (owner.process.hProcess != null) api.TerminateProcess(owner.process.hProcess, 126);
            owner.close(); throw error;
        }
    }

    public ProcessIdentity identity() { ensureOpen(); return Objects.requireNonNull(identity); }

    public Accounting accounting() {
        ensureOpen();
        ExtendedLimits limits = new ExtendedLimits();
        require(nativeApi.QueryInformationJobObject(job, 9, limits.getPointer(), limits.size(), null)); limits.read();
        BasicAccounting counts = new BasicAccounting();
        require(nativeApi.QueryInformationJobObject(job, 1, counts.getPointer(), counts.size(), null)); counts.read();
        return new Accounting(limits.PeakJobMemoryUsed.longValue(), counts.ActiveProcesses,
                limits.JobMemoryLimit.longValue(), limits.BasicLimitInformation.LimitFlags);
    }

    public boolean isRunning() {
        ensureOpen();
        int state = nativeApi.WaitForSingleObject(process.hProcess, 0);
        if (state == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
        return state == WAIT_TIMEOUT;
    }

    public void terminate(int exitCode) { ensureOpen(); require(nativeApi.TerminateJobObject(job, exitCode)); }

    public CommandResult await(Duration timeout, Instant leaseDeadline, Runnable periodicGuard) throws InterruptedException {
        return await(timeout, leaseDeadline, periodicGuard, null).commandResult();
    }

    /** Optional CREATE_NEW sidecar is captured before the first owned-Job kill; diagnostic failure never masks its terminal. */
    public AwaitResult await(Duration timeout, Instant leaseDeadline, Runnable periodicGuard, Path diagnosticSidecar) throws InterruptedException {
        return await(timeout, leaseDeadline, periodicGuard, diagnosticSidecar, RootExitDrainPolicy.DEFAULT_FIVE_SECONDS);
    }

    /**
     * Explicit per-call drain choice. The deadline policy observes the entire owned
     * Job after root exit within the original command/lease limits and guard.
     * It does not ignore, rename or exempt any child and does not extend a deadline.
     * After actual root exit, a zero-member Job skips the live periodic guard only.
     * Callers retain final provenance, authority, and output/resource validation.
     */
    public AwaitResult await(Duration timeout, Instant leaseDeadline, Runnable periodicGuard, Path diagnosticSidecar,
            RootExitDrainPolicy rootExitDrainPolicy) throws InterruptedException {
        ensureOpen(); Objects.requireNonNull(leaseDeadline); Objects.requireNonNull(periodicGuard);
        Objects.requireNonNull(rootExitDrainPolicy);
        if (timeout.isZero() || timeout.isNegative()) throw new IllegalArgumentException("Finite positive timeout required");
        long deadline = Math.addExact(System.nanoTime(), timeout.toNanos());
        String reason = null; boolean interrupted = false;
        JobDiagnosticOutcome diagnostic = diagnosticSidecar == null
                ? new JobDiagnosticOutcome(DiagnosticWriteState.NOT_REQUESTED, null, null, null)
                : new JobDiagnosticOutcome(DiagnosticWriteState.NOT_NEEDED, diagnosticSidecar.toString(), null, null);
        while (isRunning()) {
            if (System.nanoTime() >= deadline || !Instant.now().isBefore(leaseDeadline)) {
                reason = "timeout_or_release_expired"; break;
            }
            try { periodicGuard.run(); }
            catch (RuntimeException error) { reason = "periodic_guard: " + error.getMessage(); break; }
            if (accounting().peakJobMemoryBytes() > accounting().memoryLimitBytes()) {
                reason = "observed_job_peak_exceeded_limit"; break;
            }
            try { Thread.sleep(250); }
            catch (InterruptedException error) { interrupted = true; reason = "interrupted"; break; }
        }
        if (reason != null) {
            diagnostic = captureBeforeCleanup(diagnosticSidecar, reason, diagnostic);
            terminate(124);
        }
        if (reason == null && rootExitDrainPolicy == RootExitDrainPolicy.UNTIL_COMMAND_DEADLINE) {
            while (true) {
                if (System.nanoTime() >= deadline || !Instant.now().isBefore(leaseDeadline)) {
                    reason = "timeout_or_release_expired"; break;
                }
                Accounting remaining = accounting();
                // Native queries and guard time consume the same original finite budget.
                if (System.nanoTime() >= deadline || !Instant.now().isBefore(leaseDeadline)) {
                    reason = "timeout_or_release_expired"; break;
                }
                if (remaining.peakJobMemoryBytes() > remaining.memoryLimitBytes()) {
                    reason = "observed_job_peak_exceeded_limit"; break;
                }
                // The original root handle already reported exit before this drain.
                // With no owned members left there is no live writer to guard here.
                // Callers still perform their complete final source/resource checks.
                if (remaining.activeProcesses() == 0) break;
                try { periodicGuard.run(); }
                catch (RuntimeException error) { reason = "periodic_guard: " + error.getMessage(); break; }
                if (System.nanoTime() >= deadline || !Instant.now().isBefore(leaseDeadline)) {
                    reason = "timeout_or_release_expired"; break;
                }
                try { Thread.sleep(100); }
                catch (InterruptedException error) { interrupted = true; reason = "interrupted"; break; }
            }
            if (reason != null) {
                diagnostic = captureBeforeCleanup(diagnosticSidecar, reason, diagnostic);
                terminate(124);
            }
        }
        for (int i = 0; i < 50 && accounting().activeProcesses() != 0; i++) {
            try { Thread.sleep(100); } catch (InterruptedException error) { interrupted = true; }
        }
        if (accounting().activeProcesses() != 0) {
            reason = reason == null ? "root_exited_with_live_children" : reason;
            diagnostic = captureBeforeCleanup(diagnosticSidecar, reason, diagnostic);
            terminate(125);
            for (int i = 0; i < 50 && accounting().activeProcesses() != 0; i++) {
                try { Thread.sleep(100); } catch (InterruptedException error) { interrupted = true; }
            }
        }
        // Job accounting can reach zero before the root process object becomes signalled.
        // Observe that independent terminal state before consuming its exit code.
        int rootSignal = nativeApi.WaitForSingleObject(process.hProcess, 5000);
        if (rootSignal == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
        if (rootSignal == WAIT_TIMEOUT) reason = "root_exit_not_observed";
        IntByReference exit = new IntByReference();
        require(nativeApi.GetExitCodeProcess(process.hProcess, exit));
        Accounting finalState = accounting();
        if (finalState.activeProcesses() != 0) reason = "job_cleanup_incomplete";
        if (finalState.peakJobMemoryBytes() > finalState.memoryLimitBytes()) reason = "observed_job_peak_exceeded_limit";
        CommandResult result = new CommandResult(identity(), exit.getValue(), (System.nanoTime() - started) / 1_000_000_000.0,
                finalState, reason);
        if (interrupted) Thread.currentThread().interrupt();
        return new AwaitResult(result, diagnostic);
    }

    private JobDiagnosticOutcome captureBeforeCleanup(Path sidecar, String trigger, JobDiagnosticOutcome previous) {
        if (previous.state() != DiagnosticWriteState.NOT_NEEDED) return previous; // One bounded observation/write attempt.
        try {
            if (!sidecar.isAbsolute()) throw new IOException("Absolute diagnostic sidecar required");
            JobDiagnostic snapshot = ownedJobDiagnostic(trigger);
            byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(snapshot);
            while (raw.length > JOB_DIAGNOSTIC_MAX_BYTES && !snapshot.members().isEmpty()) {
                // Preserve exact identities; omit a bounded tail instead of truncating an image or birth value.
                int keep = snapshot.members().size() / 2;
                snapshot = new JobDiagnostic(snapshot.schema(), snapshot.machineId(), snapshot.observedAtUtc(), snapshot.scope(),
                        snapshot.trigger(), snapshot.root(), snapshot.accounting(), snapshot.accountingError(),
                        snapshot.listState() == JobListState.UNAVAILABLE ? JobListState.UNAVAILABLE : JobListState.TRUNCATED,
                        snapshot.assignedProcesses(), snapshot.listedProcesses(), snapshot.members().subList(0, keep),
                        snapshot.win32Error(), diagnosticText("sidecar_byte_budget; " + Objects.toString(snapshot.error(), "")));
                raw = ControlBuild.strictMapper().writeValueAsBytes(snapshot);
            }
            if (raw.length == 0 || raw.length > JOB_DIAGNOSTIC_MAX_BYTES) throw new IOException("Diagnostic metadata exceeds 64 KiB");
            Files.write(sidecar, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            ControlBuild.FileRef reference = ControlBuild.FileRef.measure(sidecar); reference.verify();
            return new JobDiagnosticOutcome(DiagnosticWriteState.WRITTEN, sidecar.toString(), reference, null);
        } catch (IOException | RuntimeException | LinkageError error) {
            // A diagnostic failure never bypasses the original kill, accounting, stop reason or caller cleanup.
            return new JobDiagnosticOutcome(DiagnosticWriteState.UNAVAILABLE, sidecar.toString(), null,
                    diagnosticText(error.getClass().getName() + ": " + error.getMessage()));
        }
    }

    private JobDiagnostic ownedJobDiagnostic(String trigger) {
        String observed = Instant.now().toString();
        RootDiagnostic root = rootDiagnostic();
        Accounting counts = null; String accountingError = null;
        try { counts = accounting(); }
        catch (RuntimeException | LinkageError error) { accountingError = diagnosticText(error.toString()); }
        JobListState state = JobListState.COMPLETE; Long assigned = null, listed = null, nativeError = null;
        String error = null; List<JobMember> members = new ArrayList<>();
        // x64 DWORD,DWORD,ULONG_PTR[]: offset8, pointer stride8. No system process enumeration or retry loop.
        try (Memory buffer = new Memory(8L + JOB_DIAGNOSTIC_MAX_MEMBERS * Native.POINTER_SIZE)) {
            buffer.clear();
            boolean queried = nativeApi.QueryInformationJobObject(job, 3, buffer, (int) buffer.size(), null);
            if (!queried) nativeError = Integer.toUnsignedLong(Native.getLastError());
            if (!queried && nativeError != 234) {
                state = JobListState.UNAVAILABLE; error = "QueryInformationJobObject(JobObjectBasicProcessIdList) failed";
            } else {
                assigned = Integer.toUnsignedLong(buffer.getInt(0)); listed = Integer.toUnsignedLong(buffer.getInt(4));
                if (listed > JOB_DIAGNOSTIC_MAX_MEMBERS || listed > assigned) {
                    state = JobListState.UNAVAILABLE; error = "Invalid actual Job PID list counts; no PID lookup attempted";
                } else {
                    if (!queried || listed < assigned) {
                        state = JobListState.TRUNCATED; error = "Bounded partial Job PID list";
                    }
                    for (int i = 0; i < listed; i++) {
                        long pid = buffer.getLong(8L + i * Native.POINTER_SIZE);
                        if (pid <= 0 || pid > 0xffff_ffffL) {
                            state = JobListState.UNAVAILABLE;
                            error = "Non-DWORD Job PID; no external PID lookup: " + Long.toUnsignedString(pid); break;
                        }
                        members.add(memberDiagnostic(pid));
                    }
                }
            }
        }
        return new JobDiagnostic("xar.windows-owned-job-before-cleanup/v1", currentMachineId(), observed,
                "OWNED_JOB_BEFORE_CLEANUP", diagnosticText(trigger), root, counts, accountingError,
                state, assigned, listed, members, nativeError, error);
    }

    private RootDiagnostic rootDiagnostic() {
        Long wait = null, exit = null, nativeError = null; String error = null;
        try {
            int observed = nativeApi.WaitForSingleObject(process.hProcess, 0); wait = Integer.toUnsignedLong(observed);
            if (observed == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
            IntByReference code = new IntByReference(); require(nativeApi.GetExitCodeProcess(process.hProcess, code));
            exit = Integer.toUnsignedLong(code.getValue());
        } catch (RuntimeException | LinkageError failure) {
            nativeError = diagnosticNativeError(failure); error = diagnosticText(failure.toString());
        }
        return new RootDiagnostic(identity(), wait, exit, nativeError, error);
    }

    private JobMember memberDiagnostic(long pid) {
        HANDLE handle = nativeApi.OpenProcess(0x1000 | 0x100000, false, (int) pid);
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            long nativeError = Integer.toUnsignedLong(Native.getLastError());
            return new JobMember(Long.toString(pid), MemberState.UNAVAILABLE, null, null, null, null,
                    nativeError, "OpenProcess after owned Job enumeration unavailable; process may have exited");
        }
        ProcessIdentity measured = null; Boolean inJob = null; Long wait = null, exit = null, nativeError = null;
        String error = null, stage = "IsProcessInJob";
        try {
            IntByReference membership = new IntByReference(); require(nativeApi.IsProcessInJob(handle, job, membership));
            inJob = membership.getValue() != 0;
            if (!inJob) error = "Enumerated PID is no longer in this owned Job; no identity read permitted";
            else {
                stage = "GetProcessTimes/QueryFullProcessImageName"; measured = identity(nativeApi, handle, pid);
                stage = "WaitForSingleObject";
                int observed = nativeApi.WaitForSingleObject(handle, 0); wait = Integer.toUnsignedLong(observed);
                if (observed == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
                stage = "GetExitCodeProcess";
                IntByReference code = new IntByReference(); require(nativeApi.GetExitCodeProcess(handle, code));
                exit = Integer.toUnsignedLong(code.getValue());
                stage = "IsProcessInJob recheck"; require(nativeApi.IsProcessInJob(handle, job, membership));
                inJob = membership.getValue() != 0;
                if (!inJob) error = "Same held generation left the owned Job during observation";
            }
        } catch (RuntimeException | LinkageError failure) {
            nativeError = diagnosticNativeError(failure); error = diagnosticText(stage + ": " + failure);
        } finally {
            // Close this single query handle exactly once, without changing command cleanup semantics.
            try {
                if (!nativeApi.CloseHandle(handle)) {
                    long closeError = Integer.toUnsignedLong(Native.getLastError());
                    if (nativeError == null) nativeError = closeError;
                    error = diagnosticText(Objects.toString(error, "") + "; CloseHandle Win32=" + closeError);
                }
            } catch (RuntimeException | LinkageError closeFailure) {
                if (nativeError == null) nativeError = diagnosticNativeError(closeFailure);
                error = diagnosticText(Objects.toString(error, "") + "; CloseHandle: " + closeFailure);
            }
        }
        return new JobMember(Long.toString(pid), error == null ? MemberState.OBSERVED : MemberState.UNAVAILABLE,
                measured, inJob, wait, exit, nativeError, error);
    }

    private static Long diagnosticNativeError(Throwable error) {
        return error instanceof Win32Exception nativeError ? Integer.toUnsignedLong(nativeError.getErrorCode()) : null;
    }
    private static String diagnosticText(String text) {
        if (text.length() <= 512) return text;
        int end = Character.isHighSurrogate(text.charAt(511)) ? 511 : 512;
        return text.substring(0, end);
    }
    private static void checkDiagnosticError(String error) {
        if (error != null && (error.isBlank() || error.length() > 512)) throw new IllegalArgumentException("Bounded diagnostic error required");
    }
    private static void checkDword(Long value) {
        if (value != null && (value < 0 || value > 0xffff_ffffL)) throw new IllegalArgumentException("Unsigned DWORD diagnostic value required");
    }

    @Override public void close() {
        if (!closed) {
            try { nativeApi.TerminateJobObject(job, 125); }
            finally {
                if (process.hThread != null) nativeApi.CloseHandle(process.hThread);
                if (process.hProcess != null) nativeApi.CloseHandle(process.hProcess);
                for (HANDLE stream : streams) nativeApi.CloseHandle(stream);
                nativeApi.CloseHandle(job); closed = true;
            }
        }
        for (WindowsPreloadCustody.Lease lease : preloadLeases) try { lease.close(); }
        catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
    }

    public static ProcessIdentity exactProcess(long pid) {
        requireWindows();
        if (pid <= 0 || pid > 0xffff_ffffL) throw new IllegalArgumentException("DWORD PID required");
        HANDLE handle = requireHandle(Kernel32.INSTANCE.OpenProcess(0x1000 | 0x100000, false, (int) pid));
        try { return identity(Kernel32.INSTANCE, handle, pid); }
        finally { Kernel32.INSTANCE.CloseHandle(handle); }
    }

    /**
     * Owns one non-inheritable query/synchronize handle for an exact generation.
     * This type exposes no native handle, process mutation, Job or stdio authority.
     * Birth and image are measured once from the acquired handle; wait and exit
     * queries keep using that same handle, including after the process exits.
     */
    public static final class ReadOnlyProcessHandle implements AutoCloseable {
        private final Kernel32 nativeApi;
        private final HANDLE processHandle;
        private final ProcessIdentity identity;
        private boolean closed;

        private ReadOnlyProcessHandle(Kernel32 nativeApi, HANDLE processHandle, long pid) {
            this.nativeApi = nativeApi;
            this.processHandle = processHandle;
            this.identity = WindowsJobProcess.identity(nativeApi, processHandle, pid);
        }

        /** Cached identity measured from this handle, never a subsequent PID lookup. */
        public synchronized ProcessIdentity identity() {
            ensureHandleOpen();
            return identity;
        }

        /** Actual unsigned WaitForSingleObject(handle, 0) result; WAIT_FAILED throws. */
        public synchronized long waitZero() {
            ensureHandleOpen();
            int state = nativeApi.WaitForSingleObject(processHandle, 0);
            if (state == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
            return Integer.toUnsignedLong(state);
        }

        /** Actual unsigned DWORD; 259 alone does not establish process liveness. */
        public synchronized long exitCode() {
            ensureHandleOpen();
            IntByReference exit = new IntByReference();
            require(nativeApi.GetExitCodeProcess(processHandle, exit));
            return Integer.toUnsignedLong(exit.getValue());
        }

        /** One close attempt, including failures; later queries reject without a native call. */
        @Override public synchronized void close() {
            if (closed) return;
            closed = true;
            require(nativeApi.CloseHandle(processHandle));
        }

        private void ensureHandleOpen() {
            if (closed) throw new IllegalStateException("Read-only process handle is closed");
        }
    }

    /**
     * Retains a single actual generation without requiring it to be currently live.
     * A successful capture is identity evidence; callers independently inspect wait
     * and exit status and keep their original creator/stdio/Job ownership.
     */
    public static ReadOnlyProcessHandle retainReadOnlyProcess(long pid) {
        requireWindows();
        if (pid <= 0 || pid > 0xffff_ffffL) throw new IllegalArgumentException("DWORD PID required");
        Kernel32 api = Kernel32.INSTANCE;
        HANDLE handle = requireHandle(api.OpenProcess(0x1000 | 0x100000, false, (int) pid));
        try {
            return new ReadOnlyProcessHandle(api, handle, pid);
        } catch (RuntimeException | Error error) {
            try { require(api.CloseHandle(handle)); }
            catch (RuntimeException | Error closeError) {
                if (closeError != error) error.addSuppressed(closeError);
            }
            throw error;
        }
    }

    /** One held native handle binds both liveness checks, process birth/EXE and monotonic observation. */
    public static LiveProcessObservation observeLiveProcess(long pid) {
        requireWindows();
        if (pid <= 0 || pid > 0xffff_ffffL) throw new IllegalArgumentException("DWORD PID required");
        Kernel32 api = Kernel32.INSTANCE;
        HANDLE handle = requireHandle(api.OpenProcess(0x1000 | 0x100000, false, (int) pid));
        try {
            requireLiveHandle(api, handle);
            ProcessIdentity observed = identity(api, handle, pid);
            String uptime = Long.toUnsignedString(api.GetTickCount64());
            requireLiveHandle(api, handle);
            return new LiveProcessObservation(observed, uptime);
        } finally { api.CloseHandle(handle); }
    }

    private static void requireLiveHandle(Kernel32 api, HANDLE handle) {
        int state = api.WaitForSingleObject(handle, 0);
        if (state == WAIT_FAILED) throw new Win32Exception(Native.getLastError());
        if (state != WAIT_TIMEOUT) throw new IllegalStateException("Native process is not live");
    }

    public static String currentMachineId() {
        requireWindows();
        char[] host = new char[32768]; IntByReference length = new IntByReference(host.length);
        require(Kernel32.INSTANCE.GetComputerNameEx(1, host, length));
        String hostname = new String(host, 0, length.getValue());
        String guid = Advapi32Util.registryGetStringValue(WinReg.HKEY_LOCAL_MACHINE,
                "SOFTWARE\\Microsoft\\Cryptography", "MachineGuid");
        String slug = hostname.trim().toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "-")
                .replaceAll("^-|-$", "");
        if (slug.isEmpty() || guid.isEmpty()) throw new IllegalStateException("Actual machine identity unavailable");
        slug = slug.substring(0, Math.min(32, slug.length())).replaceAll("-+$", "");
        try {
            String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(("windows-machine-guid:" + guid).getBytes(StandardCharsets.UTF_8)));
            return slug + "-" + digest.substring(0, 10);
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private HANDLE openStream(String path, int access, int disposition, WinBase.SECURITY_ATTRIBUTES attributes) {
        HANDLE handle = requireHandle(nativeApi.CreateFile(path, access, 7, attributes, disposition, 0x80, null));
        streams.add(handle); return handle;
    }

    private static ProcessIdentity identity(Kernel32 api, HANDLE process, long pid) {
        String filetime = creationFiletime(api, process);
        char[] image = new char[32768]; IntByReference count = new IntByReference(image.length);
        require(api.QueryFullProcessImageName(process, 0, image, count));
        return new ProcessIdentity(pid, filetime, new String(image, 0, count.getValue()));
    }
    private static String creationFiletime(Kernel32 api, HANDLE process) {
        WinBase.FILETIME created = new WinBase.FILETIME();
        require(api.GetProcessTimes(process, created, new WinBase.FILETIME(), new WinBase.FILETIME(), new WinBase.FILETIME()));
        return BigInteger.valueOf(Integer.toUnsignedLong(created.dwHighDateTime)).shiftLeft(32)
                .or(BigInteger.valueOf(Integer.toUnsignedLong(created.dwLowDateTime))).toString();
    }

    private static Memory environmentBlock(Map<String, String> environment) {
        TreeMap<String, String> sorted = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); sorted.putAll(environment);
        if (sorted.size() != environment.size()) throw new IllegalArgumentException("Duplicate environment keys");
        StringBuilder text = new StringBuilder();
        sorted.forEach((key, value) -> text.append(key).append('=').append(value).append('\0'));
        if (sorted.isEmpty()) text.append('\0');
        text.append('\0');
        byte[] encoded = text.toString().getBytes(StandardCharsets.UTF_16LE);
        Memory block = new Memory(encoded.length); block.write(0, encoded, 0, encoded.length); return block;
    }

    private static String commandLine(CommandSpec spec) {
        if (spec.executable().getFileName().toString().equalsIgnoreCase("cmd.exe")) {
            if (spec.arguments().size() != 3 || !spec.arguments().get(0).equals("/d")
                    || !spec.arguments().get(1).equals("/c") || !spec.arguments().get(2).matches("[^\\s\"&|<>^%!]+")) {
                throw new IllegalArgumentException("CMD accepts only the exact static batch path route");
            }
            return "cmd.exe /d /c " + spec.arguments().get(2);
        }
        List<String> words = new ArrayList<>(); words.add(spec.executable().toString()); words.addAll(spec.arguments());
        return words.stream().map(WindowsJobProcess::quoteArgument).reduce((a, b) -> a + " " + b).orElseThrow();
    }

    private static String quoteArgument(String word) {
        requireNoNul(word);
        StringBuilder out = new StringBuilder("\""); int backslashes = 0;
        for (char ch : word.toCharArray()) {
            if (ch == '\\') { backslashes++; continue; }
            if (ch == '"') out.append("\\".repeat(backslashes * 2 + 1));
            else out.append("\\".repeat(backslashes));
            out.append(ch); backslashes = 0;
        }
        return out.append("\\".repeat(backslashes * 2)).append('"').toString();
    }

    private static void requireNoNul(String value) {
        if (Objects.requireNonNull(value).indexOf('\0') >= 0) throw new IllegalArgumentException("NUL is forbidden");
    }
    private static void requireWindows() {
        String temporary = System.getProperty("jna.tmpdir", "");
        if (!System.getProperty("os.name", "").toLowerCase(Locale.ROOT).startsWith("windows")
                || temporary.isEmpty() || !Path.of(temporary).isAbsolute() || !Files.isDirectory(Path.of(temporary))) {
            throw new UnsupportedOperationException("Windows and explicit existing -Djna.tmpdir are required");
        }
        if (!Platform.isWindows() || Native.POINTER_SIZE != 8) throw new UnsupportedOperationException("64-bit Windows Job adapter required");
    }
    private void ensureOpen() { if (closed) throw new IllegalStateException("Job owner is closed"); }
    private static void require(boolean result) { if (!result) throw new Win32Exception(Native.getLastError()); }
    private static HANDLE requireHandle(HANDLE handle) {
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new Win32Exception(Native.getLastError());
        return handle;
    }
}
