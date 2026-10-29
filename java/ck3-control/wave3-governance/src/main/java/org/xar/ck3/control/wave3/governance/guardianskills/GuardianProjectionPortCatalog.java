package org.xar.ck3.control.wave3.governance.guardianskills;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceProjectionPort;

public final class GuardianProjectionPortCatalog implements ProjectionPortCatalog {
    public GuardianProjectionPortCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new GuardianSkillsProjectionPort()), RegisteredProjection.of(new GuardianCadenceProjectionPort()));
    }
}
