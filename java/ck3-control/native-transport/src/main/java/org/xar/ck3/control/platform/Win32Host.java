package org.xar.ck3.control.platform;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.Structure;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Read-only OS observations. Game mutation always remains in the original WindowsJobProcess. */
final class Win32Host {
    interface Api extends StdCallLibrary {
        HANDLE CreateToolhelp32Snapshot(int flags, int pid);
        boolean Process32FirstW(HANDLE snapshot, ProcessEntry entry);
        boolean Process32NextW(HANDLE snapshot, ProcessEntry entry);
        boolean Module32FirstW(HANDLE snapshot, ModuleEntry entry);
        boolean Module32NextW(HANDLE snapshot, ModuleEntry entry);
        HANDLE OpenProcess(int rights, boolean inherit, int pid);
        boolean CloseHandle(HANDLE handle);
        int WaitForSingleObject(HANDLE handle, int milliseconds);
        boolean GetExitCodeProcess(HANDLE handle, IntByReference code);
        boolean GetProcessTimes(HANDLE handle, LongByReference created, LongByReference exited,
                LongByReference kernel, LongByReference user);
        boolean QueryFullProcessImageNameW(HANDLE handle, int flags, char[] image, IntByReference length);
        boolean ReadProcessMemory(HANDLE process, Pointer address, Pointer buffer, long size, LongByReference read);
        HANDLE CreateMutexW(Pointer security, boolean initialOwner, String name);
        boolean ReleaseMutex(HANDLE mutex);
    }
    @Structure.FieldOrder({"size","usage","pid","heap","module","threads","parent","priority","flags","exe"})
    public static final class ProcessEntry extends Structure {
        public int size,usage,pid;
        public Pointer heap;
        public int module,threads,parent,priority,flags;
        public char[] exe = new char[260];
        public ProcessEntry() { size = size(); }
    }
    @Structure.FieldOrder({"size","module","pid","globalUsage","processUsage","base","imageSize","handle","name","path"})
    public static final class ModuleEntry extends Structure {
        public int size,module,pid,globalUsage,processUsage;
        public Pointer base;
        public int imageSize;
        public HANDLE handle;
        public char[] name = new char[256], path = new char[260];
        public ModuleEntry() { size = size(); }
    }
    record ProcessRow(long pid, long parentPid, WindowsJobProcess.ProcessIdentity identity) { }
    enum ProcessState { RUNNING, SIGNALLED, UNAVAILABLE }
    enum ProcessOperation { OPEN, WAIT_BEFORE, TIMES, EXIT_CODE, IMAGE, IMAGE_PATH, WAIT_AFTER }
    record ProcessFailure(ProcessOperation operation, Integer win32Error, String detail) {
        ProcessFailure { Objects.requireNonNull(operation); Objects.requireNonNull(detail); }
    }
    /** Raw FILETIME observations are strings; zero exit time never supplies liveness evidence. */
    record ProcessTimes(String creationFiletimeDecimal, String exitFiletimeDecimal) {
        ProcessTimes { decimal(creationFiletimeDecimal); decimal(exitFiletimeDecimal); }
    }
    record ProcessObservation(long pid, long parentPid, ProcessState state, Long waitBefore, Long waitAfter,
            ProcessTimes times, Long exitCode, String executable, List<ProcessFailure> failures) {
        ProcessObservation {
            if (pid <= 0 || pid > 0xffff_ffffL || parentPid < 0 || parentPid > 0xffff_ffffL)
                throw new IllegalArgumentException("DWORD process identities required");
            Objects.requireNonNull(state); failures = List.copyOf(failures);
            if ((waitBefore != null && (waitBefore < 0 || waitBefore > 0xffff_ffffL))
                    || (waitAfter != null && (waitAfter < 0 || waitAfter > 0xffff_ffffL)))
                throw new IllegalArgumentException("unsigned DWORD wait results required");
            if (exitCode != null && (exitCode < 0 || exitCode > 0xffff_ffffL))
                throw new IllegalArgumentException("unsigned DWORD exit code required");
            if (state != classify(waitBefore, waitAfter, times, exitCode, executable, failures))
                throw new IllegalArgumentException("process state differs from original signal/identity observations");
        }
        ProcessRow running() throws IOException {
            if (state != ProcessState.RUNNING) throw new IOException("Process lacks a complete live identity: " + this);
            return new ProcessRow(pid, parentPid, new WindowsJobProcess.ProcessIdentity(pid,
                    times.creationFiletimeDecimal(), executable));
        }
    }
    record ProcessInventory(String exactName, String observedAtUtc, List<ProcessObservation> observations) {
        ProcessInventory {
            Objects.requireNonNull(exactName); Objects.requireNonNull(observedAtUtc);
            Instant.parse(observedAtUtc);
            observations = List.copyOf(observations);
            if (exactName.isBlank() || exactName.length() > 260 || observations.size() > 32768)
                throw new IllegalArgumentException("bounded named process inventory required");
        }
        /** A signalled retained process is excluded; an unreadable live/unknown row still blocks. */
        List<ProcessRow> qualifiedRunning() throws IOException {
            List<ProcessRow> result = new ArrayList<>();
            for (ProcessObservation observation : observations) {
                if (observation.state() == ProcessState.UNAVAILABLE)
                    throw new IOException("Process inventory contains an unqualified observation: " + observation);
                if (observation.state() == ProcessState.RUNNING) result.add(observation.running());
            }
            return List.copyOf(result);
        }
    }
    record Module(long base, long size, String path) { }
    private static final class Holder { static final Api API = Native.load("kernel32", Api.class, W32APIOptions.UNICODE_OPTIONS); }
    private Win32Host() { }
    private static Api api() throws IOException {
        if (Native.POINTER_SIZE != 8 || !System.getProperty("os.name", "").startsWith("Windows")) throw new IOException("x64 Windows resource provider required");
        return Holder.API;
    }
    static void deadline(Instant deadline) throws IOException {
        if (deadline == null || !Instant.now().isBefore(deadline)) throw new IOException("Lifecycle observation deadline expired");
    }
    private static HANDLE valid(HANDLE handle) throws IOException {
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw failure("native handle acquire");
        return handle;
    }
    static IOException failure(String operation) { return new IOException(operation + " Win32=" + Native.getLastError()); }
    static List<ProcessRow> processes(String exactName, Instant deadline) throws IOException {
        return processInventory(exactName, deadline).qualifiedRunning();
    }
    static ProcessInventory processInventory(String exactName, Instant deadline) throws IOException {
        deadline(deadline);
        Api k = api(); HANDLE snapshot = valid(k.CreateToolhelp32Snapshot(2, 0));
        List<ProcessObservation> result = new ArrayList<>();
        try {
            ProcessEntry entry = new ProcessEntry(); boolean more = k.Process32FirstW(snapshot, entry); int count = 0;
            while (more) {
                deadline(deadline); if (++count > 32768) throw new IOException("Process snapshot exceeds32768");
                if (Native.toString(entry.exe).equalsIgnoreCase(exactName)) {
                    result.add(inspectProcess(Integer.toUnsignedLong(entry.pid), Integer.toUnsignedLong(entry.parent), deadline));
                }
                more = k.Process32NextW(snapshot, entry);
            }
            if (Native.getLastError() != 18) throw failure("complete process snapshot");
            return new ProcessInventory(exactName, Instant.now().toString(), result);
        } finally { if (!k.CloseHandle(snapshot)) throw failure("process snapshot close"); }
    }
    static ProcessObservation inspectProcess(long pid, long parentPid, Instant deadline) throws IOException {
        deadline(deadline);
        if (pid <= 0 || pid > 0xffff_ffffL) throw new IOException("DWORD process identity required");
        Api k=api(); HANDLE handle=k.OpenProcess(0x1000 | 0x100000,false,(int)pid);
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            return new ProcessObservation(pid, parentPid, ProcessState.UNAVAILABLE, null, null, null, null, null,
                    List.of(nativeFailure(ProcessOperation.OPEN)));
        }
        try (ReadProcess process = new ReadProcess(k,handle,pid)) { return process.observe(parentPid); }
    }
    private static void decimal(String value) {
        if (value == null || !value.matches("0|[1-9][0-9]*") || new BigInteger(value).bitLength() > 64)
            throw new IllegalArgumentException("canonical unsigned decimal FILETIME required");
    }
    private static ProcessState classify(Long before, Long after, ProcessTimes times, Long exitCode,
            String executable, List<ProcessFailure> failures) {
        // Wait is authoritative even for exit259, exit FILETIME0 or an unavailable image.
        if (after != null && after == 0L) return ProcessState.SIGNALLED;
        if (before != null && before == 258L && after != null && after == 258L
                && times != null && !times.creationFiletimeDecimal().equals("0")
                && exitCode != null && exitCode == 259L && executable != null && !executable.isBlank() && failures.isEmpty())
            return ProcessState.RUNNING;
        return ProcessState.UNAVAILABLE;
    }
    static Module module(long pid, Path exactPath, Instant deadline) throws IOException {
        Api k = api(); HANDLE snapshot = valid(k.CreateToolhelp32Snapshot(0x18, (int)pid));
        Module found = null;
        try {
            ModuleEntry entry = new ModuleEntry(); boolean more = k.Module32FirstW(snapshot, entry); int count = 0;
            while (more) {
                deadline(deadline); if (++count > 4096) throw new IOException("Module snapshot exceeds4096");
                Path actual = Path.of(Native.toString(entry.path)).toRealPath();
                if (actual.equals(exactPath.toRealPath())) {
                    if (found != null) throw new IOException("Duplicate exact loaded module");
                    found = new Module(Pointer.nativeValue(entry.base), Integer.toUnsignedLong(entry.imageSize), actual.toString());
                }
                more = k.Module32NextW(snapshot, entry);
            }
            if (Native.getLastError() != 18) throw failure("complete module snapshot");
            if (found == null) throw new IOException("Exact source module is not loaded"); return found;
        } finally { if (!k.CloseHandle(snapshot)) throw failure("module snapshot close"); }
    }
    static ReadProcess open(long pid) throws IOException {
        return open(pid, 0x1000 | 0x10 | 0x100000);
    }
    private static ReadProcess open(long pid, int rights) throws IOException {
        if (pid <= 0 || pid > 0xffff_ffffL) throw new IOException("DWORD process identity required");
        Api k = api(); return new ReadProcess(k, valid(k.OpenProcess(rights, false, (int)pid)), pid);
    }
    static final class ReadProcess implements AutoCloseable {
        private final Api api;
        private final HANDLE handle;
        private final long pid;
        private boolean closed;
        ReadProcess(Api api, HANDLE handle, long pid) { this.api=api; this.handle=handle; this.pid=pid; }
        WindowsJobProcess.ProcessIdentity identity() throws IOException {
            return observe(0).running().identity();
        }
        ProcessObservation observe(long parentPid) throws IOException {
            if (closed) throw new IOException("Original observed process handle is closed");
            List<ProcessFailure> failures = new ArrayList<>();
            long before = Integer.toUnsignedLong(api.WaitForSingleObject(handle,0));
            if (before != 0 && before != 258) failures.add(nativeFailure(ProcessOperation.WAIT_BEFORE));
            LongByReference birth = new LongByReference();
            LongByReference exitTime = new LongByReference();
            ProcessTimes times = null;
            if (api.GetProcessTimes(handle,birth,exitTime,new LongByReference(),new LongByReference()))
                times = new ProcessTimes(Long.toUnsignedString(birth.getValue()), Long.toUnsignedString(exitTime.getValue()));
            else failures.add(nativeFailure(ProcessOperation.TIMES));
            IntByReference code = new IntByReference(); Long exitCode = null;
            if (api.GetExitCodeProcess(handle,code)) exitCode = Integer.toUnsignedLong(code.getValue());
            else failures.add(nativeFailure(ProcessOperation.EXIT_CODE));
            char[] image = new char[32768]; IntByReference size = new IntByReference(image.length);
            String executable = null;
            if (!api.QueryFullProcessImageNameW(handle,0,image,size)) failures.add(nativeFailure(ProcessOperation.IMAGE));
            else if (size.getValue() <= 0 || size.getValue() > image.length)
                failures.add(new ProcessFailure(ProcessOperation.IMAGE, null, "invalid image character count"));
            else try { executable = Path.of(new String(image,0,size.getValue())).toRealPath().toString(); }
            catch (IOException | RuntimeException unavailable) {
                failures.add(new ProcessFailure(ProcessOperation.IMAGE_PATH, null, unavailable.toString()));
            }
            long after = Integer.toUnsignedLong(api.WaitForSingleObject(handle,0));
            if (after != 0 && after != 258) failures.add(nativeFailure(ProcessOperation.WAIT_AFTER));
            return new ProcessObservation(pid, parentPid, classify(before,after,times,exitCode,executable,failures),
                    before, after, times, exitCode, executable, failures);
        }
        byte[] read(long address, int count, Instant deadline) throws IOException {
            deadline(deadline);
            if (closed || address < 0x10000 || address > 0x7fff_ffff_ffffL-count || count < 1 || count > 1024)
                throw new IOException("Bounded read-only native address required");
            try (Memory memory = new Memory(count)) {
                LongByReference bytes = new LongByReference();
                if (!api.ReadProcessMemory(handle,new Pointer(address),memory,count,bytes) || bytes.getValue()!=count) throw failure("ReadProcessMemory");
                deadline(deadline); return memory.getByteArray(0,count);
            }
        }
        @Override public void close() throws IOException {
            if (!closed) { closed=true; if (!api.CloseHandle(handle)) throw failure("read-only process close"); }
        }
    }
    private static ProcessFailure nativeFailure(ProcessOperation operation) {
        int error = Native.getLastError(); return new ProcessFailure(operation, error, "Win32=" + error);
    }
    static Mutex mutex(String name, Instant deadline) throws IOException, InterruptedException {
        Api k=api(); HANDLE handle=valid(k.CreateMutexW(Pointer.NULL,false,name)); boolean owned=false;
        try {
            while (true) {
                deadline(deadline); int status=k.WaitForSingleObject(handle,50);
                if (status==0) { owned=true; return new Mutex(k,handle); }
                if (status==128) throw new IOException("Previous Java launch mutex owner abandoned; require explicit cleanup review");
                if (status!=258) throw failure("launch mutex wait");
                if (Thread.currentThread().isInterrupted()) throw new InterruptedException("launch mutex interrupted");
            }
        } finally { if (!owned) k.CloseHandle(handle); }
    }
    static final class Mutex implements AutoCloseable {
        private final Api api; private final HANDLE handle;
        private boolean released;
        private Mutex(Api api,HANDLE handle){this.api=api;this.handle=handle;}
        void requireHeld()throws IOException{if(released)throw new IOException("Original launch mutex was released");}
        @Override public void close() throws IOException {
            if(released)return;released=true;
            boolean released=api.ReleaseMutex(handle), closed=api.CloseHandle(handle);
            if (!released || !closed) throw failure("launch mutex release");
        }
    }
}
