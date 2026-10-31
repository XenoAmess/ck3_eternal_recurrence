package org.xar.ck3.control.g2.m2.nativecode;

/** Normal470B slot producer2A32770; explicit unknown callees remain ports.
 * No actual allocation, Game query, command submission or generic-type inventory.
 */
public final class PendingSlotProducer2A32770 {
    private PendingSlotProducer2A32770() { }
    public interface Memory extends PendingComponentInit2756120.Memory {
        int read8(long address);
        int read32(long address);
        long read64(long address);
    }
    public interface Calls {
        boolean call1ACDFB0(Memory memory, long rcx, int edx);
        boolean call2A321F0(Memory memory, long rcx, int edx);
        void call3076B60(Memory memory, long rcx, long rdx);
    }
    public record Input(long receiver, long sourceContext,
            long argument3DwordPointer, long argument4BytePointer,
            long argument5BytePointer, long argument6DwordPointer,
            long moduleBase) { }
    public static long produce(Memory memory, Calls calls, Input input) {
        long table = input.receiver() + 8L;
        long fallbackAddress = input.moduleBase() + 0x5D1EC70L;
        if (memory.read8(table + 0x40L) != 0) return memory.read64(fallbackAddress);
        if (memory.read8(table + 0x41L) != 0) return memory.read64(fallbackAddress);
        if (memory.read32(table + 0x38L) == 0xFFFFFF) {
            int capacity = memory.read32(table + 0x24L);
            int doubled = capacity + capacity;
            int requested = Integer.compareUnsigned(doubled, 0xFFFFFF) < 0 ? doubled : 0xFFFFFE;
            if (capacity == requested) return memory.read64(fallbackAddress);
            if (!calls.call1ACDFB0(memory, table, requested)) return memory.read64(fallbackAddress);
        }
        int index = memory.read32(table + 0x38L);
        if (!calls.call2A321F0(memory, table, index + 1)) return memory.read64(fallbackAddress);
        long unsignedIndex = Integer.toUnsignedLong(index);
        long pages = memory.read64(table);
        long page = memory.read64(pages + (unsignedIndex >>> 10) * 8L);
        long object = page + (unsignedIndex & 0x3FFL) * 0x5C8L;
        long slotOffset = (unsignedIndex + unsignedIndex) * 8L;
        long slots = memory.read64(table + 0x18L);
        int next = memory.read32(slots + slotOffset);
        memory.write32(table + 0x38L, next);
        int freshNext = memory.read32(slots + slotOffset);
        if (Integer.compareUnsigned(freshNext, 0xFFFFFF) < 0) {
            long nextOffset = Integer.toUnsignedLong(freshNext) * 16L;
            memory.write32(slots + nextOffset + 4L, 0xFFFFFF);
            long currentSlots = memory.read64(table + 0x18L);
            memory.write32(currentSlots + slotOffset, 0xFFFFFF);
            slots = memory.read64(table + 0x18L);
        }
        memory.write32(table + 0x34L, memory.read32(table + 0x34L) + 1);
        memory.write8(table + 0x42L, 1);
        int generation = (memory.read32(object + 0x10L) & 0xFF000000) + 0x1000000;
        memory.write64(slots + slotOffset + 8L, object);
        int highest = memory.read32(table + 0x30L);
        if (highest == -1 || Integer.compareUnsigned(index, highest) > 0)
            memory.write32(table + 0x30L, index);
        int fullId = index | generation;
        int argument6 = memory.read32(input.argument6DwordPointer());
        int argument5 = memory.read8(input.argument5BytePointer());
        int argument4 = memory.read8(input.argument4BytePointer());
        int argument3 = memory.read32(input.argument3DwordPointer());
        memory.write32(object + 0x10L, -1);
        memory.write32(object + 0x14L, 0x4368496E);
        memory.write64(object, input.moduleBase() + 0x4759250L);
        memory.write64(object + 8L, input.moduleBase() + 0x4759288L);
        calls.call3076B60(memory, object + 0x18L, input.sourceContext());
        PendingComponentInit2756120.initialize(memory, object + 0x350L, input.moduleBase());
        memory.write32(object + 0x5B8L, 0);
        memory.write32(object + 0x5BCL, argument3);
        memory.write32(object + 0x5C0L,
                memory.read32(input.sourceContext() + 0x2E8L) == -1 ? 0 : 1);
        memory.write8(object + 0x5C4L, argument4 == 1 ? 1 : 0);
        memory.write8(object + 0x5C5L, argument5 == 1 ? 1 : 0);
        memory.write8(object + 0x5C6L, argument6 == 1 ? 1 : 0);
        memory.write32(object + 0x10L, fullId);
        return object;
    }
}
