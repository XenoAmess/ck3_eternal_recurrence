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

public final class StackContext424de88226Calls {
    private StackContext424de88226Calls() { }

    public static Calls60 bind(long image, GovernmentCrtBoundary185Api.Memory memory, Calls60 fallback) {
        return new Calls60Impl(image, memory, fallback);
    }

    private static final class Calls60Impl implements Calls60 {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final Calls60 fallback;

        Calls60Impl(long image, GovernmentCrtBoundary185Api.Memory memory, Calls60 fallback) {
            this.image = image;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x4242162L && call.targetBits() == 0x424DE88L) {
                Entry childEntry = new Entry(
                    image,
                    call.rspBits() - 8L,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );
                NormalReturn nr = StackContext424de88226.execute(childEntry, memory, fallback);
                if (nr.returnRipBits() != image + 0x4242167L) {
                    throw new AssertionError("RIP mismatch");
                }
                if (nr.callerRspBits() != call.rspBits()) {
                    throw new AssertionError("SP mismatch");
                }
                if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new AssertionError("NV mismatch");
                }
                return nr.volatileBits();
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

        @Override
        public long readGsQword60() {
            return fallback.readGsQword60();
        }
    }
}