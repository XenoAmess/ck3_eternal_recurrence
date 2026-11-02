package org.xar.ck3.study.m6.transfer217;

import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Budget;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Calls;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Input;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Memory;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Operations;

/** B2EEE0 normal logical body. Deep call implementations and EH remain outside this contract. */
public final class Transfer4Move217 {
    private Transfer4Move217() { }

    private enum Bound implements Operations {
        INSTANCE;
        @Override public long move(Input input, Memory memory, Calls calls, Budget budget) {
            return execute(input, memory, calls, budget, this);
        }
        @Override public void swap(Input input, Memory memory, Calls calls, Budget budget) {
            Transfer4Swap217.execute(input, memory, calls, budget, this);
        }
    }

    /** Thin binding routes both actual mutually recursive bodies, without replacing either algorithm. */
    public static long execute(Input input, Memory memory, Calls calls, Budget budget) {
        return Bound.INSTANCE.move(input, memory, calls, budget);
    }

    public static long execute(Input input, Memory memory, Calls calls, Budget budget, Operations operations) {
        budget.step();
        long destination = input.destinationRaw64();
        long source = input.sourceRaw64();
        long allocator = memory.read64(destination + 0x10);
        if (allocator == memory.read64(source + 0x10)) {
            long table = memory.read64(allocator);
            long pointer = memory.read64(destination);
            calls.release16(memory.read64(table + 0x10), allocator, pointer, 4, 0xb2ef06);
            memory.write64(destination, 0);
            memory.write64(destination + 8, 0);
            operations.swap(new Input(destination, source, input.imageBaseRaw64(), input.frameRaw64() - 0x460),
                    memory, calls, budget);
            return destination;
        }
        memory.write32(destination + 0xc, 0);
        long sourceBegin = memory.read64(source);
        long sourceBytes = ((long) memory.read32(source + 0xc)) << 2;
        if (sourceBegin != sourceBegin + sourceBytes) {
            int capacity = memory.read32(destination + 8);
            int count = (int) (sourceBytes >> 2);
            if (count > capacity) {
                float scaled = (float) capacity * Float.intBitsToFloat(memory.read32(input.imageBaseRaw64() + 0x49f64f0L));
                int converted = cvttss2si(scaled);
                int newCapacity = count < converted ? converted : count;
                long table = memory.read64(allocator);
                long newBuffer = calls.allocate08(memory.read64(table + 8), allocator,
                        Integer.toUnsignedLong(newCapacity) << 2, 4, 0xb2ef9e);
                long oldPointer = memory.read64(destination);
                calls.copy4226860(newBuffer, oldPointer, 0, 0xb2efad);
                calls.copy4226860(newBuffer, sourceBegin, sourceBytes, 0xb2efbb);
                long oldBytes = ((long) memory.read32(destination + 0xc)) << 2;
                oldPointer = memory.read64(destination);
                calls.copy4226860(newBuffer + (((long) count) << 2), oldPointer, oldBytes, 0xb2efd2);
                long currentAllocator = memory.read64(destination + 0x10);
                oldPointer = memory.read64(destination);
                table = memory.read64(currentAllocator);
                calls.release16(memory.read64(table + 0x10), currentAllocator, oldPointer, 4, 0xb2efe5);
                memory.write64(destination, newBuffer);
                memory.write32(destination + 0xc, count);
                memory.write32(destination + 8, newCapacity);
            } else {
                long pointer = memory.read64(destination);
                calls.copy4226860(pointer, sourceBegin, sourceBytes, 0xb2effe);
                long oldCount = memory.read32(destination + 0xc);
                long begin = memory.read64(destination);
                int total = (int) oldCount + count;
                long middle = begin + (oldCount << 2);
                memory.write32(destination + 0xc, total);
                long end = begin + (((long) total) << 2);
                if (begin != middle && middle != end) {
                    calls.reverse4220aa4(begin, middle, 0xb2f02d);
                    calls.reverse4220aa4(middle, end, 0xb2f038);
                    calls.reverse4220aa4(begin, end, 0xb2f043);
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
}
