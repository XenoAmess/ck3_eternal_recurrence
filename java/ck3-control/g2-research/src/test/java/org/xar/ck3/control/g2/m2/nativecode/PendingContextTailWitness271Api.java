package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
public final class PendingContextTailWitness271Api {
    private PendingContextTailWitness271Api() { }
    public enum Kind { R8, R64, W64, HELPER, VIRTUAL }
    public record Cell(long address, int width, long value) { }
    /** HELPER args=[RCX,RDX], VIRTUAL args=[target,RCX,RDX,R8]; memory events have empty args/effects. */
    public record Step(Kind kind, long address, long value, List<Long> arguments, long returned, List<Cell> effects) { }
    public record Scene(String name, long destination, long source, List<Cell> initial, List<Step> steps,
            long expectedReturn, List<Cell> finalCells) { }
}
