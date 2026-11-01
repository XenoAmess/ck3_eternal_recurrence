package org.xar.ck3.research.m0.title274;

import org.xar.ck3.research.m4.Free61FullState201;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Exact leaf-tail binding; the three known thunks add no CALL push or RET. */
public final class TitleSlotRelease876390FreeCalls {
    private TitleSlotRelease876390FreeCalls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                return fallback.invoke(call);
            }

            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                if (transfer.jumpSiteRva() != 0x876399L
                        || transfer.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || transfer.targetBits() != 0x4223F44L
                        || transfer.entry().imageBaseBits() != imageBaseBits) {
                    return fallback.tail(transfer);
                }
                GovernmentCrtBoundary185Api.Entry entry = transfer.entry();
                Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                        entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
                // 4223F44 -> 40EC530 -> 423543C: write only the DWORD, then reload EAX.
                memory.writeDword(r.rsp + 0x10L, 0);
                r.rax = Integer.toUnsignedLong(memory.readDword(r.rsp + 0x10L));
                return Free61FullState201.execute(new GovernmentCrtBoundary185Api.Entry(
                        imageBaseBits, r.rsp, r.volatileBits(), r.nonvolatileBits()), memory, fallback);
            }

            @Override public long readGsQword58() { return fallback.readGsQword58(); }
        };
    }
}
