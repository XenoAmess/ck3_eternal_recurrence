package org.xar.ck3.control.build;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.platform.win32.BaseTSD.SIZE_T;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import com.sun.jna.win32.W32APIOptions;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Actual pre-resume resources only. No Game/Native authority, injector or process discovery. */
public final class WindowsPreloadCustody {
    private WindowsPreloadCustody() { }
    public record DllRef(ControlBuild.FileRef file, Instant deadline, WindowsJobProcess.StdioGuard guard) {
        public DllRef {
            Objects.requireNonNull(file); Objects.requireNonNull(deadline); Objects.requireNonNull(guard);
        }
    }
    /** Requested reference plus actual held-file metadata; empty sha256 means content was not hashed. */
    public record DllReadback(ControlBuild.FileRef originalRef, SharedSourceFiles.NativeFile nativeFile,
            String fullDosPath, String kernelNtPath, long size, String sha256) { }
    public record PreloadImage(String allocationBaseDecimal, String mappedNtPath) { }
    public record LoadedModule(String baseDecimal, long imageSize, String fullDosPath, String mappedNtPath,
            Optional<SharedSourceFiles.NativeFile> heldFile) { }
    public record LoadedObservation(WindowsJobProcess.ProcessIdentity targetIdentity, DllReadback dll,
            List<LoadedModule> modules, LoadedModule matchingDll) {
        public LoadedObservation { modules = List.copyOf(modules); Objects.requireNonNull(matchingDll); }
    }
    /** Only the resource producer can attest a valid original server awaiting its client. */
    public static final class PipeNotConnected extends IOException {
        private static final long serialVersionUID = 1L;
        private final int win32Error;
        private PipeNotConnected(int win32Error) {
            super("Actual verified server has no connected client: Win32=" + win32Error); this.win32Error = win32Error;
        }
        public int win32Error() { return win32Error; }
    }
    public interface Api extends WindowsJobProcess.JobKernel32 {
        void GetNativeSystemInfo(Pointer info);
        SIZE_T VirtualQueryEx(HANDLE process, Pointer address, Pointer info, SIZE_T bytes);
        int GetFinalPathNameByHandleW(HANDLE file, char[] output, int count, int flags);
        HANDLE CreateFileMappingW(HANDLE file, WinBase.SECURITY_ATTRIBUTES attributes, int protect,
                int high, int low, WString name);
        Pointer MapViewOfFile(HANDLE mapping, int access, int high, int low, SIZE_T bytes);
        boolean GetNamedPipeClientProcessId(HANDLE pipe, IntByReference pid);
        boolean GetNamedPipeServerProcessId(HANDLE pipe, IntByReference pid);
        boolean GetNamedPipeHandleStateW(HANDLE pipe, IntByReference state, IntByReference instances,
                IntByReference maximumCollection, IntByReference collectionTimeout, char[] username, int characters);
    }
    public interface Psapi extends StdCallLibrary {
        boolean EnumProcessModulesEx(HANDLE process, Pointer modules, int bytes, IntByReference needed, int flags);
        boolean GetModuleInformation(HANDLE process, Pointer module, Pointer info, int bytes);
        int GetModuleFileNameExW(HANDLE process, Pointer module, char[] name, int count);
        int GetMappedFileNameW(HANDLE process, Pointer address, char[] name, int count);
    }
    public interface NtApi extends StdCallLibrary {
        int NtQueryObject(HANDLE object, int kind, Pointer output, int bytes, IntByReference needed);
    }
    private static final class APIs {
        static final Api K = Native.load("kernel32", Api.class, W32APIOptions.UNICODE_OPTIONS);
        static final Psapi P = Native.load("psapi", Psapi.class, W32APIOptions.UNICODE_OPTIONS);
    }
    public static Lease prepare(WindowsJobProcess.SuspendedTarget target, DllRef reference) throws IOException {
        Objects.requireNonNull(target); Objects.requireNonNull(reference); target.requireActive();
        Lease lease = new Lease(target, reference);
        target.retain(lease);
        try {
            lease.process = target.duplicateRead();
            lease.file = valid(APIs.K.CreateFile(reference.file().path(), 0x80000000, 1, null, 3, 0x80, null));
            lease.expected = lease.readDll();
            lease.verify();
            return lease;
        } catch (IOException | RuntimeException failure) {
            try { lease.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        }
    }
    public static final class Lease implements AutoCloseable {
        private final WindowsJobProcess.SuspendedTarget source;
        private final WindowsJobProcess.ProcessIdentity identity;
        private final DllRef reference;
        private final long monotonicDeadline;
        private final List<Endpoint> endpoints = new ArrayList<>();
        private HANDLE process, file;
        private DllReadback expected;
        private boolean closed, runtimeActive;
        private Lease(WindowsJobProcess.SuspendedTarget source, DllRef reference) throws IOException {
            this.source = source; this.identity = source.identity(); this.reference = reference;
            Duration remaining = Duration.between(Instant.now(), reference.deadline());
            if (remaining.isNegative() || remaining.isZero())
                throw new IOException("preload startup deadline expired");
            try { monotonicDeadline = System.nanoTime() + remaining.toNanos(); }
            catch (ArithmeticException invalid) { throw new IOException("startup duration cannot be represented in nanoseconds", invalid); }
        }
        boolean from(WindowsJobProcess.SuspendedTarget target) { return source == target && !closed && process != null && file != null; }
        public WindowsJobProcess.ProcessIdentity targetIdentity() { return identity; }
        public synchronized DllReadback dllReadback() throws IOException { verify(); return expected; }
        /** Compatibility accessor: startup no longer walks the complete address-space image catalogue. */
        public synchronized List<PreloadImage> preloadImages() throws IOException { verify(); return List.of(); }
        private void budget() throws IOException {
            if (closed) throw new IOException("preload resource closed");
            if (!runtimeActive && (!Instant.now().isBefore(reference.deadline()) || System.nanoTime() - monotonicDeadline >= 0))
                throw new IOException("preload startup deadline expired");
        }
        /** Transfer the existing live resource from startup budget to its owner's explicit lifetime. */
        public synchronized void activateRuntime() throws IOException {
            if (runtimeActive) throw new IOException("preload runtime is already activated");
            verify();
            runtimeActive = true;
        }
        /** Resource availability only; this method grants no source or module-roster proof. */
        public synchronized void verify() throws IOException {
            budget();
            if (process == null || file == null) throw new IOException("preload resources incomplete");
            if (APIs.K.WaitForSingleObject(process, 0) != 258) throw new IOException("held target is not live");
        }
        private DllReadback readDll() throws IOException {
            budget();
            SharedSourceFiles.NativeFile actual = SharedSourceFiles.nativeHeldFile(file);
            return new DllReadback(reference.file(), actual, finalName(file, 0), finalName(file, 2),
                    actual.logicalBytes(), "");
        }
        public synchronized LoadedObservation observeLoaded() throws IOException {
            verify();
            List<LoadedModule> observed = modules();
            if (observed.isEmpty()) throw new IOException("requested DLL is not currently observed in the held process");
            return new LoadedObservation(identity, expected, observed, observed.getFirst());
        }
        /** One current enumeration, used only to locate the requested DLL; unrelated modules are not audited. */
        private List<LoadedModule> modules() throws IOException {
            budget();
            int capacity = 4096;
            try (Memory handles = new Memory(capacity * Native.POINTER_SIZE); Memory info = new Memory(24)) {
                IntByReference bytes = new IntByReference();
                need(APIs.P.EnumProcessModulesEx(process, handles, (int) handles.size(), bytes, 3), "enumerate current modules");
                int count = Math.min(capacity, Math.max(0, bytes.getValue()) / Native.POINTER_SIZE);
                for (int i = 0; i < count; i++) {
                    Pointer module = handles.getPointer((long) i * Native.POINTER_SIZE);
                    char[] name = new char[32768];
                    int length = APIs.P.GetModuleFileNameExW(process, module, name, name.length);
                    // Other modules may naturally load or unload during this observation.
                    if (length <= 0 || length >= name.length) continue;
                    String dos = normalizeDos(new String(name, 0, length));
                    if (!dos.equalsIgnoreCase(expected.fullDosPath())) continue;
                    need(APIs.P.GetModuleInformation(process, module, info, 24), "requested module information");
                    long base = Pointer.nativeValue(info.getPointer(0));
                    long size = Integer.toUnsignedLong(info.getInt(8));
                    return List.of(new LoadedModule(Long.toUnsignedString(base), size, dos,
                            mappedName(process, base), Optional.of(expected.nativeFile())));
                }
                return List.of();
            }
        }
        public synchronized Endpoint retainOwnerServer(WindowsJobProcess.OwnedStdio actualOwner,
                String handleDecimal, String exactPipeName) throws IOException {
            verify(); Objects.requireNonNull(actualOwner); pipeName(exactPipeName);
            HANDLE duplicate = actualOwner.duplicateOwnedHandle(handleDecimal);
            Endpoint endpoint = new Endpoint(this, actualOwner, duplicate, exactPipeName);
            endpoints.add(endpoint);
            try { endpoint.verify(); return endpoint; }
            catch (IOException | RuntimeException failure) {
                try { endpoint.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        }
        @Override public synchronized void close() throws IOException {
            closed = true; IOException failure = null;
            for (Endpoint endpoint : endpoints) try { endpoint.close(); } catch (IOException error) { failure = error; }
            if (file != null) { if (APIs.K.CloseHandle(file)) file = null; else failure = error("close held DLL"); }
            if (process != null) { if (APIs.K.CloseHandle(process)) process = null; else failure = error("close held target"); }
            if (failure != null) throw failure;
        }
    }
    public static final class Endpoint implements AutoCloseable {
        private final Lease lease;
        private final WindowsJobProcess.OwnedStdio owner;
        private final String name;
        private HANDLE pipe;
        private Endpoint(Lease lease, WindowsJobProcess.OwnedStdio owner, HANDLE pipe, String name) {
            this.lease = lease; this.owner = owner; this.pipe = pipe; this.name = name;
        }
        public WindowsJobProcess.ProcessIdentity ownerIdentity() { return owner.identity(); }
        public WindowsJobProcess.ProcessIdentity targetIdentity() { return lease.identity; }
        public String pipeName() { return name; }
        /** Read the retained pipe state; no repeated owner/source or kernel-name certification. */
        public void verify() throws IOException {
            synchronized (lease) {
                lease.verify();
                if (pipe == null) throw new IOException("endpoint closed");
                requireNonblockingPipe();
                IntByReference client = new IntByReference();
                if (!APIs.K.GetNamedPipeClientProcessId(pipe, client)) {
                    int error = Native.getLastError();
                    if (error != 233 && error != 1168) throw new IOException("client PID Win32=" + error);
                    throw new PipeNotConnected(error);
                }
            }
        }
        private void requireNonblockingPipe() throws IOException {
            IntByReference state = new IntByReference();
            need(APIs.K.GetNamedPipeHandleStateW(pipe, state, null, null, null, null, 0),
                    "actual server pipe mode");
            if ((state.getValue() & 1) == 0)
                throw new IOException("PIPE_NOWAIT server required; PIPE_WAIT endpoint unavailable");
        }
        @Override public void close() throws IOException {
            synchronized (lease) {
                if (pipe != null) { need(APIs.K.CloseHandle(pipe), "close retained endpoint duplicate"); pipe = null; }
            }
        }
    }
    private static String pipeName(String value) throws IOException {
        if (value == null || !value.startsWith("\\\\.\\pipe\\") || value.length() > 240
                || !value.substring(9).matches("[A-Za-z0-9_.-]{1,231}")) throw new IOException("exact local pipe name required");
        return value;
    }
    private static String mappedName(HANDLE process, long base) throws IOException {
        char[] name = new char[32768]; int length = APIs.P.GetMappedFileNameW(process, new Pointer(base), name, name.length);
        if (length <= 0 || length >= name.length - 1) throw error("kernel mapped path");
        String value = new String(name, 0, length);
        if (!value.startsWith("\\Device\\") || value.indexOf('\0') >= 0) throw new IOException("kernel mapped NT path required");
        return value;
    }
    private static String finalName(HANDLE file, int flags) throws IOException {
        char[] name = new char[32768]; int count = APIs.K.GetFinalPathNameByHandleW(file, name, name.length, flags);
        if (count <= 0 || count >= name.length - 1) throw error("held final path");
        String result = new String(name, 0, count); return flags == 0 ? normalizeDos(result) : result;
    }
    private static String normalizeDos(String value) {
        return value.startsWith("\\\\?\\") ? value.substring(4) : value;
    }
    private static String lastName(String value) { return value.substring(value.lastIndexOf('\\') + 1); }
    private static HANDLE valid(HANDLE value) throws IOException {
        if (value == null || WinBase.INVALID_HANDLE_VALUE.equals(value)) throw error("acquire held resource"); return value;
    }
    private static void need(boolean success, String operation) throws IOException { if (!success) throw error(operation); }
    private static IOException error(String operation) { return new IOException(operation + " Win32=" + Native.getLastError()); }
}
