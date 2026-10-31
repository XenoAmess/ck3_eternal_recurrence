package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class LoadRowReferenceCallee337b7e0199Calls {
    private LoadRowReferenceCallee337b7e0199Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        if (memory == null) throw new NullPointerException("memory");
        if (delegate == null) throw new NullPointerException("delegate");
        if (budget == null) throw new NullPointerException("budget");
        if (floating == null) throw new NullPointerException("floating");
        return new Adapter(imageBaseBits, memory, delegate, budget, floating);
    }

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBaseBits;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls delegate;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        Adapter(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.delegate = delegate;
            this.budget = budget;
            this.floating = floating;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.callSiteRva() == 0x34EF8C5L && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == 0x337B7E0L) {
                long nextRip = imageBaseBits + 0x34EF8CAL;
                long callerRsp = call.rspBits();
                long childRsp = callerRsp - 8L;
                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(imageBaseBits, childRsp, call.volatileBits(), call.nonvolatileBits());
                GovernmentCrtBoundary185Api.NormalReturn ret = LoadRowReferenceCallee337b7e0199.execute(entry, memory, delegate, budget, floating);
                if (ret.returnRipBits() != nextRip) throw new IllegalStateException("RIP mismatch");
                if (ret.callerRspBits() != callerRsp) throw new IllegalStateException("RSP mismatch");
                if (!ret.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalStateException("NV mismatch");
                return ret.volatileBits();
            }
            return delegate.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return delegate.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }
    }
}
