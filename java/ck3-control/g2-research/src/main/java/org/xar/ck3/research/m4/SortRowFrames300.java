package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

public final class SortRowFrames300 {
    private SortRowFrames300() { }

    /**
     * Captures the row data from the source pointer (RBX) into XMM registers and stack slots.
     * Translates instructions 0x1A817F0..0x1A8180D.
     *
     * 0x1A817F0: movups xmm2, xmmword ptr [rbx] -> read 128 bits from r.rbx into r.x2
     * 0x1A817F3: mov rcx, rbx -> r.rcx = r.rbx
     * 0x1A817F6: movups xmm3, xmmword ptr [rbx + 0x10] -> read 128 bits from r.rbx+0x10 into r.x3
     * 0x1A817FA: movsd xmm4, qword ptr [rbx + 0x20] -> read 64 bits from r.rbx+0x20 into r.x4 (low 64 bits)
     * 0x1A817FF: movd edx, xmm2 -> extract low 32 bits of r.x2 into r.rdx (zero-extended to 64)
     * 0x1A81803: movups xmmword ptr [rsp + 0x30], xmm2 -> write r.x2 to stack at r.rsp+0x30
     * 0x1A81808: movups xmmword ptr [rsp + 0x40], xmm3 -> write r.x3 to stack at r.rsp+0x40
     * 0x1A8180D: movsd qword ptr [rsp + 0x80], xmm4 -> write low 64 bits of r.x4 to stack at r.rsp+0x80
     */
    public static void capture(Registers r, GovernmentCrtBoundary185Api.Memory memory) {
        // 0x1A817F0: movups xmm2, xmmword ptr [rbx]
        r.x2 = memory.read128(r.rbx);

        // 0x1A817F3: mov rcx, rbx
        r.rcx = r.rbx;

        // 0x1A817F6: movups xmm3, xmmword ptr [rbx + 0x10]
        r.x3 = memory.read128(r.rbx + 0x10L);

        // 0x1A817FA: movsd xmm4, qword ptr [rbx + 0x20]
        // MOVSD loads a 64-bit value into the low 64 bits of the XMM register, high 64 bits are zeroed.
        long qword4 = memory.readQword(r.rbx + 0x20L);
        r.x4 = new Bits128(qword4, 0L);

        // 0x1A817FF: movd edx, xmm2
        // Extracts the low 32 bits of xmm2 into EDX. EDX is zero-extended to RDX.
        int edxVal = (int) r.x2.lowBits();
        r.rdx = Integer.toUnsignedLong(edxVal);

        // 0x1A81803: movups xmmword ptr [rsp + 0x30], xmm2
        memory.write128(r.rsp + 0x30L, r.x2);

        // 0x1A81808: movups xmmword ptr [rsp + 0x40], xmm3
        memory.write128(r.rsp + 0x40L, r.x3);

        // 0x1A8180D: movsd qword ptr [rsp + 0x80], xmm4
        // Writes the low 64 bits of xmm4 to the stack.
        memory.writeQword(r.rsp + 0x80L, r.x4.lowBits());
    }

    /**
     * Restores the row data from stack slots back into XMM registers and writes to the destination pointer (RDI).
     * Translates instructions 0x1A8182F..0x1A81849.
     *
     * 0x1A8182F: movups xmm0, xmmword ptr [rsp + 0x30] -> read 128 bits from r.rsp+0x30 into r.x0
     * 0x1A81834: movups xmm1, xmmword ptr [rsp + 0x40] -> read 128 bits from r.rsp+0x40 into r.x1
     * 0x1A81839: movups xmmword ptr [rdi], xmm0 -> write r.x0 to stack/memory at r.rdi
     * 0x1A8183C: movsd xmm0, qword ptr [rsp + 0x80] -> read 64 bits from r.rsp+0x80 into r.x0 (low 64 bits)
     * 0x1A81845: movups xmmword ptr [rdi + 0x10], xmm1 -> write r.x1 to memory at r.rdi+0x10
     * 0x1A81849: movsd qword ptr [rdi + 0x20], xmm0 -> write low 64 bits of r.x0 to memory at r.rdi+0x20
     */
    public static void restoreFront(Registers r, GovernmentCrtBoundary185Api.Memory memory) {
        // 0x1A8182F: movups xmm0, xmmword ptr [rsp + 0x30]
        r.x0 = memory.read128(r.rsp + 0x30L);

        // 0x1A81834: movups xmm1, xmmword ptr [rsp + 0x40]
        r.x1 = memory.read128(r.rsp + 0x40L);

        // 0x1A81839: movups xmmword ptr [rdi], xmm0
        memory.write128(r.rdi, r.x0);

        // 0x1A8183C: movsd xmm0, qword ptr [rsp + 0x80]
        // MOVSD loads a 64-bit value into the low 64 bits of the XMM register, high 64 bits are zeroed.
        long qword0 = memory.readQword(r.rsp + 0x80L);
        r.x0 = new Bits128(qword0, 0L);

        // 0x1A81845: movups xmmword ptr [rdi + 0x10], xmm1
        memory.write128(r.rdi + 0x10L, r.x1);

        // 0x1A81849: movsd qword ptr [rdi + 0x20], xmm0
        // Writes the low 64 bits of xmm0 to the memory.
        memory.writeQword(r.rdi + 0x20L, r.x0.lowBits());
    }
}