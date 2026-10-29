package org.xar.ck3.control.g2.context;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;

/** Read-only Win32 process/file facts. No process creation, memory reads, UI or Game commands. */
public final class G2WindowsReadOnlyObservation implements G2WindowsRootSources.ObservationPort {
    public interface FileApi extends com.sun.jna.win32.StdCallLibrary {
        boolean GetFileInformationByHandleEx(HANDLE handle, int kind, Pointer data, int length);
        boolean ReadFile(HANDLE handle, Pointer data, int maximumBytes, IntByReference actualBytes, Pointer overlapped);
    }
    private static final class Api { private static final FileApi VALUE = Native.load("kernel32", FileApi.class); }
    public record FileIdentity(String volumeSerial, String fileId, String creationFiletime,
            String modifiedFiletime, String changeFiletime, long bytes, long links) {
        public FileIdentity {
            for (String value : new String[] {volumeSerial, fileId, creationFiletime, modifiedFiletime, changeFiletime}) {
                if (value == null || !value.matches("0|[1-9][0-9]*")) { throw new IllegalArgumentException("canonical native decimal required"); }
            }
            if (bytes < 0 || links < 1) { throw new IllegalArgumentException("ordinary native file facts required"); }
        }
        public String mtimeNs() {
            return new BigInteger(modifiedFiletime).multiply(BigInteger.valueOf(100))
                    .subtract(new BigInteger("11644473600000000000")).toString();
        }
    }
    public record FileObservation(ExactRef reference, FileIdentity identity) {
        public FileObservation { Objects.requireNonNull(reference); Objects.requireNonNull(identity); }
    }
    public record FileRead(FileObservation observation, byte[] bytes) {
        public FileRead { Objects.requireNonNull(observation); bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    @Override public String machineId() { return WindowsJobProcess.currentMachineId(); }
    @Override public WindowsJobProcess.ProcessIdentity process(long pid) {
        return WindowsJobProcess.observeLiveProcess(pid).identity();
    }
    @Override public FileIdentity stat(Path path) throws IOException {
        plain(path);
        HANDLE handle = open(path);
        try { return identity(handle); }
        finally { close(handle); }
    }
    @Override public FileObservation hash(Path path, long maximumBytes) throws IOException {
        return read(path, maximumBytes, false).observation();
    }
    @Override public FileRead read(Path path, long maximumBytes) throws IOException {
        return read(path, maximumBytes, true);
    }
    private static FileRead read(Path path, long maximumBytes, boolean retain) throws IOException {
        if (maximumBytes < 1 || (retain && maximumBytes > 16 * 1024 * 1024)) { throw new IOException("finite file read budget required"); }
        plain(path);
        HANDLE handle = open(path);
        FileIdentity before;
        byte[] captured;
        String digest;
        try {
            before = identity(handle);
            if (before.bytes() > maximumBytes) { throw new IOException("file exceeds exact Root read budget"); }
            MessageDigest sha = sha256();
            ByteArrayOutputStream body = new ByteArrayOutputStream(retain ? (int) before.bytes() : 0);
            long total = 0;
            try (Memory chunk = new Memory(65_536)) {
                IntByReference count = new IntByReference();
                while (true) {
                    if (!Api.VALUE.ReadFile(handle, chunk, 65_536, count, null)) {
                        throw new IOException("read-only file read Win32=" + Native.getLastError());
                    }
                    int size = count.getValue();
                    if (size < 0 || size > 65_536) { throw new IOException("invalid native read size"); }
                    if (size == 0) { break; }
                    total += size;
                    if (total > maximumBytes || total > before.bytes()) { throw new IOException("file grew beyond Root budget"); }
                    byte[] part = chunk.getByteArray(0, size);
                    sha.update(part);
                    if (retain) { body.write(part, 0, size); }
                }
            }
            if (total != before.bytes() || !before.equals(identity(handle))) { throw new IOException("file changed during held-handle read"); }
            digest = HexFormat.of().formatHex(sha.digest());
            captured = body.toByteArray();
            // A second path open while the first handle denies writes/deletes binds the current name.
            plain(path);
            HANDLE named = open(path);
            try { if (!before.equals(identity(named))) { throw new IOException("file path identity changed during read"); } }
            finally { close(named); }
        } finally { close(handle); }
        ExactRef ref = new ExactRef(path.toAbsolutePath().normalize().toString().replace('\\', '/'), before.bytes(), digest);
        return new FileRead(new FileObservation(ref, before), captured);
    }
    private static HANDLE open(Path path) throws IOException {
        // FILE_SHARE_READ only: existing conflicting writers make the observation unavailable.
        HANDLE value = Kernel32.INSTANCE.CreateFile(extended(path), 0x80000080, 1, null, 3, 0x00200000, null);
        if (value == null || WinBase.INVALID_HANDLE_VALUE.equals(value)) { throw new IOException("read-only file open Win32=" + Native.getLastError()); }
        return value;
    }
    private static FileIdentity identity(HANDLE handle) throws IOException {
        try (Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24)) {
            if (!Api.VALUE.GetFileInformationByHandleEx(handle, 18, id, 24)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 0, basic, 40)
                    || !Api.VALUE.GetFileInformationByHandleEx(handle, 1, standard, 24)) {
                throw new IOException("native file facts Win32=" + Native.getLastError());
            }
            if ((basic.getInt(32) & (0x400 | 0x10)) != 0 || standard.getByte(20) != 0 || standard.getByte(21) != 0) {
                throw new IOException("ordinary non-reparse non-delete-pending file required");
            }
            byte[] little = id.getByteArray(8, 16), big = new byte[16];
            for (int index = 0; index < 16; index++) { big[index] = little[15 - index]; }
            return new FileIdentity(Long.toUnsignedString(id.getLong(0)), new BigInteger(1, big).toString(),
                    Long.toUnsignedString(basic.getLong(0)), Long.toUnsignedString(basic.getLong(16)),
                    Long.toUnsignedString(basic.getLong(24)), standard.getLong(8), Integer.toUnsignedLong(standard.getInt(16)));
        }
    }
    static void plain(Path path) throws IOException {
        if (!com.sun.jna.Platform.isWindows() || !path.isAbsolute() || !path.normalize().equals(path)) {
            throw new IOException("normalized absolute Windows source required");
        }
        Path current = path;
        while (current != null) {
            if (Files.exists(current, LinkOption.NOFOLLOW_LINKS)) {
                int attributes = Kernel32.INSTANCE.GetFileAttributes(extended(current));
                if (attributes == -1 || (attributes & 0x400) != 0) { throw new IOException("source ancestor unavailable/reparse"); }
            }
            current = current.getParent();
        }
    }
    private static String extended(Path path) {
        String raw = path.toString();
        if (raw.startsWith("\\\\?\\")) { return raw; }
        return raw.startsWith("\\\\") ? "\\\\?\\UNC\\" + raw.substring(2) : "\\\\?\\" + raw;
    }
    private static void close(HANDLE handle) throws IOException {
        if (!Kernel32.INSTANCE.CloseHandle(handle)) { throw new IOException("read-only handle close Win32=" + Native.getLastError()); }
    }
    private static MessageDigest sha256() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
