package org.xar.ck3.control.build;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.UUID;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Mechanical file support for the one SdkSourceAssembly producer; no process or SDK loader. */
public final class SharedSourceFiles {
    public interface AttributeApi extends com.sun.jna.win32.StdCallLibrary {
        boolean GetFileInformationByHandleEx(HANDLE handle, int kind, Pointer memory, int length);
        boolean GetFileInformationByHandle(HANDLE handle, Pointer memory);
    }
    private static final class Api { private static final AttributeApi VALUE = Native.load("kernel32", AttributeApi.class); }
    private SharedSourceFiles() { }
    public record NativeFile(String volumeSerialDecimal, String fileIdDecimal, String legacyVolumeSerialDecimal, String legacyFileIdHex, String creationFiletimeDecimal,
                             String lastWriteFiletimeDecimal, String changeFiletimeDecimal,
                             long logicalBytes, long allocatedBytes, long linkCount) {
        public NativeFile {
            unsignedDecimal(volumeSerialDecimal, 64); unsignedDecimal(fileIdDecimal, 128);
            unsignedDecimal(legacyVolumeSerialDecimal, 32); unsignedDecimal(creationFiletimeDecimal, 64);
            unsignedDecimal(lastWriteFiletimeDecimal, 64); unsignedDecimal(changeFiletimeDecimal, 64);
            if (legacyFileIdHex == null || !legacyFileIdHex.matches("[0-9a-f]{16}")) throw new IllegalArgumentException("exact original exporter native FileID64 required");
            if (logicalBytes < 0 || allocatedBytes < 0 || linkCount <= 0) throw new IllegalArgumentException("actual native file facts required");
        }
        public String identityKey() { return volumeSerialDecimal + ":" + fileIdDecimal + ":" + creationFiletimeDecimal; }
    }
    public record Witness(FileRef source, NativeFile nativeFile) { }
    /** Allocation/change time may change when NTFS adds a filename; identity and file bytes may not. */
    public record LinkResult(Witness before, Witness sourceAfter, Witness destinationAfter) {
        public LinkResult {
            if (!sameIdentityAndContent(before, sourceAfter) || !sameIdentityAndContent(before, destinationAfter)
                    || !sourceAfter.nativeFile().equals(destinationAfter.nativeFile())
                    || sourceAfter.nativeFile().linkCount() != Math.addExact(before.nativeFile().linkCount(), 1)) {
                throw new IllegalArgumentException("hardlink must preserve exact bytes/native identity/mtime and add exactly one link");
            }
        }
        public long allocatedGrowthBytes() { return Math.max(0, Math.subtractExact(sourceAfter.nativeFile().allocatedBytes(), before.nativeFile().allocatedBytes())); }
    }

