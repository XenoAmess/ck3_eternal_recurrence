package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Shared projection of actual B67..B77 and BC5..BD8 byte loops, not a separate native entry. */
public final class LoadByteNames4260b67 {
    private LoadByteNames4260b67() { }
    public static int compare(long left, long right, LoadSearch4260af0.ReadMemory memory) {
        long l = left;
        long r = right;
        while (true) {
            int lb = memory.readUnsigned8(l);
            int rb = memory.readUnsigned8(r);
            int diff = lb - rb;
            if (diff != 0) {
                return diff;
            }
            if (rb == 0) {
                return 0;
            }
            l++;
            r++;
        }
    }
}
