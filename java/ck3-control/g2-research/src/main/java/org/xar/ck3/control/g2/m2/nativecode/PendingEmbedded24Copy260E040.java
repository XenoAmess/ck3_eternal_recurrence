package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Complete251 normal260E040, actual233 CALL373ADAE, inline24-byte copies. */
public final class PendingEmbedded24Copy260E040 {
    private PendingEmbedded24Copy260E040() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        Bits128 read128(long address);
        void write32(long address, int value);
        void write64(long address, long value);
        void write128(long address, Bits128 value);
    }
    public interface Calls {
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
    }
    public static long copy(Memory memory, Calls calls, long destination, long source) {
        if (destination == source) {
            return destination;
        }

        int ebx = memory.read32(source + 0xC);
        long rdi = memory.read64(source);

        memory.write32(destination + 0xC, 0);

        if (ebx > 0 && ebx > memory.read32(destination + 0x8)) {
            long allocator = memory.read64(destination + 0x10);
            long vptr = memory.read64(allocator);
            long target = memory.read64(vptr + 0x8);
            long rdx = Integer.toUnsignedLong(ebx) * 24L;
            int r8d = 8;

            long newBuffer = calls.allocate(memory, target, allocator, rdx, r8d);

            int oldCount = memory.read32(destination + 0xC);

            if (oldCount > 0) {
                long oldBase = memory.read64(destination);
                long srcPtr = oldBase;
                long dstPtr = newBuffer;
                for (int i = 0; i < oldCount; i++) {
                    Bits128 xmm0 = memory.read128(srcPtr);
                    memory.write128(dstPtr, xmm0);
                    long xmm1 = memory.read64(srcPtr + 0x10);
                    memory.write64(dstPtr + 0x10, xmm1);
                    srcPtr += 24;
                    dstPtr += 24;
                }
            }

            long freshAllocator = memory.read64(destination + 0x10);
            long freshBase = memory.read64(destination);
            long freshVptr = memory.read64(freshAllocator);
            long freshTarget = memory.read64(freshVptr + 0x10);
            calls.release(memory, freshTarget, freshAllocator, freshBase, 8);

            memory.write64(destination, newBuffer);
            memory.write32(destination + 0x8, ebx);
            memory.write32(destination + 0xC, ebx);

            long finalBase = memory.read64(destination);
            long srcPtr = rdi;
            long dstPtr = finalBase;
            for (int i = 0; i < ebx; i++) {
                Bits128 xmm0 = memory.read128(srcPtr);
                memory.write128(dstPtr, xmm0);
                long xmm1 = memory.read64(srcPtr + 0x10);
                memory.write64(dstPtr + 0x10, xmm1);
                srcPtr += 24;
                dstPtr += 24;
            }
        } else {
            memory.write32(destination + 0xC, ebx);
            if (ebx > 0) {
                long dstBase = memory.read64(destination);
                long srcPtr = rdi;
                long dstPtr = dstBase;
                for (int i = 0; i < ebx; i++) {
                    Bits128 xmm0 = memory.read128(srcPtr);
                    memory.write128(dstPtr, xmm0);
                    long xmm1 = memory.read64(srcPtr + 0x10);
                    memory.write64(dstPtr + 0x10, xmm1);
                    srcPtr += 24;
                    dstPtr += 24;
                }
            }
        }

        return destination;
    }
}