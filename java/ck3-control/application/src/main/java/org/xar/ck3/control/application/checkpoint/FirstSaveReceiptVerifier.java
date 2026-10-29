package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Actual canonical SAVE originals, independent of an ordinary completed-cycle proof. */
public interface FirstSaveReceiptVerifier {
    record Original(String digest, ActionReceipt receipt, ExactRef receiptReference,
            ExactRef pairReference, DriverStateSnapshot.Complete savedDriver) {
        public Original {
            Objects.requireNonNull(receipt); Objects.requireNonNull(receiptReference);
            Objects.requireNonNull(pairReference); Objects.requireNonNull(savedDriver);
            StrictJson.require(digest != null && digest.matches("[0-9a-f]{64}"), "canonical SAVE original digest");
        }
    }
    Original verifyFirst(ContinuityStorePort.Session same, SessionIdentity owner, CheckpointPair pair,
            ObservationIdentity opening, boolean physical) throws IOException;
}
