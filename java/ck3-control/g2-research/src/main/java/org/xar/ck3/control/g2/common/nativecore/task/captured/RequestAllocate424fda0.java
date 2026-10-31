package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;

/** Captured allocation control flow with supplied heap and failure-cell ports. */
public final class RequestAllocate424fda0 {
    private RequestAllocate424fda0() { }
    public interface Ports {
        int call424e250();
        int call424cffc(long knownRcx);
        long heapAlloc(long heapHandleBits,int flagsBits,long bytesBits);
        Cell32 call423b18c();
    }
    public static long allocate(long moduleBase,long sizeBits,NativeTaskMemory memory,Ports ports) {
        long rbx = sizeBits;
        long rcx = sizeBits;
        if (Long.compareUnsigned(rcx, 0xFFFFFFFFFFFFFFE0L) > 0) {
            return failure(moduleBase, memory, ports);
        }
        if (rcx == 0L) {
            rbx = 1L;
        }
        while (true) {
            long heapHandle = memory.readPointer(moduleBase + 0x5c5de30L);
            long rax = ports.heapAlloc(heapHandle, 0, rbx);
            if (rax != 0L) {
                return rax;
            }
            int eax1 = ports.call424e250();
            if (eax1 == 0) {
                return failure(moduleBase, memory, ports);
            }
            int eax2 = ports.call424cffc(rbx);
            if (eax2 == 0) {
                return failure(moduleBase, memory, ports);
            }
        }
    }

    private static long failure(long moduleBase, NativeTaskMemory memory, Ports ports) {
        Cell32 cell = ports.call423b18c();
        cell.value = 12;
        return 0L;
    }
}
