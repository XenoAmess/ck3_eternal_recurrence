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
    @FunctionalInterface public interface SeedAuthority {
        State readCompleteOriginal(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
                ExactRef completeOriginalManifest, ActionPorts.OutcomeArchive archive) throws IOException;
    }
}
