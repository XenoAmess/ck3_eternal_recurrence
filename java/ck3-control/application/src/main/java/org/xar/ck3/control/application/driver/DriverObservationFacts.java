package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** A complete, versioned Driver producer projection. Never constructed from a requested action's before frame. */
public record DriverObservationFacts(DriverStateSnapshot.Complete driver, long driverVersion, long episodeEpoch,
        NativeObservationPort.TransportSession transport, String snapshotId, BigInteger nativeRevision,
        String nativeStateSha256, BigInteger publicRevision, long observationVersion, G2Source source,
        OpportunityJson.Obj originalSemanticFields, ExactRef semanticFactsEvidence) {
    public DriverObservationFacts {
        Objects.requireNonNull(driver); StrictJson.safe(driverVersion, 0); StrictJson.safe(episodeEpoch, 0);
        Objects.requireNonNull(transport); StrictJson.text(snapshotId); Objects.requireNonNull(nativeRevision);
        StrictJson.require(nativeRevision.signum() > 0, "actual positive native frame required");
        StrictJson.require(nativeStateSha256 != null && nativeStateSha256.matches("[0-9a-f]{64}"), "actual native state SHA required");
        new org.xar.ck3.control.contracts.PublicRevision(publicRevision);
        StrictJson.safe(observationVersion, 1); Objects.requireNonNull(source); Objects.requireNonNull(originalSemanticFields);
        Objects.requireNonNull(semanticFactsEvidence); StrictJson.require(semanticFactsEvidence.bytes() > 0, "real semantic facts evidence required");
    }
    public sealed interface Result permits Known, Unavailable { }
    public record Known(DriverObservationFacts facts) implements Result { public Known { Objects.requireNonNull(facts); } }
    public record Unavailable(List<String> reasons) implements Result {
        public Unavailable { reasons = List.copyOf(reasons); StrictJson.require(!reasons.isEmpty(), "explicit missing semantic facts required"); }
    }
    @FunctionalInterface public interface Reader {
        /** Must join the actual frame to the same frozen Driver/episode/public-revision producer. */
        Result read(NativeObservationPort.ObservedFrame actual);
    }
}
