package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class MergeRangeCalls297 {
    private MergeRangeCalls297() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() == 0x1A813C6L && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == 0x1A81AB0L) {
                    long preSP = call.rspBits();
                    long childSP = preSP - 8L;
                    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                        imageBaseBits,
                        childSP,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );
                    GovernmentCrtBoundary185Api.NormalReturn nr = MergeRangeFullState297.execute(entry, memory, fallback, budget);
                    if (nr.returnRipBits() != imageBaseBits + 0x1A813CB) {
                        throw new UnsupportedOperationException("RIP mismatch");
                    }
                    if (nr.callerRspBits() != preSP) {
                        throw new UnsupportedOperationException("SP mismatch");
                    }
                    if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Nonvolatile mismatch");
                    }
                    return nr.volatileBits();
                }
                return fallback.invoke(call);
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                return fallback.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}