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
    private final NativeEffectEvidence.FrameLoader frames;
    private final AdvanceClockArchivedReplay timeline;

    public LifeAdvanceRootReplay(NativeEffectEvidence.FrameLoader actualFrames) {
        this.frames = Objects.requireNonNull(actualFrames);
        this.timeline = new AdvanceClockArchivedReplay(actualFrames);
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
        return Optional.of(push(AdvancePrimitiveEvidence.load(child, archive, frames)));
    }

    @Override public AdvanceObservationPort.Frame rebuild(ActionCommand parent, LifeAdvanceEvidence.FrameRecord retained,
            ActionPorts.OutcomeArchive archive) {
        Complete complete = Objects.requireNonNull(frames.load(
                new NativeEffectEvidence.FrameBasis(retained.nativeFrame(), retained.driverFacts()), archive));
        AdvanceObservationPort.Frame rebuilt = push(complete);
        require(rebuilt.source().equals(parent.source()) && rebuilt.sessionId().equals(parent.sessionId())
                && rebuilt.identity().game().equals(parent.before().game()), "archived life native/Driver frame crossed Game/source/session");
        // The actual transport producer publishes snapshots. A retained historical Query cannot
        // be upgraded to a Push or accepted merely because its scalar ID resembles a snapshot ID.
        require(rebuilt.provenance().equals(retained.provenance()), "archived life observation provenance differs from its actual producer");
        return rebuilt;
    }

    /** Pure DATA read through this identical installed full-frame/timeline replay pair. */
    public LifeAdvanceEvidence.Recorded readRecorded(ActionReceipt actual, ActionPorts.OutcomeArchive originals) {
        return LifeAdvanceEvidence.readRecorded(actual, originals, this, timeline);
    }

    @Override public void verify(WriterContracts.Head actualLockedHead, ActionReceipt proposed,
            ActionPorts.OutcomeArchive sameWriterArchive) {
        require(proposed.command().origin().machineId().equals(actualLockedHead.state().machineId()),
                "life replay crossed the actual canonical writer machine");
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
            return;
        }
        if (proposed.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.CompositeNoGameplayWrite terminal) {
            LifeAdvanceComposite.requireNoGameplayWriteOriginal(proposed.command(), settled.execution());
            terminal.observation().validate(proposed.command(), settled.execution());
            ActionEffects.validateComposite(proposed.command(), settled.execution(), terminal);
            ActionEffects.validateCompositeChildren(settled.execution(), terminal, java.util.List.of());
            return;
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
            return;
        }
        LifeAdvanceEvidence.verifyRecorded(proposed, sameWriterArchive, this, timeline);
    }

    public static AdvanceObservationPort.Frame push(Complete complete) {
        Objects.requireNonNull(complete);
        var frame = complete.identity().frame();
        var provenance = new ObservationProvenance.Push(frame.snapshotId(), frame.identity().nativeRevision(), complete.originalEvidence());
        return new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                provenance, complete.observedAt(), complete.originalEvidence());
    }
}
