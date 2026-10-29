package org.xar.ck3.control.wave3.governance.educationoptions;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsOperation.Request;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsOperation.Result;

/** Shared host registration for validated options and the actual Service's pure intent/attempt consumers. */
public final class EducationOptionsProjectionPort implements ProjectionPort<Request, Result> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_OPTIONS; }
    @Override public Request decode(byte[] rawPayload) { return EducationOptionsOperation.decode(rawPayload); }
    @Override public Result project(Request input) { return EducationOptionsOperation.execute(input); }
    @Override public byte[] encode(Result result) { return EducationOptionsOperation.encode(result); }
    @Override public int inputMaximumBytes() { return EducationOptionsCodec.BYTE_BUDGET; }
    @Override public int outputMaximumBytes() { return EducationOptionsCodec.BYTE_BUDGET; }
}
