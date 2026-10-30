package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.util.Arrays;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture.Captured;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionEffects;
import org.xar.ck3.control.application.action.CompositeContinuationReport;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition;
import org.xar.ck3.control.application.action.PreSubmissionRevisionMismatchException;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.planning.OrdinaryPlanner;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.RetainedIncidentBatchSource;
import static org.xar.ck3.control.application.session.BatchReport.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/**
 * One persistent ordinary loop. It never launches a JVM/Game, implements a strategy,
 * dispatches a native primitive, writes a ledger file, restores, or repeats UNKNOWN.
 */
public final class SessionController {
    private final SessionIdentity identity;
    private final LifecyclePort lifecycle;
    private final ObservationPort observations;
    private final OrdinaryPlanner planner;
    private final ActionCoordinatorPort actions;
    private final CheckpointService checkpoints;
    private final CheckpointRequestFactory checkpointRequests;
    private final BatchJournal journal;
    private final OfflineAnalysisPort analyses;
    private final AtomicReference<RetainedIncidentBatchSource> retainedIncidents = new AtomicReference<>();
    private final SessionClock clock;
    private final OrdinaryPlanCompletion completion;
    private final OrdinaryPlanCompletion.PlanningScope planningScope;
    private final EpisodeContinuation episodes;
    private final AtomicBoolean running = new AtomicBoolean();
    private final AtomicBoolean stopRequested = new AtomicBoolean();
    private final Set<String> usedBatches = new HashSet<>();
    private final Set<String> unsavedGameplayActions = new HashSet<>();
    private final LinkedHashMap<String, AnalysisTicket> pendingAnalyses = new LinkedHashMap<>();
    /** Original capture references survive a failed enqueue until the real port accepts their identical work. */
    private final LinkedHashMap<String, BatchRequest> retainedAnalysisInputs = new LinkedHashMap<>();
    private final List<AnalysisCompletion> completedAnalyses = new ArrayList<>();
    private final Set<String> completedAnalysisIds = new HashSet<>();
    private final List<String> failedAnalyses = new ArrayList<>();
    private Optional<CheckpointPair> savedPair;
    private Optional<ExactRef> ledgerHead = Optional.empty();
    private int eligibleSinceSave;
    private boolean dirty;
    private volatile boolean quarantined;
    private volatile boolean localUnresolved;
    private Optional<ActionCommand> publicCheckpointUnknown=Optional.empty();
    private Optional<ActionCommand> adoptedPublicCheckpoint=Optional.empty();
    /** Only this Controller can mint a deferral from its exact private captured in-flight SAVE. */
    private static final class CapturedCheckpointDeferred extends RuntimeException {
        private static final long serialVersionUID=1L;
        // In-process control transfer only; captured SAVE authority is never Java-serialized.
        final transient Captured actual;
        private CapturedCheckpointDeferred(Captured actual,Throwable failure){super("original SAVE is captured; Controller adoption remains pending",failure);this.actual=actual;}
    }
    private static final class CheckpointInvocation {
        final ActionCommand original;Captured adopted;
        CheckpointInvocation(ActionCommand original){this.original=original;}
    }
    private final ThreadLocal<CheckpointInvocation> checkpointInvocation=new ThreadLocal<>();
    private volatile boolean retired;
    private long totalCommittedDays;
    private volatile Optional<NaturalEpisodeAdoption> naturalAdoption=Optional.empty();
    private Optional<ContinuityBatchJournal.ReboundTransport> transportAdoption=Optional.empty();
    /** Minted only after this actual Controller consumed its original journal's private admission. */
    public static final class NaturalEpisodeAdoption {
        private final SessionIdentity owner;
        private final ActionReceipt parent;
        private final ContinuityBatchJournal.AdmittedEpisode admission;
        private NaturalEpisodeAdoption(SessionIdentity owner,ActionReceipt parent,ContinuityBatchJournal.AdmittedEpisode admission) {
            this.owner=owner;this.parent=parent;this.admission=admission;
        }
        public SessionIdentity owner(){return owner;}
        public ActionReceipt parent(){return parent;}
        public ContinuityBatchJournal.AdmittedEpisode admission(){return admission;}
    }
    /** Source-owned acceptance knowledge. The caller must also ask the identical journal to replay its historical evidence. */
    public Optional<NaturalEpisodeAdoption> naturalEpisodeAdoption(ActionReceipt exactParent) {
        Objects.requireNonNull(exactParent);
        return naturalAdoption.filter(value->sameNaturalParent(value.parent,exactParent));
    }
    private static boolean sameNaturalParent(ActionReceipt original,ActionReceipt actual) {
        if(!sameCommand(original.command(),actual.command()))return false;
        var left=lifecycleProof(original);var right=lifecycleProof(actual);
        return left.isPresent()&&right.isPresent()&&left.orElseThrow().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR
                &&Arrays.equals(LifecycleProofCodec.encode(left.orElseThrow()),LifecycleProofCodec.encode(right.orElseThrow()));
    }
    /** Idle adoption of this identical Journal's canonical owner transfer. It clears no dirty/UNKNOWN state or saved credit. */
    public void adoptTransportRebound(ContinuityBatchJournal.ReboundTransport actual)throws IOException {
        adoptTransportRebound(Optional.empty(),actual);
    }
    /** Root construction may retain its existing writer transaction without nesting another OS lock. */
    public void adoptTransportRebound(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ContinuityBatchJournal.ReboundTransport actual)throws IOException {
        adoptTransportRebound(Optional.of(Objects.requireNonNull(same)),actual);
    }
    private void adoptTransportRebound(Optional<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> borrowed,
            ContinuityBatchJournal.ReboundTransport actual)throws IOException {
        Objects.requireNonNull(actual);StrictJson.require(running.compareAndSet(false,true),"transport adoption cannot replace an active Controller turn");
        try {
            StrictJson.require(!retired&&identity.equals(actual.owner())&&journal instanceof ContinuityBatchJournal,
                    "transport adoption needs the actual new-owner Controller and original Journal");
            var actualJournal=(ContinuityBatchJournal)journal;
            if(borrowed.isPresent())actualJournal.requireHistoricalTransport(borrowed.orElseThrow(),actual);
            else actualJournal.requireHistoricalTransport(actual);
            boolean needsSave=actual.checkpointRequired()||savedPair.isEmpty()
                    ||actual.savedFrontier().filter(pair->savedPair.filter(pair::equals).isPresent()).isEmpty();
            dirty|=needsSave;transportAdoption=Optional.of(actual);
        }finally{running.set(false);}
    }
    /** Finalized cold metadata may publish actual private current admission without replaying the old parent or another AUTO turn. */
    public void adoptTransportedEpisode(ContinuityBatchJournal.ReboundTransport transport,ActionReceipt exactParent,
            ContinuityBatchJournal.AdmittedEpisode admitted)throws IOException {
        adoptTransportedEpisode(Optional.empty(),transport,exactParent,admitted);
    }
    public void adoptTransportedEpisode(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ContinuityBatchJournal.ReboundTransport transport,ActionReceipt exactParent,
            ContinuityBatchJournal.AdmittedEpisode admitted)throws IOException {
        adoptTransportedEpisode(Optional.of(Objects.requireNonNull(same)),transport,exactParent,admitted);
    }
    private void adoptTransportedEpisode(Optional<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> borrowed,
            ContinuityBatchJournal.ReboundTransport transport,ActionReceipt exactParent,
            ContinuityBatchJournal.AdmittedEpisode admitted)throws IOException {
        Objects.requireNonNull(transport);Objects.requireNonNull(exactParent);Objects.requireNonNull(admitted);
        StrictJson.require(running.compareAndSet(false,true),"transported episode adoption cannot replace an active Controller turn");
        try {
            StrictJson.require(!retired&&identity.equals(transport.owner())&&journal instanceof ContinuityBatchJournal
                    &&sameCommand(transport.parent(),exactParent.command()),"transported final admission changed its actual owner or original parent");
            var actualJournal=(ContinuityBatchJournal)journal;
            if(borrowed.isPresent()) {
                actualJournal.requireHistoricalTransport(borrowed.orElseThrow(),transport);
                actualJournal.requireHistoricalEpisodeAdoption(borrowed.orElseThrow(),admitted);
            }else {actualJournal.requireHistoricalTransport(transport);actualJournal.requireHistoricalEpisodeAdoption(admitted);}
            transportAdoption=Optional.of(transport);
            acceptNaturalEpisode(exactParent,admitted);
        }finally{running.set(false);}
    }
    private void acceptNaturalEpisode(ActionReceipt receipt,ContinuityBatchJournal.AdmittedEpisode admitted) {
        var proof=admitted.proof();
        StrictJson.require(admitted.owner().equals(identity)&&sameNaturalParent(admitted.parent(),receipt)
                &&proof.frame().machineId().equals(identity.machineId())&&proof.frame().game().equals(identity.game()),
                "actual episode admission returned another parent or physical successor owner");
        boolean needsSave=admitted.newBinding()||admitted.checkpointRequired()||savedPair.isEmpty()
                ||admitted.savedFrontier().filter(pair->savedPair.filter(pair::equals).isPresent()).isEmpty()
                ||savedPair.filter(pair->pair.frame().frame().identity().player().equals(proof.frame().frame().identity().player())
                &&pair.frame().frame().episodeRunId().equals(proof.frame().frame().episodeRunId())).isEmpty();
        dirty|=needsSave;naturalAdoption=Optional.of(new NaturalEpisodeAdoption(identity,receipt,admitted));
        if(transportAdoption.filter(transport->sameCommand(transport.parent(),receipt.command())).isPresent())transportAdoption=Optional.empty();
    }
    private volatile Optional<BatchReport> lastReport = Optional.empty();
    /** Actual ordinary observations retained for one completed batch; no new observation or action is requested. */
    public record BatchBoundary(String batchId, SessionIdentity session,
            Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> firstObservation,
            Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> lastObservation,
            int observationCount, boolean observedDateChanged, boolean pendingAction) {
        public BatchBoundary {
            Objects.requireNonNull(batchId); Objects.requireNonNull(session);
            Objects.requireNonNull(firstObservation); Objects.requireNonNull(lastObservation);
            StrictJson.require(observationCount >= 0, "nonnegative actual observation count required");
        }
    }
    private volatile Optional<BatchBoundary> lastBatchBoundary = Optional.empty();
    private Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> latestProgressObservation = Optional.empty();
    public Optional<BatchBoundary> lastBatchBoundary() {
        return running.get() ? Optional.empty() : lastBatchBoundary;
    }
    private volatile org.xar.ck3.control.application.presentation.DecisionDisplay decisionDisplay;
    /** Audience-only port; the original Controller and coordinator retain all execution authority. */
    public synchronized void bindDecisionDisplay(org.xar.ck3.control.application.presentation.DecisionDisplay actual) {
        StrictJson.require(decisionDisplay == null && !running.get() && usedBatches.isEmpty() && lastReport.isEmpty(),
                "decision display binds once before the original Controller is used");
        decisionDisplay = Objects.requireNonNull(actual);
    }
    private volatile Optional<BatchLimits> lastLimits = Optional.empty();
    private record PendingReadParent(String actionId,OrdinaryPlanCompletion.Published publication) { }
    private Optional<PendingReadParent> pendingReadParent=Optional.empty();
    private record TerminalConstraint(LifecycleExpectedPostcondition.Operation operation,Optional<BigInteger> expectedRevision) {
        TerminalConstraint {
            Objects.requireNonNull(operation);Objects.requireNonNull(expectedRevision);
            StrictJson.require(operation!=LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL,
                    "a private lifecycle child is not a public terminal turn");
            expectedRevision.ifPresent(value->StrictJson.require(value.signum()>=0&&value.compareTo(StrictJson.UINT64_MAX)<=0,
                    "exact unsigned public lifecycle revision required"));
        }
    }

