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
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.TreeMap;

/** Actual pre-resume resources only. No Game/Native authority, injector or process discovery. */
public final class WindowsPreloadCustody {
    private WindowsPreloadCustody() { }
    public record DllRef(ControlBuild.FileRef file, Instant deadline, WindowsJobProcess.StdioGuard guard) {
        public DllRef {
            Objects.requireNonNull(file); Objects.requireNonNull(deadline); Objects.requireNonNull(guard);
            if (file.bytes() < 1 || file.bytes() > (256L << 20)) throw new IllegalArgumentException("bounded pinned file required");
        }
    }
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
        static final NtApi N = Native.load("ntdll", NtApi.class);
    }
    public static Lease prepare(WindowsJobProcess.SuspendedTarget target, DllRef reference) throws IOException {
        Objects.requireNonNull(target); Objects.requireNonNull(reference); target.requireActive();
        Lease lease = new Lease(target, reference);
        target.retain(lease);
        try {
            lease.process = target.duplicateRead();
            SharedSourceFiles.plainAncestors(Path.of(reference.file().path()));
            lease.file = valid(APIs.K.CreateFile(reference.file().path(), 0x80000000, 1, null, 3, 0x80, null));
            lease.expected = lease.readDll();
            lease.verify();
            List<PreloadImage> first = lease.walkImages(), second = lease.walkImages();
            if (!first.equals(second)) throw new IOException("preload MEM_IMAGE roster changed");
            String basename = Path.of(lease.expected.fullDosPath()).getFileName().toString();
            for (PreloadImage image : first)
                if (lastName(image.mappedNtPath()).equalsIgnoreCase(basename)) throw new IOException("DLL basename already mapped before resume");
            lease.preload = first; target.requireActive(); lease.verify();
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
        private List<PreloadImage> preload = List.of();
        private boolean closed;
        private Lease(WindowsJobProcess.SuspendedTarget source, DllRef reference) throws IOException {
            this.source = source; this.identity = source.identity(); this.reference = reference;
            Duration remaining = Duration.between(Instant.now(), reference.deadline());
            if (remaining.isNegative() || remaining.isZero() || remaining.compareTo(Duration.ofDays(1)) > 0)
                throw new IOException("finite preload deadline within one day required");
            monotonicDeadline = System.nanoTime() + remaining.toNanos();
        }
        boolean from(WindowsJobProcess.SuspendedTarget target) { return source == target && !closed && !preload.isEmpty(); }
        public WindowsJobProcess.ProcessIdentity targetIdentity() { return identity; }
        public synchronized DllReadback dllReadback() throws IOException { verify(); return expected; }
        public synchronized List<PreloadImage> preloadImages() throws IOException { verify(); return preload; }
        private void budget() throws IOException {
            if (closed || !Instant.now().isBefore(reference.deadline()) || System.nanoTime() - monotonicDeadline >= 0)
                throw new IOException("preload resource closed or deadline expired");
        }
        public synchronized void verify() throws IOException {
            budget(); reference.guard().verify(); budget();
            if (process == null || file == null) throw new IOException("preload resources incomplete");
            if (APIs.K.WaitForSingleObject(process, 0) != 258) throw new IOException("held target is not live");
            int pid = APIs.K.GetProcessId(process);
            WinBase.FILETIME birth = new WinBase.FILETIME();
            need(APIs.K.GetProcessTimes(process, birth, new WinBase.FILETIME(), new WinBase.FILETIME(), new WinBase.FILETIME()), "held process birth");
            String created = BigInteger.valueOf(Integer.toUnsignedLong(birth.dwHighDateTime)).shiftLeft(32)
                    .or(BigInteger.valueOf(Integer.toUnsignedLong(birth.dwLowDateTime))).toString();
            char[] image = new char[32768]; IntByReference count = new IntByReference(image.length);
            need(APIs.K.QueryFullProcessImageName(process, 0, image, count), "held image");
            if (Integer.toUnsignedLong(pid) != identity.pid() || !created.equals(identity.creationFiletimeDecimal())
                    || !Path.of(new String(image, 0, count.getValue())).equals(Path.of(identity.executable())))
                throw new IOException("held target generation differs");
            DllReadback actual = readDll();
            if (expected != null && (!actual.nativeFile().identityKey().equals(expected.nativeFile().identityKey())
                    || actual.size() != expected.size() || !actual.sha256().equals(expected.sha256())
                    || !actual.fullDosPath().equalsIgnoreCase(expected.fullDosPath())
                    || !actual.kernelNtPath().equalsIgnoreCase(expected.kernelNtPath())))
                throw new IOException("continuous DLL lease drift");
            reference.guard().verify(); budget();
        }
        private DllReadback readDll() throws IOException {
            budget();
            SharedSourceFiles.NativeFile before = SharedSourceFiles.nativeHeldFile(file);
            String dos = finalName(file, 0), nt = finalName(file, 2);
            if (!Path.of(dos).equals(Path.of(reference.file().path()).toAbsolutePath().normalize()))
                throw new IOException("held final DOS path differs; no aliases");
            if (!nt.startsWith("\\Device\\")) throw new IOException("kernel DLL path unavailable");
            String hash = hashHeld(file, before.logicalBytes());
            SharedSourceFiles.NativeFile after = SharedSourceFiles.nativeHeldFile(file);
            if (!before.identityKey().equals(after.identityKey()) || before.logicalBytes() != after.logicalBytes()
                    || before.logicalBytes() != reference.file().bytes() || !hash.equals(reference.file().sha256()))
                throw new IOException("held DLL identity or exact source bytes differ");
            return new DllReadback(reference.file(), after, dos, nt, after.logicalBytes(), hash);
        }
        private String hashHeld(HANDLE handle, long size) throws IOException {
            if (size < 1 || size > (256L << 20)) throw new IOException("bounded held DLL required");
            HANDLE mapping = valid(APIs.K.CreateFileMappingW(handle, null, 2, 0, 0, null));
            Pointer address = null;
            try {
                address = APIs.K.MapViewOfFile(mapping, 4, 0, 0, new SIZE_T(0));
                if (address == null) throw error("map held DLL");
                MessageDigest digest;
                try { digest = MessageDigest.getInstance("SHA-256"); }
                catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
                for (long offset = 0; offset < size; offset += 65536) {
                    budget(); digest.update(address.getByteArray(offset, (int) Math.min(65536, size - offset)));
                }
                return HexFormat.of().formatHex(digest.digest());
            } finally {
                try { if (address != null) need(APIs.K.UnmapViewOfFile(address), "unmap held DLL"); }
                finally { need(APIs.K.CloseHandle(mapping), "close DLL mapping"); }
            }
        }
        private List<PreloadImage> walkImages() throws IOException {
            budget();
            try (Memory system = new Memory(48); Memory region = new Memory(48)) {
                APIs.K.GetNativeSystemInfo(system);
                long page = Integer.toUnsignedLong(system.getInt(4)), minimum = system.getLong(8), maximum = system.getLong(16);
                if (page == 0 || (page & (page - 1)) != 0 || minimum <= 0 || maximum < minimum
                        || minimum % page != 0 || (maximum + 1) % page != 0) throw new IOException("complete x64 address bounds required");
                TreeMap<Long, String> images = new TreeMap<>(); long position = minimum; int regions = 0;
                while (position <= maximum) {
                    budget(); if (++regions > 65536) throw new IOException("preload region bound exceeded");
                    long returned = APIs.K.VirtualQueryEx(process, new Pointer(position), region, new SIZE_T(48)).longValue();
                    if (returned != 48) throw error("complete preload VirtualQueryEx");
                    long base = region.getLong(0), allocation = region.getLong(8), size = region.getLong(24);
                    int state = region.getInt(32), kind = region.getInt(40);
                    long end;
                    try { end = Math.addExact(base, size); } catch (ArithmeticException invalid) { throw new IOException("region overflow", invalid); }
                    if (base < 0 || base > position || size <= 0 || end <= position || base % page != 0 || size % page != 0)
                        throw new IOException("incomplete preload region advance");
                    if (state != 0x1000 && state != 0x2000 && state != 0x10000) throw new IOException("unknown region state");
                    if (state != 0x10000) {
                        if (kind != 0x20000 && kind != 0x40000 && kind != 0x1000000) throw new IOException("unknown allocation kind");
                        if (kind == 0x1000000) {
                            if (allocation < minimum || allocation > base || allocation % page != 0) throw new IOException("invalid image allocation");
                            if (!images.containsKey(allocation)) {
                                if (images.size() >= 4096) throw new IOException("preload image limit");
                                images.put(allocation, mappedName(process, allocation));
                            }
                        }
                    }
                    position = end;
                }
                if (images.isEmpty()) throw new IOException("empty preload image walk");
                return images.entrySet().stream().map(e -> new PreloadImage(Long.toUnsignedString(e.getKey()), e.getValue())).toList();
            }
        }
        public synchronized LoadedObservation observeLoaded() throws IOException {
            verify(); List<LoadedModule> first = modules(), second = modules();
            if (!first.equals(second)) throw new IOException("loaded roster changed; no partial observation");
            List<LoadedModule> matches = first.stream().filter(m -> m.heldFile().isPresent()).toList();
            long basenames = first.stream().filter(m -> lastName(m.fullDosPath()).equalsIgnoreCase(lastName(expected.fullDosPath()))).count();
            if (matches.size() != 1 || basenames != 1) throw new IOException("exact held DLL is absent or ambiguous in loaded roster");
            verify(); return new LoadedObservation(identity, expected, first, matches.getFirst());
        }
        private List<LoadedModule> modules() throws IOException {
            budget(); int capacity = 1024;
            for (int attempt = 0; attempt < 2; attempt++) {
                try (Memory handles = new Memory(capacity * 8L); Memory info = new Memory(24)) {
                    IntByReference bytes = new IntByReference();
                    need(APIs.P.EnumProcessModulesEx(process, handles, capacity * 8, bytes, 3), "complete module roster");
                    if (bytes.getValue() < 0 || bytes.getValue() % 8 != 0 || bytes.getValue() > 4096 * 8) throw new IOException("module extent invalid");
                    int count = bytes.getValue() / 8;
                    if (count > capacity) { capacity = count; continue; }
                    if (count == 0) throw new IOException("empty loaded roster");
                    TreeMap<Long, LoadedModule> result = new TreeMap<>();
                    for (int i = 0; i < count; i++) {
                        budget(); Pointer module = handles.getPointer(i * 8L);
                        need(APIs.P.GetModuleInformation(process, module, info, 24), "module information");
                        long base = Pointer.nativeValue(info.getPointer(0)), size = Integer.toUnsignedLong(info.getInt(8));
                        if (base <= 0 || size <= 0) throw new IOException("invalid actual module");
                        char[] name = new char[32768]; int length = APIs.P.GetModuleFileNameExW(process, module, name, name.length);
                        if (length <= 0 || length >= name.length - 1) throw error("full module DOS path");
                        String dos = normalizeDos(new String(name, 0, length)), nt = mappedName(process, base);
                        Optional<SharedSourceFiles.NativeFile> held = dos.equalsIgnoreCase(expected.fullDosPath())
                                && nt.equalsIgnoreCase(expected.kernelNtPath()) ? Optional.of(SharedSourceFiles.nativeHeldFile(file)) : Optional.empty();
                        LoadedModule row = new LoadedModule(Long.toUnsignedString(base), size, dos, nt, held);
                        if (result.put(base, row) != null) throw new IOException("duplicate module allocation");
                    }
                    return List.copyOf(result.values());
                }
            }
            throw new IOException("module roster grew; no partial result");
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
        public void verify() throws IOException {
            synchronized (lease) {
                lease.verify(); owner.verifyLiveOwner();
                if (pipe == null) throw new IOException("endpoint closed");
                requireNonblockingPipe();
                IntByReference flags = new IntByReference(), server = new IntByReference(), client = new IntByReference();
                need(APIs.K.GetNamedPipeInfo(pipe, flags, null, null, null), "server endpoint flags");
                need(APIs.K.GetNamedPipeServerProcessId(pipe, server), "server PID");
                if ((flags.getValue() & 1) == 0 || Integer.toUnsignedLong(server.getValue()) != owner.identity().pid())
                    throw new IOException("actual retained server end/owner identity differs");
                String objectName;
                try (Memory data = new Memory(65568)) {
                    int status = APIs.N.NtQueryObject(pipe, 1, data, (int) data.size(), new IntByReference());
                    if (status != 0) throw new IOException("kernel endpoint name query NTSTATUS=" + Integer.toUnsignedString(status));
                    int bytes = Short.toUnsignedInt(data.getShort(0));
                    Pointer text = data.getPointer(8); long offset = Pointer.nativeValue(text) - Pointer.nativeValue(data);
                    if (bytes == 0 || (bytes & 1) != 0 || offset < 0 || offset > data.size() - bytes)
                        throw new IOException("bounded kernel endpoint name required");
                    objectName = new String(text.getByteArray(0, bytes), StandardCharsets.UTF_16LE);
                }
                String prefix = "\\Device\\NamedPipe\\";
                if (!objectName.regionMatches(true, 0, prefix, 0, prefix.length())
                        || !("\\\\.\\pipe\\" + objectName.substring(prefix.length())).equalsIgnoreCase(name))
                    throw new IOException("kernel endpoint pipe name differs");
                requireNonblockingPipe();
                owner.verifyLiveOwner(); lease.verify();
                if (!APIs.K.GetNamedPipeClientProcessId(pipe, client)) {
                    int error = Native.getLastError();
                    if (error != 233 && error != 1168) throw new IOException("client PID Win32=" + error);
                    requireNonblockingPipe(); owner.verifyLiveOwner(); lease.verify();
                    throw new PipeNotConnected(error);
                }
                if (Integer.toUnsignedLong(client.getValue()) != lease.identity.pid())
                    throw new IOException("actual retained client identity differs");
                owner.verifyLiveOwner(); lease.verify();
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
