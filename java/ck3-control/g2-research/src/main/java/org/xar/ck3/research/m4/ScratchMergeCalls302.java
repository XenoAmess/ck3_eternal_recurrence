package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;

public final class ScratchMergeCalls302 {
    private ScratchMergeCalls302() { }

    public static Calls bind(Memory memory, Calls fallback, LoopBudget budget) {
        return new CallsImpl(memory, fallback, budget);
    }

    private static final class CallsImpl implements Calls {
        private final Memory memory;
        private final Calls fallback;
        private final LoopBudget budget;

        private CallsImpl(Memory memory, Calls fallback, LoopBudget budget) {
            this.memory = memory;
            this.fallback = fallback;
            this.budget = budget;
        }

        @Override
        public VolatileBits invoke(Call call) {
            return fallback.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            if (transfer.kind() == TargetKind.DIRECT_RVA
                    && transfer.jumpSiteRva() == 0x1A81B9CL
                    && transfer.targetBits() == 0x1A82450L) {
                return ScratchMergeFullState302.execute(transfer.entry(), memory, fallback, budget);
            }
            return fallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }
    }
}