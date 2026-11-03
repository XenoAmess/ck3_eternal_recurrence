package org.xar.ck3.study.m6.postfree251;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** Four actual full-call boundaries in the held61 body, already pushed by the unchanged201 owner. */
public final class FreePostState251Api {
    public static final long FREE61_ENTRY_RVA=0x424E364L;
    private FreePostState251Api() { }

    /** Metadata only: this frame and its factory own no push, target lookup or return-slot read. */
    public record AlreadyPushedCallFrame(long ownerEntryRva,long imageBaseBits,
            GovernmentCrtBoundary185Api.Call call,PostState240Api.Input childInput,
            int instructionLength,long returnRipBits) {
        public AlreadyPushedCallFrame {
            Objects.requireNonNull(call);Objects.requireNonNull(childInput);
            int actualLength=sourceLength(call);
            if(ownerEntryRva!=FREE61_ENTRY_RVA || instructionLength!=actualLength)
                throw new IllegalArgumentException("Not an actual already-pushed held61 CALL");
            GovernmentCrtBoundary185Api.Entry child=childInput.entry();
            if(child.imageBaseBits()!=imageBaseBits || child.rspBits()!=call.rspBits()-8L
                    || !child.volatileBits().equals(call.volatileBits())
                    || !child.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Actual held61 child Entry mismatch");
            if(childInput.originCallSiteRva()!=call.callSiteRva()
                    || returnRipBits!=imageBaseBits+call.callSiteRva()+actualLength)
                throw new IllegalArgumentException("Actual held61 origin/return RIP mismatch");
        }

        /** Ordinary opaque children preserve supplied whole N; their actual post environment is free. */
        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            GovernmentCrtBoundary185Api.NormalReturn nr=actual.base().normalReturn();
            if(nr.returnRipBits()!=returnRipBits || nr.callerRspBits()!=call.rspBits()
                    || !nr.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Actual held61 child normal RIP/SP/N mismatch");
        }
    }

    public static AlreadyPushedCallFrame alreadyPushed(long imageBaseBits,
            GovernmentCrtBoundary185Api.Call actualCall,boolean directionFlagSet,
            QueueFp604Api.Mxcsr mxcsr) {
        int length=sourceLength(Objects.requireNonNull(actualCall));
        GovernmentCrtBoundary185Api.Entry child=new GovernmentCrtBoundary185Api.Entry(imageBaseBits,
                actualCall.rspBits()-8L,actualCall.volatileBits(),actualCall.nonvolatileBits());
        PostState240Api.Input input=new PostState240Api.Input(child,directionFlagSet,mxcsr,
                actualCall.callSiteRva());
        return new AlreadyPushedCallFrame(FREE61_ENTRY_RVA,imageBaseBits,actualCall,input,length,
                imageBaseBits+actualCall.callSiteRva()+length);
    }

    private static int sourceLength(GovernmentCrtBoundary185Api.Call call) {
        long site=call.callSiteRva();
        if((site==0x424E37AL || site==0x424E38CL)
                && call.kind()==GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE)return 6;
        if(call.kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                && ((site==0x424E384L && call.targetBits()==0x423B18CL)
                    || (site==0x424E394L && call.targetBits()==0x423B0D4L)))return 5;
        throw new IllegalArgumentException("No held61 source CALL at supplied site/kind/target");
    }

    public interface Children {
        /** Same actual RAM. Every reached child supplies a complete explicit Outcome. */
        QueueFp604Api.Outcome invoke(AlreadyPushedCallFrame frame,GovernmentCrtBoundary185Api.Memory sameMemory);
    }
}
