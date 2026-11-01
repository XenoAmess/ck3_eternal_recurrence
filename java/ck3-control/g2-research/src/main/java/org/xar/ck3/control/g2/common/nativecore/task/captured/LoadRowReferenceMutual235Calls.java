package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceMutual235Calls {
    private LoadRowReferenceMutual235Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        return new SourceBus(image, memory, originalFallback, budget, floating);
    }

    private static final long TARGET_337C0C0 = 0x337C0C0L;
    private static final long TARGET_337C5D0 = 0x337C5D0L;
    private static final long SITE_337C882 = 0x337C882L;
    private static final long SITE_337BB8B = 0x337BB8BL;
    private static final long SITE_337C198 = 0x337C198L;
    private static final long SITE_337C7F8 = 0x337C7F8L;
    private static final long SITE_337C8A0 = 0x337C8A0L;
    private static final long JUMP_337C064 = 0x337C064L;

    private static final class SourceBus implements GovernmentCrtBoundary185Api.Calls {
        private final GovernmentCrtBoundary185Api.Calls a204;
        private final GovernmentCrtBoundary185Api.Calls a205;
        private final GovernmentCrtBoundary185Api.Calls a234;
        private final GovernmentCrtBoundary185Api.Calls originalFallback;

        SourceBus(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.originalFallback = originalFallback;
            this.a204 = LoadRowReferenceCallee337c0c0204Calls.bind(image, memory, this, budget);
            this.a205 = LoadRowReferenceCallee337c5d0FromC0c0205Calls.bind(image, memory, this, budget, floating);
            this.a234 = LoadRowReferenceSelf337c5d0234Calls.bind(image, memory, this, budget, floating);
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                if (call.targetBits() == TARGET_337C0C0 && (call.callSiteRva() == SITE_337C882 || call.callSiteRva() == SITE_337BB8B)) {
                    return a204.invoke(call);
                }
                if (call.targetBits() == TARGET_337C5D0 && call.callSiteRva() == SITE_337C198) {
                    return a205.invoke(call);
                }
                if (call.targetBits() == TARGET_337C5D0 && (call.callSiteRva() == SITE_337C7F8 || call.callSiteRva() == SITE_337C8A0)) {
                    return a234.invoke(call);
                }
            }
            return originalFallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && transfer.targetBits() == TARGET_337C0C0 && transfer.jumpSiteRva() == JUMP_337C064) {
                return a204.tail(transfer);
            }
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }
    }
}