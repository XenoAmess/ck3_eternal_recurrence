package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Separate producer: parent reservation and PREPARED commit precede all late
 * reads. The source owns a real lexical held-original scope. No material or
 * canonical outcome is written until that scope has returned and closed. */
final class PreparedCleanupCoordinatorSupport {
    static final String CURSOR_PREFIX="prepared-cleanup-successor/v1: ";
    private PreparedCleanupCoordinatorSupport(){}
    static CompositeContinuationReport run(ActionJournal.LockedJournal locked,LifePreparedCleanupContinuation token,
            CompositeRegistry registry,NativeActionPort nativePort,Clock clock){
        var prepared=token.prepared();var parent=locked.find(token.originalParent().actionId()).orElseThrow();
        StrictJson.require(parent.command().equals(token.originalParent())&&parent.state() instanceof ActionState.CompositeUnknown,
                "prepared cleanup requires its actual unresolved original parent");
        var before=((ActionState.CompositeUnknown)parent.state()).execution();
        var installed=registry.require(before.handlerId());
        StrictJson.require(installed instanceof CompositeActionPort.PreparedCleanupSource&&installed instanceof LifeAdvanceComposite,
                "prepared cleanup requires the actual installed Life producer");
        var source=(CompositeActionPort.PreparedCleanupSource)installed;
        var archive=source.preparedCleanupArchive().withSession(locked.writerSession());
        var child=prepared.command();var existing=locked.find(child.actionId());
        if(existing.isPresent()){
            var original=existing.orElseThrow();
            StrictJson.require(original.command().equals(child)&&original.state() instanceof PreparedCleanupAction
                    &&((PreparedCleanupAction)original.state()).preparationReference().equals(prepared.reference()),
                    "same-ID prepared collection changed its original body or preparation");
            // A prior PREPARED may have crashed on either side of the endpoint.
            // This first child software stage deliberately leaves it untouched.
            // The separate read-only collection/promotion role must retain every
            // original ACK and complete proof before its own canonical admission.
            // No poll is popped/discarded and no new observation/write permit exists.
            return report(parent,original);
        }
        boolean successor=PreparedCleanupSuccessorEvidence.isSuccessor(prepared);
        if(successor)StrictJson.require(clock.instant().isBefore(token.deadline())&&before.children().size()==5
                &&before.children().equals(((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution().children()),
                "prepared successor cannot reserve another ordinal or renew any old preparation");
        else
        StrictJson.require(clock.instant().isBefore(token.deadline())&&before.children().size()==4
                &&before.children().equals(((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution().children()),
                "prepared cleanup cannot reserve another ordinal or renew an old preparation");
        source.requirePreparedCleanup(child,token);
        try{nativePort.requirePreparedCleanupCapacity(prepared);}catch(IOException failure){throw new UncheckedIOException(failure);}
        var next=new ArrayList<>(before.children());next.add(new CompositeExecution.Child(child.actionId(),ActionCodec.bodySha256(child)));
        var evidence=new ArrayList<>(((ActionState.CompositeUnknown)parent.state()).evidence());
        evidence.removeIf(prepared.reference()::equals);evidence.add(prepared.reference());
        ActionCoordinator.append(locked,parent.command(),parent.bodySha256(),new ActionState.CompositeUnknown(
                new CompositeExecution(before.handlerId(),before.startedAt(),before.guard(),next),
                successor?PreparedCleanupSuccessorEvidence.CURSOR_PREFIX+"distinct sixth child after canonical C5 NoEffect; original five-child prefix unchanged":
                        CURSOR_PREFIX+"distinct child reserved after canonical NoEffect; original four-child prefix unchanged",evidence));
        ActionReceipt durable=ActionCoordinator.append(locked,child,ActionCodec.bodySha256(child),PreparedCleanupAction.prepared(prepared.reference()));
        // Every slow hook, intent barrier and complete source replay has ended
        // before this point or inside withPreparedCleanupWrite BEFORE observeLate.
        AtomicBoolean worldMethodEntered=new AtomicBoolean();
        AtomicReference<PreparedCleanupEvidence.LateBinding> actualLate=new AtomicReference<>();
        AtomicReference<PreparedCleanupNativeOutcome> actualOutcome=new AtomicReference<>();
        Throwable failure=null;
        try{
            source.withPreparedCleanupWrite(child,token,prepared,()->{
                var observation=new PreparedCleanupObservationPermit(source,token,prepared,durable.sequence(),clock);
                var late=nativePort.observePreparedCleanupLate(observation);actualLate.set(late);
                PreparedCleanupEvidence.requireLateBinding(late,clock.instant());
                var permit=new PreparedCleanupPermit(source,token,prepared,late,durable.sequence(),clock);
                worldMethodEntered.set(true);
                var returned=actualCommand(child,()->nativePort.submitPreparedCleanup(permit,prepared.nativePrepared(),permit.writeDeadline()));
                StrictJson.require(returned.preparationNonce().equals(prepared.preparationNonce()),"SDK returned another preparation nonce");
                actualOutcome.set(returned);return returned;
            });
        }catch(IOException|InterruptedException|RuntimeException actual){failure=actual;if(actual instanceof InterruptedException)Thread.currentThread().interrupt();}
        // The source's actual historical lease has now finished. Even a close or
        // dependency failure after a received ACK is retained as UNKNOWN, never
        // erased or converted to a fresh permit/no-send conclusion.
        var result=actualOutcome.get();var late=actualLate.get();
        if(failure==null&&result!=null&&result.originalFailure().isPresent())failure=result.originalFailure().orElseThrow();
        if(failure==null&&result!=null&&result.captured().isPresent()){
            Optional<ExactRef> lateReference=late==null?Optional.empty():Optional.of(PreparedCleanupEvidence.preserveLateBinding(late,archive,source.preparedCleanupFrames()));
            var capture=result.captured().orElseThrow();PreparedCleanupEvidence.requirePostAckCaptured(capture);
            var captureRef=PreparedCleanupEvidence.preservePostAckCaptured(capture,archive,source.preparedCleanupFrames());
            // The historical lease has closed. Keep the actual SDK occurrence
            // strongly alive; project/archive it before slow canonical outcomes.
            var projection=source.projectPreparedCleanup(token,prepared,capture,captureRef);
            archived(prepared,captureRef,projection.reference(),locked.head().state().sequence());
            var terminal=ActionCoordinator.append(locked,child,ActionCodec.bodySha256(child),new PreparedCleanupAction(
                    PreparedCleanupAction.Phase.CONFIRMED,prepared.reference(),lateReference,Optional.of(result.original()),Optional.of(captureRef),Optional.empty()));
            try{
                var effect=source.completePreparedCleanupParent(token,prepared,terminal,projection);
                var currentParent=locked.find(parent.command().actionId()).orElseThrow();
                StrictJson.require(currentParent.state() instanceof ActionState.CompositeUnknown&&PreparedCleanupCursor.marked(currentParent),
                        "prepared parent changed after actual child canonical commit");
                var execution=((ActionState.CompositeUnknown)currentParent.state()).execution();
                var children=execution.children().stream().map(bound->locked.find(bound.actionId()).orElseThrow()).toList();
                var settled=new ActionState.Applied(effect);
                ActionEffects.validateComposite(parent.command(),execution,settled);
                ActionEffects.validateCompositeChildren(parent.command(),execution,settled,children);
                var finished=ActionCoordinator.append(locked,parent.command(),parent.bodySha256(),new ActionState.CompositeSettled(execution,settled));
                return report(finished,terminal);
            }finally{java.lang.ref.Reference.reachabilityFence(capture.afterFrame());}
        }
        if(failure==null)failure=new IOException("prepared cleanup has no complete original volatile post-ACK capture; same-ID collection only");
        final Throwable originalFailure=failure;
        return PreparedCleanupFailure.retainingOriginal(originalFailure,()->{
            Optional<ExactRef> lateReference=late==null?Optional.empty():Optional.of(PreparedCleanupEvidence.preserveLateBinding(late,archive,source.preparedCleanupFrames()));
            var failureOriginal=PreparedCleanupFailure.preserve(originalFailure,clock.instant(),archive);
            NativeActionPort.DispatchOutcome original;
            var observations=new ArrayList<NativeActionPort.DispatchOutcome>();var supplemental=new ArrayList<ExactRef>();supplemental.add(failureOriginal);
            if(originalFailure instanceof NativeActionPort.PreparedCleanupObservationFailure unavailable)observations.addAll(unavailable.originals());
            if(result!=null){original=result.original();result.failure().ifPresent(value->observations.addAll(value.observationOriginals()));
                if(result.captured().isPresent())supplemental.add(PreparedCleanupEvidence.preservePostAckCaptured(result.captured().orElseThrow(),archive,source.preparedCleanupFrames()));
            }else if(!worldMethodEntered.get())original=PreparedCleanupFailure.beforeNativeCall(prepared.nativeRequestId(),originalFailure,clock.instant(),failureOriginal);
            else original=new NativeActionPort.Unknown(prepared.nativeRequestId(),"actual prepared world-method failed; preserve complete failure and collect only",new byte[0],Optional.empty());
            var data=new PreparedCleanupEvidence.FailureData(prepared,Optional.ofNullable(late),original,observations,clock.instant(),supplemental);
            var failureRef=PreparedCleanupEvidence.preserveFailure(data,archive,source.preparedCleanupFrames());
            var phase=original instanceof NativeActionPort.RejectedBeforeDispatch?PreparedCleanupAction.Phase.BEFORE_WRITE_REJECTED:PreparedCleanupAction.Phase.UNKNOWN;
            var recorded=ActionCoordinator.append(locked,child,ActionCodec.bodySha256(child),new PreparedCleanupAction(phase,prepared.reference(),lateReference,
                    Optional.of(original),Optional.empty(),Optional.of(failureRef)));
            return report(locked.find(parent.command().actionId()).orElseThrow(),recorded);
        });
    }

    private static void archived(PreparedCleanupEvidence.Prepared prepared,ExactRef capture,ExactRef projection,long head){
        try{
            var row=org.xar.ck3.control.contracts.StrictJson.object();row.put("schema","xar.prepared-cleanup-archived-before-canonical/v1");
            row.put("child_action_id",prepared.command().actionId());row.put("body_sha256",ActionCodec.bodySha256(prepared.command()));
            row.set("preparation_ref",prepared.reference().toJson());row.set("capture_ref",capture.toJson());row.set("projection_ref",projection.toJson());
            row.put("actual_head_before_outcome",head);row.put("child_or_parent_canonical_success_claimed",false);
            System.out.println("B_CLEANUP_ARCHIVED "+new String(StrictJson.canonical(row,16384),java.nio.charset.StandardCharsets.UTF_8));
        }catch(Throwable diagnosticUnavailable){ /* Evidence has already been saved; diagnostics cannot alter/retry control. */ }
    }
    private static final class ActualCommandInterrupted extends RuntimeException {
        private static final long serialVersionUID=1L;
        ActualCommandInterrupted(InterruptedException original){super(original);}
    }
    private static <T>T actualCommand(ActionCommand command,CompositeActionPort.PreparedCleanupWork<T> operation)
            throws IOException,InterruptedException {
        try{return ActionScope.run(command.actionId(),()->ActionCommandScope.within(command,()->{
            try{return operation.run();}catch(IOException failure){throw new UncheckedIOException(failure);}
            catch(InterruptedException interrupted){throw new ActualCommandInterrupted(interrupted);}
        }));}catch(UncheckedIOException failure){throw failure.getCause();}
        catch(ActualCommandInterrupted interrupted){throw (InterruptedException)interrupted.getCause();}
    }
    private static CompositeContinuationReport report(ActionReceipt parent,ActionReceipt child){
        // PREPARED never impersonates a legacy Attempt. The original parent stays
        // UNKNOWN; this report cannot grant an advance/checkpoint or fabricate ACK.
        return new CompositeContinuationReport(parent,List.of(),CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT);
    }
}
