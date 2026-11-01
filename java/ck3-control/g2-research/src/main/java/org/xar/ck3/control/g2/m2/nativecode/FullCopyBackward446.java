package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import java.util.Objects;

public final class FullCopyBackward446 {
    private FullCopyBackward446() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input, FullCopy437Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        boolean df = input.directionFlagSet();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();

        // Registers from entry
        long rax = entry.volatileBits().raxBits();
        long rcx = entry.volatileBits().rcxBits();
        long rdx = entry.volatileBits().rdxBits();
        long r8 = entry.volatileBits().r8Bits();
        long r9 = entry.volatileBits().r9Bits();
        long r10 = entry.volatileBits().r10Bits();
        long r11 = entry.volatileBits().r11Bits();
        GovernmentPrimaryTail155Api.Bits128 x0 = entry.volatileBits().xmm0();
        GovernmentPrimaryTail155Api.Bits128 x1 = entry.volatileBits().xmm1();
        GovernmentPrimaryTail155Api.Bits128 x2 = entry.volatileBits().xmm2();
        GovernmentPrimaryTail155Api.Bits128 x3 = entry.volatileBits().xmm3();
        GovernmentPrimaryTail155Api.Bits128 x4 = entry.volatileBits().xmm4();
        GovernmentPrimaryTail155Api.Bits128 x5 = entry.volatileBits().xmm5();
        GovernmentPrimaryTail155Api.NonvolatileBits n = entry.nonvolatileBits();
        long rsp = entry.rspBits();
        long imageBase = entry.imageBaseBits();

        // 4226DF0: mov r11,rcx
        r11 = rcx;
        // 4226DF3: mov r10,rdx
        r10 = rdx;
        // 4226DF6: sub rdx,rcx
        rdx = rdx - rcx;
        // 4226DF9: add rcx,r8
        rcx = rcx + r8;

        // 4226DFC: movups xmm0,[rcx+rdx*1-0x10]
        x0 = memory.read128(rcx + rdx - 0x10);
        // 4226E01: sub rcx,0x10
        rcx = rcx - 0x10;
        // 4226E05: sub r8,0x10
        r8 = r8 - 0x10;
        // 4226E09: test cl,0xf
        boolean testCl = (rcx & 0xF) != 0;

        if (testCl) {
            // 4226E0E: mov rax,rcx
            rax = rcx;
            // 4226E11: and rcx,0xfffffffffffffff0
            rcx = rcx & 0xFFFFFFFFFFFFFFF0L;
            // 4226E15: movups xmm1,xmm0
            x1 = x0;
            // 4226E18: movups xmm0,[rcx+rdx*1]
            x0 = memory.read128(rcx + rdx);
            // 4226E1C: movups [rax],xmm1
            memory.write128(rax, x1);
            // 4226E1F: mov r8,rcx
            r8 = rcx;
            // 4226E22: sub r8,r11
            r8 = r8 - r11;
        }

