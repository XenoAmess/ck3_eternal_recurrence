package org.xar.ck3.study.m6.range8c194;

import org.xar.ck3.study.m6.element172.Element172Inputs;

public final class Range8c194Candidate {
    private Range8c194Candidate() { }

    public static void apply(Range8c194Inputs.Input input, Range8c194Inputs.Memory memory, Range8c194Inputs.Calls calls) {
        long rdi = input.destinationHeaderRaw64();
        long rdx = input.rdxRaw64();
        long r8 = input.beginRaw64();
        long r9 = input.endRaw64();

        if (r8 == r9) {
            return;
        }

        long rax = (long) memory.read32(rdi + 0x0C);
        long rbx = r8;
        int ecx = memory.read32(rdi + 0x08);
        long rbp = r9 - rbx;
        rbp = rbp >> 4;
        long rsi = r9;
        long r14 = (long) (int) rdx;
        int r15d = (int) (rax + rbp);

        if (r15d <= ecx) {
            rax = rax << 4;
            rax = rax + memory.read64(rdi);

            while (rbx != rsi) {
                Range8c194Inputs.Word16 word = memory.read16(rbx);
                rbx = rbx + 0x10;
                rax = rax + 0x10;
                memory.write16(rax - 0x10, word);
            }

            long rcx_val = (long) memory.read32(rdi + 0x0C);
            long r9_local = memory.read64(rdi);
            long rdx_local = rcx_val << 4;
            rdx_local = rdx_local + r9_local;

            // 008C7225: lea eax, [rcx + rbp] -> register sum/truncate, NOT memory read
            int eax = (int) (rcx_val + rbp);

            rcx_val = r14;
            long r8_local = (long) eax;
            r8_local = r8_local << 4;
            r8_local = r8_local + r9_local;

            rcx_val = rcx_val << 4;
            rcx_val = rcx_val + r9_local;

            memory.write32(rdi + 0x0C, eax);
            calls.direct8f8550(rcx_val, rdx_local, r8_local, r9_local);
            return;
        }

        float xmm0 = (float) ecx;
        r8 = 8L;
        long rcx = memory.read64(rdi + 0x10);
        int r13d = r15d;

        xmm0 = xmm0 * 1.5f;

        int eax;
        if (Float.isNaN(xmm0) || xmm0 >= 2147483648.0f || xmm0 < -2147483648.0f) {
            eax = Integer.MIN_VALUE;
        } else {
            eax = (int) xmm0;
        }

        if (r15d < eax) {
            r13d = eax;
        }

        rax = memory.read64(rcx);
        // 008C712A: mov edx, r13d (zero-extend 32 to 64)
        // 008C712D: shl rdx, 4
        long rdx_alloc = ((long) r13d & 0xFFFFFFFFL) << 4;

        // 008C7131: call qword ptr [rax + 8]
        // Target is the function pointer value at [rax+8], not the address rax+8
        long target8 = memory.read64(rax + 8);
        long newBase = calls.virtual8(target8, rcx, rdx_alloc, 8L, r9);

        rcx = memory.read64(rdi);
        long r10 = r14 << 4;
        long r12 = newBase;
        long rdx_copy = newBase;
        r8 = r10 + rcx;

        if (rcx != r8) {
            while (rcx != r8) {
                Range8c194Inputs.Word16 word = memory.read16(rcx);
                rcx = rcx + 0x10;
                rdx_copy = rdx_copy + 0x10;
                memory.write16(rdx_copy - 0x10, word);
            }
        }

        rcx = r10;
        rcx = rcx - rbx;
        rcx = rcx + r12;

        while (rbx != rsi) {
            Range8c194Inputs.Word16 word = memory.read16(rbx);
            memory.write16(rcx + rbx, word);
            rbx = rbx + 0x10;
        }

        long r9_release = memory.read64(rdi);
        long rdx_release = (long) memory.read32(rdi + 0x0C);
        rdx_release = rdx_release << 4;
        rdx_release = rdx_release + r9_release;

        // 008C718B: movsxd rcx, ebp -> signed low32 of rbp
        long rcx_release = (long) (int) rbp;
        rcx_release = rcx_release + r14;

        rax = r10 + r9_release;
        rcx_release = rcx_release << 4;
        rcx_release = rcx_release + r12;

        if (rax != rdx_release) {
            while (rax != rdx_release) {
                Range8c194Inputs.Word16 word = memory.read16(rax);
                rax = rax + 0x10;
                rcx_release = rcx_release + 0x10;
                memory.write16(rcx_release - 0x10, word);
            }

            // 008C71C4: mov r9, qword ptr [rdi] occurs only after loop
            r9_release = memory.read64(rdi);
        }

        rcx = memory.read64(rdi + 0x10);
        r8 = 8L;
        rdx_release = r9_release;
        rax = memory.read64(rcx);

        // 008C71D7: call qword ptr [rax + 0x10]
        long target16 = memory.read64(rax + 0x10);
        calls.virtual16(target16, rcx, rdx_release, 8L, r9_release);

        memory.write64(rdi, r12);
        memory.write32(rdi + 0x08, r13d);
        memory.write32(rdi + 0x0C, r15d);
    }
}