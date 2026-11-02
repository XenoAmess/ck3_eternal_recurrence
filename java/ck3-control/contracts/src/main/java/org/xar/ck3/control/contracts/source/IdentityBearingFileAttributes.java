package org.xar.ck3.control.contracts.source;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Identity-bearing metadata for source readers. Windows NIO deliberately supplies no fileKey. */
public final class IdentityBearingFileAttributes {
    private IdentityBearingFileAttributes() { }
    private static final java.util.regex.Pattern CANONICAL_DECIMAL = java.util.regex.Pattern.compile("0|[1-9][0-9]*");
    public record WindowsFileIdentity(String volumeSerialDecimal, String fileIdDecimal, String creationFiletimeDecimal) {
        public WindowsFileIdentity {
            for (String value : new String[] {volumeSerialDecimal, fileIdDecimal, creationFiletimeDecimal})
                if (value == null || !CANONICAL_DECIMAL.matcher(value).matches()) throw new IllegalArgumentException("canonical native identity required");
        }
    }
    public interface AttributeApi extends com.sun.jna.win32.StdCallLibrary {
        boolean GetFileInformationByHandleEx(HANDLE handle, int kind, Pointer memory, int length);
    }
    private static final class Api { private static final AttributeApi VALUE = Native.load("kernel32", AttributeApi.class); }
    private record WindowsStamp(WindowsFileIdentity key, long bytes, long creation, long modified, boolean directory) { }
    /** Fresh per-call bytes transferred to the caller; the reader retains no copy or cache. */
    public record BoundedFileRead(BasicFileAttributes attributes, byte[] bytes) {
        public BoundedFileRead { Objects.requireNonNull(attributes); Objects.requireNonNull(bytes); }
    }
    private interface DataApi extends com.sun.jna.win32.StdCallLibrary {
        boolean ReadFile(HANDLE handle, Pointer buffer, int requested,
                com.sun.jna.ptr.IntByReference transferred, Pointer overlapped);
    }
    private static final class Data { private static final DataApi VALUE = Native.load("kernel32", DataApi.class); }

