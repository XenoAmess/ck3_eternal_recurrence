package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.z32;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.low8;

final class LoadRowReferenceCallee337c200207Displace {
    private LoadRowReferenceCallee337c200207Displace() { }

    static void run(LoadRowReferenceCallee337c200207.State s) {
        while (true) {
            // 337C420: lea rbx,[rbx+0x50]
            s.budget.beforeStep(0x337C420, s.rbx);
            s.rbx = s.rbx + 0x50;

            // 337C424: movzx eax,BYTE PTR [rbx+0x4]
            int al = s.m.readUnsignedByte(s.rbx + 0x4);
            s.rax = z32(al);

            // 337C428: test al,al
            // 337C42A: je 0x337C50B
            if (al == 0) {
                // 337C50B: mov eax,DWORD PTR [rsp+0x30]
                s.rax = z32(s.m.readDword(s.rsp + 0x30));
                // 337C50F: mov DWORD PTR [rbx],eax
                s.m.writeDword(s.rbx, (int)s.rax);
                // 337C511: mov BYTE PTR [rbx+0x4],cl
                s.m.writeByte(s.rbx + 0x4, (int)s.rcx);
                // 337C514: mov rax,QWORD PTR [rsp+0x38]
                s.rax = s.m.readQword(s.rsp + 0x38);
                // 337C519: mov QWORD PTR [rbx+0x8],rax
                s.m.writeQword(s.rbx + 0x8, s.rax);
                // 337C51D: lea rcx,[rbx+0x10]
                s.rcx = s.rbx + 0x10;
                // 337C521: mov QWORD PTR [rcx+0x38],r12
                s.m.writeQword(s.rcx + 0x38, s.r12);
                // 337C525: lea rdx,[rsp+0x40]
                s.rdx = s.rsp + 0x40;
                // 337C52A: call 0x87c9b0 (direct, length 5)
                s.direct(0x337C52A, 0x87C9B0);
                // 337C52F: mov rcx,QWORD PTR [rbp-0x51]
                s.rcx = s.m.readQword(s.rbp - 0x51);
                // 337C533: test rcx,rcx
                // 337C536: je 0x337C549
                if (s.rcx == 0) {
                    // 337C549: inc DWORD PTR [rsi+0x10]
                    int val = s.m.readDword(s.rsi + 0x10);
                    s.m.writeDword(s.rsi + 0x10, val + 1);
                    // 337C54C: mov QWORD PTR [rdi],r14
                    s.m.writeQword(s.rdi, s.r14);
                    // 337C54F: mov BYTE PTR [rdi+0x8],0x1
                    s.m.writeByte(s.rdi + 0x8, 1);
                    // 337C553: jmp 0x337C598
                    s.pc = 0x337C598;
                    return;
                } else {
                    // 337C538: mov rax,QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);
                    // 337C53B: lea rdx,[rsp+0x40]
                    s.rdx = s.rsp + 0x40;
                    // 337C540: cmp rcx,rdx
                    // 337C543: setne dl
                    int dl = (s.rcx != s.rdx) ? 1 : 0;
                    s.rdx = low8(s.rdx, dl);
                    // 337C546: call QWORD PTR [rax+0x20] (indirect, length 3)
                    long target = s.m.readQword(s.rax + 0x20);
                    s.indirect(0x337C546, target, 3);
                    // 337C549: inc DWORD PTR [rsi+0x10]
                    int val = s.m.readDword(s.rsi + 0x10);
                    s.m.writeDword(s.rsi + 0x10, val + 1);
                    // 337C54C: mov QWORD PTR [rdi],r14
                    s.m.writeQword(s.rdi, s.r14);
                    // 337C54F: mov BYTE PTR [rdi+0x8],0x1
                    s.m.writeByte(s.rdi + 0x8, 1);
                    // 337C553: jmp 0x337C598
                    s.pc = 0x337C598;
                    return;
                }
            }

            // 337C430: cmp al,cl
            // 337C432: jae 0x337C47D
            if ((al & 0xFF) >= ((int)s.rcx & 0xFF)) {
                // 337C47D: inc cl
                s.rcx = low8(s.rcx, (int)s.rcx + 1);
                // 337C47F: mov BYTE PTR [rsp+0x34],cl
                s.m.writeByte(s.rsp + 0x34, (int)s.rcx);
                // 337C483: cmp cl,BYTE PTR [rsi+0x18]
                int limit = s.m.readUnsignedByte(s.rsi + 0x18);
                // 337C486: jbe 0x337C420
                if (((int)s.rcx & 0xFF) <= limit) {
                    continue;
                }
                // 337C488: mov ecx,DWORD PTR [rsp+0x30]
                s.rcx = z32(s.m.readDword(s.rsp + 0x30));
                // 337C48C: mov eax,DWORD PTR [r14]
                s.rax = z32(s.m.readDword(s.r14));
                // 337C48F: mov DWORD PTR [rsp+0x30],eax
                s.m.writeDword(s.rsp + 0x30, (int)s.rax);
                // 337C493: mov DWORD PTR [r14],ecx
                s.m.writeDword(s.r14, (int)s.rcx);
                // 337C496: movzx ecx,BYTE PTR [rsp+0x34]
                s.rcx = z32(s.m.readUnsignedByte(s.rsp + 0x34));
                // 337C49B: movzx eax,BYTE PTR [r14+0x4]
                s.rax = z32(s.m.readUnsignedByte(s.r14 + 0x4));
                // 337C4A0: mov BYTE PTR [rsp+0x34],al
                s.m.writeByte(s.rsp + 0x34, (int)s.rax);
                // 337C4A4: mov BYTE PTR [r14+0x4],cl
                s.m.writeByte(s.r14 + 0x4, (int)s.rcx);
                // 337C4A8: mov rcx,QWORD PTR [rsp+0x38]
                s.rcx = s.m.readQword(s.rsp + 0x38);
                // 337C4AD: mov rax,QWORD PTR [r14+0x8]
                s.rax = s.m.readQword(s.r14 + 0x8);
                // 337C4B1: mov QWORD PTR [rsp+0x38],rax
                s.m.writeQword(s.rsp + 0x38, s.rax);
                // 337C4B6: mov QWORD PTR [r14+0x8],rcx
                s.m.writeQword(s.r14 + 0x8, s.rcx);
                // 337C4BA: mov rdx,r13
                s.rdx = s.r13;
                // 337C4BD: lea rcx,[rsp+0x40]
                s.rcx = s.rsp + 0x40;
                // 337C4C2: call 0xa636f0 (direct, length 5)
                s.direct(0x337C4C2, 0xA636F0);
                // 337C4C7: mov rcx,rsi
                s.rcx = s.rsi;
                // 337C4CA: call 0x337c040 (direct, length 5)
                s.direct(0x337C4CA, 0x337C040);
                // 337C4CF: lea r9,[rsp+0x38]
                s.r9 = s.rsp + 0x38;
                // 337C4D4: mov r8d,DWORD PTR [rsp+0x30]
                s.r8 = z32(s.m.readDword(s.rsp + 0x30));
                // 337C4D9: lea rdx,[rbp-0x1]
                s.rdx = s.rbp - 0x1;
                // 337C4DD: mov rcx,rsi
                s.rcx = s.rsi;
                // 337C4E0: call 0x337c5d0 (direct, length 5)
                s.direct(0x337C4E0, 0x337C5D0);
                // 337C4E5: mov rcx,QWORD PTR [rbp-0x51]
                s.rcx = s.m.readQword(s.rbp - 0x51);
                // 337C4E9: test rcx,rcx
                // 337C4EC: je 0x337C4FF
                if (s.rcx == 0) {
                    // 337C4FF: movups xmm0,XMMWORD PTR [rbp-0x1]
                    s.x0 = s.m.read128(s.rbp - 0x1);
                    // 337C503: movups XMMWORD PTR [rdi],xmm0
                    s.m.write128(s.rdi, s.x0);
                    // 337C506: jmp 0x337C598
                    s.pc = 0x337C598;
                    return;
                } else {
                    // 337C4EE: mov rax,QWORD PTR [rcx]
                    s.rax = s.m.readQword(s.rcx);
                    // 337C4F1: lea rdx,[rsp+0x40]
                    s.rdx = s.rsp + 0x40;
                    // 337C4F6: cmp rcx,rdx
                    // 337C4F9: setne dl
                    int dl = (s.rcx != s.rdx) ? 1 : 0;
                    s.rdx = low8(s.rdx, dl);
                    // 337C4FC: call QWORD PTR [rax+0x20] (indirect, length 3)
                    long target = s.m.readQword(s.rax + 0x20);
                    s.indirect(0x337C4FC, target, 3);
                    // 337C4FF: movups xmm0,XMMWORD PTR [rbp-0x1]
                    s.x0 = s.m.read128(s.rbp - 0x1);
                    // 337C503: movups XMMWORD PTR [rdi],xmm0
                    s.m.write128(s.rdi, s.x0);
                    // 337C506: jmp 0x337C598
                    s.pc = 0x337C598;
                    return;
                }
            }

            // 337C434: mov ecx,DWORD PTR [rsp+0x30]
            s.rcx = z32(s.m.readDword(s.rsp + 0x30));
            // 337C438: mov eax,DWORD PTR [rbx]
            s.rax = z32(s.m.readDword(s.rbx));
            // 337C43A: mov DWORD PTR [rsp+0x30],eax
            s.m.writeDword(s.rsp + 0x30, (int)s.rax);
            // 337C43E: mov DWORD PTR [rbx],ecx
            s.m.writeDword(s.rbx, (int)s.rcx);
            // 337C440: movzx ecx,BYTE PTR [rsp+0x34]
            s.rcx = z32(s.m.readUnsignedByte(s.rsp + 0x34));
            // 337C445: movzx eax,BYTE PTR [rbx+0x4]
            s.rax = z32(s.m.readUnsignedByte(s.rbx + 0x4));
            // 337C449: mov BYTE PTR [rsp+0x34],al
            s.m.writeByte(s.rsp + 0x34, (int)s.rax);
            // 337C44D: mov BYTE PTR [rbx+0x4],cl
            s.m.writeByte(s.rbx + 0x4, (int)s.rcx);
            // 337C450: mov rcx,QWORD PTR [rsp+0x38]
            s.rcx = s.m.readQword(s.rsp + 0x38);
            // 337C455: mov rax,QWORD PTR [rbx+0x8]
            s.rax = s.m.readQword(s.rbx + 0x8);
            // 337C459: mov QWORD PTR [rsp+0x38],rax
            s.m.writeQword(s.rsp + 0x38, s.rax);
            // 337C45E: mov QWORD PTR [rbx+0x8],rcx
            s.m.writeQword(s.rbx + 0x8, s.rcx);
            // 337C462: lea rdx,[rbx+0x10]
            s.rdx = s.rbx + 0x10;
            // 337C466: lea rcx,[rsp+0x40]
            s.rcx = s.rsp + 0x40;
            // 337C46B: call 0xa636f0 (direct, length 5)
            s.direct(0x337C46B, 0xA636F0);
            // 337C470: movzx ecx,BYTE PTR [rsp+0x34]
            s.rcx = z32(s.m.readUnsignedByte(s.rsp + 0x34));
            // 337C475: inc cl
            s.rcx = low8(s.rcx, (int)s.rcx + 1);
            // 337C477: mov BYTE PTR [rsp+0x34],cl
            s.m.writeByte(s.rsp + 0x34, (int)s.rcx);
            // 337C47B: jmp 0x337C420
            // Loop back
        }
    }
}