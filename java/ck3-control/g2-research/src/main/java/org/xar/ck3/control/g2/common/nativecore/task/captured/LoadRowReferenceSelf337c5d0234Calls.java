package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceSelf337c5d0234Calls {
    private LoadRowReferenceSelf337c5d0234Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls originalFallback,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        return new Adapter(image, memory, originalFallback, budget, floating);
    }

    private static final long TARGET_337C5D0 = 0x337C5D0L;
    private static final long SITE_337C7F8 = 0x337C7F8L;
    private static final long SITE_337C8A0 = 0x337C8A0L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls originalFallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls originalFallback,
                GovernmentCrtBoundary185Api.LoopBudget budget,
                LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.image = image;
            this.memory = memory;
            this.originalFallback = originalFallback;
            this.budget = budget;
            this.floating = floating;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == TARGET_337C5D0
                    && (call.callSiteRva() == SITE_337C7F8 || call.callSiteRva() == SITE_337C8A0)) {

                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits());

                GovernmentCrtBoundary185Api.NormalReturn result =
                        LoadRowReferenceCallee337c5d0203.execute(
                                childEntry, memory, this, budget, floating);

                if (result.returnRipBits() != image + call.callSiteRva() + 5L) {
                    throw new IllegalStateException("Malformed return RIP");
                }
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("Malformed caller RSP");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Malformed nonvolatile restoration");
                }

                return result.volatileBits();
            }

            return originalFallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }
    }
}