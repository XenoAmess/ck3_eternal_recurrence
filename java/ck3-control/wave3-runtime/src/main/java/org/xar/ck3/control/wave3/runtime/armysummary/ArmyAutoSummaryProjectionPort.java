package org.xar.ck3.control.wave3.runtime.armysummary;

import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Pure shared-host adapter; no second summary, native query or Python fallback is present. */
public final class ArmyAutoSummaryProjectionPort implements ProjectionPort<ArmyMcpSummary.AutoTurn, ArmyMcpSummary.AutoTurn> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.ARMY_AUTO_SUMMARY_PROJECT; }
    @Override public ArmyMcpSummary.AutoTurn decode(byte[] rawPayload) { return ArmyMcpSummaryCodec.decodeAutoTurn(rawPayload); }
    @Override public ArmyMcpSummary.AutoTurn project(ArmyMcpSummary.AutoTurn input) { return Objects.requireNonNull(input); }
    @Override public byte[] encode(ArmyMcpSummary.AutoTurn result) { return ArmyMcpSummaryCodec.encodeAutoResult(Objects.requireNonNull(result)); }
    @Override public int inputMaximumBytes() { return ArmyMcpSummaryCodec.MAX_INPUT_BYTES; }
    @Override public int outputMaximumBytes() { return ArmyMcpSummaryCodec.MAX_OUTPUT_BYTES; }
}
