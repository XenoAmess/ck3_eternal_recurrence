package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Model implementation of the scalar tail, entered at the comparison at 4220B60.
 * Executes the 4220B49 loop body as needed and the remaining epilogue through 4220B66.
 * Does not execute prologue, earlier blocks, or implement old algorithms.
 */
public final class ReverseScalarTail641 {
    private ReverseScalarTail641() { }

    /**
     * Completes the tail block using current registers, memory, budget, DF, and MXCSR.
     * @param r Current registers (must reflect state entering the tail block).
     * @param memory Owned memory view.
     * @param budget Loop budget for the tail block.
     * @param df Current direction flag.
     * @param fp Current MXCSR state (preserved as-is).
     * @return Normal outcome with post-state.
     */
    public static QueueFp604Api.Normal finish(Registers r, GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget, boolean df, QueueFp604Api.Mxcsr fp) {
        Objects.requireNonNull(r);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(fp);

        // 4220B49: sub rdx, 4
        // 4220B4D: cmp r8, rdx
        // 4220B50: je 0x4220B65 (RET)
        // 4220B52: mov ecx, dword ptr [r8]
        // 4220B55: mov eax, dword ptr [rdx]
        // 4220B57: mov dword ptr [r8], eax
        // 4220B5A: add r8, 4
        // 4220B5E: mov dword ptr [rdx], ecx
        // 4220B60: cmp r8, rdx
        // 4220B63: jne 0x4220B49
        // 4220B65: ret

        while (r.r8 != r.rdx) {
            budget.beforeStep(0x4220B49L, r.r8);
            r.rdx -= 4;
            if (r.r8 == r.rdx) break;
            r.rcx = Integer.toUnsignedLong(memory.readDword(r.r8));
            r.rax = Integer.toUnsignedLong(memory.readDword(r.rdx));
            memory.writeDword(r.r8, (int)r.rax);
            r.r8 += 4;
            memory.writeDword(r.rdx, (int)r.rcx);
        }

        // 4220B65: ret
        long rip = memory.readQword(r.rsp);
        r.rsp += 8;

        // Construct Normal outcome
        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),
            rip,
            r.rsp,
            r.nonvolatileBits()
        );
        FullCopy437Api.CallResult base = new FullCopy437Api.CallResult(nr, df);
        return new QueueFp604Api.Normal(base, fp);
    }
}