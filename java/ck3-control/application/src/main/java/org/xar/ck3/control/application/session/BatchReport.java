package org.xar.ck3.control.application.session;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.CompositeContinuationToken;
import org.xar.ck3.control.application.action.CompositeContinuationReport;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** ACK, native application, physical paired SAVE and sole writer credit are distinct facts. */
public record BatchReport(SessionIdentity session, String batchId, Terminal terminal, String detail,
        SessionClock.Tick began, SessionClock.Tick ended, List<PhaseSpan> phases, List<Turn> turns, List<Reconciliation> reconciliations,List<LifecycleTurn> lifecycleTurns,List<ReadPublicationReconciliation> readPublicationReconciliations,
        List<RevisionReplan> revisionReplans, Optional<PlanTrace> lastPlan,Optional<TerminalReady> lastTerminalObservation,
        Optional<GameLifecycle.Observation> lastLifecycle, Optional<CheckpointPair> lastSavedPair,
        Optional<ExactRef> committedLedgerHead, long committedSavedDays, int eligibleAdvancesSinceSave,
        boolean dirtySinceSave, List<String> pendingAnalysisBatchIds, List<AnalysisCompletion> completedAnalyses,
        List<String> failedAnalysisBatchIds) {
    public enum Terminal {
        TURN_BOUND, OPERATOR_STOP, CHECKPOINT_DEFERRED, WALL_TIMEOUT, READINESS_TIMEOUT,
        INNER_EXIT, LIFECYCLE_UNAVAILABLE, OBSERVATION_UNAVAILABLE, PLANNER_STOPPED,
        INCOMPLETE_MIGRATION, ACTION_REJECTED, ACTION_UNKNOWN, CHECKPOINT_REJECTED,
        CHECKPOINT_UNKNOWN, WRITER_UNKNOWN, ANALYSIS_UNAVAILABLE, INTERNAL_FAILURE,EPISODE_HANDOFF
    }
    public enum Phase { LIFECYCLE, OBSERVATION, PLANNING, ACTION, ACTION_RECONCILIATION, OUTCOME_CONSUMPTION, CHECKPOINT, JOURNAL, IDLE_WAIT, ANALYSIS_ENQUEUE }
    public enum PhaseTerminal { RETURNED, FAILED, INTERRUPTED }
    public record PhaseSpan(Phase phase, SessionClock.Tick began, SessionClock.Tick ended, PhaseTerminal terminal) {
        public PhaseSpan {
            Objects.requireNonNull(phase); Objects.requireNonNull(began); Objects.requireNonNull(ended); Objects.requireNonNull(terminal);
            StrictJson.require(ended.elapsedNanos() >= began.elapsedNanos(), "monotonic phase time regressed");
        }
    }
    public record Turn(int index, ObservationIdentity before, PlanTrace plan, ActionReceipt receipt, TurnFacts facts) {
        public Turn {
            StrictJson.require(index > 0, "positive turn index"); Objects.requireNonNull(before); Objects.requireNonNull(plan);
            Objects.requireNonNull(receipt); Objects.requireNonNull(facts);
            StrictJson.require(receipt.command().origin() instanceof CommandOrigin.Gameplay
                    &&receipt.command().before().equals(before) && plan.before().equals(before), "turn crossed original ordinary observed frame");
            StrictJson.require(receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED || !facts.visibleGameplay(), "unconfirmed action cannot receive gameplay credit");
        }
    }
    public record Reconciliation(int index, ObservationIdentity currentFrame, PlanTrace plan, ActionReceipt originalReceipt) {
        public Reconciliation {
            StrictJson.require(index > 0, "positive original-action reconciliation index"); Objects.requireNonNull(currentFrame);
            Objects.requireNonNull(plan); Objects.requireNonNull(originalReceipt);
            StrictJson.require(originalReceipt.command().origin() instanceof CommandOrigin.Gameplay
                    &&plan.before().equals(currentFrame) && currentFrame.machineId().equals(originalReceipt.command().origin().machineId())
                    && currentFrame.game().equals(originalReceipt.command().origin().game()), "original ordinary action reconciliation crossed Game/plan frame");
        }
    }
    /** An actual finite same-parent continuation may enter a new child; it is not a read-only reconciliation. */
    public record SuccessorUiContinuation(CompositeContinuationToken.Kind kind,CompositeContinuationReport actual,
            ExactRef canonicalDomain,ExactRef actualPublishedDriver,ExactRef canonicalPublicationProof) {
        public SuccessorUiContinuation {
            Objects.requireNonNull(kind);Objects.requireNonNull(actual);
            StrictJson.require(kind==CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE||kind==CompositeContinuationToken.Kind.SUCCESSOR_UI_EVENT||kind==CompositeContinuationToken.Kind.SUCCESSOR_UI_DATE_ADVANCE,
                    "finite actual successor UI continuation kind required");
            for(ExactRef source:List.of(canonicalDomain,actualPublishedDriver,canonicalPublicationProof))
                StrictJson.require(Objects.requireNonNull(source).bytes()>0,"actual canonical continuation sources required");
        }
    }
    public record LifecycleTurn(int index,LifecycleIdentity current,ActionReceipt receipt,boolean reconciliation,
            Optional<SuccessorUiContinuation> successorUiContinuation) {
        public LifecycleTurn(int index,LifecycleIdentity current,ActionReceipt receipt,boolean reconciliation) {
            this(index,current,receipt,reconciliation,Optional.empty());
        }
        public LifecycleTurn {
            StrictJson.require(index>0,"positive terminal turn index");Objects.requireNonNull(current);Objects.requireNonNull(receipt);
            successorUiContinuation=Objects.requireNonNull(successorUiContinuation);
            if(successorUiContinuation.isPresent()) {
                var pass=successorUiContinuation.orElseThrow();
                StrictJson.require(!reconciliation&&pass.actual().parent().equals(receipt)
                        &&receipt.command().origin() instanceof CommandOrigin.LifecycleTerminal
                        &&LifecycleComposites.parentKind(receipt.command().operation()).filter(kind->kind==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR).isPresent()
                        &&receipt.command().lifecycleBefore().sameGuardFrame(current),"successor UI report changed its original terminal CONTINUE parent or borrowed read-only reconciliation");
            }else if(reconciliation&&receipt.command().origin() instanceof CommandOrigin.Gameplay original) {
                var before=original.before();StrictJson.require(before.machineId().equals(current.machineId())&&before.game().equals(current.game())
                        &&receipt.command().sessionId().equals(current.sessionId())&&before.frame().identity().player().equals(current.subject().characterId())
                        &&before.frame().episodeRunId().equals(current.subject().episodeRunId()),"terminal reconciliation crossed the original gameplay subject or owned session");
            }else {
                StrictJson.require(receipt.command().origin() instanceof CommandOrigin.LifecycleTerminal,"terminal submission requires its actual lifecycle command origin");
                LifecycleIdentity original=receipt.command().lifecycleBefore();
                StrictJson.require(reconciliation?original.sameSession(current):original.equals(current),"terminal result crossed original lifecycle source or current owned episode");
            }
        }
    }
    /** No current frame or plan is invented while the original unresolved parent prevents ordinary Ready. */
    public record ReadPublicationReconciliation(int index,ActionReceipt originalReceipt,OrdinaryPlanCompletion.Published readPublication) {
        public ReadPublicationReconciliation {
            StrictJson.require(index>0,"positive original read-publication reconciliation index");Objects.requireNonNull(originalReceipt);Objects.requireNonNull(readPublication);
            StrictJson.require(originalReceipt.command().origin().machineId().equals(readPublication.predecessor().state().machineId()),"original read-publication reconciliation crossed machine");
        }
    }
    public record RevisionReplan(PlanTrace originalPlan, GuardEvidence freshGuard, Optional<ActionReceipt> zeroDispatchReceipt) {
        public RevisionReplan { Objects.requireNonNull(originalPlan); Objects.requireNonNull(freshGuard); Objects.requireNonNull(zeroDispatchReceipt); }
    }
    public BatchReport {
        Objects.requireNonNull(session); org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.batchId(batchId);
        Objects.requireNonNull(terminal); StrictJson.text(detail); Objects.requireNonNull(began); Objects.requireNonNull(ended);
        StrictJson.require(ended.elapsedNanos() >= began.elapsedNanos(), "complete batch wall time regressed");
        phases = List.copyOf(phases); turns = List.copyOf(turns); reconciliations = List.copyOf(reconciliations);lifecycleTurns=List.copyOf(lifecycleTurns);readPublicationReconciliations=List.copyOf(readPublicationReconciliations);
        revisionReplans = List.copyOf(revisionReplans); Objects.requireNonNull(lastPlan);Objects.requireNonNull(lastTerminalObservation); Objects.requireNonNull(lastLifecycle); Objects.requireNonNull(lastSavedPair);
        Objects.requireNonNull(committedLedgerHead); StrictJson.safe(committedSavedDays, 0);
        StrictJson.require(committedSavedDays == 0 || lastSavedPair.isPresent() && committedLedgerHead.isPresent(), "saved-day credit requires actual pair and authoritative committed head");
        StrictJson.require(eligibleAdvancesSinceSave >= 0, "nonnegative unsaved advances required");
        pendingAnalysisBatchIds = List.copyOf(pendingAnalysisBatchIds); completedAnalyses = List.copyOf(completedAnalyses); failedAnalysisBatchIds = List.copyOf(failedAnalysisBatchIds);
    }
    public long fullWallNanos() { return ended.elapsedNanos() - began.elapsedNanos(); }
}
