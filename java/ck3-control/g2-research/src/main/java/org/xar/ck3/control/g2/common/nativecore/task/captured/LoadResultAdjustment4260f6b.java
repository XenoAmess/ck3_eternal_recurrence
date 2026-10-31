package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
/** New source-bound normal result projection from 4260F6B..4260F8E; supplied memory only. */
public final class LoadResultAdjustment4260f6b {
    private LoadResultAdjustment4260f6b() { }
    public static long adjust(long completeObjectBits, long descriptorBits, NativeTaskMemory memory) {
        int ebx = 0;
        int r9_c = memory.readInt32(descriptorBits + 0xC);
        if (r9_c < ebx) {
            long rax = (long) memory.readInt32(descriptorBits + 0x8);
            rax = rax + 0L;
            long result = completeObjectBits + rax;
            return result;
        }
        long rbx = (long) memory.readInt32(descriptorBits + 0xC);
        long rcx = (long) memory.readInt32(descriptorBits + 0x10);
        long rax = memory.readPointer(rbx + completeObjectBits);
        rcx = (long) memory.readInt32(rax + rcx);
        rbx = rbx + rcx;
        rax = (long) memory.readInt32(descriptorBits + 0x8);
        rax = rbx + rax;
        long result = completeObjectBits + rax;
        return result;
    }
}
