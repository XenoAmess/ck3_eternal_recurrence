package org.xar.ck3.research.m5;

import org.xar.ck3.research.m1.GovernmentMemoryFill206Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentFill207Api;

public final class GovernmentCrtFill207Calls {
    private GovernmentCrtFill207Calls() { }

    public static Calls bind(long imageBaseBits, GovernmentFill207Api.Memory memory, Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
        GovernmentPrimaryTail155Api.Calls adaptedTailFallback = new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public VolatileBits invoke(OpaqueCall c) {
                return fallback.invoke(new Call(c.callSiteRva(), TargetKind.DIRECT_RVA, c.targetRva(), c.rspBits(), c.volatileBits(), c.nonvolatileBits()));
            }
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };

        GovernmentPrimaryTail155Api.Calls boundM1 = GovernmentMemoryFill206Calls.bindTail(imageBaseBits, memory, adaptedTailFallback, fallback, budget);

        return new Calls() {
            @Override
            public VolatileBits invoke(Call call) {
                if (call.kind() == TargetKind.DIRECT_RVA && call.callSiteRva() == 0x425B87CL && call.targetBits() == 0x4226F10L) {
                    OpaqueCall opaque = new OpaqueCall(call.callSiteRva(), call.targetBits(), call.rspBits(), call.volatileBits(), call.nonvolatileBits());
                    return boundM1.invoke(opaque);
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
        };
    }
}
