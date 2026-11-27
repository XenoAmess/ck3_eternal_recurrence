package org.xar.ck3.control.application.session;

import java.io.IOException;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.HistoricalTransition;

/** Allows the real local-service SAVE fixture to exercise the package-private successor replay guard. */
public final class CommittedImportedSavedMaterialAssertions {
    private CommittedImportedSavedMaterialAssertions() { }

    public static void verify(OrdinaryCycleTransitions cycles, ContinuityStorePort.Session same,
            HistoricalTransition saved, SessionIdentity owner, CheckpointPair pair, ActionPorts.OutcomeArchive archive)
            throws IOException {
        var original = ContinuityActionJournal.receipts(saved.before(), archive).stream()
                .filter(receipt -> receipt.command().actionId().equals(pair.saveActionId())).findFirst().orElseThrow();
        cycles.withLocked(same, () -> {
            ContinuityBatchJournal.requireCommittedImportedMaterial(cycles, same, saved,
                    ContinuityJson.parseObject(saved.details(), ContinuityJson.DOCUMENT_MAX_BYTES), owner, pair, original, archive);
            return null;
        });
    }
}
