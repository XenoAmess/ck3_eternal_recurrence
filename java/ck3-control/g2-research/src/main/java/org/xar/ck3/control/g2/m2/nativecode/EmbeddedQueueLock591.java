package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;

/**
 * Package-private final helper implementing the exact lock acquisition loop
 * from original 0x3727EE4..0x3727EFA.
 *
 * Contract requirements:
 * - Caller has already set ECX=1 (desired value for CAS).
 * - Before every iteration (read or CAS attempt), call budget.beforeStep(0x3727EE4L, lockAddress).
 * - Read DWORD at lockAddress, zero-extend into RAX.
 * - If nonzero, retry (PAUSE is represented as no-op in this model).
 * - If zero, perform atomic compareExchangeDword(lockAddress, 0, (int)r.rcx).
 * - The result of compareExchangeDword is the old value; zero-extend into RAX.
 * - If old == 0, lock acquired (return). Else retry.
 * - Preserve all other registers/XMM/SP state.
 * - Propagate exceptions unchanged.
 */
final class EmbeddedQueueLock591 {
    private EmbeddedQueueLock591() { }

    static void acquire(Registers r, EmbeddedQueue591Api.Memory memory, LoopBudget budget, long lockAddress) {
        // ECX is already set to 1 by the caller (desired value for CAS).
        // The loop implements: 0x3727EE4 (mov eax, [lock]) -> 0x3727EFA (jmp back)

        while (true) {
            // Before every iteration, invoke the budget hook.
            budget.beforeStep(0x3727EE4L, lockAddress);

            // 0x3727EE4: mov eax, DWORD PTR [rip+0x257807e] (read lock)
            // Read DWORD and zero-extend into RAX.
            int lockVal = memory.readDword(lockAddress);
            r.rax = Integer.toUnsignedLong(lockVal);

            // 0x3727EEA: test eax, eax
            // 0x3727EEC: jne 0x3727EF8 (if nonzero, jump to pause/retry)
            if (lockVal != 0) {
                // Nonzero: retry. PAUSE is represented as no-op in this model.
                continue;
            }

            // 0x3727EEE: lock cmpxchg DWORD PTR [rip+0x2578072], ecx
            // Perform atomic compare-exchange: expected=0, desired=ECX (which is 1).
            // The result is the old value.
            int old = memory.compareExchangeDword(lockAddress, 0, (int)r.rcx);

            // Zero-extend the old value into RAX.
            r.rax = Integer.toUnsignedLong(old);

            // 0x3727EF6: je (ZF if old == 0)
            // If old == 0, we successfully acquired the lock (CAS succeeded).
            if (old == 0) {
                return;
            }

            // 0x3727EF8: pause (represented as no-op)
            // 0x3727EFA: jmp 0x3727EE4 (retry)
            // If old != 0, the CAS failed (someone else held the lock), so retry.
        }
    }
}