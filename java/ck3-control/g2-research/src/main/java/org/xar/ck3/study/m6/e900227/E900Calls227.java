package org.xar.ck3.study.m6.e900227;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class E900Calls227 {
    private E900Calls227() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() == 0x424FC96L && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == 0x424E900L) {
                    GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                            image,
                            call.rspBits() - 8L,
                            call.volatileBits(),
                            call.nonvolatileBits()
                    );
                    GovernmentCrtBoundary185Api.NormalReturn nr = E900FullState227.execute(childEntry, memory, fallback);

                    if (nr.returnRipBits() != image + 0x424FC9BL) {
                        throw new IllegalStateException("returnRip mismatch");
                    }
                    if (nr.callerRspBits() != call.rspBits()) {
                        throw new IllegalStateException("callerRsp mismatch");
                    }
                    if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new IllegalStateException("nonvolatile mismatch");
                    }

                    return nr.volatileBits();
                }
                return fallback.invoke(call);
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