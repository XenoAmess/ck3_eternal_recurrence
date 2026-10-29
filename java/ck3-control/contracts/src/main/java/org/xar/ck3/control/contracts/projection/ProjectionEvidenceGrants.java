package org.xar.ck3.control.contracts.projection;

import java.util.List;

/** Only the server assembly supplies this fixed source; callers cannot select a manifest or publish grants. */
@FunctionalInterface
public interface ProjectionEvidenceGrants {
    List<ProjectionEvidenceGrant> currentGrants();
    static ProjectionEvidenceGrants fixed(List<ProjectionEvidenceGrant> grants) {
        List<ProjectionEvidenceGrant> snapshot = ProjectionEvidenceCodec.validated(grants);
        return () -> snapshot;
    }
}
