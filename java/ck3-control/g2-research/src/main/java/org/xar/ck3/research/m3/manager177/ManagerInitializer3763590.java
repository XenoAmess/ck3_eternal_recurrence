package org.xar.ck3.research.m3.manager177;

import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Memory;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Outcome;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Ports;

/** Owner normal business-field projection of the six connected captured RF fragments. */
public final class ManagerInitializer3763590 {
    private ManagerInitializer3763590() { }
    public static Outcome initialize(long imageBase, Memory memory, Ports ports) {
        long global = imageBase + 0x5C6A4D0L;
        long guard = memory.readPointer(global);
        if (guard != 0) return new Outcome(false, guard);
        long context = ports.context(0x37635B6L, memory);
        long object = ports.allocateObject(0x37635C3L, memory, 0x210);
        memory.writeInt64(object, 0);
        memory.writeInt64(object + 0x8, 0);
        memory.writeInt64(object + 0x10, 0);
        memory.writeInt64(object + 0x18, imageBase + 0x54F2A78L);
        memory.writeByte(object + 0x20, 0);
        long provider = ports.allocatorProvider(0x37635EDL, memory);
        memory.writeInt64(object + 0x30, provider);
        memory.writeInt64(object + 0x38, 0);
        memory.writeInt64(object + 0x48, imageBase + 0x54F2A80L);
        memory.writeByte(object + 0x40, 0);
        memory.writeInt32(object + 0x44, 0x3F666666);
        memory.writeInt32(object + 0x50, 0);
        memory.writeInt64(object + 0x68, imageBase + 0x54DE268L);
        memory.writeInt64(object + 0x58, 0);
        memory.writeInt64(object + 0x60, 0);
        memory.writeInt32(object + 0x70, 0);
        ports.initializeMap(0x376362FL, memory, object + 0x78);
        ports.initializeMap(0x376363BL, memory, object + 0xD8);
        ports.initializeMap(0x3763647L, memory, object + 0x138);
        ports.initializeMap(0x3763653L, memory, object + 0x198);
        memory.writeInt64(object + 0x1F8, 0);
        memory.writeInt64(object + 0x208, imageBase + 0x54F2A88L);
        memory.writeInt64(object + 0x200, 0);
        if (memory.readInt32(object + 0x10) < 0x4E20) {
            long allocator = memory.readPointer(object + 0x18);
            long vtable = memory.readPointer(allocator);
            long allocationTarget = memory.readPointer(vtable + 0x8);
            long allocated = ports.allocateSlots(0x3763692L, memory, allocationTarget, allocator, 0x27100, 8);
            int count = memory.readInt32(object + 0x14);
            if (count > 0) {
                long source = memory.readPointer(object + 0x8);
                ports.copy(0x37636AEL, memory, allocated, source, ((long) count) << 3);
                count = memory.readInt32(object + 0x14);
            }
            long freshAllocator = memory.readPointer(object + 0x18);
            long freshData = memory.readPointer(object + 0x8);
            long freshVtable = memory.readPointer(freshAllocator);
            long releaseTarget = memory.readPointer(freshVtable + 0x10);
            ports.releaseSlots(0x37636C7L, memory, releaseTarget, freshAllocator, freshData, 8);
            memory.writeInt64(object + 0x8, allocated);
            memory.writeInt32(object + 0x14, count);
            memory.writeInt32(object + 0x10, 0x4E20);
        }
        long old = memory.readPointer(context);
        memory.writeInt64(context, object);
        if (old != 0) {
            ports.destroyOld(0x37636F0L, memory, old);
            ports.freeOld(0x37636FDL, memory, old, 0x210);
            memory.writeInt64(global, 0);
        }
        long fresh = memory.readPointer(context);
        memory.writeInt64(global, fresh);
        return new Outcome(true, fresh);
    }
}
