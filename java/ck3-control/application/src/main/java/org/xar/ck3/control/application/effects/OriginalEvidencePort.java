package org.xar.ck3.control.application.effects;

import java.io.IOException;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Root binds NativeOutcomeArchive.readArtifact; this application port reads the committed original bytes in the borrowed same-writer scope. */
@FunctionalInterface public interface OriginalEvidencePort {
    byte[] read(ContinuityStorePort.Session borrowed, ExactRef original, int maximumBytes) throws IOException;
}
