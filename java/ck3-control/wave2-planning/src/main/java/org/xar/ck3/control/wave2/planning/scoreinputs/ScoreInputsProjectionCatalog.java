package org.xar.ck3.control.wave2.planning.scoreinputs;

import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Existing wave2 domain artifact contributes one pure operation to the single Quarkus host. */
public final class ScoreInputsProjectionCatalog implements ProjectionPortCatalog {
    public ScoreInputsProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new CashMetricsPort()));
    }
    private static final class CashMetricsPort implements ProjectionPort<CashMetricsCodec.Request, CashProjection> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.SCORE_CASH_METRICS; }
        @Override public int inputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
        @Override public int outputMaximumBytes() { return StrictJson.INPUT_MAX_BYTES; }
        @Override public CashMetricsCodec.Request decode(byte[] input) { return CashMetricsCodec.decodeRequest(input); }
        @Override public CashProjection project(CashMetricsCodec.Request input) { return input.project(); }
        @Override public byte[] encode(CashProjection result) { return CashMetricsCodec.encode(result); }
    }
}
