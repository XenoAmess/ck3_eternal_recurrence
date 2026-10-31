package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Data325.*;

/** Owner NONBLIND original394 literals; no target-generated expected. */
public final class Embedded32Cases325 {
    private Embedded32Cases325() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("self-still-trailing4", 0x1100000000L, 0x1100000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x1100000028L, 0x89abcdefL), 0x0L),
                new Step(Op.W32, List.of(0x1100000028L, 0x89abcdefL), 0x0L),
                new Step(Op.COPY37282, List.of(0x1100000030L, 0x1100000030L), 0x0L),
                new Step(Op.FINALIZE, List.of(0x1100000000L), 0x0L)
            ), 0x1100000000L),
            new Scene("shrink-two-fresh-bases", 0x1100000000L, 0x2200000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x220000001cL, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x2200000010L, 0x4400000000L), 0x0L),
                new Step(Op.PREP, List.of(0x1100000010L), 0x0L),
                new Step(Op.R32, List.of(0x110000001cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x5500000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x5500000000L), 0x0L),
                new Step(Op.R64, List.of(0x5500000000L, 0x6600000000L), 0x0L),
                new Step(Op.R64, List.of(0x6600000000L, 0x7700000000L), 0x0L),
                new Step(Op.DESTROY, List.of(0x7700000000L, 0x5500000000L, 0x0L), 0x0L),
                new Step(Op.W32, List.of(0x110000001cL, 0x0L), 0x0L),
                new Step(Op.R32, List.of(0x2200000028L, 0xaabbccddL), 0x0L),
                new Step(Op.W32, List.of(0x1100000028L, 0xaabbccddL), 0x0L),
                new Step(Op.COPY37282, List.of(0x1100000030L, 0x2200000030L), 0x0L),
                new Step(Op.FINALIZE, List.of(0x1100000000L), 0x0L)
            ), 0x1100000000L),
            new Scene("capacity-reuse-no-replace", 0x1100000000L, 0x2200000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x220000001cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x2200000010L, 0x4400000000L), 0x0L),
                new Step(Op.PREP, List.of(0x1100000010L), 0x0L),
                new Step(Op.R32, List.of(0x110000001cL, 0x0L), 0x0L),
                new Step(Op.R32, List.of(0x1100000018L, 0x1L), 0x0L),
                new Step(Op.W32, List.of(0x110000001cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x5500000000L), 0x0L),
                new Step(Op.W64, List.of(0x5500000000L, 0x330448d230L), 0x0L),
                new Step(Op.R32, List.of(0x4400000008L, 0x12345678L), 0x0L),
                new Step(Op.W32, List.of(0x5500000008L, 0x12345678L), 0x0L),
                new Step(Op.R32, List.of(0x440000000cL, 0x89abcdefL), 0x0L),
                new Step(Op.W32, List.of(0x550000000cL, 0x89abcdefL), 0x0L),
                new Step(Op.R128, List.of(0x4400000010L, 0x102030405060708L, 0x1112131415161718L), 0x0L),
                new Step(Op.W128, List.of(0x5500000010L, 0x102030405060708L, 0x1112131415161718L), 0x0L),
                new Step(Op.R32, List.of(0x2200000028L, 0xaabbccddL), 0x0L),
                new Step(Op.W32, List.of(0x1100000028L, 0xaabbccddL), 0x0L),
                new Step(Op.COPY37282, List.of(0x1100000030L, 0x2200000030L), 0x0L),
                new Step(Op.FINALIZE, List.of(0x1100000000L), 0x0L)
            ), 0x1100000000L),
            new Scene("growth-old7-fresh-count-final7", 0x1100000000L, 0x2200000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x220000001cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x2200000010L, 0x4400000000L), 0x0L),
                new Step(Op.PREP, List.of(0x1100000010L), 0x0L),
                new Step(Op.R32, List.of(0x110000001cL, 0x0L), 0x0L),
                new Step(Op.R32, List.of(0x1100000018L, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x1100000020L, 0x8800000000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000008L, 0xaa00000000L), 0x0L),
                new Step(Op.ALLOC, List.of(0xaa00000000L, 0x8800000000L, 0x20L, 0x8L), 0xbb00000000L),
                new Step(Op.R32, List.of(0x110000001cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x5500000000L), 0x0L),
                new Step(Op.W64, List.of(0xbb00000000L, 0x330448d230L), 0x0L),
                new Step(Op.R32, List.of(0x5500000008L, 0x13579bdfL), 0x0L),
                new Step(Op.W32, List.of(0xbb00000008L, 0x13579bdfL), 0x0L),
                new Step(Op.R32, List.of(0x550000000cL, 0x2468ace0L), 0x0L),
                new Step(Op.W32, List.of(0xbb0000000cL, 0x2468ace0L), 0x0L),
                new Step(Op.R128, List.of(0x5500000010L, 0x2122232425262728L, 0x3132333435363738L), 0x0L),
                new Step(Op.W128, List.of(0xbb00000010L, 0x2122232425262728L, 0x3132333435363738L), 0x0L),
                new Step(Op.R32, List.of(0x110000001cL, 0x2L), 0x0L),
                new Step(Op.REPLACE, List.of(0x1100000010L, 0xbb00000000L, 0x2L, 0x1L), 0x0L),
                new Step(Op.W32, List.of(0x110000001cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0xbb00000000L), 0x0L),
                new Step(Op.W64, List.of(0xbb00000000L, 0x330448d230L), 0x0L),
                new Step(Op.R32, List.of(0x4400000008L, 0x12345678L), 0x0L),
                new Step(Op.W32, List.of(0xbb00000008L, 0x12345678L), 0x0L),
                new Step(Op.R32, List.of(0x440000000cL, 0x89abcdefL), 0x0L),
                new Step(Op.W32, List.of(0xbb0000000cL, 0x89abcdefL), 0x0L),
                new Step(Op.R128, List.of(0x4400000010L, 0x102030405060708L, 0x1112131415161718L), 0x0L),
                new Step(Op.W128, List.of(0xbb00000010L, 0x102030405060708L, 0x1112131415161718L), 0x0L),
                new Step(Op.R32, List.of(0x2200000028L, 0xaabbccddL), 0x0L),
                new Step(Op.W32, List.of(0x1100000028L, 0xaabbccddL), 0x0L),
                new Step(Op.COPY37282, List.of(0x1100000030L, 0x2200000030L), 0x0L),
                new Step(Op.FINALIZE, List.of(0x1100000000L), 0x0L)
            ), 0x1100000000L)
        );
    }
}
