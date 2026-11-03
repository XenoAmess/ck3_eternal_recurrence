package org.xar.ck3.study.m6.poststate242;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.CallFrame;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.NormalRule;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.Ports;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.SourceSite;

/** Single-push thin CALL dispatcher. It neither applies a producer state nor implements a child. */
public final class CallOutcome242Provider {
    private CallOutcome242Provider() { }

    /** Pure preparation. callerState is an actual instruction snapshot with pre-CALL RSP. */
    public static CallFrame prepare(long ownerEntryRva,long siteRva,long resolvedTargetBits,
            GovernmentCrtBoundary185Api.Entry callerState,boolean directionFlagSet,
            QueueFp604Api.Mxcsr mxcsr) {
        Objects.requireNonNull(callerState);Objects.requireNonNull(mxcsr);
        SourceSite source=CallOutcome242Sites.require(ownerEntryRva,siteRva);
        long image=callerState.imageBaseBits();
        GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(siteRva,
                source.kind(),resolvedTargetBits,callerState.rspBits(),
                callerState.volatileBits(),callerState.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child=new GovernmentCrtBoundary185Api.Entry(
                image,call.rspBits()-8L,call.volatileBits(),call.nonvolatileBits());
        return new CallFrame(ownerEntryRva,image,call,child,directionFlagSet,mxcsr,
                source.instructionLength(),image+siteRva+source.instructionLength(),source.normalRule());
    }

    /**
     * Owns the only actual CALL push. Memory/port exceptions propagate without retry or fabricated Outcome.
     * A Stopped is returned by identity: no parent snapshot, restore, continuation or extra normal check.
     * Caller must consume Normal only after this validation, including actual post DF/MXCSR.
     */
    public static QueueFp604Api.Outcome invokePrepared(CallFrame frame,
            GovernmentCrtBoundary185Api.Memory memory,Ports ports) {
        Objects.requireNonNull(frame);Objects.requireNonNull(memory);Objects.requireNonNull(ports);
        memory.writeQword(frame.childEntry().rspBits(),frame.returnRipBits());
        QueueFp604Api.Outcome offered=(frame.normalRule()==NormalRule.KNOWN_ACTUAL_N
                ?ports.known():ports.opaque()).invoke(frame);
        if(offered==null)throw new IllegalStateException("CALL port did not offer explicit Normal or Stopped");
        if(offered instanceof QueueFp604Api.Normal normal)frame.checkNormalReturn(normal);
        return offered;
    }
}
