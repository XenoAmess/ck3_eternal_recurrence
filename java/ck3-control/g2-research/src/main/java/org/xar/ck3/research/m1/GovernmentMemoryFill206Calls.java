package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;

public final class GovernmentMemoryFill206Calls {
    private GovernmentMemoryFill206Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bindTail(long imageBase,
            GovernmentMemoryFill206Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls fallback,
            GovernmentCrtBoundary185Api.Calls transferPorts,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x425B87CL && call.targetRva() == 0x4226F10L) {
                    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                            imageBase,
                            call.rspBits() - 8,
                            call.volatileBits(),
                            call.nonvolatileBits());
                    GovernmentCrtBoundary185Api.NormalReturn nr = GovernmentMemoryFill206.execute(
                            entry, memory, transferPorts, budget);
                    if (nr.returnRipBits() != imageBase + 0x425B881L ||
                        nr.callerRspBits() != call.rspBits() ||
                        !nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("Validation failed");
                    }
                    return nr.volatileBits();
                }
                return fallback.invoke(call);
            }
        };
    }
}
