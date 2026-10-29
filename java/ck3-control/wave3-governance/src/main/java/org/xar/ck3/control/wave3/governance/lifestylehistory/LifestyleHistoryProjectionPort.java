package org.xar.ck3.control.wave3.governance.lifestylehistory;

import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Typed host phases over the existing unique domain. No I/O, fallback or authority. */
public final class LifestyleHistoryProjectionPort implements ProjectionPort<LifestyleHistory.Input, LifestyleHistory.Selection> {
    public LifestyleHistoryProjectionPort() { }
    @Override public ProjectionOperation operation() { return ProjectionOperation.GOVERNANCE_LIFESTYLE_HISTORY; }
    @Override public LifestyleHistory.Input decode(byte[] raw) { return LifestyleHistoryCodec.decode(raw); }
    @Override public LifestyleHistory.Selection project(LifestyleHistory.Input input) { return LifestyleHistory.select(input); }
    @Override public byte[] encode(LifestyleHistory.Selection result) { return LifestyleHistoryCodec.encodeSelection(result); }
    @Override public int inputMaximumBytes() { return 65_536; }
    @Override public int outputMaximumBytes() { return 65_536; }
}
