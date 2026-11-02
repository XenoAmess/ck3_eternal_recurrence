package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Memory;

/**
 * Implements the exact source interval [0x8803A2, 0x8803B8) from the complete 227-byte function at RVA 0x880340.
 * This segment handles the post-allocation fresh count check and potential copy setup.
 * Entry state assumes the allocator call has returned, with RAX holding the new buffer address.
 */
public final class QueueAppendGrowthStore598 {
    private QueueAppendGrowthStore598() { }

    /**
     * Executes the loads and register updates for the specified interval.
     * @param r The current register state (RAX=newbuffer, RBX=container, R14=elementPointer).
     * @param memory The owned memory view.
     * @return true if the fresh count (EAX) is > 0 (fallthrough to 0x8803B8), false if <= 0 (JLE to 0x8803CA).
     */
    public static boolean prepare(Registers r, Memory memory) {
        // 0x8803A2: movsxd rdx, DWORD PTR [rbx+0xc]
        // Read fresh count from container+0xC as signed 32-bit, sign-extend to 64-bit RDX.
        int freshCountBits = memory.readDword(r.rbx + 0xC);
        r.rdx = (long)freshCountBits;

        // 0x8803A6: mov rdi, rax
        // RDI becomes the new buffer address (currently in RAX).
        r.rdi = r.rax;

        // 0x8803A9: mov rcx, QWORD PTR [r14]
        // RCX becomes the element value pointed to by R14 (elementPointer).
        r.rcx = memory.readQword(r.r14);

        // 0x8803AC: mov QWORD PTR [rax+rdx*8], rcx
        // Store the element value (RCX) into the new buffer (RAX) at index RDX.
        // Note: RDX was set to the fresh count read above.
        long destAddress = r.rax + (r.rdx << 3);
        memory.writeQword(destAddress, r.rcx);

        // 0x8803B0: movsxd rax, DWORD PTR [rbx+0xc]
        // Re-read fresh count from container+0xC into RAX (signed 32-bit to 64-bit).
        // This overwrites the previous RAX (newbuffer) value.
        int freshCountBits2 = memory.readDword(r.rbx + 0xC);
        r.rax = (long)freshCountBits2;

        // 0x8803B4: test eax, eax
        // Check if the new RAX (fresh count) is zero. Sets ZF if zero.
        // In Java, we evaluate the condition for the subsequent branch.

        // 0x8803B6: jle 0x8803CA
        // Jump if Less or Equal (signed comparison of EAX vs 0).
        // If EAX <= 0, jump to 0x8803CA (skip copy).
        // If EAX > 0, fall through to 0x8803B8 (setup copy).

        // The return value indicates whether we fall through to the copy setup (true) or jump to skip (false).
        // JLE means jump if signed value <= 0. So fallthrough is if signed value > 0.
        return freshCountBits2 > 0;
    }
}