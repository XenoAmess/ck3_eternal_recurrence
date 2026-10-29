package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Actual same-Game successor adapter. Seed-next Game replacement remains at Root's real factory. */
public final class OrdinaryEpisodeContinuation implements EpisodeContinuation {
    private final ContinuityBatchJournal journal;
    private final LifecycleEpisodeInputs inputs;
    private final PostLifecycleSemanticCapture capture;
    public OrdinaryEpisodeContinuation(ContinuityBatchJournal actualJournal,LifecycleEpisodeInputs actualInputs,PostLifecycleSemanticCapture actualNoQueryCapture) {
        journal=Objects.requireNonNull(actualJournal);inputs=Objects.requireNonNull(actualInputs);
        capture=Objects.requireNonNull(actualNoQueryCapture);
    }
    @Override public CompletedCycleProof continueSameGame(SessionIdentity owner,ActionReceipt receipt,Instant deadline) throws IOException {
        return continueAdmittedSameGame(owner,receipt,deadline).proof();
    }
    @Override public ContinuityBatchJournal.AdmittedEpisode continueAdmittedSameGame(SessionIdentity owner,ActionReceipt receipt,Instant deadline)throws IOException {
        var admitted=journal.admitEpisode(inputs,owner,receipt,capture,deadline);
        journal.requireHistoricalEpisodeAdoption(admitted);return admitted;
    }
    public CompletedCycleProof continueSameGame(ContinuityStorePort.Session borrowed,SessionIdentity owner,
            ActionReceipt receipt,Instant deadline)throws IOException {
        return continueAdmittedSameGame(borrowed,owner,receipt,deadline).proof();
    }
    /** The same actual continuation borrows Core's original session and retains its private journal evidence. */
    public ContinuityBatchJournal.AdmittedEpisode continueAdmittedSameGame(ContinuityStorePort.Session borrowed,SessionIdentity owner,
            ActionReceipt receipt,Instant deadline)throws IOException {
        var admitted=journal.admitEpisode(borrowed,inputs,owner,receipt,capture,deadline);
        journal.requireHistoricalEpisodeAdoption(borrowed,admitted);return admitted;
    }
}
