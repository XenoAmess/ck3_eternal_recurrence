package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;

public final class Callee4259250FullState203Calls {
    public static Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        return new CallsImpl(imageBaseBits, memory, fallback);
    }

    private static final class CallsImpl implements Calls {
        private final long imageBase;
        private final Memory mem;
        private final Calls fb;

        CallsImpl(long imageBaseBits, Memory memory, Calls fallback) {
            this.imageBase = imageBaseBits;
            this.mem = memory;
            this.fb = fallback;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x425B848L && call.targetBits() == 0x4259250L) {
                long childRsp = call.rspBits() - 8L;
                Entry childEntry = new Entry(imageBase, childRsp, call.volatileBits(), call.nonvolatileBits());
                NormalReturn nr = Callee4259250FullState203.execute(childEntry, mem, fb);
                if (nr.returnRipBits() != imageBase + 0x425B84DL) {
                    throw new IllegalStateException("RIP mismatch");
                }
                if (nr.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("SP mismatch");
                }
                if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("N mismatch");
                }
                return nr.volatileBits();
            }
            return fb.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            return fb.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fb.readGsQword58();
        }
    }
}