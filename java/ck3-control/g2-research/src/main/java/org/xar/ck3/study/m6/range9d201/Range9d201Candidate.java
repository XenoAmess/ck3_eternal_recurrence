package org.xar.ck3.study.m6.range9d201;

public final class Range9d201Candidate {
    public static long apply(Range9d201Inputs.Input input, Range9d201Inputs.Calls calls) {
        long rcx = input.beginRaw64();
        long rdx = input.middleRaw64();
        long r8 = input.endRaw64();
        long r9 = input.entryR9Raw64();

        // Save begin/middle/end across calls (rbx=r8, rsi=rdx, rdi=rcx)
        long rbx = r8;
        long rsi = rdx;
        long rdi = rcx;

        // cmp rcx, rdx; jne 0x9D0980
        if (rcx != rdx) {
            // cmp rsi, rbx; jne 0x9D0998
            if (rsi != rbx) {
                // First CALL: four fully source-qualified original argument register values
                calls.first4220aa4(rcx, rdx, r8, r9);
                // mov rdx, rbx; mov rcx, rsi
                rdx = rbx;
                rcx = rsi;
                // Second CALL: only RCX/RDX qualified
                calls.later4220aa4(rcx, rdx);
                // mov rdx, rbx; mov rcx, rdi
                rdx = rbx;
                rcx = rdi;
                // Third CALL: only RCX/RDX qualified
                calls.later4220aa4(rcx, rdx);
                // sub rbx, rsi
                rbx = rbx - rsi;
                // sar rbx, 2
                rbx = rbx >> 2;
                // lea rax, [rdi + rbx*4]
                return rdi + (rbx << 2);
            } else {
                // mov rax, rdi
                return rdi;
            }
        } else {
            // mov rax, rbx
            return rbx;
        }
    }
}