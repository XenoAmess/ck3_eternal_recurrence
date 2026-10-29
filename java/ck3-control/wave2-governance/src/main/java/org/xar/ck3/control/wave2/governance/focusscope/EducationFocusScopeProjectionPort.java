package org.xar.ck3.control.wave2.governance.focusscope;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Typed host phases over the existing unique domain. No I/O, fallback or authority. */
public final class EducationFocusScopeProjectionPort implements ProjectionPort<EducationFocusScopeCodec.Request, EducationFocusScopeCodec.Result> {
    public EducationFocusScopeProjectionPort() { }
    @Override public ProjectionOperation operation() { return ProjectionOperation.GOVERNANCE_EDUCATION_FOCUS_SCOPE; }
    @Override public EducationFocusScopeCodec.Request decode(byte[] raw) { return EducationFocusScopeCodec.decode(raw); }
    @Override public EducationFocusScopeCodec.Result project(EducationFocusScopeCodec.Request input) { return EducationFocusScopeCodec.execute(input); }
    @Override public byte[] encode(EducationFocusScopeCodec.Result result) { return EducationFocusScopeCodec.encodeResult(result); }
    @Override public int inputMaximumBytes() { return 65_536; }
    @Override public int outputMaximumBytes() { return 65_536; }
}
