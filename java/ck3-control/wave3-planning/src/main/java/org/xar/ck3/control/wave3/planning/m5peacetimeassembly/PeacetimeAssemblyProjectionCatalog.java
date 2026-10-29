package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Domain-owned ServiceLoader registration consumed once by the shared host. */
public final class PeacetimeAssemblyProjectionCatalog implements ProjectionPortCatalog {
    public PeacetimeAssemblyProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new PeacetimeAssemblyProjectionPort()));
    }
}
