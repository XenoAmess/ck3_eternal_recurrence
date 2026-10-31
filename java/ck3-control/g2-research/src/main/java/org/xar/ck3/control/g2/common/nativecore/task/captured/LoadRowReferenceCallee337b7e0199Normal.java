package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * Package-private helper implementing source range [337B873, 337B9B4).
 * Handles new-entry dispatch, empty insertion, existing-key cleanup, and occupied-next-empty move.
 * Exits to 337BBAB (normal return) or 337B9B4 (displacement loop).
 */
final class LoadRowReferenceCallee337b7e0199Normal {

    private static final long RVA_337B873 = 0x337B873L;
    private static final long RVA_337B8C4 = 0x337B8C4L;
    private static final long RVA_337B917 = 0x337B917L;
    private static final long RVA_337B9B4 = 0x337B9B4L;
    private static final long RVA_337BBAB = 0x337BBABL;

    public static void run(LoadRowReferenceCallee337b7e0199.State s) {
        if (s.pc == RVA_337B873) {
            // 337B873: movzx eax, BYTE PTR [rbx+0x4]
            s.rax = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rbx + 4L));

            // 337B877: lea r13, [rbx+0x10] -> R13 = RBX + 0x10
            s.r13 = s.rbx + 0x10L;

            // 337B87B: xor r12d, r12d -> R12D = 0, R12 = 0 (zero-extend)
            s.r12 = 0L;

            // 337B87E: test al, al
            // 337B880: jne 0x337B917
            if ((s.rax & 0xFFL) != 0L) {
                s.pc = RVA_337B917;
                return;
            }

            // 337B886: mov DWORD PTR [rbx], r8d
            s.m.writeDword(s.rbx, (int)s.r8);

            // 337B889: mov BYTE PTR [rbx+0x4], r14b
            s.m.writeByte(s.rbx + 4L, (int)(s.r14 & 0xFFL));

            // 337B88D: mov rax, QWORD PTR [r9]
            s.rax = s.m.readQword(s.r9);

            // 337B890: mov QWORD PTR [rbx+0x8], rax
            s.m.writeQword(s.rbx + 8L, s.rax);

            // 337B894: mov QWORD PTR [rbp+0x57], r13
            s.m.writeQword(s.rbp + 0x57L, s.r13);

            // 337B898: mov QWORD PTR [r13+0x38], r12
            s.m.writeQword(s.r13 + 0x38L, s.r12);

            // 337B89C: mov rax, QWORD PTR [rbp+0x7f]
            s.rax = s.m.readQword(s.rbp + 0x7FL);

            // 337B8A0: mov rcx, QWORD PTR [rax+0x38]
            s.rcx = s.m.readQword(s.rax + 0x38L);

            // 337B8A4: test rcx, rcx
            // 337B8A7: je 0x337B8B5
            if (s.rcx == 0L) {
                // Fall through to 337B8B5
            } else {
                // 337B8A9: mov rax, QWORD PTR [rcx]
                s.rax = s.m.readQword(s.rcx);

                // 337B8AC: mov rdx, r13
                s.rdx = s.r13;

                // 337B8AF: call QWORD PTR [rax]
                // Length 2 for [RAX] call.
                s.call(0x337B8AFL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax), 2);

