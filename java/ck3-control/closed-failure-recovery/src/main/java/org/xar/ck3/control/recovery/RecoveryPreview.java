package org.xar.ck3.control.recovery;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Every branch is read-only and grants no Game, RPC, SAVE or attachment authority. */
public sealed interface RecoveryPreview permits RecoveryPreview.Candidate, RecoveryPreview.Unavailable, RecoveryPreview.Rejected {
    default boolean ready() { return false; }
    default long ordinaryCycleCredit() { return 0; }
    default long gameDayCredit() { return 0; }
    default boolean originalActionsReplayed() { return false; }

    record Unavailable(String reason) implements RecoveryPreview {
        public Unavailable { StrictJson.text(reason); }
    }
    record Rejected(String reason) implements RecoveryPreview {
        public Rejected { StrictJson.text(reason); }
    }
    final class Candidate implements RecoveryPreview {
        private final String inputDigest;
        private final String predecessorDigest;
        private final String eventIdentity;
        private final String sourceKey;
        private final long expectedSequence;
        private final byte[] details;
        private final byte[] reducedState;
        private final byte[] committedState;

        Candidate(String inputDigest, String predecessorDigest, String eventIdentity, String sourceKey,
                long expectedSequence, byte[] details, byte[] reducedState, byte[] committedState) {
            this.inputDigest = Objects.requireNonNull(inputDigest);
            this.predecessorDigest = Objects.requireNonNull(predecessorDigest);
            this.eventIdentity = Objects.requireNonNull(eventIdentity);
            this.sourceKey = Objects.requireNonNull(sourceKey);
            this.expectedSequence = StrictJson.safe(expectedSequence, 1);
            this.details = details.clone(); this.reducedState = reducedState.clone();
            this.committedState = committedState.clone();
        }
        public String kind() { return "repair_required"; }
        public String status() { return "CANDIDATE_REQUIRES_ORIGINAL_WRITER_REVALIDATION"; }
        public String inputDigest() { return inputDigest; }
        public String predecessorDigest() { return predecessorDigest; }
        public String eventIdentity() { return eventIdentity; }
        public String sourceKey() { return sourceKey; }
        public long expectedSequence() { return expectedSequence; }
        public byte[] details() { return details.clone(); }
        public byte[] reducedState() { return reducedState.clone(); }
        public byte[] committedState() { return committedState.clone(); }
    }
}
