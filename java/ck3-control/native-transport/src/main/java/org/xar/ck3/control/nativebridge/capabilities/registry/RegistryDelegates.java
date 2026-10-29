package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.planning.OrdinaryPlanner;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Public facades bind the real authorities. They contain no planner, loop, ledger or lifecycle implementation. */
public final class RegistryDelegates {
    public record Save(ObservationIdentity before, G2Source source, String sessionId,
            Optional<CheckpointPair> baseline, Instant deadline) {
        public Save {
            Objects.requireNonNull(before); Objects.requireNonNull(source); Objects.requireNonNull(baseline); Objects.requireNonNull(deadline);
            RegistryJson.require(sessionId != null && !sessionId.isEmpty(), "real session identity required");
        }
    }
    private final OrdinaryPlanner planner;
    private final ActionCoordinatorPort actions;
    private final CheckpointRequestFactory checkpointRequests;
    private final CheckpointService checkpoints;
    private final RestoreCheckpointService restore;
    private final SessionController session;
    public RegistryDelegates(OrdinaryPlanner planner, ActionCoordinatorPort actions, CheckpointRequestFactory checkpointRequests,
            CheckpointService checkpoints, RestoreCheckpointService restore, SessionController session) {
        this.planner = Objects.requireNonNull(planner, "actual ordinary planner required");
        this.actions = Objects.requireNonNull(actions, "sole actual action authority required");
        this.checkpointRequests = Objects.requireNonNull(checkpointRequests, "actual readiness producer required");
        this.checkpoints = Objects.requireNonNull(checkpoints, "actual checkpoint service required");
        this.restore = Objects.requireNonNull(restore, "actual restore lifecycle/reducer service required");
        this.session = Objects.requireNonNull(session, "sole actual ordinary session required");
    }
    public PlanningResult plan_turn(PlanningRequest request) { return planner.plan(Objects.requireNonNull(request)); }
    public SessionController.TurnReport auto_turn(Instant deadline) { return session.autoTurn(Objects.requireNonNull(deadline)); }
    /** Typed ActionCommand must already name a registered command origin and expected independent postcondition. */
    public ActionReceipt execute_step(ActionCommand command) { return actions.execute(Objects.requireNonNull(command)); }
    public CheckpointResult save_checkpoint(Save request) throws InterruptedException {
        Objects.requireNonNull(request);
        return checkpoints.checkpoint(checkpointRequests.prepare(request.before(),request.source(),request.sessionId(),request.baseline(),request.deadline()));
    }
    public RestoreCheckpointService.Result restore_checkpoint(RestoreCheckpointService.Request request) throws InterruptedException {
        return restore.restore(Objects.requireNonNull(request));
    }
}

