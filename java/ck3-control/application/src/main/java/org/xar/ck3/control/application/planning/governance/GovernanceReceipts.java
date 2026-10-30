package org.xar.ck3.control.application.planning.governance;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionEffects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Consumer of the sole writer's real receipt. No ACK, cold law observation or current holder is promoted to a receipt. */
public final class GovernanceReceipts {
    private GovernanceReceipts() { }
    public enum Status { UNRESOLVED, REJECTED, WAIT_FOLLOWING_TURN, CONSUMED, WAIT_CHECKPOINT }
    public record Consumption(Status status, ActionReceipt original, String reason) {
        public Consumption { Objects.requireNonNull(status); Objects.requireNonNull(original); StrictJson.text(reason); }
    }
    public static Consumption consume(ActionReceipt receipt, PlanningRequest current, Optional<CheckpointFact> checkpoint,
            boolean opening) {
        Objects.requireNonNull(receipt);Objects.requireNonNull(current);
        StrictJson.require(receipt.command().source().equals(current.source()) && receipt.command().sessionId().equals(current.sessionId()),
                "current governance receipt consumption crossed its actual source/session");
        return consumeAtFrame(receipt,current.before(),checkpoint,opening);
    }
    /** A current physical Game consumes its applied focus on the following formal frame without requiring a SAVE. */
    public static Consumption consumeOpeningSameGame(ActionReceipt receipt, PlanningRequest current,
            Optional<CheckpointFact> checkpoint) {
        Objects.requireNonNull(receipt); Objects.requireNonNull(current); Objects.requireNonNull(checkpoint);
        StrictJson.require(receipt.command().operation().equals(GovernancePolicies.FOCUS),
                "same-Game opening consumption requires its original focus action");
        return consume(receipt, current, checkpoint, checkpoint.isPresent());
    }
    /** Archived SAVE semantics can supply the actual original formal frame after the physical Game was restored. */
    public static Consumption consumeAtFrame(ActionReceipt receipt, org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity now,
            Optional<CheckpointFact> checkpoint, boolean opening) {
        var before = receipt.command().before();
        StrictJson.require(!opening || receipt.command().operation().equals(GovernancePolicies.FOCUS),
                "opening completion requires its original focus action, never another governance receipt");
        StrictJson.require(before.machineId().equals(now.machineId()) && before.game().equals(now.game())
                && before.frame().episodeRunId().equals(now.frame().episodeRunId())
                && before.frame().identity().player().equals(now.frame().identity().player()), "receipt crossed Game/actor/episode");
        if (!receipt.settled()) return new Consumption(Status.UNRESOLVED, receipt, "existing action is unresolved; dispatch is forbidden");
        if (receipt.outcome() != ActionReceipt.Outcome.APPLIED_CONFIRMED)
            return new Consumption(Status.REJECTED, receipt, "retain the exact confirmed rejection; no applied effect inferred");
        ActionState.Settled settled = (ActionState.Settled) receipt.state();
        ActionEffects.validate(receipt.command(), settled.attempt(), settled.settlement());
        var effect = ((ActionState.Applied) settled.settlement()).observation();
        StrictJson.require(now.frame().identity().nativeRevision().compareTo(effect.after().frame().identity().nativeRevision()) >= 0
                && now.frame().identity().dateRaw().compareTo(effect.after().frame().identity().dateRaw()) >= 0,
                "current frame predates the independent effect receipt");
        if (now.frame().snapshotId().equals(effect.after().frame().snapshotId()))
            return new Consumption(Status.WAIT_FOLLOWING_TURN, receipt, "receipt is applied; a following formal turn must consume it");
        if (opening) {
            if (checkpoint.isEmpty()) return new Consumption(Status.WAIT_CHECKPOINT, receipt, "opening receipt has no qualified checkpoint fact");
            CheckpointFact fact = checkpoint.orElseThrow(); var observed = fact.observed();
            StrictJson.require(fact.actionId().equals(receipt.command().actionId()) && observed.machineId().equals(now.machineId())
                    && observed.game().equals(now.game()) && observed.frame().episodeRunId().equals(now.frame().episodeRunId())
                    && observed.frame().identity().player().equals(now.frame().identity().player())
                    && observed.frame().identity().nativeRevision().compareTo(effect.after().frame().identity().nativeRevision()) >= 0
                    && observed.frame().identity().nativeRevision().compareTo(now.frame().identity().nativeRevision()) <= 0
                    && observed.frame().identity().dateRaw().compareTo(effect.after().frame().identity().dateRaw()) >= 0
                    && observed.frame().identity().dateRaw().compareTo(now.frame().identity().dateRaw()) <= 0,
                    "opening checkpoint is not bound to the consumed action and current campaign");
        }
        return new Consumption(Status.CONSUMED, receipt, "actual independent effect reached the following formal turn");
    }
}
