package org.xar.ck3.control.wave2.runtime.savedproof;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Locale;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Finite source/small evidence access. This helper never accepts Driver/SAVE bodies. */
final class SavedProofFiles {
    private SavedProofFiles() { }
    static byte[] read(Path path, int cap) throws IOException {
        String name = path.toString().replace('\\', '/').toLowerCase(Locale.ROOT);
        StrictJson.require(!name.endsWith("/driver-state.json") && !name.endsWith(".ck3") && !name.endsWith(".sav"), "body path outside source/evidence lane");
        BasicFileAttributes before = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        StrictJson.require(before.isRegularFile() && !before.isSymbolicLink() && before.size() <= cap, "ordinary finite source/evidence");
        byte[] bytes;
        try (InputStream stream = Files.newInputStream(path, LinkOption.NOFOLLOW_LINKS)) { bytes = stream.readNBytes(cap + 1); }
        BasicFileAttributes after = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        StrictJson.require(bytes.length <= cap && bytes.length == before.size()
                && before.size() == after.size() && before.lastModifiedTime().equals(after.lastModifiedTime())
                && java.util.Objects.equals(before.fileKey(), after.fileKey()), "stable complete bounded metadata/source");
        return bytes;
    }
    static byte[] exact(ExactRef ref, int cap) throws IOException {
        StrictJson.require(ref.bytes() <= cap, "source-specific cap");
        byte[] bytes = read(Path.of(ref.path()), cap);
        StrictJson.require(bytes.length == ref.bytes() && RecoveryEvidence.sha256(bytes).equals(ref.sha256()), "exact source/evidence bytes");
        return bytes;
    }
    static RecoveryEvidence publish(Path path, byte[] bytes) throws IOException {
        RecoveryEvidence result = new RecoveryEvidence(new ExactRef(path.toString(), bytes.length, RecoveryEvidence.sha256(bytes)), bytes);
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) { channel.write(buffer); }
            channel.force(true);
        }
        StrictJson.require(java.util.Arrays.equals(bytes, read(path, RecoveryEvidence.MAX_BYTES)), "create-only evidence readback");
        return result;
    }
}
