package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWitnessData237.Cell;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWitnessData237.Scene;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWitnessData237.Step;

/** Four owner ASM-derived literals; no target implementation or run result was read. */
public final class PendingSlotCapacityWitnessBook237 {
    private static final long T = 0x8100000000001000L;
    private static final long OLD = 0x8200000000002000L, BASE = 0x8300000000002000L;
    private static final long OCCUPIED = 0xF100000000000001L, END = 0x00FFFFFFL;
    private PendingSlotCapacityWitnessBook237() { }
    private static Cell c(long address, int width, long value) { return new Cell(address, width, value); }
    private static Step e(String kind, long address, long value) { return new Step(kind, address, value, 0, List.of()); }
    private static Step r8(long address, long value) { return e("R8", address, value); }
    private static Step r32(long address, long value) { return e("R32", address, value); }
    private static Step r64(long address, long value) { return e("R64", address, value); }
    private static Step w32(long address, long value) { return e("W32", address, value); }
    private static Step w64(long address, long value) { return e("W64", address, value); }
    private static Step reserve(int requested, Cell... effects) {
        return new Step("RESERVE", T + 0x18, Integer.toUnsignedLong(requested), 0, List.of(effects));
    }
    private static Step set(long address, long count) { return new Step("SET", address, 0, count, List.of()); }
    private static Scene flag() {
        return new Scene("flag-short-circuit", T, 2, false,
                List.of(c(T + 0x40, 1, 0x80)), List.of(r8(T + 0x40, 0x80)), List.of(c(T + 0x40, 1, 0x80)));
    }
    private static Scene equalLimit() {
        return new Scene("equal-FFFFFF-early", T, 0x00FFFFFF, true,
                List.of(c(T + 0x40, 1, 0), c(T + 0x24, 4, END)),
                List.of(r8(T + 0x40, 0), r32(T + 0x24, END)), List.of(c(T + 0x24, 4, END)));
    }
    private static Scene emptyHead() {
        return new Scene("zero-to-two-empty-head", T, 2, true,
                List.of(c(T + 0x40, 1, 0), c(T + 0x24, 4, 0), c(T + 0x18, 8, OLD), c(T + 0x38, 4, END)),
                List.of(r8(T + 0x40, 0), r32(T + 0x24, 0), r32(T + 0x24, 0),
                    reserve(2, c(T + 0x18, 8, BASE)), r32(T + 0x24, 0), r64(T + 0x18, BASE), set(BASE, 0x20),
                    w32(T + 0x24, 2),
                    r64(T + 0x18, BASE), w32(BASE + 0x14, END), r64(T + 0x18, BASE), w64(BASE + 0x18, 0),
                    r64(T + 0x18, BASE), w32(BASE + 0x10, END),
                    r64(T + 0x18, BASE), w32(BASE + 0x4, END), r64(T + 0x18, BASE), w64(BASE + 0x8, 0),
                    r64(T + 0x18, BASE), w32(BASE + 0x14, 0), r64(T + 0x18, BASE), w32(BASE, 1),
                    r32(T + 0x38, END), w32(T + 0x38, 0)),
                List.of(c(T + 0x24, 4, 2), c(T + 0x18, 8, BASE), c(T + 0x38, 4, 0),
                    c(BASE, 4, 1), c(BASE + 0x4, 4, END), c(BASE + 0x8, 8, 0),
                    c(BASE + 0x10, 4, END), c(BASE + 0x14, 4, 0), c(BASE + 0x18, 8, 0)));
    }
    private static Scene existingHead() {
        return new Scene("two-to-three-tail-occupied-then-free", T, 3, true,
                List.of(c(T + 0x40, 1, 0), c(T + 0x24, 4, 2), c(T + 0x18, 8, OLD), c(T + 0x38, 4, 1)),
                List.of(r8(T + 0x40, 0), r32(T + 0x24, 2), r32(T + 0x24, 2),
                    reserve(3, c(T + 0x18, 8, BASE), c(BASE, 4, END), c(BASE + 0x4, 4, 0x7FFFFF), c(BASE + 0x8, 8, 0),
                        c(BASE + 0x10, 4, 0xABCD01), c(BASE + 0x14, 4, END), c(BASE + 0x18, 8, OCCUPIED)),
                    r32(T + 0x24, 2), r64(T + 0x18, BASE), set(BASE + 0x20, 0x10), w32(T + 0x24, 3),
                    r64(T + 0x18, BASE), w32(BASE + 0x24, END), r64(T + 0x18, BASE), w64(BASE + 0x28, 0),
                    r64(T + 0x18, BASE), w32(BASE + 0x20, END),
                    r32(T + 0x38, 1), r64(T + 0x18, BASE),
                    r64(BASE + 0x18, OCCUPIED), r64(BASE + 0x8, 0), r32(BASE, END),
                    w32(BASE, 2), r64(T + 0x18, BASE), w32(BASE + 0x24, 0)),
                List.of(c(T + 0x24, 4, 3), c(T + 0x18, 8, BASE), c(T + 0x38, 4, 1),
                    c(BASE, 4, 2), c(BASE + 0x4, 4, 0x7FFFFF), c(BASE + 0x8, 8, 0),
                    c(BASE + 0x10, 4, 0xABCD01), c(BASE + 0x14, 4, END), c(BASE + 0x18, 8, OCCUPIED),
                    c(BASE + 0x20, 4, END), c(BASE + 0x24, 4, 0), c(BASE + 0x28, 8, 0)));
    }
    public static List<Scene> scenes() { return List.of(flag(), equalLimit(), emptyHead(), existingHead()); }
}
