package org.xar.ck3.control.wave2.runtime.savedproof;

import java.io.IOException;
import java.nio.file.Path;
import org.xar.ck3.control.contracts.FileStatIdentity;

/** Attributes only. This port must not open/read/hash persistence bodies. */
@FunctionalInterface
public interface SavedProofIdentityReader {
    FileStatIdentity stat(Path path) throws IOException;
}
