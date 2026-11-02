package org.xar.ck3.research.m0.staticobject361;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Consumer leaf for the actual StaticObjectB15000FullState CALL B15056 -> 4223A24.
 * Reuses GovernmentCrtBoundary185.execute3A24; does not restate or modify it.
 */
public final class StaticObjectFooter361Calls {
    private StaticObjectFooter361Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback) {

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                // Only intercept the specific call site: B15056 -> 4223A24 (DIRECT_RVA)
                if (call.callSiteRva() != 0xB15056L
                        || call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || call.targetBits() != 0x4223A24L) {
                    return fallback.invoke(call);
                }

                long expectedRip = imageBaseBits + 0xB1505BL;
                long entryRsp = call.rspBits() - 8L;

                // Check existing CALL return slot; do not create or overwrite it.
                if (memory.readQword(entryRsp) != expectedRip) {
                    throw new IllegalStateException("existing CALL return slot mismatch");
                }

                // Invoke the existing producer with fallback as its opaque Calls.
                GovernmentCrtBoundary185Api.NormalReturn result = GovernmentCrtBoundary185.execute3A24(
                        new GovernmentCrtBoundary185Api.Entry(imageBaseBits, entryRsp,
                                call.volatileBits(), call.nonvolatileBits()),
                        memory,
                        fallback);

                // Verify normal return boundary.
                if (result.returnRipBits() != expectedRip
                        || result.callerRspBits() != call.rspBits()
                        || !result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("normal return boundary mismatch");
                }

                // Return all actual result volatile bits unchanged.
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