    public SessionController(SessionIdentity identity, LifecyclePort lifecycle, ObservationPort observations,
            OrdinaryPlanner planner, ActionCoordinatorPort actions, CheckpointService checkpoints,
            CheckpointRequestFactory checkpointRequests, BatchJournal journal, OfflineAnalysisPort analyses,
            SessionClock clock, Optional<CheckpointPair> admittedBaseline, long admittedCommittedSavedDays,
            OrdinaryPlanCompletion completion,EpisodeContinuation actualEpisodes) {
        this.identity = Objects.requireNonNull(identity); this.lifecycle = Objects.requireNonNull(lifecycle);
        this.observations = Objects.requireNonNull(observations); this.planner = Objects.requireNonNull(planner);
        this.actions = Objects.requireNonNull(actions); this.checkpoints = Objects.requireNonNull(checkpoints);
        this.checkpointRequests = Objects.requireNonNull(checkpointRequests); this.journal = Objects.requireNonNull(journal);
        this.analyses = Objects.requireNonNull(analyses); this.clock = Objects.requireNonNull(clock);
        this.completion = Objects.requireNonNull(completion);
        StrictJson.require(completion instanceof OrdinaryPlanCompletion.PlanningScope,"the actual original-writer planning scope is required");
        this.planningScope=(OrdinaryPlanCompletion.PlanningScope)completion;
        this.episodes=Objects.requireNonNull(actualEpisodes);
        savedPair = Objects.requireNonNull(admittedBaseline);
        savedPair.ifPresent(pair -> StrictJson.require(pair.frame().machineId().equals(identity.machineId()), "baseline belongs to another machine"));
        StrictJson.safe(admittedCommittedSavedDays, 0); totalCommittedDays = admittedCommittedSavedDays;
        StrictJson.require(admittedCommittedSavedDays == 0 || admittedBaseline.isPresent(), "nonzero admitted saved frontier requires its actual paired baseline");
    }
    public SessionIdentity identity() { return identity; }
    private org.xar.ck3.control.application.driver.DriverStateAssembler restartDriver;
    /** Construction-only binding to the identical complete Driver producer owned by this Root session. */
    public void bindRestartDriver(org.xar.ck3.control.application.driver.DriverStateAssembler actual){
        Objects.requireNonNull(actual);StrictJson.require(restartDriver==null&&!running.get()&&usedBatches.isEmpty()&&lastReport.isEmpty(),"restart Driver is bound once before execution");restartDriver=actual;
    }
    static final class CapturedRestart {
        private final SessionController issuer;private final ControllerRestartState state;
        private CapturedRestart(SessionController issuer,ControllerRestartState state){this.issuer=issuer;this.state=state;}
        ControllerRestartState state(){return state;}
        void requireJournal(ContinuityBatchJournal actual){StrictJson.require(issuer.journal==actual&&issuer.running.get(),"actual idle Controller capture scope required");}
    }
    /** Joins already submitted analysis futures before taking the writer lock. Failure retains the real backlog. */
    public void drainForCleanRestart(Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(deadline);StrictJson.require(running.compareAndSet(false,true),"clean restart requires an idle Controller");
        try {
            requireCleanRestartIdle();
            for(var ticket:List.copyOf(pendingAnalyses.values())) {
                long nanos=java.time.Duration.between(clock.now().utc(),deadline).toNanos();
                if(nanos<=0)throw new IOException("offline analysis drain exceeded its actual restart deadline");
                try {ticket.completion().toCompletableFuture().get(nanos,java.util.concurrent.TimeUnit.NANOSECONDS);}
                catch(java.util.concurrent.TimeoutException failure){throw new IOException("offline analysis remains pending at clean restart",failure);}
                catch(java.util.concurrent.ExecutionException failure){throw new IOException("offline analysis failed before clean restart",failure);}
            }
            reapAnalyses();
            StrictJson.require(pendingAnalyses.isEmpty()&&retainedAnalysisInputs.isEmpty()&&failedAnalyses.isEmpty()
                    &&lastReport.map(report->report.failedAnalysisBatchIds().isEmpty()).orElse(true),"clean restart requires the actual offline queue to drain successfully");
        } finally {running.set(false);}
    }
    /** Captures dirty and unsaved state without requesting SAVE, advancing a day or retrying an action. */
    public ContinuityBatchJournal.CleanRestartTicket captureCleanRestart(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            String batchPrefix,long nextSequence)throws IOException {
        StrictJson.require(running.compareAndSet(false,true),"clean restart requires an idle Controller");
        try {
            requireCleanRestartIdle();StrictJson.require(journal instanceof ContinuityBatchJournal&&restartDriver!=null,"actual canonical restart producers are required");
            StrictJson.require(pendingAnalyses.isEmpty()&&retainedAnalysisInputs.isEmpty()&&failedAnalyses.isEmpty(),"offline work must actually drain before capture");
            var state=new ControllerRestartState(identity,batchPrefix,nextSequence,usedBatches,unsavedGameplayActions,savedPair,ledgerHead,
                    eligibleSinceSave,dirty,quarantined,localUnresolved,totalCommittedDays,completedAnalysisIds,stopRequested.get());
            var known=restartDriver.withFrozenFacts(same,frozen->{
                StrictJson.require(frozen.activeActionId().isEmpty()&&frozen.actions().actions().stream().allMatch(ActionReceipt::settled)
                        &&frozen.state() instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known,"active or unresolved Driver/action cannot restart");
                return (org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known)frozen.state();
            });
            // Leave the immutable Driver read scope before the actual metadata commit; the same writer lock remains held.
            return ((ContinuityBatchJournal)journal).captureCleanRestart(same,new CapturedRestart(this,state),known);
        } finally {running.set(false);}
    }
    /** Only the new actual Root owner can consume the original writer's private canonical admission. */
    public void restoreCleanRestart(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ContinuityBatchJournal.CleanRestartAdmission actual)throws IOException {
        StrictJson.require(running.compareAndSet(false,true),"restart restoration requires an idle Controller");
        try {
            StrictJson.require(journal instanceof ContinuityBatchJournal&&usedBatches.isEmpty()&&lastReport.isEmpty()&&!retired,
                    "restart cannot overwrite an executed Controller");
            ((ContinuityBatchJournal)journal).requireRestartAdmission(same,actual,identity);
            restoreCapturedController(same,actual.controller());
        } finally {running.set(false);}
    }
    /** Preserve all proven consumed initial batches without reconstructing or clearing any runtime queue. */
    public void restoreInitialNoDispatchRecovery(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ContinuityBatchJournal.InitialNoDispatchRecovery actual)throws IOException {
        StrictJson.require(running.compareAndSet(false,true),"initial interruption recovery requires an idle Controller");
        try {
            var captured=Objects.requireNonNull(actual).capturedController();
            StrictJson.require(journal instanceof ContinuityBatchJournal&&!retired&&usedBatches.isEmpty()&&lastReport.isEmpty()
                    &&(captured.isPresent()||unsavedGameplayActions.isEmpty()&&savedPair.isEmpty()&&eligibleSinceSave==0&&!dirty&&totalCommittedDays==0),
                    "initial interruption cannot overwrite an executed or saved Controller");
            requireCleanRestartIdle();
            ((ContinuityBatchJournal)journal).requireInitialNoDispatchRecovery(same,actual,identity);
            if(captured.isPresent())restoreCapturedController(same,captured.orElseThrow());
            usedBatches.addAll(actual.consumedBatchIds());
            ledgerHead=Optional.of(same.persistedHead());
            // Existing incident inputs, futures, completions and stop state remain owned by this actual instance.
        } finally {running.set(false);}
    }


