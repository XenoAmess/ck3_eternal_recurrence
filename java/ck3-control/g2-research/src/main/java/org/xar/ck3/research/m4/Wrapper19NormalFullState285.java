package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m4.Retry60NormalFullState284;

public final class Wrapper19NormalFullState285 {
    private Wrapper19NormalFullState285() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        long image = entry.imageBaseBits();
        long entryS = entry.rspBits();
        long pre = entryS - 0x28L;
        long pushAddr = pre - 8L;
        long returnAddr = image + 0x42242D5L;

        memory.writeQword(pushAddr, returnAddr);

        GovernmentCrtBoundary185Api.Entry calleeEntry = new GovernmentCrtBoundary185Api.Entry(
                image,
                pushAddr,
                entry.volatileBits(),
                entry.nonvolatileBits());

        GovernmentCrtBoundary185Api.NormalReturn calleeNR = Retry60NormalFullState284.execute(
                calleeEntry, memory, calls, budget);

        if (calleeNR.returnRipBits() != returnAddr) {
            throw new UnsupportedOperationException("callee RIP mismatch");
        }
        if (calleeNR.callerRspBits() != pre) {
            throw new UnsupportedOperationException("callee SP mismatch");
        }

        if (!calleeNR.nonvolatileBits().equals(entry.nonvolatileBits())) {
            throw new UnsupportedOperationException("callee N mismatch");
        }

        long rip = memory.readQword(entryS);
        long callerSP = entryS + 8L;

        return new GovernmentCrtBoundary185Api.NormalReturn(
                calleeNR.volatileBits(),
                rip,
                callerSP,
                calleeNR.nonvolatileBits());
    }
}