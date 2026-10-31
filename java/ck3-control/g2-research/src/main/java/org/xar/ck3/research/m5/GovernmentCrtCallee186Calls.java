package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentCrtCallee186Calls {
    private GovernmentCrtCallee186Calls() { }

    public static Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        return new CallsImpl(imageBaseBits, memory, fallback);
    }

    private static final class CallsImpl implements Calls {
        private final long image;
        private final Memory mem;
        private final Calls fb;

        CallsImpl(long imageBaseBits, Memory memory, Calls fallback) {
            this.image = imageBaseBits;
            this.mem = memory;
            this.fb = fallback;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x4223F28L && call.targetBits() == 0x4223EE8L) {
                Entry entry = new Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                NormalReturn result = GovernmentCrtCallee186.execute(entry, mem, fb);
                if (result.returnRipBits() != image + 0x4223F2DL || result.callerRspBits() != call.rspBits() || !result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Validation mismatch");
                }
                return result.volatileBits();
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