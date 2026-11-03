package org.xar.ck3.study.m6.postvtable247;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Exact51/58 normal-source boundaries. Child post-state stays explicit; no legacy NR adapter. */
public final class PostVtable247Api {
    private PostVtable247Api() { }

    /** Unknown DF cannot be encoded as false; partial MXCSR knowledge remains explicit. */
    public record Input(GovernmentCrtBoundary185Api.Entry entry,boolean directionFlagSet,
            QueueFp604Api.Mxcsr mxcsr,long originCallSiteRva) {
        public Input { Objects.requireNonNull(entry);Objects.requireNonNull(mxcsr); }
    }

    /** Actual preSP Call plus post-push child Input. Only three held source CALL sites exist. */
    public record CallFrame(long ownerEntryRva,long imageBaseBits,
            GovernmentCrtBoundary185Api.Call call,Input childInput,
            int instructionLength,long returnRipBits) {
        public CallFrame {
            Objects.requireNonNull(call);Objects.requireNonNull(childInput);
            int sourceLength;
            if(ownerEntryRva==0x855870L && call.callSiteRva()==0x855883L)sourceLength=3;
            else if(ownerEntryRva==0x855830L && call.callSiteRva()==0x85584CL)sourceLength=3;
            else if(ownerEntryRva==0x855830L && call.callSiteRva()==0x85585BL)sourceLength=4;
            else throw new IllegalArgumentException("Not an exact held51/58 CALL");
            if(call.kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                    || instructionLength!=sourceLength)
                throw new IllegalArgumentException("Actual indirect CALL encoding mismatch");
            GovernmentCrtBoundary185Api.Entry child=childInput.entry();
            if(child.imageBaseBits()!=imageBaseBits || child.rspBits()!=call.rspBits()-8L)
                throw new IllegalArgumentException("Actual child image/post-push SP mismatch");
            if(!child.volatileBits().equals(call.volatileBits())
                    || !child.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Actual child whole V/N mismatch");
            if(childInput.originCallSiteRva()!=call.callSiteRva())
                throw new IllegalArgumentException("New CALL must supply its own actual source origin");
            if(returnRipBits!=imageBaseBits+call.callSiteRva()+sourceLength)
                throw new IllegalArgumentException("Actual source return RIP mismatch");
        }

        /** Opaque normal child contract; no DF/MXCSR preservation is guessed by this check. */
        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            GovernmentCrtBoundary185Api.NormalReturn nr=actual.base().normalReturn();
            if(nr.returnRipBits()!=returnRipBits || nr.callerRspBits()!=call.rspBits())
                throw new IllegalArgumentException("Opaque normal child return RIP/SP mismatch");
            if(!nr.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Opaque normal child did not preserve supplied whole N");
        }
    }

    /**
     * Tail JMP transfers the existing continuation. It owns no push, source RET or new return RIP.
     * targetInput.origin remains the incoming continuation CALL origin; jumpSiteRva is separate.
     */
    public record TailFrame(long ownerEntryRva,GovernmentCrtBoundary185Api.Tail transfer,
            Input targetInput,int instructionLength) {
        public TailFrame {
            Objects.requireNonNull(transfer);Objects.requireNonNull(targetInput);
            if(ownerEntryRva!=0x855870L || transfer.jumpSiteRva()!=0x8558A0L
                    || instructionLength!=3
                    || transfer.kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE)
                throw new IllegalArgumentException("Not exact held51 JMP R9");
            if(!targetInput.entry().equals(transfer.entry()))
                throw new IllegalArgumentException("Tail must retain exact current target Entry/SP");
            if(transfer.targetBits()!=transfer.entry().volatileBits().r9Bits())
                throw new IllegalArgumentException("Tail target is not actual current R9");
        }
    }

    public interface Children {
        /** Only explicitly qualified opaque children; sameMemory is the actual producer RAM object. */
        QueueFp604Api.Outcome invoke(CallFrame frame,GovernmentCrtBoundary185Api.Memory sameMemory);
        /** Owns the tail target's complete continuation and any actual RET; no caller rebuilding. */
        QueueFp604Api.Outcome tail(TailFrame frame,GovernmentCrtBoundary185Api.Memory sameMemory);
    }
}
