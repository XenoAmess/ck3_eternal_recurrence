package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Only the concrete provider's lock-held callback grants a current frontend lease. */
public interface FrontendAuthority {
    <T> T current(ContinuityStorePort.Session borrowed, FrontendIdentity expected, Instant deadline, CheckedWork<T> work) throws IOException;
    /** Only the concrete issuer may borrow an already active source-bound scope. Legacy authorities never imply this qualification. */
    default <T> T currentSourceBoundRead(ContinuityStorePort.Session borrowed, FrontendIdentity expected,
            Instant deadline, CheckedWork<T> work) throws IOException {
        throw new IOException("actual source-bound frontend read continuation authority is not installed");
    }
    @FunctionalInterface interface CheckedWork<T> { T apply(LeaseSnapshot actual) throws IOException; }
    record LeaseSnapshot(FrontendIdentity identity, G2Source source, NativeActionPort.AckReceived originalRoute,
            ExactRef originalHeartbeat, Set<OperationKey> executableOperations, Set<String> bridgeCapabilities,
            Instant observedAt, Instant validUntil, List<ExactRef> supportingEvidence) {
        public LeaseSnapshot {
            Objects.requireNonNull(identity); Objects.requireNonNull(source); Objects.requireNonNull(originalRoute);
            Objects.requireNonNull(originalHeartbeat); executableOperations = Set.copyOf(executableOperations);
            bridgeCapabilities = Set.copyOf(bridgeCapabilities); Objects.requireNonNull(observedAt); Objects.requireNonNull(validUntil);
            supportingEvidence = List.copyOf(supportingEvidence);
            StrictJson.require(supportingEvidence.size() <= 16 && new java.util.HashSet<>(supportingEvidence).size() == supportingEvidence.size(), "bounded distinct actual frontend support required");
            StrictJson.require(identity.frame() instanceof FrontendFrame.Menu || !supportingEvidence.isEmpty(), "frontend snapshot needs the original Driver evidence closure");
        }
        public LeaseSnapshot(FrontendIdentity identity, G2Source source, NativeActionPort.AckReceived originalRoute,
                ExactRef originalHeartbeat, Set<OperationKey> executableOperations, Set<String> bridgeCapabilities,
                Instant observedAt, Instant validUntil) {
            this(identity, source, originalRoute, originalHeartbeat, executableOperations, bridgeCapabilities, observedAt, validUntil, List.of());
        }
    }
}
