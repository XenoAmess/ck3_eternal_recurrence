package org.xar.ck3.control.application.action.council;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

public final class CouncilContinuationPorts {
    private CouncilContinuationPorts() { }
    public interface NativePort {
        NativeActionPort.DispatchOutcome submit(CouncilContinuationPermit permit, NativeRequest exactRequest, Instant deadline) throws IOException, InterruptedException;
        /** Existing original request only; this method must never send or create a new native request. */
        Optional<NativeActionPort.AckReceived> collectOriginalOutcome(String requestId, Instant deadline) throws IOException, InterruptedException;
    }
    /** Fresh source/SEM custody of an already submitted original action; it must not grant a new ordinary action. */
    @FunctionalInterface public interface GuardPort {
        GuardEvidence current(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt originalParent,
                Instant deadline) throws IOException;
    }
    /** Root installs the sole source-bound Council policy, not a boolean supplied by an action caller. */
    public interface Policy {
        List<ExactRef> prepareEvidence(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
                Stage stage, List<Retained> prior, ActionPorts.OutcomeArchive archive) throws IOException;
        void verifyIssue(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
                List<Retained> prior, Request next, ActionPorts.OutcomeArchive archive) throws IOException;
        void verifyOutcome(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
                List<Retained> prior, Entry next, NativeActionPort.DispatchOutcome original, ActionPorts.OutcomeArchive archive) throws IOException;
    }
    /** Same actual held occurrence only; this DATA record never issues a permission. */
    public record RecoveredObservation(GuardEvidence guard,ObservationProvenance provenance) {
        public RecoveredObservation {
            java.util.Objects.requireNonNull(guard);java.util.Objects.requireNonNull(provenance);
            org.xar.ck3.control.contracts.StrictJson.require(guard.origin() instanceof CommandOrigin.Reconciliation,
                    "actual dedicated recovered observation guard required");
            provenance.validate(guard.origin().requireReconciliation().factual(),guard.nativeEvidence());
        }
    }
    /** Bound once by the actual Root source; decoded DATA cannot implement an issued permission. */
    public interface RecoveryAuthority {
        GuardEvidence currentRecovered(ContinuityStorePort.Session same, WriterContracts.Head head,
                ActionReceipt originalParent, Instant deadline) throws IOException;
        default GuardEvidence observationRecovered(ContinuityStorePort.Session same,
                CouncilContinuationCoordinator.RecoveryOriginal original,Instant deadline) throws IOException {
            throw new IOException("actual recovered Council observation source is not installed");
        }
        default RecoveredObservation captureRecoveredObservation(ContinuityStorePort.Session same,
                CouncilContinuationCoordinator.RecoveryOriginal original,Instant deadline) throws IOException {
            throw new IOException("actual recovered Council observation/provenance source is not installed");
        }
        ActionPorts.PostconditionResult observeRecovered(ContinuityStorePort.Session same,
                ActionReceipt originalParent, ActionState.Attempt originalAttempt,
                NativeActionPort.AckReceived originalAck, Instant deadline) throws IOException, InterruptedException;
    }
    @FunctionalInterface public interface SeedAuthority {
        State readCompleteOriginal(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
                ExactRef completeOriginalManifest, ActionPorts.OutcomeArchive archive) throws IOException;
    }
}
