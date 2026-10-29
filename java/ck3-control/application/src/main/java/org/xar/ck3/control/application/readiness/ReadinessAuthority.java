package org.xar.ck3.control.application.readiness;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** A current observation is usable only inside the original writer and frozen Driver callback. */
public interface ReadinessAuthority {
    record LeaseSnapshot(Complete frame, Known driver, Obj capabilities, SemanticEvidence semantic,
            Set<OperationKey> executableSteps, Set<String> bridgeCapabilities,
            ExactRef originalHello, ExactRef originalHeartbeat, Instant validUntil, Optional<ExactRef> originalSourceQualification) {
        public LeaseSnapshot(Complete frame,Known driver,Obj capabilities,SemanticEvidence semantic,
                Set<OperationKey> executableSteps,Set<String> bridgeCapabilities,ExactRef originalHello,
                ExactRef originalHeartbeat,Instant validUntil,ExactRef originalSourceQualification) {
            this(frame,driver,capabilities,semantic,executableSteps,bridgeCapabilities,originalHello,originalHeartbeat,
                    validUntil,Optional.of(originalSourceQualification));
        }
        public LeaseSnapshot {
            Objects.requireNonNull(frame); Objects.requireNonNull(driver); Objects.requireNonNull(capabilities);
            Objects.requireNonNull(semantic); Objects.requireNonNull(originalHello); Objects.requireNonNull(originalHeartbeat);
            Objects.requireNonNull(originalSourceQualification);
            Objects.requireNonNull(validUntil); executableSteps = Set.copyOf(executableSteps); bridgeCapabilities = Set.copyOf(bridgeCapabilities);
        }
    }
    @FunctionalInterface interface CheckedWork<T> { T apply(LeaseSnapshot current) throws IOException; }
    /** The original caller deadline bounds all observation I/O and the callback; it cannot be renewed by the authority. */
    <T> T current(ContinuityStorePort.Session borrowed, ObservationIdentity expected, Instant callerDeadline, CheckedWork<T> work) throws IOException;

    /** Actual physical read originals only; this data has no executable-action projection or Ready publication. */
    record PhysicalReadLease(Complete frame, Known driver, Obj capabilities, SemanticEvidence semantic,
            Set<String> bridgeCapabilities, ExactRef originalHello, ExactRef originalHeartbeat,
            Instant validUntil, Optional<ExactRef> originalSourceQualification) {
        public PhysicalReadLease(Complete frame,Known driver,Obj capabilities,SemanticEvidence semantic,
                Set<String> bridgeCapabilities,ExactRef originalHello,ExactRef originalHeartbeat,
                Instant validUntil,ExactRef originalSourceQualification) {
            this(frame,driver,capabilities,semantic,bridgeCapabilities,originalHello,originalHeartbeat,
                    validUntil,Optional.of(originalSourceQualification));
        }
        public PhysicalReadLease {
            Objects.requireNonNull(frame); Objects.requireNonNull(driver); Objects.requireNonNull(capabilities);
            Objects.requireNonNull(semantic); Objects.requireNonNull(originalHello); Objects.requireNonNull(originalHeartbeat);
            Objects.requireNonNull(validUntil); Objects.requireNonNull(originalSourceQualification);
            bridgeCapabilities = Set.copyOf(bridgeCapabilities);
        }
    }
    @FunctionalInterface interface PhysicalReadWork<T> { T apply(PhysicalReadLease current) throws IOException; }
    /** Keeps the actual received physical source alive across one registered read and both guards.
     * The original packet, observed time, source pins and same writer head remain authoritative;
     * current() or a copied before guard cannot substitute for this scope. */
    default <T> T withOriginalReadSource(ContinuityStorePort.Session borrowed, PlanningReadRequest original,
            PhysicalReadWork<T> work) throws IOException {
        throw new IOException("actual original-read physical source scope is not installed");
    }
    /** A held-only consumer cannot fall back to current(), recapture, or extend an expired world observation. */
    default <T> T currentHeldOriginal(ContinuityStorePort.Session borrowed, PlanningReadRequest original,
            PhysicalReadWork<T> work) throws IOException {
        throw new IOException("actual held original-read authority is not installed");
    }
    /** Physical source DATA for an exact reserved cleanup child; it confers no ordinary Ready or executable inventory. */
    default <T> T currentDerivedCleanup(ContinuityStorePort.Session borrowed, ObservationIdentity expected,
            Instant deadline, PhysicalReadWork<T> work) throws IOException {
        throw new IOException("actual physical derived-cleanup source is not installed");
    }
}
