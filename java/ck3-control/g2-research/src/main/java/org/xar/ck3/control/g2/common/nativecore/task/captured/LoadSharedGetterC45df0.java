package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Only C45DF0's supplied-storage call/selection projection; 4260E74 stays opaque. */
public final class LoadSharedGetterC45df0 {
    private LoadSharedGetterC45df0() { }
    public interface Ports {
        long call4260e74(long objectPointer, int adjustmentBits, long sourceToken,
                long targetToken, int failureModeBits);
    }
    public static long get(long moduleBase, NativeTaskMemory memory, Ports ports) {
        long a = memory.readPointer(moduleBase + 0x5C6A520L);
        long x = memory.readPointer(a + 0x10L);
        long y = ports.call4260e74(x, 0, moduleBase + 0x5514438L, moduleBase + 0x5514460L, 0);
        if (y != 0L) {
            return memory.readPointer(y + 0x28L);
        }
        long z = ports.call4260e74(x, 0, moduleBase + 0x5514438L, moduleBase + 0x5519DC0L, 0);
        if (z != 0L) {
            return memory.readPointer(z + 0x10L);
        }
        return 0L;
    }
}
