package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Assembly supplies real source-bound observers; none may submit except NativeActionPort. */
public final class ActionPorts {
    private ActionPorts() { }
    @FunctionalInterface public interface GuardPort { GuardEvidence verify(org.xar.ck3.control.continuity.writer.WriterContracts.Head actualLockedHead, ActionCommand command); }
    /** Import source-bound pending domain state under the original lock before the first durable action intent. */
    @FunctionalInterface public interface IntentPreparationPort {
        void prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session originalSession, ActionCommand command);
    }
    /** Runs once for a new durable native attempt, including UNKNOWN and rejection, under its original writer Session. */
    @FunctionalInterface public interface AttemptCompletionPort {
        void afterAttempt(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session originalSession, ActionReceipt actualCanonicalReceipt);
    }
    /** Actual Root READ queue gate; it may only return clear or throw ReadPublicationRequiredException. It never publishes or submits. */
    @FunctionalInterface public interface IntentBarrierPort {
        void check(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session originalSession, ActionCommand command);
    }
    /** Only registered, migrated operations may produce a native primitive. A composite is never passed through as a step. */
    @FunctionalInterface public interface PreparationPort {
        NativeRequest prepare(ActionCommand command);
        /** Actual installed read-only scope gate. A source without such a scope has nothing to reject. */
        default void requireOutsideReadOnlyScope(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                ActionCommand command) { Objects.requireNonNull(same); Objects.requireNonNull(command); }
        /** Only the private original owner may bind the already completed query to this one observer call. */
        default PostconditionResult observeOriginalDirectWindowQuery(
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ActionReceipt actualCanonicalPending,
                DirectFixedWindowQueryContinuation actual, DirectWindowQueryWork observer)
                throws java.io.IOException, InterruptedException {
            throw new java.io.IOException("actual original direct-window query source is unavailable");
        }

        /** Only the identical installed operator source may open its original read-only continuation. */
        default PostconditionResult observeOperatorReconciliation(
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session originalSession,
                ActionReceipt actualCanonicalPending, java.time.Instant observationDeadline, OperatorReconciliationWork observer)
                throws java.io.IOException, InterruptedException {
            throw new java.io.IOException("actual original operator reconciliation source is unavailable");
        }
        /** Only the identical installed source preparer may admit an explicit original protocol identity. */
        default void requireProtocolIdentity(ActionCommand command) {
            StrictJson.require(Objects.requireNonNull(command).protocolIdentity() instanceof ProtocolRequestIdentity.BodyDerived,
                    "explicit original protocol identity is not admitted by this source preparer");
        }
        /** Request-aware native producers override this for real nonce==request_id contracts. */
        default NativeRequest prepare(ActionCommand command, String requestId) { return prepare(command); }
        /** Source-qualified preflight may borrow the existing lock; it must not construct another writer or submit. */
        default NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session originalSession, ActionCommand command, String requestId) {
            java.util.Objects.requireNonNull(originalSession); return prepare(command, requestId);
        }
    }
    /** Work carries no Complete or synthetic old-player frame; the actual source owns the physical read scope. */
    @FunctionalInterface public interface OperatorReconciliationWork { PostconditionResult apply(); }
    @FunctionalInterface public interface DirectWindowQueryWork { PostconditionResult apply(); }
    @FunctionalInterface public interface PostconditionPort {
        PostconditionResult observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch);
    }
    /** The original canonical primitive is observed inside one actual physical source/Driver lease. No submit permission. */
    @FunctionalInterface public interface ReconciliationObservationPort {
        PostconditionResult observe(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session originalSession,
                ActionReceipt actualCanonicalPending, java.time.Instant observationDeadline, ReconciliationWork observer)
                throws java.io.IOException, InterruptedException;
    }
    @FunctionalInterface public interface ReconciliationWork {
        PostconditionResult apply(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actualData,
                ReconciliationIdentity actualIdentity, GuardEvidence actualObservationGuard);
    }
    public record OperatorRebindObserved(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.Completion observation) implements PostconditionResult {
        public OperatorRebindObserved { Objects.requireNonNull(observation); }
    }
    public record NativeSourceObserved(org.xar.ck3.control.application.effects.coa.NativeSourceObservation observation) implements PostconditionResult {
        public NativeSourceObserved { Objects.requireNonNull(observation); }
    }
    public record CompositeNoGameplayWriteObserved(CompositeNoGameplayWriteObservation observation) implements PostconditionResult {
        public CompositeNoGameplayWriteObserved { Objects.requireNonNull(observation); }
    }
    public record LifeControlPrefixInterruptedObserved(org.xar.ck3.control.application.advance.LifeControlPrefixInterruption observation) implements PostconditionResult {
        public LifeControlPrefixInterruptedObserved { Objects.requireNonNull(observation); }
    }
    public record NormalExitPhaseObserved(org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation observation) implements PostconditionResult {
        public NormalExitPhaseObserved { Objects.requireNonNull(observation); }
    }
    public record DirectFixedWindowObserved(org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation.Completion completion) implements PostconditionResult {
        public DirectFixedWindowObserved { Objects.requireNonNull(completion); }
    }
    public record PauseObserved(ActionState.EffectObservation observation) implements PostconditionResult {
        public PauseObserved { Objects.requireNonNull(observation); }
    }
    public record ControlSequenceObserved(org.xar.ck3.control.application.effects.control.ControlSequenceObservation observation) implements PostconditionResult {
        public ControlSequenceObserved { Objects.requireNonNull(observation); }
    }
    public sealed interface PostconditionResult permits FixtureStartObserved, FixtureBusinessObserved, DirectFixedWindowObserved, PauseObserved, ControlSequenceObserved, EffectObserved, RejectionObserved, ControlObserved, CompositeControlObserved, FrontendObserved, GameplayEntryObserved, LifecycleObserved, TerminalObserved, CompositeRejectionObserved, LifecycleControlObserved, SwaySchedulerObserved, FamilySendObserved, NativeSourceObserved, NormalExitPhaseObserved, OperatorRebindObserved, CompositeNoGameplayWriteObserved, LifeControlPrefixInterruptedObserved, Pending { }
    public record FixtureStartObserved(FixtureStartObservation observation) implements PostconditionResult {public FixtureStartObserved {Objects.requireNonNull(observation);}}
    public record FixtureBusinessObserved(FixtureBusinessObservation observation) implements PostconditionResult {public FixtureBusinessObserved {Objects.requireNonNull(observation);}}
    /** An observed outgoing request has no relationship, payment, alliance, game-day or SAVE credit. */
    public record FamilySendObserved(org.xar.ck3.control.application.effects.family.FamilySendObservation observation) implements PostconditionResult {
        public FamilySendObserved { Objects.requireNonNull(observation); }
    }
    public record SwaySchedulerObserved(org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletion proof) implements PostconditionResult { public SwaySchedulerObserved { Objects.requireNonNull(proof); } }
    public record LifecycleControlObserved(LifecycleControlObservation observation) implements PostconditionResult { public LifecycleControlObserved { Objects.requireNonNull(observation); } }
    public record TerminalObserved(ActionTerminalObservation observation) implements PostconditionResult { public TerminalObserved { Objects.requireNonNull(observation); } }
    public record CompositeRejectionObserved(String reason, List<CompositeExecution.Child> children, List<ExactRef> evidence) implements PostconditionResult {
        public CompositeRejectionObserved {
            StrictJson.text(reason); children = List.copyOf(children); evidence = List.copyOf(evidence);
            StrictJson.require(!children.isEmpty() && evidence.size()<=64 && evidence.stream().distinct().count()==evidence.size()
                    && evidence.stream().allMatch(ref->ref.bytes()>0), "actual canonical rejected children and finite unique original evidence required");
        }
        public CompositeRejectionObserved(String reason,List<CompositeExecution.Child> children){this(reason,children,List.of());}
    }
    public record LifecycleObserved(org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof proof) implements PostconditionResult { public LifecycleObserved { Objects.requireNonNull(proof); } }
    public record EffectObserved(ActionState.EffectObservation observation) implements PostconditionResult { public EffectObserved { Objects.requireNonNull(observation); } }
    public record RejectionObserved(ActionState.Rejected rejection) implements PostconditionResult { public RejectionObserved { Objects.requireNonNull(rejection); } }
    public record ControlObserved(ActionState.ControlApplied observation) implements PostconditionResult { public ControlObserved { Objects.requireNonNull(observation); } }
    public record CompositeControlObserved(CompositeControlObservation observation) implements PostconditionResult { public CompositeControlObserved { Objects.requireNonNull(observation); } }
    public record FrontendObserved(FrontendEffectObservation observation) implements PostconditionResult { public FrontendObserved { Objects.requireNonNull(observation); } }
    public record GameplayEntryObserved(FrontendGameplayObservation observation) implements PostconditionResult { public GameplayEntryObserved { Objects.requireNonNull(observation); } }
    public record Pending(String reason, List<ExactRef> evidence) implements PostconditionResult {
        public Pending { StrictJson.text(reason); evidence = List.copyOf(evidence); }
    }
    /** Exact original dependencies consumed by the existing failed-read archive reader; DATA only. */
    public record FailedReadOriginals(List<ExactRef> references) {
        public FailedReadOriginals { references = List.copyOf(references); }
    }
    /** Keeps full native packets outside bounded canonical ledger metadata, with original evidence and byte integrity. */
    public interface OutcomeArchive extends org.xar.ck3.control.contracts.presentation.PresentationOriginals {
        /** Existing original DATA only. It neither constructs a PlanningReadReceipt nor grants read/history authority. */
        default void verifyReadAttemptOriginals(PlanningReadRequest request, String actualRequestId,
                PlanningReadGuard before, NativeRequest prepared, NativeActionPort.DispatchOutcome original) {
            throw new UnsupportedOperationException("original failed-read protocol validation is unavailable");
        }
        /** Replays the same failed READ's actual guards, original wire and writer head; no Known or effect credit. */
        default void verifyReadFailureOriginals(PlanningReadFailure original) {
            throw new UnsupportedOperationException("actual failed-read after observation validation is unavailable");
        }

        /** Runs the original failed-read readers and returns all actual/source dependencies they consumed. */
        default FailedReadOriginals loadFailedReadOriginals(PlanningReadRequest request, String actualRequestId,
                PlanningReadGuard before, NativeRequest prepared, NativeActionPort.DispatchOutcome original,
                Optional<ExactRef> observedFailureReference) {
            throw new UnsupportedOperationException("actual failed-read original dependency capture is unavailable");
        }


        default ExactRef preserveFrontendWindowCaptureRequest(org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest actual) { throw new UnsupportedOperationException("frontend capture request archive is unavailable"); }
        default org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest loadFrontendWindowCaptureRequest(ExactRef original) { throw new UnsupportedOperationException("frontend capture request archive is unavailable"); }
        default ExactRef frontendWindowCaptureRequestReferenceOf(org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest actual) { throw new UnsupportedOperationException("frontend capture request archive is unavailable"); }
        default ExactRef preserveFrontendWindowCaptureOutcome(org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome actual) { throw new UnsupportedOperationException("frontend capture outcome archive is unavailable"); }
        default org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome loadFrontendWindowCaptureOutcome(ExactRef original) { throw new UnsupportedOperationException("frontend capture outcome archive is unavailable"); }
        default ExactRef frontendWindowCaptureOutcomeReferenceOf(org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome actual) { throw new UnsupportedOperationException("frontend capture outcome archive is unavailable"); }

        /** Separate physical-plane DATA. No native-pipe packet or ACK parser is used. */
        default ExactRef preservePresentationOutcome(org.xar.ck3.control.contracts.presentation.OriginalOutcome actual) {
            throw new UnsupportedOperationException("presentation outcome archive is unavailable");
        }
        default org.xar.ck3.control.contracts.presentation.OriginalOutcome loadPresentationOutcome(ExactRef original) {
            throw new UnsupportedOperationException("presentation outcome archive is unavailable");
        }
        default ExactRef presentationOutcomeReferenceOf(org.xar.ck3.control.contracts.presentation.OriginalOutcome actual) {
            throw new UnsupportedOperationException("presentation outcome archive is unavailable");
        }
        default ExactRef preservePresentationObservation(org.xar.ck3.control.contracts.presentation.PresentationObservation actual) {
            throw new UnsupportedOperationException("presentation observation archive is unavailable");
        }
        default org.xar.ck3.control.contracts.presentation.PresentationObservation loadPresentationObservation(ExactRef original) {
            throw new UnsupportedOperationException("presentation observation archive is unavailable");
        }
        default ExactRef presentationObservationReferenceOf(org.xar.ck3.control.contracts.presentation.PresentationObservation actual) {
            throw new UnsupportedOperationException("presentation observation archive is unavailable");
        }

        /** Optional real immutable CAS lookup; old adapters explicitly lack this capability. */
        default ExactRef materialReference(String sha256, long bytes) { throw new IllegalStateException("actual immutable material digest lookup is unavailable"); }
        /** A live borrowed view must verify the exact original writer, owning thread and held lock. */
        default OutcomeArchive withSession(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
            throw new IllegalStateException("same-writer archive session binding is unavailable");
        }
        /** Explicit dynamic scope for authority callbacks; implementations must restore the previous binding in finally. */
        default <T> T inSession(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, java.util.function.Function<OutcomeArchive, T> work) {
            throw new IllegalStateException("same-writer archive callback scope is unavailable");
        }
        ExactRef preserve(NativeActionPort.DispatchOutcome original);
        NativeActionPort.DispatchOutcome load(ExactRef original);
        ExactRef preserveRequest(NativeRequest original);
        NativeRequest loadRequest(ExactRef original);
        /** Read-only lookup, fails if the original has not already been durably archived. */
        ExactRef referenceOf(NativeActionPort.DispatchOutcome original);
        ExactRef requestReferenceOf(NativeRequest original);
        ExactRef preserveRead(PlanningReadReceipt original);
        /** Successful ordinary planning observations only. Unmodified implementations retain strong publication. */
        default ExactRef preservePlanningRead(PlanningReadReceipt original) { return preserveRead(original); }
        PlanningReadReceipt loadRead(ExactRef original);
        ExactRef readReferenceOf(PlanningReadReceipt original);
        ExactRef preserveRecord(ActionRecord original);
        ActionRecord loadRecord(ExactRef original);
        ExactRef recordReferenceOf(ActionRecord original);
        ExactRef preserveReceipt(ActionReceipt original);
        ActionReceipt loadReceipt(ExactRef original);
        ExactRef receiptReferenceOf(ActionReceipt original);
        ExactRef preserveMaterial(RawJson original);
        RawJson loadMaterial(ExactRef original);
        /** Existing complete Driver/auxiliary/manifest material only; ordinary/native token limits are unchanged. */
        default RawJson loadFullMaterial(ExactRef original) {
            throw new UnsupportedOperationException("complete original material reading is unavailable");
        }
        ExactRef materialReferenceOf(RawJson original);
        ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original);
        byte[] loadNativeFrame(ExactRef original);
        /** Exact retained native wire bytes, including HELLO. This is read access, never source or domain qualification.
         * Implementations must bind the actual owning writer Session and enforce original pin, role, identity and byte bounds.
         * Historical adapters without this distinct capability fail explicitly; JSON material decoding is not a substitute.
         */
        default byte[] readOriginalPacket(ExactRef original) {
            throw new IllegalStateException("exact retained native packet reading is unavailable");
        }
    }
    /** Decode and bind retained original evidence using the fixed domain registry; constructors do not grant writer qualification. */
    @FunctionalInterface public interface RecordedEvidenceVerifier { void verify(org.xar.ck3.control.continuity.writer.WriterContracts.Head actualLockedHead, ActionReceipt proposed); }
}


