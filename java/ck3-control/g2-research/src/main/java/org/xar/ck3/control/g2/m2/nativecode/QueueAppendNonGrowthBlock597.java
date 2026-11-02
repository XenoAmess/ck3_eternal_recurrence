package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Memory;

/**
 * Implements the non-growth path block [8803ED, 880403) of the 227-byte function.
 * This corresponds to the JNE branch taken when count != capacity.
 *
 * Instructions:
 * 1. MOV RCX, QWORD PTR [RBX]       -> r.rcx = memory.readQword(r.rbx)
 * 2. MOV RDX, RAX                  -> r.rdx = r.rax
 * 3. MOV RAX, QWORD PTR [R14]      -> r.rax = memory.readQword(r.r14)
 * 4. MOV QWORD PTR [RCX+RDX*8], RAX -> memory.writeQword(r.rcx + (r.rdx << 3), r.rax)
 * 5. INC DWORD PTR [RBX+0xC]       -> Fresh read/write of count with int wrap
 * 6. MOV ESI, DWORD PTR [RBX+0xC]  -> Fresh read of count, zero-extended to RSI
 * 7. MOV RDI, QWORD PTR [RBX]      -> Fresh read of base to RDI
 */
public final class QueueAppendNonGrowthBlock597 {
    private QueueAppendNonGrowthBlock597() { }

    public static void append(Registers r, Memory memory) {
        // 1. MOV RCX, QWORD PTR [RBX]
        // Read container base address into RCX
        r.rcx = memory.readQword(r.rbx);

        // 2. MOV RDX, RAX
        // Copy current RAX (signed-extended count) to RDX
        r.rdx = r.rax;

        // 3. MOV RAX, QWORD PTR [R14]
        // Read element value from element pointer (R14) into RAX
        r.rax = memory.readQword(r.r14);

        // 4. MOV QWORD PTR [RCX+RDX*8], RAX
        // Write element value to base + count * 8
        // RDX holds the count (as a long, originally from signed int extension)
        // Address calculation: RCX + (RDX * 8)
        long writeAddress = r.rcx + (r.rdx << 3);
        memory.writeQword(writeAddress, r.rax);

        // 5. INC DWORD PTR [RBX+0xC]
        // Increment the count at container + 0xC
        // Fresh read of the DWORD count
        long countAddr = r.rbx + 0xC;
        int currentCount = memory.readDword(countAddr);
        // Increment with int wrap (Java int addition wraps naturally)
        int newCount = currentCount + 1;
        // Fresh write of the incremented count
        memory.writeDword(countAddr, newCount);

        // 6. MOV ESI, DWORD PTR [RBX+0xC]
        // Fresh read of the count again (post-increment)
        int freshCount = memory.readDword(countAddr);
        // Zero-extend to RSI (64-bit)
        r.rsi = Integer.toUnsignedLong(freshCount);

        // 7. MOV RDI, QWORD PTR [RBX]
        // Fresh read of the container base into RDI
        r.rdi = memory.readQword(r.rbx);
    }
}