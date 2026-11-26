package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Root installs this once with its actual archived Driver decoder; every method is archive-only. */
public final class LifeAdvanceRootReplay implements LifeAdvanceEvidence.EntryFrameReader,
        LifeAdvanceEvidence.BoundFrameVerifier, NativeRecordedEvidenceVerifier.ArchivedVerifier {
    @FunctionalInterface public interface PreparedCursorVerifier {
        void verify(WriterContracts.Head head,ActionReceipt cursor,ActionPorts.OutcomeArchive archive);
    }
    private final Optional<PreparedCursorVerifier> preparedParentVerifier;
    private final Optional<PreparedCursorVerifier> preparedCursorVerifier;
    private final NativeEffectEvidence.FrameLoader frames;
    private final AdvanceClockArchivedReplay timeline;
    private final java.util.function.Supplier<Optional<CompositeOperatorQuarantineSource>> operatorSource;
    private final java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> operatorSession;

    public LifeAdvanceRootReplay(NativeEffectEvidence.FrameLoader actualFrames) {
        this(actualFrames,Optional::empty,()->{throw new IllegalStateException("actual Life operator writer session is not installed");});
    }
    public LifeAdvanceRootReplay(NativeEffectEvidence.FrameLoader actualFrames,
            java.util.function.Supplier<Optional<CompositeOperatorQuarantineSource>> actualOperatorSource,
            java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> actualOperatorSession) {
        this.preparedCursorVerifier=Optional.empty();this.preparedParentVerifier=Optional.empty();
        this.frames = Objects.requireNonNull(actualFrames);
        this.timeline = new AdvanceClockArchivedReplay(actualFrames);
        this.operatorSource=Objects.requireNonNull(actualOperatorSource);this.operatorSession=Objects.requireNonNull(actualOperatorSession);
    }

    public LifeAdvanceRootReplay(NativeEffectEvidence.FrameLoader actualFrames,
            java.util.function.Supplier<Optional<CompositeOperatorQuarantineSource>> actualOperatorSource,
            java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> actualOperatorSession,
            PreparedCursorVerifier actualPreparedCursorVerifier){
        this.frames=Objects.requireNonNull(actualFrames);this.timeline=new AdvanceClockArchivedReplay(actualFrames);
        this.operatorSource=Objects.requireNonNull(actualOperatorSource);this.operatorSession=Objects.requireNonNull(actualOperatorSession);
        this.preparedCursorVerifier=Optional.of(Objects.requireNonNull(actualPreparedCursorVerifier));this.preparedParentVerifier=Optional.empty();
    }
    public LifeAdvanceRootReplay(NativeEffectEvidence.FrameLoader actualFrames,
            java.util.function.Supplier<Optional<CompositeOperatorQuarantineSource>> actualOperatorSource,
            java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> actualOperatorSession,
            PreparedCursorVerifier actualCursor,PreparedCursorVerifier actualParent){
        this.frames=Objects.requireNonNull(actualFrames);this.timeline=new AdvanceClockArchivedReplay(actualFrames);
        this.operatorSource=Objects.requireNonNull(actualOperatorSource);this.operatorSession=Objects.requireNonNull(actualOperatorSession);
        this.preparedCursorVerifier=Optional.of(Objects.requireNonNull(actualCursor));this.preparedParentVerifier=Optional.of(Objects.requireNonNull(actualParent));
    }
    public LifeAdvanceRootReplay(NativeEffectEvidence.FrameLoader actualFrames,
            java.util.function.Supplier<Optional<CompositeOperatorQuarantineSource>> actualOperatorSource,
            java.util.function.Supplier<org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session> actualOperatorSession,
            PreparedCursorVerifier actualCursor,PreparedCursorVerifier actualParent,
            AdvancePrimitiveArchivedReplay.ZeroCancellationVerifier actualZeroCancellationVerifier) {
        this.frames=Objects.requireNonNull(actualFrames);
        this.timeline=new AdvanceClockArchivedReplay(actualFrames,Objects.requireNonNull(actualZeroCancellationVerifier));
        this.operatorSource=Objects.requireNonNull(actualOperatorSource);this.operatorSession=Objects.requireNonNull(actualOperatorSession);
        this.preparedCursorVerifier=Optional.of(Objects.requireNonNull(actualCursor));this.preparedParentVerifier=Optional.of(Objects.requireNonNull(actualParent));
    }
    public NativeRecordedEvidenceVerifier.Binding binding(OperationKey exactOperation, ExactRef actualDefinition) {
        require(LifeAdvanceComposite.accepts(exactOperation.value()), "life archived verifier requires one exact registered operation");
        return new NativeRecordedEvidenceVerifier.Binding(exactOperation, actualDefinition, this);
    }

    @Override public Optional<AdvanceObservationPort.Frame> read(ActionCommand parent, GuardEvidence guard,
            ActionPorts.OutcomeArchive archive) {
        require(parent.origin().acceptsGuard(guard.origin()) && guard.observed().equals(parent.before())
                && guard.source().equals(parent.source()) && guard.sessionId().equals(parent.sessionId())
                && guard.operation().equals(parent.operation()), "archived life entry guard crossed the original authority");
        // Old receipts remain queryable and UNKNOWN. Missing complete originals do not authorize
        // synthesizing the old public revision, episode, Driver history or a new native submission.
        if (guard.supportingEvidence().isEmpty()) return Optional.empty();
        return Optional.of(push(RootGuardEvidence.loadFrame(guard, archive, frames)));
    }

    @Override public Optional<AdvanceObservationPort.Frame> readChild(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        var complete = AdvancePrimitiveEvidence.load(child, archive, frames);
        var effect = ActionEffects.observation(child).orElseThrow(() -> new IllegalArgumentException("child has no semantic observation"));
        return Optional.of(new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                effect.provenance(), complete.observedAt(), complete.originalEvidence()));
    }

    @Override public AdvanceObservationPort.Frame rebuild(ActionCommand parent, LifeAdvanceEvidence.FrameRecord retained,
            ActionPorts.OutcomeArchive archive) {
        Complete complete = Objects.requireNonNull(frames.load(
                new NativeEffectEvidence.FrameBasis(retained.nativeFrame(), retained.driverFacts()), archive));
        AdvanceObservationPort.Frame rebuilt;
        if (retained.provenance() instanceof ObservationProvenance.PhysicalAfterAcknowledgement physical) {
            frames.verifyPhysicalAfterAcknowledgement(physical, complete, archive);
            rebuilt = new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                    physical, complete.observedAt(), complete.originalEvidence());
        } else if (retained.provenance() instanceof ObservationProvenance.FreshSnapshotQuery query) {
            frames.verifyFreshSnapshotQuery(query, complete, archive);
            if (query.basis() instanceof ObservationProvenance.SameGameWatch watch) {
                var originalParent = archive.loadReceipt(watch.originalParentReceipt());
                var originalResume = archive.loadReceipt(watch.originalResumeReceipt());
                require(originalParent.command().equals(parent) && (originalParent.state() instanceof ActionState.CompositeUnknown
                        ||org.xar.ck3.control.application.session.ContinuityBatchJournal.isReadOnlyRunningLifeRecovery(originalParent))
                        && AdvancePrimitives.confirmedResume(originalResume)
                        && archive.receiptReferenceOf(originalParent).equals(watch.originalParentReceipt())
                        && archive.receiptReferenceOf(originalResume).equals(watch.originalResumeReceipt())
                        && originalParent.bodySha256().equals(ActionCodec.bodySha256(parent))
                        && ActionTransitions.composite(originalParent.state()).orElseThrow().children().stream().filter(child ->
                            child.actionId().equals(originalResume.command().actionId()) && child.bodySha256().equals(originalResume.bodySha256())).count() == 1,
                        "same-game watch basis does not bind the exact original parent/resume receipts");
                if(originalParent.state() instanceof ActionState.CompositeRunning running) {
                    var last=running.execution().children().getLast();
                    require(last.actionId().equals(originalResume.command().actionId())&&last.bodySha256().equals(originalResume.bodySha256()),
                            "running Life watch must retain its exact final settled resume");
                }
                AdvanceClockArchivedReplay.verifyChildBindings(parent, java.util.List.of(originalResume));
            } else if(query.basis() instanceof ObservationProvenance.PostResumePauseWatch watch) {
                var originalParent=archive.loadReceipt(watch.originalParentReceipt());
                var originalResume=archive.loadReceipt(watch.originalResumeReceipt());
                var originalPause=archive.loadReceipt(watch.originalPauseReceipt());
                require(originalParent.command().equals(parent)&&archive.receiptReferenceOf(originalParent).equals(watch.originalParentReceipt())
                        &&archive.receiptReferenceOf(originalResume).equals(watch.originalResumeReceipt())
                        &&archive.receiptReferenceOf(originalPause).equals(watch.originalPauseReceipt()),
                        "post-resume pause Life basis changed its original parent/resume/pause references");
                org.xar.ck3.control.application.session.ContinuityBatchJournal.requirePostResumePauseWatchRole(originalParent,originalResume,originalPause);
            }
            if(query.basis() instanceof ObservationProvenance.PreparedCleanupSuccessorWatch watch){
                var prepared=PreparedCleanupSuccessorEvidence.loadPreparedOriginals(watch.preparationReference(),archive);
                var captured=PreparedCleanupEvidence.loadPostAckCapturedOriginals(watch.captureReference(),archive);
                var terminal=(ActionState.PreparedCleanupNoEffectConfirmed)prepared.children().getLast().state();
                require(prepared.parentReference().equals(watch.originalParentReceipt())&&prepared.parentReceipt().command().equals(parent)
                        &&prepared.childReferences().getLast().equals(watch.predecessorNoEffectReceipt())&&terminal.proofReference().equals(watch.predecessorNoEffectProof())
                        &&captured.binding().prepared().reference().equals(prepared.reference()),"prepared successor Frame basis changed its parent/C5 proof/preparation/capture");
            }
            if(query.basis() instanceof ObservationProvenance.PreparedCleanupWatch watch){
                var prepared=PreparedCleanupEvidence.loadPreparedOriginals(watch.preparationReference(),archive);
                var capture=PreparedCleanupEvidence.loadPostAckCapturedOriginals(watch.captureReference(),archive);
                require(prepared.parentReference().equals(watch.originalParentReceipt())&&prepared.parentReceipt().command().equals(parent)
                        &&capture.binding().prepared().reference().equals(prepared.reference()),"prepared Frame basis changed original parent/complete capture");
            }
            rebuilt = new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                    query, complete.observedAt(), complete.originalEvidence());
        } else {
            rebuilt = push(complete);
        }
        require(rebuilt.source().equals(parent.source()) && rebuilt.sessionId().equals(parent.sessionId())
                && rebuilt.identity().game().equals(parent.before().game()), "archived life native/Driver frame crossed Game/source/session");
        require(rebuilt.provenance().equals(retained.provenance()), "archived life observation provenance differs from its actual producer");
        return rebuilt;
    }

    /** Pure DATA read through this identical installed full-frame/timeline replay pair. */
    public LifeAdvanceEvidence.Recorded readRecorded(ActionReceipt actual, ActionPorts.OutcomeArchive originals) {
        return LifeAdvanceEvidence.readRecorded(actual, originals, this, timeline);
    }

    LifeAdvanceEvidence.Recorded readExpiryRecorded(ActionReceipt receipt,
            LifeExpiredPartialAdvanceEvidence.TerminalData originals, ActionPorts.OutcomeArchive archive) {
        return new LifeExpiredPartialAdvanceEvidence(archive, this, new AdvancePrimitiveArchivedReplay(frames))
                .verifyTerminal(receipt, originals);
    }

    private LifeAdvanceEvidence.Recorded verifyExpiryRecorded(WriterContracts.Head head, ActionReceipt receipt,
            LifeExpiredPartialAdvanceEvidence.TerminalData originals, ActionPorts.OutcomeArchive archive) {
        var prior = originals.original();
        var current = ContinuityActionJournal.lookup(head.state(), receipt.command().actionId(), archive).orElseThrow();
        var history = new java.util.ArrayList<>(originals.children());
        history.add(prior);
        if (receipt.sequence() <= head.state().sequence()) {
            require(receipt.equals(current), "expired Life cold receipt differs from its settled canonical parent");
            history.add(receipt);
        } else {
            require(receipt.sequence() == head.state().sequence() + 1
                    && LifeExpiredPartialAdvanceEvidence.isPredecessor(current, prior, originals.expiryReference()),
                    "expired Life settlement changed its canonical unresolved predecessor");
        }
        for (var child : originals.children())
            require(ContinuityActionJournal.lookup(head.state(), child.command().actionId(), archive).filter(child::equals).isPresent(),
                    "expired Life settlement changed an original canonical child");
        var resume = (ActionState.Settled) originals.children().getLast().state();
        var core = (ActionState.ResumeCoreApplied) resume.settlement();
        history.add(archive.loadReceipt(core.observation().parentReceipt()));
        ContinuityActionJournal.requireHistoricalReceipts(head.state(), history, archive);
        var settlement = (ActionState.CompositeSettled) receipt.state();
        ActionEffects.validateComposite(receipt.command(), settlement.execution(), settlement.settlement());
        ActionEffects.validateCompositeChildren(receipt.command(), settlement.execution(), settlement.settlement(), originals.children());
        return readExpiryRecorded(receipt, originals, archive);
    }

    /** Archive-only dedicated cleanup proof; no permit or current observation is created. */
    public void verifyPostResumePauseCleanup(LifePostResumePauseCleanupEvidence.Authorization authorization,
            CompositeExecution successor,java.util.List<ActionReceipt> children,ClockStatusRead.Observation terminal,
            AdvanceObservationPort.Frame ending,ActionPorts.OutcomeArchive originals) {
        LifePostResumePauseCleanupProof.verify(authorization.original(),successor,children,
                authorization.parentReference(),authorization.childReferences(),authorization.armedStatus(),authorization.beforeCancel(),
                terminal,ending,authorization.issuedAt(),authorization.deadline(),authorization.reference(),originals,frames);
    }

    @Override public void verify(WriterContracts.Head actualLockedHead, ActionReceipt proposed,
            ActionPorts.OutcomeArchive sameWriterArchive) {
        if(proposed.state() instanceof ActionState.CompositeOperatorQuarantined) {
            var actual=operatorSource.get().orElseThrow(()->new IllegalStateException("actual Life operator decision source is absent"));
            try {actual.verify(Objects.requireNonNull(operatorSession.get()),actualLockedHead,proposed,sameWriterArchive);}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}return;
        }
        verifyAndReadRecorded(actualLockedHead, proposed, sameWriterArchive);
    }

    /** Original full qualification with its same-invocation DATA result; no current or writer permission. */
    public Optional<LifeAdvanceEvidence.Recorded> verifyAndReadRecorded(WriterContracts.Head actualLockedHead,
            ActionReceipt proposed, ActionPorts.OutcomeArchive sameWriterArchive) {
        require(proposed.command().origin().machineId().equals(actualLockedHead.state().machineId()),
                "life replay crossed the actual canonical writer machine");
        var expiry = LifeExpiredPartialAdvanceEvidence.readTerminalData(proposed, sameWriterArchive);
        if (expiry.isPresent()) return Optional.of(verifyExpiryRecorded(actualLockedHead, proposed, expiry.orElseThrow(), sameWriterArchive));
        if(preparedParent(proposed)){
            var recorded=PreparedCleanupParentEvidence.readRecorded(proposed,sameWriterArchive,this);
            preparedParentVerifier.orElseThrow(()->new IllegalStateException("actual prepared parent source qualification is absent"))
                    .verify(actualLockedHead,proposed,sameWriterArchive);return Optional.of(recorded);
        }
        if(PreparedCleanupCursor.marked(proposed)){
            PreparedCleanupCursor.load(proposed,sameWriterArchive,this);
            preparedCursorVerifier.orElseThrow(()->new IllegalStateException("actual prepared Life cursor qualification is absent"))
                    .verify(actualLockedHead,proposed,sameWriterArchive);return Optional.empty();
        }
        if (proposed.state() instanceof ActionState.CompositeSettled interruptedState
                && interruptedState.settlement() instanceof ActionState.LifeControlPrefixInterrupted interrupted) {
            var parent = proposed.command();
            var observation = interrupted.observation();
            var canonicalChildren = interruptedState.execution().children().stream().map(child -> {
                var actual = ContinuityActionJournal.lookup(actualLockedHead.state(), child.actionId(), sameWriterArchive).orElseThrow();
                require(actual.bodySha256().equals(child.bodySha256()), "interrupted Life child differs from canonical writer");
                return actual;
            }).toList();
            observation.validateParent(parent, interruptedState.execution());
            observation.validateChildren(parent, canonicalChildren);
            var actualEnding = LifeAdvanceEvidence.restore(parent, observation.ending(), sameWriterArchive, this);
            observation.validateFrame(parent, actualEnding, canonicalChildren);
            // The terminal ending is the existing independent post-state of the last canonical child,
            // not a fabricated parent clock completion or a new Native observation.
            var last = readChild(canonicalChildren.getLast(), sameWriterArchive).orElseThrow();
            require(last.identity().equals(actualEnding.identity()) && last.provenance().equals(actualEnding.provenance())
                    && last.observedAt().equals(actualEnding.observedAt()) && last.semantic().equals(actualEnding.semantic()),
                    "interrupted Life ending is not its actual canonical child's post-state");
            ActionEffects.validateComposite(parent, interruptedState.execution(), interrupted);
            ActionEffects.validateCompositeChildren(parent, interruptedState.execution(), interrupted, canonicalChildren);
            return Optional.empty();
        }
        if (proposed.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.CompositeNoGameplayWrite terminal) {
            LifeAdvanceComposite.requireNoGameplayWriteOriginal(proposed.command(), settled.execution());
            terminal.observation().validate(proposed.command(), settled.execution());
            ActionEffects.validateComposite(proposed.command(), settled.execution(), terminal);
            ActionEffects.validateCompositeChildren(settled.execution(), terminal, java.util.List.of());
            return Optional.empty();
        }
        if (proposed.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.CompositeRejected rejected) {
            var children = settled.execution().children().stream().map(bound -> {
                var child = ContinuityActionJournal.lookup(actualLockedHead.state(), bound.actionId(), sameWriterArchive).orElseThrow();
                require(child.bodySha256().equals(bound.bodySha256()), "rejected Life child differs from its canonical original");
                new AdvancePrimitiveArchivedReplay(frames).verify(actualLockedHead, child, sameWriterArchive);
                return child;
            }).toList();
            LifeAdvanceComposite.requireRejectedInitialization(proposed.command(), settled.execution(), children);
            ActionEffects.validateComposite(proposed.command(), settled.execution(), rejected);
            ActionEffects.validateCompositeChildren(proposed.command(), settled.execution(), rejected, children);
            return Optional.empty();
        }
        return Optional.of(LifeAdvanceEvidence.readRecorded(proposed, sameWriterArchive, this, timeline));
    }

    public static boolean preparedParent(ActionReceipt receipt){
        return receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.Applied applied
                &&applied.observation().provenance() instanceof ObservationProvenance.FreshSnapshotQuery query
                &&(query.basis() instanceof ObservationProvenance.PreparedCleanupWatch||query.basis() instanceof ObservationProvenance.PreparedCleanupSuccessorWatch);
    }
    public static AdvanceObservationPort.Frame push(Complete complete) {
        Objects.requireNonNull(complete);
        var frame = complete.identity().frame();
        var provenance = new ObservationProvenance.Push(frame.snapshotId(), frame.identity().nativeRevision(), complete.originalEvidence());
        return new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                provenance, complete.observedAt(), complete.originalEvidence());
    }
}
