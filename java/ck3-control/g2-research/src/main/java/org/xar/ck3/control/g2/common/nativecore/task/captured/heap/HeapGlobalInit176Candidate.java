package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.HeapGlobalInit176Inputs.Calls;

/** Exact-width address operations for supplied storage; no process attachment. */
public final class HeapGlobalInit176Candidate {
    private HeapGlobalInit176Candidate() { }

    public static long init(long moduleBase, NativeTaskMemory memory, Calls calls) {
        // 1. Call GetProcessHeap (simulated via calls.getProcessHeap())
        long rax = calls.getProcessHeap();

        // 2. TEST RAX, RAX
        // Sets ZF based on all 64 bits of RAX. MOV does not modify flags.
        // SETNE AL sets AL to 1 if ZF is clear (RAX != 0), else 0.
        // AL is bits 0-7 of RAX. Bits 8-63 of RAX are preserved.

        // 3. MOV QWORD PTR [RIP + 0x1A02580], RAX
        // Writes the full 64-bit RAX value to the heap cell.
        memory.writeInt64(moduleBase + 0x5C5DE30L, rax);

        // 4. SETNE AL
        // AL = (RAX != 0) ? 1 : 0
        long al = (rax != 0L) ? 1L : 0L;
        long finalRax = (rax & 0xFFFFFFFFFFFFFF00L) | al;

        return finalRax;
    }
}