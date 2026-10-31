package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.Embedded24Data313.*;

/** Owner original251 literals after target review: NONBLIND, no target-generated expected. */
public final class Embedded24Cases313 {
    private Embedded24Cases313() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("selfguard-zero-events", 0x1100000000L, 0x1100000000L, List.of(
            ), 0x1100000000L),
            new Scene("signed-negative-preserve-bits", 0x1100000000L, 0x2200000000L, List.of(
                new Step(Op.R32, List.of(0x220000000cL, 0xffffffffL), 0x0L),
                new Step(Op.R64, List.of(0x2200000000L, 0x3300000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x0L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0xffffffffL), 0x0L)
            ), 0x1100000000L),
            new Scene("reuse-captured-source-and128-before64", 0x1100000000L, 0x2200000000L, List.of(
                new Step(Op.R32, List.of(0x220000000cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x2200000000L, 0x3300000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x0L), 0x0L),
                new Step(Op.R32, List.of(0x1100000008L, 0x1L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0x4400000000L), 0x0L),
                new Step(Op.R128, List.of(0x3300000000L, 0x1122334455667788L, 0x99aabbccddeeff00L), 0x0L),
                new Step(Op.W128, List.of(0x4400000000L, 0x1122334455667788L, 0x99aabbccddeeff00L), 0x0L),
                new Step(Op.R64, List.of(0x3300000010L, 0xfedcba9876543210L), 0x0L),
                new Step(Op.W64, List.of(0x4400000010L, 0xfedcba9876543210L), 0x0L)
            ), 0x1100000000L),
            new Scene("allocator-input-effect-oldcopy-alias-fresh-release", 0x1100000000L, 0x2200000000L, List.of(
                new Step(Op.R32, List.of(0x220000000cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x2200000000L, 0x3300000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x0L), 0x0L),
                new Step(Op.R32, List.of(0x1100000008L, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x5500000000L), 0x0L),
                new Step(Op.R64, List.of(0x5500000000L, 0x6600000000L), 0x0L),
                new Step(Op.R64, List.of(0x6600000008L, 0x7700000000L), 0x0L),
                new Step(Op.ALLOC, List.of(0x7700000000L, 0x5500000000L, 0x18L, 0x8L), 0x1100000000L),
                new Step(Op.R32, List.of(0x110000000cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0x4400000000L), 0x0L),
                new Step(Op.R128, List.of(0x4400000000L, 0x8800000000L, 0x123456789abcdefL), 0x0L),
                new Step(Op.W128, List.of(0x1100000000L, 0x8800000000L, 0x123456789abcdefL), 0x0L),
                new Step(Op.R64, List.of(0x4400000010L, 0x9900000000L), 0x0L),
                new Step(Op.W64, List.of(0x1100000010L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0x8800000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000000L, 0xaa00000000L), 0x0L),
                new Step(Op.R64, List.of(0xaa00000010L, 0xbb00000000L), 0x0L),
                new Step(Op.RELEASE, List.of(0xbb00000000L, 0x9900000000L, 0x8800000000L, 0x8L), 0x0L),
                new Step(Op.W64, List.of(0x1100000000L, 0x1100000000L), 0x0L),
                new Step(Op.W32, List.of(0x1100000008L, 0x1L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x1L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0x1100000000L), 0x0L),
                new Step(Op.R128, List.of(0x3300000000L, 0xcc00000000L, 0xdd00000000L), 0x0L),
                new Step(Op.W128, List.of(0x1100000000L, 0xcc00000000L, 0xdd00000000L), 0x0L),
                new Step(Op.R64, List.of(0x3300000010L, 0xee00000000L), 0x0L),
                new Step(Op.W64, List.of(0x1100000010L, 0xee00000000L), 0x0L)
            ), 0x1100000000L)
        );
    }
}
