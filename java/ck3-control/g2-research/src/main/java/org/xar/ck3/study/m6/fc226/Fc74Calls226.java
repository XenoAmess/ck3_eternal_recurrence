package org.xar.ck3.study.m6.fc226;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.study.m6.fc226.Fc74FullState226;

public final class Fc74Calls226 {
    private Fc74Calls226() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        return new CallsImpl(image, memory, fallback);
    }

    private static final class CallsImpl implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;

        CallsImpl(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
            this.image = image;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.callSiteRva() == 0x423B190L
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x424FC74L) {
                long childSP = call.rspBits() - 0x8L;
                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        childSP,
                        call.volatileBits(),
                        call.nonvolatileBits());
                GovernmentCrtBoundary185Api.NormalReturn nr = Fc74FullState226.execute(entry, memory, fallback);

                long expectedRip = image + 0x423B195L;
                if (nr.returnRipBits() != expectedRip) {
                    throw new IllegalStateException("returnRip mismatch");
                }
                if (nr.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("callerRsp mismatch");
                }
                if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("nonvolatile mismatch");
                }

                return nr.volatileBits();
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