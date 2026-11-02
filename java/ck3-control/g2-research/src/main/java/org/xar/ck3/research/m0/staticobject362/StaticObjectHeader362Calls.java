package org.xar.ck3.research.m0.staticobject362;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * One new consumer only: binds actual StaticObjectB15000FullState CALL B15033/DIRECT_RVA/4223A84
 * to the supplied current GovernmentCrtBoundary185.execute3A84.
 * Every unmatched Call goes unchanged to fallback.invoke, each Tail and its result go unchanged to fallback.tail, GS58 delegates.
 */
public final class StaticObjectHeader362Calls {
    private StaticObjectHeader362Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() != 0xB15033L
                        || call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || call.targetBits() != 0x4223A84L) {
                    return fallback.invoke(call);
                }

                long expectedRip = imageBaseBits + 0xB15038L;
                long entryRsp = call.rspBits() - 8L;

                if (memory.readQword(entryRsp) != expectedRip) {
                    throw new IllegalStateException("existing CALL return slot mismatch");
                }

                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                        imageBaseBits, entryRsp, call.volatileBits(), call.nonvolatileBits());

                GovernmentCrtBoundary185Api.NormalReturn result = GovernmentCrtBoundary185.execute3A84(
                        entry, memory, fallback, budget);

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
