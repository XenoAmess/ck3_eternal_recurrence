package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.reconciliation.LateOutcome.State;

/** Replays original timeline primitives against their native packets and complete Driver manifests. No I/O to Game. */
public final class AdvancePrimitiveArchivedReplay {
    private final NativeEffectEvidence.FrameLoader frames;
    public AdvancePrimitiveArchivedReplay(NativeEffectEvidence.FrameLoader frames) { this.frames = Objects.requireNonNull(frames); }
    public NativeRecordedEvidenceVerifier.Binding binding(OperationKey operation, ExactRef actualDefinition) {
        require(AdvancePrimitives.supports(operation), "registered timeline primitive required");
        return new NativeRecordedEvidenceVerifier.Binding(operation, actualDefinition, this::verify);
    }
    public void verify(WriterContracts.Head lockedHead, ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        verify(Optional.of(Objects.requireNonNull(lockedHead)), child, archive);
    }
    public void verify(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        verify(Optional.empty(), child, archive);
    }
    private void verify(Optional<WriterContracts.Head> lockedHead, ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(child); Objects.requireNonNull(archive);
        if (child.state() instanceof ActionState.IntentAbandoned) {
            IntentAbandonmentProof.verifyArchived(child, archive);
            lockedHead.ifPresent(head -> ContinuityActionJournal.requireHistoricalReceipt(head.state(), child, archive));
            return;
        }
        boolean zero = child.state() instanceof ActionState.RejectedBeforeDispatch;
        require(child.bodySha256().equals(ActionCodec.bodySha256(child.command()))
                && (child.state() instanceof ActionState.Settled || zero), "original settled or zero-write primitive required");
        var command = child.command();
        var attempt = ActionTransitions.attempt(child.state()).orElseThrow();
        var dispatch = ActionTransitions.dispatch(child.state()).orElseThrow();
        require(AdvancePrimitives.supports(command.operation()) && command.arguments().members().isEmpty(), "unsupported timeline primitive");
        require(command.origin().acceptsGuard(attempt.guard().origin()) && command.source().equals(attempt.guard().source())
                && command.sessionId().equals(attempt.guard().sessionId()) && command.operation().equals(attempt.guard().operation()), "primitive original attempt binding changed");
        require(attempt.preparedRequest().equals(archive.loadRequest(archive.requestReferenceOf(attempt.preparedRequest())))
                && attempt.preparedRequest().equals(AdvancePrimitives.prepareRequest(command)), "original prepared primitive changed or differs from the shared producer");
        require(dispatch.equals(archive.load(archive.referenceOf(dispatch))), "original primitive native dispatch changed");
        var before = RootGuardEvidence.loadFrame(attempt.guard(), archive, frames);
        require(before.identity().equals(command.before()), "primitive original before identity changed");
        var beforePush = new ObservationProvenance.Push(before.identity().frame().snapshotId(), before.identity().frame().identity().nativeRevision(), before.originalEvidence());
        var beforeFrame = new AdvanceObservationPort.Frame(before.identity(), before.source(), before.sessionId(), before.semantic(), beforePush, before.observedAt(), before.originalEvidence());
        require(command.equals(AdvancePrimitives.child(command, beforeFrame, command.actionId(), command.operation().value(), command.deadline())),
                "original primitive expected fields differ from the shared actual command producer");
        if (zero) {
            require(command.operation().value().equals("pause-map") || command.operation().value().equals("resume-map")
                    || command.operation().value().startsWith(ClockStatusRead.ARM_PREFIX), "only an actual pause, resume or ARM zero-write result is replayed here");
            requireOriginalReceipt(lockedHead, child, attempt, dispatch, archive);
            var original = (NativeActionPort.RejectedBeforeDispatch) dispatch;
            require(original.requestId().equals(attempt.requestId())
                    && original.proof().stage() == NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                    && original.proof().requestBytesWritten() == 0 && child.ack().isEmpty(),
                    "zero-write proof differs from the original unsubmitted attempt");
            return;
        }
        var settled = (ActionState.Settled) child.state();
        ActionEffects.validate(command, attempt, dispatch, settled.settlement());
        NativeActionPort.AckReceived ack = child.ack().orElseThrow(() -> new IllegalArgumentException("original native primitive ACK required"));
        if (settled.settlement() instanceof ActionState.Rejected rejected) {
            require(command.operation().value().equals("pause-map") && !ack.nativeOk()
                    && rejected.requestId().equals(attempt.requestId()), "only an actual rejected pause is replayed here");
            requireOriginalReceipt(lockedHead, child, attempt, dispatch, archive);
            // The sole archive reopens the actual response and outbound execute packet, and
            // verifies its fields against this original prepared request and Root guard.
            // Custody adds the real endpoint order; no parser or chronology is reconstructed.
            var custody = ack.custody().orElseThrow(() -> new IllegalArgumentException("actual rejected pause request custody required"));
            custody.verify(ack, attempt.guard());
            require(!custody.writeEntered().observedAt().isBefore(attempt.submittedAt()), "rejected pause write predates its original canonical attempt");
            var packet = org.xar.ck3.control.contracts.StrictJson.parse(ack.originalFrame().bytes());
            require(packet.path("error").isTextual() && packet.path("error").textValue().equals(rejected.reason())
                    && rejected.originalEvidence().equals(archive.referenceOf(ack)), "pause rejection lacks its exact original native error and archive identity");
            // Recovery remains a separate composite decision. ControlSequenceObservation
            // and the clock consumers still require their exact map-unavailable profile.
            return;
        }
        boolean confirmedPause = settled.settlement() instanceof ActionState.PauseConfirmed;
        require((child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED || confirmedPause) && ack.nativeOk(), "UNKNOWN or unconfirmed primitive cannot grant timeline credit");
        String step = command.operation().value();
        var original = AdvancePrimitives.nativeResult(ack, step);
        if (settled.settlement() instanceof ActionState.ControlApplied control) {
            require(command.expected().observerSchema().equals(AdvancePrimitives.CLOCK_OBSERVER)
                    && control.observerSchema().equals(AdvancePrimitives.CLOCK_OBSERVER), "clock control observer differs");
            require(control.supportingReads().isEmpty(), "timeline clock control has no unaccounted supporting query receipts");
            verifyIndependentRead(command, control.read(), archive);
            var actual = ClockStatusRead.decode(control.read().original());
            require(control.actual().equals(AdvancePrimitives.statusValues(actual)) && control.actual().containsAll(command.expected().values()), "clock control did not rederive actual original values");
            if (step.startsWith(ClockStatusRead.ARM_PREFIX)) {
                require(original.path("status").isTextual() && original.path("status").textValue().equals("available")
                        && actual.equals(AdvancePrimitives.acknowledgedSentinel(ack, step)), "arm ACK and independent original Status disagree");
            } else require(step.startsWith(ClockStatusRead.CANCEL_PREFIX) && original.path("status").isTextual()
                    && original.path("status").textValue().equals("canceled") && actual.state() == State.IDLE
                    && new BigInteger(actual.generation().decimal()).equals(AdvancePrimitives.cancelGeneration(step)), "cancel ACK lacks actual same-generation IDLE readback");
            return;
        }
        require(settled.settlement() instanceof ActionState.Applied || confirmedPause, "timeline primitive settlement kind unavailable");
        var effect = confirmedPause ? ((ActionState.PauseConfirmed) settled.settlement()).observation() : ((ActionState.Applied) settled.settlement()).observation();
        var after = AdvancePrimitiveEvidence.load(child, archive, frames);
        require(effect.observerSchema().equals(AdvancePrimitives.TIMELINE_OBSERVER)
                && command.expected().observerSchema().equals(AdvancePrimitives.TIMELINE_OBSERVER)
                && after.identity().game().equals(before.identity().game()) && after.identity().frame().episodeRunId().equals(before.identity().frame().episodeRunId())
                && after.identity().frame().identity().player().equals(before.identity().frame().identity().player())
                && after.identity().frame().identity().nativeRevision().compareTo(before.identity().frame().identity().nativeRevision()) > 0
                && !after.observedAt().isBefore(before.observedAt()) && effect.provenance().independentOf(attempt.requestId()), "timeline effect has no independent later native frame");
        List<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue> actual;
        if (step.startsWith("set-speed-")) {
            BigInteger speed = integer(after.semantic().get("speed"), "speed");
            require(speed.intValueExact() == Integer.parseInt(step.substring(10)), "original speed poststate differs");
            actual = List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("speed"), speed));
        } else if (step.equals("pause-map")) {
            require(AdvancePolicy.truth(after.semantic(), "paused"), "pause ACK lacks actual paused native state");
            actual = confirmedPause ? PauseConfirmation.actualValues() : List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"), true));
            if (confirmedPause) PauseConfirmation.validate(command, attempt, settled.dispatch(), effect);
        } else {
            require(step.equals("resume-map") && (!AdvancePolicy.truth(after.semantic(), "paused")
                    || after.identity().frame().identity().dateRaw().compareTo(before.identity().frame().identity().dateRaw()) > 0
                    || AdvanceProgress.newModal(after.semantic(), before.identity(), Optional.of(before.semantic())).isPresent()),
                    "resume ACK lacks actual original running/date/new-modal poststate");
            actual = List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("timeline.resume_observed"), true));
        }
        require(effect.actual().equals(actual) && (confirmedPause ? command.expected().values().equals(PauseConfirmation.expectedValues()) : actual.equals(command.expected().values())), "timeline original poststate differs from canonical semantic values");
    }
    private static void requireOriginalReceipt(Optional<WriterContracts.Head> lockedHead, ActionReceipt proposed,
            ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch, ActionPorts.OutcomeArchive archive) {
        ActionReceipt actual = lockedHead.map(head -> ContinuityActionJournal.lookup(head.state(), proposed.command().actionId(), archive)
                .orElseThrow(() -> new IllegalArgumentException("negative pause lacks its actual canonical original"))).orElse(proposed);
        require(actual.command().equals(proposed.command()) && actual.bodySha256().equals(proposed.bodySha256())
                && ActionTransitions.attempt(actual.state()).filter(attempt::equals).isPresent()
                && ActionTransitions.dispatch(actual.state()).filter(dispatch::equals).isPresent(),
                "negative pause differs from its canonical original attempt and dispatch");
        require(actual.equals(proposed) || actual.state() instanceof ActionState.AckReceived
                && proposed.state() instanceof ActionState.Settled, "negative pause replaced an already retained terminal receipt");
        // During settlement the locked head retains the already committed ACK. During cold
        // replay this is the original child itself. Both go through the sole physical archive.
        require(actual.equals(archive.loadReceipt(archive.receiptReferenceOf(actual))), "negative pause receipt changed in the original archive");
    }
    public static void verifyRead(ActionCommand parent, PlanningReadReceipt read, ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read, archive);
        boolean reconciling = read.request().origin() instanceof CommandOrigin.Reconciliation;
        var after = reconciling ? read.request().origin().requireReconciliation().factual() : read.after().binding().observed();
        require(read.contractId().equals(reconciling ? ClockStatusRead.RECONCILIATION_CONTRACT_ID : ClockStatusRead.CONTRACT_ID)
                && read.request().operation().value().equals(ClockStatusRead.STEP)
                && read.request().source().equals(parent.source()) && read.request().sessionId().equals(parent.sessionId())
                && after.game().equals(parent.before().game()) && after.machineId().equals(parent.before().machineId())
                && after.frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                && after.frame().identity().player().equals(parent.before().frame().identity().player()),
                "independent Status read crossed original source/session/Game/episode");
        if (reconciling) {
            var identity = read.request().origin().requireReconciliation();
            require(identity.pending().actionId().equals(parent.actionId())
                    && identity.pending().bodySha256().equals(ActionCodec.bodySha256(parent))
                    && identity.pending().originalBefore().equals(parent.before())
                    && read.before().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    && read.after().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                    && read.before().binding().origin() instanceof CommandOrigin.Reconciliation
                    && read.after().binding().origin() instanceof CommandOrigin.Reconciliation
                    && read.before().binding().origin().requireReconciliation().equals(identity)
                    && read.after().binding().origin().requireReconciliation().equals(identity),
                    "reconciliation Status lost its complete original pending and held query identity");
        }
    }
    public void verifyIndependentRead(ActionCommand parent, PlanningReadReceipt read, ActionPorts.OutcomeArchive archive) {
        verifyRead(parent, read, archive);
        if (read.request().origin() instanceof CommandOrigin.Reconciliation) loadStatusFrame(read, archive);
        else {
            RootGuardEvidence.loadFrame(read.before().binding(), archive, frames);
            RootGuardEvidence.loadFrame(read.after().binding(), archive, frames);
        }
    }
    /** Existing full Native/Driver frame of a genuinely retained Status read, without a new observation. */
    public org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete loadStatusFrame(
            PlanningReadReceipt read, ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read, archive);
        if (!(read.request().origin() instanceof CommandOrigin.Reconciliation))
            return RootGuardEvidence.loadFrame(read.after().binding(), archive, frames);
        var identity = read.request().origin().requireReconciliation();
        require(read.contractId().equals(ClockStatusRead.RECONCILIATION_CONTRACT_ID)
                && read.before().binding().origin() instanceof CommandOrigin.Reconciliation
                && read.after().binding().origin() instanceof CommandOrigin.Reconciliation
                && read.before().binding().origin().requireReconciliation().equals(identity)
                && read.after().binding().origin().requireReconciliation().equals(identity),
                "actual reconciliation Status frame lost its typed query identity");
        var actual = frames.load(new NativeEffectEvidence.FrameBasis(identity.nativeEvidence(), identity.evidence().observationManifest()), archive);
        require(actual.identity().equals(identity.factual()) && actual.source().equals(identity.source())
                && actual.sessionId().equals(identity.sessionId()) && actual.connectionGeneration().equals(identity.connectionGeneration())
                && actual.originalEvidence().equals(identity.nativeEvidence()) && actual.observedAt().equals(identity.observedAt()),
                "actual reconciliation Status Native/Driver frame differs from its retained identity");
        return actual;
    }
}
