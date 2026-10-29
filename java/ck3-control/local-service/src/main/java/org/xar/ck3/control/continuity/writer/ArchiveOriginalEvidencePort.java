package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Concrete Root original-byte reader. Only this installed archive's committed objects are read;
 * caller paths cannot acquire custody by matching a digest or writer-lock path.
 */
public final class ArchiveOriginalEvidencePort implements OriginalEvidencePort {
    private final NativeOutcomeArchive archive;

    public ArchiveOriginalEvidencePort(NativeOutcomeArchive archive) { this.archive = Objects.requireNonNull(archive); }
    public NativeOutcomeArchive archive() { return archive; }
    public ContinuityWriter writer() { return archive.writer(); }

    @Override public byte[] read(ContinuityStorePort.Session borrowed, ExactRef original, int maximumBytes) throws IOException {
        return archive.readArtifact(Objects.requireNonNull(borrowed), Objects.requireNonNull(original), maximumBytes);
    }
}
