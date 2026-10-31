package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class GovernmentCrtCallee186 {
    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        long rbx = entry.nonvolatileBits().rbxBits();
        long rbp = entry.nonvolatileBits().rbpBits();
        long rsi = entry.nonvolatileBits().rsiBits();
        long rdi = entry.nonvolatileBits().rdiBits();
        long r12 = entry.nonvolatileBits().r12Bits();
        long r13 = entry.nonvolatileBits().r13Bits();
        long r14 = entry.nonvolatileBits().r14Bits();
        long r15 = entry.nonvolatileBits().r15Bits();
        Bits128 x6 = entry.nonvolatileBits().xmm6();
        long rax = entry.volatileBits().raxBits();
        long rcx = entry.volatileBits().rcxBits();
        long rdx = entry.volatileBits().rdxBits();
        long r8 = entry.volatileBits().r8Bits();
        long r9 = entry.volatileBits().r9Bits();
        long r10 = entry.volatileBits().r10Bits();
        long r11 = entry.volatileBits().r11Bits();
        Bits128 x0 = entry.volatileBits().xmm0();
        Bits128 x1 = entry.volatileBits().xmm1();
        Bits128 x2 = entry.volatileBits().xmm2();
        Bits128 x3 = entry.volatileBits().xmm3();
        Bits128 x4 = entry.volatileBits().xmm4();
        Bits128 x5 = entry.volatileBits().xmm5();

        rsp -= 8;
        memory.writeQword(rsp, rbx);
        rsp -= 0x20;

        long cmpAddr = imageBase + 0x5C5CB68L;
        long cmpVal = memory.readQword(cmpAddr);
        boolean branch = (cmpVal != -1L);

        if (branch) {
            rbx = rcx;
            rdx = rbx;
            rcx = cmpAddr;
            Call c = new Call(0x4223f0cL, TargetKind.DIRECT_RVA, 0x424deecL, rsp,
                new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5),
                new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6));
            memory.writeQword(rsp - 8, imageBase + 0x4223f11L);
            VolatileBits v = calls.invoke(c);
            rax = v.raxBits(); rcx = v.rcxBits(); rdx = v.rdxBits();
            r8 = v.r8Bits(); r9 = v.r9Bits(); r10 = v.r10Bits(); r11 = v.r11Bits();
            x0 = v.xmm0(); x1 = v.xmm1(); x2 = v.xmm2(); x3 = v.xmm3(); x4 = v.xmm4(); x5 = v.xmm5();
        } else {
            rbx = rcx;
            Call c = new Call(0x4223efbL, TargetKind.DIRECT_RVA, 0x424de78L, rsp,
                new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5),
                new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6));
            memory.writeQword(rsp - 8, imageBase + 0x4223f00L);
            VolatileBits v = calls.invoke(c);
            rax = v.raxBits(); rcx = v.rcxBits(); rdx = v.rdxBits();
            r8 = v.r8Bits(); r9 = v.r9Bits(); r10 = v.r10Bits(); r11 = v.r11Bits();
            x0 = v.xmm0(); x1 = v.xmm1(); x2 = v.xmm2(); x3 = v.xmm3(); x4 = v.xmm4(); x5 = v.xmm5();
        }

        rdx = 0L;
        boolean test = ((rax & 0xFFFFFFFFL) != 0);
        if (!test) rdx = rbx;
        rax = rdx;

        rsp += 0x20;
        rbx = memory.readQword(rsp);
        rsp += 8;
        long retRip = memory.readQword(rsp);

        return new NormalReturn(
            new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5),
            retRip, entry.rspBits() + 8L,
            new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6));
    }
}