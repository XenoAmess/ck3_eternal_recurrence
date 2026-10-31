package org.xar.ck3.study.m6.block8f198;

import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;

public final class BlockRange8f198Candidate {
    private BlockRange8f198Candidate() { }

    public static long apply(BlockRange8f198Inputs.Input input, Range8c194Inputs.Memory memory) {
        long rcx = input.beginRaw64();
        long rdx = input.middleRaw64();
        long r8 = input.endRaw64();
        long r9 = rcx;
        if (rcx == rdx) return r8;
        if (rdx == r8) return r9;

        long rax = rdx;
        do {
            rax -= 16;
            if (rcx == rax) break;
            Range8c194Inputs.Word16 first = memory.read16(rcx);
            Range8c194Inputs.Word16 last = memory.read16(rax);
            memory.write16(rcx, last);
            rcx += 16;
            memory.write16(rax, first);
        } while (rcx != rax);

        rcx = rdx;
        rax = r8;
        do {
            rax -= 16;
            if (rcx == rax) break;
            Range8c194Inputs.Word16 first = memory.read16(rcx);
            Range8c194Inputs.Word16 last = memory.read16(rax);
            memory.write16(rcx, last);
            rcx += 16;
            memory.write16(rax, first);
        } while (rcx != rax);

        rcx = r9;
        rax = r8;
        if (r9 != r8) {
            do {
                rax -= 16;
                if (rcx == rax) break;
                Range8c194Inputs.Word16 first = memory.read16(rcx);
                Range8c194Inputs.Word16 last = memory.read16(rax);
                memory.write16(rcx, last);
                rcx += 16;
                memory.write16(rax, first);
            } while (rcx != rax);
        }
        return r9 + ((r8 - rdx) & -16L);
    }
}