                // 337B8B1: mov QWORD PTR [r13+0x38], rax
                s.m.writeQword(s.r13 + 0x38L, s.rax);
            }

            // 337B8B5: inc DWORD PTR [rsi+0x10]
            int val = s.m.readDword(s.rsi + 0x10L);
            s.m.writeDword(s.rsi + 0x10L, val + 1);

            // 337B8B8: mov QWORD PTR [rdi], rbx
            s.m.writeQword(s.rdi, s.rbx);

            // 337B8BB: mov BYTE PTR [rdi+0x8], 0x1
            s.m.writeByte(s.rdi + 8L, 1);

            // 337B8BF: jmp 0x337BBAB
            s.pc = RVA_337BBAB;
            return;

        } else if (s.pc == RVA_337B8C4) {
            // 337B8C4: xor r12d, r12d -> R12 = 0
            s.r12 = 0L;

            // 337B8C7: mov QWORD PTR [rbp-0x11], r12
            s.m.writeQword(s.rbp - 0x11L, s.r12);

            // 337B8CB: mov rax, QWORD PTR [rbp+0x7f]
            s.rax = s.m.readQword(s.rbp + 0x7FL);

            // 337B8CF: mov rcx, QWORD PTR [rax+0x38]
            s.rcx = s.m.readQword(s.rax + 0x38L);

            // 337B8D3: test rcx, rcx
            // 337B8D6: je 0x337B8E5
            if (s.rcx == 0L) {
                // Fall through to 337B8E5
            } else {
                // 337B8D8: mov rax, QWORD PTR [rcx]
                s.rax = s.m.readQword(s.rcx);

                // 337B8DB: lea rdx, [rbp-0x49] -> RDX = RBP - 0x49
                s.rdx = s.rbp - 0x49L;

                // 337B8DF: call QWORD PTR [rax]
                s.call(0x337B8DFL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax), 2);

                // 337B8E1: mov QWORD PTR [rbp-0x11], rax
                s.m.writeQword(s.rbp - 0x11L, s.rax);
            }

            // 337B8E5: lea rdx, [rbx+0x10] -> RDX = RBX + 0x10
            s.rdx = s.rbx + 0x10L;

            // 337B8E9: lea rcx, [rbp-0x49] -> RCX = RBP - 0x49
            s.rcx = s.rbp - 0x49L;

            // 337B8ED: call 0xa636f0
            s.call(0x337B8EDL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0xA636F0L, 5);

            // 337B8F2: mov rcx, QWORD PTR [rbp-0x11]
            s.rcx = s.m.readQword(s.rbp - 0x11L);

            // 337B8F6: test rcx, rcx
            // 337B8F9: je 0x337B90B
            if (s.rcx == 0L) {
                // Fall through to 337B90B
            } else {
                // 337B8FB: mov rax, QWORD PTR [rcx]
                s.rax = s.m.readQword(s.rcx);

                // 337B8FE: lea rdx, [rbp-0x49] -> RDX = RBP - 0x49
                s.rdx = s.rbp - 0x49L;

                // 337B902: cmp rcx, rdx
                // 337B905: setne dl
                // SETNE DL: if RCX != RDX, DL = 1, else DL = 0. Only low 8 bits of RDX change.
                if (s.rcx != s.rdx) {
                    s.rdx = (s.rdx & 0xFFFFFFFFFFFFFF00L) | 1L;
                } else {
                    s.rdx = (s.rdx & 0xFFFFFFFFFFFFFF00L) | 0L;
                }

                // 337B908: call QWORD PTR [rax+0x20]
                s.call(0x337B908L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax + 0x20L), 3);
            }

            // 337B90B: mov QWORD PTR [rdi], rbx
            s.m.writeQword(s.rdi, s.rbx);

            // 337B90E: mov BYTE PTR [rdi+0x8], 0x0
            s.m.writeByte(s.rdi + 8L, 0);

            // 337B912: jmp 0x337BBAB
            s.pc = RVA_337BBAB;
            return;

        } else if (s.pc == RVA_337B917) {
            // 337B917: mov ecx, DWORD PTR [rbx]
            s.rcx = Integer.toUnsignedLong(s.m.readDword(s.rbx));

            // 337B919: inc al
            // INC AL: increments low 8 bits of RAX. Preserves upper bits.
            s.rax = (s.rax & 0xFFFFFFFFFFFFFF00L) | ((s.rax + 1L) & 0xFFL);

            // 337B91B: mov rdx, r13
            s.rdx = s.r13;

            // 337B91E: cmp BYTE PTR [rbx+0x54], 0x0
            // 337B922: jne 0x337B9B4
            int flag = s.m.readUnsignedByte(s.rbx + 0x54L);
            if (flag != 0) {
                s.pc = RVA_337B9B4;
                return;
            }

            // 337B928: mov DWORD PTR [rbx+0x50], ecx
            s.m.writeDword(s.rbx + 0x50L, (int)s.rcx);

            // 337B92B: mov BYTE PTR [rbx+0x54], al
            s.m.writeByte(s.rbx + 0x54L, (int)(s.rax & 0xFFL));

            // 337B92E: mov rax, QWORD PTR [rbx+0x8]
            s.rax = s.m.readQword(s.rbx + 8L);

            // 337B932: mov QWORD PTR [rbx+0x58], rax
            s.m.writeQword(s.rbx + 0x58L, s.rax);

            // 337B936: lea rcx, [rbx+0x60] -> RCX = RBX + 0x60
            s.rcx = s.rbx + 0x60L;

            // 337B93A: mov QWORD PTR [rcx+0x38], r12
            s.m.writeQword(s.rcx + 0x38L, s.r12);

            // 337B93E: call 0x87c9b0
            s.call(0x337B93EL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x87C9B0L, 5);

            // 337B943: mov r8d, DWORD PTR [rbp+0x67]
            s.r8 = Integer.toUnsignedLong(s.m.readDword(s.rbp + 0x67L));

            // 337B947: mov DWORD PTR [rbx], r8d
            s.m.writeDword(s.rbx, (int)s.r8);

            // 337B94A: mov BYTE PTR [rbx+0x4], r14b
            s.m.writeByte(s.rbx + 4L, (int)(s.r14 & 0xFFL));

            // 337B94E: mov rax, QWORD PTR [rbp+0x6f]
            s.rax = s.m.readQword(s.rbp + 0x6FL);

            // 337B952: mov rax, QWORD PTR [rax]
            s.rax = s.m.readQword(s.rax);

            // 337B955: mov QWORD PTR [rbp-0x49], rax
            s.m.writeQword(s.rbp - 0x49L, s.rax);

            // 337B959: lea rax, [rbp-0x41] -> RAX = RBP - 0x41
            s.rax = s.rbp - 0x41L;

            // 337B95D: mov QWORD PTR [rbp+0x57], rax
            s.m.writeQword(s.rbp + 0x57L, s.rax);

            // 337B961: mov QWORD PTR [rbp-0x9], r12
            s.m.writeQword(s.rbp - 9L, s.r12);

            // 337B965: mov rax, QWORD PTR [rbp+0x7f]
            s.rax = s.m.readQword(s.rbp + 0x7FL);

            // 337B969: mov rcx, QWORD PTR [rax+0x38]
            s.rcx = s.m.readQword(s.rax + 0x38L);

            // 337B96D: test rcx, rcx
            // 337B970: je 0x337B97F
            if (s.rcx == 0L) {
                // Fall through to 337B97F
            } else {
                // 337B972: mov rax, QWORD PTR [rcx]
                s.rax = s.m.readQword(s.rcx);

                // 337B975: lea rdx, [rbp-0x41] -> RDX = RBP - 0x41
                s.rdx = s.rbp - 0x41L;

                // 337B979: call QWORD PTR [rax]
                s.call(0x337B979L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax), 2);

                // 337B97B: mov QWORD PTR [rbp-0x9], rax
                s.m.writeQword(s.rbp - 9L, s.rax);
            }

            // 337B97F: lea rdx, [rbp-0x49] -> RDX = RBP - 0x49
            s.rdx = s.rbp - 0x49L;

            // 337B983: lea rcx, [rbx+0x8] -> RCX = RBX + 0x8
            s.rcx = s.rbx + 8L;

            // 337B987: call 0xe23ea0
            s.call(0x337B987L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0xE23EA0L, 5);

            // 337B98C: mov rcx, QWORD PTR [rbp-0x9]
            s.rcx = s.m.readQword(s.rbp - 9L);

            // 337B990: test rcx, rcx
            // 337B993: je 0x337B9A5
            if (s.rcx == 0L) {
                // Fall through to 337B9A5
            } else {
                // 337B995: mov rax, QWORD PTR [rcx]
                s.rax = s.m.readQword(s.rcx);

                // 337B998: lea rdx, [rbp-0x41] -> RDX = RBP - 0x41
                s.rdx = s.rbp - 0x41L;

                // 337B99C: cmp rcx, rdx
                // 337B99F: setne dl
                if (s.rcx != s.rdx) {
                    s.rdx = (s.rdx & 0xFFFFFFFFFFFFFF00L) | 1L;
                } else {
                    s.rdx = (s.rdx & 0xFFFFFFFFFFFFFF00L) | 0L;
                }

                // 337B9A2: call QWORD PTR [rax+0x20]
                s.call(0x337B9A2L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.m.readQword(s.rax + 0x20L), 3);
            }

            // 337B9A5: inc DWORD PTR [rsi+0x10]
            int val2 = s.m.readDword(s.rsi + 0x10L);
            s.m.writeDword(s.rsi + 0x10L, val2 + 1);

            // 337B9A8: mov QWORD PTR [rdi], rbx
            s.m.writeQword(s.rdi, s.rbx);

            // 337B9AB: mov BYTE PTR [rdi+0x8], 0x1
            s.m.writeByte(s.rdi + 8L, 1);

            // 337B9AF: jmp 0x337BBAB
            s.pc = RVA_337BBAB;
            return;
        }

        throw new UnsupportedOperationException("Unexpected PC in Normal helper: " + Long.toHexString(s.pc));
    }
}
