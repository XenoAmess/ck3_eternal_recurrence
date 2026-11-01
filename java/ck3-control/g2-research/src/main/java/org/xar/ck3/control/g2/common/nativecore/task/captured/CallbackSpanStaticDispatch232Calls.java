package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalAbort4242284215.Calls60;

public final class CallbackSpanStaticDispatch232Calls {
    private CallbackSpanStaticDispatch232Calls() { }

    public static Calls60 bind(long image, Calls60 originalFallback) {
        return new Calls60Impl(image, originalFallback);
    }

    private static final class Calls60Impl implements Calls60 {
        private final long image;
        private final Calls60 originalFallback;

        Calls60Impl(long image, Calls60 originalFallback) {
            this.image = image;
            this.originalFallback = originalFallback;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.INDIRECT_ABSOLUTE
                    && call.callSiteRva() == 0x424E1E9L
                    && call.targetBits() == image + 0x4267630L) {
                Entry childEntry = new Entry(
                    image,
                    call.rspBits() - 8L,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );
                NormalReturn actualNR = RequestStaticDispatch4267630232.execute(childEntry, originalFallback);
                if (actualNR.returnRipBits() != image + 0x424E1EFL) {
                    throw new AssertionError("RIP mismatch");
                }
                if (actualNR.callerRspBits() != call.rspBits()) {
                    throw new AssertionError("SP mismatch");
                }
                if (!actualNR.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new AssertionError("NV mismatch");
                }
                return actualNR.volatileBits();
            }
            return originalFallback.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }

        @Override
        public long readGsQword60() {
            return originalFallback.readGsQword60();
        }
    }
}