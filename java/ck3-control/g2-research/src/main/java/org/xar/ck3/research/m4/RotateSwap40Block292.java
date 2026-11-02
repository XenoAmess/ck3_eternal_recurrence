package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

public final class RotateSwap40Block292 {
    private RotateSwap40Block292() { }

    public record Result(long lowAfterBits, Bits128 xmm0, Bits128 xmm1, Bits128 xmm2, Bits128 xmm3, Bits128 xmm4) { }

    public static Result transfer(GovernmentCrtBoundary185Api.Memory memory, long lowBits, long highBits) {
        Bits128 xmm0 = memory.read128(highBits);
        Bits128 xmm3 = memory.read128(lowBits);
        Bits128 xmm4 = memory.read128(lowBits + 0x10L);
        long xmm2Low = memory.readQword(lowBits + 0x20L);
        Bits128 xmm2 = new Bits128(xmm2Low, 0L);
        memory.write128(lowBits, xmm0);
        Bits128 xmm1 = memory.read128(highBits + 0x10L);
        memory.write128(lowBits + 0x10L, xmm1);
        long xmm0Low = memory.readQword(highBits + 0x20L);
        xmm0 = new Bits128(xmm0Low, 0L);
        memory.writeQword(lowBits + 0x20L, xmm0Low);
        memory.write128(highBits, xmm3);
        memory.write128(highBits + 0x10L, xmm4);
        memory.writeQword(highBits + 0x20L, xmm2Low);
        return new Result(lowBits + 0x28L, xmm0, xmm1, xmm2, xmm3, xmm4);
    }
}