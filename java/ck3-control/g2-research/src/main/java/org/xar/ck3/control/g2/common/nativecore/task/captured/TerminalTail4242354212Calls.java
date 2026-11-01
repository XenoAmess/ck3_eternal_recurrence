package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class TerminalTail4242354212Calls {
    private TerminalTail4242354212Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback) {
        return new Adapter(image, memory, fallback);
    }

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
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.callSiteRva() == 0x4232D44L
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x4242354L) {
                GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits());

                GovernmentCrtBoundary185Api.NormalReturn actual =
                        TerminalTail4242354212.execute(child, memory, fallback);

                if (actual.returnRipBits() != image + 0x4232D49L) {
                    throw new IllegalStateException("returnRipBits mismatch");
                }
                if (actual.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("callerRspBits mismatch");
                }
                if (!actual.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("nonvolatileBits mismatch");
                }

                return actual.volatileBits();
            }
            return fallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return fallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }
    }
}