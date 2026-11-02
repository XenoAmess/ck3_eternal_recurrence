package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

public final class GeneralBridgeCall294 {
    private GeneralBridgeCall294() { }

    public static void invoke(long imageBaseBits, Registers r, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls, GovernmentCrtBoundary185Api.LoopBudget budget) {
        long preSP = r.rsp;
        long childSP = preSP - 8L;
        memory.writeQword(childSP, imageBaseBits + 0x1A830B9L);

        var offeredV = r.volatileBits();
        var offeredN = r.nonvolatileBits();

        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                imageBaseBits,
                childSP,
                offeredV,
                offeredN
        );

        GovernmentCrtBoundary185Api.NormalReturn ret = BridgeFullState293.execute(childEntry, memory, calls, budget);

        if (ret.returnRipBits() != imageBaseBits + 0x1A830B9L) {
            throw new UnsupportedOperationException("Invalid return RIP");
        }
        if (ret.callerRspBits() != preSP) {
            throw new UnsupportedOperationException("Invalid caller RSP");
        }
        if (!ret.nonvolatileBits().equals(offeredN)) {
            throw new UnsupportedOperationException("Invalid nonvolatile bits");
        }

        r.apply(ret.volatileBits());
    }
}