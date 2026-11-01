package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class LoadRowReferenceSwap238Calls {
    private LoadRowReferenceSwap238Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory sameMemory, GovernmentCrtBoundary185Api.Calls originalFallback) {
        return new Adapter(image, sameMemory, originalFallback);
    }

    private static final long TARGET_A636F0 = 0xA636F0L;
    private static final long CALL_SITE_337C784 = 0x337C784L;
    private static final long CALL_SITE_337C7CF = 0x337C7CFL;

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
        public VolatileBits invoke(Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == TARGET_A636F0
                    && (call.callSiteRva() == CALL_SITE_337C784 || call.callSiteRva() == CALL_SITE_337C7CF)) {
                long preSP = call.rspBits();
                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                    image,
                    preSP - 8L,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );
                NormalReturn nr = LoadRowReferenceCalleeA636f0200.execute(childEntry, this.memory, this.fallback);
                long expectedRip = image + call.callSiteRva() + 5L;
                if (nr.returnRipBits() != expectedRip) throw new IllegalStateException("Malformed returnRipBits");
                if (nr.callerRspBits() != preSP) throw new IllegalStateException("Malformed callerRspBits");
                if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalStateException("Malformed restoredNonvolatile");
                return nr.volatileBits();
            }
            return fallback.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            return fallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }
    }
}