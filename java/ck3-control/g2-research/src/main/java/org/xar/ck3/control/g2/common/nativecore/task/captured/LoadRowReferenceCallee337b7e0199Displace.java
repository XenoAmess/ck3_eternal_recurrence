package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * Package-private helper implementing the displacement path of LoadRowReferenceCallee337b7e0199.
 * Owns source range [337B9B4, 337BB75).
 */
final class LoadRowReferenceCallee337b7e0199Displace {

    private static final long RVA_337B9B4 = 0x337B9B4L;
    private static final long RVA_337BA40 = 0x337BA40L;
    private static final long RVA_337BA9D = 0x337BA9DL;
    private static final long RVA_337BB2B = 0x337BB2BL;
    private static final long RVA_337BB75 = 0x337BB75L;
    private static final long RVA_337BBAB = 0x337BBABL;

    // Direct callee RVAs
    private static final long TARGET_87C9B0 = 0x87C9B0L;
    private static final long TARGET_A636F0 = 0xA636F0L;
    private static final long TARGET_337C040 = 0x337C040L;
    private static final long TARGET_337C5D0 = 0x337C5D0L;
    private static final long TARGET_E23EA0 = 0xE23EA0L;

    static void run(LoadRowReferenceCallee337b7e0199.State s) {
        // Entry point: 337B9B4
        // Save current state to stack slots for later restoration/cleanup
        // 337B9B4: mov DWORD PTR [rsp+0x30], ecx
        s.m.writeDword(s.rsp + 0x30, (int) s.rcx);
        // 337B9B8: mov BYTE PTR [rsp+0x34], al
        s.m.writeByte(s.rsp + 0x34, (int) (s.rax & 0xFF));
        // 337B9BC: mov rax, QWORD PTR [rbx+0x8]
        s.rax = s.m.readQword(s.rbx + 0x8);
        // 337B9C0: mov QWORD PTR [rsp+0x38], rax
        s.m.writeQword(s.rsp + 0x38, s.rax);
        // 337B9C5: mov QWORD PTR [rbp-0x51], r12
        s.m.writeQword(s.rbp - 0x51, s.r12);
        // 337B9C9: lea rcx, [rsp+0x40]
        s.rcx = s.rsp + 0x40;
        // 337B9CE: call 0x87C9B0 (Direct)
        s.call(0x337B9CEL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_87C9B0, 5);

        // 337B9D3: mov r8d, DWORD PTR [rbp+0x67]
        s.r8 = Integer.toUnsignedLong(s.m.readDword(s.rbp + 0x67));
        // 337B9D7: mov DWORD PTR [rbx], r8d
        s.m.writeDword(s.rbx, (int) s.r8);
        // 337B9DA: mov BYTE PTR [rbx+0x4], r14b
        s.m.writeByte(s.rbx + 0x4, (int) (s.r14 & 0xFF));

        // 337B9DE: mov rax, QWORD PTR [rbp+0x6f]
        s.rax = s.m.readQword(s.rbp + 0x6F);
        // 337B9E2: mov rax, QWORD PTR [rax]
        s.rax = s.m.readQword(s.rax);
        // 337B9E5: mov QWORD PTR [rbp-0x49], rax
        s.m.writeQword(s.rbp - 0x49, s.rax);
        // 337B9E9: lea rax, [rbp-0x41]
        s.rax = s.rbp - 0x41;
        // 337B9ED: mov QWORD PTR [rbp+0x57], rax
        s.m.writeQword(s.rbp + 0x57, s.rax);
        // 337B9F1: mov QWORD PTR [rbp-0x9], r12
        s.m.writeQword(s.rbp - 0x9, s.r12);

        // 337B9F5: mov rax, QWORD PTR [rbp+0x7f]
        s.rax = s.m.readQword(s.rbp + 0x7F);
        // 337B9F9: mov rcx, QWORD PTR [rax+0x38]
        s.rcx = s.m.readQword(s.rax + 0x38);
        // 337B9FD: test rcx, rcx
        if (s.rcx == 0) {
            // 337BA00: je 0x337BA0F
            // Fall through to 337BA0F
        } else {
            // 337BA02: mov rax, QWORD PTR [rcx]
            s.rax = s.m.readQword(s.rcx);
            // 337BA05: lea rdx, [rbp-0x41]
            s.rdx = s.rbp - 0x41;
            // 337BA09: call QWORD PTR [rax] (Indirect)
            s.call(0x337BA09L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax), 2);
            // 337BA0B: mov QWORD PTR [rbp-0x9], rax
            s.m.writeQword(s.rbp - 0x9, s.rax);
        }

