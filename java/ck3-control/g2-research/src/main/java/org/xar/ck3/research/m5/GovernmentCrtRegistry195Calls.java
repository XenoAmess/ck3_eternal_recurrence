package org.xar.ck3.research.m5;

import org.xar.ck3.research.m1.GovernmentRegistryDispatch194Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class GovernmentCrtRegistry195Calls {
    private GovernmentCrtRegistry195Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        GovernmentPrimaryTail155Api.Calls adaptedFallback = new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall c) {
                GovernmentCrtBoundary185Api.Call crtCall = new GovernmentCrtBoundary185Api.Call(
                    c.callSiteRva(),
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    c.targetRva(),
                    c.rspBits(),
                    c.volatileBits(),
                    c.nonvolatileBits()
                );
                return fallback.invoke(crtCall);
            }
        };

        GovernmentPrimaryTail155Api.Calls boundM1Consumer = GovernmentRegistryDispatch194Calls.bind(image, memory, adaptedFallback);

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call c) {
                if (c.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && c.callSiteRva() == 0x424DF29L
                        && c.targetBits() == 0x424DB38L) {
                    GovernmentPrimaryTail155Api.OpaqueCall tailCall = new GovernmentPrimaryTail155Api.OpaqueCall(
                        c.callSiteRva(),
                        c.targetBits(),
                        c.rspBits(),
                        c.volatileBits(),
                        c.nonvolatileBits()
                    );
                    return boundM1Consumer.invoke(tailCall);
                }
                return fallback.invoke(c);
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                return fallback.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}
