package org.xar.ck3.study.m6.indexed230;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;

public final class Indexed448FullCalls230 {
    private Indexed448FullCalls230() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, AtomicIndexedMemory229 memory, GovernmentCrtBoundary185Api.Calls fallback, GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(budget);
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() == 0x424E922L && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == 0x424E448L) {
                    GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(image, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                    GovernmentCrtBoundary185Api.NormalReturn nr = Indexed448FullState230.execute(childEntry, memory, fallback, budget);
                    if (nr.returnRipBits() != image + 0x424E927L) throw new IllegalStateException("returnRip mismatch");
                    if (nr.callerRspBits() != call.rspBits()) throw new IllegalStateException("callerRsp mismatch");
                    if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalStateException("nonvolatile mismatch");
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