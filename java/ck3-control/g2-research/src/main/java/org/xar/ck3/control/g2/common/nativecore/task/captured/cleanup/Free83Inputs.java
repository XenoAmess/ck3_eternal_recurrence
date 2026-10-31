package org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup;

/** Exact observable roles of the held 5+17+61 byte release chain; source-bound software projection. */
public final class Free83Inputs {
    private Free83Inputs() { }

    public static final class Cell32 {
        public int value;
        public Cell32(int value) { this.value = value; }
    }

    public interface Calls {
        int heapFree(long heapHandleRaw, int flagsRaw32, long blockRaw);
        Cell32 failureCell();
        int lastErrorBits();
        int mapCode(long zeroExtendedError32);
    }
}