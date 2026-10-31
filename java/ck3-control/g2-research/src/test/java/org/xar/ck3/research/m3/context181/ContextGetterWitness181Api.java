package org.xar.ck3.research.m3.context181;
import java.util.List;
import org.xar.ck3.research.m3.context181.ContextGetter181Api.Input;
/** Pure source-derived scripted DATA; expected output must not be obtained from the target implementation. */
public final class ContextGetterWitness181Api {
    private ContextGetterWitness181Api() { }
    public enum Kind { R8, R32, R64, R128, W8, W32, W64, W128, CALL }
    /** Width1/4/8 consumes low bits; width16 consumes low and high. */
    public record Cell(long address, int width, long low, long high) { }
    /** CALL arguments are [siteRva,unsignedECX,descriptor,unsignedR8D,unsignedR9D]; effects are opaque input changes. */
    public record Step(Kind kind, long address, long low, long high, List<Long> arguments, long returned, List<Cell> effects) { }
    public record Scene(String name, Input input, List<Cell> initial, List<Step> steps, long expectedReturn, List<Cell> finalCells) { }
}
