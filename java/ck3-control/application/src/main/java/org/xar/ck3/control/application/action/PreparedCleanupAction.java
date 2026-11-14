package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable source preparation and its actual outcome. PREPARED is unresolved and
 * contains no legacy Attempt, SUBMITTING, physical Guard or send capability.
 * Only the actual registered source/writer may admit these DATA into the ledger. */
public record PreparedCleanupAction(Phase phase, ExactRef preparationReference,
        Optional<ExactRef> lateBindingReference, Optional<NativeActionPort.DispatchOutcome> originalDispatch,
        Optional<ExactRef> capturedPostAcknowledgement, Optional<ExactRef> failureReference) implements ActionState {
    public enum Phase { PREPARED, UNKNOWN, BEFORE_WRITE_REJECTED, CONFIRMED }
    public PreparedCleanupAction {
        Objects.requireNonNull(phase); Objects.requireNonNull(preparationReference);
        lateBindingReference=Objects.requireNonNull(lateBindingReference);
        originalDispatch=Objects.requireNonNull(originalDispatch);
        capturedPostAcknowledgement=Objects.requireNonNull(capturedPostAcknowledgement);
        failureReference=Objects.requireNonNull(failureReference);
        StrictJson.require(preparationReference.bytes()>0,"complete durable cleanup preparation required");
        for(var ref:java.util.List.of(lateBindingReference,capturedPostAcknowledgement,failureReference))
            ref.ifPresent(value->StrictJson.require(value.bytes()>0,"nonempty cleanup original reference required"));
        if(phase==Phase.PREPARED)
            StrictJson.require(lateBindingReference.isEmpty()&&originalDispatch.isEmpty()
                    &&capturedPostAcknowledgement.isEmpty()&&failureReference.isEmpty(),"PREPARED cannot invent a write, binding or result");
        if(phase==Phase.BEFORE_WRITE_REJECTED) {
            StrictJson.require(originalDispatch.orElse(null) instanceof NativeActionPort.RejectedBeforeDispatch
                    &&failureReference.isPresent()&&capturedPostAcknowledgement.isEmpty(),"typed actual before-write evidence and complete failure originals required");
            var zero=(NativeActionPort.RejectedBeforeDispatch)originalDispatch.orElseThrow();
            StrictJson.require(zero.proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                    &&zero.proof().requestBytesWritten()==0,"cleanup before-write classification requires the original typed zero-write result");
        }
        if(phase==Phase.CONFIRMED)
            StrictJson.require(lateBindingReference.isPresent()&&originalDispatch.orElse(null) instanceof NativeActionPort.AckReceived ack
                    &&ack.nativeOk()&&capturedPostAcknowledgement.isPresent()&&failureReference.isEmpty(),
                    "cleanup confirmation needs its actual late-bound ACK and complete volatile post-ACK capture");
        if(phase==Phase.UNKNOWN)
            StrictJson.require(capturedPostAcknowledgement.isEmpty()&&failureReference.isPresent(),"UNKNOWN retains the actual complete failure and never claims completed capture");
    }
    public boolean terminal(){return phase==Phase.BEFORE_WRITE_REJECTED||phase==Phase.CONFIRMED;}
    public static PreparedCleanupAction prepared(ExactRef reference){
        return new PreparedCleanupAction(Phase.PREPARED,reference,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
    }
}
