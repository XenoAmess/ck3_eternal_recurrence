package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner block container: initial CMP/branch, remaining scan/AL and RET belong to owner. */
final class EmbeddedClassifyFirstVector594 {
    private EmbeddedClassifyFirstVector594() { }
    static boolean firstVectorNonnegative(Registers r, FullCopy437Api.Memory memory) {
        // Source 3727586: movsxd rdx, DWORD PTR [rcx+0x1c]
        // Fresh signed read of the count. Java int is signed 32-bit; assigning to long preserves sign.
        r.rdx = memory.readDword(r.rcx + 0x1CL);

        // Source 372758a: mov rax, QWORD PTR [rcx+0x10]
        r.rax = memory.readQword(r.rcx + 0x10L);

        // Source 372758e: shl rdx, 0x5
        // Shift left by 5 (multiply by 32). In Java, long << 5 wraps modulo 2^64.
        r.rdx <<= 5;

        // Source 3727592: cmp DWORD PTR [rdx+rax*1-0x14], 0xffffffff
        // Calculate address: rdx + rax - 0x14
        long addr = r.rdx + r.rax - 0x14L;

        // Read DWORD at calculated address.
        // The comparison is against 0xffffffff (which is -1 in signed 32-bit).
        // The instruction is 'cmp ... 0xffffffff'.
        // The subsequent jump is 'jg 0x37275ce' (jump if greater).
        // 'jg' checks if the first operand (the value at address) is greater than the second operand (-1).
        // So we return true if the signed int value at addr is > -1 (i.e., >= 0).
        int val = memory.readDword(addr);

        return val > -1;
    }
}