        // 4226E25: mov r9,r8
        r9 = r8;
        // 4226E28: shr r9,0x7
        r9 = r9 >>> 7;
        // 4226E2C: je 0x4226E9D (if r9==0)
        if (r9 == 0) {
            // jump to 4226E9D
        } else {
            // 4226E2E: movaps [rcx],xmm0
            memory.write128(rcx, x0);
            // 4226E31: first bulk entry jumps directly to 4226E47.
            // 4226E47: movups xmm0,[rcx+rdx*1-0x10]
            budget.beforeStep(0x4226E47L, rcx);
            x0 = memory.read128(rcx + rdx - 0x10);
            // 4226E4C: movups xmm1,[rcx+rdx*1-0x20]
            x1 = memory.read128(rcx + rdx - 0x20);
            // 4226E51: sub rcx,0x80
            rcx = rcx - 0x80;
            // 4226E58: movaps [rcx+0x70],xmm0
            memory.write128(rcx + 0x70, x0);
            // 4226E5C: movaps [rcx+0x60],xmm1
            memory.write128(rcx + 0x60, x1);
            // 4226E60: movups xmm0,[rcx+rdx*1+0x50]
            x0 = memory.read128(rcx + rdx + 0x50);
            // 4226E65: movups xmm1,[rcx+rdx*1+0x40]
            x1 = memory.read128(rcx + rdx + 0x40);
            // 4226E6A: dec r9
            r9 = r9 - 1;
            // 4226E6D: movaps [rcx+0x50],xmm0
            memory.write128(rcx + 0x50, x0);
            // 4226E71: movaps [rcx+0x40],xmm1
            memory.write128(rcx + 0x40, x1);
            // 4226E75: movups xmm0,[rcx+rdx*1+0x30]
            x0 = memory.read128(rcx + rdx + 0x30);
            // 4226E7A: movups xmm1,[rcx+rdx*1+0x20]
            x1 = memory.read128(rcx + rdx + 0x20);
            // 4226E7F: movaps [rcx+0x30],xmm0
            memory.write128(rcx + 0x30, x0);
            // 4226E83: movaps [rcx+0x20],xmm1
            memory.write128(rcx + 0x20, x1);
            // 4226E87: movups xmm0,[rcx+rdx*1+0x10]
            x0 = memory.read128(rcx + rdx + 0x10);
            // 4226E8C: movups xmm1,[rcx+rdx*1]
            x1 = memory.read128(rcx + rdx);
            // 4226E90: jne 0x4226E40 (if r9!=0)
            while (r9 != 0) {
                // 4226E40/44: delayed stores precede the next 4226E47 admission.
                memory.write128(rcx + 0x10, x0);
                memory.write128(rcx, x1);
                budget.beforeStep(0x4226E47L, rcx);
                x0 = memory.read128(rcx + rdx - 0x10);
                x1 = memory.read128(rcx + rdx - 0x20);
                rcx = rcx - 0x80;
                memory.write128(rcx + 0x70, x0);
                memory.write128(rcx + 0x60, x1);
                x0 = memory.read128(rcx + rdx + 0x50);
                x1 = memory.read128(rcx + rdx + 0x40);
                r9 = r9 - 1;
                memory.write128(rcx + 0x50, x0);
                memory.write128(rcx + 0x40, x1);
                x0 = memory.read128(rcx + rdx + 0x30);
                x1 = memory.read128(rcx + rdx + 0x20);
                memory.write128(rcx + 0x30, x0);
                memory.write128(rcx + 0x20, x1);
                x0 = memory.read128(rcx + rdx + 0x10);
                x1 = memory.read128(rcx + rdx);
            }
            // 4226E92: movaps [rcx+0x10],xmm0
            memory.write128(rcx + 0x10, x0);
            // 4226E96/9A are reached only after a nonzero bulk loop.
            r8 = r8 & 0x7F;
            x0 = x1;
        }

        // 4226E9D: mov r9,r8
        r9 = r8;
        // 4226EA0: shr r9,0x4
        r9 = r9 >>> 4;
        // 4226EA4: je 0x4226EC0 (if r9==0)
        if (r9 != 0) {
            // 4226EB0: movups [rcx],xmm0
            budget.beforeStep(0x4226EB0L, rcx);
            memory.write128(rcx, x0);
            // 4226EB3: sub rcx,0x10
            rcx = rcx - 0x10;
            // 4226EB7: movups xmm0,[rcx+rdx*1]
            x0 = memory.read128(rcx + rdx);
            // 4226EBB: dec r9
            r9 = r9 - 1;
            // 4226EBE: jne 0x4226EB0
            while (r9 != 0) {
                budget.beforeStep(0x4226EB0L, rcx);
                memory.write128(rcx, x0);
                rcx = rcx - 0x10;
                x0 = memory.read128(rcx + rdx);
                r9 = r9 - 1;
            }
        }

        // 4226EC0: and r8,0xf
        r8 = r8 & 0xF;
        // 4226EC4: je 0x4226ECE (if r8==0)
        if (r8 != 0) {
            // 4226EC6: movups xmm1,[r10]
            x1 = memory.read128(r10);
            // 4226ECA: movups [r11],xmm1
            memory.write128(r11, x1);
        }
        // 4226ECE: movups [rcx],xmm0
        memory.write128(rcx, x0);
        // 4226ED1: mov rax,r11
        rax = r11;
        // 4226ED4: ret
        long retRip = memory.readQword(rsp);
        long callerRsp = rsp + 8;

        GovernmentPrimaryTail155Api.VolatileBits outV = new GovernmentPrimaryTail155Api.VolatileBits(
            rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            outV, retRip, callerRsp, n);
        return new FullCopy437Api.CallResult(nr, df);
    }
}