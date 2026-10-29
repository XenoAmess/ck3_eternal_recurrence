package org.xar.ck3.control.wave3.runtime.childexports;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

public final class ChildExportProjectionCatalog implements ProjectionPortCatalog {
    public ChildExportProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new ChildExportProjectionPort()));
    }
}
