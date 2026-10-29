package org.xar.ck3.control.application.session;

import java.io.IOException;
import org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture.Captured;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletionStage;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandExpectation;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.CompositeContinuationToken;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Application ports borrow the original sole session, writer and native custody. */
public final class SessionPorts {
    private SessionPorts() { }
    public record SessionIdentity(String machineId, GameGeneration game, String sessionId) {
        public SessionIdentity {
            StrictJson.require(machineId != null && machineId.matches("[a-z0-9][a-z0-9-]{0,63}") && !machineId.equals("unknown"), "explicit session machine ID required");
            Objects.requireNonNull(game);
            StrictJson.require(sessionId != null && sessionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"), "bounded owned session identity required");
        }
        public void require(PlanningRequest request) {
            StrictJson.require(machineId.equals(request.before().machineId()) && game.equals(request.before().game())
                    && sessionId.equals(request.sessionId()) && machineId.equals(request.source().machineId()), "ordinary observation crossed owned Game/session");
        }
    }
    @FunctionalInterface public interface LifecyclePort {
        /** Measure actual inner process identity and terminal state; outer tool ACK is not a Running result. */
        GameLifecycle.Observation inspect(SessionIdentity expected, Instant deadline) throws IOException;
    }
    public enum CheckpointEligibility { SAFE, MODAL_PENDING, TERMINAL_PENDING, UNRESOLVED_ACTION, UNAVAILABLE }
    public sealed interface Observation permits Ready, TerminalReady, PendingSuccessorUi, Waiting, ObservationUnavailable { }
    /** Pending successor DATA, not ordinary Ready or a permission to submit. The registered continuation revalidates its private source. */
    public record PendingSuccessorUi(NaturalSuccessionPreparation.PendingToken token) implements Observation {
        public PendingSuccessorUi {
            Objects.requireNonNull(token);Objects.requireNonNull(token.deadline());
            ActionCommand parent=Objects.requireNonNull(token.originalParent());
            StrictJson.require((token.kind()==CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE||token.kind()==CompositeContinuationToken.Kind.SUCCESSOR_UI_EVENT||token.kind()==CompositeContinuationToken.Kind.SUCCESSOR_UI_DATE_ADVANCE)
                    &&parent.origin() instanceof CommandOrigin.LifecycleTerminal
                    &&LifecycleComposites.parentKind(parent.operation()).filter(kind->kind==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR).isPresent(),
                    "pending successor UI must retain the actual original terminal CONTINUE parent");
            var obligation=Objects.requireNonNull(token.obligation());var binding=obligation.binding();
            StrictJson.require(parent.lifecycleBefore().sameGuardFrame(binding.predecessor())&&parent.actionId().equals(binding.parentActionId())
                    &&ActionCodec.bodySha256(parent).equals(binding.parentBodySha256()),"pending successor UI crossed its original parent body or causal predecessor");
            var sources=List.copyOf(Objects.requireNonNull(token.evidence()));
            StrictJson.require(!sources.isEmpty(),"actual pending successor evidence required");
            for(ExactRef ref:sources)StrictJson.require(ref.bytes()>0,"pending successor evidence must be nonempty");
            for(ExactRef ref:List.of(token.canonicalDomain(),token.actualPublishedDriver(),token.canonicalPublicationProof()))
                StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"actual canonical pending successor sources required");
        }
        public void requireOwner(SessionIdentity owner) {
            Objects.requireNonNull(owner);ActionCommand parent=token.originalParent();
            StrictJson.require(owner.machineId().equals(parent.origin().machineId())&&owner.game().equals(parent.origin().game())
                    &&owner.sessionId().equals(parent.sessionId()),"pending successor UI crossed the original owned Game/session");
        }
        /** Owner consistency only; the identical Journal must replay this private ticket and NS must freshly qualify its current source. */
        public void requireOwner(SessionIdentity owner,ContinuityBatchJournal.ReboundTransport transport) {
            Objects.requireNonNull(owner);Objects.requireNonNull(transport);
            StrictJson.require(owner.equals(transport.owner())
                    &&java.util.Arrays.equals(ActionCodec.encodeCommand(token.originalParent()),ActionCodec.encodeCommand(transport.parent()))
                    &&owner.machineId().equals(token.originalParent().origin().machineId())
                    &&owner.game().equals(token.originalParent().origin().game()),
                    "pending successor UI differs from its actual private transported owner or original parent");
        }
    }
    /** Produced in the actual terminal source scope; no ordinary observation identity is synthesized. */
    public record TerminalReady(LifecycleIdentity identity,TerminalDecision decision) implements Observation {
        public TerminalReady {
            Objects.requireNonNull(identity);Objects.requireNonNull(decision);
            if(decision instanceof TerminalAction selected)StrictJson.require(selected.command().lifecycleBefore().equals(identity),"terminal decision crossed its actual lifecycle source");
        }
    }
    public sealed interface TerminalDecision permits TerminalAction,TerminalReconciliation,TerminalWait,TerminalBlocked { }
    public record TerminalAction(ActionCommand command) implements TerminalDecision {
        public TerminalAction {
            Objects.requireNonNull(command);StrictJson.require(command.origin() instanceof CommandOrigin.LifecycleTerminal,"actual lifecycle terminal command required");
            StrictJson.require(org.xar.ck3.control.application.lifecycle.LifecycleComposites.parentKind(command.operation()).isPresent(),"terminal loop only dispatches the actual registered parent lifecycle composites");
        }
    }
    public record TerminalReconciliation(String actionId) implements TerminalDecision {
        public TerminalReconciliation {StrictJson.require(actionId!=null&&actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"),"bounded original terminal action ID required");}
    }
    public record TerminalWait(String reason) implements TerminalDecision {public TerminalWait {StrictJson.text(reason);}}
    public record TerminalBlocked(String reason,List<ExactRef> evidence) implements TerminalDecision {
        public TerminalBlocked {StrictJson.text(reason);evidence=List.copyOf(evidence);StrictJson.require(!evidence.isEmpty(),"actual terminal block requires its original evidence");}
    }
    /** Each reference is an actual archived original, including the full thirteen-field Driver wire. */
    public record SemanticEvidence(ObservationIdentity frame, ExactRef semantic, ExactRef originalNativePacket,
            ExactRef driverStamp, ExactRef originalDriver, Instant observedAt) {
        public SemanticEvidence {
            Objects.requireNonNull(frame); Objects.requireNonNull(observedAt);
            for (ExactRef ref : List.of(semantic, originalNativePacket, driverStamp, originalDriver))
                StrictJson.require(ref.bytes() > 0 && java.nio.file.Path.of(ref.path()).isAbsolute(), "actual nonempty archived semantic/native/Driver evidence required");
            StrictJson.require(!semantic.equals(originalNativePacket), "raw native packet is not a semantic export");
        }
        public List<ExactRef> references() { return List.of(semantic, originalNativePacket, driverStamp, originalDriver); }
    }
    /** DATA consistency only. The installed Root source and actual canonical writer must still qualify it. */
    public static OperatorPlayerSwitch.Completion requireOperatorEvidence(SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic) {
        Objects.requireNonNull(owner);Objects.requireNonNull(actual);Objects.requireNonNull(semantic);
        StrictJson.require(actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.OperatorRebound,
                "actual settled typed operator receipt required");
        var settled=(ActionState.Settled)actual.state();
        var completion=((ActionState.OperatorRebound)settled.settlement()).observation();
        completion.validate(actual.command(),settled.attempt(),settled.dispatch());
        StrictJson.require(actual.command().expectation() instanceof CommandExpectation.OperatorRebind,"original operator expectation required");
        var expectation=((CommandExpectation.OperatorRebind)actual.command().expectation()).expected();
        expectation.validateCommand(actual.command());expectation.validateCompletion(completion);
        var frame=semantic.frame();var nativeIdentity=frame.frame().identity();
        StrictJson.require(actual.command().origin().machineId().equals(owner.machineId())&&actual.command().origin().game().equals(owner.game())
                &&actual.command().sessionId().equals(owner.sessionId())&&frame.machineId().equals(owner.machineId())&&frame.game().equals(owner.game())
                &&frame.frame().episodeRunId().equals(completion.episodeRunId())&&nativeIdentity.player().longValueExact()==completion.request().characterId()
                &&frame.frame().revision().equals(completion.afterRevision())&&nativeIdentity.nativeRevision().equals(completion.nativeRevision())
                &&nativeIdentity.dateRaw().longValueExact()==completion.dateRaw()&&semantic.originalDriver().equals(completion.originals().afterDriver())
                &&semantic.semantic().equals(completion.originals().reboundNative()),"operator rebound full SEM differs from its exact actual receipt/Driver/subject/frame");
        StrictJson.require(actual.settled()&&!actual.visibleGameplay()&&!actual.eligibleAdvance()&&actual.applied().isEmpty(),"operator rebind grants no gameplay/day/ordinary-cycle credit");
        return completion;
    }
    public record CompletedCycleProof(long completedCycles, SemanticEvidence semantic, String cycleStateDigest) {
        public CompletedCycleProof {
            StrictJson.safe(completedCycles, 0); Objects.requireNonNull(semantic);
            org.xar.ck3.control.continuity.writer.WriterContracts.requireDigest(cycleStateDigest);
        }
        public ObservationIdentity frame() { return semantic.frame(); }
    }
    /** Root supplies the actual private lifecycle producer + original journal implementation. */
    @FunctionalInterface public interface EpisodeContinuation {
        /** Separate actual transported-current producer; the strict same-session path remains unchanged. */
        default ContinuityBatchJournal.AdmittedEpisode continueTransportedSameGame(SessionIdentity owner,ActionReceipt parent,
                ContinuityBatchJournal.ReboundTransport transport,Instant deadline)throws IOException {
            throw new IOException("actual private transported episode admission is unavailable");
        }
        /** Only the original Journal may issue an admitted same-Game episode; legacy DATA proof ports fail closed. */
        default ContinuityBatchJournal.AdmittedEpisode continueAdmittedSameGame(SessionIdentity owner,ActionReceipt parent,Instant deadline)throws IOException {
            throw new IOException("actual private journal episode admission is unavailable");
        }
        CompletedCycleProof continueSameGame(SessionIdentity owner,ActionReceipt actualLifecycleReceipt,Instant deadline) throws IOException;
    }
    /** The sole collector captures full post-lifecycle SEM without planning queries or Driver/history publication. */
    @FunctionalInterface public interface PostLifecycleSemanticCapture {
        SemanticEvidence capture(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
                SessionIdentity owner,ActionReceipt actualParent,Instant deadline) throws IOException;
    }
    public record Ready(PlanningRequest request, CheckpointEligibility checkpointEligibility,
            Optional<BatchRequest> offlineAnalysis, Optional<SemanticEvidence> semanticEvidence) implements Observation {
        public Ready {
            Objects.requireNonNull(request); Objects.requireNonNull(checkpointEligibility); Objects.requireNonNull(offlineAnalysis); Objects.requireNonNull(semanticEvidence);
            semanticEvidence.ifPresent(proof -> StrictJson.require(proof.frame().equals(request.before()), "semantic evidence must bind actual current frame"));
        }
    }
    public record Waiting(String reason, ExactRef evidence) implements Observation {
        public Waiting { StrictJson.text(reason); Objects.requireNonNull(evidence); }
    }
    public record ObservationUnavailable(String reason, ExactRef evidence) implements Observation {
        public ObservationUnavailable { StrictJson.text(reason); Objects.requireNonNull(evidence); }
    }
    @FunctionalInterface public interface ObservationPort {
        /** Real complete observation assembler; no Python planner or fallback. */
        Observation observe(SessionIdentity expected, Instant deadline) throws IOException, InterruptedException;
        /** Default deny. Only this installed Root observation source may reopen its private canonical operator execution. */
        default SemanticEvidence requireOperatorRebound(SessionIdentity expected,ActionReceipt actual,Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(expected);Objects.requireNonNull(actual);Objects.requireNonNull(deadline);
            throw new IOException("installed actual operator rebound source is unavailable");
        }
        /** The actual private source may reveal its retained successor obligation before ordinary planning/quarantine gates.
         * Empty performs no query by default and grants no permission to retry any UNKNOWN. */
        default Optional<PendingSuccessorUi> pendingSuccessorUi(SessionIdentity expected,Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(expected);Objects.requireNonNull(deadline);return Optional.empty();
        }
        /** The installed NS adapter reopens a new actual current scope; historical transport knowledge is never a Native permission. */
        default Optional<PendingSuccessorUi> pendingTransportSuccessorUi(SessionIdentity expected,
                ContinuityBatchJournal.ReboundTransport transport,Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(expected);Objects.requireNonNull(transport);Objects.requireNonNull(deadline);
            throw new IOException("actual private transported pending successor source is unavailable");
        }
    }
    public record TurnFacts(boolean visibleGameplay, boolean eligibleAdvance, List<ExactRef> independentEvidence) {
        public TurnFacts {
            independentEvidence = List.copyOf(independentEvidence);
            independentEvidence.forEach(ref -> StrictJson.require(ref.bytes() > 0, "independent native evidence must be nonempty"));
            StrictJson.require(!visibleGameplay || !independentEvidence.isEmpty(), "visible gameplay requires original independent native evidence");
            StrictJson.require(!eligibleAdvance || visibleGameplay, "eligible advance requires visible native gameplay");
        }
    }
    public record AnalysisCompletion(String batchId, List<ExactRef> persistedReviews, ExactRef publishedKnowledge) {
        public AnalysisCompletion {
            org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.batchId(batchId);
            persistedReviews = org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.references(persistedReviews, 4609);
            org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.absolute(publishedKnowledge);
            StrictJson.require(publishedKnowledge.bytes() > 0, "actual published knowledge evidence required");
        }
    }
    public record AnalysisTicket(String batchId, CompletionStage<AnalysisCompletion> completion) {
        public AnalysisTicket { org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.batchId(batchId); Objects.requireNonNull(completion); }
    }
    @FunctionalInterface public interface OfflineAnalysisPort {
        /** Persist work before queue ACK; bounded executor uses the original analyzer and completes only after durable knowledge publication. */
        AnalysisTicket enqueue(BatchRequest captured) throws IOException;
    }
    public enum JournalKind { BATCH_STARTED, SAVE_CONFIRMED, BATCH_DEFERRED, BATCH_INTERRUPTED, BATCH_FINISHED, WORKER_RESTART_CAPTURE }
    public record JournalInput(SessionIdentity session, String batchId, JournalKind kind,
            Optional<ObservationIdentity> frame, Optional<CheckpointPair> pair, Optional<CompletedCycleProof> completedCycleProof, List<ExactRef> evidence) {
        public JournalInput {
            Objects.requireNonNull(session); org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.batchId(batchId);
            Objects.requireNonNull(kind); Objects.requireNonNull(frame); Objects.requireNonNull(pair); Objects.requireNonNull(completedCycleProof); evidence = List.copyOf(evidence);
            StrictJson.require(kind == JournalKind.SAVE_CONFIRMED || pair.isEmpty(), "only a shared confirmed checkpoint can be attached");
            StrictJson.require(kind == JournalKind.SAVE_CONFIRMED || completedCycleProof.isEmpty(), "non-SAVE metadata cannot carry a new cycle claim");
            if (kind == JournalKind.SAVE_CONFIRMED) StrictJson.require(pair.isPresent() && completedCycleProof.isPresent(), "confirmed paired SAVE and real completed-cycle proof are required");
        }
    }
    public record JournalCommit(ExactRef persistedHead, long committedSavedDays) {
        public JournalCommit { Objects.requireNonNull(persistedHead); StrictJson.safe(committedSavedDays, 0); StrictJson.require(persistedHead.bytes() > 0, "actual persisted writer head required"); }
    }
    @FunctionalInterface public interface BatchJournal {
        /** Only the original private saved-material issuer can qualify a real saved frontier; no new SAVE/commit. */
        default JournalCommit acceptPublicCheckpoint(SessionIdentity owner,Captured actual)throws IOException {
            throw new IOException("actual captured public checkpoint adoption is unavailable");
        }
        /** Borrowed Root execution must never open a nested writer lock. */
        default JournalCommit acceptPublicCheckpoint(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,SessionIdentity owner,Captured actual)throws IOException {
            throw new IOException("actual borrowed captured checkpoint adoption is unavailable");
        }
        /** No default source or constructor DATA can rebind the retained ordinary cycle. */
        default void acceptOperatorRebound(SessionIdentity owner,ActionReceipt actual,SemanticEvidence semantic)throws IOException {
            throw new IOException("actual operator cycle rebind authority is unavailable");
        }
        /** Sole ContinuityWriter adapter runs its real reducer and revalidation inside its existing writer lock. */
        JournalCommit commit(JournalInput input) throws IOException;
        /** Absent means that the original cycle producer has not been adopted; it never grants zero cycles. */
        default Optional<CompletedCycleProof> cycleProof(SessionIdentity session, SemanticEvidence semantic) throws IOException { return Optional.empty(); }
        /** Persist the classified original receipt before collecting its after-SEM. */
        default void retainCycle(SessionIdentity session, ActionReceipt receipt) throws IOException { throw new IOException("ordinary cycle producer unavailable"); }
        /** Actual AUTO classification plus a fresh archived SEM, under the existing sole writer lock. */
        default CompletedCycleProof settleCycle(SessionIdentity session, ActionReceipt receipt, SemanticEvidence semantic) throws IOException {
            throw new IOException("ordinary cycle producer unavailable");
        }
    }
}
