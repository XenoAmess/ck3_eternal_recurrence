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
import org.xar.ck3.research.m1.GovernmentIndexedTails198;

public final class StackResultIndexedTails229Calls {
    private StackResultIndexedTails229Calls() { }

    public static Calls60 bind(long image, GovernmentCrtBoundary185Api.Memory memory, Calls60 originalFallback) {
        return new Calls60Impl(image, memory, originalFallback);
    }

    private static final class Calls60Impl implements Calls60 {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final Calls60 originalFallback;

        Calls60Impl(long image, GovernmentCrtBoundary185Api.Memory memory, Calls60 originalFallback) {
            this.image = image;
            this.memory = Objects.requireNonNull(memory);
            this.originalFallback = Objects.requireNonNull(originalFallback);
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA) {
                if (call.callSiteRva() == 0x424DB8BL && call.targetBits() == 0x4247FFCL) {
                    Entry childEntry = new Entry(
                        image,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );
                    NormalReturn nr = GovernmentIndexedTails198.tail4247ffc(childEntry, memory, originalFallback);
                    if (nr.returnRipBits() != image + 0x424DB90L) {
                        throw new AssertionError("RIP mismatch for 4247FFC");
                    }
                    if (nr.callerRspBits() != call.rspBits()) {
                        throw new AssertionError("SP mismatch for 4247FFC");
                    }
                    if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new AssertionError("NV mismatch for 4247FFC");
                    }
                    return nr.volatileBits();
                } else if (call.callSiteRva() == 0x424DB9DL && call.targetBits() == 0x4248050L) {
                    Entry childEntry = new Entry(
                        image,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );
                    NormalReturn nr = GovernmentIndexedTails198.tail4248050(childEntry, memory, originalFallback);
                    if (nr.returnRipBits() != image + 0x424DBA2L) {
                        throw new AssertionError("RIP mismatch for 4248050");
                    }
                    if (nr.callerRspBits() != call.rspBits()) {
                        throw new AssertionError("SP mismatch for 4248050");
                    }
                    if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new AssertionError("NV mismatch for 4248050");
                    }
                    return nr.volatileBits();
                }
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