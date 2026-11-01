package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/** Pure shape only: no recipe seeds, expected trace/state or subject algorithm. */
public final class PendingContextFullData507 {
    private PendingContextFullData507() { }
    /** Width4/8 scalars use Bits128(lowRawBits,0); width4 low is unsigned. Width16 uses both full raw limbs. */
    public record Cell(int widthBytes, long addressBits, Bits128 valueBits) { }
    public sealed interface Step permits Read, Write, Invoke { }
    public record Read(int widthBytes, long addressBits, Bits128 valueBits) implements Step { }
    public record Write(int widthBytes, long addressBits, Bits128 valueBits) implements Step { }
    /** Effects also occur as immediately following Write steps and update the same logged RAM. */
    public record Invoke(FullContext493Api.CallFrame frame,
            FullCopy437Api.CallResult result, List<Write> effects) implements Step { }
    public record Scene(String name, GovernmentCrtBoundary185Api.Entry entry,
            boolean directionFlagSet, List<Cell> initialMemory, List<Step> steps,
            FullCopy437Api.CallResult expectedResult, List<Cell> finalMemory) { }
}
