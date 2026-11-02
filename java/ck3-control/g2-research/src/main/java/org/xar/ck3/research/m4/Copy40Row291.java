package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

public final class Copy40Row291 {
    private Copy40Row291() { }

    public record Result(Bits128 xmm0, Bits128 xmm1) { }

    public static Result transfer(GovernmentCrtBoundary185Api.Memory memory, long sourceBits, long destinationBits) {
        Bits128 first = memory.read128(sourceBits);
        memory.write128(destinationBits, first);
        Bits128 second = memory.read128(sourceBits + 0x10L);
        memory.write128(destinationBits + 0x10L, second);
        long qword = memory.readQword(sourceBits + 0x20L);
        memory.writeQword(destinationBits + 0x20L, qword);
        Bits128 legacyXmm0 = new Bits128(qword, 0L);
        return new Result(legacyXmm0, second);
    }
}