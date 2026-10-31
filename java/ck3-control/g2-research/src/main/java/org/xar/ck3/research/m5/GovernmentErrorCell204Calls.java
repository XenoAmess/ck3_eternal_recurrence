package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentErrorCell204Calls {
    private GovernmentErrorCell204Calls() { }

    public static Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        return new CallsImpl(imageBaseBits, memory, fallback);
    }

    private static final class CallsImpl implements Calls {
        private final long imageBaseBits;
        private final Memory memory;
        private final Calls fallback;

        CallsImpl(long imageBaseBits, Memory memory, Calls fallback) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x423B18CL
                    && (call.callSiteRva() == 0x425B834L || call.callSiteRva() == 0x424E384L)) {
                long site = call.callSiteRva();
                long rspBits = call.rspBits();
                long entryRspBits = rspBits - 8L;
                Entry entry = new Entry(imageBaseBits, entryRspBits, call.volatileBits(), call.nonvolatileBits());
                NormalReturn result = GovernmentErrorCell204.execute(entry, memory, fallback);
                long expectedRip = imageBaseBits + site + 5L;
                if (result.returnRipBits() != expectedRip) {
                    throw new IllegalStateException("returnRip mismatch");
                }
                if (result.callerRspBits() != rspBits) {
                    throw new IllegalStateException("callerRsp mismatch");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("nonvolatile mismatch");
                }
                return result.volatileBits();
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
