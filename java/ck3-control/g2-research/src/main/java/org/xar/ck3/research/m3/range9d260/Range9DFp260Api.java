package org.xar.ck3.research.m3.range9d260;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Exact three normal CALL boundaries of the held 126-byte function. */
public final class Range9DFp260Api {
    private Range9DFp260Api() { }
    public interface Memory extends FullCopy437Api.Memory { }
    public record CallFrame(GovernmentCrtBoundary185Api.Call call,
            GovernmentCrtBoundary185Api.Entry childEntry, boolean directionFlagSet,
            QueueFp604Api.Mxcsr preMxcsr, int instructionLength, long returnRipBits) {
        public CallFrame {
            Objects.requireNonNull(call);Objects.requireNonNull(childEntry);Objects.requireNonNull(preMxcsr);
            long site=call.callSiteRva();
            if(site!=0x9D0998L&&site!=0x9D09A3L&&site!=0x9D09AEL)
                throw new IllegalArgumentException("Unknown range call site");
            if(call.kind()!=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA||call.targetBits()!=0x4220AA4L||instructionLength!=5)
                throw new IllegalArgumentException("Invalid range call transfer");
            if(childEntry.rspBits()!=call.rspBits()-8||!childEntry.volatileBits().equals(call.volatileBits())||!childEntry.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Contradictory range child state");
            if(returnRipBits!=childEntry.imageBaseBits()+site+5)
                throw new IllegalArgumentException("Invalid range return RIP");
        }
        public void checkNormalReturn(QueueFp604Api.Normal offered) {
            Objects.requireNonNull(offered);
            var actual=offered.base().normalReturn();
            if(actual.returnRipBits()!=returnRipBits||actual.callerRspBits()!=call.rspBits()||!actual.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Contradictory range normal return");
        }
    }
    @FunctionalInterface public interface Calls {QueueFp604Api.Outcome invoke(CallFrame frame);}
}
