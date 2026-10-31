package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentRegistryForward185 {
    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls) {

        GovernmentPrimaryTail155Api.VolatileBits v = entry.volatileBits();

        // MOV RDX, RCX: RDX becomes old RCX
        long newRdx = v.rcxBits();

        // LEA RCX, [RIP + 0x1a0f816]: RCX becomes imageBase + 0x5C5D698
        long newRcx = entry.imageBaseBits() + 0x5C5D698L;

        GovernmentPrimaryTail155Api.VolatileBits modifiedV = new GovernmentPrimaryTail155Api.VolatileBits(
            v.raxBits(),
            newRcx,
            newRdx,
            v.r8Bits(),
            v.r9Bits(),
            v.r10Bits(),
            v.r11Bits(),
            v.xmm0(),
            v.xmm1(),
            v.xmm2(),
            v.xmm3(),
            v.xmm4(),
            v.xmm5()
        );

        GovernmentCallee164Api.Entry newEntry = new GovernmentCallee164Api.Entry(
            entry.imageBaseBits(),
            entry.frameRspBits(),
            modifiedV,
            entry.nonvolatileBits()
        );

        return GovernmentRegistryTable186.execute(newEntry, memory, calls);
    }
}
