package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Pure literal fixture data and mechanical bank factories; no target algorithm. */
public final class EmbeddedElementsData578 {
    private EmbeddedElementsData578() { }
    public sealed interface Step permits Read, Write, Invoke, Budget { }
    public record Cell(int widthBytes, long addressBits, long valueBits) { }
    public record Read(int widthBytes, long addressBits, long valueBits) implements Step { }
    public record Write(int widthBytes, long addressBits, long valueBits) implements Step { }
    public record Invoke(EmbeddedElements578Api.CallFrame frame, FullCopy437Api.CallResult result,
                         List<Cell> effects) implements Step {
        public Invoke { Objects.requireNonNull(frame); Objects.requireNonNull(result); effects=List.copyOf(effects); }
    }
    public record Budget(long headerRva, long guardBits, boolean stop) implements Step { }
    public record Scene(String name, GovernmentCrtBoundary185Api.Entry entry, boolean df,
                        List<Cell> initial, List<Step> steps, FullCopy437Api.CallResult expected,
                        boolean stopped, List<Cell> finalCells) {
        public Scene { Objects.requireNonNull(name);Objects.requireNonNull(entry);
            initial=List.copyOf(initial);steps=List.copyOf(steps);finalCells=List.copyOf(finalCells);
            if (stopped==(expected!=null)) throw new IllegalArgumentException("Outcome"); }
    }
    public static VolatileBits v(long seed) {
        return new VolatileBits(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,
            new Bits128(seed+0x10,seed+0x11),new Bits128(seed+0x20,seed+0x21),
            new Bits128(seed+0x30,seed+0x31),new Bits128(seed+0x40,seed+0x41),
            new Bits128(seed+0x50,seed+0x51),new Bits128(seed+0x60,seed+0x61));
    }
    public static NonvolatileBits n(long seed) {
        return new NonvolatileBits(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,
            new Bits128(seed+8,seed+9));
    }
}
