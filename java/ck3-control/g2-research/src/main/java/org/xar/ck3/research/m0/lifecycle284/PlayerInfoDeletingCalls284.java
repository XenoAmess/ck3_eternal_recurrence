package org.xar.ck3.research.m0.lifecycle284;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Binds the exact virtual call to the PlayerInfo wrapper. */
public final class PlayerInfoDeletingCalls284 {
    private PlayerInfoDeletingCalls284() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() != 0xA07B31L
                        || call.kind() != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                        || call.targetBits() != imageBaseBits + 0x23DA680L) {
                    return fallback.invoke(call);
                }
                long expectedRip = imageBaseBits + 0xA07B33L;
                long entryRsp = call.rspBits() - 8L;
                if (memory.readQword(entryRsp) != expectedRip) {
                    throw new IllegalStateException("existing CALL return slot mismatch");
                }
                GovernmentCrtBoundary185Api.NormalReturn result = DeletingWrappers284.executePlayerInfo(
                        new GovernmentCrtBoundary185Api.Entry(imageBaseBits, entryRsp,
                                call.volatileBits(), call.nonvolatileBits()),
                        memory, fallback);
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