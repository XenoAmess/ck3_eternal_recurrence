package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/**
 * Model implementation of actual small-block [8C71F1, 8C723F) before DIRECT CALL.
 * Implements ONLY the source instructions in this range. Does not execute prologue, calls, or FP.
 */
public final class Range16NoGrowth638 {
    private Range16NoGrowth638() { }

    public static void copyAndPrepare(Registers r, Range16Fp638Api.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(r);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);

        // 8C71F1: shl rax, 4
        r.rax <<= 4;

        // 8C71F5: add rax, qword ptr [rdi]
        r.rax += memory.readQword(r.rdi);

        // 8C71F8: nop dword ptr [rax + rax] (no effect)

        // 8C7200: movups xmm0, xmmword ptr [rbx]
        // 8C7203: add rbx, 0x10
        // 8C7207: lea rax, [rax + 0x10]
        // 8C720B: movups xmmword ptr [rax - 0x10], xmm0
        // 8C720F: cmp rbx, rsi
        // 8C7212: jne 0x8C7200
        while (true) {
            budget.beforeStep(0x8C7200L, r.rbx);
            r.x0 = memory.read128(r.rbx);
            r.rbx += 0x10;
            r.rax += 0x10;
            memory.write128(r.rax - 0x10, r.x0);
            if (r.rbx == r.rsi) break;
        }

        // 8C7214: movsxd rcx, dword ptr [rdi + 0xc]
        r.rcx = (long)memory.readDword(r.rdi + 0x0C);

        // 8C7218: mov r9, qword ptr [rdi]
        r.r9 = memory.readQword(r.rdi);

        // 8C721B: mov rdx, rcx
        r.rdx = r.rcx;

        // 8C721E: shl rdx, 4
        r.rdx <<= 4;

        // 8C7222: add rdx, r9
        r.rdx += r.r9;

        // 8C7225: lea eax, [rcx + rbp]
        r.rax = Integer.toUnsignedLong((int)(r.rcx + r.rbp));

        // 8C7228: mov rcx, r14
        r.rcx = r.r14;

        // 8C722B: movsxd r8, eax
        r.r8 = (long)(int)r.rax;

        // 8C722E: shl r8, 4
        r.r8 <<= 4;

        // 8C7232: shl rcx, 4
        r.rcx <<= 4;

        // 8C7236: add r8, r9
        r.r8 += r.r9;

        // 8C7239: add rcx, r9
        r.rcx += r.r9;

        // 8C723C: mov dword ptr [rdi + 0xc], eax
        memory.writeDword(r.rdi + 0x0C, (int)r.rax);
    }
}