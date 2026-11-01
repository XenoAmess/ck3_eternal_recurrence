package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class CapacityIndex86e160204Calls {
    private CapacityIndex86e160204Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        return new Adapter(image, memory, fallback);
    }

    private static final long TARGET_86E160 = 0x86E160L;
    private static final long SITE_337BB7C = 0x337BB7CL;
    private static final long SITE_337C051 = 0x337C051L;
    private static final long SITE_337C873 = 0x337C873L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory mem;
        private final GovernmentCrtBoundary185Api.Calls fb;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory mem, GovernmentCrtBoundary185Api.Calls fb) {
            this.image = image;
            this.mem = mem;
            this.fb = fb;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == TARGET_86E160) {
                long site = call.callSiteRva();
                if (site == SITE_337BB7C || site == SITE_337C051 || site == SITE_337C873) {
                    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );
                    GovernmentCrtBoundary185Api.NormalReturn result = CapacityIndex86e160204.execute(entry, mem);
                    validate(call, result);
                    return result.volatileBits();
                }
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

        private void validate(GovernmentCrtBoundary185Api.Call call, GovernmentCrtBoundary185Api.NormalReturn result) {
            if (result.returnRipBits() != image + call.callSiteRva() + 5L) throw new IllegalArgumentException("Malformed return RIP");
            if (result.callerRspBits() != call.rspBits()) throw new IllegalArgumentException("Malformed caller RSP");
            if (!result.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("Malformed nonvolatile restoration");
        }
    }
}