        // 337BA0F: lea rdx, [rbp-0x49]
        s.rdx = s.rbp - 0x49;
        // 337BA13: lea rcx, [rbx+0x8]
        s.rcx = s.rbx + 0x8;
        // 337BA17: call 0xE23EA0 (Direct)
        s.call(0x337BA17L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_E23EA0, 5);

        // 337BA1C: mov rcx, QWORD PTR [rbp-0x9]
        s.rcx = s.m.readQword(s.rbp - 0x9);
        // 337BA20: test rcx, rcx
        if (s.rcx == 0) {
            // 337BA23: je 0x337BA35
            // Fall through to 337BA35
        } else {
            // 337BA25: mov rax, QWORD PTR [rcx]
            s.rax = s.m.readQword(s.rcx);
            // 337BA28: lea rdx, [rbp-0x41]
            s.rdx = s.rbp - 0x41;
            // 337BA2C: cmp rcx, rdx
            // 337BA2F: setne dl
            // SETNE DL compares full 64 pointers for inequality and changes only low8 RDX.
            // Preserve upper 56 bits of RDX.
            s.rdx = (s.rcx != s.rdx) ? ((s.rdx & ~0xFFL) | 1L) : (s.rdx & ~0xFFL);
            // 337BA32: call QWORD PTR [rax+0x20] (Indirect)
            s.call(0x337BA32L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax + 0x20), 3);
        }

        // 337BA35: mov r14, rbx
        s.r14 = s.rbx;
        // 337BA38: movzx ecx, BYTE PTR [rsp+0x34]
        s.rcx = s.m.readUnsignedByte(s.rsp + 0x34);
        // 337BA3D: nop DWORD PTR [rax] (No-op, does not read memory)
        // 337BA40: lea rbx, [rbx+0x50]
        // Loop: Displacement Walk
        while (true) {
            // Budget check before iteration at 337BA40
            s.budget.beforeStep(RVA_337BA40, s.rbx);

            // Advance RBX
            s.rbx = s.rbx + 0x50;

            // 337BA44: movzx eax, BYTE PTR [rbx+0x4]
            s.rax = s.m.readUnsignedByte(s.rbx + 0x4);
            // 337BA48: test al, al
            if (s.rax == 0) {
                // 337BA4A: je 0x337BB2B
                // Final Empty Slot Path
                // 337BB2B: mov eax, DWORD PTR [rsp+0x30]
                s.rax = Integer.toUnsignedLong(s.m.readDword(s.rsp + 0x30));
                // 337BB2F: mov DWORD PTR [rbx], eax
                s.m.writeDword(s.rbx, (int) s.rax);
                // 337BB31: mov BYTE PTR [rbx+0x4], cl
                s.m.writeByte(s.rbx + 0x4, (int) (s.rcx & 0xFF));
                // 337BB34: mov rax, QWORD PTR [rsp+0x38]
                s.rax = s.m.readQword(s.rsp + 0x38);
                // 337BB39: mov QWORD PTR [rbx+0x8], rax
                s.m.writeQword(s.rbx + 0x8, s.rax);
                // 337BB3D: lea rcx, [rbx+0x10]
                s.rcx = s.rbx + 0x10;
                // 337BB41: mov QWORD PTR [rcx+0x38], r12
                s.m.writeQword(s.rcx + 0x38, s.r12);
                // 337BB45: lea rdx, [rsp+0x40]
                s.rdx = s.rsp + 0x40;
                // 337BB4A: call 0x87C9B0 (Direct)
                s.call(0x337BB4AL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_87C9B0, 5);

                // 337BB4F: mov rcx, QWORD PTR [rbp-0x51]
                s.rcx = s.m.readQword(s.rbp - 0x51);
                // 337BB53: test rcx, rcx
                if (s.rcx == 0) {
                    // 337BB56: je 0x337BB69
                    // Fall through to 337BB69
                } else {
                    // 337BB58: mov rax, QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);
                    // 337BB5B: lea rdx, [rsp+0x40]
                    s.rdx = s.rsp + 0x40;
                    // 337BB60: cmp rcx, rdx
                    // 337BB63: setne dl
                    s.rdx = (s.rcx != s.rdx) ? ((s.rdx & ~0xFFL) | 1L) : (s.rdx & ~0xFFL);
                    // 337BB66: call QWORD PTR [rax+0x20] (Indirect)
                    s.call(0x337BB66L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax + 0x20), 3);
                }

                // 337BB69: inc DWORD PTR [rsi+0x10]
                int val = s.m.readDword(s.rsi + 0x10);
                s.m.writeDword(s.rsi + 0x10, val + 1);
                // 337BB6C: mov QWORD PTR [rdi], r14
                s.m.writeQword(s.rdi, s.r14);
                // 337BB6F: mov BYTE PTR [rdi+0x8], 0x1
                s.m.writeByte(s.rdi + 0x8, 1);
                // 337BB73: jmp 0x337BBAB
                s.pc = RVA_337BBAB;
                return;
            }

            // 337BA50: cmp al, cl
            // 337BA52: jae 0x337BA9D
            // Unsigned comparison AL >= CL
            if ((s.rax & 0xFFL) >= (s.rcx & 0xFFL)) {
                // Excessive Distance / Revert Path (337BA9D .. 337BB26)
                // 337BA9D: inc cl
                s.rcx = (s.rcx & ~0xFFL) | ((s.rcx + 1) & 0xFFL);
                // 337BA9F: mov BYTE PTR [rsp+0x34], cl
                s.m.writeByte(s.rsp + 0x34, (int) s.rcx);
                // 337BAA3: cmp cl, BYTE PTR [rsi+0x18]
                int limit = s.m.readUnsignedByte(s.rsi + 0x18);
                // 337BAA6: jbe 0x337BA40
                if ((s.rcx & 0xFFL) <= limit) {
                    // Continue loop
                    continue;
                }

                // 337BAA8: mov ecx, DWORD PTR [rsp+0x30]
                s.rcx = Integer.toUnsignedLong(s.m.readDword(s.rsp + 0x30));
                // 337BAAC: mov eax, DWORD PTR [r14]
                s.rax = Integer.toUnsignedLong(s.m.readDword(s.r14));
                // 337BAB3: mov DWORD PTR [rsp+0x30], eax
                s.m.writeDword(s.rsp + 0x30, (int) s.rax);
                // 337BAB6: mov DWORD PTR [r14], ecx
                s.m.writeDword(s.r14, (int) s.rcx);

                // 337BAB6: movzx ecx, BYTE PTR [rsp+0x34]
                s.rcx = s.m.readUnsignedByte(s.rsp + 0x34);
                // 337BABB: movzx eax, BYTE PTR [r14+0x4]
                s.rax = s.m.readUnsignedByte(s.r14 + 0x4);
                // 337BAC0: mov BYTE PTR [rsp+0x34], al
                s.m.writeByte(s.rsp + 0x34, (int) s.rax);
                // 337BAC4: mov BYTE PTR [r14+0x4], cl
                s.m.writeByte(s.r14 + 0x4, (int) s.rcx);

                // 337BAC8: mov rcx, QWORD PTR [rsp+0x38]
                s.rcx = s.m.readQword(s.rsp + 0x38);
                // 337BACD: mov rax, QWORD PTR [r14+0x8]
                s.rax = s.m.readQword(s.r14 + 0x8);
                // 337BAD1: mov QWORD PTR [rsp+0x38], rax
                s.m.writeQword(s.rsp + 0x38, s.rax);
                // 337BAD6: mov QWORD PTR [r14+0x8], rcx
                s.m.writeQword(s.r14 + 0x8, s.rcx);

                // 337BADA: mov rdx, r13
                s.rdx = s.r13;
                // 337BADD: lea rcx, [rsp+0x40]
                s.rcx = s.rsp + 0x40;
                // 337BAE2: call 0xA636F0 (Direct)
                s.call(0x337BAE2L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_A636F0, 5);

                // 337BAE7: mov rcx, rsi
                s.rcx = s.rsi;
                // 337BAEA: call 0x337C040 (Direct)
                s.call(0x337BAEAL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_337C040, 5);

                // 337BAEF: lea r9, [rsp+0x38]
                s.r9 = s.rsp + 0x38;
                // 337BAF4: mov r8d, DWORD PTR [rsp+0x30]
                s.r8 = Integer.toUnsignedLong(s.m.readDword(s.rsp + 0x30));
                // 337BAF9: lea rdx, [rbp-0x1]
                s.rdx = s.rbp - 0x1;
                // 337BAFD: mov rcx, rsi
                s.rcx = s.rsi;
                // 337BB00: call 0x337C5D0 (Direct)
                s.call(0x337BB00L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_337C5D0, 5);

                // 337BB05: mov rcx, QWORD PTR [rbp-0x51]
                s.rcx = s.m.readQword(s.rbp - 0x51);
                // 337BB09: test rcx, rcx
                if (s.rcx == 0) {
                    // 337BB0C: je 0x337BB1F
                    // Fall through to 337BB1F
                } else {
                    // 337BB0E: mov rax, QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);
                    // 337BB11: lea rdx, [rsp+0x40]
                    s.rdx = s.rsp + 0x40;
                    // 337BB16: cmp rcx, rdx
                    // 337BB19: setne dl
                    s.rdx = (s.rcx != s.rdx) ? ((s.rdx & ~0xFFL) | 1L) : (s.rdx & ~0xFFL);
                    // 337BB1C: call QWORD PTR [rax+0x20] (Indirect)
                    s.call(0x337BB1CL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax + 0x20), 3);
                }

                // 337BB1F: movups xmm0, XMMWORD PTR [rbp-0x1]
                s.x0 = s.m.read128(s.rbp - 0x1);
                // 337BB23: movups XMMWORD PTR [rdi], xmm0
                s.m.write128(s.rdi, s.x0);
                // 337BB26: jmp 0x337BBAB
                s.pc = RVA_337BBAB;
                return;
            }

            // Swap Path (337BA54 .. 337BA9B)
            // 337BA54: mov ecx, DWORD PTR [rsp+0x30]
            s.rcx = Integer.toUnsignedLong(s.m.readDword(s.rsp + 0x30));
            // 337BA58: mov eax, DWORD PTR [rbx]
            s.rax = Integer.toUnsignedLong(s.m.readDword(s.rbx));
            // 337BA5A: mov DWORD PTR [rsp+0x30], eax
            s.m.writeDword(s.rsp + 0x30, (int) s.rax);
            // 337BA5E: mov DWORD PTR [rbx], ecx
            s.m.writeDword(s.rbx, (int) s.rcx);

            // 337BA60: movzx ecx, BYTE PTR [rsp+0x34]
            s.rcx = s.m.readUnsignedByte(s.rsp + 0x34);
            // 337BA65: movzx eax, BYTE PTR [rbx+0x4]
            s.rax = s.m.readUnsignedByte(s.rbx + 0x4);
            // 337BA69: mov BYTE PTR [rsp+0x34], al
            s.m.writeByte(s.rsp + 0x34, (int) s.rax);
            // 337BA6D: mov BYTE PTR [rbx+0x4], cl
            s.m.writeByte(s.rbx + 0x4, (int) s.rcx);

            // 337BA70: mov rcx, QWORD PTR [rsp+0x38]
            s.rcx = s.m.readQword(s.rsp + 0x38);
            // 337BA75: mov rax, QWORD PTR [rbx+0x8]
            s.rax = s.m.readQword(s.rbx + 0x8);
            // 337BA79: mov QWORD PTR [rsp+0x38], rax
            s.m.writeQword(s.rsp + 0x38, s.rax);
            // 337BA7E: mov QWORD PTR [rbx+0x8], rcx
            s.m.writeQword(s.rbx + 0x8, s.rcx);

            // 337BA82: lea rdx, [rbx+0x10]
            s.rdx = s.rbx + 0x10;
            // 337BA86: lea rcx, [rsp+0x40]
            s.rcx = s.rsp + 0x40;
            // 337BA8B: call 0xA636F0 (Direct)
            s.call(0x337BA8BL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, TARGET_A636F0, 5);

            // 337BA90: movzx ecx, BYTE PTR [rsp+0x34]
            s.rcx = s.m.readUnsignedByte(s.rsp + 0x34);
            // 337BA95: inc cl
            s.rcx = (s.rcx & ~0xFFL) | ((s.rcx + 1) & 0xFFL);
            // 337BA97: mov BYTE PTR [rsp+0x34], cl
            s.m.writeByte(s.rsp + 0x34, (int) s.rcx);
            // 337BA9B: jmp 0x337BA40
            // Continue loop
        }
    }
}
