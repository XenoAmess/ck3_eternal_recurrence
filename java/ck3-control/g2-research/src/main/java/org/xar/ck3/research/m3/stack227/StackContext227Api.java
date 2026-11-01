package org.xar.ck3.research.m3.stack227;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/**
 * Minimal business producer API for the actual 58-byte callee at 0x424DE88.
 * This contract defines the explicit stack context (E) and the typed port for the
 * single observed child call (0x424DB74) based on the raw ASM prologue and call site.
 * It does not implement the body, nor does it assume full CPU state or OS semantics.
 */
public interface StackContext227Api {

    /**
     * Represents the explicit stack frame context for the 58-byte callee.
     * E is the entry RSP (stack pointer at function entry).
     * entryRCX is the value of RCX at function entry, which is written to E+8.
     */
    record Context(long E, long entryRCX) { }

    /**
     * Typed port for the child call to 0x424DB74.
     * The arguments are derived from the ASM prologue and call site:
     * - RCX = E + 0x10
     * - RDX = E + 0x20
     * - R8  = E - 0x18
     * - R9  = E + 0x18
     * The return value is the opaque RAX from the child call.
     */
    interface Ports {
        long call424db74(NativeTaskMemory memory, long siteRva, long rcx, long rdx, long r8, long r9);
    }

    /**
     * Exact write table for the prologue of 0x424DE88.
     * These operations establish the stack context before the child call.
     * E+0x10 is not initialized by this body; its entire supplied-storage value
     * remains unknown before the opaque child. Pointer use does not establish a
     * low-32-bit interpretation. The two DWORD writes at E+0x18 and E+0x20
     * preserve their adjacent high DWORDs.
     */
    // Prologue writes (conceptual, for implementation reference):
    // 1. W64[E+0x08] = entryRCX
    // 2. W64[E-0x18] = E+0x08
    // 3. W32[E+0x18] = 2
    // 4. W32[E+0x20] = 2
    // Child Call:
    // 5. call424db74(memory, 0x424DEB8, E+0x10, E+0x20, E-0x18, E+0x18)
}
