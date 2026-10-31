package org.xar.ck3.research.m3.map191;

import java.util.List;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Input;

/** Pure controlled input and independently source-derived expectations; no target execution. */
public final class MapInsertWitness191Api {
    private MapInsertWitness191Api() { }
    public enum Kind { R8, R32, R64, R128, W8, W32, W64, W128,
        EQUAL, INSERT_SLOT, REHASH, INSERT_OTHER, DESTROY, CAPACITY, RESERVE, OVERFLOW, TERMINAL }
    /** width is 1/4/8/16; low-address little endian, high used only at width16. */
    public record Cell(long address, int width, long low, long high) { }
    /** Memory op: address/low/high. Port: address=siteRva, arguments in declared order, returned=EAX bits where applicable. */
    public record Step(Kind kind, long address, long low, long high, List<Long> arguments,
                       long returned, List<Cell> effects) { }
    public record Scene(String name, Input input, List<Cell> initial, List<Step> steps,
                        long expectedReturn, List<Cell> finalCells) { }
}
