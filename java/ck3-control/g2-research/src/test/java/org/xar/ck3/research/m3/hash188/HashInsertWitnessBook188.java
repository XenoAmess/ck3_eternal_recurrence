package org.xar.ck3.research.m3.hash188;

import java.util.List;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Input;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Scratch;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Cell;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Kind;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Scene;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Step;

/** Independent finite literal observations derived only from the held C39C60 source. */
public final class HashInsertWitnessBook188 {
    private HashInsertWitnessBook188() { }

    public static List<Scene> scenes() {
        return List.of(occupiedEqual(), emptyCopy(), shortDisplacement());
    }

    private static Scene occupiedEqual() {
        long map = 0x0000001100001000L;
        long data = 0x0000002200002000L;
        long bucket = data + 0x50L;
        long output = 0x0000003300003000L;
        long descriptor = 0x0000004400004000L;
        long keyData = 0x8123456700006000L;
        long bucketData = 0x9234567800007000L;
        long keyCap = 0x8000000100000010L;
        long bucketCap = 0x8000000200000010L;
        return new Scene("occupied_heap_equal_low8_true",
            new Input(0x0000006600000000L, map, output, 0x80000002, descriptor,
                new Scratch(0x0000005500005000L)),
            List.of(c32(map + 0x14L, 3), c64(map + 8L, data), c8(bucket + 4L, 1),
                c64(descriptor + 0x18L, keyCap), c64(bucket + 0x20L, bucketCap),
                c64(bucket + 8L, bucketData), c64(descriptor, keyData)),
            List.of(
                m(Kind.R32, map + 0x14L, 3),
                m(Kind.R64, map + 8L, data),
                m(Kind.R8, bucket + 4L, 1),
                m(Kind.R64, descriptor + 0x18L, keyCap),
                m(Kind.R64, bucket + 0x20L, bucketCap),
                m(Kind.R64, bucket + 8L, bucketData),
                m(Kind.R64, descriptor, keyData),
                p(Kind.EQUAL, 0xC39CCAL, List.of(keyData, bucketData), 0x101L, List.of()),
                m(Kind.W64, output, bucket),
                m(Kind.W8, output + 8L, 0)),
            output, List.of(c64(output, bucket), c8(output + 8L, 0)));
    }

    private static Scene emptyCopy() {
        long map = 0x0000001200001000L;
        long data = 0x0000002300002000L;
        long bucket = data + 0x28L;
        long output = 0x0000003400003000L;
        long descriptor = 0x0000004500004000L;
        long copiedLow = 0x0123456789ABCDEFL;
        long copiedHigh = 0xFEDCBA9876543210L;
        long copiedLength = 0x0000000100000013L;
        long copiedCapacity = 0x0000000200000022L;
        return new Scene("empty_copy_effect_fresh_increment_wrap32",
            new Input(0x0000006700000000L, map, output, 0x80000001, descriptor,
                new Scratch(0x0000005600005000L)),
            List.of(c32(map + 0x14L, 7), c64(map + 8L, data), c8(bucket + 4L, 0),
                c8(map + 0x18L, 4), c32(map + 0x10L, 2), c32(map + 0x1CL, 0x3F800000L)),
            List.of(
                m(Kind.R32, map + 0x14L, 7),
                m(Kind.R64, map + 8L, data),
                m(Kind.R8, bucket + 4L, 0),
                m(Kind.R8, map + 0x18L, 4),
                m(Kind.R32, map + 0x10L, 2),
                m(Kind.R32, map + 0x1CL, 0x3F800000L),
                m(Kind.R8, bucket + 4L, 0),
                m(Kind.W32, bucket, 0x80000001L),
                m(Kind.W8, bucket + 4L, 1),
                p(Kind.COPY, 0xC39D27L, List.of(bucket + 8L, descriptor), 0,
                    List.of(c32(map + 0x10L, 0x7FFFFFFFL),
                        c128(bucket + 8L, copiedLow, copiedHigh),
                        c128(bucket + 0x18L, copiedLength, copiedCapacity))),
                m(Kind.R32, map + 0x10L, 0x7FFFFFFFL),
                m(Kind.W32, map + 0x10L, 0x80000000L),
                m(Kind.W64, output, bucket),
                m(Kind.W8, output + 8L, 1)),
            output,
            List.of(c64(output, bucket), c8(output + 8L, 1),
                c32(map + 0x10L, 0x80000000L), c32(bucket, 0x80000001L),
                c8(bucket + 4L, 1), c128(bucket + 8L, copiedLow, copiedHigh),
                c128(bucket + 0x18L, copiedLength, copiedCapacity)));
    }

