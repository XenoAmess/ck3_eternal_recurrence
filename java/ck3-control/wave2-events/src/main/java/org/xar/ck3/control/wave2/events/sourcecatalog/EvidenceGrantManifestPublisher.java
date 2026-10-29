package org.xar.ck3.control.wave2.events.sourcecatalog;

import java.io.IOException;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;

/** Shared offline evidence publisher. Its target comes from server configuration, never projection JSON. */
public final class EvidenceGrantManifestPublisher {
    private EvidenceGrantManifestPublisher() { }
    public record Publication(Path path, int bytes, String sha256, int grants, int added) { }
    private record Directory(Path path, Object key) { }
    private record FileStamp(Object key, long bytes, java.nio.file.attribute.FileTime modified) { }
    @FunctionalInterface public interface LockedWork<T> { T run(Writer writer) throws IOException; }
    public static final class Writer {
        private final Path manifest;
        private final Thread owner = Thread.currentThread();
        private boolean active = true;
        private Writer(Path manifest) { this.manifest = manifest; }
        public Publication publish(List<ProjectionEvidenceGrant> additions) throws IOException {
            if (!active || owner != Thread.currentThread()) throw new IOException("offline evidence writer transaction is closed or belongs to another thread");
            return merge(manifest, ProjectionEvidenceCodec.validated(additions));
        }
    }

    /** All offline review producers use this exact manifest-side lock and immutable grant merge. */
    public static Publication publish(Path configuredManifest, List<ProjectionEvidenceGrant> verifiedAdditions) throws IOException {
        return transaction(configuredManifest, writer -> writer.publish(verifiedAdditions));
    }
    /** Batch analysis and grant publication share the same existing manifest writer lock. */
    public static synchronized <T> T transaction(Path configuredManifest, LockedWork<T> work) throws IOException {
        Path manifest = absolute(configuredManifest);
        Objects.requireNonNull(work);
        List<Directory> parents = directories(manifest.getParent());
        Path lockPath = manifest.resolveSibling(manifest.getFileName() + ".lock");
        if (OfflineAnalysisFiles.current().isPresent()) OfflineAnalysisFiles.current().orElseThrow().beforeLock(lockPath);
        try (FileChannel lockChannel = FileChannel.open(lockPath, StandardOpenOption.CREATE, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS);
                FileLock lock = lockChannel.lock()) {
            if (!lock.isValid()) throw new IOException("offline evidence writer lock unavailable");
            FileStamp locked = stamp(lockPath); verify(parents);
            Writer writer = new Writer(manifest);
            try {
                T result = work.run(writer);
                verify(parents);
                if (!locked.equals(stamp(lockPath))) throw new IOException("offline evidence writer lock identity changed");
                return result;
            } finally { writer.active = false; }
        }
    }
    private static Publication merge(Path manifest, List<ProjectionEvidenceGrant> additions) throws IOException {
            List<Directory> parents = directories(manifest.getParent());
            List<ProjectionEvidenceGrant> merged = new ArrayList<>();
            if (Files.exists(manifest, LinkOption.NOFOLLOW_LINKS)) {
                merged.addAll(ProjectionEvidenceCodec.decode(readStable(manifest, ProjectionEvidenceCodec.MAX_BYTES)));
            }
            int added = 0;
            for (ProjectionEvidenceGrant grant : additions) {
                byte[] actual = readStable(grant.path(), 2_097_152);
                if (actual.length != grant.bytes() || !sha(actual).equals(grant.sha256())) throw new IOException("published evidence pin changed before grant commit");
                ProjectionEvidenceGrant old = merged.stream().filter(row -> row.path().equals(grant.path()) && row.role() == grant.role()).findFirst().orElse(null);
                if (old != null && !old.equals(grant)) throw new IOException("immutable evidence grant already differs");
                if (old == null) { merged.add(grant); added++; }
            }
            byte[] raw = ProjectionEvidenceCodec.encode(merged);
            verify(parents);
            if (!Files.exists(manifest, LinkOption.NOFOLLOW_LINKS) || !java.util.Arrays.equals(readStable(manifest, ProjectionEvidenceCodec.MAX_BYTES), raw)) {
                if (OfflineAnalysisFiles.current().isPresent()) {
                    var actual = OfflineAnalysisFiles.current().orElseThrow().replace(manifest, raw);
                    if (!actual.path().equals(manifest.toString()) || actual.bytes() != raw.length || !actual.sha256().equals(sha(raw)))
                        throw new IOException("guarded manifest publication differs");
                } else {
                Path temporary = manifest.resolveSibling(manifest.getFileName() + ".tmp-" + UUID.randomUUID());
                try {
                    try (FileChannel output = FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS)) {
                        ByteBuffer bytes = ByteBuffer.wrap(raw); while (bytes.hasRemaining()) output.write(bytes); output.force(true);
                    }
                    verify(parents);
                    Files.move(temporary, manifest, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
                } finally { Files.deleteIfExists(temporary); }
                }
            }
            verify(parents);
            byte[] readback = readStable(manifest, ProjectionEvidenceCodec.MAX_BYTES);
            if (!java.util.Arrays.equals(raw, readback)) throw new IOException("offline evidence manifest readback differs");
            return new Publication(manifest, raw.length, sha(raw), merged.size(), added);
    }

    /** Identity-bearing, bounded exact read, also shared by the offline producer's declared roots. */
    public static byte[] readStable(Path supplied, int maximum) throws IOException {
        Path path = absolute(supplied); List<Directory> parents = directories(path.getParent());
        FileStamp before = stamp(path);
        if (maximum < 1 || before.bytes() < 1 || before.bytes() > maximum) throw new IOException("offline evidence byte bound exceeded");
        byte[] raw;
        try (var input = Files.newInputStream(path, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS)) { raw = input.readNBytes(maximum + 1); }
        if (raw.length != before.bytes() || !before.equals(stamp(path))) throw new IOException("offline evidence changed while reading");
        verify(parents); return raw;
    }
    private static FileStamp stamp(Path path) throws IOException {
        BasicFileAttributes attrs = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        if (!attrs.isRegularFile() || attrs.isSymbolicLink() || attrs.fileKey() == null || !path.toRealPath().equals(path)) throw new IOException("regular evidence file without aliases required");
        return new FileStamp(attrs.fileKey(), attrs.size(), attrs.lastModifiedTime());
    }
    private static Path absolute(Path path) throws IOException {
        if (path == null || !path.isAbsolute()) throw new IOException("absolute server-configured evidence path required"); return path.normalize();
    }
    private static List<Directory> directories(Path parent) throws IOException {
        List<Directory> result = new ArrayList<>(); Path cursor = parent.getRoot(); result.add(directory(cursor));
        for (Path part : cursor.relativize(parent)) { cursor = cursor.resolve(part); result.add(directory(cursor)); }
        return List.copyOf(result);
    }
    private static Directory directory(Path path) throws IOException {
        BasicFileAttributes attrs = org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(path);
        if (!attrs.isDirectory() || attrs.isSymbolicLink() || attrs.fileKey() == null || !path.toRealPath().equals(path)) throw new IOException("fixed evidence directory without aliases required");
        return new Directory(path, attrs.fileKey());
    }
    private static void verify(List<Directory> parents) throws IOException {
        for (Directory parent : parents) if (!Objects.equals(parent.key(), directory(parent.path()).key())) throw new IOException("evidence directory identity changed");
    }
    private static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
