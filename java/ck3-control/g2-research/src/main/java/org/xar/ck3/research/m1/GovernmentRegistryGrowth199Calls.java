package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

public final class GovernmentRegistryGrowth199Calls {
    private static final long SITE = 0x424DB58L;
    private static final long TARGET = 0x424DBB0L;
    private static final long RET_RIP = 0x424DB5DL;

    public static GovernmentPrimaryTail155Api.Calls bind(long imageBase, GovernmentPrimaryTail155Api.Memory memory, GovernmentPrimaryTail155Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == SITE && call.targetRva() == TARGET) {
                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                        imageBase,
                        call.rspBits() - 8,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );

                    GovernmentCallee164Api.NormalReturn result = GovernmentRegistryGrowth199.execute(entry, memory, fallback, budget);

                    if (result.returnRipBits() != imageBase + RET_RIP) {
                        throw new IllegalStateException("Invalid return RIP");
                    }
                    if (result.callerRspBits() != call.rspBits()) {
                        throw new IllegalStateException("Invalid caller SP");
                    }

                    GovernmentPrimaryTail155Api.NonvolatileBits expectedN = call.nonvolatileBits();
                    GovernmentPrimaryTail155Api.NonvolatileBits actualN = result.nonvolatileBits();
                    if (expectedN.rbxBits() != actualN.rbxBits() ||
                        expectedN.rbpBits() != actualN.rbpBits() ||
                        expectedN.rsiBits() != actualN.rsiBits() ||
                        expectedN.rdiBits() != actualN.rdiBits() ||
                        expectedN.r12Bits() != actualN.r12Bits() ||
                        expectedN.r13Bits() != actualN.r13Bits() ||
                        expectedN.r14Bits() != actualN.r14Bits() ||
                        expectedN.r15Bits() != actualN.r15Bits() ||
                        !expectedN.xmm6().equals(actualN.xmm6())) {
                        throw new IllegalStateException("Nonvolatile mismatch");
                    }

                    return result.volatileBits();
                }
                return fallback.invoke(call);
            }
        };
    }
}