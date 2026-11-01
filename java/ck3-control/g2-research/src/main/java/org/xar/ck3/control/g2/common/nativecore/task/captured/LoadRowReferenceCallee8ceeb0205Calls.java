package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class LoadRowReferenceCallee8ceeb0205Calls {
    private LoadRowReferenceCallee8ceeb0205Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        return new Adapter(imageBaseBits, memory, fallback);
    }

    private static final long TARGET_8CEEB0 = 0x8CEEB0L;
    private static final long SITE_337C161 = 0x337C161L;
    private static final long SITE_337C1C3 = 0x337C1C3L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory mem;
        private final GovernmentCrtBoundary185Api.Calls fb;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory mem, GovernmentCrtBoundary185Api.Calls fb) {
            this.image = image; this.mem = mem; this.fb = fb;
        }

        @Override
        public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == TARGET_8CEEB0
                    && (call.callSiteRva() == SITE_337C161 || call.callSiteRva() == SITE_337C1C3)) {
                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                GovernmentCrtBoundary185Api.NormalReturn nr = LoadRowReferenceCallee8ceeb0205.execute(entry, mem, fb);
                if (nr.returnRipBits() != image + call.callSiteRva() + 5L) throw new IllegalArgumentException("Malformed return RIP");
                if (nr.callerRspBits() != call.rspBits()) throw new IllegalArgumentException("Malformed caller RSP");
                if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("Malformed nonvolatile restoration");
                return nr.volatileBits();
            }
            return fb.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return fb.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fb.readGsQword58();
        }
    }
}
