package org.xar.ck3.control.wave3.military.landcontext;

import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave3.military.holyobservation.HolyDefenderObservationPort;

/** Existing complete LAND and ordinary holy-war observation in the one host; no Game or writer capability. */
public final class LandContextProjectionCatalog implements ProjectionPortCatalog {
    public static final int MAX_BYTES = 524_288;
    public LandContextProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new StockPort()),
                RegisteredProjection.of(new HolyDefenderObservationPort(ProjectionOperation.MILITARY_HOLY_DEFENDER_OBSERVATION)));
    }
    private static final class StockPort implements ProjectionPort<FullLandStockInput, FullLandStockProjection> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_LAND_CONTEXT_STOCK; }
        @Override public FullLandStockInput decode(byte[] raw) { return LandContextCodec.decodeStockInput(raw); }
        @Override public FullLandStockProjection project(FullLandStockInput input) { return FullLandStockPolicy.project(input); }
        @Override public byte[] encode(FullLandStockProjection output) {
            return StrictJson.canonical(LandContextCodec.encodeStockProjection(output), MAX_BYTES);
        }
        @Override public int inputMaximumBytes() { return MAX_BYTES; }
        @Override public int outputMaximumBytes() { return MAX_BYTES; }
    }
}
