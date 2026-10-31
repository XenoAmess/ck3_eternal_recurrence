package org.xar.ck3.control.g2.m2.nativecode;

/** Complete227 normal880340, actual103 CALL3727F0D; explicitallocator/copyports. */
public final class PendingQueueAppend880340 {
    private PendingQueueAppend880340() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        void write32(long address,int value);
        void write64(long address,long value);
    }
    public interface Calls {
        long allocate(Memory memory,long target,long rcx,long rdx,int r8d);
        void release(Memory memory,long target,long rcx,long rdx,int r8d);
        void copy4226860(Memory memory,long rcx,long rdx,long r8);
    }
    public static long append(Memory memory,Calls calls,long container,long elementPointer,long moduleBase) {
        // 1. Read count and capacity (signed 32-bit)
        int count = memory.read32(container + 0xC);
        int capacity = memory.read32(container + 0x8);

        if (count != capacity) {
            // Non-growth path
            // Read base and element value
            long base = memory.read64(container);
            long elemVal = memory.read64(elementPointer);

            // Write element at base + count * 8
            memory.write64(base + ((long)count << 3), elemVal);

            // Increment count (read-modify-write)
            int newCount = memory.read32(container + 0xC) + 1;
            memory.write32(container + 0xC, newCount);

            // Fresh reads for return calculation
            int freshCount = memory.read32(container + 0xC);
            long freshBase = memory.read64(container);

            // Return freshBase + (freshCount - 1) * 8
            return freshBase + ((long)(freshCount - 1) << 3);
        } else {
            // Growth path
            // Read allocator
            long allocator = memory.read64(container + 0x10);

            // Read factor from moduleBase + 0x49F64F0
            long factorAddr = moduleBase + 0x49F64F0L;
            int factorBits = memory.read32(factorAddr);
            float factor = Float.intBitsToFloat(factorBits);

            // Calculate proposed capacity
            int newCount = count + 1;
            float capFloat = (float)capacity;
            float mulResult = capFloat * factor;

            // CVTTSS2SI emulation: NaN or out of range -> INT_MIN
            int converted;
            if (Float.isNaN(mulResult) || mulResult >= 2147483648.0f || mulResult < -2147483648.0f) {
                converted = Integer.MIN_VALUE;
            } else {
                converted = (int)mulResult;
            }

            int proposed = Math.max(newCount, converted);

            // Allocate
            long vptr = memory.read64(allocator);
            long allocTarget = memory.read64(vptr + 8);
            long size = Integer.toUnsignedLong(proposed) << 3;
            long newBuffer = calls.allocate(memory, allocTarget, allocator, size, 8);

            // Post-alloc fresh count
            int postCount = memory.read32(container + 0xC);

            // Read element and write to new buffer
            long elemVal = memory.read64(elementPointer);
            memory.write64(newBuffer + ((long)postCount << 3), elemVal);

            // Copy old buffer if needed
            int freshCount = memory.read32(container + 0xC);
            if (freshCount > 0) {
                long oldBuffer = memory.read64(container);
                calls.copy4226860(memory, newBuffer, oldBuffer, ((long)freshCount << 3));
            }

            // Release old buffer
            long freshAllocator = memory.read64(container + 0x10);
            long oldBuffer = memory.read64(container);
            long freshVptr = memory.read64(freshAllocator);
            long freeTarget = memory.read64(freshVptr + 16);
            calls.release(memory, freeTarget, freshAllocator, oldBuffer, 8);

            // Publish new state
            memory.write32(container + 0x8, proposed);
            memory.write64(container, newBuffer);
            memory.write32(container + 0xC, newCount);

            // Return newBuffer + (newCount - 1) * 8
            return newBuffer + ((long)(newCount - 1) << 3);
        }
    }
}