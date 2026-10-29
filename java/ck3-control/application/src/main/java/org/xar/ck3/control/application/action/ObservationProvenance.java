package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** A received push has no request ID. Only a real independent query may carry one. */
public sealed interface ObservationProvenance permits ObservationProvenance.Query, ObservationProvenance.Push {
    boolean independentOf(String submittedRequestId);
    void validate(ObservationIdentity after, ExactRef originalEvidence);

    record Query(String requestId) implements ObservationProvenance {
        public Query { StrictJson.text(requestId); }
        @Override public boolean independentOf(String submittedRequestId) {
            StrictJson.text(submittedRequestId); return !requestId.equals(submittedRequestId);
        }
        @Override public void validate(ObservationIdentity after, ExactRef originalEvidence) {
            Objects.requireNonNull(after); Objects.requireNonNull(originalEvidence);
            StrictJson.require(originalEvidence.bytes() > 0, "independent query original evidence required");
        }
    }

    record Push(String snapshotId, BigInteger nativeRevision, ExactRef originalPacket) implements ObservationProvenance {
        public Push {
            StrictJson.text(snapshotId); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(originalPacket);
            StrictJson.require(nativeRevision.signum() >= 0 && nativeRevision.toString().length() <= 1000 && originalPacket.bytes() > 0, "actual bounded native push revision and original packet required");
        }
        @Override public boolean independentOf(String submittedRequestId) { StrictJson.text(submittedRequestId); return true; }
        @Override public void validate(ObservationIdentity after, ExactRef originalEvidence) {
            Objects.requireNonNull(after); Objects.requireNonNull(originalEvidence);
            StrictJson.require(snapshotId.equals(after.frame().snapshotId())
                    && nativeRevision.equals(after.frame().identity().nativeRevision())
                    && originalPacket.equals(originalEvidence), "push provenance differs from its actual observed frame/packet");
        }
    }
}
