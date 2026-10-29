package org.xar.ck3.control.application.checkpoint;

import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** A physical Driver/SAVE pair. Its existence grants neither action replay nor ledger credit. */
public record CheckpointPair(FileWitness save, FileWitness driver, ObservationIdentity frame,
        String lineageId, long historyIndex, String saveActionId, ExactRef nativeAckRef, Instant observedAt) {
    public record FileWitness(ExactRef reference, FileStatIdentity identity) {
        public FileWitness {
            Objects.requireNonNull(reference); Objects.requireNonNull(identity);
            StrictJson.require(identity.bytes().longValueExact() == reference.bytes(), "exact physical file witness, including an observed empty prestate");
        }
    }
    public CheckpointPair {
        Objects.requireNonNull(save); Objects.requireNonNull(driver); Objects.requireNonNull(frame);
        StrictJson.text(lineageId); StrictJson.safe(historyIndex, 1); StrictJson.text(saveActionId);
        Objects.requireNonNull(nativeAckRef); Objects.requireNonNull(observedAt);
        StrictJson.require(save.reference().bytes() > 0 && driver.reference().bytes() > 0 && nativeAckRef.bytes() > 0
                && !save.reference().path().equals(driver.reference().path()), "positive independent physical pair and native ACK source");
    }
}
