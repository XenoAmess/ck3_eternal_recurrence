package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class GovernmentRegistryDispatch194Calls {
    private GovernmentRegistryDispatch194Calls() {}

    public static GovernmentPrimaryTail155Api.Calls bind(long imageBase, GovernmentPrimaryTail155Api.Memory memory, GovernmentPrimaryTail155Api.Calls fallback) {
        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x424DF29L && call.targetRva() == 0x424DB38L) {
                    long preSP = call.rspBits();
                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                        imageBase,
                        preSP - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits()
                    );
                    GovernmentCallee164Api.NormalReturn result = GovernmentRegistryDispatch194.execute(entry, memory, fallback);
                    if (result.returnRipBits() != imageBase + 0x424DF2EL) {
                        throw new IllegalStateException("RIP mismatch");
                    }
                    if (result.callerRspBits() != preSP) {
                        throw new IllegalStateException("RSP mismatch");
                    }
                    if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new IllegalStateException("Nonvolatile mismatch");
                    }
                    return result.volatileBits();
                }
                return fallback.invoke(call);
            }
        };
    }
}