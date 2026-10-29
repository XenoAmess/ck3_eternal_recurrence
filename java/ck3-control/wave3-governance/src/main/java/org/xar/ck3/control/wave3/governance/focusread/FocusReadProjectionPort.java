package org.xar.ck3.control.wave3.governance.focusread;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Typed shared-host boundary; malformed protocol/ID tokens are rejected during decode. */
public final class FocusReadProjectionPort implements ProjectionPort<FocusReadCodec.Request, FocusReadCodec.Evaluation> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.GOVERNANCE_LIFESTYLE_FOCUS_READ; }
    @Override public int inputMaximumBytes() { return FocusReadCodec.MAX_BYTES; }
    @Override public int outputMaximumBytes() { return FocusReadCodec.MAX_BYTES; }
    @Override public FocusReadCodec.Request decode(byte[] raw) { return FocusReadCodec.decode(raw); }
    @Override public FocusReadCodec.Evaluation project(FocusReadCodec.Request input) { return FocusReadCodec.project(input); }
    @Override public byte[] encode(FocusReadCodec.Evaluation result) { return FocusReadCodec.encode(result); }
}
