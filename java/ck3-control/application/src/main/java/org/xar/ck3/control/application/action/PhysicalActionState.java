package org.xar.ck3.control.application.action;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Versioned non-pipe state. COMPLETED is presentation/source fact only; it has no Game/day/SAVE credit. */
public record PhysicalActionState(PreparedAction request, Instant submittedAt, GuardEvidence guard, Phase phase,
        Optional<PhysicalOutcome> outcome, List<ExactRef> evidence, String diagnostic) implements ActionState {
    public enum Phase { SUBMITTING, UNKNOWN, COMPLETED, NOT_POSTED }
    public PhysicalActionState {
        Objects.requireNonNull(request); Objects.requireNonNull(submittedAt); Objects.requireNonNull(guard); Objects.requireNonNull(phase);
        outcome = Objects.requireNonNull(outcome); evidence = List.copyOf(evidence); StrictJson.text(diagnostic);
        StrictJson.require(!(request instanceof PreparedAction.PipeRequest), "historical pipe actions retain their strict original Attempt contract");
        outcome.ifPresent(value -> StrictJson.require(value.requestId().equals(request.requestId()) && value.transportKind() == request.transportKind(), "physical outcome crossed prepared identity/plane"));
        StrictJson.require(phase != Phase.COMPLETED || !evidence.isEmpty(), "independent completion originals required");
        StrictJson.require(phase != Phase.SUBMITTING || outcome.isEmpty(), "SUBMITTING cannot already contain a physical return");
    }
    public boolean terminal() { return phase == Phase.COMPLETED || phase == Phase.NOT_POSTED; }
}