    public static Witness observe(Path path) throws IOException {
        plainAncestors(path);
        FileRef before = FileRef.measure(path);
        NativeFile nativeFile = nativeFile(path);
        FileRef after = FileRef.measure(path);
        if (!before.equals(after) || before.bytes() != nativeFile.logicalBytes()) throw new IOException("source changed while native identity/content was observed");
        return new Witness(after, nativeFile);
    }
    public record DirectoryIdentity(String volumeSerialDecimal, String fileIdDecimal, String creationFiletimeDecimal) {
        public DirectoryIdentity {
            unsignedDecimal(volumeSerialDecimal, 64); unsignedDecimal(fileIdDecimal, 128);
            unsignedDecimal(creationFiletimeDecimal, 64);
        }
    }
    private static void unsignedDecimal(String value, int bits) {
        if (value == null || !value.matches("0|[1-9][0-9]*") || new BigInteger(value).bitLength() > bits) {
            throw new IllegalArgumentException("canonical unsigned native identity/time decimal within " + bits + " bits required");
        }
    }
    public static DirectoryIdentity nativeDirectory(Path path) throws IOException {
        NativeFile entry = nativeEntry(path, true);
        return new DirectoryIdentity(entry.volumeSerialDecimal(), entry.fileIdDecimal(), entry.creationFiletimeDecimal());
    }
    public static NativeFile nativeFile(Path path) throws IOException { return nativeEntry(path, false); }
    private static NativeFile nativeEntry(Path path, boolean directory) throws IOException {
        if (!com.sun.jna.Platform.isWindows() || !path.isAbsolute()) throw new IOException("actual Windows file metadata required");
        plainAncestors(path);
        if (directory ? !Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) : !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("ordinary source entry of the expected type required");
        HANDLE handle = Kernel32.INSTANCE.CreateFile(nativePath(path), 0x80, 7, null, 3, 0x00200000 | (directory ? 0x02000000 : 0), null);
        if (WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("source metadata open Win32=" + Native.getLastError() + " path=" + path);
        try { return nativeHeldEntry(handle, directory); }
        finally { if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("source metadata handle close Win32=" + Native.getLastError()); }
    }
    /** Same decoder on a caller's continuously retained file handle; never reopens a path. */
    public static NativeFile nativeHeldFile(HANDLE handle) throws IOException {
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("actual held file handle required");
        return nativeHeldEntry(handle, false);
    }
    private static NativeFile nativeHeldEntry(HANDLE handle, boolean directory) throws IOException {
        try (Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24); Memory legacy = new Memory(52)) {
            if (!Api.VALUE.GetFileInformationByHandleEx(handle, 18, id, 24)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 0, basic, 40)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 1, standard, 24)
                    || !Api.VALUE.GetFileInformationByHandle(handle, legacy)) throw new IOException("source metadata Win32=" + Native.getLastError());
            if ((basic.getInt(32) & 0x400) != 0 || standard.getByte(20) != 0 || ((standard.getByte(21) != 0) != directory)) throw new IOException("ordinary non-reparse non-delete-pending source required");
            byte[] little = id.getByteArray(8, 16), big = new byte[16];
            for (int index = 0; index < big.length; index++) big[index] = little[15 - index];
            long legacyBytes = (Integer.toUnsignedLong(legacy.getInt(32)) << 32) | Integer.toUnsignedLong(legacy.getInt(36));
            if (legacyBytes != standard.getLong(8) || legacy.getLong(4) != basic.getLong(0) || legacy.getLong(20) != basic.getLong(16)
                    || legacy.getInt(40) != standard.getInt(16)) throw new IOException("native source facts changed between exact identity APIs");
            return new NativeFile(Long.toUnsignedString(id.getLong(0)), new BigInteger(1, big).toString(), Integer.toUnsignedString(legacy.getInt(28)),
                    java.util.HexFormat.of().toHexDigits(legacy.getInt(44)) + java.util.HexFormat.of().toHexDigits(legacy.getInt(48)), Long.toUnsignedString(basic.getLong(0)),
                    Long.toUnsignedString(basic.getLong(16)), Long.toUnsignedString(basic.getLong(24)),
                    standard.getLong(8), standard.getLong(0), Integer.toUnsignedLong(standard.getInt(16)));
        }
    }
    /** Extended spelling is only for Win32 calls; persisted paths retain the caller's normalized Path. */
    static String nativePath(Path path) throws IOException {
        if (path == null || !path.isAbsolute()) throw new IOException("absolute native source path required");
        return nativePathValue(path.toAbsolutePath().normalize().toString());
    }
    /** A Path can hide its extended spelling; keep this mechanical conversion independently testable. */
    static String nativePathValue(String value) throws IOException {
        if (value == null || value.indexOf('\0') >= 0) throw new IOException("ordinary absolute Windows spelling required");
        if (value.startsWith("\\\\?\\")) return value;
        if (value.startsWith("\\\\")) return "\\\\?\\UNC\\" + value.substring(2);
        if (!value.matches("[A-Za-z]:\\\\.*")) throw new IOException("canonical Windows drive or UNC path required");
        return "\\\\?\\" + value;
    }
    public static void plainAncestors(Path path) throws IOException {
        if (!path.isAbsolute()) throw new IOException("absolute source path required");
        Path current = path.toAbsolutePath().normalize();
        while (current != null) {
            if (Files.exists(current, LinkOption.NOFOLLOW_LINKS)) {
                if (Files.isSymbolicLink(current)) throw new IOException("source symlink/reparse path rejected");
                if (com.sun.jna.Platform.isWindows()) {
                    int attributes = Kernel32.INSTANCE.GetFileAttributes(nativePath(current));
                    if (attributes == -1 || (attributes & 0x400) != 0) throw new IOException("source path attributes unavailable or reparse Win32=" + (attributes == -1 ? Native.getLastError() : 0) + " path=" + current);
                }
            }
            current = current.getParent();
        }
    }
    public static Witness link(Path immutableSource, Path destination) throws IOException {
        return linkObserved(immutableSource, destination).destinationAfter();
    }
    public static LinkResult linkObserved(Path immutableSource, Path destination) throws IOException {
        plainAncestors(immutableSource); plainAncestors(destination);
        if (Files.exists(destination, LinkOption.NOFOLLOW_LINKS)) throw new IOException("source view path already exists");
        Witness original = observe(immutableSource);
        Files.createDirectories(destination.getParent());
        if (!Files.getFileStore(immutableSource).equals(Files.getFileStore(destination.getParent()))) throw new IOException("hardlink source views require the same actual volume");
        Files.createLink(destination, immutableSource);
        Witness linked = observe(destination);
        Witness sourceAfter = observe(immutableSource);
        if (!sameIdentityAndContent(original, linked) || !sameIdentityAndContent(original, sourceAfter)
                || !Files.isSameFile(immutableSource, destination)) throw new IOException("source hardlink did not retain exact native identity/content: before=" + original + "; source_after=" + sourceAfter + "; destination_after=" + linked);
        try { return new LinkResult(original, sourceAfter, linked); }
        catch (IllegalArgumentException error) { throw new IOException("source hardlink metadata differs: before=" + original + "; source_after=" + sourceAfter + "; destination_after=" + linked, error); }
    }
    /** CREATE_NEW complete private bytes, then one atomic path replacement; never write a linked inode. */
    public static Witness replacePrivate(Path target, Path privateTemporaryRoot, byte[] completeBytes,
                                         List<Witness> baselineAndOtherView) throws IOException {
        if (completeBytes == null || completeBytes.length > 8 * 1024 * 1024 || baselineAndOtherView.isEmpty()) throw new IOException("bounded complete bytes and protected source witnesses required");
        plainAncestors(target); plainAncestors(privateTemporaryRoot);
        target = target.toAbsolutePath().normalize(); privateTemporaryRoot = privateTemporaryRoot.toAbsolutePath().normalize();
        Path viewRoot = privateTemporaryRoot.getParent();
        if (!privateTemporaryRoot.getFileName().toString().equals(".assembly") || !target.startsWith(viewRoot)
                || target.startsWith(privateTemporaryRoot)) throw new IOException("private replacement must stay in its explicit source view");
        Witness previous = observe(target);
        for (Witness witness : baselineAndOtherView) {
            if (Path.of(witness.source().path()).toAbsolutePath().normalize().equals(target)) throw new IOException("cannot replace a protected baseline/sibling path");
            assertUnchanged(witness);
        }
        Path temporary = privateTemporaryRoot.resolve("private-source-" + UUID.randomUUID() + ".tmp");
        try (FileChannel output = FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer bytes = ByteBuffer.wrap(completeBytes);
            while (bytes.hasRemaining()) output.write(bytes);
            output.force(true);
        }
        Witness privateFile = observe(temporary);
        if (!privateFile.nativeFile().volumeSerialDecimal().equals(previous.nativeFile().volumeSerialDecimal())
                || privateFile.nativeFile().identityKey().equals(previous.nativeFile().identityKey())) throw new IOException("private source file did not separate from linked inode on the same volume");
        assertUnchanged(previous);
        for (Witness witness : baselineAndOtherView) assertUnchanged(witness);
        Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        Witness changed = observe(target);
        if (!changed.nativeFile().identityKey().equals(privateFile.nativeFile().identityKey())
                || !changed.source().sha256().equals(privateFile.source().sha256()) || changed.source().bytes() != completeBytes.length) throw new IOException("atomic private source replacement readback differs");
        for (Witness witness : baselineAndOtherView) assertUnchanged(witness);
        return changed;
    }
    public static void assertUnchanged(Witness expected) throws IOException {
        if (!sameIdentityAndContent(expected, observe(Path.of(expected.source().path())))) throw new IOException("baseline/sibling source content or native identity changed");
    }
    private static boolean sameIdentityAndContent(Witness before, Witness after) {
        return before.source().bytes() == after.source().bytes() && before.source().sha256().equals(after.source().sha256())
                && before.nativeFile().identityKey().equals(after.nativeFile().identityKey())
                && before.nativeFile().legacyVolumeSerialDecimal().equals(after.nativeFile().legacyVolumeSerialDecimal())
                && before.nativeFile().legacyFileIdHex().equals(after.nativeFile().legacyFileIdHex())
                && before.nativeFile().lastWriteFiletimeDecimal().equals(after.nativeFile().lastWriteFiletimeDecimal());
    }
}
