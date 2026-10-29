package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Loaded once by the existing Quarkus composition root, within this domain artifact. */
public final class DeadlineTransportProjectionCatalog implements ProjectionPortCatalog {
    public DeadlineTransportProjectionCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new DeadlineTransportProjectionPort()));
    }
}
