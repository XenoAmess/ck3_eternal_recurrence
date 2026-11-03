package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

/**
 * Model iteration with owner assignment repairs for the SSE128 block [4220B1E, 4220B42).
 * Implements ONLY the source instructions in this range. Does not execute prologue, calls, loops, or FP.
 */
public final class ReverseSseStep641 {
    private ReverseSseStep641() { }

    /**
     * Executes one iteration of the reverse shuffle block.
     * @param r Current registers.
     * @param memory Owned memory view.
     */
    public static void step(Registers r, FullCopy437Api.Memory memory) {
        Objects.requireNonNull(r);
        Objects.requireNonNull(memory);

        // 4220B1E: movdqu xmm0, xmmword ptr [r8]
        r.x0 = memory.read128(r.r8);

        // 4220B23: sub rdx, 0x10
        r.rdx -= 0x10;

        // 4220B27: pshufd xmm2, xmm0, 0x1b
        // 0x1B = 00011011b -> indices: 3, 2, 1, 0 (reverse order)
        r.x2 = reverseDwords(r.x0);

        // 4220B2C: movdqu xmm1, xmmword ptr [rdx]
        r.x1 = memory.read128(r.rdx);

        // 4220B30: pshufd xmm0, xmm1, 0x1b
        r.x0 = reverseDwords(r.x1);

        // 4220B35: movdqu xmmword ptr [r8], xmm0
        memory.write128(r.r8, r.x0);

        // 4220B3A: add r8, 0x10
        r.r8 += 0x10;

        // 4220B3E: movdqu xmmword ptr [rdx], xmm2
        memory.write128(r.rdx, r.x2);
    }

    /**
     * Reverses the order of the four 32-bit DWORDs in a Bits128 value.
     * Input:  [D0, D1, D2, D3] (low to high)
     * Output: [D3, D2, D1, D0] (low to high)
     */
    private static Bits128 reverseDwords(Bits128 v) {
        long low = v.lowBits();
        long high = v.highBits();

        // Extract DWORDs
        long d0 = low & 0xFFFFFFFFL;
        long d1 = (low >>> 32) & 0xFFFFFFFFL;
        long d2 = high & 0xFFFFFFFFL;
        long d3 = (high >>> 32) & 0xFFFFFFFFL;

        // Reconstruct in reverse order: new low = [d3, d2], new high = [d1, d0]
        long newLow = (d2 << 32) | d3;
        long newHigh = (d0 << 32) | d1;

        return new Bits128(newLow, newHigh);
    }
}