    private static Scene shortDisplacement() {
        long map = 0x0000001300001000L;
        long data = 0x0000002400002000L;
        long chosen = data + 0x28L;
        long next = data + 0x50L;
        long output = 0x0000003500003000L;
        long descriptor = 0x0000004600004000L;
        long keyData = 0xA345678900007000L;
        long freshKeyLength = 0x0000000100000003L;
        long freshKeyCapacity = 0x8000000100000010L;
        long oldLow = 0x1111222233334444L;
        long oldHigh = 0x5555666677778888L;
        long oldLength = 0x0000000100000011L;
        long oldCapacity = 0x0000000200000022L;
        long assignedLow = 0x9999AAAABBBBCCCCL;
        long assignedHigh = 0xDDDDEEEEFFFF0001L;
        long assignedCapacity = 0x0000000300000040L;
        return new Scene("collision_short_move32_assign_fresh_count",
            new Input(0x0000006800000000L, map, output, 0x80000000, descriptor,
                new Scratch(0x0000005700005000L)),
            List.of(c32(map + 0x14L, 3), c64(map + 8L, data), c8(data + 4L, 1),
                c64(descriptor + 0x18L, 0xFL), c64(data + 0x20L, 0xFL),
                c8(chosen + 4L, 1), c8(map + 0x18L, 6), c32(map + 0x10L, 1),
                c32(map + 0x1CL, 0x3F800000L), c32(chosen, 0xF1234567L),
                c8(next + 4L, 0), c128(chosen + 8L, oldLow, oldHigh),
                c128(chosen + 0x18L, oldLength, oldCapacity)),
            List.of(
                m(Kind.R32, map + 0x14L, 3),
                m(Kind.R64, map + 8L, data),
                m(Kind.R8, data + 4L, 1),
                m(Kind.R64, descriptor + 0x18L, 0xFL),
                m(Kind.R64, data + 0x20L, 0xFL),
                p(Kind.EQUAL, 0xC39CCAL, List.of(descriptor, data + 8L), 0x100L,
                    List.of(c64(descriptor + 0x18L, freshKeyCapacity),
                        c64(descriptor + 0x10L, freshKeyLength), c64(descriptor, keyData))),
                m(Kind.R8, chosen + 4L, 1),
                m(Kind.R32, map + 0x14L, 3),
                m(Kind.R8, map + 0x18L, 6),
                m(Kind.R32, map + 0x10L, 1),
                m(Kind.R32, map + 0x1CL, 0x3F800000L),
                m(Kind.R8, chosen + 4L, 1),
                m(Kind.R32, chosen, 0xF1234567L),
                m(Kind.R8, next + 4L, 0),
                m(Kind.W32, next, 0xF1234567L),
                m(Kind.W8, next + 4L, 2),
                m(Kind.W64, next + 8L, 0),
                m(Kind.W64, next + 0x18L, 0),
                m(Kind.W64, next + 0x20L, 0),
                v(Kind.R128, chosen + 8L, oldLow, oldHigh),
                v(Kind.W128, next + 8L, oldLow, oldHigh),
                v(Kind.R128, chosen + 0x18L, oldLength, oldCapacity),
                v(Kind.W128, next + 0x18L, oldLength, oldCapacity),
                m(Kind.W64, chosen + 0x18L, 0),
                m(Kind.W64, chosen + 0x20L, 0xFL),
                m(Kind.W8, chosen + 8L, 0),
                m(Kind.W32, chosen, 0x80000000L),
                m(Kind.W8, chosen + 4L, 2),
                m(Kind.R64, descriptor + 0x18L, freshKeyCapacity),
                m(Kind.R64, descriptor + 0x10L, freshKeyLength),
                m(Kind.R64, descriptor, keyData),
                p(Kind.ASSIGN, 0xC39DA4L, List.of(chosen + 8L, keyData, freshKeyLength), 0,
                    List.of(c32(map + 0x10L, 0xFFFFFFFFL),
                        c128(chosen + 8L, assignedLow, assignedHigh),
                        c128(chosen + 0x18L, freshKeyLength, assignedCapacity))),
                m(Kind.R32, map + 0x10L, 0xFFFFFFFFL),
                m(Kind.W32, map + 0x10L, 0),
                m(Kind.W64, output, chosen),
                m(Kind.W8, output + 8L, 1)),
            output,
            List.of(c64(output, chosen), c8(output + 8L, 1), c32(map + 0x10L, 0),
                c32(chosen, 0x80000000L), c8(chosen + 4L, 2),
                c128(chosen + 8L, assignedLow, assignedHigh),
                c128(chosen + 0x18L, freshKeyLength, assignedCapacity),
                c32(next, 0xF1234567L), c8(next + 4L, 2),
                c128(next + 8L, oldLow, oldHigh),
                c128(next + 0x18L, oldLength, oldCapacity)));
    }

    private static Step m(Kind kind, long address, long low) {
        return new Step(kind, address, low, 0, List.of(), 0, List.of());
    }

    private static Step v(Kind kind, long address, long low, long high) {
        return new Step(kind, address, low, high, List.of(), 0, List.of());
    }

    private static Step p(Kind kind, long site, List<Long> arguments, long returned, List<Cell> effects) {
        return new Step(kind, site, 0, 0, arguments, returned, effects);
    }

    private static Cell c8(long address, long low) { return new Cell(address, 1, low, 0); }
    private static Cell c32(long address, long low) { return new Cell(address, 4, low, 0); }
    private static Cell c64(long address, long low) { return new Cell(address, 8, low, 0); }
    private static Cell c128(long address, long low, long high) { return new Cell(address, 16, low, high); }
}
