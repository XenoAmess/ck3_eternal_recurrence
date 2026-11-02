package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class SortRangeCalls300 {
    private SortRangeCalls300() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new Adapter(image, memory, fallback, budget);
    }

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
            this.image = image;
            this.memory = memory;
            this.fallback = fallback;
            this.budget = budget;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x1A81780L
                    && (call.callSiteRva() == 0x1A81363L || call.callSiteRva() == 0x1A81378L)) {
                long site = call.callSiteRva();
                long preSP = call.rspBits();
                long childSP = preSP - 8L;

                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        childSP,
                        call.volatileBits(),
                        call.nonvolatileBits()
                );

                GovernmentCrtBoundary185Api.NormalReturn nr = SortRangeFullState300.execute(
                        childEntry,
                        memory,
                        fallback,
                        budget
                );

                long expectedRIP = image + site + 5L;
                if (nr.returnRipBits() != expectedRIP) {
                    throw new UnsupportedOperationException("Child RIP mismatch");
                }
                if (nr.callerRspBits() != preSP) {
                    throw new UnsupportedOperationException("Child SP mismatch");
                }
                if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new UnsupportedOperationException("Child NonvolatileBits mismatch");
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
    }
}