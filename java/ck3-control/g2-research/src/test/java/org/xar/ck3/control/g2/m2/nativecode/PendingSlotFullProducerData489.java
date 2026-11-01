package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Shape only; no recipe seeds, expected events, target algorithm or oracle. */
public final class PendingSlotFullProducerData489 {
    private PendingSlotFullProducerData489() { }
    /** Width is exactly 1, 4 or 8 bytes. Low-width values are unsigned. */
    public record Cell(int widthBytes, long addressBits, long valueBits) { }
    public sealed interface Step permits Read, Write, Invoke { }
    /** One logged exact-width observation; result must come from actual backing bytes. */
    public record Read(int widthBytes, long addressBits, long valueBits) implements Step { }
    /** One logged exact-width store. */
    public record Write(int widthBytes, long addressBits, long valueBits) implements Step { }
    /** Effects must also occur as the immediately following ordinary Write steps. */
    public record Invoke(FullSlotProducer479Api.CallFrame frame,
            FullCopy437Api.CallResult result, List<Write> effects) implements Step { }
    /** Initial/final cells are unlogged; steps share one global cursor. */
    public record Scene(String name, GovernmentCrtBoundary185Api.Entry entry,
            boolean directionFlagSet, List<Cell> initialMemory, List<Step> steps,
            FullCopy437Api.CallResult expectedResult, List<Cell> finalMemory) { }
}
