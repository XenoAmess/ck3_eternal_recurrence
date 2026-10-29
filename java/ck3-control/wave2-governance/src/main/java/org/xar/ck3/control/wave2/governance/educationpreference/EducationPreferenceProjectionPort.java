package org.xar.ck3.control.wave2.governance.educationpreference;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.Input;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.Result;

/** Whole-batch host port: retained requests preserve native pair identity and original indices. */
public final class EducationPreferenceProjectionPort implements ProjectionPort<Input, Result> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_PREFERENCE; }
    @Override public int inputMaximumBytes() { return EducationBatchJson.MAX_BYTES; }
    @Override public int outputMaximumBytes() { return EducationBatchJson.MAX_BYTES; }
    @Override public Input decode(byte[] rawPayload) {
        return EducationPreferenceCodec.projectParsedInput(EducationBatchJson.decode(rawPayload));
    }
    @Override public Result project(Input input) { return EducationRequestPreference.order(input); }
    @Override public byte[] encode(Result result) {
        return EducationBatchJson.encode(EducationPreferenceCodec.resultNode(result));
    }
}
