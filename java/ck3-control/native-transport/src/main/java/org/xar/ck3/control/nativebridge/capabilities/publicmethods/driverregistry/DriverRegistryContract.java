package org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;

/** Sole cached-succession public contract; other delegated original families keep their own typed models. */
public final class DriverRegistryContract {
    public static final String CACHED_NAME = "ck3_query_actor_cached_succession_v1";
    private DriverRegistryContract() { }
    public record CachedRequest(BigInteger expectedRevision) {
        public CachedRequest { StrictJson.require(expectedRevision != null && expectedRevision.signum() > 0
                && expectedRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "positive actual public uint64 revision required"); }
    }
    public record CachedResponse(CachedSuccession12004.Observation original) {
        public CachedResponse { Objects.requireNonNull(original); }
    }
}
