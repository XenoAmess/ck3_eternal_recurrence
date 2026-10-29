package org.xar.ck3.control.wave3.planning.military;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Registration fragment consumed by the existing planning catalog and the one resident host. */
public final class MilitaryRouteGeometryPorts {
    private MilitaryRouteGeometryPorts() { }
    public static List<RegisteredProjection> registrations(ProjectionOperation geometryOperation) {
        return List.of(RegisteredProjection.of(new GeometryPort(Objects.requireNonNull(geometryOperation))));
    }
    private record GeometryPort(ProjectionOperation operation)
            implements ProjectionPort<MilitaryRouteGeometryCodec.Input, MilitaryRouteGeometryCodec.Input> {
        @Override public int inputMaximumBytes() { return MilitaryRouteGeometryCodec.MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MilitaryRouteGeometryCodec.MAXIMUM_BYTES; }
        @Override public MilitaryRouteGeometryCodec.Input decode(byte[] raw) { return MilitaryRouteGeometryCodec.decode(raw); }
        @Override public MilitaryRouteGeometryCodec.Input project(MilitaryRouteGeometryCodec.Input input) { return input; }
        @Override public byte[] encode(MilitaryRouteGeometryCodec.Input result) { return MilitaryRouteGeometryCodec.encode(result); }
    }
}
