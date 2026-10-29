package org.xar.ck3.control.warbudget.projection;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** One declaration inside the existing domain artifact; the resident host owns assembly. */
public final class WarBudgetProjectionCatalog implements ProjectionPortCatalog {
    public WarBudgetProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new WarBudgetProjectionPort()));
    }
}
