package org.xar.ck3.control.application.planning.military;

import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;

/** Commander has a query result as originalEvidence, so it has its own full original-frame replay. */
public final class CommanderArchivedVerifier {
    private CommanderArchivedVerifier() {}
    @FunctionalInterface public interface ReconciliationFrames {
        org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete load(GuardEvidence guard,ActionPorts.OutcomeArchive archive) throws java.io.IOException;
    }
    public static NativeRecordedEvidenceVerifier.Binding binding(OperationKey operation,ExactRef actualSource,
            NativeEffectEvidence.FrameLoader actualFrames) {
        return binding(operation,actualSource,actualFrames,(guard,archive)->{throw new java.io.IOException("commander reconciliation archive authority is not installed");});
    }
    public static NativeRecordedEvidenceVerifier.Binding binding(OperationKey operation,ExactRef actualSource,
            NativeEffectEvidence.FrameLoader actualFrames,ReconciliationFrames reconciliation) {
        Objects.requireNonNull(actualFrames);
        Objects.requireNonNull(reconciliation);
        return new NativeRecordedEvidenceVerifier.Binding(operation,actualSource,(head,receipt,archive)-> {
            StrictJson.require(receipt.command().operation().equals(operation)&&receipt.state() instanceof ActionState.Settled,
                    "commander archive verifier requires its original settled primitive");
            var settled=(ActionState.Settled)receipt.state();
            StrictJson.require(receipt.command().before().machineId().equals(head.state().machineId()),"commander archived effect crossed writer machine");
            var originalBefore=RootGuardEvidence.loadFrame(settled.attempt().guard(),archive,actualFrames);
            StrictJson.require(originalBefore.identity().equals(receipt.command().before())&&originalBefore.source().equals(receipt.command().source())
                    &&originalBefore.sessionId().equals(receipt.command().sessionId()),"commander archived submission source differs");
            if(settled.settlement() instanceof ActionState.Rejected rejected) {
                StrictJson.require(settled.dispatch().equals(archive.load(rejected.originalEvidence()))&&rejected.requestId().equals(settled.attempt().requestId()),"commander rejection lacks original archived dispatch");
                StrictJson.require(settled.dispatch() instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()&&ack.originalResultToken().isPresent(),"commander domain rejection requires actual native result");
                // Replay the same status/identity decoder without manufacturing a current read.
                CommanderAssignmentPostcondition.requireRejection(receipt.command(),settled.attempt(),settled.dispatch(),rejected,archive);
                return;
            }
            StrictJson.require(settled.settlement() instanceof ActionState.Applied,"commander cannot prove unrelated control/frontend settlement");
            var effect=((ActionState.Applied)settled.settlement()).observation();
            StrictJson.require(effect.supportingEvidence().size()==2,"commander needs its exact original dispatch and independent read");
            ExactRef dispatchRef=effect.supportingEvidence().get(0),readRef=effect.supportingEvidence().get(1);
            StrictJson.require(settled.dispatch().equals(archive.load(dispatchRef))&&dispatchRef.equals(archive.referenceOf(settled.dispatch())),"commander supporting dispatch changed");
            PlanningReadReceipt read=archive.loadRead(readRef);
            StrictJson.require(readRef.equals(archive.readReferenceOf(read)),"commander original query archive changed");
            NativeRecordedEvidenceVerifier.requireRead(read,archive);
            if(read.request().origin() instanceof CommandOrigin.Reconciliation) {
                var before=loadReconciliation(reconciliation,read.before().binding(),archive);
                var after=loadReconciliation(reconciliation,read.after().binding(),archive);
                var identity=read.request().origin().requireReconciliation();
                StrictJson.require(before.identity().equals(identity.factual())&&after.identity().equals(identity.factual())
                        &&before.source().equals(identity.source())&&after.source().equals(identity.source())
                        &&before.sessionId().equals(identity.sessionId())&&after.sessionId().equals(identity.sessionId())
                        &&before.connectionGeneration().equals(identity.connectionGeneration())&&after.connectionGeneration().equals(identity.connectionGeneration())
                        &&before.fullBindingSha256().equals(after.fullBindingSha256())&&before.semantic().equals(after.semantic()),
                        "commander reconciliation original full frame/source/pending replay differs");
                var input=new CommanderReconciliationCollector.Input(identity,before.semantic());
                var replayed=CommanderAssignmentPostcondition.projectReconciliation(receipt.command(),settled.attempt(),settled.dispatch(),input,read,archive);
                StrictJson.require(replayed instanceof ActionPorts.EffectObserved&&((ActionPorts.EffectObserved)replayed).observation().equals(effect),
                        "commander reconciliation archive differs from original incumbent/native effect");
                return;
            }
            var before=RootGuardEvidence.loadFrame(read.before().binding(),archive,actualFrames);
            var after=RootGuardEvidence.loadFrame(read.after().binding(),archive,actualFrames);
            StrictJson.require(before.identity().equals(after.identity())&&before.source().equals(after.source())&&before.sessionId().equals(after.sessionId())
                    &&before.connectionGeneration().equals(after.connectionGeneration())&&before.fullBindingSha256().equals(after.fullBindingSha256())
                    &&before.semantic().equals(after.semantic())&&before.identity().equals(read.request().before())
                    &&before.source().equals(receipt.command().source())&&before.sessionId().equals(receipt.command().sessionId()),
                    "commander independent read crossed full native/Driver frame");
            // The exact successfully guarded read establishes this one fixed query capability; no planner capability set is fabricated.
            var input=new CommanderObservationCollector.ObservedInput(before.identity(),before.source(),before.sessionId(),
                    read.request().deadline(),before.semantic(),Set.of(CommanderQuality.QUERY_CAPABILITY));
            var replayed=CommanderAssignmentPostcondition.project(receipt.command(),settled.attempt(),settled.dispatch(),input,read,archive);
            StrictJson.require(replayed instanceof ActionPorts.EffectObserved&&((ActionPorts.EffectObserved)replayed).observation().equals(effect),
                    "commander archived native/frame/current-incumbent replay differs from every proposed effect field");
        });
    }
    private static org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete loadReconciliation(
            ReconciliationFrames actual,GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        try{return actual.load(guard,archive);}catch(java.io.IOException unavailable){throw new java.io.UncheckedIOException(unavailable);}
    }
}
