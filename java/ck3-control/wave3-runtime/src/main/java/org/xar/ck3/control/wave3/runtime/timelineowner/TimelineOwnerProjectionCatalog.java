package org.xar.ck3.control.wave3.runtime.timelineowner;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Discovered by the existing application host; creates no service, HTTP client or process. */
public final class TimelineOwnerProjectionCatalog implements ProjectionPortCatalog {
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new TimelineOwnerProjectionPort()));
    }
}
