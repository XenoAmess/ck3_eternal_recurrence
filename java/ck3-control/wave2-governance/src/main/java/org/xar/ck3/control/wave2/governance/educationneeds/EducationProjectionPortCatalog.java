package org.xar.ck3.control.wave2.governance.educationneeds;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceProjectionPort;

public final class EducationProjectionPortCatalog implements ProjectionPortCatalog {
    public EducationProjectionPortCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new EducationNeedsProjectionPort()),
                RegisteredProjection.of(new EducationCandidateProjectionPort()), RegisteredProjection.of(new EducationPreferenceProjectionPort()));
    }
}
