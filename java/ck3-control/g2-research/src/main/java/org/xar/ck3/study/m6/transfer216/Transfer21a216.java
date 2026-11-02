package org.xar.ck3.study.m6.transfer216;

import org.xar.ck3.study.m6.transfer216.Transfer216Api.Bits128;
import org.xar.ck3.study.m6.transfer216.Transfer216Api.Budget;
import org.xar.ck3.study.m6.transfer216.Transfer216Api.Calls;
import org.xar.ck3.study.m6.transfer216.Transfer216Api.Input;
import org.xar.ck3.study.m6.transfer216.Transfer216Api.Memory;

/** Instruction-ordered normal-body kernel; virtual internals and EH language remain unknown. */
public final class Transfer21a216 {
    private Transfer21a216() { }

    public static long execute(Input input, Memory memory, Calls calls, Budget budget) {
        budget.step();
        long destination = input.destinationRaw64();
        long source = input.sourceRaw64();
        long allocator = memory.read64(destination + 0x10);
        if (allocator == memory.read64(source + 0x10)) {
            long table = memory.read64(allocator);
            long pointer = memory.read64(destination);
            calls.release16(memory.read64(table + 0x10), allocator, pointer, 8, 0x21a508f);
            memory.write64(destination, 0);
            memory.write64(destination + 8, 0);
            long sourceAllocator = memory.read64(source + 0x10);
            if (memory.read64(destination + 0x10) == sourceAllocator) {
                long sourcePointer = memory.read64(source);
                memory.write64(destination, sourcePointer);
                memory.write64(source, 0);
                int destinationCount = memory.read32(destination + 0xc);
                int sourceCount = memory.read32(source + 0xc);
                memory.write32(destination + 0xc, sourceCount);
                memory.write32(source + 0xc, destinationCount);
                int destinationCapacity = memory.read32(destination + 8);
                int sourceCapacity = memory.read32(source + 8);
                memory.write32(destination + 8, sourceCapacity);
                memory.write32(source + 8, destinationCapacity);
                return destination;
            }
            int sourceCount = memory.read32(source + 0xc);
            long first = sourceCount < 0 ? source : destination;
            long second = sourceCount >= 0 ? source : destination;
            long frame = input.frameRaw64();
            long temporary = frame + 0x20;
            memory.write64(frame + 0x40, input.imageBaseRaw64() + 0x46b3a90L);
            memory.write64(frame + 0x448, input.imageBaseRaw64() + 0x54de260L);
            memory.write64(temporary, 0);
            memory.write64(temporary + 8, 0);
            memory.write64(temporary + 0x10, frame + 0x40);
            long childFrame = frame - 0x480;
            execute(new Input(temporary, first, input.imageBaseRaw64(), childFrame), memory, calls, budget);
            execute(new Input(first, second, input.imageBaseRaw64(), childFrame), memory, calls, budget);
            execute(new Input(second, temporary, input.imageBaseRaw64(), childFrame), memory, calls, budget);
            long temporaryPointer = memory.read64(temporary);
            if (temporaryPointer != 0) {
                memory.write32(temporary + 0xc, 0);
                long temporaryAllocator = memory.read64(temporary + 0x10);
                table = memory.read64(temporaryAllocator);
                calls.release16(memory.read64(table + 0x10), temporaryAllocator, temporaryPointer, 8, 0x21a5159);
            }
            return destination;
        }

        memory.write32(destination + 0xc, 0);
        long sourceBytes = ((long) memory.read32(source + 0xc)) << 4;
        long sourceBegin = memory.read64(source);
        long sourceEnd = sourceBegin + sourceBytes;
        if (sourceBegin != sourceEnd) {
            int count = (int) (sourceBytes >> 4);
            int capacity = memory.read32(destination + 8);
            if (count > capacity) {
                float scaled = (float) capacity * Float.intBitsToFloat(memory.read32(input.imageBaseRaw64() + 0x49f64f0L));
                int converted = cvttss2si(scaled);
                int newCapacity = count < converted ? converted : count;
                long table = memory.read64(allocator);
                long bytes = Integer.toUnsignedLong(newCapacity) << 4;
                long newBuffer = calls.allocate08(memory.read64(table + 8), allocator, bytes, 8, 0x21a51b9);
                long displacement = newBuffer - sourceBegin;
                do {
                    budget.step();
                    Bits128 value = memory.read128(sourceBegin);
                    memory.write128(displacement + sourceBegin, value);
                    sourceBegin += 0x10;
                } while (sourceBegin != sourceEnd);

                long oldBegin = memory.read64(destination);
                long oldEnd = oldBegin + (((long) memory.read32(destination + 0xc)) << 4);
                long tail = newBuffer + (((long) count) << 4);
                if (oldBegin != oldEnd) {
                    do {
                        budget.step();
                        Bits128 value = memory.read128(oldBegin);
                        memory.write128(tail, value);
                        tail += 0x10;
                        oldBegin += 0x10;
                    } while (oldBegin != oldEnd);
                    oldBegin = memory.read64(destination);
                }
                long currentAllocator = memory.read64(destination + 0x10);
                table = memory.read64(currentAllocator);
                calls.release16(memory.read64(table + 0x10), currentAllocator, oldBegin, 8, 0x21a5223);
                memory.write64(destination, newBuffer);
                memory.write32(destination + 0xc, count);
                memory.write32(destination + 8, newCapacity);
            } else {
                long write = memory.read64(destination);
                do {
                    budget.step();
                    Bits128 value = memory.read128(sourceBegin);
                    memory.write128(write, value);
                    write += 0x10;
                    sourceBegin += 0x10;
                } while (sourceBegin != sourceEnd);
                long oldCount = memory.read32(destination + 0xc);
                long begin = memory.read64(destination);
                int total = (int) oldCount + count;
                memory.write32(destination + 0xc, total);
                long middle = begin + (oldCount << 4);
                long end = begin + (((long) total) << 4);
                if (begin != middle && middle != end) {
                    reverse(memory, budget, begin, middle);
                    reverse(memory, budget, middle, end);
                    if (begin != end) reverse(memory, budget, begin, end);
                }
            }
        }
        memory.write32(source + 0xc, 0);
        return destination;
    }

    private static int cvttss2si(float value) {
        if (!(value >= -0x1.0p31f && value < 0x1.0p31f)) return Integer.MIN_VALUE;
        return (int) value;
    }

    /** Equality-controlled native loop; deliberately does not replace its guards with signed pointer ordering. */
    private static void reverse(Memory memory, Budget budget, long begin, long end) {
        long low = begin;
        long high = end;
        while (true) {
            high -= 0x10;
            if (low == high) return;
            budget.step();
            Bits128 lower = memory.read128(low);
            Bits128 upper = memory.read128(high);
            memory.write128(low, upper);
            memory.write128(high, lower);
            low += 0x10;
            if (low == high) return;
        }
    }
}
