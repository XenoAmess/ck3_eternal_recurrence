package org.xar.ck3.research.m3.word226;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/**
 * Exact-width address operations for supplied storage; no process attachment.
 * This interface defines the contract for the 44-byte NORMAL44 body at 0x4246a60.
 */
public interface WordCompare226Api {

    /**
     * Minimal nested strong Memory with one exact unsigned 16-bit read operation.
     * This satisfies the requirement that exact 16-bit reads cannot be implemented by 32/64-bit read+mask.
     */
    interface Memory extends NativeTaskMemory {
        /** Read a single unsigned 16-bit word at the given address. */
        int readWord16(long address);
    }

    /**
     * Result of the source-derived DATA request.
     * Contains the 32-bit difference, the actual remaining R8 (full 64-bit),
     * the final right cursor address (64-bit), the final fresh right WORD (16-bit),
     * and a flag indicating whether final reads occurred (false if count was 0).
     */
    record Result(
        int difference32,
        long remainingR8,
        long finalRightCursor,
        int finalRightWord,
        boolean finalReadsOccurred
    ) { }

    /**
     * The single execution entry point for the generic comparison.
     * Inputs correspond to the actual generic inputs: RCX (left pointer), RDX (right pointer), R8 (count).
     * The implementation must use the supplied Memory interface for reads.
     */
    Result execute(Memory memory, long rcx, long rdx, long r8);
}