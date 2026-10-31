package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;

public final class GovernmentMemoryFillRep207Calls {
    private GovernmentMemoryFillRep207Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            GovernmentMemoryFill206Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            boolean directionFlagSet,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                return fallback.invoke(call);
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                if (transfer.jumpSiteRva() == 0x4226F57L &&
                    transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    transfer.targetBits() == 0x4226EF0L) {
                    return GovernmentMemoryFillRep207.execute(
                        transfer.entry(),
                        memory,
                        directionFlagSet,
                        budget
                    );
                }
                return fallback.tail(transfer);
            }
        };
    }
}
