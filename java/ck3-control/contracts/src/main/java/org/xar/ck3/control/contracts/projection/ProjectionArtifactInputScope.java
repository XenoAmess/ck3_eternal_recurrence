package org.xar.ck3.control.contracts.projection;

import java.util.function.Function;

/** Server-owned, single-slot input capability. The computation and result are covered by both custody checks. */
public interface ProjectionArtifactInputScope {
    <T> T withInput(ProjectionOperation operation, ProjectionArtifactInputRef input, Function<byte[], T> computation);
}
