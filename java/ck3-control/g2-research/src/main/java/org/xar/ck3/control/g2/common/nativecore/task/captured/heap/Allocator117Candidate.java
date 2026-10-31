package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs.Calls;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs.HeapCell64;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;

/** Owner takeover after two rejected complete-method candidates; normal117B behavior only. */
public final class Allocator117Candidate {
    private Allocator117Candidate() { }

    public static long allocate(long countRaw, long elementBytesRaw, HeapCell64 heap, Calls calls) {
        if (countRaw != 0L) {
            long quotient = Long.divideUnsigned(-32L, countRaw);
            if (Long.compareUnsigned(quotient, elementBytesRaw) < 0) {
                return fail(calls);
            }
        }

        long bytes = countRaw * elementBytesRaw;
        if (bytes == 0L) {
            bytes = 1L;
        }

        for (;;) {
            long allocated = calls.allocateImported(heap.value, 8, bytes);
            if (allocated != 0L) {
                return allocated;
            }
            if (calls.retryGate() == 0) {
                return fail(calls);
            }
            if (calls.retryCall(bytes) == 0) {
                return fail(calls);
            }
        }
    }

    private static long fail(Calls calls) {
        Cell32 selected = calls.failureCell();
        selected.value = 0xC;
        return 0L;
    }
}
