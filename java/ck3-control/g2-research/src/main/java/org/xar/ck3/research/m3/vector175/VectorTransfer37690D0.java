package org.xar.ck3.research.m3.vector175;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Source-bound header/scratch effects; opaque ports grant no native register/allocator semantics. */
public final class VectorTransfer37690D0 {
    private VectorTransfer37690D0() { }
    public interface Ports {
        long allocate(long callSiteRva, long functionTarget, long allocator, long bytes, int alignment);
        void release(long callSiteRva, long functionTarget, long allocator, long data, int alignment);
        void copy(long callSiteRva, long destination, long source, long bytes);
        void range(long callSiteRva, long first, long last);
        /** Pure exact CVTDQ2PS/MULSS/CVTTSS2SI result; this scalar instruction has no memory side effects. */
        int capacityGrowth(int oldCapacity, int factorBits);
    }
    /** bodyRsp and every recursive bodyRsp-0x480 must name caller-owned scratch, not native allocation. */
    public static long execute(long destination, long source, long bodyRsp, long imageBase,
            NativeTaskMemory memory, Ports ports) {
        long allocator = memory.readPointer(destination + 0x10);
        long sourceAllocator = memory.readPointer(source + 0x10);
        if (allocator == sourceAllocator) {
            long vtable = memory.readPointer(allocator);
            long released = memory.readPointer(destination);
            long target = memory.readPointer(vtable + 0x10);
            ports.release(0x376910FL, target, allocator, released, 8);
            memory.writeInt64(destination, 0);
            memory.writeInt64(destination + 0x8, 0);
            long freshSourceAllocator = memory.readPointer(source + 0x10);
            long freshDestinationAllocator = memory.readPointer(destination + 0x10);
            if (freshDestinationAllocator == freshSourceAllocator) {
                long moved = memory.readPointer(source);
                memory.writeInt64(destination, moved);
                memory.writeInt64(source, 0);
                int destinationCount = memory.readInt32(destination + 0xC);
                int sourceCount = memory.readInt32(source + 0xC);
                memory.writeInt32(destination + 0xC, sourceCount);
                memory.writeInt32(source + 0xC, destinationCount);
                int destinationCapacity = memory.readInt32(destination + 0x8);
                int sourceCapacity = memory.readInt32(source + 0x8);
                memory.writeInt32(destination + 0x8, sourceCapacity);
                memory.writeInt32(source + 0x8, destinationCapacity);
            } else {
                int sourceCount = memory.readInt32(source + 0xC);
                long first = sourceCount < 0 ? source : destination;
                long second = sourceCount < 0 ? destination : source;
                memory.writeInt64(bodyRsp + 0x40, imageBase + 0x492E730L);
                memory.writeInt64(bodyRsp + 0x448, imageBase + 0x54F2A78L);
                memory.writeInt64(bodyRsp + 0x20, 0);
                memory.writeInt64(bodyRsp + 0x28, 0);
                memory.writeInt64(bodyRsp + 0x30, bodyRsp + 0x40);
                execute(bodyRsp + 0x20, first, bodyRsp - 0x480, imageBase, memory, ports);
                execute(first, second, bodyRsp - 0x480, imageBase, memory, ports);
                execute(second, bodyRsp + 0x20, bodyRsp - 0x480, imageBase, memory, ports);
                long temporaryData = memory.readPointer(bodyRsp + 0x20);
                if (temporaryData != 0) {
                    memory.writeInt32(bodyRsp + 0x2C, 0);
                    long temporaryAllocator = memory.readPointer(bodyRsp + 0x30);
                    long temporaryVtable = memory.readPointer(temporaryAllocator);
                    long temporaryTarget = memory.readPointer(temporaryVtable + 0x10);
                    ports.release(0x37691DDL, temporaryTarget, temporaryAllocator, temporaryData, 8);
                }
            }
            return destination;
        }
        memory.writeInt32(destination + 0xC, 0);
        long sourceBytes = ((long) memory.readInt32(source + 0xC)) << 3;
        long sourceData = memory.readPointer(source);
        long sourceEnd = sourceData + sourceBytes;
        if (sourceData != sourceEnd) {
            int required = (int) (sourceBytes >> 3);
            int capacity = memory.readInt32(destination + 0x8);
            if (required > capacity) {
                int factorBits = memory.readInt32(imageBase + 0x49F64F0L);
                int scaled = ports.capacityGrowth(capacity, factorBits);
                int selectedCapacity = required < scaled ? scaled : required;
                long vtable = memory.readPointer(allocator);
                long allocationBytes = Integer.toUnsignedLong(selectedCapacity) << 3;
                long target = memory.readPointer(vtable + 0x8);
                long allocated = ports.allocate(0x3769240L, target, allocator, allocationBytes, 8);
                long oldData = memory.readPointer(destination);
                ports.copy(0x376924FL, allocated, oldData, 0);
                ports.copy(0x376925DL, allocated, sourceData, sourceBytes);
                long freshOldData = memory.readPointer(destination);
                long trailingBytes = ((long) memory.readInt32(destination + 0xC)) << 3;
                ports.copy(0x3769274L, allocated + (((long) required) << 3), freshOldData, trailingBytes);
                long freshAllocator = memory.readPointer(destination + 0x10);
                long freshVtable = memory.readPointer(freshAllocator);
                long freshData = memory.readPointer(destination);
                long freshTarget = memory.readPointer(freshVtable + 0x10);
                ports.release(0x3769287L, freshTarget, freshAllocator, freshData, 8);
                memory.writeInt64(destination, allocated);
                memory.writeInt32(destination + 0xC, required);
                memory.writeInt32(destination + 0x8, selectedCapacity);
            } else {
                long destinationData = memory.readPointer(destination);
                ports.copy(0x37692A0L, destinationData, sourceData, sourceBytes);
                int oldCount = memory.readInt32(destination + 0xC);
                int newCount = oldCount + required;
                memory.writeInt32(destination + 0xC, newCount);
                long freshData = memory.readPointer(destination);
                long middle = freshData + (((long) oldCount) << 3);
                long end = freshData + (((long) newCount) << 3);
                if (freshData != middle && middle != end) {
                    ports.range(0x37692CFL, freshData, middle);
                    ports.range(0x37692DAL, middle, end);
                    ports.range(0x37692E5L, freshData, end);
                }
            }
        }
        memory.writeInt32(source + 0xC, 0);
        return destination;
    }
}
