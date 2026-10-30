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
        try (Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24)) {
            if (!Api.VALUE.GetFileInformationByHandleEx(handle, 18, id, 24)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 0, basic, 40)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 1, standard, 24))
                throw new IOException("source identity query Win32=" + Native.getLastError());
            if ((basic.getInt(32) & 0x400) != 0 || standard.getByte(20) != 0)
                throw new IOException("source reparse or delete-pending identity rejected");
            byte[] little = id.getByteArray(8, 16), big = new byte[16];
            for (int index = 0; index < big.length; index++) big[index] = little[15 - index];
            WindowsFileIdentity key = new WindowsFileIdentity(Long.toUnsignedString(id.getLong(0)),
                new BigInteger(1, big).toString(), Long.toUnsignedString(basic.getLong(0)));
            return new WindowsStamp(key, standard.getLong(8), basic.getLong(0), basic.getLong(16), standard.getByte(21) != 0);
        } finally {
            if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("source identity close Win32=" + Native.getLastError());
        }
    }
}

