package org.xar.ck3.control.application.action;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** UNKNOWN has no replay transition. ACK and independently observed game effect remain separate facts. */
public sealed interface ActionState permits ActionState.IntentDurable, ActionState.Submitting, ActionState.AckReceived,
        ActionState.Unknown, ActionState.Settled, ActionState.RejectedBeforeDispatch, ActionState.IntentAbandoned, ActionState.CompositeRunning,
        ActionState.CompositeUnknown, ActionState.CompositeSettled, PhysicalActionState {
    record Attempt(String requestId, Instant submittedAt, GuardEvidence guard, NativeRequest preparedRequest) {
        public Attempt { StrictJson.text(requestId); Objects.requireNonNull(submittedAt); Objects.requireNonNull(guard); Objects.requireNonNull(preparedRequest); }
    }
    record IntentDurable() implements ActionState { }
    /** Source-owned canonical proof of abandonment before Submitting; no Attempt, packet, ACK or effect is invented. */
    record IntentAbandoned(ExactRef originalIntentRecord, ExactRef originalActionHead) implements ActionState {
        public IntentAbandoned {
            Objects.requireNonNull(originalIntentRecord); Objects.requireNonNull(originalActionHead);
            StrictJson.require(originalIntentRecord.bytes() > 0 && originalActionHead.bytes() > 0,
                    "abandoned Intent requires its actual original record and complete action-head prefix");
        }
    }
    record Submitting(Attempt attempt) implements ActionState { public Submitting { Objects.requireNonNull(attempt); } }
    record AckReceived(Attempt attempt, NativeActionPort.AckReceived dispatch) implements ActionState {
        public AckReceived { Objects.requireNonNull(attempt); Objects.requireNonNull(dispatch); matching(attempt, dispatch); }
    }
    record Unknown(Optional<Attempt> attempt, Optional<NativeActionPort.DispatchOutcome> dispatch, String reason, List<ExactRef> evidence) implements ActionState {
        public Unknown {
            attempt = Objects.requireNonNull(attempt); dispatch = Objects.requireNonNull(dispatch); StrictJson.text(reason);
            evidence = List.copyOf(evidence); if (dispatch.isPresent()) { StrictJson.require(attempt.isPresent(), "dispatch requires original attempt"); matching(attempt.orElseThrow(), dispatch.orElseThrow()); }
        }
    }
    sealed interface Settlement permits FixtureStarted, FixtureBusinessCompleted, DirectFixedWindowCompleted, PauseConfirmed, ControlSequenceCompleted, Applied, Rejected, ControlApplied, CompositeControlApplied, FrontendApplied, GameplayEntered, LifecycleApplied, NonAppliedTerminal, CompositeRejected, LifecycleControlApplied, SwaySchedulerCompleted, FamilySendConfirmed, NativeSourceCompleted, NormalExitPhaseConfirmed, OperatorRebound, CompositeNoGameplayWrite, LifeControlPrefixInterrupted { }
    record FixtureStarted(FixtureStartObservation observation) implements Settlement {public FixtureStarted {Objects.requireNonNull(observation);}}
    record FixtureBusinessCompleted(FixtureBusinessObservation observation) implements Settlement {public FixtureBusinessCompleted {Objects.requireNonNull(observation);}}
    /** A real native pause and independent Push prove only the paused control state. */
    /** Finite execution completion; no gameplay, Closed, day or SAVE credit. */
    record DirectFixedWindowCompleted(org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation.Completion completion) implements Settlement {
        public DirectFixedWindowCompleted { Objects.requireNonNull(completion); }
    }

    record PauseConfirmed(EffectObservation observation) implements Settlement {
        public PauseConfirmed { Objects.requireNonNull(observation); }
    }
    /** Bounded original pause children and the installed source prove this control sequence. */
    record ControlSequenceCompleted(org.xar.ck3.control.application.effects.control.ControlSequenceObservation observation) implements Settlement {
        public ControlSequenceCompleted { Objects.requireNonNull(observation); }
    }
    /** Identity-only DATA; the installed source must replay native, Driver and Window originals. */
    record OperatorRebound(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.Completion observation) implements Settlement {
        public OperatorRebound { Objects.requireNonNull(observation); }
    }
    record NativeSourceCompleted(org.xar.ck3.control.application.effects.coa.NativeSourceObservation observation) implements Settlement {
        public NativeSourceCompleted { Objects.requireNonNull(observation); }
    }
    record CompositeNoGameplayWrite(CompositeNoGameplayWriteObservation observation) implements Settlement {
        public CompositeNoGameplayWrite { Objects.requireNonNull(observation); }
    }
    record LifeControlPrefixInterrupted(org.xar.ck3.control.application.advance.LifeControlPrefixInterruption observation) implements Settlement {
        public LifeControlPrefixInterrupted { Objects.requireNonNull(observation); }
    }
    record NormalExitPhaseConfirmed(org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation observation) implements Settlement {
        public NormalExitPhaseConfirmed { Objects.requireNonNull(observation); }
    }
    /** DATA only. The fixed family verifier must replay original storage queries and preparation under the same writer. */
    record FamilySendConfirmed(org.xar.ck3.control.application.effects.family.FamilySendObservation observation) implements Settlement {
        public FamilySendConfirmed { Objects.requireNonNull(observation); }
    }
    /** DATA only; the installed Sway domain verifier must replay the actual canonical publication and child history. */
    record SwaySchedulerCompleted(org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletion proof) implements Settlement { public SwaySchedulerCompleted { Objects.requireNonNull(proof); } }
    record LifecycleControlApplied(LifecycleControlObservation observation) implements Settlement { public LifecycleControlApplied { Objects.requireNonNull(observation); } }
    record NonAppliedTerminal(ActionTerminalObservation observation) implements Settlement { public NonAppliedTerminal { Objects.requireNonNull(observation); } }
    /** Every actual child must be a canonical proven rejection/zero-dispatch; no other effect may be erased. */
    record CompositeRejected(String reason, List<CompositeExecution.Child> children, List<ExactRef> evidence) implements Settlement {
        public CompositeRejected {
            StrictJson.text(reason); children = List.copyOf(children); evidence = List.copyOf(evidence);
            StrictJson.require(!children.isEmpty() && evidence.size()<=64 && evidence.stream().distinct().count()==evidence.size()
                    && evidence.stream().allMatch(ref->ref.bytes()>0), "canonical rejected child history and finite unique original evidence required");
        }
        public CompositeRejected(String reason,List<CompositeExecution.Child> children){this(reason,children,List.of());}
    }
    /** Domain proof is revalidated against the actual canonical lifecycle events by its installed archived verifier. */
    record LifecycleApplied(org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof proof) implements Settlement {
        public LifecycleApplied { Objects.requireNonNull(proof); }
        @Override public boolean equals(Object other) { return other instanceof LifecycleApplied value && java.util.Arrays.equals(proof.encode(), value.proof.encode()); }
        @Override public int hashCode() { return java.util.Arrays.hashCode(proof.encode()); }
    }
    record EffectObservation(ObservationIdentity after, G2Source source, String sessionId, String observerSchema,
            List<ExpectedValue> actual, ObservationProvenance provenance, Instant observedAt, ExactRef originalEvidence, List<ExactRef> supportingEvidence) {
        public EffectObservation {
            Objects.requireNonNull(after); Objects.requireNonNull(source); StrictJson.text(sessionId); StrictJson.text(observerSchema);
            actual = List.copyOf(actual); Objects.requireNonNull(provenance); Objects.requireNonNull(observedAt);
            Objects.requireNonNull(originalEvidence); StrictJson.require(originalEvidence.bytes() > 0, "independent original effect evidence required");
            supportingEvidence = List.copyOf(supportingEvidence);
            supportingEvidence.forEach(ref -> StrictJson.require(ref.bytes() > 0, "nonempty durable effect basis required"));
            provenance.validate(after, originalEvidence);
        }
        public EffectObservation(ObservationIdentity after, G2Source source, String sessionId, String observerSchema,
                List<ExpectedValue> actual, String readRequestId, Instant observedAt, ExactRef originalEvidence, List<ExactRef> supportingEvidence) {
            this(after, source, sessionId, observerSchema, actual, new ObservationProvenance.Query(readRequestId), observedAt, originalEvidence, supportingEvidence);
        }
        public EffectObservation(ObservationIdentity after, G2Source source, String sessionId, String observerSchema,
                List<ExpectedValue> actual, ObservationProvenance provenance, Instant observedAt, ExactRef originalEvidence) {
            this(after, source, sessionId, observerSchema, actual, provenance, observedAt, originalEvidence, List.of());
        }
        /** Historical v1 observations have no durable basis; a real verifier must not invent one. */
        public EffectObservation(ObservationIdentity after, G2Source source, String sessionId, String observerSchema,
                List<ExpectedValue> actual, String readRequestId, Instant observedAt, ExactRef originalEvidence) {
            this(after, source, sessionId, observerSchema, actual, readRequestId, observedAt, originalEvidence, List.of());
        }
    }
    record Applied(EffectObservation observation) implements Settlement { public Applied { Objects.requireNonNull(observation); } }
    record FrontendApplied(FrontendEffectObservation observation) implements Settlement { public FrontendApplied { Objects.requireNonNull(observation); } }
    record GameplayEntered(FrontendGameplayObservation observation) implements Settlement { public GameplayEntered { Objects.requireNonNull(observation); } }
    record CompositeControlApplied(CompositeControlObservation observation) implements Settlement { public CompositeControlApplied { Objects.requireNonNull(observation); } }
    /** Clock/sentinel state is observed through a fresh registered native Status query, without inventing a semantic revision. */
    record ControlApplied(PlanningReadReceipt read, List<PlanningReadReceipt> supportingReads, String observerSchema, List<ExpectedValue> actual,
            Optional<ReconciledControlAck> reconciledAck) implements Settlement {
        public ControlApplied { Objects.requireNonNull(read); supportingReads = List.copyOf(supportingReads); StrictJson.text(observerSchema); actual = List.copyOf(actual); reconciledAck = Objects.requireNonNull(reconciledAck); }
        public ControlApplied(PlanningReadReceipt read, List<PlanningReadReceipt> supportingReads, String observerSchema, List<ExpectedValue> actual) { this(read, supportingReads, observerSchema, actual, Optional.empty()); }
        public ControlApplied(PlanningReadReceipt read, String observerSchema, List<ExpectedValue> actual) { this(read, List.of(), observerSchema, actual); }
    }
    /** Only a real native terminal rejection can create this; a currently absent effect cannot. */
    record Rejected(String requestId, String reason, ExactRef originalEvidence) implements Settlement {
        public Rejected { StrictJson.text(requestId); StrictJson.text(reason); Objects.requireNonNull(originalEvidence); StrictJson.require(originalEvidence.bytes() > 0, "native rejection proof required"); }
    }
    record Settled(Attempt attempt, NativeActionPort.DispatchOutcome dispatch, Settlement settlement) implements ActionState {
        public Settled { Objects.requireNonNull(attempt); Objects.requireNonNull(dispatch); Objects.requireNonNull(settlement); matching(attempt, dispatch); }
    }
    record RejectedBeforeDispatch(Attempt attempt, NativeActionPort.RejectedBeforeDispatch dispatch) implements ActionState {
        public RejectedBeforeDispatch { Objects.requireNonNull(attempt); Objects.requireNonNull(dispatch); matching(attempt, dispatch); }
    }
    record CompositeRunning(CompositeExecution execution) implements ActionState { public CompositeRunning { Objects.requireNonNull(execution); } }
    record CompositeUnknown(CompositeExecution execution, String reason, List<ExactRef> evidence) implements ActionState {
        public CompositeUnknown { Objects.requireNonNull(execution); StrictJson.text(reason); evidence = List.copyOf(evidence); }
    }
    record CompositeSettled(CompositeExecution execution, Settlement settlement) implements ActionState {
        public CompositeSettled { Objects.requireNonNull(execution); Objects.requireNonNull(settlement); }
    }
    private static void matching(Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        StrictJson.require(attempt.requestId().equals(dispatch.requestId()), "native outcome must match the original request ID");
    }
}
