package org.xar.ck3.control.wave3.runtime.armysummary;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** One domain-owned catalog for the resident Quarkus host's ordinary ServiceLoader assembly. */
public final class ArmyMcpSummaryProjectionCatalog implements ProjectionPortCatalog {
    public ArmyMcpSummaryProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new ArmyQuerySummaryProjectionPort()),
                RegisteredProjection.of(new ArmyAutoSummaryProjectionPort()));
    }
}
