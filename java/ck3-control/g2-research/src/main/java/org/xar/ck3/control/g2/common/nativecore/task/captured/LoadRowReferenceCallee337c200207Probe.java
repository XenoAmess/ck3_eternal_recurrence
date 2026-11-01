package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.z32;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.low8;

final class LoadRowReferenceCallee337c200207Probe {
    private LoadRowReferenceCallee337c200207Probe() { }

    static void run(LoadRowReferenceCallee337c200207.State s) {
        // Prologue: [337C200, 337C292) plus matched [337C2DF, 337C2EB)
        // 337C200: mov QWORD PTR [rsp+0x10],rbx
        s.m.writeQword(s.rsp + 0x10, s.rbx);
        // 337C205: mov DWORD PTR [rsp+0x18],r8d
        s.m.writeDword(s.rsp + 0x18, (int)s.r8);
        // 337C20A: push rbp
        s.push(s.rbp);
        // 337C20B: push rsi
        s.push(s.rsi);
        // 337C20C: push rdi
        s.push(s.rdi);
        // 337C20D: push r12
        s.push(s.r12);
        // 337C20F: push r13
        s.push(s.r13);
        // 337C211: push r14
        s.push(s.r14);
        // 337C213: push r15
        s.push(s.r15);
        // 337C215: lea rbp,[rsp-0x17]
        s.rbp = s.rsp - 0x17;
        // 337C21A: sub rsp,0xe0
        s.rsp -= 0xE0;
        // 337C221: mov r12,r9
        s.r12 = s.r9;
        // 337C224: mov rdi,rdx
        s.rdi = s.rdx;
        // 337C227: mov rsi,rcx
        s.rsi = s.rcx;
        // 337C22A: mov ecx,DWORD PTR [rcx+0x14]
        s.rcx = z32(s.m.readDword(s.rcx + 0x14));
        // 337C22D: mov eax,ecx
        s.rax = s.rcx;
        // 337C22F: and eax,r8d
        s.rax = s.rax & s.r8;
        // 337C232: cdqe
        s.rax = (long)(int)s.rax;
        // 337C234: lea rbx,[rax+rax*4]
        s.rbx = s.rax + s.rax * 4;
        // 337C238: shl rbx,0x4
        s.rbx <<= 4;
        // 337C23C: add rbx,QWORD PTR [rsi+0x8]
        s.rbx += s.m.readQword(s.rsi + 0x8);
        // 337C240: mov r14b,0x1
        s.r14 = low8(s.r14, 1);
        // 337C243: cmp BYTE PTR [rbx+0x4],r14b
        int cmpVal = s.m.readUnsignedByte(s.rbx + 0x4);
        int r14b = (int)(s.r14 & 0xFF);
        // 337C247: jb 0x337c267
        if (cmpVal < r14b) {
            s.pc = 0x337C267;
        } else {
            // 337C249: mov rax,QWORD PTR [r9]
            s.rax = s.m.readQword(s.r9);
            // Lookup loop: 337C250..337C265
            while (true) {
                // 337C250: cmp rax,QWORD PTR [rbx+0x8]
                s.budget.beforeStep(0x337C250, s.rbx);
                long keyVal = s.m.readQword(s.rbx + 0x8);
                // 337C254: je 0x337c2df
                if (s.rax == keyVal) {
                    s.pc = 0x337C2DF;
                    break;
                }
                // 337C25A: inc r14b
                s.r14 = low8(s.r14, (int)(s.r14 & 0xFF) + 1);
                // 337C25D: add rbx,0x50
                s.rbx += 0x50;
                // 337C261: cmp r14b,BYTE PTR [rbx+0x4]
                int r14b2 = (int)(s.r14 & 0xFF);
                int cmpVal2 = s.m.readUnsignedByte(s.rbx + 0x4);
                // 337C265: jbe 0x337c250
                if (r14b2 <= cmpVal2) {
                    continue;
                } else {
                    s.pc = 0x337C267;
                    break;
                }
            }
        }

        // Handle matched [337C2DF, 337C2EB) if pc is 337C2DF
        if (s.pc == 0x337C2DF) {
            // 337C2DF: mov QWORD PTR [rdx],rbx
            s.m.writeQword(s.rdx, s.rbx);
            // 337C2E2: mov BYTE PTR [rdx+0x8],0x0
            s.m.writeByte(s.rdx + 0x8, 0);
            // 337C2E6: jmp 0x337c598
            s.pc = 0x337C598;
            return;
        }

        // 337C267: cmp r14b,BYTE PTR [rsi+0x18]
        int r14b3 = (int)(s.r14 & 0xFF);
        int cmpVal3 = s.m.readUnsignedByte(s.rsi + 0x18);
        // 337C26B: ja 0x337c555
        if (r14b3 > cmpVal3) {
            s.pc = 0x337C555;
            return;
        }

        // 337C271: mov eax,DWORD PTR [rsi+0x10]
        s.rax = z32(s.m.readDword(s.rsi + 0x10));
        // 337C274: inc eax
        s.rax = z32((int)s.rax + 1);
        // 337C276: movd xmm1,eax
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(z32((int)s.rax), 0);
        // 337C27A: cvtdq2ps xmm1,xmm1
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(z32(s.floating.convertSignedDwordToFloatBits((int)s.rax)), 0);
        // 337C27D: movd xmm0,ecx
        s.x0 = new GovernmentPrimaryTail155Api.Bits128(z32((int)s.rcx), 0);
        // 337C281: cvtdq2ps xmm0,xmm0
        s.x0 = new GovernmentPrimaryTail155Api.Bits128(z32(s.floating.convertSignedDwordToFloatBits((int)s.rcx)), 0);
        // 337C284: divss xmm1,xmm0
        int divResult = s.floating.divideScalarFloatBits((int)s.x1.lowBits(), (int)s.x0.lowBits());
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(z32(divResult), s.x1.highBits());
        // 337C288: comiss xmm1,DWORD PTR [rsi+0x1c]
        int threshold = s.m.readDword(s.rsi + 0x1C);
        // 337C28C: ja 0x337c555
        if (s.floating.orderedAbove((int)s.x1.lowBits(), threshold)) {
            s.pc = 0x337C555;
            return;
        }

        // Stop before 337C292
        s.pc = 0x337C292;
    }
}
