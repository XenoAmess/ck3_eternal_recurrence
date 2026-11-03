package org.xar.ck3.study.m6.posttable257;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

public final class TableDwordLeaf257 implements PostState240Api.EntryExecutor {
    public TableDwordLeaf257() { }

    @Override
    public QueueFp604Api.Outcome execute(PostState240Api.Input input, GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long image = entry.imageBaseBits();
        long rsp = entry.rspBits();
        VolatileBits v = entry.volatileBits();
        NonvolatileBits n = entry.nonvolatileBits();
        boolean df = input.directionFlagSet();
        QueueFp604Api.Mxcsr mxcsr = input.mxcsr();

        // Local register state initialized from entry V/N
        long rax = v.raxBits();
        long rcx = v.rcxBits();
        long rdx = v.rdxBits();
        long r8 = v.r8Bits();
        long r9 = v.r9Bits();
        long r10 = v.r10Bits();
        long r11 = v.r11Bits();
        long rbx = n.rbxBits();
        long rbp = n.rbpBits();
        long rsi = n.rsiBits();
        long rdi = n.rdiBits();
        long r12 = n.r12Bits();
        long r13 = n.r13Bits();
        long r14 = n.r14Bits();
        long r15 = n.r15Bits();

        // 0x423b0d4: xor eax, eax -> EAX = 0
        rax = 0L;

        // 0x423b0d6: lea r9, [rip + 0x1e8983]
        // nextRIP = 0x423b0dd. Table RVA = 0x4423a60. Address = image + 0x4423a60
        r9 = image + 0x4423a60L;

        // 0x423b0dd: mov rdx, r9
        rdx = r9;

        // 0x423b0e0: lea r8d, [rax + 8] -> R8D = 8 (zero-extended)
        r8 = 8L;

        // Loop: scan at most 45 key DWORDs at stride 8
        // 0x423b0e4: cmp ecx, dword ptr [rdx]
        // 0x423b0e6: je 0x423b113 (match)
        // 0x423b0e8: inc eax
        // 0x423b0ea: add rdx, r8
        // 0x423b0ed: cmp eax, 0x2d
        // 0x423b0f0: jb 0x423b0e4 (continue if EAX < 45)

        boolean matched = false;
        for (int i = 0; i < 45; i++) {
            int key = memory.readDword(rdx);
            if (Integer.toUnsignedLong(key) == Integer.toUnsignedLong((int)rcx)) {
                // Match found
                // 0x423b113: mov eax, dword ptr [r9 + rax*8 + 4]
                // rax is the index i (0-based)
                long addr = r9 + rax * 8L + 4L;
                int val = memory.readDword(addr);
                rax = Integer.toUnsignedLong(val);
                matched = true;
                break;
            }
            // 0x423b0e8: inc eax
            rax = (rax + 1L) & 0xFFFFFFFFL;
            // 0x423b0ea: add rdx, r8
            rdx = rdx + r8;
            // 0x423b0ed: cmp eax, 0x2d
            // 0x423b0f0: jb 0x423b0e4
            // If EAX >= 45, loop ends (full miss)
            if (rax >= 45L) {
                break;
            }
        }

        if (!matched) {
            // Full miss path
            // 0x423b0f2: lea eax, [rcx - 0x13] -> EAX = RCX - 19 (mod 32-bit)
            rax = (rcx - 0x13L) & 0xFFFFFFFFL;

            // 0x423b0f5: cmp eax, 0x11
            // 0x423b0f8: ja 0x423b100 (if EAX > 17)
            if (rax > 0x11L) {
                // 0x423b100: add ecx, 0xffffff44 -> ECX = ECX - 188 (mod 32-bit)
                rcx = (rcx - 0xBC) & 0xFFFFFFFFL;
                // 0x423b106: mov eax, 0x16
                rax = 0x16L;
                // 0x423b10b: cmp ecx, 0xe
                // 0x423b10e: cmovbe eax, r8d (if ECX <= 14, EAX = R8D = 8)
                if (rcx <= 0xEL) {
                    rax = r8;
                }
            } else {
                // 0x423b0fa: mov eax, 0xd
                rax = 0x0DL;
            }
        }

        // RET: read QWORD at entry SP
        long returnRip = memory.readQword(rsp);
        long callerRsp = rsp + 8L;

        // Construct NormalReturn with updated V/N
        VolatileBits newV = new VolatileBits(
            rax, rcx, rdx, r8, r9, r10, r11,
            v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5()
        );
        NonvolatileBits newN = new NonvolatileBits(
            rbx, rbp, rsi, rdi, r12, r13, r14, r15, n.xmm6()
        );

        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            newV, returnRip, callerRsp, newN
        );

        FullCopy437Api.CallResult cr = new FullCopy437Api.CallResult(nr, df);
        return new QueueFp604Api.Normal(cr, mxcsr);
    }
}