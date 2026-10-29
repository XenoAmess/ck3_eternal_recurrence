package org.xar.ck3.control.wave3.runtime.armysummary;

import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;

/** Pure shared-host adapter; the existing Army codec remains the only projection implementation. */
public final class ArmyQuerySummaryProjectionPort implements ProjectionPort<ArmyMcpSummary.Query, ArmyMcpSummary.Query> {
    @Override public ProjectionOperation operation() { return ProjectionOperation.ARMY_QUERY_SUMMARY_PROJECT; }
    @Override public ArmyMcpSummary.Query decode(byte[] rawPayload) { return ArmyMcpSummaryCodec.decodeQuery(rawPayload); }
    @Override public ArmyMcpSummary.Query project(ArmyMcpSummary.Query input) { return Objects.requireNonNull(input); }
    @Override public byte[] encode(ArmyMcpSummary.Query result) { return ArmyMcpSummaryCodec.encodeQueryResult(Objects.requireNonNull(result)); }
    @Override public int inputMaximumBytes() { return ArmyMcpSummaryCodec.MAX_INPUT_BYTES; }
    @Override public int outputMaximumBytes() { return ArmyMcpSummaryCodec.MAX_OUTPUT_BYTES; }
}
