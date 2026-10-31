package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Finite source-derived DATA for the complete127B normal path; no target-produced expected values. */
public final class PendingContextChildWitness259Api {
    private PendingContextChildWitness259Api() { }
    public enum Kind { R64, W32, W64, CALL10, CALL20 }
    public record Cell(long address, int width, long value) { }
    /** Memory events have empty args/effects. CALL args=[target,RCX,RDX,R8unsigned32or64], address/value zero. */
    public record Step(Kind kind, long address, long value, List<Long> arguments, List<Cell> effects) { }
    public record Scene(String name, long receiver, long moduleBase, List<Cell> initial, List<Step> steps,
            long expectedReturn, List<Cell> finalCells) { }
}
