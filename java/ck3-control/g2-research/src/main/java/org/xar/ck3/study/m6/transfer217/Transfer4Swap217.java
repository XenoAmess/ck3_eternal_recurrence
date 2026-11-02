package org.xar.ck3.study.m6.transfer217;

import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Budget;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Calls;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Input;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Memory;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Operations;

/** B2EDF0 normal helper. Its volatile RAX has no promised return value in this logical API. */
public final class Transfer4Swap217 {
    private Transfer4Swap217() { }

    public static void execute(Input input, Memory memory, Calls calls, Budget budget, Operations operations) {
        budget.step();
        long destination = input.destinationRaw64();
        long source = input.sourceRaw64();
        long sourceAllocator = memory.read64(source + 0x10);
        if (memory.read64(destination + 0x10) == sourceAllocator) {
            long destinationPointer = memory.read64(destination);
            long sourcePointer = memory.read64(source);
            memory.write64(destination, sourcePointer);
            memory.write64(source, destinationPointer);
            int destinationCount = memory.read32(destination + 0xc);
            int sourceCount = memory.read32(source + 0xc);
            memory.write32(destination + 0xc, sourceCount);
            memory.write32(source + 0xc, destinationCount);
            int destinationCapacity = memory.read32(destination + 8);
            int sourceCapacity = memory.read32(source + 8);
            memory.write32(destination + 8, sourceCapacity);
            memory.write32(source + 8, destinationCapacity);
            return;
        }
        int sourceCount = memory.read32(source + 0xc);
        int destinationCount = memory.read32(destination + 0xc);
        long first = sourceCount < destinationCount ? source : destination;
        long second = sourceCount >= destinationCount ? source : destination;
        long frame = input.frameRaw64();
        long temporary = frame + 0x20;
        memory.write64(frame + 0x40, input.imageBaseRaw64() + 0x44bbb10L);
        memory.write64(frame + 0x448, input.imageBaseRaw64() + 0x54de268L);
        memory.write64(temporary, 0);
        memory.write64(temporary + 8, 0);
        memory.write64(temporary + 0x10, frame + 0x40);
        long childFrame = frame - 0x50;
        operations.move(new Input(temporary, first, input.imageBaseRaw64(), childFrame), memory, calls, budget);
        operations.move(new Input(first, second, input.imageBaseRaw64(), childFrame), memory, calls, budget);
        operations.move(new Input(second, temporary, input.imageBaseRaw64(), childFrame), memory, calls, budget);
        long temporaryPointer = memory.read64(temporary);
        if (temporaryPointer != 0) {
            memory.write32(temporary + 0xc, 0);
            long allocator = memory.read64(temporary + 0x10);
            long table = memory.read64(allocator);
            calls.release16(memory.read64(table + 0x10), allocator, temporaryPointer, 4, 0xb2eebb);
        }
    }
}
