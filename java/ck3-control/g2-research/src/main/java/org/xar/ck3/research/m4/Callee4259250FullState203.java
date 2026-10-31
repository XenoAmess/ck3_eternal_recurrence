package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Exact held57B normal-return projection; opaque normal ports retain their represented full state. */
public final class Callee4259250FullState203 {
    private Callee4259250FullState203() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        long image = entry.imageBaseBits();
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        r.rsp -= 0x28L;
        if (r.rcx == 0L) {
            invoke(image, 0x4259259L, 0x423B18CL, r, memory, calls);
            memory.writeDword(r.rax, 0x16);
            invoke(image, 0x4259264L, 0x4232A50L, r, memory, calls);
            r.rax = -1L;
            r.rsp += 0x28L;
            long actualRip = memory.readQword(r.rsp);
            return new GovernmentCrtBoundary185Api.NormalReturn(
                    r.volatileBits(), actualRip, r.rsp + 8L, r.nonvolatileBits());
        }
        r.r8 = r.rcx;
        r.rdx = 0L;
        r.rcx = memory.readQword(image + 0x5C5DE30L);
        r.rsp += 0x28L;
        long target = memory.readQword(image + 0x43DA7C8L);
        return calls.tail(new GovernmentCrtBoundary185Api.Tail(
                0x4259282L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target,
                new GovernmentCrtBoundary185Api.Entry(image, r.rsp, r.volatileBits(), r.nonvolatileBits())));
    }

    private static void invoke(long image, long site, long target, Registers r,
            GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls calls) {
        memory.writeQword(r.rsp - 8L, image + site + 5L);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target,
                r.rsp, r.volatileBits(), r.nonvolatileBits())));
    }
}
