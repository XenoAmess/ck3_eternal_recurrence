package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceCallee337c5d0FromC0c0205Calls {
    private LoadRowReferenceCallee337c5d0FromC0c0205Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        return new Adapter(imageBaseBits, memory, fallback, budget, floating);
    }

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBaseBits;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        Adapter(long imageBaseBits,
                GovernmentCrtBoundary185Api.Memory memory,
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
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.callSiteRva() == 0x337C198L
                    && call.targetBits() == 0x337C5D0L) {
                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        imageBaseBits,
                        call.rspBits() - 8,
                        call.volatileBits(),
                        call.nonvolatileBits());
                GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCallee337c5d0203.execute(
                        childEntry, memory, fallback, budget, floating);
                if (result.returnRipBits() != imageBaseBits + 0x337C198L + 5L) {
                    throw new IllegalStateException("Return RIP mismatch");
                }
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("Caller RSP mismatch");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Nonvolatile mismatch");
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