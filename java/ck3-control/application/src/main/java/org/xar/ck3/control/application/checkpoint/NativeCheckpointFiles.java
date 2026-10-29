package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;

/** Reuses the shared Windows file producer; this adapter never launches Game or changes SAVE. */
public final class NativeCheckpointFiles implements CheckpointFiles {
    private static final BigInteger UNIX_EPOCH_FILETIME = new BigInteger("116444736000000000");
    @Override public Optional<FileWitness> observe(Path path) throws IOException {
        if (!path.isAbsolute()) throw new IOException("explicit absolute checkpoint path required");
        if (!Files.exists(path)) return Optional.empty();
        SharedSourceFiles.Witness observed = SharedSourceFiles.observe(path);
        var ref = observed.source(); var nativeFile = observed.nativeFile();
        String unixNs = new BigInteger(nativeFile.lastWriteFiletimeDecimal()).subtract(UNIX_EPOCH_FILETIME).multiply(BigInteger.valueOf(100)).toString();
        return Optional.of(new FileWitness(new ExactRef(ref.path(), ref.bytes(), ref.sha256()),
                new FileStatIdentity(BigInteger.valueOf(ref.bytes()), nativeFile.fileIdDecimal(), unixNs)));
    }
    @Override public byte[] read(FileWitness expected, int maximumBytes) throws IOException {
        verify(expected);
        if (expected.reference().bytes() > maximumBytes) throw new IOException("bounded Driver read exceeded");
        byte[] raw = Files.readAllBytes(Path.of(expected.reference().path())); verify(expected);
        if (raw.length != expected.reference().bytes()) throw new IOException("Driver size changed");
        return raw;
    }
    @Override public FileWitness replace(Path target, byte[] completeBytes) throws IOException {
        if (!target.isAbsolute() || completeBytes == null || completeBytes.length == 0 || completeBytes.length > DriverCheckpointStore.MAX_DRIVER_BYTES) throw new IOException("bounded complete Driver bytes required");
        SharedSourceFiles.plainAncestors(target);
        Path temporary = target.resolveSibling("." + target.getFileName() + "." + UUID.randomUUID() + ".tmp");
        try {
            try (FileChannel output = FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(completeBytes); while (buffer.hasRemaining()) output.write(buffer); output.force(true);
            }
            Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            FileWitness result = observe(target).orElseThrow(() -> new IOException("Driver replacement missing"));
            if (!result.reference().sha256().equals(DriverCheckpointStore.sha256(completeBytes))) throw new IOException("Driver replacement content mismatch");
            return result;
        } finally { Files.deleteIfExists(temporary); }
    }
    @Override public FileWitness createNew(Path target, byte[] completeBytes) throws IOException {
        if (!target.isAbsolute() || completeBytes == null || completeBytes.length == 0
                || completeBytes.length > DriverCheckpointStore.MAX_DRIVER_BYTES)
            throw new IOException("bounded complete immutable bytes and absolute target required");
        SharedSourceFiles.plainAncestors(target);
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) throw new IOException("immutable target already exists");
        Path temporary = target.resolveSibling("." + target.getFileName() + "." + UUID.randomUUID() + ".tmp");
        try {
            try (FileChannel output = FileChannel.open(temporary, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(completeBytes);
                while (buffer.hasRemaining()) output.write(buffer);
                output.force(true);
            }
            FileWitness privateFile = observe(temporary).orElseThrow(() -> new IOException("immutable private file missing"));
            if (privateFile.reference().bytes() != completeBytes.length
                    || !privateFile.reference().sha256().equals(DriverCheckpointStore.sha256(completeBytes)))
                throw new IOException("immutable private file differs from complete input");
            // NTFS creates the target name only if absent; ATOMIC_MOVE is allowed to replace on Windows.
            Files.createLink(target, temporary);
            FileWitness published = observe(target).orElseThrow(() -> new IOException("immutable publication missing"));
            if (!published.identity().equals(privateFile.identity()) || published.reference().bytes() != completeBytes.length
                    || !published.reference().sha256().equals(privateFile.reference().sha256()))
                throw new IOException("immutable publication identity or bytes differ");
            return published;
        } finally { Files.deleteIfExists(temporary); }
    }
    @Override public FileWitness copyNew(FileWitness source, Path target) throws IOException {
        if (!target.isAbsolute()) throw new IOException("explicit absolute immutable seed path required");
        SharedSourceFiles.plainAncestors(target); verify(source);
        if (Files.exists(target)) throw new IOException("immutable seed target already exists");
        Path temporary = target.resolveSibling("." + target.getFileName() + "." + UUID.randomUUID() + ".tmp");
        try {
            Files.copy(Path.of(source.reference().path()), temporary);
            try (FileChannel output = FileChannel.open(temporary, StandardOpenOption.WRITE)) { output.force(true); }
            FileWitness copied = observe(temporary).orElseThrow(() -> new IOException("immutable seed copy missing"));
            if (copied.reference().bytes() != source.reference().bytes() || !copied.reference().sha256().equals(source.reference().sha256())) throw new IOException("immutable seed copy content differs");
            verify(source);
            // Same-directory private file, atomically published without replacing an existing immutable seed.
            Files.createLink(target, temporary);
            FileWitness result = observe(target).orElseThrow(() -> new IOException("published immutable seed missing"));
            if (!result.identity().equals(copied.identity()) || result.reference().bytes() != source.reference().bytes()
                    || !result.reference().sha256().equals(source.reference().sha256())) throw new IOException("immutable seed readback differs");
            verify(source); return result;
        } finally { Files.deleteIfExists(temporary); }
    }
}
