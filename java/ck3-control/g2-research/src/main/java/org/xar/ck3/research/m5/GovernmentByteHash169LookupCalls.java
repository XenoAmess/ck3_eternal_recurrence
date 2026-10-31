package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.Entry;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.Memory;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.CallFrame;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.CallPost;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Calls;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.StaticRva;

/** Owner exact31F9 consumer; full455B integer source proves normal XMM/MXCSR preservation. */
public final class GovernmentByteHash169LookupCalls {
    private GovernmentByteHash169LookupCalls() { }
    public static Calls bind(long image,Memory memory,Calls fallback,LoopBudget budget) {
        Objects.requireNonNull(memory);Objects.requireNonNull(fallback);Objects.requireNonNull(budget);
        return new Calls() {
            @Override public long readGsQword58() {return fallback.readGsQword58();}
            @Override public CallPost invoke(CallFrame call) {
                Objects.requireNonNull(call);
                if(call.callSiteRva()!=0x30a31f9L||!(call.target() instanceof StaticRva target)
                        ||target.targetRva()!=0x3f7e220L)return fallback.invoke(call);
                long rip=image+0x30a31feL;
                memory.writeQword(call.frameRspBits()-8,rip);
                var result=GovernmentByteHash169.execute(new Entry(image,call.frameRspBits()-8,
                        call.volatileBits(),call.nonvolatileBits(),call.mxcsr()),memory,budget);
                if(result.returnRipBits()!=rip||result.callerRspBits()!=call.frameRspBits()
                        ||!result.nonvolatileBits().equals(call.nonvolatileBits())||!result.mxcsr().equals(call.mxcsr())) {
                    throw new UnsupportedOperationException("hash wrapper normal CALL boundary mismatch");
                }
                return new CallPost(result.volatileBits(),result.mxcsr());
            }
        };
    }
}
