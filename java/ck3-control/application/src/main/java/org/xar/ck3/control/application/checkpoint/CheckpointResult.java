package org.xar.ck3.control.application.checkpoint;

import java.math.BigDecimal;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;

public sealed interface CheckpointResult permits CheckpointResult.Confirmed, CheckpointResult.Rejected, CheckpointResult.Unknown {
    record Confirmed(CheckpointPair pair, ExactRef ackEvidence, ObservationIdentity poststate, BigDecimal advancedDays, ActionReceipt action, SeedAdoption seedAdoption) implements CheckpointResult {
        public Confirmed { Objects.requireNonNull(pair); Objects.requireNonNull(ackEvidence); Objects.requireNonNull(poststate); Objects.requireNonNull(advancedDays); Objects.requireNonNull(action); Objects.requireNonNull(seedAdoption);
            if (action.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED || advancedDays.signum() < 0) throw new IllegalArgumentException("confirmed physical SAVE requires independently settled action"); }
    }
    record Rejected(String actionId, String reason, ActionReceipt action) implements CheckpointResult {
        public Rejected { Objects.requireNonNull(action); Objects.requireNonNull(actionId); Objects.requireNonNull(reason); }
    }
    record Unknown(String actionId, String reason, Optional<ActionReceipt> action) implements CheckpointResult {
        public Unknown { Objects.requireNonNull(actionId); Objects.requireNonNull(reason); action = Objects.requireNonNull(action); }
    }
}
