package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.WindowsFileIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;

/** Existing native file reader/lease only. Pins record file facts, never Game/source/action qualification. */
final class CodexDecisionFilePins {
    record Document(Pin pin, byte[] bytes) {
        Document { Objects.requireNonNull(pin); bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    static final class Held implements AutoCloseable {
        private final IdentityBearingFileAttributes.ReadOnlyLease lease;
        private final Document original;
        private Held(IdentityBearingFileAttributes.ReadOnlyLease lease, Document original) {
            this.lease = lease; this.original = original;
        }
        Document original() { return original; }
        void verify() throws IOException {
            FileIdentity current = identity(lease.verifyCurrent());
            if (!current.equals(original.pin().identity())) throw new IOException("Codex native file identity drift");
        }
        @Override public void close() throws IOException { lease.close(); }
    }
    private CodexDecisionFilePins() { }
    static Held hold(Path path, int maximum) throws IOException {
        var lease = IdentityBearingFileAttributes.leaseBoundedWindows(path, maximum);
        try {
            var raw = lease.originalRead();
            byte[] bytes = raw.bytes();
            if (bytes.length == 0) throw new IOException("nonempty exact Codex file required");
            var ref = new ExactRef(path.toAbsolutePath().normalize().toString(), bytes.length, ActionCodec.sha256(bytes));
            Held held = new Held(lease, new Document(new Pin(ref, identity(raw.attributes())), bytes));
            lease.releaseOriginalBytes(); held.verify();
            return held;
        } catch (IOException | RuntimeException | Error failure) {
            try { lease.close(); } catch (IOException closing) { failure.addSuppressed(closing); }
            throw failure;
        }
    }
    static Document read(Path path, int maximum) throws IOException {
        try (Held held = hold(path, maximum)) { held.verify(); return held.original(); }
    }
    private static FileIdentity identity(BasicFileAttributes attributes) throws IOException {
        if (!(attributes.fileKey() instanceof WindowsFileIdentity key)) throw new IOException("actual Windows Codex FileID required");
        return new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                attributes.lastModifiedTime().toInstant().toString(), attributes.size());
    }
}
