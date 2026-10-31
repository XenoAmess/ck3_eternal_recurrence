package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower88;

public final class Lower88Candidate {
    private Lower88Candidate() { }

    public static void execute(Lower88Inputs.CallInput input, Lower88Inputs.Memory memory, Lower88Inputs.Calls calls) {
        long rbx = input.arrayRaw();
        long rdx = input.countRaw();
        long rax = rbx + rdx * 8;
        long rsi = rdx & 0x1fffffffffffffffL;
        long rdi = 0;
        long rcx;

        if (Long.compareUnsigned(rbx, rax) > 0) {
            rsi = 0;
        }

        if (rsi == 0) return;

        while (true) {
            rcx = memory.readPointer(rbx);
            calls.call424E364(rcx);
            rdi = rdi + 1;
            rbx = rbx + 8;
            if (Long.compareUnsigned(rdi, rsi) == 0) break;
        }
    }
}
