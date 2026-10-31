package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import java.util.Objects;

public final class GovernmentRegistryResize201Calls {
    private GovernmentRegistryResize201Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(long imageBase, GovernmentPrimaryTail155Api.Memory memory, GovernmentPrimaryTail155Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                long site = call.callSiteRva();
                long target = call.targetRva();
                long preSP = call.rspBits();
                GovernmentPrimaryTail155Api.VolatileBits fullV = call.volatileBits();
                GovernmentPrimaryTail155Api.NonvolatileBits fullN = call.nonvolatileBits();

                if (target != 0x425B804L) {
                    return fallback.invoke(call);
                }
                if (site != 0x424DC3EL && site != 0x424DC62L) {
                    return fallback.invoke(call);
                }

                GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                    imageBase,
                    preSP - 8,
                    fullV,
                    fullN
                );
                GovernmentCallee164Api.NormalReturn ret = GovernmentRegistryResize201.execute(entry, memory, fallback);

                long expectedRip = (site == 0x424DC3EL) ? (imageBase + 0x424DC43L) : (imageBase + 0x424DC67L);
                if (ret.returnRipBits() != expectedRip) {
                    throw new IllegalStateException("RIP mismatch");
                }
                if (ret.callerRspBits() != preSP) {
                    throw new IllegalStateException("SP mismatch");
                }
                if (!Objects.equals(ret.nonvolatileBits(), fullN)) {
                    throw new IllegalStateException("N mismatch");
                }

                return ret.volatileBits();
            }
        };
    }
}