    private record Snapshot(BasicFileAttributes original, Object fileKey) implements BasicFileAttributes {
        private Snapshot { Objects.requireNonNull(original); Objects.requireNonNull(fileKey); }
        @Override public FileTime lastModifiedTime() { return original.lastModifiedTime(); }
        @Override public FileTime lastAccessTime() { return original.lastAccessTime(); }
        @Override public FileTime creationTime() { return original.creationTime(); }
        @Override public boolean isRegularFile() { return original.isRegularFile(); }
        @Override public boolean isDirectory() { return original.isDirectory(); }
        @Override public boolean isSymbolicLink() { return original.isSymbolicLink(); }
        @Override public boolean isOther() { return original.isOther(); }
        @Override public long size() { return original.size(); }
    }
    public static BasicFileAttributes read(Path supplied) throws IOException {
        Objects.requireNonNull(supplied);
        BasicFileAttributes before = Files.readAttributes(supplied, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!Platform.isWindows()) {
            if (before.fileKey() == null) throw new IOException("identity-bearing source metadata unavailable");
            return before;
        }
        Path path = supplied.toAbsolutePath().normalize();
        try {
            // One metadata observation supplies this read's identity. Content readers already
            // observe before and after their actual I/O; do not nest another two-pass audit here.
            WindowsStamp observed = windows(path);
            return new Snapshot(before, observed.key());
        } catch (LinkageError unavailable) { throw new IOException("Windows source identity provider unavailable", unavailable); }
    }
    /**
     * Bounded ordinary Windows content read whose before identity belongs to its data handle.
     * A separate ordinary path observation after the bytes still binds the requested name.
     * General metadata and whole-parent readers retain their existing independent contracts.
     */
    public static BoundedFileRead readBoundedWindows(Path supplied, int limit) throws IOException {
        return readBoundedWindows(supplied, limit, null);
    }
    /** Package-local seam for controlled real-file replacement/close-failure regression cases. */
    static BoundedFileRead readBoundedWindows(Path supplied, int limit,
            java.util.function.Consumer<HANDLE> afterContent) throws IOException {
        if (!Platform.isWindows()) throw new IOException("native Windows file identity required");
        Path path = Objects.requireNonNull(supplied).toAbsolutePath().normalize();
        BasicFileAttributes nioBefore = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        requireOrdinaryFile(nioBefore);
        BasicFileAttributes before;
        byte[] bytes;
        try {
            ordinaryAttributes(path);
            HANDLE handle = Kernel32.INSTANCE.CreateFile(nativePath(path.toString()), 0x80000080, 7, null, 3, 0x02200000, null);
            if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("source identity open Win32=" + Native.getLastError());
            try {
                WindowsStamp observed = windowsStamp(handle, true);
                before = new Snapshot(nioBefore, observed.key());
                if (before.size() > limit) throw new IOException("named ledger source exceeds finite cap: path=" + path
                        + ", actual_bytes=" + before.size() + ", cap=" + limit);
                // Match readNBytes(limit + 1)'s invalid-length case without integer overflow/allocation.
                if (limit == Integer.MAX_VALUE) throw new IllegalArgumentException("len < 0");
                if (before.size() < 0) throw new IOException("ledger source size drift");
                int expected = Math.toIntExact(before.size());
                bytes = readData(handle, expected);
                if (afterContent != null) afterContent.accept(handle);
            } finally {
                // Close before after-path observation, as the original content stream did.
                // A close failure cannot be swallowed as a later NoSuchFileException/absence.
                if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("source identity close Win32=" + Native.getLastError());
            }
        } catch (LinkageError unavailable) { throw new IOException("Windows source identity provider unavailable", unavailable); }
        BasicFileAttributes after = read(path);
        requireOrdinaryFile(after);
        if (!(after.fileKey() instanceof WindowsFileIdentity)
                || !before.fileKey().equals(after.fileKey()) || before.size() != after.size()
                || !before.lastModifiedTime().toInstant().equals(after.lastModifiedTime().toInstant()))
            throw new IOException("ledger source native identity drift");
        return new BoundedFileRead(after, bytes);
    }
    /** One thread's bounded read custody. Sharing denies data writes/delete, not metadata or ACL changes. */
    public static final class ReadOnlyLease implements AutoCloseable {
        private final Thread thread = Thread.currentThread();
        private final Path path;
        private final HANDLE handle;
        private final WindowsStamp stamp;
        private final BasicFileAttributes initial;
        private byte[] bytes;
        private boolean closed;
        private boolean failed;
        private ReadOnlyLease(Path path, HANDLE handle, WindowsStamp stamp,
                BasicFileAttributes initial, byte[] bytes) {
            this.path = path; this.handle = handle; this.stamp = stamp;
            this.initial = initial; this.bytes = bytes;
        }
        private void requireOpen() throws IOException {
            if (Thread.currentThread() != thread) throw new IOException("read lease crossed its owner thread");
            if (closed) throw new IOException("read lease is closed");
            if (failed) throw new IOException("read lease failed its current qualification");
        }
        /** Fresh name/full identity and current GENERIC_READ authority, without payload reads/hashes. */
        public BasicFileAttributes verifyCurrent() throws IOException {
            requireOpen();
            try { return qualifyLeasePath(path, stamp, initial); }
            catch (IOException | RuntimeException | Error problem) { failed = true; throw problem; }
        }
        /** Captured acquisition DATA, not a new current-permission or pathname qualification. */
        public BoundedFileRead originalRead() throws IOException {
            requireOpen();
            if (bytes == null) throw new IOException("read lease content was retired");
            return new BoundedFileRead(initial, bytes.clone());
        }
        public BoundedFileRead read() throws IOException {
            BasicFileAttributes actual = verifyCurrent();
            if (bytes == null) throw new IOException("read lease content was retired");
            return new BoundedFileRead(actual, bytes.clone());
        }
        /** Retire captured content only; custody/current qualification and close remain active. */
        public void releaseOriginalBytes() throws IOException {
            requireOpen();
            bytes = null;
        }
        @Override public void close() throws IOException {
            if (Thread.currentThread() != thread) throw new IOException("read lease close crossed its owner thread");
            if (closed) return;
            closed = true; bytes = null;
            closeLeaseHandle(handle, "read lease close");
        }
    }
    /** One fresh path observation: the actual GENERIC_READ open binds the queried full native identity. */
    private static BasicFileAttributes qualifyLeasePath(Path path, WindowsStamp original,
            BasicFileAttributes initial) throws IOException {
        try {
            BasicFileAttributes current = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            requireOrdinaryFile(current); ordinaryAttributes(path);
            HANDLE handle = Kernel32.INSTANCE.CreateFile(nativePath(path.toString()), 0x80000080, 1, null, 3, 0x02200000, null);
            if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("current lease read open Win32=" + Native.getLastError());
            Throwable failure = null;
            try {
                WindowsStamp actual = windowsStamp(handle, true);
                if (!original.equals(actual)) throw new IOException("lease pathname full native identity/metadata drift");
                return validated(path, initial, current, original, actual);
            } catch (IOException | RuntimeException | Error problem) { failure = problem; throw problem; }
            finally {
                try { closeLeaseHandle(handle, "current lease read close"); }
                catch (IOException closing) { if (failure != null) failure.addSuppressed(closing); else throw closing; }
            }
        } catch (LinkageError unavailable) { throw new IOException("Windows read lease provider unavailable", unavailable); }
    }
    /** Acquire custody before first content read; a separate fresh path read-open qualifies the result. */
    public static ReadOnlyLease leaseBoundedWindows(Path supplied, int limit) throws IOException {
        if (!Platform.isWindows()) throw new IOException("native Windows read lease required");
        if (limit < 0 || limit == Integer.MAX_VALUE) throw new IllegalArgumentException("finite read lease cap required");
        Path path = Objects.requireNonNull(supplied).toAbsolutePath().normalize();
        BasicFileAttributes before = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        requireOrdinaryFile(before);
        HANDLE handle = null;
        Throwable failure = null;
        try {
            ordinaryAttributes(path);
            handle = Kernel32.INSTANCE.CreateFile(nativePath(path.toString()), 0x80000080, 1, null, 3, 0x02200000, null);
            if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
                handle = null; throw new IOException("read lease open Win32=" + Native.getLastError());
            }
            WindowsStamp first = windowsStamp(handle, true);
            BasicFileAttributes original = validated(path, before, before, first, first);
            if (first.bytes() < 0 || first.bytes() > limit) throw new IOException("read lease exceeds its finite cap");
            byte[] bytes = readData(handle, Math.toIntExact(first.bytes()));
            BasicFileAttributes actual = qualifyLeasePath(path, first, original);
            ReadOnlyLease result = new ReadOnlyLease(path, handle, first, actual, bytes);
            handle = null;
            return result;
        } catch (LinkageError unavailable) {
            IOException problem = new IOException("Windows read lease provider unavailable", unavailable);
            failure = problem; throw problem;
        } catch (IOException | RuntimeException | Error problem) { failure = problem; throw problem; }
        finally {
            if (handle != null) try { closeLeaseHandle(handle, "partial read lease close"); }
            catch (IOException closing) { if (failure != null) failure.addSuppressed(closing); else throw closing; }
        }
    }

    /**
     * Optional acquisition seam: returns empty ONLY when the initial CreateFile fails with
     * ERROR_SHARING_VIOLATION (32) and no handle was acquired. All other failures preserve
     * the original IOException/unchecked behavior of leaseBoundedWindows.
     */
    public static java.util.Optional<ReadOnlyLease> tryLeaseBoundedWindows(Path supplied, int limit) throws IOException {
        if (!Platform.isWindows()) throw new IOException("native Windows read lease required");
        if (limit < 0 || limit == Integer.MAX_VALUE) throw new IllegalArgumentException("finite read lease cap required");
        Path path = Objects.requireNonNull(supplied).toAbsolutePath().normalize();
        BasicFileAttributes before = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        requireOrdinaryFile(before);
        HANDLE handle = null;
        Throwable failure = null;
        try {
            ordinaryAttributes(path);
            handle = Kernel32.INSTANCE.CreateFile(nativePath(path.toString()), 0x80000080, 1, null, 3, 0x02200000, null);
            if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
                handle = null;
                int error = Native.getLastError();
                if (error == 32) return java.util.Optional.empty();
                throw new IOException("read lease open Win32=" + error);
            }
            WindowsStamp first = windowsStamp(handle, true);
            BasicFileAttributes original = validated(path, before, before, first, first);
            if (first.bytes() < 0 || first.bytes() > limit) throw new IOException("read lease exceeds its finite cap");
            byte[] bytes = readData(handle, Math.toIntExact(first.bytes()));
            BasicFileAttributes actual = qualifyLeasePath(path, first, original);
            ReadOnlyLease result = new ReadOnlyLease(path, handle, first, actual, bytes);
            java.util.Optional<ReadOnlyLease> wrapped = java.util.Optional.of(result);
            handle = null;
            return wrapped;
        } catch (LinkageError unavailable) {
            IOException problem = new IOException("Windows read lease provider unavailable", unavailable);
            failure = problem; throw problem;
        } catch (IOException | RuntimeException | Error problem) { failure = problem; throw problem; }
        finally {
            if (handle != null) try { closeLeaseHandle(handle, "partial read lease close"); }
            catch (IOException closing) { if (failure != null) failure.addSuppressed(closing); else throw closing; }
        }
    }
    private static void closeLeaseHandle(HANDLE handle, String context) throws IOException {
        try {
            if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException(context + " Win32=" + Native.getLastError());
        } catch (LinkageError unavailable) { throw new IOException(context + " provider unavailable", unavailable); }
    }
    private static byte[] readData(HANDLE handle, int expected) throws IOException {
        byte[] bytes = new byte[expected];
        try (Memory data = new Memory(Math.max(1, Math.min(65_536, expected)))) {
            var transferred = new com.sun.jna.ptr.IntByReference();
            int offset = 0;
            while (offset < expected) {
                int requested = Math.min(65_536, expected - offset);
                transferred.setValue(0);
                if (!Data.VALUE.ReadFile(handle, data, requested, transferred, null))
                    throw new IOException("source read Win32=" + Native.getLastError());
                int count = transferred.getValue();
                if (count <= 0 || count > requested) throw new IOException("ledger source size drift");
                data.read(0, bytes, offset, count); offset += count;
            }
            transferred.setValue(0);
            if (!Data.VALUE.ReadFile(handle, data, 1, transferred, null))
                throw new IOException("source read Win32=" + Native.getLastError());
            if (transferred.getValue() != 0) throw new IOException("ledger source size drift");
        }
        return bytes;
    }

    private static void requireOrdinaryFile(BasicFileAttributes value) throws IOException {
        if (!value.isRegularFile() || value.isSymbolicLink())
            throw new IOException("ordinary identity-bearing ledger file required");
    }

    /**
     * Windows ledger observation: two complete root-to-leaf observations, with ordinary parents.
     * Every node retains NIO metadata and full native identity in both observations.
     * State is local to this call; no ancestor observation is reused by another read.
     */
    public static BasicFileAttributes readWithOrdinaryParents(Path supplied) throws IOException {
        return beginOrdinaryPathObservation(supplied).complete();
    }
    private record NodeObservation(Path path, BasicFileAttributes attributes, WindowsStamp stamp) { }
    /** Two phases keep the actual filesystem change window testable within this package. */
    static final class OrdinaryPathObservation {
        private final List<NodeObservation> first;
        private OrdinaryPathObservation(List<NodeObservation> first) { this.first = List.copyOf(first); }
        BasicFileAttributes complete() throws IOException {
            try {
                BasicFileAttributes leaf = null;
                for (int index = 0; index < first.size(); index++) {
                    NodeObservation before = first.get(index);
                    NodeObservation after = observeNode(before.path(), index + 1 < first.size());
                    leaf = validated(before.path(), before.attributes(), after.attributes(), before.stamp(), after.stamp());
                }
                return Objects.requireNonNull(leaf);
            } catch (LinkageError unavailable) { throw new IOException("Windows source identity provider unavailable", unavailable); }
        }
    }
    static OrdinaryPathObservation beginOrdinaryPathObservation(Path supplied) throws IOException {
        Objects.requireNonNull(supplied);
        if (!Platform.isWindows()) throw new IOException("native Windows whole-path identity required");
        Path path = supplied.toAbsolutePath().normalize();
        var paths = new ArrayDeque<Path>();
        for (Path cursor = path; cursor != null; cursor = cursor.getParent()) paths.addFirst(cursor);
        var first = new ArrayList<NodeObservation>(paths.size());
        try {
            for (Path node : paths) first.add(observeNode(node, !node.equals(path)));
            return new OrdinaryPathObservation(first);
        } catch (LinkageError unavailable) { throw new IOException("Windows source identity provider unavailable", unavailable); }
    }
    private static NodeObservation observeNode(Path path, boolean parent) throws IOException {
        BasicFileAttributes attributes = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        int nativeAttributes = ordinaryAttributes(path);
        WindowsStamp stamp = windowsStamp(path);
        if (parent && ((nativeAttributes & 0x10) == 0 || !attributes.isDirectory()
                || attributes.isSymbolicLink() || !stamp.directory())) throw new IOException("ordinary ledger parent required");
        return new NodeObservation(path, attributes, stamp);
    }
    private static BasicFileAttributes validated(Path path, BasicFileAttributes before, BasicFileAttributes after,
            WindowsStamp first, WindowsStamp second) throws IOException {
        if (!first.equals(second) || !same(before, after) || before.isSymbolicLink()
                || before.isDirectory() != first.directory() || (!before.isDirectory() && !before.isRegularFile())
                || (!first.directory() && before.size() != first.bytes())
                || !before.creationTime().equals(fileTime(first.creation()))
                || !before.lastModifiedTime().equals(fileTime(first.modified()))) {
            throw new IOException("source native identity, type or metadata changed during observation; path=" + path
                    + "; before_nio=" + metadata(before) + "; after_nio=" + metadata(after)
                    + "; first_native=" + first + "; second_native=" + second);
        }
        return new Snapshot(after, first.key());
    }
    private static String metadata(BasicFileAttributes value) {
        return "{regular=" + value.isRegularFile() + ",directory=" + value.isDirectory()
                + ",symbolicLink=" + value.isSymbolicLink() + ",bytes=" + value.size()
                + ",creation=" + value.creationTime() + ",modified=" + value.lastModifiedTime() + "}";
    }
    private static boolean same(BasicFileAttributes first, BasicFileAttributes second) {
        return first.isRegularFile() == second.isRegularFile() && first.isDirectory() == second.isDirectory()
            && first.isSymbolicLink() == second.isSymbolicLink() && (first.isDirectory() || first.size() == second.size())
            && first.creationTime().equals(second.creationTime()) && first.lastModifiedTime().equals(second.lastModifiedTime());
    }
    private static FileTime fileTime(long ticks) {
        long epochTicks = Math.subtractExact(ticks, 116444736000000000L);
        return FileTime.from(Instant.ofEpochSecond(Math.floorDiv(epochTicks, 10000000L), Math.floorMod(epochTicks, 10000000L) * 100));
    }
    /** Win32 metadata APIs need extended syntax even when NIO can read the ordinary long path. */
    static String nativePath(String value) {
        Objects.requireNonNull(value);
        if (value.startsWith("\\\\?\\")) {
            if (value.regionMatches(true, 4, "UNC\\", 0, 4)
                    || (value.length() >= 7 && Character.isLetter(value.charAt(4))
                        && value.charAt(5) == ':' && value.charAt(6) == '\\')) return value;
            throw new IllegalArgumentException("ordinary absolute metadata path required");
        }
        if (value.startsWith("\\\\.\\")) throw new IllegalArgumentException("device metadata path rejected");
        if (value.startsWith("\\\\")) return "\\\\?\\UNC\\" + value.substring(2);
        if (value.length() >= 3 && Character.isLetter(value.charAt(0)) && value.charAt(1) == ':' && value.charAt(2) == '\\')
            return "\\\\?\\" + value;
        throw new IllegalArgumentException("absolute metadata path required");
    }
    private static int ordinaryAttributes(Path path) throws IOException {
        int attributes = Kernel32.INSTANCE.GetFileAttributes(nativePath(path.toString()));
        if (attributes == -1 || (attributes & 0x400) != 0) throw new IOException("source path attributes unavailable or reparse: Win32=" + Native.getLastError() + "; path=" + path);
        return attributes;
    }
    private static WindowsStamp windows(Path path) throws IOException {
        ordinaryAttributes(path);
        return windowsStamp(path);
    }
    private static WindowsStamp windowsStamp(Path path) throws IOException {
        HANDLE handle = Kernel32.INSTANCE.CreateFile(nativePath(path.toString()), 0x80, 7, null, 3, 0x02200000, null);
        if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("source identity open Win32=" + Native.getLastError());
        try { return windowsStamp(handle, false); }
        finally {
            if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("source identity close Win32=" + Native.getLastError());
        }
    }
    private static WindowsStamp windowsStamp(HANDLE handle, boolean ordinaryFile) throws IOException {
        try (Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24)) {
            if (!Api.VALUE.GetFileInformationByHandleEx(handle, 18, id, 24)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 0, basic, 40)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 1, standard, 24))
                throw new IOException("source identity query Win32=" + Native.getLastError());
            if ((basic.getInt(32) & 0x400) != 0 || standard.getByte(20) != 0)
                throw new IOException("source reparse or delete-pending identity rejected");
            if (ordinaryFile && ((basic.getInt(32) & 0x40) != 0 || standard.getByte(21) != 0))
                throw new IOException("ordinary identity-bearing ledger file required");
            byte[] little = id.getByteArray(8, 16), big = new byte[16];
            for (int index = 0; index < big.length; index++) big[index] = little[15 - index];
            WindowsFileIdentity key = new WindowsFileIdentity(Long.toUnsignedString(id.getLong(0)),
                new BigInteger(1, big).toString(), Long.toUnsignedString(basic.getLong(0)));
            return new WindowsStamp(key, standard.getLong(8), basic.getLong(0), basic.getLong(16), standard.getByte(21) != 0);
        }
    }
}

