package org.xar.ck3.research.m0.staticobject357;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class ManagerStaticObjectB15000Calls {
    private ManagerStaticObjectB15000Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback) {

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() != 0x28EE6AFL
                        || call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || call.targetBits() != 0xB15000L) {
                    return fallback.invoke(call);
                }

                long expectedRip = imageBaseBits + 0x28EE6B4L;
                long entryRsp = call.rspBits() - 8L;

                if (memory.readQword(entryRsp) != expectedRip) {
                    throw new IllegalStateException("existing CALL return slot mismatch");
                }

                GovernmentCrtBoundary185Api.NormalReturn result = StaticObjectB15000FullState.execute(
                        new GovernmentCrtBoundary185Api.Entry(imageBaseBits, entryRsp,
                                call.volatileBits(), call.nonvolatileBits()),
                        memory,
                        fallback);

                if (result.returnRipBits() != expectedRip
                        || result.callerRspBits() != call.rspBits()
                        || !result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("normal return boundary mismatch");
                }

                return result.volatileBits();
            }

            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                return fallback.tail(transfer);
            }

            @Override public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}