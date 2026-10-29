package org.xar.ck3.control.wave3.planning.military;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Existing one-host ProjectionDispatcher consumes this explicit ServiceLoader catalog. */
public final class MilitaryPlanningProjectionCatalog implements ProjectionPortCatalog {
    public MilitaryPlanningProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return MilitaryRouteGeometryPorts.registrations(ProjectionOperation.MILITARY_ROUTE_GEOMETRY);
    }
}
