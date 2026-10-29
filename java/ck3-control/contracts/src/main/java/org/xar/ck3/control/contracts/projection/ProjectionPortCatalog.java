package org.xar.ck3.control.contracts.projection;

import java.util.List;

/** Public no-argument providers are declared in the existing domain artifact's standard service descriptor. */
public interface ProjectionPortCatalog {
    List<RegisteredProjection> registrations();
    /** Contextual catalogs must keep the no-arg path closed. Existing pure catalogs need no capabilities. */
    default List<RegisteredProjection> registrations(ProjectionHostContext context) {
        java.util.Objects.requireNonNull(context);
        return registrations();
    }
}
