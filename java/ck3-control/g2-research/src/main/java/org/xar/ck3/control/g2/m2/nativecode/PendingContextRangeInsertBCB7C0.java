package org.xar.ck3.control.g2.m2.nativecode;

/** Full306B normalBCB7C0, actual four unknown callees stay opaque. */
public final class PendingContextRangeInsertBCB7C0 {
    private PendingContextRangeInsertBCB7C0() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        void write32(long address, int value);
        void write64(long address, long value);
    }
    public interface Calls {
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226860(Memory memory, long rcx, long rdx, long r8);
        void call9CF240(Memory memory, long rcx, long rdx, long r8);
    }
    public record Input(long receiver, int index, long begin, long end, long moduleBase) { }
    private static int cvttss2si(float value) {
        if (!(value >= -2147483648.0f && value < 2147483648.0f)) return Integer.MIN_VALUE;
        return (int) value;
    }
    public static void insert(Memory memory, Calls calls, Input input) {
        long begin = input.begin();
        long end = input.end();
        if (begin == end) return;
        long receiver = input.receiver();
        long initialCount = memory.read32(receiver + 0xC);
        int delta = (int) end - (int) begin;
        long index = input.index();
        int capacity = memory.read32(receiver + 8);
        int desired = (int) initialCount + delta;
        if (desired > capacity) {
            long allocator = memory.read64(receiver + 0x10);
            float factor = Float.intBitsToFloat(memory.read32(input.moduleBase() + 0x49F64F0));
            int scaled = cvttss2si((float) capacity * factor);
            int selectedCapacity = desired < scaled ? scaled : desired;
            long vtable = memory.read64(allocator);
            long target = memory.read64(vtable + 8);
            long newBuffer = calls.allocate(memory, target, allocator,
                    Integer.toUnsignedLong(selectedCapacity), 1);
            long oldBuffer = memory.read64(receiver);
            calls.call4226860(memory, newBuffer, oldBuffer, index);
            long length = end - begin;
            calls.call4226860(memory, index + newBuffer, begin, length);
            oldBuffer = memory.read64(receiver);
            long freshCount = memory.read32(receiver + 0xC);
            long destination = (long) delta + index + newBuffer;
            long source = index + oldBuffer;
            long bytes = freshCount - source + oldBuffer;
            calls.call4226860(memory, destination, source, bytes);
            allocator = memory.read64(receiver + 0x10);
            oldBuffer = memory.read64(receiver);
            vtable = memory.read64(allocator);
            target = memory.read64(vtable + 0x10);
            calls.release(memory, target, allocator, oldBuffer, 1);
            memory.write64(receiver, newBuffer);
            memory.write32(receiver + 8, selectedCapacity);
            memory.write32(receiver + 0xC, desired);
        } else {
            long buffer = memory.read64(receiver);
            calls.call4226860(memory, initialCount + buffer, begin, end - begin);
            long freshCount = memory.read32(receiver + 0xC);
            buffer = memory.read64(receiver);
            int newCount = (int) freshCount + delta;
            long after = (long) newCount + buffer;
            long before = buffer + freshCount;
            memory.write32(receiver + 0xC, newCount);
            calls.call9CF240(memory, buffer + index, before, after);
        }
    }
}
