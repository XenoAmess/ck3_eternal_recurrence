package org.xar.ck3.research.m5;

import org.xar.ck3.research.m1.GovernmentRegistryGrowth199Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class GovernmentCrtGrowth200Calls {
    private GovernmentCrtGrowth200Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {

        GovernmentPrimaryTail155Api.Calls adaptedTailFallback = new GovernmentPrimaryTail155Api.Calls() {
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

        GovernmentPrimaryTail155Api.Calls boundM1Consumer = GovernmentRegistryGrowth199Calls.bind(
                imageBaseBits,
                memory,
                adaptedTailFallback,
                budget
        );

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && call.callSiteRva() == 0x424DB58L
                        && call.targetBits() == 0x424DBB0L) {
                    GovernmentPrimaryTail155Api.OpaqueCall tailCall = new GovernmentPrimaryTail155Api.OpaqueCall(
                            call.callSiteRva(),
                            call.targetBits(),
                            call.rspBits(),
                            call.volatileBits(),
                            call.nonvolatileBits()
                    );
                    return boundM1Consumer.invoke(tailCall);
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
        };
    }
}
