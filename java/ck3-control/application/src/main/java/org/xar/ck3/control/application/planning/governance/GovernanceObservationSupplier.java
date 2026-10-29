package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory;

/** Domain I/O seam. Missing producer/state evidence is explicit, never an empty ledger or permission. */
public interface GovernanceObservationSupplier {
    Read<Durable> durable(PlanningRequest request);
    Read<Life> lifestyle(PlanningRequest request, String preferredFocus, boolean opening);
    Read<OpeningComparison> openingComparison(PlanningRequest request);
    Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position);
    Read<CouncilSelection.Query> coreCouncil(PlanningRequest request);
    Read<CouncilRoot> councilRoot(PlanningRequest request);
    Read<Crown> crown(PlanningRequest request);
    Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey);
    Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request);

    default Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) {
        return new Unavailable<>("actual private same-publication Crown query due input is not installed");
    }

    sealed interface Read<T> permits Known, Unavailable { }
    record Known<T>(T value, List<ExactRef> originals) implements Read<T> {
        public Known {
            Objects.requireNonNull(value); originals = List.copyOf(originals);
            StrictJson.require(!originals.isEmpty() && originals.stream().allMatch(ref -> ref.bytes() > 0),
                    "actual producer references required");
        }
    }
    record Unavailable<T>(String reason, Optional<CouncilTechnicalReadFailure> councilTechnicalReadFailure) implements Read<T> {
        public Unavailable { StrictJson.text(reason); Objects.requireNonNull(councilTechnicalReadFailure); }
        public Unavailable(String reason) { this(reason, Optional.empty()); }
    }
    enum DomainStatus { KNOWN_CLEAR, PENDING, UNKNOWN }
    record DomainState(DomainStatus status, Optional<ActionReceipt> latest, Optional<OpportunityJson.Obj> legacyPending, OpportunityJson.Obj originalBody) {
        public DomainState {
            Objects.requireNonNull(status); Objects.requireNonNull(latest); Objects.requireNonNull(legacyPending);
            Objects.requireNonNull(originalBody);
            StrictJson.require(status != DomainStatus.KNOWN_CLEAR || legacyPending.isEmpty()
                    && latest.filter(receipt -> !receipt.settled()).isEmpty(), "clear state contains unresolved intent");
            StrictJson.require(status != DomainStatus.PENDING || latest.isPresent() || legacyPending.isPresent(),
                    "pending state needs the retained original action");
        }
    }
    enum OpeningStage { AWAIT_SUBMIT, AWAIT_RECEIPT, AWAIT_CONSUMPTION, COMPLETE }
    /** Only the existing qualified checkpoint producer may supply this fact. It grants no save authority. */
    record CheckpointFact(String actionId, ObservationIdentity observed, ExactRef actualReceipt) {
        public CheckpointFact {
            StrictJson.text(actionId); Objects.requireNonNull(observed); Objects.requireNonNull(actualReceipt);
            StrictJson.require(actualReceipt.bytes() > 0, "actual checkpoint receipt required");
        }
    }
    record OpeningGate(String episodeRunId, BigInteger dateRaw, OpeningStage stage,
            Optional<ActionReceipt> action, Optional<CheckpointFact> checkpoint) {
        public OpeningGate {
            StrictJson.text(episodeRunId); Objects.requireNonNull(dateRaw); Objects.requireNonNull(stage);
            Objects.requireNonNull(action); Objects.requireNonNull(checkpoint);
            StrictJson.require(stage == OpeningStage.AWAIT_SUBMIT || stage == OpeningStage.COMPLETE || action.isPresent(),
                    "opening continuation requires its original action receipt");
        }
    }
    /** Read under the sole continuity store lock; the domain adapters never publish it. */
    record Durable(ObservationIdentity observed, String sessionId, Optional<CadenceModels.State> cadence,
            Optional<OpeningGate> opening, Optional<DomainState> council, Optional<DomainState> crown) {
        public Durable {
            Objects.requireNonNull(observed); StrictJson.text(sessionId); Objects.requireNonNull(cadence);
            Objects.requireNonNull(opening); Objects.requireNonNull(council); Objects.requireNonNull(crown);
        }
        public void bind(PlanningRequest request) {
            StrictJson.require(observed.equals(request.before()) && sessionId.equals(request.sessionId()),
                    "durable state crossed the current Game/session/frame");
            cadence.ifPresent(state -> StrictJson.require(state.episodeRunId().equals(request.before().frame().episodeRunId()),
                    "cadence state must be reduced for the current episode by its producer"));
        }
    }
    record Life(LifestyleConsumer.Request input, LifestyleHistory.Input history, OpportunityJson.Obj originalQuery) {
        public Life { Objects.requireNonNull(input); Objects.requireNonNull(history); Objects.requireNonNull(originalQuery); }
    }
    record OpeningComparison(LifestyleMinPolicy.FirstFocusRequest input, OpportunityJson.Obj originalEvidence) {
        public OpeningComparison { Objects.requireNonNull(input); Objects.requireNonNull(originalEvidence); }
    }
    record Crown(CrownAuthorityPolicy.Readback readback, OpportunityJson.Obj originalReadback) {
        public Crown { Objects.requireNonNull(readback); Objects.requireNonNull(originalReadback); }
    }
    record Seat(CouncilSelection.Position position, Optional<BigInteger> incumbent) {
        public Seat { Objects.requireNonNull(position); Objects.requireNonNull(incumbent); }
    }
    record CouncilRoot(List<Seat> seats, OpportunityJson.Obj original) {
        public CouncilRoot { seats = List.copyOf(seats); Objects.requireNonNull(original); }
    }
}
