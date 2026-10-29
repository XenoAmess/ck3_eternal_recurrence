package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;

/** Bounded immutable input-file output only. This port grants neither a continuity writer nor any Game admission.
 * Only the actual independent bootstrap-card guard and the identical existing runtime guard may supply it. */
public sealed interface RootBootstrapInputFiles permits RootBootstrapOutputGuard,RootRuntimeBootstrapInputFiles {
    /** Exact absolute target files, distinct and below the issuer-approved existing plain directories. */
    void requireTargets(List<Path> actualTargets)throws IOException;
    /** One retained producer: actual observe/read/verify plus CREATE_NEW. Mutable replace is never an input producer. */
    CheckpointFiles files();
}
