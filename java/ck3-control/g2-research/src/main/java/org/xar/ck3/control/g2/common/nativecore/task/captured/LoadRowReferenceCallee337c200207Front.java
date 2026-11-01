package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.z32;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.low8;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

final class LoadRowReferenceCallee337c200207Front {
    private LoadRowReferenceCallee337c200207Front() { }

    static void run(LoadRowReferenceCallee337c200207.State s) {
        // Entry at 0x337C292
        s.pc = 0x337C292;

        // 337c292: movzx eax, BYTE PTR [rbx+0x4]
        s.rax = z32(s.m.readUnsignedByte(s.rbx + 0x4));

        // 337c296: lea r13, [rbx+0x10]
        s.r13 = s.rbx + 0x10;

        // 337c29a: test al, al
        // 337c29c: jne 0x337c2eb
        if (s.rax != 0) {
            // 337c2eb: mov ecx, DWORD PTR [rbx]
            s.rcx = z32(s.m.readDword(s.rbx));

            // 337c2ed: inc al
            s.rax = low8(s.rax, (int)(s.rax + 1));

            // 337c2ef: mov rdx, r13
            s.rdx = s.r13;

            // 337c2f2: cmp BYTE PTR [rbx+0x54], 0x0
            // 337c2f6: jne 0x337c38c
            if (s.m.readUnsignedByte(s.rbx + 0x54) != 0) {
                // 337c38c: mov DWORD PTR [rsp+0x30], ecx
                s.m.writeDword(s.rsp + 0x30, (int)s.rcx);

                // 337c390: mov BYTE PTR [rsp+0x34], al
                s.m.writeByte(s.rsp + 0x34, (int)s.rax);

                // 337c394: mov rax, QWORD PTR [rbx+0x8]
                s.rax = s.m.readQword(s.rbx + 0x8);

                // 337c398: mov QWORD PTR [rsp+0x38], rax
                s.m.writeQword(s.rsp + 0x38, s.rax);

                // 337c39d: mov QWORD PTR [rbp-0x51], 0x0
                s.m.writeQword(s.rbp - 0x51, 0L);

                // 337c3a5: lea rcx, [rsp+0x40]
                s.rcx = s.rsp + 0x40;

                // 337c3aa: call 0x87c9b0 (Direct, length 5)
                s.direct(0x337C3AA, 0x87C9B0L);

                // 337c3af: mov r8d, DWORD PTR [rbp+0x67]
                s.r8 = z32(s.m.readDword(s.rbp + 0x67));

                // 337c3b3: mov DWORD PTR [rbx], r8d
                s.m.writeDword(s.rbx, (int)s.r8);

                // 337c3b6: mov BYTE PTR [rbx+0x4], r14b
                s.m.writeByte(s.rbx + 0x4, (int)s.r14);

                // 337c3ba: mov rax, QWORD PTR [r12]
                s.rax = s.m.readQword(s.r12);

                // 337c3be: mov QWORD PTR [rbp-0x49], rax
                s.m.writeQword(s.rbp - 0x49, s.rax);

                // 337c3c2: lea rax, [rbp-0x41]
                s.rax = s.rbp - 0x41;

                // 337c3c6: mov QWORD PTR [rbp+0x57], rax
                s.m.writeQword(s.rbp + 0x57, s.rax);

                // 337c3ca: xor r12d, r12d
                s.r12 = 0;

                // 337c3cd: mov QWORD PTR [rbp-0x9], r12
                s.m.writeQword(s.rbp - 0x9, s.r12);

                // 337c3d1: mov rcx, QWORD PTR [rbp+0x7f]
                s.rcx = s.m.readQword(s.rbp + 0x7f);

                // 337c3d5: mov rcx, QWORD PTR [rcx+0x38]
                s.rcx = s.m.readQword(s.rcx + 0x38);

                // 337c3d9: test rcx, rcx
                // 337c3dc: je 0x337c3eb
                if (s.rcx != 0) {
                    // 337c3de: mov rax, QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);

                    // 337c3e1: lea rdx, [rbp-0x41]
                    s.rdx = s.rbp - 0x41;

                    // 337c3e5: call QWORD PTR [rax] (Indirect, length 2)
                    s.indirect(0x337C3E5, s.m.readQword(s.rax), 2);

                    // 337c3e7: mov QWORD PTR [rbp-0x9], rax
                    s.m.writeQword(s.rbp - 0x9, s.rax);
                }

                // 337c3eb: lea rdx, [rbp-0x49]
                s.rdx = s.rbp - 0x49;

                // 337c3ef: lea rcx, [rbx+0x8]
                s.rcx = s.rbx + 0x8;

                // 337c3f3: call 0xe23ea0 (Direct, length 5)
                s.direct(0x337C3F3, 0xE23EA0L);

                // 337c3f8: mov rcx, QWORD PTR [rbp-0x9]
                s.rcx = s.m.readQword(s.rbp - 0x9);

                // 337c3fc: test rcx, rcx
                // 337c3ff: je 0x337c411
                if (s.rcx != 0) {
                    // 337c401: mov rax, QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);

                    // 337c404: lea rdx, [rbp-0x41]
                    s.rdx = s.rbp - 0x41;

                    // 337c408: cmp rcx, rdx
                    // 337c40b: setne dl
                    s.rdx = low8(s.rdx, s.rcx != s.rdx ? 1 : 0);

                    // 337c40e: call QWORD PTR [rax+0x20] (Indirect, length 3)
                    s.indirect(0x337C40E, s.m.readQword(s.rax + 0x20), 3);
                }

                // 337c411: mov r14, rbx
                s.r14 = s.rbx;

                // 337c414: movzx ecx, BYTE PTR [rsp+0x34]
                s.rcx = z32(s.m.readUnsignedByte(s.rsp + 0x34));

                // 337c419: nop

                // 337c420: lea rbx, [rbx+0x50] (Displace entry)
                s.pc = 0x337C420;
                return;
            } else {
                // 337c2fc: mov DWORD PTR [rbx+0x50], ecx
                s.m.writeDword(s.rbx + 0x50, (int)s.rcx);

                // 337c2ff: mov BYTE PTR [rbx+0x54], al
                s.m.writeByte(s.rbx + 0x54, (int)s.rax);

                // 337c302: mov rax, QWORD PTR [rbx+0x8]
                s.rax = s.m.readQword(s.rbx + 0x8);

                // 337c306: mov QWORD PTR [rbx+0x58], rax
                s.m.writeQword(s.rbx + 0x58, s.rax);

                // 337c30a: lea rcx, [rbx+0x60]
                s.rcx = s.rbx + 0x60;

                // 337c30e: mov QWORD PTR [rcx+0x38], 0x0
                s.m.writeQword(s.rcx + 0x38, 0L);

                // 337c316: call 0x87c9b0 (Direct, length 5)
                s.direct(0x337C316, 0x87C9B0L);

                // 337c31b: mov r8d, DWORD PTR [rbp+0x67]
                s.r8 = z32(s.m.readDword(s.rbp + 0x67));

                // 337c31f: mov DWORD PTR [rbx], r8d
                s.m.writeDword(s.rbx, (int)s.r8);

                // 337c322: mov BYTE PTR [rbx+0x4], r14b
                s.m.writeByte(s.rbx + 0x4, (int)s.r14);

                // 337c326: mov rax, QWORD PTR [r12]
                s.rax = s.m.readQword(s.r12);

                // 337c32a: mov QWORD PTR [rbp-0x49], rax
                s.m.writeQword(s.rbp - 0x49, s.rax);

                // 337c32e: lea rax, [rbp-0x41]
                s.rax = s.rbp - 0x41;

                // 337c332: mov QWORD PTR [rbp+0x57], rax
                s.m.writeQword(s.rbp + 0x57, s.rax);

                // 337c336: xor r12d, r12d
                s.r12 = 0;

                // 337c339: mov QWORD PTR [rbp-0x9], r12
                s.m.writeQword(s.rbp - 0x9, s.r12);

                // 337c33d: mov rcx, QWORD PTR [rbp+0x7f]
                s.rcx = s.m.readQword(s.rbp + 0x7f);

                // 337c341: mov rcx, QWORD PTR [rcx+0x38]
                s.rcx = s.m.readQword(s.rcx + 0x38);

                // 337c345: test rcx, rcx
                // 337c348: je 0x337c357
                if (s.rcx != 0) {
                    // 337c34a: mov rax, QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);

                    // 337c34d: lea rdx, [rbp-0x41]
                    s.rdx = s.rbp - 0x41;

                    // 337c351: call QWORD PTR [rax] (Indirect, length 2)
                    s.indirect(0x337C351, s.m.readQword(s.rax), 2);

                    // 337c353: mov QWORD PTR [rbp-0x9], rax
                    s.m.writeQword(s.rbp - 0x9, s.rax);
                }

                // 337c357: lea rdx, [rbp-0x49]
                s.rdx = s.rbp - 0x49;

                // 337c35b: lea rcx, [rbx+0x8]
                s.rcx = s.rbx + 0x8;

                // 337c35f: call 0xe23ea0 (Direct, length 5)
                s.direct(0x337C35F, 0xE23EA0L);

                // 337c364: mov rcx, QWORD PTR [rbp-0x9]
                s.rcx = s.m.readQword(s.rbp - 0x9);

                // 337c368: test rcx, rcx
                // 337c36b: je 0x337c37d
                if (s.rcx != 0) {
                    // 337c36d: mov rax, QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);

                    // 337c370: lea rdx, [rbp-0x41]
                    s.rdx = s.rbp - 0x41;

                    // 337c374: cmp rcx, rdx
                    // 337c377: setne dl
                    s.rdx = low8(s.rdx, s.rcx != s.rdx ? 1 : 0);

                    // 337c37a: call QWORD PTR [rax+0x20] (Indirect, length 3)
                    s.indirect(0x337C37A, s.m.readQword(s.rax + 0x20), 3);
                }

                // 337c37d: inc DWORD PTR [rsi+0x10]
                s.m.writeDword(s.rsi + 0x10, s.m.readDword(s.rsi + 0x10) + 1);

                // 337c380: mov QWORD PTR [rdi], rbx
                s.m.writeQword(s.rdi, s.rbx);

                // 337c383: mov BYTE PTR [rdi+0x8], 0x1
                s.m.writeByte(s.rdi + 0x8, 1);

                // 337c387: jmp 0x337c598
                s.pc = 0x337C598;
                return;
            }
        }

        // 337c29e: mov DWORD PTR [rbx], r8d
        s.m.writeDword(s.rbx, (int)s.r8);

        // 337c2a1: mov BYTE PTR [rbx+0x4], r14b
        s.m.writeByte(s.rbx + 0x4, (int)s.r14);

        // 337c2a5: mov rax, QWORD PTR [r9]
        s.rax = s.m.readQword(s.r9);

        // 337c2a8: mov QWORD PTR [rbx+0x8], rax
        s.m.writeQword(s.rbx + 0x8, s.rax);

        // 337c2ac: mov QWORD PTR [rbp+0x57], r13
        s.m.writeQword(s.rbp + 0x57, s.r13);

        // 337c2b0: xor r12d, r12d
        s.r12 = 0;

        // 337c2b3: mov QWORD PTR [r13+0x38], r12
        s.m.writeQword(s.r13 + 0x38, s.r12);

        // 337c2b7: mov rcx, QWORD PTR [rbp+0x7f]
        s.rcx = s.m.readQword(s.rbp + 0x7f);

        // 337c2bb: mov rcx, QWORD PTR [rcx+0x38]
        s.rcx = s.m.readQword(s.rcx + 0x38);

        // 337c2bf: test rcx, rcx
        // 337c2c2: je 0x337c2d0
        if (s.rcx != 0) {
            // 337c2c4: mov rax, QWORD PTR [rcx]
            s.rax = s.m.readQword(s.rcx);

            // 337c2c7: mov rdx, r13
            s.rdx = s.r13;

            // 337c2ca: call QWORD PTR [rax] (Indirect, length 2)
            s.indirect(0x337C2CA, s.m.readQword(s.rax), 2);

            // 337c2cc: mov QWORD PTR [r13+0x38], rax
            s.m.writeQword(s.r13 + 0x38, s.rax);
        }

        // 337c2d0: inc DWORD PTR [rsi+0x10]
        s.m.writeDword(s.rsi + 0x10, s.m.readDword(s.rsi + 0x10) + 1);

        // 337c2d3: mov QWORD PTR [rdi], rbx
        s.m.writeQword(s.rdi, s.rbx);

        // 337c2d6: mov BYTE PTR [rdi+0x8], 0x1
        s.m.writeByte(s.rdi + 0x8, 1);

        // 337c2da: jmp 0x337c598
        s.pc = 0x337C598;
    }
}