    public void restoreUnresolvedSameGame(ContinuityStorePort.Session same, ContinuityBatchJournal.UnresolvedSameGameData data) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(data);
        StrictJson.require(running.compareAndSet(false, true), "unresolved same-game recovery requires an idle Controller");
        try {
            StrictJson.require(!retired && usedBatches.isEmpty() && lastReport.isEmpty(), "unresolved recovery cannot overwrite an executed Controller");
            StrictJson.require(journal instanceof ContinuityBatchJournal, "unresolved recovery requires the actual ContinuityBatchJournal");
            StrictJson.require(identity.equals(data.capturedController().owner()), "unresolved recovery crossed the actual owner");
            StrictJson.require(data.canonicalSequence() == same.head().state().sequence() && data.canonicalHeadDigest().equals(same.head().digest()), "unresolved recovery crossed the actual current journal state");
            StrictJson.require(!data.unresolvedActions().isEmpty(), "unresolved recovery requires at least one original unresolved action");
            for (var action : data.unresolvedActions()) {
                StrictJson.require(action.command().sessionId().equals(identity.sessionId()) && action.command().origin().game().equals(identity.game()) && action.command().origin().machineId().equals(identity.machineId()), "unresolved action crossed the actual owner");
            }
            restoreCapturedController(same, data.capturedController());
            usedBatches.addAll(data.usedBatches());
            ledgerHead = Optional.of(same.persistedHead());
            quarantined = true;
            localUnresolved = true;
        } finally { running.set(false); }
    }

    /** Restore settled dirty gameplay after an ordinary interruption without SAVE or action dispatch. */
    public void restoreSettledSameGame(ContinuityStorePort.Session same,
            ContinuityBatchJournal.SettledSameGameData data) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(data);
        StrictJson.require(running.compareAndSet(false, true), "settled same-game recovery requires an idle Controller");
        try {
            StrictJson.require(!retired && usedBatches.isEmpty() && lastReport.isEmpty()
                    && unsavedGameplayActions.isEmpty() && pendingReadParent.isEmpty() && publicCheckpointUnknown.isEmpty()
                    && !dirty && !quarantined && !localUnresolved,
                    "settled recovery cannot overwrite an executed Controller");
            StrictJson.require(journal instanceof ContinuityBatchJournal,
                    "settled recovery requires the actual ContinuityBatchJournal");
            ((ContinuityBatchJournal) journal).requireSettledSameGameRecovery(same, data, identity);
            var restored = data.controller();
            StrictJson.require(identity.equals(restored.owner()) && !restored.quarantined() && !restored.localUnresolved(),
                    "settled recovery cannot clear an unresolved original or change its owner");
            restoreCapturedController(same, restored);
        } finally { running.set(false); }
    }

    public ActionReceipt reconcileUnresolvedOriginal(ContinuityBatchJournal.UnresolvedSameGameData data, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(data); Objects.requireNonNull(deadline);
        StrictJson.require(running.compareAndSet(false, true), "unresolved original reconciliation requires an idle Controller");
        try {
            StrictJson.require(data.unresolvedActions().size() == 1, "unresolved original reconciliation requires exactly one original action");
            var originalReceipt = data.unresolvedActions().get(0);
            var originalCommand = originalReceipt.command();
            StrictJson.require(originalCommand.sessionId().equals(identity.sessionId()) && originalCommand.origin().game().equals(identity.game()) && originalCommand.origin().machineId().equals(identity.machineId()), "unresolved original action crossed the actual owner");
            
            StrictJson.require(!retired && quarantined && localUnresolved, "original reconciliation requires restored unresolved Controller state");
            var batchId = data.capturedController().batchPrefix() + "-" + (data.nextBatchSequence() - 1);
            StrictJson.require(usedBatches.contains(batchId) && data.usedBatches().contains(batchId), "original interrupted batch was not restored");
            var began = clock.now();
            Duration remaining = Duration.between(began.utc(), deadline);
            // BatchLimits accepts whole milliseconds. Round down so this local recovery
            // budget never extends the operation deadline or the original action deadline.
            long remainingMillis = remaining.toMillis();
            StrictJson.require(remainingMillis >= 1, "new reconciliation operation deadline expired");
            Duration budget = Duration.ofMillis(Math.min(remainingMillis, 3_600_000L));
            Duration poll = budget.compareTo(Duration.ofMillis(50)) < 0 ? budget : Duration.ofMillis(50);
            var limits = new BatchLimits(batchId, 1, budget, budget, poll, 1);
            var run = new Run(limits, began, Math.addExact(began.elapsedNanos(), budget.toNanos()), totalCommittedDays, Optional.empty(), false);
            
            ActionReceipt actual;
            try {
                actual = run.measured(Phase.ACTION_RECONCILIATION, () -> actions.reconcile(originalCommand.actionId()));
            } catch (RuntimeException failure) {
                quarantineUnresolved();
                throw new IOException("unresolved original reconciliation failed", failure);
            }
            
            StrictJson.require(sameCommand(actual.command(), originalCommand) && actual.bodySha256().equals(originalReceipt.bodySha256()), "unresolved original reconciliation changed the complete original command");
            
            var disposition = run.afterExecution(actual);
            
            if (!actual.settled()) {
                quarantineUnresolved();
                return actual;
            }
            
            if (actual.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                run.completeCycle(actual);
                run.requireCompletion(disposition);
                quarantined = false;
                localUnresolved = false;
            }
            
            return actual;
        } finally { running.set(false); }
    }

    private void restoreCapturedController(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            ControllerRestartState state)throws IOException {
        usedBatches.addAll(state.usedBatches());unsavedGameplayActions.addAll(state.unsavedGameplayActions());savedPair=state.savedPair();
        ledgerHead=Optional.of(same.persistedHead());eligibleSinceSave=state.eligibleSinceSave();dirty=state.dirty();quarantined=state.quarantined();
        localUnresolved=state.localUnresolved();totalCommittedDays=state.totalCommittedDays();completedAnalysisIds.addAll(state.completedAnalysisIds());
        stopRequested.set(state.stopRequested());
    }
    private void requireCleanRestartIdle(){
        StrictJson.require(!retired&&!quarantined&&!localUnresolved&&pendingReadParent.isEmpty()&&publicCheckpointUnknown.isEmpty(),
                "unresolved or pending continuation remains retained without replay");
    }
    /** Construction-only binding of the original journal DATA source; it grants no Ready or native authority. */
    public void bindRetainedIncidents(RetainedIncidentBatchSource actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(!running.get() && usedBatches.isEmpty() && lastReport.isEmpty(),
                "retained incident source must be bound before the first batch");
        StrictJson.require(retainedIncidents.compareAndSet(null, actual), "retained incident source binds exactly once");
    }
    /** Queue original journal DATA after rejected Root entry, without starting a batch or consuming its report. */
    public void enqueueRetainedIncidentData() throws IOException {
        StrictJson.require(retainedIncidents.get() != null, "actual retained incident DATA source must be bound before enqueue");
        StrictJson.require(running.compareAndSet(false, true), "retained incident DATA cannot overlap an active Controller call");
        try { enqueueAnalysisInputs(List.of(), failure -> { }); }
        finally { running.set(false); }
    }
    private void enqueueAnalysisInputs(List<BatchRequest> current, java.util.function.Consumer<Exception> scanFailureNote) throws IOException {
        Exception scanFailure = null;
        List<BatchRequest> incoming = List.of();
        try {
            List<BatchRequest> supplied = Objects.requireNonNull(retainedIncidents.get()).scan();
            StrictJson.require(supplied != null && supplied.size() <= RetainedIncidentBatchSource.MAX_BATCHES,
                    "retained incident DATA source exceeded its finite batch bound");
            incoming = List.copyOf(supplied);
            StrictJson.require(incoming.size() <= RetainedIncidentBatchSource.MAX_BATCHES,
                    "retained incident DATA source changed its finite batch bound");
        } catch (IOException | RuntimeException failure) {
            scanFailure = failure; scanFailureNote.accept(failure);
        }
        try {
            var candidates = new LinkedHashMap<String, BatchRequest>(retainedAnalysisInputs);
            for (BatchRequest work : current) mergeAnalysisInput(candidates, work);
            for (BatchRequest work : incoming) mergeAnalysisInput(candidates, work);
            for (BatchRequest work : candidates.values()) {
                if (pendingAnalyses.containsKey(work.batchId()) || completedAnalysisIds.contains(work.batchId())) continue;
                if (!retainedAnalysisInputs.containsKey(work.batchId()) && retainedAnalysisInputs.size() >= 32)
                    throw new IOException("bounded unaccepted offline backlog retains its original inputs for a later batch");
                retainedAnalysisInputs.putIfAbsent(work.batchId(), work);
                StrictJson.require(pendingAnalyses.size() < 32, "bounded offline analysis backlog requires completion before more batches");
                AnalysisTicket ticket = analyses.enqueue(work);
                StrictJson.require(ticket.batchId().equals(work.batchId()), "offline analyzer returned another captured batch");
                pendingAnalyses.put(ticket.batchId(), ticket); retainedAnalysisInputs.remove(work.batchId());
            }
            if (scanFailure != null) throw new IOException("retained incident DATA scan unavailable", scanFailure);
        } catch (IOException | RuntimeException failure) {
            if (scanFailure != null && scanFailure != failure && scanFailure != failure.getCause()) failure.addSuppressed(scanFailure);
            throw failure;
        }
    }
    private void mergeAnalysisInput(LinkedHashMap<String, BatchRequest> candidates, BatchRequest work) {
        Objects.requireNonNull(work);
        BatchRequest original = candidates.putIfAbsent(work.batchId(), work);
        StrictJson.require(original == null || original.equals(work), "retained offline incident batch ID changed captured sources");
        StrictJson.require(candidates.size() <= 64 + RetainedIncidentBatchSource.MAX_BATCHES,
                "bounded retained/current/original analysis candidate inputs required");
    }
    public boolean isRunning() { return running.get(); }
    public boolean isQuarantined() { return quarantined; }
    public boolean isRetired() { return retired; }
    /** Stable retained SAVE data only. Root owns the calls lock and validates the actual pair/physical state. */
    public synchronized Optional<CheckpointPair> savedPair() {
        StrictJson.require(!running.get(), "retained SAVE data requires the original Controller to be idle");
        return savedPair;
    }
    /** Exact existing planner, under the caller's original Root planning scope; no turn or dispatch is performed. */
    public PlanningResult planPublic(PlanningRequest actual)throws IOException {
        Objects.requireNonNull(actual);identity.require(actual);
        StrictJson.require(!quarantined&&!retired&&running.compareAndSet(false,true),"public planning requires the idle original resolved Controller");
        try{
            PlanningResult result = planner.plan(actual);
            var display = decisionDisplay; if (display != null) display.planned(actual, result);
            return result;
        }finally{running.set(false);}
    }
    /** Root holds its original calls lock before any new operator submission. A terminal dead subject is not itself UNKNOWN. */
    public void requireOperatorBefore()throws IOException {
        if(running.get()||retired||localUnresolved||pendingReadParent.isPresent()||quarantined)
            throw new IOException("operator submission cannot replace an active, retired, pending-UI or unresolved original Controller");
    }
    /** Consume the original typed canonical operator completion; no actor-change DTO can clear an UNKNOWN. */
    public void acceptOperatorRebound(ActionReceipt actual,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
        StrictJson.require(actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.OperatorRebound
                &&actual.command().sessionId().equals(identity.sessionId())&&actual.command().origin().game().equals(identity.game())
                &&actual.command().origin().machineId().equals(identity.machineId()),"exact owned typed operator completion required");
        StrictJson.require(!retired&&!localUnresolved&&pendingReadParent.isEmpty()&&running.compareAndSet(false,true),
                "operator rebound cannot replace an active, retired or locally unresolved original Controller");
        try {
            StrictJson.require(deadline.isAfter(clock.now().utc()),"finite current operator admission deadline required");
            SemanticEvidence rebound=observations.requireOperatorRebound(identity,actual,deadline);
            requireOperatorEvidence(identity,actual,rebound);
            try{journal.acceptOperatorRebound(identity,actual,rebound);}
            catch(IOException|RuntimeException failure){quarantineUnresolved();throw failure;}
            quarantined=false; // Actual private source + same writer reducer completed. Saved identities, credits and history stay original.
        }finally{running.set(false);}
    }
    private void quarantineUnresolved(){quarantined=true;localUnresolved=true;publicCheckpointUnknown=Optional.empty();}
    private void quarantineCheckpoint(ActionCommand original){
        if(!localUnresolved&&!quarantined&&pendingReadParent.isEmpty())publicCheckpointUnknown=Optional.of(original);
        quarantined=true;localUnresolved=true;
    }
    private static boolean checkpoint(ActionCommand command){return command.operation().value().equals("save-checkpoint");}
    private static boolean sameCommand(ActionCommand first,ActionCommand second){
        return Arrays.equals(ActionCodec.encodeCommand(first),ActionCodec.encodeCommand(second));
    }
    @FunctionalInterface private interface CheckpointAcceptance {JournalCommit require()throws IOException;}
    /** Consume the exact private captured SAVE; this method never saves, commits or manufactures a cycle. */
    public void acceptPublicCheckpoint(Captured actual,Instant deadline)throws IOException {
        acceptPublicCheckpoint(actual,deadline,()->journal.acceptPublicCheckpoint(identity,actual));
    }
    /** Root planned SAVE confirms in its original held writer while this Controller is executing that exact command. */
    public void acceptPublicCheckpoint(ContinuityStorePort.Session same,Captured actual,Instant deadline)throws IOException {
        Objects.requireNonNull(same);
        acceptPublicCheckpoint(actual,deadline,()->journal.acceptPublicCheckpoint(same,identity,actual));
    }
    private void acceptPublicCheckpoint(Captured actual,Instant deadline,CheckpointAcceptance qualification)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
        var original=actual.originalCommand();
        StrictJson.require(checkpoint(original)&&actual.material().session().equals(identity)
                &&actual.pair().saveActionId().equals(original.actionId()),"exact owned original captured SAVE required");
        var active=checkpointInvocation.get();boolean borrowedExecution=active!=null;
        if(borrowedExecution)StrictJson.require(running.get()&&sameCommand(active.original,original)
                &&(active.adopted==null||active.adopted==actual),"capture differs from this exact in-flight planned SAVE");
        else StrictJson.require(running.compareAndSet(false,true),"capture cannot replace another active Controller call");
        try {
            StrictJson.require(!retired&&pendingReadParent.isEmpty()&&deadline.isAfter(clock.now().utc()),"current finite owned checkpoint adoption required");
            StrictJson.require(!quarantined||localUnresolved&&publicCheckpointUnknown.filter(command->sameCommand(command,original)).isPresent(),
                    "a captured SAVE cannot clear a different UNKNOWN, pending UI or writer failure");
            var committed=Objects.requireNonNull(qualification.require());
            StrictJson.require(committed.equals(actual.journalCommit())&&committed.committedSavedDays()>=totalCommittedDays,
                    "original confirmed saved frontier required without cumulative credit regression");
            savedPair=Optional.of(actual.pair());ledgerHead=Optional.of(committed.persistedHead());totalCommittedDays=committed.committedSavedDays();
            dirty=false;eligibleSinceSave=0;unsavedGameplayActions.clear();adoptedPublicCheckpoint=Optional.of(original);
            if(borrowedExecution)active.adopted=actual;
            publicCheckpointUnknown=Optional.empty();localUnresolved=false;quarantined=false;
        }catch(IOException|RuntimeException failure){
            if(borrowedExecution&&active.adopted==null&&!retired&&!quarantined&&!localUnresolved&&pendingReadParent.isEmpty())
                throw new CapturedCheckpointDeferred(actual,failure);
            throw failure;
        }finally{if(!borrowedExecution)running.set(false);}
    }
    public void requestStop() { stopRequested.set(true); }
    /** An explicit owner resume is distinct from re-entering a timed-out/UNKNOWN session. */
    public void resume() {
        StrictJson.require(!running.get() && !quarantined && !retired, "active, unresolved or retired session cannot resume"); stopRequested.set(false);
    }
    /** Root-only in-process retirement before the original transport owner closes; no custody reset or replacement. */
    public void retire() {
        StrictJson.require(running.compareAndSet(false, true), "active batch must reach its original terminal state before retirement");
        try { retired = true; stopRequested.set(true); }
        finally { running.set(false); }
    }
    public Optional<BatchReport> lastReport() { return lastReport; }

    /** Public auto_turn delegates to this same loop and authority; it adds no periodic or final SAVE. */
    public TurnReport autoTurn(Instant deadline) {
        return singleTurn(deadline,Optional.empty(),false);
    }
    /** The requested canonical lifecycle operation is constrained before any command submission. */
    public TurnReport terminalTurn(LifecycleExpectedPostcondition.Operation desiredOperation,Optional<BigInteger> expectedRevision,Instant deadline) {
        return singleTurn(deadline,Optional.of(new TerminalConstraint(desiredOperation,expectedRevision)),false);
    }
    /** Public pending-UI calls consume exactly one private continuation through this original Controller. */
    public TurnReport pendingSuccessorUiTurn(Instant deadline) {
        return singleTurn(deadline,Optional.empty(),true);
    }
    private TurnReport singleTurn(Instant deadline,Optional<TerminalConstraint> terminalConstraint,boolean pendingOnly) {
        Objects.requireNonNull(deadline); long remaining = Duration.between(clock.now().utc(), deadline).toMillis();
        StrictJson.require(remaining > 0 && remaining <= 86_400_000, "finite future auto-turn deadline required");
        Duration wall = Duration.ofMillis(remaining); Duration readiness = Duration.ofMillis(Math.min(remaining, 30_000));
        BatchLimits single = new BatchLimits("auto-turn-" + java.util.UUID.randomUUID(), 1, wall, readiness,
                Duration.ofMillis(Math.min(readiness.toMillis(), 50)), 3);
        return new TurnReport(run(single, false, Optional.of(deadline),terminalConstraint,pendingOnly));
    }
    public record TurnReport(BatchReport execution) { public TurnReport { Objects.requireNonNull(execution); } }

    public BatchReport runBatch(BatchLimits limits) {
        return run(limits, true, Optional.empty(),Optional.empty(),false);
    }
    private BatchReport run(BatchLimits limits, boolean checkpointsEnabled, Optional<Instant> callerDeadline,
            Optional<TerminalConstraint> terminalConstraint,boolean pendingOnly) {
        Objects.requireNonNull(limits);Objects.requireNonNull(terminalConstraint);
        StrictJson.require(retainedIncidents.get() != null, "actual retained incident DATA source must be bound before batch execution");
        StrictJson.require(!pendingOnly||terminalConstraint.isEmpty(),"pending-only and desired terminal constraints are distinct");
        Optional<BatchReport> prior = lastReport;
        if (prior.filter(report -> report.batchId().equals(limits.batchId())).isPresent()) {
            StrictJson.require(lastLimits.filter(limits::equals).isPresent(), "same batch ID changed its exact request");
            return prior.orElseThrow();
        }
        StrictJson.require(running.compareAndSet(false, true), "one Game has one ordinary batch at a time");
        lastBatchBoundary = Optional.empty();
        SessionClock.Tick began = clock.now();
        long allowedNanos = callerDeadline.map(until -> Math.min(limits.wallTime().toNanos(),
                Math.max(0, Duration.between(began.utc(), until).toNanos()))).orElse(limits.wallTime().toNanos());
        Run run = new Run(limits, began, began.elapsedNanos() + allowedNanos, totalCommittedDays,terminalConstraint,pendingOnly);
        try {
            StrictJson.require(!retired, "original ordinary session has permanently retired");
            if((quarantined||pendingOnly)&&terminalConstraint.isEmpty())run.pendingUi=run.probePendingUi();
            if(pendingOnly&&run.pendingUi.isEmpty())throw new End(Terminal.ACTION_REJECTED,"actual private successor UI continuation is unavailable; ordinary planning and SAVE were not entered");
            if(run.pendingUi.isPresent())quarantined=true;
            StrictJson.require(!quarantined||run.pendingUi.isPresent(), "previous unresolved action/checkpoint/writer must be reconciled by its original authority");
            StrictJson.require(usedBatches.size() < 65_536 && usedBatches.add(limits.batchId()), "bounded unique batch ID required; replay is forbidden");
            reapAnalyses();
            run.requireTime();
            run.commit(JournalKind.BATCH_STARTED, Optional.empty(), Optional.empty(), List.of());
            // The admission probe predates this real writer event. Reopen the private current source
            // after the commit instead of carrying an old head-bound continuation token across it.
            run.pendingUi=Optional.empty();
            while (run.completedCount() < limits.maximumTurns()) {
                run.requireTime();
                if (stopRequested.get()) { run.terminal = Terminal.OPERATOR_STOP; break; }
                if(pendingReadParent.isPresent()){
                    if(terminalConstraint.isPresent())throw new End(Terminal.ACTION_REJECTED,"requested terminal operation cannot replace its retained unresolved read-publication parent");
                    run.reconcileReadParent(pendingReadParent.orElseThrow());continue;
                }
                // A private source may retain a new-actor UI obligation while the old parent is UNKNOWN.
                // Probe outside the ordinary frozen planning scope; token shape grants no authority.
                if(run.pendingUi.isEmpty()&&terminalConstraint.isEmpty())run.pendingUi=run.probePendingUi();
                if(quarantined&&run.pendingUi.isEmpty())throw new End(Terminal.ACTION_UNKNOWN,
                        "private successor UI source is no longer current after the real batch writer event");
                if(run.pendingUi.isPresent()) {
                    PendingSuccessorUi pending=run.pendingUi.orElseThrow();run.pendingUi=Optional.empty();
                    run.pendingUiTurn(pending);continue;
                }
                if(pendingOnly)throw new End(Terminal.ACTION_REJECTED,"pending-only call cannot enter ordinary planning, terminal selection or SAVE");
                var scoped=planningScope.inPlanningScope(()->run.planRound(checkpointsEnabled));
                if(scoped.readPublication().isPresent()){
                    if(scoped.value() instanceof PlannedRound decided)run.requireNoSourceContractFailure(decided.planned());
                    run.replanAfterPublication();continue;
                } // Selected actions require a new frame; an explicit contract failure remains a failure.
                PlanningRound round=scoped.value();
                run.requireTime();
                if(round instanceof TerminalRound terminal){run.terminalTurn(terminal.ready());continue;}
                if(round instanceof PendingUiRound pending){run.pendingUiTurn(pending.pending());continue;}
                if(round instanceof SaveRound save) {
                    if (!checkpointsEnabled) throw new End(Terminal.INCOMPLETE_MIGRATION, "auto_turn requires its actual initial paired baseline; it does not create a SAVE");
                    run.save(save.ready());continue;
                }
                PlannedRound decided=(PlannedRound)round;Ready ready=decided.ready();PlanningResult planned=decided.planned();
                var publication=decided.disposition();
                Objects.requireNonNull(publication,"actual planning completion disposition required");
                if(publication instanceof OrdinaryPlanCompletion.Published){run.requireNoSourceContractFailure(planned);run.replanAfterPublication();continue;}
                if(publication instanceof OrdinaryPlanCompletion.Blocked blocked)throw new End(Terminal.INCOMPLETE_MIGRATION,"actual plan publication blocked: "+blocked.reason());
                if(publication instanceof OrdinaryPlanCompletion.CheckpointRequired required){
                    ActionReceipt focus=required.original();
                    StrictJson.require(focus.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                            &&focus.command().sessionId().equals(identity.sessionId())&&focus.command().origin().game().equals(identity.game())
                            &&focus.command().origin().machineId().equals(identity.machineId())
                            &&focus.command().before().frame().episodeRunId().equals(ready.request().before().frame().episodeRunId())
                            &&focus.command().before().frame().identity().player().equals(ready.request().before().frame().identity().player()),"checkpoint request crossed actual original action owner or episode subject");
                    if(!checkpointsEnabled||ready.checkpointEligibility()!=CheckpointEligibility.SAFE)
                        throw new End(Terminal.CHECKPOINT_DEFERRED,"actual domain requires a paired SAVE before planning can continue");
                    run.save(ready);continue;
                }
                if(publication instanceof OrdinaryPlanCompletion.AwaitingOutcome waiting)
                    StrictJson.require(planned instanceof PlanningResult.ActionSelected selected&&waiting.command().equals(selected.command()),
                            "pending domain publication must bind the exact selected command");
                var display = decisionDisplay;
                if (display != null) display.planned(ready.request(), planned);
                if (planned instanceof PlanningResult.IncompleteMigration incomplete) {
                    throw new End(Terminal.INCOMPLETE_MIGRATION, "missing real production stages: " + incomplete.missingStages());
                }
                if (planned instanceof PlanningResult.Stopped stopped) {
                    throw new End(Terminal.PLANNER_STOPPED, stopped.reason() + ": " + stopped.detail());
                }
                if (planned instanceof PlanningResult.ReadOnlyWait) { run.pause(); continue; }
                if (planned instanceof PlanningResult.RefreshRequired) { continue; }
                if (planned instanceof PlanningResult.ExistingActionReconciliation existing) {
                    run.requireTime(); run.live();
                    if (stopRequested.get()) { run.terminal = Terminal.OPERATOR_STOP; break; }
                    ActionReceipt original;
                    try { original = run.measured(Phase.ACTION_RECONCILIATION, () -> actions.reconcile(existing.actionId())); }
                    catch (RuntimeException failure) { quarantineUnresolved(); throw new End(Terminal.ACTION_UNKNOWN, failure.toString()); }
                    StrictJson.require(original.command().actionId().equals(existing.actionId())
                            && original.command().sessionId().equals(identity.sessionId()), "reconciliation returned another original action/session");
                    run.reconciliations.add(new Reconciliation(run.completedCount() + 1,
                            ready.request().before(), planned.trace(), original));
                    run.currentTurnRevisionReplans = 0;
                    var completed=run.afterExecution(original);
                    if (!original.settled()) { quarantineUnresolved(); throw new End(Terminal.ACTION_UNKNOWN, "original action remains unresolved after read-only reconciliation"); }
                    if(original.outcome()==ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT){run.requireCompletion(completed);continue;}
                    if (original.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                        run.completeCycle(original);
                    }
                    run.requireCompletion(completed);
                    continue;
                }
                var selected = (PlanningResult.ActionSelected) planned;
                StrictJson.require(selected.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                        &&selected.command().before().equals(ready.request().before())
                        && selected.command().source().equals(ready.request().source())
                        && selected.command().sessionId().equals(identity.sessionId())
                        && !selected.command().deadline().isAfter(run.deadline()), "selected command crossed observation/session/deadline");
                // Ordinary submission requires its archived current SEM and actual cycle producer.
                // The independent terminal branch retains its real LifecycleIdentity instead.
                run.proof(ready);
                run.requireTime(); run.live();
                if (stopRequested.get()) { run.terminal = Terminal.OPERATOR_STOP; break; }
                ActionReceipt receipt;
                CheckpointInvocation checkpointCall=checkpoint(selected.command())?new CheckpointInvocation(selected.command()):null;
                StrictJson.require(checkpointInvocation.get()==null,"no nested original checkpoint invocation");
                if(checkpointCall!=null)checkpointInvocation.set(checkpointCall);
                try { receipt = run.measured(Phase.ACTION, () -> actions.execute(selected.command())); }
                catch(CapturedCheckpointDeferred pending){
                    ActionReceipt original=pending.actual.originalReceipt();
                    StrictJson.require(checkpointCall!=null&&sameCommand(original.command(),selected.command())
                            &&original.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&original.settled(),"private captured deferral changed its original canonical SAVE");
                    run.turns.add(new Turn(run.completedCount()+1,ready.request().before(),planned.trace(),original,
                            new TurnFacts(false,false,ActionEffects.observation(original).map(effect->List.of(effect.originalEvidence())).orElseGet(()->List.of(pending.actual.pair().nativeAckRef())))));
                    run.checkpointAdoptionDeferred=true;quarantineCheckpoint(selected.command());
                    run.requireCompletion(run.afterExecution(original)); // Consume the real canonical receipt once even while private adoption is deferred.
                    throw new End(Terminal.CHECKPOINT_DEFERRED,"actual original SAVE and SAVE_CONFIRMED retained; only private captured adoption may be retried, no new SAVE or ordinary credit");
                }
                catch(ReadPublicationRefreshException published){
                    StrictJson.require(published.command().equals(selected.command()),"actual read refresh changed the interrupted original command");
                    published.unresolvedParentId().ifPresent(id->pendingReadParent=Optional.of(new PendingReadParent(id,published.publication())));
                    if(published.zeroDispatchReceipt().isPresent())run.requireCompletion(run.afterExecution(published.zeroDispatchReceipt().orElseThrow()));
                    run.replanAfterPublication();
                    continue;
                }
                catch (PreSubmissionRevisionMismatchException changed) {
                    changed.zeroDispatchReceipt().ifPresent(zero -> StrictJson.require(zero.command().equals(selected.command())
                            && zero.outcome() == ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH, "revision refresh lost its actual zero-dispatch receipt"));
                    run.revisionReplans.add(new RevisionReplan(planned.trace(), changed.current(), changed.zeroDispatchReceipt()));
                    if (changed.zeroDispatchReceipt().isPresent())run.requireCompletion(run.afterExecution(changed.zeroDispatchReceipt().orElseThrow()));
                    if (run.currentTurnRevisionReplans++ >= 1) throw new End(Terminal.ACTION_REJECTED, "native frame changed again after the one allowed zero-dispatch refresh");
                    continue; // A fresh complete observation and plan, never a retry of this command.
                }
                catch (RuntimeException failure) {
                    quarantineUnresolved(); throw new End(Terminal.ACTION_UNKNOWN, failure.toString());
                }
                finally {checkpointInvocation.remove();}
                StrictJson.require(receipt.command().equals(selected.command()), "coordinator returned another action body");
                boolean applied = receipt.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED;
                List<ExactRef> nativeEvidence = ActionEffects.observation(receipt)
                        .map(effect -> List.of(effect.originalEvidence())).orElseGet(()->
                                receipt.state() instanceof ActionState.CompositeSettled settled
                                        &&settled.settlement() instanceof ActionState.SwaySchedulerCompleted scheduler
                                        ?scheduler.proof().originalEvidence():List.of());
                TurnFacts facts = new TurnFacts(applied && !checkpoint(receipt.command()) && receipt.visibleGameplay(), applied && !checkpoint(receipt.command()) && receipt.eligibleAdvance(), nativeEvidence);
                run.turns.add(new Turn(run.completedCount() + 1, ready.request().before(), planned.trace(), receipt, facts));
                run.currentTurnRevisionReplans = 0;
                run.currentTurnReadReplans=0;
                var completed=run.afterExecution(receipt);
                if (!receipt.settled()) { if(checkpoint(receipt.command()))quarantineCheckpoint(receipt.command());else quarantineUnresolved(); throw new End(Terminal.ACTION_UNKNOWN, "original action remains " + receipt.outcome()); }
                if(receipt.outcome()==ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT||receipt.outcome()==ActionReceipt.Outcome.SEND_CONFIRMED){run.requireCompletion(completed);continue;}
                if (!applied) throw new End(Terminal.ACTION_REJECTED, "original native/coordinator result: " + receipt.outcome());
                run.completeCycle(receipt);
                run.requireCompletion(completed);
                run.requireTime();
            }
            if (checkpointsEnabled && dirty) {
                Ready fresh = run.ready(true);
                if (fresh.checkpointEligibility() == CheckpointEligibility.SAFE) run.save(fresh);
                else { run.terminal = Terminal.CHECKPOINT_DEFERRED; run.detail = "dirty tail retained: " + fresh.checkpointEligibility(); }
            }
        } catch (End end) { run.terminal = end.terminal; run.detail = end.getMessage(); }
        catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt(); quarantineUnresolved(); run.terminal = Terminal.INTERNAL_FAILURE;
            run.detail = "owner thread interrupted; no action/save replay";
        } catch (IOException failure) {
            run.failIo(failure);
        } catch (java.io.UncheckedIOException failure) {
            run.failIo(failure);
        } catch (RuntimeException failure) {
            failure.printStackTrace(System.err);
            quarantineUnresolved(); run.terminal = Terminal.INTERNAL_FAILURE; run.detail = failure.toString();
        } finally {
            if (run.cyclePending) quarantineUnresolved();
            try { run.enqueueAnalyses(); }
            catch (IOException | RuntimeException failure) {
                run.detail += "; offline analysis enqueue failed: " + failure;
                // Preserve the original process, timeout or planning terminal through batch cleanup.
                if (!quarantined && (run.terminal == Terminal.TURN_BOUND || run.terminal == Terminal.OPERATOR_STOP))
                    run.terminal = Terminal.ANALYSIS_UNAVAILABLE;
            }
            // A failed writer is not called twice. UNKNOWN neither clears pending nor creates saved-day credit.
            // A private captured SAVE already committed its real saved frontier. While only adoption is deferred,
            // do not append metadata using the old unadopted Controller total or mark that canonical SAVE repair-required.
            if (run.journalStarted && !run.journalUnknown
                    && !(run.checkpointAdoptionDeferred && publicCheckpointUnknown.isPresent() && !run.cyclePending)) {
                try { run.commit(run.terminal == Terminal.TURN_BOUND || run.terminal == Terminal.OPERATOR_STOP
                        ? JournalKind.BATCH_FINISHED : !quarantined && !run.cyclePending
                        && Set.of(Terminal.CHECKPOINT_DEFERRED, Terminal.READINESS_TIMEOUT, Terminal.OBSERVATION_UNAVAILABLE, Terminal.WALL_TIMEOUT,Terminal.EPISODE_HANDOFF).contains(run.terminal)
                        ? JournalKind.BATCH_DEFERRED : JournalKind.BATCH_INTERRUPTED,
                        run.latest.map(value -> value.request().before()), Optional.empty(), List.of()); }
                catch (IOException | RuntimeException failure) { quarantineUnresolved(); run.terminal = Terminal.WRITER_UNKNOWN; run.detail += "; journal completion unknown: " + failure; }
                catch (InterruptedException failure) { Thread.currentThread().interrupt(); quarantineUnresolved(); run.terminal = Terminal.WRITER_UNKNOWN; run.detail += "; journal interrupted"; }
            }
            try {
                reapAnalyses();
                BatchReport report = new BatchReport(identity, limits.batchId(), run.terminal, run.detail, began, clock.now(),
                    run.spans, run.turns, run.reconciliations,run.lifecycleTurns,run.readReconciliations, run.revisionReplans, run.lastPlan,run.lastTerminal, run.lastLifecycle, savedPair, ledgerHead, totalCommittedDays - run.initialCommittedDays,
                    eligibleSinceSave, dirty, List.copyOf(pendingAnalyses.keySet()), completedAnalyses, failedAnalyses);
                lastBatchBoundary = Optional.of(new BatchBoundary(limits.batchId(), identity,
                        run.firstObservation, run.lastObservation, run.observationCount, run.observedDateChanged,
                        retired || quarantined || localUnresolved || pendingReadParent.isPresent()
                                || publicCheckpointUnknown.isPresent() || run.cyclePending || run.pendingUi.isPresent()
                                || run.checkpointAdoptionDeferred || run.journalUnknown || run.observedPendingAction));
                lastLimits = Optional.of(limits); lastReport = Optional.of(report); completedAnalyses.clear(); failedAnalyses.clear();
            } finally { running.set(false); }
        }
        return lastReport.orElseThrow();
    }

    private final class Run {
        final BatchLimits limits; final SessionClock.Tick began; final long untilNanos; final long initialCommittedDays;
        final Optional<TerminalConstraint> terminalConstraint;
        final boolean pendingOnly;
        final List<PhaseSpan> spans = new ArrayList<>(); final List<Turn> turns = new ArrayList<>(); final List<Reconciliation> reconciliations = new ArrayList<>();
        final List<LifecycleTurn> lifecycleTurns=new ArrayList<>();
        final List<ReadPublicationReconciliation> readReconciliations=new ArrayList<>();
        Optional<TerminalReady> lastTerminal=Optional.empty();
        Optional<PendingSuccessorUi> pendingUi=Optional.empty();
        final List<RevisionReplan> revisionReplans = new ArrayList<>(); Optional<org.xar.ck3.control.application.planning.PlanTrace> lastPlan = Optional.empty(); int currentTurnRevisionReplans,currentTurnReadReplans;
        final LinkedHashMap<String, BatchRequest> captured = new LinkedHashMap<>();
        Optional<GameLifecycle.Observation> lastLifecycle = Optional.empty(); Optional<Ready> latest = Optional.empty();
        Terminal terminal = Terminal.TURN_BOUND; String detail = "bounded ordinary batch ended"; boolean journalUnknown; boolean journalStarted; boolean cyclePending; boolean checkpointAdoptionDeferred;
        Optional<CompletedCycleProof> savingProof = Optional.empty();
        Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> firstObservation = Optional.empty();
        Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> lastObservation = Optional.empty();
        int observationCount;
        boolean observedDateChanged;
        boolean observedPendingAction;
        final Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> previousObservation = latestProgressObservation;
        void observed(PlanningRequest actualRequest) {
            var actual = actualRequest.before();
            observedPendingAction |= actualRequest.observations().actionFacts().stream().anyMatch(fact -> fact.unresolved());
            var comparison = firstObservation.isPresent() ? firstObservation : previousObservation;
            if (comparison.isPresent()) {
                var first = comparison.orElseThrow();
                observedDateChanged |= !first.machineId().equals(actual.machineId()) || !first.game().equals(actual.game())
                    || !first.frame().episodeRunId().equals(actual.frame().episodeRunId())
                    || !first.frame().identity().player().equals(actual.frame().identity().player())
                    || !first.frame().identity().dateRaw().equals(actual.frame().identity().dateRaw());
            }
            if (firstObservation.isEmpty()) firstObservation = Optional.of(actual);
            lastObservation = Optional.of(actual);
            latestProgressObservation = lastObservation;
            observationCount = Math.addExact(observationCount, 1);
        }
        Run(BatchLimits limits, SessionClock.Tick began, long untilNanos, long initialCommittedDays,
                Optional<TerminalConstraint> terminalConstraint,boolean pendingOnly) {
            this.limits = limits; this.began = began; this.untilNanos = untilNanos; this.initialCommittedDays = initialCommittedDays;
            this.terminalConstraint=terminalConstraint;this.pendingOnly=pendingOnly;
        }
        void failIo(Throwable failure) {
            failure.printStackTrace(System.err);
            detail = failure.toString();
            if (!journalUnknown && !cyclePending && !quarantined && !localUnresolved && pendingReadParent.isEmpty()
                    && org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(failure)) {
                terminal = Terminal.OBSERVATION_UNAVAILABLE;
                return;
            }
            quarantineUnresolved(); journalUnknown = true; terminal = Terminal.WRITER_UNKNOWN;
        }
        PlanningRound planRound(boolean checkpointsEnabled) throws IOException,InterruptedException {
            if(pendingOnly)throw new End(Terminal.ACTION_REJECTED,"pending-only call has no ordinary planning scope");
            Observation current=available(false);
            if(current instanceof TerminalReady terminal)return new TerminalRound(terminal);
            if(current instanceof PendingSuccessorUi pending)return new PendingUiRound(pending);
            if(terminalConstraint.isPresent())throw new End(Terminal.ACTION_REJECTED,
                    "requested terminal operation requires its actual terminal decision; ordinary planning and SAVE were not entered");
            Ready ready=(Ready)current;
            if(checkpointsEnabled&&dirty&&eligibleSinceSave>=limits.checkpointEveryEligibleAdvances()
                    &&ready.checkpointEligibility()==CheckpointEligibility.SAFE)return new SaveRound(ready);
            PlanningResult planned=measured(Phase.PLANNING,()->planner.plan(ready.request(),completion));lastPlan=Optional.of(planned.trace());
            StrictJson.require(planned.trace().before().equals(ready.request().before()),"planner result crossed current observation");
            requireTime();
            var disposition=Objects.requireNonNull(measured(Phase.OUTCOME_CONSUMPTION,()->completion.afterPlanning(ready.request(),planned)),"actual planning completion disposition required");
            requireTime();
            return new PlannedRound(ready,planned,disposition);
        }
        void requireTime() { if (clock.now().elapsedNanos() >= untilNanos) throw new End(Terminal.WALL_TIMEOUT, "complete batch monotonic wall bound expired"); }
        Instant deadline() { requireTime(); return began.utc().plusNanos(untilNanos - began.elapsedNanos()); }
        void live() throws IOException, InterruptedException {
            requireTime(); GameLifecycle.Observation state = measured(Phase.LIFECYCLE, () -> lifecycle.inspect(identity, deadline()));
            lastLifecycle = Optional.of(state);
            if (state instanceof GameLifecycle.Exited exited) throw new End(Terminal.INNER_EXIT,
                    "inner exit=" + exited.exitCode() + ", timed_out=" + exited.timedOut() + ", terminal=" + exited.terminal());
            if (state instanceof GameLifecycle.Unavailable unavailable) throw new End(Terminal.LIFECYCLE_UNAVAILABLE, unavailable.reason());
            StrictJson.require(((GameLifecycle.Running) state).measured().equals(identity.game()), "live process generation changed");
        }
        Ready ready() throws IOException, InterruptedException {
            return ready(false);
        }
        Ready ready(boolean stoppingForSave) throws IOException, InterruptedException {
            while(true){
                var captured=planningScope.inPlanningScope(()->available(stoppingForSave));
                if(captured.readPublication().isPresent()){replanAfterPublication();continue;}
                Observation observed=captured.value();
                if(observed instanceof Ready ready)return ready;
                throw new End(Terminal.CHECKPOINT_DEFERRED,"actual lifecycle terminal is not an ordinary after-SEM or paired SAVE frame");
            }
        }
        int completedCount(){return turns.size()+reconciliations.size()+lifecycleTurns.size()+readReconciliations.size();}
        Optional<PendingSuccessorUi> probePendingUi() throws IOException,InterruptedException {
            requireTime();Instant until=deadline();
            Optional<PendingSuccessorUi> found=Objects.requireNonNull(measured(Phase.OBSERVATION,
                    ()->transportAdoption.isPresent()?observations.pendingTransportSuccessorUi(identity,transportAdoption.orElseThrow(),until)
                            :observations.pendingSuccessorUi(identity,until)),"actual pending UI source result required");
            if(found.isPresent()) {
                requirePendingOwner(found.orElseThrow());StrictJson.require(!found.orElseThrow().token().deadline().isAfter(until),
                        "pending successor UI source extended caller deadline");
            }
            requireTime();return found;
        }
        void requirePendingOwner(PendingSuccessorUi pending)throws IOException,InterruptedException {
            if(transportAdoption.isPresent()) {
                var transport=transportAdoption.orElseThrow();
                StrictJson.require(journal instanceof ContinuityBatchJournal,"transported pending source requires its identical Journal");
                measured(Phase.JOURNAL,()->{((ContinuityBatchJournal)journal).requireHistoricalTransport(transport);return true;});
                pending.requireOwner(identity,transport);
            }else pending.requireOwner(identity);
        }
        void pendingUiTurn(PendingSuccessorUi pending) throws IOException,InterruptedException {
            requirePendingOwner(pending);var token=pending.token();
            if(terminalConstraint.isPresent())throw new End(Terminal.ACTION_REJECTED,
                    "requested terminal operation cannot replace the retained original successor UI parent");
            StrictJson.require(!token.deadline().isAfter(deadline()),"pending UI continuation extended caller deadline");
            quarantined=true; // The actual pending source stays isolated even if process inspection or operator stop interrupts this call.
            requireTime();live();if(stopRequested.get())throw new End(Terminal.OPERATOR_STOP,"operator stop before successor UI continuation");
            CompositeContinuationReport actual;
            try {actual=measured(Phase.ACTION,()->actions.continueOriginalComposite(token));}
            catch(IOException|RuntimeException failure){throw new End(Terminal.ACTION_UNKNOWN,
                    "original successor UI continuation remains retained: "+failure);}
            StrictJson.require(actual.parent().command().equals(token.originalParent()),"continuation changed its complete original parent");
            var binding=token.obligation().binding();
            for(ActionReceipt child:actual.children())StrictJson.require(child.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay
                    &&child.command().origin().machineId().equals(identity.machineId())&&child.command().origin().game().equals(identity.game())
                    &&child.command().sessionId().equals(identity.sessionId())
                    &&child.command().before().frame().identity().player().equals(binding.successorCharacterId())
                    &&child.command().before().frame().episodeRunId().equals(binding.successorEpisodeRunId())
                    &&!child.command().deadline().isAfter(token.deadline()),"actual new UI child crossed the published successor or finite source window");
            lifecycleTurns.add(new LifecycleTurn(completedCount()+1,token.obligation().binding().predecessor(),actual.parent(),false,
                    Optional.of(new SuccessorUiContinuation(token.kind(),actual,token.canonicalDomain(),
                            token.actualPublishedDriver(),token.canonicalPublicationProof()))));
            lastPlan=Optional.empty();latest=Optional.empty();lastTerminal=Optional.empty();
            if(!actual.parent().settled())throw new End(Terminal.ACTION_UNKNOWN,"actual successor UI parent or child remains unresolved; no replay");
            if(actual.parent().outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)
                throw new End(Terminal.ACTION_REJECTED,"actual successor UI parent settled without confirmed continuation");
            StrictJson.require(lifecycleProof(actual.parent()).filter(proof->proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR).isPresent(),
                    "actual successor UI finalization requires its committed CONTINUE proof");
            completeCycle(actual.parent());
            quarantined=false;localUnresolved=false; // completeCycle used the actual same-Game EpisodeContinuation; no day or SAVE credit is inferred.
        }
        void requireNoSourceContractFailure(PlanningResult planned) {
            if(planned instanceof PlanningResult.Stopped stopped
                    &&stopped.reason()==PlanningResult.StopReason.SOURCE_CONTRACT_REJECTED)
                throw new End(Terminal.PLANNER_STOPPED,stopped.reason()+": "+stopped.detail());
        }
        void replanAfterPublication(){if(++currentTurnReadReplans>128)throw new End(Terminal.PLANNER_STOPPED,"finite actual publication replan bound reached before dispatch");}
        void reconcileReadParent(PendingReadParent original) throws IOException,InterruptedException {
            requireTime();live();ActionReceipt actual=measured(Phase.ACTION_RECONCILIATION,()->actions.reconcile(original.actionId()));
            StrictJson.require(actual.command().actionId().equals(original.actionId())&&actual.command().sessionId().equals(identity.sessionId())
                    &&actual.command().origin().game().equals(identity.game())&&actual.command().origin().machineId().equals(identity.machineId()),"read publication reconciliation changed its actual original owned parent");
            readReconciliations.add(new ReadPublicationReconciliation(completedCount()+1,actual,original.publication()));lastPlan=Optional.empty();
            OrdinaryPlanCompletion.ExecutionDisposition consumed=actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay?afterExecution(actual):null;
            if(!actual.settled()){quarantineUnresolved();throw new End(Terminal.ACTION_UNKNOWN,"original read-publication parent remains unresolved after read-only reconciliation");}
            pendingReadParent=Optional.empty();
            if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED)completeCycle(actual);
            if(consumed!=null)requireCompletion(consumed);
        }
        void terminalTurn(TerminalReady ready) throws IOException,InterruptedException {
            var current=ready.identity();
            StrictJson.require(current.machineId().equals(identity.machineId())&&current.game().equals(identity.game())
                    &&current.sessionId().equals(identity.sessionId()),"actual terminal observation crossed owned Game/session");
            if(ready.decision() instanceof TerminalBlocked blocked)throw new End(Terminal.INCOMPLETE_MIGRATION,"actual terminal decision blocked: "+blocked.reason());
            if(ready.decision() instanceof TerminalWait){pause();return;}
            if(terminalConstraint.isPresent()) {
                var requested=terminalConstraint.orElseThrow();
                if(!(ready.decision() instanceof TerminalAction selected))throw new End(Terminal.ACTION_REJECTED,
                        "retained terminal reconciliation has no selected requested operation; no new or replacement request was submitted");
                if(!selected.command().operation().equals(requested.operation().key()))throw new End(Terminal.ACTION_REJECTED,
                        "actual selected terminal operation "+selected.command().operation().value()+" differs from requested "+requested.operation().key().value());
                if(!(selected.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.LifecycleTerminal terminal))
                    throw new End(Terminal.ACTION_REJECTED,"requested operation requires the actual original terminal command frame");
                if(requested.expectedRevision().isPresent()&&!requested.expectedRevision().orElseThrow().equals(terminal.identity().frame().revision()))
                    throw new End(Terminal.ACTION_REJECTED,"requested public lifecycle revision differs from the same selected original command frame");
            }
            requireTime();live();if(stopRequested.get())throw new End(Terminal.OPERATOR_STOP,"operator stop before terminal submission");
            boolean reconcile=ready.decision() instanceof TerminalReconciliation;ActionReceipt actual;
            try {
                if(reconcile){String action=((TerminalReconciliation)ready.decision()).actionId();
                    actual=measured(Phase.ACTION_RECONCILIATION,()->actions.reconcile(action));
                    StrictJson.require(actual.command().actionId().equals(action),"terminal reconciliation changed original action ID");
                }else {var selected=((TerminalAction)ready.decision()).command();
                    StrictJson.require(!selected.deadline().isAfter(deadline()),"terminal command extended caller deadline");
                    actual=measured(Phase.ACTION,()->actions.execute(selected));
                    StrictJson.require(actual.command().equals(selected),"terminal coordinator changed the complete original command");
                }
            }catch(ReadPublicationRefreshException published){
                StrictJson.require(!reconcile&&ready.decision() instanceof TerminalAction selected&&published.command().equals(selected.command()),"terminal read refresh changed the original selected parent");
                published.unresolvedParentId().ifPresent(id->pendingReadParent=Optional.of(new PendingReadParent(id,published.publication())));
                if(published.zeroDispatchReceipt().isPresent())lifecycleTurns.add(new LifecycleTurn(completedCount()+1,current,published.zeroDispatchReceipt().orElseThrow(),false));
                replanAfterPublication();
                return;
            }catch(RuntimeException failure){quarantineUnresolved();throw new End(Terminal.ACTION_UNKNOWN,failure.toString());}
            lifecycleTurns.add(new LifecycleTurn(completedCount()+1,current,actual,reconcile));
            if(reconcile&&actual.command().origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay){
                var consumed=afterExecution(actual);
                if(!actual.settled()){quarantineUnresolved();throw new End(Terminal.ACTION_UNKNOWN,"original gameplay action remains unresolved at the actual lifecycle boundary");}
                requireCompletion(consumed);
                if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED){
                    cyclePending=true;
                    try{measured(Phase.JOURNAL,()->{journal.retainCycle(identity,actual);return true;});}
                    catch(IOException|RuntimeException failure){journalUnknown=true;throw failure;}
                    throw new End(Terminal.CHECKPOINT_DEFERRED,"original applied gameplay receipt retained; actual terminal frame cannot replace its missing ordinary after-SEM");
                }
                return; // Actual non-applied terminal/rejection grants no cycle or day and is never resubmitted.
            }
            if(!actual.settled()){quarantineUnresolved();throw new End(Terminal.ACTION_UNKNOWN,"original lifecycle action remains "+actual.outcome());}
            if(actual.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)throw new End(Terminal.ACTION_REJECTED,"original terminal lifecycle result: "+actual.outcome());
            StrictJson.require(lifecycleProof(actual).isPresent(),"registered lifecycle parent did not return its actual committed lifecycle settlement");
            completeCycle(actual);
        }
        Observation available(boolean stoppingForSave) throws IOException,InterruptedException {
            long readyUntil = Math.min(untilNanos, clock.now().elapsedNanos() + limits.readinessTimeout().toNanos());
            String waitingReason = "readiness deadline expired before observation";
            while (true) {
                if (!stoppingForSave && stopRequested.get()) throw new End(dirty ? Terminal.CHECKPOINT_DEFERRED : Terminal.OPERATOR_STOP,
                        "operator stop observed during readiness; no new gameplay submitted");
                requireTime(); live();
                if (clock.now().elapsedNanos() >= readyUntil) {
                    requireTime();
                    throw new End(Terminal.READINESS_TIMEOUT, waitingReason);
                }
                Instant until = began.utc().plusNanos(readyUntil - began.elapsedNanos());
                Instant planningUntil = deadline();
                Observation result = measured(Phase.OBSERVATION, () -> observations.observe(identity, until, planningUntil));
                if (result instanceof Ready ready) {
                    identity.require(ready.request()); StrictJson.require(!ready.request().deadline().isAfter(planningUntil), "observation extended batch planning deadline");
                    // A late actual Ready still describes an observed date; it grants no extended execution deadline.
                    observed(ready.request());
                    ready.offlineAnalysis().ifPresent(batch -> {
                        StrictJson.require(captured.size() < 32 || captured.containsKey(batch.batchId()), "bounded captured analysis work per batch");
                        BatchRequest previous = captured.get(batch.batchId());
                        StrictJson.require(previous == null || previous.equals(batch), "offline incident batch ID changed captured sources");
                        if (!completedAnalysisIds.contains(batch.batchId()) && !pendingAnalyses.containsKey(batch.batchId())) {
                            BatchRequest retained = retainedAnalysisInputs.get(batch.batchId());
                            StrictJson.require(retained == null || retained.equals(batch), "retained offline incident batch ID changed captured sources");
                            // New work remains in this Run when the rejected-input reserve is full.
                            // Its admission bound is consumed during cleanup, never as an unresolved Game action.
                            if (retained != null || retainedAnalysisInputs.size() < 32)
                                retainedAnalysisInputs.putIfAbsent(batch.batchId(), batch);
                        }
                        captured.putIfAbsent(batch.batchId(), batch);
                    });
                    // The producer may already have persisted incident DATA when observe returns late.
                    // Retaining its validated original does not extend planning, action or SAVE authority.
                    requireTime();
                    latest = Optional.of(ready);lastTerminal=Optional.empty(); return ready;
                }
                requireTime();
                if(result instanceof TerminalReady terminal){
                    var current=terminal.identity();StrictJson.require(current.machineId().equals(identity.machineId())&&current.game().equals(identity.game())
                            &&current.sessionId().equals(identity.sessionId()),"actual terminal source crossed owned Game/session");
                    latest=Optional.empty();lastPlan=Optional.empty();lastTerminal=Optional.of(terminal);return terminal;
                }
                if(result instanceof PendingSuccessorUi pending){
                    pending.requireOwner(identity);StrictJson.require(!pending.token().deadline().isAfter(until),"pending UI source extended caller deadline");
                    latest=Optional.empty();lastPlan=Optional.empty();lastTerminal=Optional.empty();return pending;
                }
                if (result instanceof ObservationUnavailable unavailable) throw new End(Terminal.OBSERVATION_UNAVAILABLE, unavailable.reason());
                waitingReason = ((Waiting) result).reason();
                if (clock.now().elapsedNanos() >= readyUntil) throw new End(Terminal.READINESS_TIMEOUT, waitingReason);
                pause();
            }
        }
        void pause() throws IOException, InterruptedException {
            requireTime(); long remaining = untilNanos - clock.now().elapsedNanos();
            if (remaining <= 0) throw new End(Terminal.WALL_TIMEOUT, "complete batch monotonic wall bound expired before poll");
            measured(Phase.IDLE_WAIT, () -> { clock.waitFor(Duration.ofNanos(Math.min(remaining, limits.pollInterval().toNanos()))); return true; });
        }
        void save(Ready ready) throws IOException, InterruptedException {
            requireTime(); live(); StrictJson.require(ready.checkpointEligibility() == CheckpointEligibility.SAFE, "SAVE is not eligible on this native frame");
            savingProof = Optional.of(proof(ready));
            var request = checkpointRequests.prepare(ready.request().before(), ready.request().source(), identity.sessionId(), savedPair, deadline());
            CheckpointResult result;
            try { result = measured(Phase.CHECKPOINT, () -> checkpoints.checkpoint(request)); }
            catch (RuntimeException failure) { quarantineUnresolved(); throw new End(Terminal.CHECKPOINT_UNKNOWN, failure.toString()); }
            if (!(result instanceof CheckpointResult.Confirmed confirmed)) {
                if (result instanceof CheckpointResult.Unknown) { quarantineUnresolved(); throw new End(Terminal.CHECKPOINT_UNKNOWN, "original SAVE/pair outcome unknown"); }
                throw new End(Terminal.CHECKPOINT_REJECTED, "original SAVE was rejected");
            }
            CheckpointPair actual = confirmed.pair();
            StrictJson.require(actual.frame().game().equals(identity.game()) && actual.frame().machineId().equals(identity.machineId()), "confirmed SAVE crossed Game identity");
            // Physical pair remains retained even if subsequent ledger commit fails. It is never silently re-saved.
            savedPair = Optional.of(actual);
            commit(JournalKind.SAVE_CONFIRMED, Optional.of(actual.frame()), savedPair,
                    List.of(actual.save().reference(), actual.driver().reference(), actual.nativeAckRef()));
            dirty = false; eligibleSinceSave = 0; unsavedGameplayActions.clear(); savingProof = Optional.empty(); requireTime();
        }
        CompletedCycleProof proof(Ready ready) throws IOException, InterruptedException {
            if (ready.semanticEvidence().isEmpty()) throw new End(Terminal.INCOMPLETE_MIGRATION,
                    "real completed-cycle semantic evidence is unavailable; no SAVE or new gameplay was submitted");
            Optional<CompletedCycleProof> checked = measured(Phase.JOURNAL,
                    () -> journal.cycleProof(identity, ready.semanticEvidence().orElseThrow()));
            return checked.orElseThrow(() -> new End(Terminal.INCOMPLETE_MIGRATION,
                    "real completed-cycle producer is unavailable or an original AUTO remains unsettled"));
        }
        void completeCycle(ActionReceipt receipt) throws IOException, InterruptedException {
            if(checkpoint(receipt.command())) {
                if(adoptedPublicCheckpoint.filter(original->sameCommand(original,receipt.command())).isEmpty()
                        ||savedPair.filter(pair->pair.saveActionId().equals(receipt.command().actionId())).isEmpty()) {
                    quarantineCheckpoint(receipt.command());
                    throw new End(Terminal.CHECKPOINT_UNKNOWN,"canonical SAVE has no privately qualified captured material adoption; no repeat SAVE or ordinary cycle credit");
                }
                return; // SAVE_CONFIRMED and its physical frontier already exist. Never retain/settle this SAVE as gameplay.
            }
            var lifecycle=lifecycleProof(receipt);
            if(lifecycle.isPresent()) {
                switch(lifecycle.orElseThrow().kind()) {
                    case DEATH -> { return; } // Actual terminal accounting is a lifecycle event, with zero ordinary cycle/day credit.
                    case NEXT_EPISODE -> {
                        retired=true;stopRequested.set(true);
                        throw new End(Terminal.EPISODE_HANDOFF,"actual lifecycle replaced the owned Game/actor; Root must publish its qualified replacement loop without replay");
                    }
                    case ACTOR_SWITCH -> throw new End(Terminal.INCOMPLETE_MIGRATION,"actor-switch proof has no actual supported lifecycle handler in this production generation");
                    case CONTINUE_SUCCESSOR -> {
                        cyclePending=true;
                        try {
                            var admitted=measured(Phase.JOURNAL,()->transportAdoption.isPresent()
                                    &&sameCommand(transportAdoption.orElseThrow().parent(),receipt.command())
                                    ?episodes.continueTransportedSameGame(identity,receipt,transportAdoption.orElseThrow(),deadline())
                                    :episodes.continueAdmittedSameGame(identity,receipt,deadline()));
                            StrictJson.require(journal instanceof ContinuityBatchJournal,"natural adoption requires the same actual continuity journal");
                            var actualJournal=(ContinuityBatchJournal)journal;
                            measured(Phase.JOURNAL,()->{actualJournal.requireHistoricalEpisodeAdoption(admitted);return true;});
                            acceptNaturalEpisode(receipt,admitted);cyclePending=false;
                            return;
                        }catch(IOException|RuntimeException failure){journalUnknown=true;throw failure;}
                    }
                }
            }
            recordGameplay(receipt); cyclePending = true;
            try {
                measured(Phase.JOURNAL, () -> { journal.retainCycle(identity, receipt); return true; });
                Ready fresh = ready(true);
                if (fresh.semanticEvidence().isEmpty()) throw new End(Terminal.INCOMPLETE_MIGRATION,
                        "the original AUTO remains retained; a fresh archived after-SEM is unavailable");
                measured(Phase.JOURNAL, () -> journal.settleCycle(identity, receipt, fresh.semanticEvidence().orElseThrow()));
                cyclePending = false;
            } catch (IOException | RuntimeException failure) { journalUnknown = true; throw failure; }
        }
        OrdinaryPlanCompletion.ExecutionDisposition afterExecution(ActionReceipt receipt) throws IOException,InterruptedException {
            var display = decisionDisplay; if (display != null) display.returned(receipt);
            measured(Phase.OUTCOME_CONSUMPTION,()->planner.afterExecution(receipt));
            return Objects.requireNonNull(measured(Phase.OUTCOME_CONSUMPTION,()->completion.afterExecution(receipt)),"actual outcome completion disposition required");
        }
        void requireCompletion(OrdinaryPlanCompletion.ExecutionDisposition disposition) {
            if(disposition instanceof OrdinaryPlanCompletion.Blocked blocked)throw new End(Terminal.INCOMPLETE_MIGRATION,"actual outcome publication blocked: "+blocked.reason());
            // Published continues only through completeCycle's fresh after-SEM and the next fresh planning capture.
        }
        void commit(JournalKind kind, Optional<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity> frame,
                Optional<CheckpointPair> pair, List<ExactRef> evidence) throws IOException, InterruptedException {
            try {
                JournalCommit committed = measured(Phase.JOURNAL, () -> journal.commit(new JournalInput(identity, limits.batchId(), kind, frame, pair,
                        kind == JournalKind.SAVE_CONFIRMED ? savingProof : Optional.empty(), evidence)));
                StrictJson.require(committed.committedSavedDays() >= totalCommittedDays, "authoritative cumulative saved-day credit regressed");
                StrictJson.require(kind == JournalKind.SAVE_CONFIRMED || committed.committedSavedDays() == totalCommittedDays, "non-SAVE journal transition granted saved-day credit");
                totalCommittedDays = committed.committedSavedDays(); ledgerHead = Optional.of(committed.persistedHead());
                if (kind == JournalKind.BATCH_STARTED) journalStarted = true;
            } catch (IOException | RuntimeException failure) { journalUnknown = true; quarantineUnresolved(); throw failure; }
        }
        void enqueueAnalyses() throws IOException {
            SessionClock.Tick start = clock.now();
            try {
                enqueueAnalysisInputs(List.copyOf(captured.values()), failure -> detail += "; retained incident DATA scan failed: " + failure);
                spans.add(new PhaseSpan(Phase.ANALYSIS_ENQUEUE, start, clock.now(), PhaseTerminal.RETURNED));
            } catch (IOException | RuntimeException failure) {
                spans.add(new PhaseSpan(Phase.ANALYSIS_ENQUEUE, start, clock.now(), PhaseTerminal.FAILED)); throw failure;
            }
        }
        <T> T measured(Phase phase, Checked<T> operation) throws IOException, InterruptedException {
            SessionClock.Tick start = clock.now();
            try { T value = operation.run(); spans.add(new PhaseSpan(phase, start, clock.now(), PhaseTerminal.RETURNED)); return value; }
            catch (IOException | RuntimeException failure) { spans.add(new PhaseSpan(phase, start, clock.now(), PhaseTerminal.FAILED)); throw failure; }
            catch (InterruptedException failure) { spans.add(new PhaseSpan(phase, start, clock.now(), PhaseTerminal.INTERRUPTED)); throw failure; }
        }
    }
    @FunctionalInterface private interface Checked<T> { T run() throws IOException, InterruptedException; }
    private sealed interface PlanningRound permits TerminalRound,PendingUiRound,SaveRound,PlannedRound { }
    private record TerminalRound(TerminalReady ready) implements PlanningRound { }
    private record PendingUiRound(PendingSuccessorUi pending) implements PlanningRound { }
    private record SaveRound(Ready ready) implements PlanningRound { }
    private record PlannedRound(Ready ready,PlanningResult planned,OrdinaryPlanCompletion.PlanningDisposition disposition) implements PlanningRound { }
    private static Optional<LifecycleTransitionProof> lifecycleProof(ActionReceipt receipt) {
        ActionState.Settlement settlement=receipt.state() instanceof ActionState.Settled settled?settled.settlement()
                :receipt.state() instanceof ActionState.CompositeSettled settled?settled.settlement():null;
        return settlement instanceof ActionState.LifecycleApplied applied?Optional.of(applied.proof()):Optional.empty();
    }
    private void recordGameplay(ActionReceipt receipt) {
        if (!receipt.visibleGameplay() && !receipt.eligibleAdvance()) return;
        StrictJson.require(unsavedGameplayActions.size() < 100_000 || unsavedGameplayActions.contains(receipt.command().actionId()),
                "finite unsaved gameplay evidence capacity exhausted");
        if (!unsavedGameplayActions.add(receipt.command().actionId())) return;
        dirty |= receipt.visibleGameplay(); if (receipt.eligibleAdvance()) eligibleSinceSave++;
    }
    private void reapAnalyses() {
        var iterator = pendingAnalyses.entrySet().iterator();
        while (iterator.hasNext()) {
            var item = iterator.next(); var result = item.getValue().completion().toCompletableFuture();
            if (!result.isDone()) continue;
            try {
                AnalysisCompletion complete = result.join();
                StrictJson.require(complete.batchId().equals(item.getKey()), "offline analysis completion crossed batch");
                StrictJson.require(completedAnalysisIds.size() < 65_536, "bounded completed analysis inventory");
                completedAnalyses.add(complete); completedAnalysisIds.add(complete.batchId());
            } catch (RuntimeException failure) { failedAnalyses.add(item.getKey()); }
            retainedAnalysisInputs.remove(item.getKey());
            iterator.remove();
        }
    }
    private static final class End extends RuntimeException {
        private static final long serialVersionUID = 1L; final Terminal terminal;
        End(Terminal terminal, String detail) { super(detail); this.terminal = terminal; }
    }
}
