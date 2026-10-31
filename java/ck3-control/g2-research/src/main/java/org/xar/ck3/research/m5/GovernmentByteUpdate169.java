package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.Entry;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.Memory;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;

public final class GovernmentByteUpdate169 {
    private static long u32(long v) { return v & 0xffffffffL; }
    private static int rol32(int v, int s) { return (v << s) | (v >>> (32 - s)); }

    public static NormalReturn execute(Entry entry, Memory memory, LoopBudget budget) {
        long rsp = entry.frameRspBits();
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
        long rbx = entry.nonvolatileBits().rbxBits();
        long rbp = entry.nonvolatileBits().rbpBits();
        long rsi = entry.nonvolatileBits().rsiBits();
        long rdi = entry.nonvolatileBits().rdiBits();
        long r12 = entry.nonvolatileBits().r12Bits();
        long r13 = entry.nonvolatileBits().r13Bits();
        long r14 = entry.nonvolatileBits().r14Bits();
        long r15 = entry.nonvolatileBits().r15Bits();
        Bits128 x6 = entry.nonvolatileBits().xmm6();
        Mxcsr32 mxcsr = entry.mxcsr();

        memory.writeQword(rsp + 8, rbx);
        memory.writeQword(rsp + 0x10, rsi);
        memory.writeQword(rsp + 0x18, rdi);
        memory.writeQword(rsp + 0x20, r14);

        r10 = u32(memory.readDword(rdx));
        rsi = rdx;
        rdi = u32(memory.readDword(rcx));
        r11 = r10;
        r11 = u32(r11 & 3);
        r14 = rcx;
        rbx = r11;
        rbx = u32(-rbx);
        rbx = u32(rbx & 3);

        if (rbx != 0) {
            if ((int)rbx <= (int)r9) {
                r9 = u32(r9 - rbx);
                while (rbx != 0) {
                    budget.beforeIteration(0x3f7e120L, r8, u32(r9), rbx);
                    int ecx = memory.readUnsignedByte(r8);
                    int eax = (int)r10;
                    ecx <<= 24;
                    rcx = u32(ecx);
                    rbx = u32(rbx - 1);
                    eax >>>= 8;
                    rax = u32(eax);
                    r10 = u32(ecx | eax);
                    r8 = r8 + 1;
                    r11 = u32(r11 + 1);
                    if (r11 != 4) continue;
                    eax = (int)(r10 * 0xcc9e2d51);
                    eax = rol32(eax, 15);
                    rax = u32(eax);
                    r10 = u32(eax * 0x1b873593);
                    rdi = u32(rdi ^ r10);
                    rdi = u32(rol32((int)rdi, 13));
                    rdi = u32(rdi + 0xfaddaf14);
                    r11 = 0;
                    rdi = u32(rdi + (rdi << 2));
                }
            }
        }

        rax = u32(r9);
        int eax = (int)rax;
        int edx = eax >> 31;
        rdx = u32(edx & 3);
        rax = u32(rax + rdx);
        rax = u32(rax & 0xfffffffc);
        rbx = (long)(int)rax;
        rbx = rbx + r8;

        if (Long.compareUnsigned(r8, rbx) < 0) {
            while (Long.compareUnsigned(r8, rbx) < 0) {
                budget.beforeIteration(0x3f7e180L, r8, u32(r9), rbx);
                int ecx = memory.readDword(r8) * 0xcc9e2d51;
                r8 = r8 + 4;
                ecx = rol32(ecx, 15);
                rcx = u32(ecx);
                int edx2 = ecx * 0x1b873593;
                rdx = u32(edx2);
                rdi = u32(rdi ^ edx2);
                rdi = u32(rol32((int)rdi, 13));
                rdi = u32(rdi + 0xfaddaf14);
                rdi = u32(rdi + (rdi << 2));
            }
        }

        r9 = u32(r9 - rax);
        if (r9 != 0) {
            while (r9 != 0) {
                budget.beforeIteration(0x3f7e1b0L, r8, u32(r9), rbx);
                int ecx = memory.readUnsignedByte(r8);
                r8 = r8 + 1;
                int eax2 = (int)r10;
                ecx <<= 24;
                rcx = u32(ecx);
                eax2 >>>= 8;
                rax = u32(eax2);
                r10 = u32(ecx | eax2);
                r9 = u32(r9 - 1);
                r11 = u32(r11 + 1);
                if (r11 != 4) continue;
                eax2 = (int)(r10 * 0xcc9e2d51);
                eax2 = rol32(eax2, 15);
                rax = u32(eax2);
                r10 = u32(eax2 * 0x1b873593);
                rdi = u32(rdi ^ r10);
                rdi = u32(rol32((int)rdi, 13));
                rdi = u32(rdi + 0xfaddaf14);
                r11 = 0;
                rdi = u32(rdi + (rdi << 2));
            }
        }

        rbx = memory.readQword(rsp + 8);
        r10 = u32(r10 & 0xffffff00);
        memory.writeDword(r14, (int)rdi);
        r10 = u32(r10 | r11);
        rdi = memory.readQword(rsp + 0x18);
        r14 = memory.readQword(rsp + 0x20);
        memory.writeDword(rsi, (int)r10);
        rsi = memory.readQword(rsp + 0x10);
        long returnRip = memory.readQword(rsp);
        long callerRsp = rsp + 8;

        return new NormalReturn(
            new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5),
            new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6),
            returnRip, callerRsp, mxcsr
        );
    }
}
