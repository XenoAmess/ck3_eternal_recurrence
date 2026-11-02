package org.xar.ck3.research.m0.lifecycle285;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Only the actual manager52B wrapper's direct destructor CALL. */
public final class ManagerDestructorCalls285 {
    private ManagerDestructorCalls285() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if(call.callSiteRva()!=0x28EE5DFL
                        || call.kind()!=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || call.targetBits()!=0x28EE610L) return fallback.invoke(call);
                long expected=imageBaseBits+0x28EE5E4L,entryRsp=call.rspBits()-8L;
                if(memory.readQword(entryRsp)!=expected)
                    throw new IllegalStateException("existing CALL return slot mismatch");
                GovernmentCrtBoundary185Api.NormalReturn result=ManagerDestructor28ee610.execute(
                        new GovernmentCrtBoundary185Api.Entry(imageBaseBits,entryRsp,
                                call.volatileBits(),call.nonvolatileBits()),memory,fallback,budget);
                if(result.returnRipBits()!=expected || result.callerRspBits()!=call.rspBits()
                        || !result.nonvolatileBits().equals(call.nonvolatileBits()))
                    throw new IllegalStateException("normal return boundary mismatch");
                return result.volatileBits();
            }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                return fallback.tail(transfer);
            }
            @Override public long readGsQword58() { return fallback.readGsQword58(); }
        };
    }
}
