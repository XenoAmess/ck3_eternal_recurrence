package org.xar.ck3.control.g2.m2.nativecode;

/** Complete 372-byte normal CFG with opaque reserve and set ports. */
public final class PendingSlotCapacity1ACDFB0 {
    private PendingSlotCapacity1ACDFB0() { }

    public interface Memory {
        int read8(long address);
        int read32(long address);
        long read64(long address);
        void write32(long address, int value);
        void write64(long address, long value);
    }

    public interface Calls {
        void call1ACE4B0(Memory memory, long rcx, int edx);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
    }

    public static boolean grow(Memory memory, Calls calls, long tableAddress, int requestedCapacity) {
        if (memory.read8(tableAddress + 0x40) != 0) {
            return false;
        }
        int oldCapacity = memory.read32(tableAddress + 0x24);
        if (Integer.compareUnsigned(requestedCapacity, oldCapacity) <= 0) {
            return true;
        }
        if (Integer.compareUnsigned(requestedCapacity, 0xFFFFFF) > 0) {
            return false;
        }
        int currentCapacity = memory.read32(tableAddress + 0x24);
        if (requestedCapacity > currentCapacity) {
            calls.call1ACE4B0(memory, tableAddress + 0x18, requestedCapacity);
            int freshCount = memory.read32(tableAddress + 0x24);
            int difference = requestedCapacity - freshCount;
            if (difference > 0) {
                long clearAt = ((long) freshCount << 4) + memory.read64(tableAddress + 0x18);
                calls.call4226F10(memory, clearAt, 0, Integer.toUnsignedLong(difference) << 4);
            }
        }
        int last = requestedCapacity - 1;
        memory.write32(tableAddress + 0x24, requestedCapacity);
        int index = last;
        int next = requestedCapacity;
        while (Integer.compareUnsigned(index, oldCapacity) >= 0
                && Integer.compareUnsigned(index, requestedCapacity) < 0) {
            long offset = Integer.toUnsignedLong(index) << 4;
            memory.write32(memory.read64(tableAddress + 0x18) + offset + 4, 0xFFFFFF);
            memory.write64(memory.read64(tableAddress + 0x18) + offset + 8, 0);
            long base = memory.read64(tableAddress + 0x18);
            if (Integer.compareUnsigned(index, last) < 0) {
                memory.write32(base + (Integer.toUnsignedLong(next) << 4) + 4, index);
                memory.write32(memory.read64(tableAddress + 0x18) + offset, next);
            } else {
                memory.write32(base + offset, 0xFFFFFF);
            }
            index--;
            next--;
        }
        if (memory.read32(tableAddress + 0x38) == 0xFFFFFF) {
            memory.write32(tableAddress + 0x38, oldCapacity);
            return true;
        }
        int tail = oldCapacity - 1;
        if (Integer.compareUnsigned(tail, oldCapacity) >= 0) {
            return true;
        }
        long oldBase = memory.read64(tableAddress + 0x18);
        do {
            long slot = oldBase + (Integer.toUnsignedLong(tail) << 4);
            if (memory.read64(slot + 8) == 0 && memory.read32(slot) == 0xFFFFFF) {
                memory.write32(slot, oldCapacity);
                long freshBase = memory.read64(tableAddress + 0x18);
                memory.write32(freshBase + (Integer.toUnsignedLong(oldCapacity) << 4) + 4, tail);
                return true;
            }
            tail--;
        } while (Integer.compareUnsigned(tail, oldCapacity) < 0);
        return true;
    }
}
