package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.z32;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c200207.low8;

final class LoadRowReferenceCallee337c200207Growth {
    private LoadRowReferenceCallee337c200207Growth() { }

    static GovernmentCrtBoundary185Api.NormalReturn run(LoadRowReferenceCallee337c200207.State s) {
        if (s.pc == 0x337C555) {
            // 337c555: inc ecx
            s.rcx = z32((int)s.rcx + 1);
            // 337c557: mov edx, 1
            s.rdx = 1;
            // 337c55c: call 0x86e160 (direct, length 5)
            s.direct(0x337C55C, 0x86E160);
            // 337c561: cmp eax, 0x1f
            int eax = (int)s.rax;
            boolean jge = eax >= 0x1F;
            // 337c564: jge 0x337c5b6
            if (jge) {
                s.pc = 0x337C5B6;
            } else {
                // 337c566: mov edx, eax
                s.rdx = z32(eax);
                // 337c568: mov rcx, rsi
                s.rcx = s.rsi;
                // 337c56b: call 0x337c0c0 (direct, length 5)
                s.direct(0x337C56B, 0x337C0C0);
                // 337c570: mov BYTE PTR [rbp+0x57], 0
                s.m.writeByte(s.rbp + 0x57, 0);
                // 337c574: mov rax, QWORD PTR [rbp+0x7f]
                s.rax = s.m.readQword(s.rbp + 0x7F);
                // 337c578: mov QWORD PTR [rsp+0x28], rax
                s.m.writeQword(s.rsp + 0x28, s.rax);
                // 337c57d: lea rax, [rbp+0x57]
                s.rax = s.rbp + 0x57;
                // 337c581: mov QWORD PTR [rsp+0x20], rax
                s.m.writeQword(s.rsp + 0x20, s.rax);
                // 337c586: mov r9, r12
                s.r9 = s.r12;
                // 337c589: mov r8d, DWORD PTR [rbp+0x67]
                s.r8 = z32(s.m.readDword(s.rbp + 0x67));
                // 337c58d: mov rdx, rdi
                s.rdx = s.rdi;
                // 337c590: mov rcx, rsi
                s.rcx = s.rsi;
                // 337c593: call 0x337c200 (direct, length 5) - SELF
                s.direct(0x337C593, 0x337C200);
                // Fall through to 337c598
                s.pc = 0x337C598;
            }
        }

        if (s.pc == 0x337C5B6) {
            // 337c5b6: mov rdx, rsi
            s.rdx = s.rsi;
            // 337c5b9: lea rcx, [rbp+0x57]
            s.rcx = s.rbp + 0x57;
            // 337c5bd: call 0x86f210 (direct, length 5)
            s.direct(0x337C5BD, 0x86F210);
            // 337c5c2: call 0x4232cf4 (direct, length 5)
            s.direct(0x337C5C2, 0x4232CF4);
            // 337c5c7: int3
            throw new UnsupportedOperationException("INT3 reached");
        }

        // Domain 337C598: Normal Return Path
        if (s.pc == 0x337C598) {
            // 337c598: mov rax, rdi
            s.rax = s.rdi;
            // 337c59b: mov rbx, QWORD PTR [rsp+0x128]
            s.rbx = s.m.readQword(s.rsp + 0x128);
            // 337c5a3: add rsp, 0xe0
            s.rsp += 0xE0;
            // 337c5aa: pop r15
            s.r15 = s.pop();
            // 337c5ac: pop r14
            s.r14 = s.pop();
            // 337c5ae: pop r13
            s.r13 = s.pop();
            // 337c5b0: pop r12
            s.r12 = s.pop();
            // 337c5b2: pop rdi
            s.rdi = s.pop();
            // 337c5b3: pop rsi
            s.rsi = s.pop();
            // 337c5b4: pop rbp
            s.rbp = s.pop();
            // 337c5b5: ret
            return s.ret();
        }

        throw new IllegalStateException("Unexpected PC in Growth: " + Integer.toHexString(s.pc));
    }
}