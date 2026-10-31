package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class LoadRowReferenceCallees337c203Calls {
    private LoadRowReferenceCallees337c203Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        return new Adapter(imageBaseBits, memory, fallback, budget, floating);
    }

    private static final long TARGET_337C040 = 0x337C040L;
    private static final long TARGET_337C5D0 = 0x337C5D0L;
    private static final long SITE_337BAEA = 0x337BAEAL;
    private static final long SITE_337BB00 = 0x337BB00L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory mem;
        private final GovernmentCrtBoundary185Api.Calls fb;
        private final GovernmentCrtBoundary185Api.LoopBudget bud;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 flt;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory mem, GovernmentCrtBoundary185Api.Calls fb, GovernmentCrtBoundary185Api.LoopBudget bud, LoadRowReferenceCallee337b7e0199Api.Float32 flt) {
            this.image = image; this.mem = mem; this.fb = fb; this.bud = bud; this.flt = flt;
        }

        @Override
        public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                if (call.callSiteRva() == SITE_337BAEA && call.targetBits() == TARGET_337C040) {
                    return run337C040(call);
                }
                if (call.callSiteRva() == SITE_337BB00 && call.targetBits() == TARGET_337C5D0) {
                    return run337C5D0(call);
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

        private VolatileBits run337C040(GovernmentCrtBoundary185Api.Call call) {
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
            GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCallee337c040203.execute(entry, mem, fb);
            validate(call, result);
            return result.volatileBits();
        }

        private VolatileBits run337C5D0(GovernmentCrtBoundary185Api.Call call) {
            GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
            GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCallee337c5d0203.execute(entry, mem, fb, bud, flt);
            validate(call, result);
            return result.volatileBits();
        }

        private void validate(GovernmentCrtBoundary185Api.Call call, GovernmentCrtBoundary185Api.NormalReturn result) {
            if (result.returnRipBits() != image + call.callSiteRva() + 5L) throw new IllegalArgumentException("Malformed return RIP");
            if (result.callerRspBits() != call.rspBits()) throw new IllegalArgumentException("Malformed caller RSP");
            if (!result.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("Malformed nonvolatile restoration");
        }
    }
}
