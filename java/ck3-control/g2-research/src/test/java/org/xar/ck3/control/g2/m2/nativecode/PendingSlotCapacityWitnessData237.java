package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;

/** Script input contract only; no implementation or literal expected scene has been written here. */
public final class PendingSlotCapacityWitnessData237 {
    private PendingSlotCapacityWitnessData237() { }
    public record Cell(long address, int width, long value) { }
    /**
     * R8/R32/R64/W32/W64: address and value have their exact memory width, bytes must be zero.
     * RESERVE: address=known RCX, value=unsigned EDX, bytes=zero.
     * SET: address=known RCX, value=unsigned EDX, bytes=raw R8 byte count.
     * effects are controlled callback INPUT only, applied after its ordered argument check.
     */
    public record Step(String kind, long address, long value, long bytes, List<Cell> effects) { }
    public record Scene(String name, long tableAddress, int requestedCapacity, boolean expectedAl,
                        List<Cell> initial, List<Step> steps, List<Cell> finalCells) { }
}
