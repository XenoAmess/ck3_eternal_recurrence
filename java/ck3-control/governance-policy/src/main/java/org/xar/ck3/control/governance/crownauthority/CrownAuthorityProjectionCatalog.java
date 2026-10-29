package org.xar.ck3.control.governance.crownauthority;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Registers the existing Crown selector in the existing resident projection host. */
public final class CrownAuthorityProjectionCatalog implements ProjectionPortCatalog {
    public CrownAuthorityProjectionCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new CrownPort()));
    }

    private static final class CrownPort implements ProjectionPort<CrownAuthorityCodec.Request, CrownAuthorityPolicy.Choice> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.GOVERNANCE_CROWN_CHOOSE; }
        @Override public CrownAuthorityCodec.Request decode(byte[] rawPayload) {
            return CrownAuthorityCodec.decodeRequest(rawPayload);
        }
        @Override public CrownAuthorityPolicy.Choice project(CrownAuthorityCodec.Request input) {
            return CrownAuthorityPolicy.choose(input.readback(), input.reservesRaw());
        }
        @Override public byte[] encode(CrownAuthorityPolicy.Choice result) {
            return CrownAuthorityCodec.encodeChoice(result);
        }
    }

    /** The original law READ decoder supplies same-call context; this is the existing Crown consumer input. */
    public static CrownAuthorityCodec.Request nativeQueryReturned(CrownAuthorityNativeQuery.RequestContext actual,
            CrownAuthorityNativeWire.Envelope original,CrownAuthorityNativeQuery.Snapshot after,
            java.util.Map<CrownAuthorityPolicy.Currency,java.math.BigInteger> reservesRaw) {
        return CrownAuthorityNativeQuery.consumerRequest(actual,original,after,reservesRaw);
    }
    public static CrownAuthorityPolicy.Choice projectNativeQuery(CrownAuthorityNativeQuery.RequestContext actual,
            CrownAuthorityNativeWire.Envelope original,CrownAuthorityNativeQuery.Snapshot after,
            java.util.Map<CrownAuthorityPolicy.Currency,java.math.BigInteger> reservesRaw) {
        return new CrownPort().project(nativeQueryReturned(actual,original,after,reservesRaw));
    }
}
