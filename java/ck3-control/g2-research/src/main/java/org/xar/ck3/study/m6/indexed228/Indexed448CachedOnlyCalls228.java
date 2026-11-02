package org.xar.ck3.study.m6.indexed228;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Cached-only consumer for the actual 424E922 direct call site. */
public final class Indexed448CachedOnlyCalls228 {
    private Indexed448CachedOnlyCalls228() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.callSiteRva() == 0x424E922L && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == 0x424E448L) {
                    long preSP = call.rspBits();
                    long coreEntrySP = preSP - 8L;
                    GovernmentCrtBoundary185Api.Entry coreEntry = new GovernmentCrtBoundary185Api.Entry(
                            image, coreEntrySP, call.volatileBits(), call.nonvolatileBits());
                    GovernmentCrtBoundary185Api.NormalReturn nr = Indexed448CachedOnly228.executeCachedOnly(coreEntry, memory);

                    long expectedRip = image + 0x424E927L;
                    if (nr.returnRipBits() != expectedRip) {
                        throw new IllegalStateException("returnRip mismatch");
                    }
                    if (nr.callerRspBits() != preSP) {
                        throw new IllegalStateException("callerRsp mismatch");
                    }
                    if (!Objects.equals(nr.nonvolatileBits(), call.nonvolatileBits())) {
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