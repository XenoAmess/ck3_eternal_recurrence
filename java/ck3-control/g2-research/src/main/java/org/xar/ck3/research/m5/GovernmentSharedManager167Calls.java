package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentSharedManager167Calls {
    private static final long TARGET_SITE = 0x3F8A7E0L;

    public static Calls bind(long imageBaseBits, GovernmentSharedManager167Api.Memory memory, Calls delegate) {
        return new Adapter(imageBaseBits, memory, delegate);
    }

    private static final class Adapter implements Calls {
        private final long imageBaseBits;
        private final GovernmentSharedManager167Api.Memory memory;
        private final Calls delegate;

        Adapter(long imageBaseBits, GovernmentSharedManager167Api.Memory memory, Calls delegate) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.delegate = delegate;
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }

        @Override
        public VolatileBits invoke(OpaqueCall call) {
            if (call.targetRva() == TARGET_SITE) {
                return handleTargetCall(call);
            }
            return delegate.invoke(call);
        }

        private VolatileBits handleTargetCall(OpaqueCall call) {
            long p = call.rspBits();
            long returnAddr = imageBaseBits + call.callSiteRva() + 5L;
            long s = p - 8L;
            memory.writeQword(s, returnAddr);

            Entry entry = new Entry(imageBaseBits, s, call.volatileBits(), call.nonvolatileBits());
            NormalReturn result = GovernmentSharedManager167.execute(entry, memory, delegate);

            long expectedRip = imageBaseBits + call.callSiteRva() + 5L;
            if (result.returnRipBits() != expectedRip) {
                throw new UnsupportedOperationException("Target returned unexpected RIP");
            }
            if (result.callerRspBits() != p) {
                throw new UnsupportedOperationException("Target returned unexpected caller RSP");
            }

            NonvolatileBits incoming = call.nonvolatileBits();
            NonvolatileBits restored = result.nonvolatileBits();
            if (incoming.rbxBits() != restored.rbxBits() ||
                incoming.rbpBits() != restored.rbpBits() ||
                incoming.rsiBits() != restored.rsiBits() ||
                incoming.rdiBits() != restored.rdiBits() ||
                incoming.r12Bits() != restored.r12Bits() ||
                incoming.r13Bits() != restored.r13Bits() ||
                incoming.r14Bits() != restored.r14Bits() ||
                incoming.r15Bits() != restored.r15Bits() ||
                !incoming.xmm6().equals(restored.xmm6())) {
                throw new UnsupportedOperationException("Target failed to preserve nonvolatile state.");
            }

            return result.volatileBits();
        }
    }
}