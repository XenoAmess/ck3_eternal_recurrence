package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

public final class PendingCopySse4226860 {
    private PendingCopySse4226860() { }

    public static void copy(Copy4226860Api.Memory memory, long destination, long source, long bytes, long moduleBase) {
        // Entry: 4226CB6 (SSE path, bytes > 32, forward copy)
        // Initial snapshots: read head and tail 128-bit values
        Bits128 xmm0 = memory.read128(source);
        Bits128 xmm5 = memory.read128(source + bytes - 16);

        // Preserve ORIGINAL destination for final head write
        long originalDestination = destination;

        // Alignment adjustment: only if bytes > 128
        if (Long.compareUnsigned(bytes, 128L) > 0) {
            long r9 = destination & 0xF;
            // Actual alignment also advances an already aligned destination by16.
            long delta = r9 - 16;
            destination -= delta;
            source -= delta;
            bytes += delta;
        }

        // Bulk loop: process 128 bytes at a time
        // Actual conditional JBE <= 128 skips loop initially if bytes <= 128
        // If bytes > 128, enter do-while loop
        if (Long.compareUnsigned(bytes, 128L) > 0) {
            do {
                // Exact eight snapshots groups: 4 reads + 4 writes, then 4 reads + 4 writes
                Bits128 xmm1 = memory.read128(source);
                Bits128 xmm2 = memory.read128(source + 16);
                Bits128 xmm3 = memory.read128(source + 32);
                Bits128 xmm4 = memory.read128(source + 48);
                memory.write128(destination, xmm1);
                memory.write128(destination + 16, xmm2);
                memory.write128(destination + 32, xmm3);
                memory.write128(destination + 48, xmm4);

                Bits128 xmm1b = memory.read128(source + 64);
                Bits128 xmm2b = memory.read128(source + 80);
                Bits128 xmm3b = memory.read128(source + 96);
                Bits128 xmm4b = memory.read128(source + 112);
                memory.write128(destination + 64, xmm1b);
                memory.write128(destination + 80, xmm2b);
                memory.write128(destination + 96, xmm3b);
                memory.write128(destination + 112, xmm4b);

                destination += 128;
                source += 128;
                bytes -= 128;
            } while (Long.compareUnsigned(bytes, 128L) >= 0);
        }

        // Tail handling: rounded = (remaining + 15) & ~15L
        long rounded = (bytes + 15) & ~15L;
        long index = rounded >>> 4;

        // Read jump table entry: table at RVA 0x6090088, each entry is 4 bytes (DWORD)
        long tableEntryAddress = moduleBase + 0x6090088 + index * 4;
        int tableValue = memory.read32(tableEntryAddress);
        long targetAddress = (tableValue & 0xFFFFFFFFL);

        // Dispatch based on actual table targets (fallthrough ascending addresses)
        // index 0 -> 0x4226de2: writes ONLY captured head to ORIGINALD
        // index 1 -> 0x4226ddb: writes captured tail to CURRENTD+remaining-16, then head to ORIGINALD
        // index 2 -> 0x4226dcd: starts read/write at CURRENT(S/D)+rounded-32, then tail/head
        // index 3 -> 0x4226dbf: starts rounded-48
        // index 4 -> 0x4226db1: starts rounded-64
        // index 5 -> 0x4226da3: starts rounded-80
        // index 6 -> 0x4226d95: starts rounded-96
        // index 7 -> 0x4226d87: starts rounded-112
        // index 8 -> 0x4226d79: starts rounded-128

        // The assembly shows specific offsets for each chunk in the tail handling
        // We follow the exact write sequence from the assembly

        // For index 0 (target 0x4226de2): only write head
        if (targetAddress == 0x4226de2L) {
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 1 (target 0x4226ddb): write tail then head
        if (targetAddress == 0x4226ddbL) {
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 2 (target 0x4226dcd): write chunk at rounded-32, then tail, then head
        if (targetAddress == 0x4226dcdL) {
            Bits128 chunk = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 3 (target 0x4226dbf): write chunks at rounded-48, rounded-32, then tail, then head
        if (targetAddress == 0x4226dbfL) {
            Bits128 chunk1 = memory.read128(source + rounded - 48);
            memory.write128(destination + rounded - 48, chunk1);
            Bits128 chunk2 = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk2);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 4 (target 0x4226db1): write chunks at rounded-64, rounded-48, rounded-32, then tail, then head
        if (targetAddress == 0x4226db1L) {
            Bits128 chunk1 = memory.read128(source + rounded - 64);
            memory.write128(destination + rounded - 64, chunk1);
            Bits128 chunk2 = memory.read128(source + rounded - 48);
            memory.write128(destination + rounded - 48, chunk2);
            Bits128 chunk3 = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk3);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 5 (target 0x4226da3): write chunks at rounded-80, rounded-64, rounded-48, rounded-32, then tail, then head
        if (targetAddress == 0x4226da3L) {
            Bits128 chunk1 = memory.read128(source + rounded - 80);
            memory.write128(destination + rounded - 80, chunk1);
            Bits128 chunk2 = memory.read128(source + rounded - 64);
            memory.write128(destination + rounded - 64, chunk2);
            Bits128 chunk3 = memory.read128(source + rounded - 48);
            memory.write128(destination + rounded - 48, chunk3);
            Bits128 chunk4 = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk4);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 6 (target 0x4226d95): write chunks at rounded-96, rounded-80, rounded-64, rounded-48, rounded-32, then tail, then head
        if (targetAddress == 0x4226d95L) {
            Bits128 chunk1 = memory.read128(source + rounded - 96);
            memory.write128(destination + rounded - 96, chunk1);
            Bits128 chunk2 = memory.read128(source + rounded - 80);
            memory.write128(destination + rounded - 80, chunk2);
            Bits128 chunk3 = memory.read128(source + rounded - 64);
            memory.write128(destination + rounded - 64, chunk3);
            Bits128 chunk4 = memory.read128(source + rounded - 48);
            memory.write128(destination + rounded - 48, chunk4);
            Bits128 chunk5 = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk5);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 7 (target 0x4226d87): write chunks at rounded-112, rounded-96, rounded-80, rounded-64, rounded-48, rounded-32, then tail, then head
        if (targetAddress == 0x4226d87L) {
            Bits128 chunk1 = memory.read128(source + rounded - 112);
            memory.write128(destination + rounded - 112, chunk1);
            Bits128 chunk2 = memory.read128(source + rounded - 96);
            memory.write128(destination + rounded - 96, chunk2);
            Bits128 chunk3 = memory.read128(source + rounded - 80);
            memory.write128(destination + rounded - 80, chunk3);
            Bits128 chunk4 = memory.read128(source + rounded - 64);
            memory.write128(destination + rounded - 64, chunk4);
            Bits128 chunk5 = memory.read128(source + rounded - 48);
            memory.write128(destination + rounded - 48, chunk5);
            Bits128 chunk6 = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk6);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }

        // For index 8 (target 0x4226d79): write chunks at rounded-128, rounded-112, rounded-96, rounded-80, rounded-64, rounded-48, rounded-32, then tail, then head
        if (targetAddress == 0x4226d79L) {
            Bits128 chunk1 = memory.read128(source + rounded - 128);
            memory.write128(destination + rounded - 128, chunk1);
            Bits128 chunk2 = memory.read128(source + rounded - 112);
            memory.write128(destination + rounded - 112, chunk2);
            Bits128 chunk3 = memory.read128(source + rounded - 96);
            memory.write128(destination + rounded - 96, chunk3);
            Bits128 chunk4 = memory.read128(source + rounded - 80);
            memory.write128(destination + rounded - 80, chunk4);
            Bits128 chunk5 = memory.read128(source + rounded - 64);
            memory.write128(destination + rounded - 64, chunk5);
            Bits128 chunk6 = memory.read128(source + rounded - 48);
            memory.write128(destination + rounded - 48, chunk6);
            Bits128 chunk7 = memory.read128(source + rounded - 32);
            memory.write128(destination + rounded - 32, chunk7);
            memory.write128(destination + bytes - 16, xmm5);
            memory.write128(originalDestination, xmm0);
            return;
        }
        throw new UnsupportedOperationException("UNKNOWN_SSE_TAIL_LABEL");
    }
}