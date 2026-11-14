package org.xar.ck3.control.application.advance;

import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;

public final class PreparedCleanupReplay {
    private PreparedCleanupReplay(){}
    public static PreparedCleanupEvidence.Prepared verifyOriginals(ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        StrictJson.require(receipt.state() instanceof PreparedCleanupAction,"exact prepared cleanup state required");
        var state=(PreparedCleanupAction)receipt.state();
        var prepared=PreparedCleanupEvidence.loadPreparedOriginals(state.preparationReference(),archive);
        StrictJson.require(prepared.command().equals(receipt.command())&&receipt.bodySha256().equals(ActionCodec.bodySha256(prepared.command())),
                "prepared receipt changed its complete durable child command");
        for(var ref:PreparedCleanupActionCodec.references(state,archive)){
            if(state.originalDispatch().isPresent()&&archive.referenceOf(state.originalDispatch().orElseThrow()).equals(ref))continue;
            byte[] raw=archive.loadMaterial(ref).bytes();StrictJson.require(raw.length==ref.bytes()&&ActionCodec.sha256(raw).equals(ref.sha256()),
                    "prepared cleanup complete original material changed");
        }
        state.originalDispatch().ifPresent(value->StrictJson.require(value.requestId().equals(prepared.nativeRequestId())
                &&archive.load(archive.referenceOf(value)).equals(value),"prepared cleanup changed its actual original Native outcome"));
        return prepared;
    }
    public static PreparedCleanupEvidence.Prepared verify(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames){
        var state=(PreparedCleanupAction)receipt.state();var prepared=verifyOriginals(receipt,archive);
        PreparedCleanupEvidence.loadPrepared(state.preparationReference(),archive,Objects.requireNonNull(frames));
        PreparedCleanupEvidence.LateBinding late=state.lateBindingReference().map(ref->PreparedCleanupEvidence.loadLateBinding(ref,archive,frames)).orElse(null);
        if(late!=null)StrictJson.require(late.prepared().reference().equals(prepared.reference()),"prepared state borrowed another late binding");
        if(state.phase()==PreparedCleanupAction.Phase.CONFIRMED){
            var captured=PreparedCleanupEvidence.loadPostAckCaptured(state.capturedPostAcknowledgement().orElseThrow(),archive,frames);
            StrictJson.require(captured.binding().prepared().reference().equals(prepared.reference())&&late!=null
                    &&PreparedCleanupEvidence.sameLate(captured.binding(),late)
                    &&state.originalDispatch().orElseThrow().equals(captured.cancellationAcknowledgement()),
                    "prepared terminal changed its exact late/cancel/two-IDLE/full-frame original closure");
        }else if(state.failureReference().isPresent()){
            var failure=PreparedCleanupEvidence.loadFailure(state.failureReference().orElseThrow(),archive,frames);
            StrictJson.require(failure.prepared().reference().equals(prepared.reference())
                    &&state.originalDispatch().orElseThrow().equals(failure.original()),"prepared state changed its actual failure closure");
            if(state.phase()==PreparedCleanupAction.Phase.BEFORE_WRITE_REJECTED)StrictJson.require(
                    failure.original() instanceof NativeActionPort.RejectedBeforeDispatch,"prepared before-write terminal has no actual typed zero-write original");
        }
        return prepared;
    }
}
