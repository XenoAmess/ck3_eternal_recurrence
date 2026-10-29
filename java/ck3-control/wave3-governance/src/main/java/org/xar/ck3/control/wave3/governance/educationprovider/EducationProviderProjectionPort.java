package org.xar.ck3.control.wave3.governance.educationprovider;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Request;
import org.xar.ck3.control.wave3.governance.educationprovider.EducationProviderModel.Validation;

/** Shared host registration for the existing pure provider owner; no source/action qualification is created. */
public final class EducationProviderProjectionPort implements ProjectionPort<Request, Validation> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_PROVIDER; }
    @Override public Request decode(byte[] rawPayload) { return EducationProviderCodec.decode(rawPayload); }
    @Override public Validation project(Request input) { return EducationProviderValidator.validate(input); }
    @Override public byte[] encode(Validation result) { return EducationProviderCodec.encode(result.provider()); }
    @Override public int inputMaximumBytes() { return EducationProviderCodec.REQUEST_LIMIT; }
    @Override public int outputMaximumBytes() { return EducationProviderCodec.PROVIDER_LIMIT; }
}
