package org.xar.ck3.research.m0.title274;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Normal-return bit projection of held [876390,87639F); flags/EH are outside this API. */
public final class TitleSlotRelease876390 {
    private TitleSlotRelease876390() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        if ((r.rdx & 0xFFL) == 0L) {
            return new GovernmentCrtBoundary185Api.NormalReturn(
                    r.volatileBits(), memory.readQword(r.rsp), r.rsp + 8L, r.nonvolatileBits());
        }
        r.rdx = 0x10L;
        return calls.tail(new GovernmentCrtBoundary185Api.Tail(
                0x876399L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4223F44L,
                new GovernmentCrtBoundary185Api.Entry(entry.imageBaseBits(), r.rsp,
                        r.volatileBits(), r.nonvolatileBits())));
    }
}
