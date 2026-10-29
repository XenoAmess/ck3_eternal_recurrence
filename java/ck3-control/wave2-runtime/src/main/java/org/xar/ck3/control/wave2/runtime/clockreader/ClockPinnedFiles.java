package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.StrictJson;

/** Bounded content measurement. This does not replace original Queue held-HANDLE/FileID custody. */
public final class ClockPinnedFiles {
    private ClockPinnedFiles() { }
    public record LocalContentStamp(Path realPath, long bytes, String creationTime, String modifiedTime) {
        public LocalContentStamp {
            StrictJson.require(realPath != null && realPath.isAbsolute(), "absolute measured source path");
            StrictJson.safe(bytes, 0); StrictJson.text(creationTime); StrictJson.text(modifiedTime);
        }
    }
    public record Pin(Path path, long bytes, String sha256, LocalContentStamp contentStamp) {
        public Pin {
            StrictJson.require(path != null && path.isAbsolute(), "absolute pinned path");
            StrictJson.safe(bytes, 1); digest(sha256); java.util.Objects.requireNonNull(contentStamp);
            StrictJson.require(bytes == contentStamp.bytes(), "pin length matches measured content stamp");
        }
    }
    public static Pin capture(Path path, String expectedSha256, int maximumBytes) throws IOException {
        digest(expectedSha256); LocalContentStamp before = stamp(path);
        byte[] raw = readBounded(path, maximumBytes); LocalContentStamp after = stamp(path);
        require(before.equals(after), "source changed while capturing local identity");
        require(hash(raw).equals(expectedSha256), "source digest differs from admitted pin");
        return new Pin(path.toAbsolutePath().normalize(), raw.length, expectedSha256, after);
    }
    public static byte[] read(Pin pin, int maximumBytes) throws IOException {
        LocalContentStamp before = stamp(pin.path()); require(before.equals(pin.contentStamp()), "pinned source content stamp changed");
        require(pin.bytes() <= maximumBytes, "pinned file exceeds explicit budget");
        byte[] raw = readBounded(pin.path(), maximumBytes); LocalContentStamp after = stamp(pin.path());
        require(before.equals(after) && raw.length == pin.bytes() && hash(raw).equals(pin.sha256()), "pinned file changed or digest mismatch");
        return raw;
    }
    public static Pin captureStreaming(Path path, String expectedSha256, long maximumBytes) throws IOException {
        digest(expectedSha256); LocalContentStamp measured = stamp(path);
        Pin pin = new Pin(path.toAbsolutePath().normalize(), measured.bytes(), expectedSha256, measured);
        verifyStreaming(pin, maximumBytes); return pin;
    }
    public static void verifyContentStamp(Pin pin) throws IOException {
        require(pin.contentStamp().equals(stamp(pin.path())), "pinned local content stamp changed");
    }
    /** Source binaries have a separate finite budget and are hashed without materializing their bodies. */
    public static void verifyStreaming(Pin pin, long maximumBytes) throws IOException {
        require(maximumBytes >= 1 && maximumBytes <= 1024L * 1024 * 1024, "explicit binary byte budget");
        verifyContentStamp(pin); require(pin.bytes() <= maximumBytes, "binary exceeds declared source budget");
        MessageDigest digest;
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("JDK SHA-256 unavailable", error); }
        long count = 0;
        try (InputStream input = Files.newInputStream(pin.path())) {
            byte[] buffer = new byte[8192]; int received;
            while ((received = input.read(buffer)) != -1) {
                count += received; require(count <= pin.bytes() && count <= maximumBytes, "source binary grew");
                digest.update(buffer, 0, received);
            }
        }
        verifyContentStamp(pin); require(count == pin.bytes() && HexFormat.of().formatHex(digest.digest()).equals(pin.sha256()), "source binary digest differs");
    }
    public static LocalContentStamp stamp(Path path) throws IOException {
        require(path != null && path.isAbsolute() && !Files.isSymbolicLink(path), "absolute regular file, no symlink");
        BasicFileAttributes a = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        require(a.isRegularFile(), "regular source file required");
        // OpenJDK Windows fileKey is null. Do not reject valid files or invent a Win32 FileID.
        return new LocalContentStamp(path.toRealPath(), a.size(), a.creationTime().toString(), a.lastModifiedTime().toString());
    }
    public static byte[] readBounded(Path path, int maximumBytes) throws IOException {
        require(maximumBytes >= 1 && maximumBytes <= 32 * 1024 * 1024, "explicit bounded file read");
        LocalContentStamp before = stamp(path); require(before.bytes() >= 1 && before.bytes() <= maximumBytes, "file exceeds read budget");
        try (InputStream in = Files.newInputStream(path); ByteArrayOutputStream out = new ByteArrayOutputStream((int) before.bytes())) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = in.read(buffer)) != -1) {
                require((long) out.size() + count <= maximumBytes, "file grew beyond byte budget"); out.write(buffer, 0, count);
            }
            require(before.equals(stamp(path)) && out.size() == before.bytes(), "file content stamp/length changed during read");
            return out.toByteArray();
        }
    }
    public static String hash(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("JDK SHA-256 unavailable", error); }
    }
    static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "lowercase SHA-256"); }
    static void require(boolean valid, String message) throws IOException { if (!valid) { throw new IOException(message); } }
}
