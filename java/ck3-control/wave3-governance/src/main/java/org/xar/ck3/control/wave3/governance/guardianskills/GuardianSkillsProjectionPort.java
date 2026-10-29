package org.xar.ck3.control.wave3.governance.guardianskills;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationBatchJson;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsModel.Input;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsModel.Projection;

/** Complete owner input, single intrinsic profile validator and independently joined raw skill projection. */
public final class GuardianSkillsProjectionPort implements ProjectionPort<Input, Projection> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_SKILLS; }
    @Override public int inputMaximumBytes() { return EducationBatchJson.MAX_BYTES; }
    @Override public int outputMaximumBytes() { return 65_536; }
    @Override public Input decode(byte[] rawPayload) {
        return GuardianSkillsCodec.projectParsedInput(EducationBatchJson.decode(rawPayload));
    }
    @Override public Projection project(Input input) { return GuardianSkillInputs.project(input); }
    @Override public byte[] encode(Projection result) { return GuardianSkillsCodec.encodeProjection(result); }
}
