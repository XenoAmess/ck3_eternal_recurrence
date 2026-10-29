package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Zero-day interruption evidence. The semantic packet is a real frame, never a fabricated query ACK. */
public record CompositeControlObservation(PlanningReadReceipt terminalStatus,
        List<PlanningReadReceipt> supportingReads, ActionState.EffectObservation semantic) {
    public CompositeControlObservation {
        Objects.requireNonNull(terminalStatus); Objects.requireNonNull(semantic);
        supportingReads = List.copyOf(supportingReads);
        StrictJson.require(!supportingReads.isEmpty(), "retained independent child-control read is required");
    }
}
