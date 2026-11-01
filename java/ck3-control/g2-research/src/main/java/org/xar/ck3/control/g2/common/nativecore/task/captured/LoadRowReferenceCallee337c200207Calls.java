package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class LoadRowReferenceCallee337c200207Calls {
    private LoadRowReferenceCallee337c200207Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        return new Adapter(imageBaseBits, memory, fallback, budget, floating);
    }

    private static final long TARGET_337C200 = 0x337C200L;
    private static final long CALL_SITE_337BBA6 = 0x337BBA6L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBaseBits;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        Adapter(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls fallback,
                GovernmentCrtBoundary185Api.LoopBudget budget,
                LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.fallback = fallback;
            this.budget = budget;
            this.floating = floating;
        }

        @Override
        public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.callSiteRva() == CALL_SITE_337BBA6
                    && call.targetBits() == TARGET_337C200) {

                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                        imageBaseBits,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits());

                GovernmentCrtBoundary185Api.NormalReturn result =
                        LoadRowReferenceCallee337c200207.execute(
                                entry, memory, fallback, budget, floating);

                long expectedReturnRip = imageBaseBits + call.callSiteRva() + 5L;
                if (result.returnRipBits() != expectedReturnRip) {
                    throw new IllegalArgumentException("Malformed return RIP");
                }
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalArgumentException("Malformed caller RSP");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalArgumentException("Malformed nonvolatile restoration");
                }

                return result.volatileBits();
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
