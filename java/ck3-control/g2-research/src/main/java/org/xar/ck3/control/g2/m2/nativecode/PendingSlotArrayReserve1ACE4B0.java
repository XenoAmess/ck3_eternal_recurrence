package org.xar.ck3.control.g2.m2.nativecode;
public final class PendingSlotArrayReserve1ACE4B0 {
    private PendingSlotArrayReserve1ACE4B0() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        void write32(long address,int value);
        void write64(long address,long value);
    }
    public interface Calls {
        long allocate(Memory memory,long target,long rcx,long rdx,int r8d);
        void release(Memory memory,long target,long rcx,long rdx,int r8d);
        void call4226860(Memory memory,long rcx,long rdx,long r8);
    }
    public static void reserve(Memory memory,Calls calls,long tableAddress,int requestedCapacity) {
        int currentCapacity = memory.read32(tableAddress + 8);
        if (requestedCapacity <= currentCapacity) {
            return;
        }
        long allocator = memory.read64(tableAddress + 0x10);
        long vtable = memory.read64(allocator);
        long target = memory.read64(vtable + 8);
        long newBuffer = calls.allocate(memory, target, allocator, Integer.toUnsignedLong(requestedCapacity) << 4, 8);
        int count = memory.read32(tableAddress + 12);
        if (count > 0) {
            long oldBuffer = memory.read64(tableAddress);
            calls.call4226860(memory, newBuffer, oldBuffer, (long)count << 4);
            count = memory.read32(tableAddress + 12);
        }
        long allocator2 = memory.read64(tableAddress + 0x10);
        long oldBuffer2 = memory.read64(tableAddress);
        long vtable2 = memory.read64(allocator2);
        long target2 = memory.read64(vtable2 + 0x10);
        calls.release(memory, target2, allocator2, oldBuffer2, 8);
        memory.write64(tableAddress, newBuffer);
        memory.write32(tableAddress + 12, count);
        memory.write32(tableAddress + 8, requestedCapacity);
    }
}