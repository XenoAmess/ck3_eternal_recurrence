package org.xar.ck3.research.m4;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestGate424cffc;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

public final class Gate47FullState273 {
    private Gate47FullState273() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        long base = entry.imageBaseBits();
        long entrySP = entry.rspBits();
        long bodypreSP = entrySP - 0x28L;

        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(base, entrySP, entry.volatileBits(), entry.nonvolatileBits()));

        memory.writeQword(entrySP - 8L, r.rbx);
        r.rbx = r.rcx;
        r.rsp = bodypreSP;

        RequestGate424cffc.Ports ports = new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                long target = 0x424D02CL;
                long retAddr = base + 0x424D00AL;
                memory.writeQword(r.rsp - 8L, retAddr);
                GovernmentCrtBoundary185Api.Call c = new GovernmentCrtBoundary185Api.Call(
                    0x424D005L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, r.rsp, r.volatileBits(), r.nonvolatileBits());
                GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(c);
                r.apply(postV);
                return r.rax;
            }
            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                r.rcx = r.rbx;
                long target = memory.readQword(base + 0x43DBBA8L);
                long retAddr = base + 0x424D018L;
                memory.writeQword(r.rsp - 8L, retAddr);
                GovernmentCrtBoundary185Api.Call c = new GovernmentCrtBoundary185Api.Call(
                    0x424D012L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target, r.rsp, r.volatileBits(), r.nonvolatileBits());
                GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(c);
                r.apply(postV);
                return (int)(r.rax & 0xFFFFFFFFL);
            }
        };

        int scalar = RequestGate424cffc.execute(r.rbx, ports);
        r.rax = (long)scalar & 0xFFFFFFFFL;

        r.rsp += 0x20L;
        r.rbx = memory.readQword(r.rsp);
        r.rsp += 8L;
        long retRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), retRip, r.rsp, r.nonvolatileBits());
    }
}