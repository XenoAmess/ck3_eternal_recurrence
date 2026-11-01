package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class LoadRowReferenceCallee337c0c0204Calls {
    private LoadRowReferenceCallee337c0c0204Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new Adapter(image, memory, fallback, budget);
    }

    private static final long TARGET_337C0C0 = 0x337C0C0L;
    private static final long SITE_337C882 = 0x337C882L;
    private static final long SITE_337BB8B = 0x337BB8BL;
    private static final long JUMP_337C064 = 0x337C064L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory mem;
        private final GovernmentCrtBoundary185Api.Calls fb;
        private final GovernmentCrtBoundary185Api.LoopBudget bud;

        Adapter(long image, GovernmentCrtBoundary185Api.Memory mem, GovernmentCrtBoundary185Api.Calls fb, GovernmentCrtBoundary185Api.LoopBudget bud) {
            this.image = image; this.mem = mem; this.fb = fb; this.bud = bud;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == TARGET_337C0C0) {
                if (call.callSiteRva() == SITE_337C882 || call.callSiteRva() == SITE_337BB8B) {
                    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                    GovernmentCrtBoundary185Api.NormalReturn nr = LoadRowReferenceCallee337c0c0204.execute(entry, mem, fb, bud);
                    if (nr.returnRipBits() != image + call.callSiteRva() + 5L) throw new IllegalArgumentException("Malformed return RIP");
                    if (nr.callerRspBits() != call.rspBits()) throw new IllegalArgumentException("Malformed caller RSP");
                    if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("Malformed nonvolatile restoration");
                    return nr.volatileBits();
                }
            }
            return fb.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && transfer.targetBits() == TARGET_337C0C0 && transfer.jumpSiteRva() == JUMP_337C064) {
                return LoadRowReferenceCallee337c0c0204.execute(transfer.entry(), mem, fb, bud);
            }
            return fb.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fb.readGsQword58();
        }
    }
}