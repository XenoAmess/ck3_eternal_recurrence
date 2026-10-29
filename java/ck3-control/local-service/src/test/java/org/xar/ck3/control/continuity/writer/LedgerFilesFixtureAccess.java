package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;

/** Test-only access to the original bounded ledger reader and native identity provider. */
public final class LedgerFilesFixtureAccess {
    private LedgerFilesFixtureAccess() { }

    /** Public test data preserves the original Pin and defensive byte ownership. */
    public record Document(WriterContracts.Pin pin, byte[] bytes) {
        public Document {
            Objects.requireNonNull(pin);
            bytes = Objects.requireNonNull(bytes).clone();
        }
        @Override public byte[] bytes() { return bytes.clone(); }
    }

    public static Document read(Path path, int maximumBytes) throws IOException {
        LedgerFiles.Document actual = LedgerFiles.read(path, maximumBytes);
        return new Document(actual.pin(), actual.bytes());
    }

    public static WriterContracts.FileIdentity identity(Path path) throws IOException {
        return LedgerFiles.identity(path);
    }
}
