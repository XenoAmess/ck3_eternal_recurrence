package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class LoadRowReferenceTransfer237Calls {
    private LoadRowReferenceTransfer237Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback) {
        return new Adapter(image, memory, originalFallback);
    }

    private static final long TARGET_87C9B0 = 0x87C9B0L;
    private static final long TARGET_E23EA0 = 0xE23EA0L;
    private static final long SITE_337C6EA = 0x337C6EAL;
    private static final long SITE_337C71D = 0x337C71DL;
    private static final long SITE_337C843 = 0x337C843L;
    private static final long SITE_337C6FC = 0x337C6FCL;
    private static final long SITE_337C72F = 0x337C72FL;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
            this.image = image;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                if (call.targetBits() == TARGET_87C9B0 && (call.callSiteRva() == SITE_337C6EA || call.callSiteRva() == SITE_337C71D || call.callSiteRva() == SITE_337C843)) {
                    return execute87C9B0(call);
                }
                if (call.targetBits() == TARGET_E23EA0 && (call.callSiteRva() == SITE_337C6FC || call.callSiteRva() == SITE_337C72F)) {
                    return executeE23EA0(call);
                }
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

        private GovernmentPrimaryTail155Api.VolatileBits execute87C9B0(GovernmentCrtBoundary185Api.Call call) {
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
            GovernmentCrtBoundary185Api.NormalReturn nr = LoadRowReferenceCallee87c9b0201.execute(entry, memory, fallback);
            if (nr.returnRipBits() != image + call.callSiteRva() + 5L) throw new IllegalArgumentException("Malformed return RIP");
            if (nr.callerRspBits() != call.rspBits()) throw new IllegalArgumentException("Malformed caller RSP");
            if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("Malformed nonvolatile restoration");
            return nr.volatileBits();
        }

        private GovernmentPrimaryTail155Api.VolatileBits executeE23EA0(GovernmentCrtBoundary185Api.Call call) {
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
            GovernmentCrtBoundary185Api.NormalReturn nr = LoadRowReferenceCalleeE23ea0202.execute(entry, memory, fallback);
            if (nr.returnRipBits() != image + call.callSiteRva() + 5L) throw new IllegalArgumentException("Malformed return RIP");
            if (nr.callerRspBits() != call.rspBits()) throw new IllegalArgumentException("Malformed caller RSP");
            if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("Malformed nonvolatile restoration");
            return nr.volatileBits();
        }
    }
}