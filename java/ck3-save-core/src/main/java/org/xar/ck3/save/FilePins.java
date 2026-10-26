package org.xar.ck3.save;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.save.SaveContracts.Pin;

public final class FilePins {
    private FilePins() { }
    public static Pin pin(Path path) throws IOException {
        Path real = path.toRealPath();
        if (!Files.isRegularFile(real)) throw new IOException("regular file required: " + real);
        MessageDigest digest = digest();
        try (InputStream stream = Files.newInputStream(real)) {
            byte[] buffer = new byte[65536]; int read;
            while ((read = stream.read(buffer)) != -1) digest.update(buffer, 0, read);
        }
        return new Pin(real.toString(), Files.size(real), HexFormat.of().formatHex(digest.digest()));
    }
    public static void verify(Path path, Pin expected) throws IOException {
        Pin actual = pin(path);
        if (actual.bytes() != expected.bytes() || !actual.sha256().equals(expected.sha256())) throw new IOException("input pin mismatch: " + path);
    }
    public static String sha256(byte[] bytes) { return HexFormat.of().formatHex(digest().digest(bytes)); }
    public static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
