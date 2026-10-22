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

    /** JNA 5.19.1 does not map Job APIs; these signatures use the Windows SDK ABI. */
    public interface JobKernel32 extends Kernel32 {
        HANDLE CreateJobObjectW(WinBase.SECURITY_ATTRIBUTES attributes, WString name);
        boolean SetInformationJobObject(HANDLE job, int kind, Pointer data, int length);
        boolean QueryInformationJobObject(HANDLE job, int kind, Pointer data, int length, IntByReference returned);
        boolean AssignProcessToJobObject(HANDLE job, HANDLE process);
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

    private WindowsJobProcess(JobKernel32 nativeApi, HANDLE job) {
        this.nativeApi = nativeApi; this.job = job;
    }

    public static WindowsJobProcess start(CommandSpec spec) throws IOException {
        requireWindows();
        if (!Files.isRegularFile(spec.executable()) || !Files.isDirectory(spec.cwd())) {
            throw new IllegalArgumentException("Actual executable and working directory must exist");
        }
        JobKernel32 api = Native.load("kernel32", JobKernel32.class, W32APIOptions.UNICODE_OPTIONS);
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
            startup.dwFlags = 0x100 | 0x1; startup.wShowWindow = new WORD(0);
            startup.hStdInput = owner.openStream("NUL", WinNT.GENERIC_READ, 3, inheritable);
            startup.hStdOutput = owner.openStream(spec.stdout().toString(), WinNT.GENERIC_WRITE, 1, inheritable);
            startup.hStdError = owner.openStream(spec.stderr().toString(), WinNT.GENERIC_WRITE, 1, inheritable);
            String command = commandLine(spec);
            try (Memory environment = environmentBlock(spec.environment())) {
                require(api.CreateProcessW(spec.executable().toString(), Native.toCharArray(command),
                        null, null, true, new DWORD(0x4 | 0x400 | 0x08000000), environment,
                        spec.cwd().toString(), startup, owner.process));
            }
            require(api.AssignProcessToJobObject(job, owner.process.hProcess));
            owner.identity = identity(api, owner.process.hProcess, Integer.toUnsignedLong(owner.process.dwProcessId.intValue()));
            if (!Files.isSameFile(Path.of(owner.identity.executable()), spec.executable())) {
                throw new IllegalStateException("Actual process image differs before resume");
            }
            if (api.ResumeThread(owner.process.hThread) == -1) throw new Win32Exception(Native.getLastError());
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
        ensureOpen(); Objects.requireNonNull(leaseDeadline); Objects.requireNonNull(periodicGuard);
        if (timeout.isZero() || timeout.isNegative()) throw new IllegalArgumentException("Finite positive timeout required");
        long deadline = Math.addExact(System.nanoTime(), timeout.toNanos());
        String reason = null; boolean interrupted = false;
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
        if (reason != null) terminate(124);
        for (int i = 0; i < 50 && accounting().activeProcesses() != 0; i++) {
            try { Thread.sleep(100); } catch (InterruptedException error) { interrupted = true; }
        }
        if (accounting().activeProcesses() != 0) {
            reason = reason == null ? "root_exited_with_live_children" : reason;
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
        if (exit.getValue() == STILL_ACTIVE || finalState.activeProcesses() != 0) reason = "job_cleanup_incomplete";
        if (finalState.peakJobMemoryBytes() > finalState.memoryLimitBytes()) reason = "observed_job_peak_exceeded_limit";
        CommandResult result = new CommandResult(identity(), exit.getValue(), (System.nanoTime() - started) / 1_000_000_000.0,
                finalState, reason);
        if (interrupted) Thread.currentThread().interrupt();
        return result;
    }

    @Override public void close() {
        if (closed) return;
        try { nativeApi.TerminateJobObject(job, 125); }
        finally {
            if (process.hThread != null) nativeApi.CloseHandle(process.hThread);
            if (process.hProcess != null) nativeApi.CloseHandle(process.hProcess);
            for (HANDLE stream : streams) nativeApi.CloseHandle(stream);
            nativeApi.CloseHandle(job); closed = true;
        }
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
        WinBase.FILETIME created = new WinBase.FILETIME();
        require(api.GetProcessTimes(process, created, new WinBase.FILETIME(), new WinBase.FILETIME(), new WinBase.FILETIME()));
        BigInteger filetime = BigInteger.valueOf(Integer.toUnsignedLong(created.dwHighDateTime)).shiftLeft(32)
                .or(BigInteger.valueOf(Integer.toUnsignedLong(created.dwLowDateTime)));
        char[] image = new char[32768]; IntByReference count = new IntByReference(image.length);
        require(api.QueryFullProcessImageName(process, 0, image, count));
        return new ProcessIdentity(pid, filetime.toString(), new String(image, 0, count.getValue()));
    }

    private static Memory environmentBlock(Map<String, String> environment) {
        TreeMap<String, String> sorted = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); sorted.putAll(environment);
        if (sorted.size() != environment.size()) throw new IllegalArgumentException("Duplicate environment keys");
        StringBuilder text = new StringBuilder();
        sorted.forEach((key, value) -> text.append(key).append('=').append(value).append('\0'));
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
