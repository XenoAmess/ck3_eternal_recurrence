package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class LoadRowReference34ef710195 {
    private LoadRowReference34ef710195() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        long image = entry.imageBaseBits();
        long rsp = entry.rspBits();
        VolatileBits v = entry.volatileBits();
        NonvolatileBits nv = entry.nonvolatileBits();

        long rax = v.raxBits();
        long rcx = v.rcxBits();
        long rdx = v.rdxBits();
        long r8 = v.r8Bits();
        long r9 = v.r9Bits();
        long r10 = v.r10Bits();
        long r11 = v.r11Bits();
        Bits128 x0 = v.xmm0();
        Bits128 x1 = v.xmm1();
        Bits128 x2 = v.xmm2();
        Bits128 x3 = v.xmm3();
        Bits128 x4 = v.xmm4();
        Bits128 x5 = v.xmm5();

        long rbx = nv.rbxBits();
        long rbp = nv.rbpBits();
        long rsi = nv.rsiBits();
        long rdi = nv.rdiBits();
        long r12 = nv.r12Bits();
        long r13 = nv.r13Bits();
        long r14 = nv.r14Bits();
        long r15 = nv.r15Bits();
        Bits128 x6 = nv.xmm6();

        // 0x34ef710: mov qword ptr [rsp + 0x10], rdx
        memory.writeQword(rsp + 0x10L, rdx);
        // 0x34ef715: mov qword ptr [rsp + 8], rcx
        memory.writeQword(rsp + 8L, rcx);
        // 0x34ef71a: push rbp
        rsp -= 8L; memory.writeQword(rsp, rbp);
        // 0x34ef71b: push rbx
        rsp -= 8L; memory.writeQword(rsp, rbx);
        // 0x34ef71c: push rsi
        rsp -= 8L; memory.writeQword(rsp, rsi);
        // 0x34ef71d: push rdi
        rsp -= 8L; memory.writeQword(rsp, rdi);
        // 0x34ef71e: push r14
        rsp -= 8L; memory.writeQword(rsp, r14);
        // 0x34ef720: lea rbp, [rsp - 0x37]
        rbp = rsp - 0x37L;
        // 0x34ef725: sub rsp, 0xa0
        rsp -= 0xa0L;
        // 0x34ef72c: mov rsi, rdx
        rsi = rdx;
        // 0x34ef72f: mov rbx, rcx
        rbx = rcx;
        // 0x34ef732: xor edi, edi
        rdi = 0L;
        // 0x34ef734: mov dword ptr [rcx + 8], edi
        memory.writeDword(rcx + 8L, (int)rdi);
        // 0x34ef737: lea rax, [rip + 0x14091ea]
        rax = image + 0x48F8928L;
        // 0x34ef73e: mov qword ptr [rcx], rax
        memory.writeQword(rcx, rax);
        // 0x34ef741: mov rax, qword ptr [rdx]
        rax = memory.readQword(rdx);
        // 0x34ef744: mov qword ptr [rcx + 0x10], rax
        memory.writeQword(rcx + 0x10L, rax);
        // 0x34ef748: mov qword ptr [rdx], rdi
        memory.writeQword(rdx, rdi);
        // 0x34ef74b: mov dword ptr [rcx + 0x18], edi
        memory.writeDword(rcx + 0x18L, (int)rdi);

        // 0x34ef74e: call 0x34f04d0 (length 5)
        memory.writeQword(rsp - 8L, image + 0x34ef753L);
        VolatileBits retV = calls.invoke(new Call(0x34ef74eL, TargetKind.DIRECT_RVA, 0x34f04d0L, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
        rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
        x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();

        // 0x34ef753: mov dword ptr [rbx + 0x30], edi
        memory.writeDword(rbx + 0x30L, (int)rdi);
        // 0x34ef756: mov dword ptr [rbx + 0x3c], 0x3f666666
        memory.writeDword(rbx + 0x3cL, 0x3f666666);
        // 0x34ef75d: lea rax, [rbx + 0x48]
        rax = rbx + 0x48L;
        // 0x34ef761: mov qword ptr [rbx + 0x40], rax
        memory.writeQword(rbx + 0x40L, rax);
        // 0x34ef765: lea rcx, [rip + 0x14092ac]
        rcx = image + 0x48F8A18L;
        // 0x34ef76c: mov qword ptr [rax], rcx
        memory.writeQword(rax, rcx);
        // 0x34ef76f: lea rcx, [rip + 0x1feea72]
        rcx = image + 0x54DE1E8L;
        // 0x34ef776: mov qword ptr [rax + 0x458], rcx
        memory.writeQword(rax + 0x458L, rcx);
        // 0x34ef77d: lea rdx, [rbx + 0x50]
        rdx = rbx + 0x50L;
        // 0x34ef781: mov r10d, 0xf
        r10 = 0xfL;
        // 0x34ef787: bsr ecx, r10d
        rcx = 3L;
        // 0x34ef78b: mov dword ptr [rbp + 0x77], ecx
        memory.writeDword(rbp + 0x77L, (int)rcx);
        // 0x34ef78e: mov r8d, 0x1f
        r8 = 0x1fL;
        // 0x34ef794: mov eax, r8d
        rax = r8;
        // 0x34ef797: sub eax, ecx
        rax = (rax - rcx) & 0xFFFFFFFFL;
        // 0x34ef799: mov ecx, r8d
        rcx = r8;
        // 0x34ef79c: sub ecx, eax
        rcx = (rcx - rax) & 0xFFFFFFFFL;
        // 0x34ef79e: mov eax, 1
        rax = 1L;
        // 0x34ef7a3: shl eax, cl
        rax = (rax << (rcx & 0x1F)) & 0xFFFFFFFFL;
        // 0x34ef7a5: lea ecx, [rdi + 0x20]
        rcx = rdi + 0x20L;
        // 0x34ef7a8: bsr r9d, eax
        r9 = (rax == 0L) ? 0L : (63L - Long.numberOfLeadingZeros(rax));
        // 0x34ef7ac: mov dword ptr [rbp + 0x7f], r9d
        memory.writeDword(rbp + 0x7fL, (int)r9);
        // 0x34ef7b0: je 0x34ef7b7 (ZF from BSR)
        if (rax == 0L) {
            // 0x34ef7b7: mov r8d, ecx
            r8 = rcx;
        } else {
            // 0x34ef7b2: sub r8d, r9d
            r8 = (r8 - r9) & 0xFFFFFFFFL;
        }
        // 0x34ef7ba: sub ecx, r8d
        rcx = (rcx - r8) & 0xFFFFFFFFL;
        // 0x34ef7bd: mov qword ptr [rbx + 0x28], rdx
        memory.writeQword(rbx + 0x28L, rdx);
        // 0x34ef7c1: mov dword ptr [rbx + 0x34], r10d
        memory.writeDword(rbx + 0x34L, (int)r10);
        // 0x34ef7c5: add cl, 2
        rcx = (rcx & ~0xFFL) | ((rcx + 2L) & 0xFFL);
        // 0x34ef7c8: movzx eax, cl
        rax = rcx & 0xFFL;
        // 0x34ef7cb: mov byte ptr [rbx + 0x38], al
        memory.writeByte(rbx + 0x38L, (int)rax);
        // 0x34ef7ce: add rax, 0x10
        rax = rax + 0x10L;
        // 0x34ef7d2: lea rcx, [rax + rax*2]
        rcx = rax + rax * 2L;
        // 0x34ef7d6: shl rcx, 4
        rcx = rcx << 4;
        // 0x34ef7da: add rcx, rdx
        rcx = rcx + rdx;
        // 0x34ef7dd: cmp rdx, rcx
        // 0x34ef7e0: je 0x34ef7ef (ZF from CMP)
        if (rdx == rcx) {
            // 0x34ef7ef: mov byte ptr [rcx + 4], 0xff
            memory.writeByte(rcx + 4L, 0xff);
        } else {
            // Loop 0x34ef7e2..0x34ef7ed
            while (rdx != rcx) {
                // 0x34ef7e2: mov byte ptr [rdx + 4], 0
                memory.writeByte(rdx + 4L, 0);
                // 0x34ef7e6: add rdx, 0x30
                rdx = rdx + 0x30L;
            }
            // 0x34ef7ef: mov byte ptr [rcx + 4], 0xff
            memory.writeByte(rcx + 4L, 0xff);
        }

        // 0x34ef7f3: mov rax, qword ptr [rbx + 0x10]
        rax = memory.readQword(rbx + 0x10L);
        // 0x34ef7f7: test rax, rax
        // 0x34ef7fa: je 0x34ef8ee (ZF from TEST)
        if (rax == 0L) {
            // Jump to 0x34ef8ee
        } else {
            // 0x34ef800: lea rdi, [rax + 0x18]
            rdi = rax + 0x18L;
            // 0x34ef804: lea rax, [rip + 0x14092c5]
            rax = image + 0x48F8AD0L;
            // 0x34ef80b: mov qword ptr [rbp - 0x11], rax
            memory.writeQword(rbp - 0x11L, rax);
            // 0x34ef80f: lea rax, [rip + 0x7ea]
            rax = image + 0x34F0000L;
            // 0x34ef816: mov qword ptr [rbp - 9], rax
            memory.writeQword(rbp - 9L, rax);
            // 0x34ef81a: mov qword ptr [rbp - 1], rbx
            memory.writeQword(rbp - 1L, rbx);
            // 0x34ef81e: lea rax, [rbp - 0x11]
            rax = rbp - 0x11L;
            // 0x34ef822: mov qword ptr [rbp + 0x27], rax
            memory.writeQword(rbp + 0x27L, rax);
            // 0x34ef826: mov qword ptr [rbp - 0x39], rbx
            memory.writeQword(rbp - 0x39L, rbx);
            // 0x34ef82a: lea r14, [rip + 0x288670f]
            r14 = image + 0x5D75F40L;
            // 0x34ef831: mov qword ptr [rbp - 0x31], r14
            memory.writeQword(rbp - 0x31L, r14);
            // 0x34ef835: mov byte ptr [rbp - 0x29], 0
            memory.writeByte(rbp - 0x29L, 0);
            // 0x34ef839: mov rcx, r14
            rcx = r14;
            // 0x34ef83c: call 0x42219e0 (length 5)
            memory.writeQword(rsp - 8L, image + 0x34ef841L);
            retV = calls.invoke(new Call(0x34ef83cL, TargetKind.DIRECT_RVA, 0x42219e0L, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
            rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
            x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();
            // 0x34ef841: test eax, eax
            // 0x34ef843: jne 0x34ef929 (ZF from TEST)
            if ((int)rax != 0) {
                // 0x34ef929: mov ecx, eax
                rcx = rax & 0xFFFFFFFFL;
                // 0x34ef92b: call 0x4222120 (length 5)
                memory.writeQword(rsp - 8L, image + 0x34ef930L);
                retV = calls.invoke(new Call(0x34ef92bL, TargetKind.DIRECT_RVA, 0x4222120L, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
                rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
                x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();
                // 0x34ef930: int3
                throw new UnsupportedOperationException("INT3 at 34EF930");
            }
            // 0x34ef849: mov byte ptr [rbp - 0x29], 1
            memory.writeByte(rbp - 0x29L, 1);
            // 0x34ef84d: movzx eax, byte ptr [rbp - 0x39]
            rax = memory.readUnsignedByte(rbp - 0x39L);
            // 0x34ef851: xor eax, 0x811c9dc5
            rax = (rax ^ 0x811c9dc5L) & 0xFFFFFFFFL;
            // 0x34ef856: imul ecx, eax, 0x1000193
            rcx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef85c: movzx eax, byte ptr [rbp - 0x38]
            rax = memory.readUnsignedByte(rbp - 0x38L);
            // 0x34ef860: xor eax, ecx
            rax = (rax ^ rcx) & 0xFFFFFFFFL;
            // 0x34ef862: imul ecx, eax, 0x1000193
            rcx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef868: movzx eax, byte ptr [rbp - 0x37]
            rax = memory.readUnsignedByte(rbp - 0x37L);
            // 0x34ef86c: xor eax, ecx
            rax = (rax ^ rcx) & 0xFFFFFFFFL;
            // 0x34ef86e: imul ecx, eax, 0x1000193
            rcx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef874: movzx eax, byte ptr [rbp - 0x36]
            rax = memory.readUnsignedByte(rbp - 0x36L);
            // 0x34ef878: xor eax, ecx
            rax = (rax ^ rcx) & 0xFFFFFFFFL;
            // 0x34ef87a: imul ecx, eax, 0x1000193
            rcx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef880: movzx eax, byte ptr [rbp - 0x35]
            rax = memory.readUnsignedByte(rbp - 0x35L);
            // 0x34ef884: xor eax, ecx
            rax = (rax ^ rcx) & 0xFFFFFFFFL;
            // 0x34ef886: imul edx, eax, 0x1000193
            rdx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef88c: movzx eax, byte ptr [rbp - 0x34]
            rax = memory.readUnsignedByte(rbp - 0x34L);
            // 0x34ef890: xor eax, edx
            rax = (rax ^ rdx) & 0xFFFFFFFFL;
            // 0x34ef892: imul edx, eax, 0x1000193
            rdx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef898: movzx eax, byte ptr [rbp - 0x33]
            rax = memory.readUnsignedByte(rbp - 0x33L);
            // 0x34ef89c: xor eax, edx
            rax = (rax ^ rdx) & 0xFFFFFFFFL;
            // 0x34ef89e: imul edx, eax, 0x1000193
            rdx = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef8a4: movzx eax, byte ptr [rbp - 0x32]
            rax = memory.readUnsignedByte(rbp - 0x32L);
            // 0x34ef8a8: xor eax, edx
            rax = (rax ^ rdx) & 0xFFFFFFFFL;
            // 0x34ef8aa: imul r8d, eax, 0x1000193
            r8 = (rax * 0x1000193L) & 0xFFFFFFFFL;
            // 0x34ef8b1: lea rax, [rbp - 0x11]
            rax = rbp - 0x11L;
            // 0x34ef8b5: mov qword ptr [rsp + 0x28], rax
            memory.writeQword(rsp + 0x28L, rax);
            // 0x34ef8ba: lea r9, [rbp - 0x39]
            r9 = rbp - 0x39L;
            // 0x34ef8be: lea rdx, [rbp - 0x21]
            rdx = rbp - 0x21L;
            // 0x34ef8c2: mov rcx, rdi
            rcx = rdi;
            // 0x34ef8c5: call 0x337b7e0 (length 5)
            memory.writeQword(rsp - 8L, image + 0x34ef8caL);
            retV = calls.invoke(new Call(0x34ef8c5L, TargetKind.DIRECT_RVA, 0x337b7e0L, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
            rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
            x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();
            // 0x34ef8ca: nop
            // 0x34ef8cb: mov rcx, r14
            rcx = r14;
            // 0x34ef8ce: call 0x4221a04 (length 5)
            memory.writeQword(rsp - 8L, image + 0x34ef8d3L);
            retV = calls.invoke(new Call(0x34ef8ceL, TargetKind.DIRECT_RVA, 0x4221a04L, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
            rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
            x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();
            // 0x34ef8d3: nop
            // 0x34ef8d4: mov rcx, qword ptr [rbp + 0x27]
            rcx = memory.readQword(rbp + 0x27L);
            // 0x34ef8d8: test rcx, rcx
            // 0x34ef8db: je 0x34ef8ee (ZF from TEST)
            if (rcx == 0L) {
                // Jump to 0x34ef8ee
            } else {
                // 0x34ef8dd: mov rax, qword ptr [rcx]
                rax = memory.readQword(rcx);
                // 0x34ef8e0: lea rdx, [rbp - 0x11]
                rdx = rbp - 0x11L;
                // 0x34ef8e4: cmp rcx, rdx
                // 0x34ef8e7: setne dl
                rdx = (rdx & ~0xFFL) | ((rcx != rdx) ? 1L : 0L);
                // 0x34ef8ea: call qword ptr [rax + 0x20] (length 3)
                long target = memory.readQword(rax + 0x20L);
                memory.writeQword(rsp - 8L, image + 0x34ef8edL);
                retV = calls.invoke(new Call(0x34ef8eaL, TargetKind.INDIRECT_ABSOLUTE, target, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
                rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
                x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();
                // 0x34ef8ed: nop
            }
        }

        // 0x34ef8ee: mov rcx, qword ptr [rsi]
        rcx = memory.readQword(rsi);
        // 0x34ef8f1: test rcx, rcx
        // 0x34ef8f4: je 0x34ef918 (ZF from TEST)
        if (rcx == 0L) {
            // Jump to 0x34ef918
        } else {
            // 0x34ef8f6: add rcx, 8
            rcx = rcx + 8L;
            // 0x34ef8fa: mov eax, 0xffffffff
            rax = 0xffffffffL;
            // 0x34ef8ff: lock xadd dword ptr [rcx + 8], eax
            int original = memory.lockedXaddDword(rcx + 8L, (int)rax);
            rax = Integer.toUnsignedLong(original);
            // 0x34ef904: cmp eax, 1
            // 0x34ef907: jne 0x34ef918 (ZF from CMP)
            if (rax != 1L) {
                // Jump to 0x34ef918
            } else {
                // 0x34ef909: test rcx, rcx
                // 0x34ef90c: je 0x34ef918 (ZF from TEST)
                if (rcx == 0L) {
                    // Jump to 0x34ef918
                } else {
                    // 0x34ef90e: mov rax, qword ptr [rcx]
                    rax = memory.readQword(rcx);
                    // 0x34ef911: mov edx, 1
                    rdx = 1L;
                    // 0x34ef916: call qword ptr [rax] (length 2)
                    long target = memory.readQword(rax);
                    memory.writeQword(rsp - 8L, image + 0x34ef918L);
                    retV = calls.invoke(new Call(0x34ef916L, TargetKind.INDIRECT_ABSOLUTE, target, rsp, new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5), new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6)));
                    rax = retV.raxBits(); rcx = retV.rcxBits(); rdx = retV.rdxBits(); r8 = retV.r8Bits(); r9 = retV.r9Bits(); r10 = retV.r10Bits(); r11 = retV.r11Bits();
                    x0 = retV.xmm0(); x1 = retV.xmm1(); x2 = retV.xmm2(); x3 = retV.xmm3(); x4 = retV.xmm4(); x5 = retV.xmm5();
                }
            }
        }

        // 0x34ef918: mov rax, rbx
        rax = rbx;
        // 0x34ef91b: add rsp, 0xa0
        rsp += 0xa0L;
        // 0x34ef922: pop r14
        r14 = memory.readQword(rsp); rsp += 8L;
        // 0x34ef924: pop rdi
        rdi = memory.readQword(rsp); rsp += 8L;
        // 0x34ef925: pop rsi
        rsi = memory.readQword(rsp); rsp += 8L;
        // 0x34ef926: pop rbx
        rbx = memory.readQword(rsp); rsp += 8L;
        // 0x34ef927: pop rbp
        rbp = memory.readQword(rsp); rsp += 8L;
        // 0x34ef928: ret
        long returnRip = memory.readQword(rsp);
        long callerRsp = rsp + 8L;

        VolatileBits finalV = new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
        NonvolatileBits finalNV = new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);

        return new NormalReturn(finalV, returnRip, callerRsp, finalNV);
    }
}
