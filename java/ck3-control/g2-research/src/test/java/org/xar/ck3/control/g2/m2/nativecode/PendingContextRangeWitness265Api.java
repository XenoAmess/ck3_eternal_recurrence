package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
/** Pure finite DATA; fields represent controlled storage/opaque effects, never target-produced expectations. */
public final class PendingContextRangeWitness265Api {
    private PendingContextRangeWitness265Api() { }
    public enum Kind { R32, R64, W32, W64, ALLOCATE, RELEASE, COPY, FINALIZE }
    public record Cell(long address, int width, long value) { }
    /** Memory events use address/value and empty args/effects; allocate/release args have4long, copy/finalize3. */
    public record Step(Kind kind, long address, long value, List<Long> arguments, long returned, List<Cell> effects) { }
    public record Scene(String name, PendingContextRangeInsertBCB7C0.Input input, List<Cell> initial,
            List<Step> steps, List<Cell> finalCells) { }
}
