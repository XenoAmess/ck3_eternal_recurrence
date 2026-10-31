package org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup;

public final class Free83Candidate {
    private Free83Candidate() { }

    public static void release(long blockRaw, long heapHandleRaw, Free83Inputs.Calls calls) {
        if (blockRaw == 0L) {
            return;
        }

        int heapFreeResult = calls.heapFree(heapHandleRaw, 0, blockRaw);

        if (heapFreeResult != 0) {
            return;
        }

        Free83Inputs.Cell32 cell = calls.failureCell();
        int lastErrorBits = calls.lastErrorBits();
        int mappedBits = calls.mapCode(Integer.toUnsignedLong(lastErrorBits));
        cell.value = mappedBits;
    }
}