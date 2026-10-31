package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class AllocatorSelector165 {
    private AllocatorSelector165() {}
    public static long select(NativeTaskMemory memory, long receiver) {
        return memory.readPointer(receiver + 0x408);
    }
}
