package org.xar.ck3.control.g2.m2.nativecode;
public final class PendingPageTableReserve2A32620 {
    private PendingPageTableReserve2A32620() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        void write32(long address,int value);
        void write64(long address,long value);
    }
    public interface Calls {
        long allocate(Memory memory,long target,long rcx,long rdx,int r8d);
        void release(Memory memory,long target,long rcx,long rdx,int r8d);
        void call4223F44(Memory memory,long rcx,int edx);
    }
    public static void reserve(Memory memory,Calls calls,long tableAddress,int desiredCount) {
        int currentCapacity = memory.read32(tableAddress + 8);
        if (desiredCount <= currentCapacity) {
            return;
        }
        long allocator = memory.read64(tableAddress + 0x10);
        long vtable = memory.read64(allocator);
        long target = memory.read64(vtable + 8);
        long size = Integer.toUnsignedLong(desiredCount) << 3;
        long newBuffer = calls.allocate(memory, target, allocator, size, 8);
        int count = memory.read32(tableAddress + 12);
        if (count > 0) {
            long oldArray = memory.read64(tableAddress);
            for (int i = 0; i < count; i++) {
                long slot = oldArray + ((long) i << 3);
                long value = memory.read64(slot);
                memory.write64(slot, 0);
                memory.write64(newBuffer + ((long) i << 3), value);
            }
            count = memory.read32(tableAddress + 12);
        }
        if (count > 0) {
            long freshOldArray = memory.read64(tableAddress);
            for (int i = 0; i < count; i++) {
                long page = memory.read64(freshOldArray + ((long) i << 3));
                if (page != 0) {
                    calls.call4223F44(memory, page, 0x172000);
                }
            }
        }
        long freshAllocator = memory.read64(tableAddress + 0x10);
        long freshOldArray = memory.read64(tableAddress);
        long freshVtable = memory.read64(freshAllocator);
        long freshTarget = memory.read64(freshVtable + 0x10);
        calls.release(memory, freshTarget, freshAllocator, freshOldArray, 8);
        memory.write64(tableAddress, newBuffer);
        memory.write32(tableAddress + 12, count);
        memory.write32(tableAddress + 8, desiredCount);
    }
}