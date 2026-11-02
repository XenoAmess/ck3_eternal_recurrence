package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

public final class BridgeRotateCall293 {
    private BridgeRotateCall293() { }

    public static void invoke(long imageBaseBits, Registers registers, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls, GovernmentCrtBoundary185Api.LoopBudget budget) {
        long preSP = registers.rsp;
        long childSP = preSP - 8L;
        long expectedRip = imageBaseBits + 0x1A83327L;

        memory.writeQword(childSP, expectedRip);

        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                imageBaseBits,
                childSP,
                registers.volatileBits(),
                registers.nonvolatileBits()
        );

        GovernmentCrtBoundary185Api.NormalReturn nr = RotateFullState292.execute(childEntry, memory, calls, budget);

        if (nr.returnRipBits() != expectedRip) {
            throw new UnsupportedOperationException("RIP mismatch");
        }
        if (nr.callerRspBits() != preSP) {
            throw new UnsupportedOperationException("SP mismatch");
        }
        if (!nr.nonvolatileBits().equals(childEntry.nonvolatileBits())) {
            throw new UnsupportedOperationException("N mismatch");
        }

        registers.apply(nr.volatileBits());
    }
}