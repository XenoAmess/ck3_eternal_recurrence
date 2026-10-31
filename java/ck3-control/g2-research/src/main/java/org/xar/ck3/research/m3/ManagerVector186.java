package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.ManagerVectorApi186.Memory;
import org.xar.ck3.research.m3.ManagerVectorApi186.Ports;

/** Normal supplied-storage effects of held416B3763F90; calls/FP are observations. */
public final class ManagerVector186 {
    private ManagerVector186() { }

    public static void collect(Memory memory, Ports ports, long moduleBase, long manager, long output) {
        long table = memory.readPointer(manager + 0x30L);
        long row = table;
        while (memory.readUnsigned8(row + 4L) == 0) {
            row += 0x18L;
        }
        int extra = memory.readUnsigned8(manager + 0x40L);
        int endIndex = memory.readInt32(manager + 0x3CL);
        endIndex = endIndex + extra + 1;
        long end = table + (long) endIndex * 0x18L;
        if (row == end) {
            return;
        }
        int multiplierBits = memory.readInt32(moduleBase + 0x49F64F0L);

        do {
            long receiver = memory.readPointer(row + 0x10L);
            long vtable = memory.readPointer(receiver);
            long code = memory.readPointer(vtable + 8L);
            long supplied = ports.objectSlot08(memory, code, receiver);
            int count = memory.readInt32(output + 0x0CL);
            int capacity = memory.readInt32(output + 8L);
            int lastCount;
            long lastData;

            if (count == capacity) {
                int required = count + 1;
                int observedGrowth = ports.growthCvtt32(memory, capacity, multiplierBits);
                int newCapacity = required < observedGrowth ? observedGrowth : required;
                long allocator = memory.readPointer(output + 0x10L);
                vtable = memory.readPointer(allocator);
                code = memory.readPointer(vtable + 8L);
                long newData = ports.allocatorSlot08(memory, code, allocator,
                        Integer.toUnsignedLong(newCapacity) << 3, 8);

                int appendIndex = memory.readInt32(output + 0x0CL);
                memory.writeInt64(newData + (long) appendIndex * 8L, supplied);
                int remaining = memory.readInt32(output + 0x0CL);
                if (remaining > 0) {
                    long source = memory.readPointer(output);
                    long destination = newData;
                    do {
                        long value = memory.readPointer(source);
                        memory.writeInt64(source, 0L);
                        memory.writeInt64(destination, value);
                        source += 8L;
                        destination += 8L;
                        remaining--;
                    } while (remaining > 0);

                    remaining = memory.readInt32(output + 0x0CL);
                    if (remaining > 0) {
                        long cleanup = memory.readPointer(output);
                        do {
                            long object = memory.readPointer(cleanup);
                            if (object != 0L) {
                                vtable = memory.readPointer(object);
                                code = memory.readPointer(vtable);
                                ports.objectSlot00(memory, code, object, 1);
                            }
                            remaining--;
                            cleanup += 8L;
                        } while (remaining > 0);
                    }
                }

                allocator = memory.readPointer(output + 0x10L);
                long oldData = memory.readPointer(output);
                vtable = memory.readPointer(allocator);
                code = memory.readPointer(vtable + 0x10L);
                ports.allocatorSlot10(memory, code, allocator, oldData, 8);
                memory.writeInt64(output, newData);
                memory.writeInt32(output + 0x0CL, required);
                memory.writeInt32(output + 8L, newCapacity);
                lastCount = required;
                lastData = newData;
            } else {
                long data = memory.readPointer(output);
                memory.writeInt64(data + (long) count * 8L, supplied);
                memory.incrementInt32(output + 0x0CL);
                lastCount = memory.readInt32(output + 0x0CL);
                lastData = memory.readPointer(output);
            }

            long last = memory.readPointer(lastData + (long) lastCount * 8L - 8L);
            int key = memory.readInt32(row + 8L);
            memory.writeInt32(last + 8L, key);
            memory.write8(last + 0x0CL, 0);
            do {
                row += 0x18L;
            } while (memory.readUnsigned8(row + 4L) == 0);
        } while (row != end);
    }
}
