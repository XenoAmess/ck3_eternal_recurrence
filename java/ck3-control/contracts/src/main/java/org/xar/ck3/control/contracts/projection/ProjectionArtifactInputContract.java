package org.xar.ck3.control.contracts.projection;

import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectionArtifactAuthority;
import org.xar.ck3.control.contracts.ExactRef;

/** Narrow claim/domain adaptation. All authority records and wire fields have one build-tools owner. */
public final class ProjectionArtifactInputContract {
    private ProjectionArtifactInputContract() { }

    public static ControlBuild.FileRef fileRef(ExactRef claim) {
        return ProjectionArtifactAuthority.reference(new ControlBuild.FileRef(claim.path(), claim.bytes(), claim.sha256()));
    }

    public static ExactRef exactRef(ControlBuild.FileRef proof) {
        ProjectionArtifactAuthority.reference(proof);
        return new ExactRef(proof.path(), proof.bytes(), proof.sha256());
    }

}
