package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

public final class PendingCopyAvx4226860 {
    private PendingCopyAvx4226860() { }

    public static void copy(Copy4226860Api.Memory memory, long destination, long source, long bytes, long moduleBase) {
        long rax = destination;
        long rdx = source;
        long rcx = destination;
        long r8 = bytes;

        // Initial head snapshot (read256 at original source)
        Copy4226860Api.Bits256 head256 = memory.read256(rdx);
        // Initial tail snapshot (read256 at original source + bytes - 32)
        Copy4226860Api.Bits256 tail256 = memory.read256(rdx + r8 - 32);

        // Alignment adjustment only if original unsigned bytes > 256
        if (Long.compareUnsigned(r8, 256) > 0) {
            long r9 = (rcx & 31) - 32;
            rcx -= r9;
            rdx -= r9;
            r8 += r9;

            // Second check: if adjusted unsigned r8 <= 256, jump directly to tail handling
            if (Long.compareUnsigned(r8, 256) <= 0) {
                tail(memory, rax, rcx, rdx, r8, moduleBase, head256, tail256, false);
            } else {
                // Streaming vs Cached branch
                if (Long.compareUnsigned(r8, 0x180000) > 0) {
                    // Streaming branch (NT)
                    while (Long.compareUnsigned(r8, 256) >= 0) {
                        // Load 4 x 256-bit values
                        Copy4226860Api.Bits256 ymm1 = memory.read256(rdx);
                        Copy4226860Api.Bits256 ymm2 = memory.read256(rdx + 32);
                        Copy4226860Api.Bits256 ymm3 = memory.read256(rdx + 64);
                        Copy4226860Api.Bits256 ymm4 = memory.read256(rdx + 96);

                        // Write 4 x 256-bit values (NT)
                        memory.write256(rcx, ymm1);
                        memory.write256(rcx + 32, ymm2);
                        memory.write256(rcx + 64, ymm3);
                        memory.write256(rcx + 96, ymm4);

                        // Next 4 loads + 4 writes
                        ymm1 = memory.read256(rdx + 128);
                        ymm2 = memory.read256(rdx + 160);
                        ymm3 = memory.read256(rdx + 192);
                        ymm4 = memory.read256(rdx + 224);

                        memory.write256(rcx + 128, ymm1);
                        memory.write256(rcx + 160, ymm2);
                        memory.write256(rcx + 192, ymm3);
                        memory.write256(rcx + 224, ymm4);

                        rcx += 256;
                        rdx += 256;
                        r8 -= 256;
                    }

                    // Tail handling for streaming (NT table 6090064)
                    tail(memory, rax, rcx, rdx, r8, moduleBase, head256, tail256, true);

                    memory.storeFence();
                } else {
                    // Cached branch (DQU)
                    while (Long.compareUnsigned(r8, 256) >= 0) {
                        // Load 4 x 256-bit values
                        Copy4226860Api.Bits256 ymm1 = memory.read256(rdx);
                        Copy4226860Api.Bits256 ymm2 = memory.read256(rdx + 32);
                        Copy4226860Api.Bits256 ymm3 = memory.read256(rdx + 64);
                        Copy4226860Api.Bits256 ymm4 = memory.read256(rdx + 96);

                        // Write 4 x 256-bit values (DQU)
                        memory.write256(rcx, ymm1);
                        memory.write256(rcx + 32, ymm2);
                        memory.write256(rcx + 64, ymm3);
                        memory.write256(rcx + 96, ymm4);

                        // Next 4 loads + 4 writes
                        ymm1 = memory.read256(rdx + 128);
                        ymm2 = memory.read256(rdx + 160);
                        ymm3 = memory.read256(rdx + 192);
                        ymm4 = memory.read256(rdx + 224);

                        memory.write256(rcx + 128, ymm1);
                        memory.write256(rcx + 160, ymm2);
                        memory.write256(rcx + 192, ymm3);
                        memory.write256(rcx + 224, ymm4);

                        rcx += 256;
                        rdx += 256;
                        r8 -= 256;
                    }

                    // Tail handling for cached (table 6090040)
                    tail(memory, rax, rcx, rdx, r8, moduleBase, head256, tail256, false);
                }
            }
        } else {
            // Original bytes <= 256: direct tail handling without alignment adjustment
            tail(memory, rax, rcx, rdx, r8, moduleBase, head256, tail256, false);
        }
    }

    /** Owner actual tail labels/order; R2 reversed allthree switches. */
    @SuppressWarnings("fallthrough")
    private static void tail(Copy4226860Api.Memory memory,long originalDestination,long destination,
            long source,long remaining,long moduleBase,Copy4226860Api.Bits256 head,
            Copy4226860Api.Bits256 capturedTail,boolean streaming) {
        long rounded = (remaining + 31L) & ~31L;
        long tableRva = streaming ? 0x6090064L : 0x6090040L;
        int target = memory.read32(moduleBase + tableRva + (rounded >>> 5) * 4L);
        if (streaming) {
            switch (target) {
                case 0x4226c05:
                    memory.write256(destination + rounded - 256L, memory.read256(source + rounded - 256L));
                case 0x4226c19:
                    memory.write256(destination + rounded - 224L, memory.read256(source + rounded - 224L));
                case 0x4226c2d:
                    memory.write256(destination + rounded - 192L, memory.read256(source + rounded - 192L));
                case 0x4226c41:
                    memory.write256(destination + rounded - 160L, memory.read256(source + rounded - 160L));
                case 0x4226c55:
                    memory.write256(destination + rounded - 128L, memory.read256(source + rounded - 128L));
                case 0x4226c63:
                    memory.write256(destination + rounded - 96L, memory.read256(source + rounded - 96L));
                case 0x4226c71:
                    memory.write256(destination + rounded - 64L, memory.read256(source + rounded - 64L));
                case 0x4226c7f:
                    memory.write256(destination + remaining - 32L, capturedTail);
                case 0x4226c86:
                    memory.write256(originalDestination, head);
                    return;
                default:
                    throw new UnsupportedOperationException("UNKNOWN_AVX_TAIL_LABEL");
            }
        } else {
            switch (target) {
                case 0x4226ad5:
                    memory.write256(destination + rounded - 256L, memory.read256(source + rounded - 256L));
                case 0x4226ae9:
                    memory.write256(destination + rounded - 224L, memory.read256(source + rounded - 224L));
                case 0x4226afd:
                    memory.write256(destination + rounded - 192L, memory.read256(source + rounded - 192L));
                case 0x4226b11:
                    memory.write256(destination + rounded - 160L, memory.read256(source + rounded - 160L));
                case 0x4226b25:
                    memory.write256(destination + rounded - 128L, memory.read256(source + rounded - 128L));
                case 0x4226b33:
                    memory.write256(destination + rounded - 96L, memory.read256(source + rounded - 96L));
                case 0x4226b41:
                    memory.write256(destination + rounded - 64L, memory.read256(source + rounded - 64L));
                case 0x4226b4f:
                    memory.write256(destination + remaining - 32L, capturedTail);
                case 0x4226b56:
                    memory.write256(originalDestination, head);
                    return;
                default:
                    throw new UnsupportedOperationException("UNKNOWN_AVX_TAIL_LABEL");
            }
        }
    }
}