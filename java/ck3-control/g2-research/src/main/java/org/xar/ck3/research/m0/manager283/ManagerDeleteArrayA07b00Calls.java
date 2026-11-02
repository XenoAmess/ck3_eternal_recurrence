package org.xar.ck3.research.m0.manager283;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Only the held direct call28EE683; all target virtual calls remain opaque. */
public final class ManagerDeleteArrayA07b00Calls {
    private ManagerDeleteArrayA07b00Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if(call.callSiteRva()!=0x28EE683L
                        || call.kind()!=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || call.targetBits()!=0xA07B00L) return fallback.invoke(call);
                long expectedRip=imageBaseBits+0x28EE688L;
                long entryRsp=call.rspBits()-8L;
                if(memory.readQword(entryRsp)!=expectedRip)
                    throw new IllegalStateException("existing CALL return slot mismatch");
                GovernmentCrtBoundary185Api.NormalReturn result=ManagerDeleteArrayA07b00.execute(
                        new GovernmentCrtBoundary185Api.Entry(imageBaseBits,entryRsp,
                                call.volatileBits(),call.nonvolatileBits()),memory,fallback,budget);
                if(result.returnRipBits()!=expectedRip || result.callerRspBits()!=call.rspBits()
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
