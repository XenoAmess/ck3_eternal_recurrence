package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppendData344.*;

/** Owner NONBLIND original227 literals after modeltarget read; no target-generated expected. */
public final class QueueAppendCases344 {
    private QueueAppendCases344() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("nongrowth-base-alias-and-fresh-return", 0x1100000000L, 0x7ff000000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x110000000cL, 0x1L), 0x0L),
                new Step(Op.R32, List.of(0x1100000008L, 0x3L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0x10fffffff8L), 0x0L),
                new Step(Op.R64, List.of(0x7ff000000000L, 0xaa00000000L), 0x0L),
                new Step(Op.W64, List.of(0x1100000000L, 0xaa00000000L), 0x0L),
                new Step(Op.R32, List.of(0x110000000cL, 0x1L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x2L), 0x0L),
                new Step(Op.R32, List.of(0x110000000cL, 0x2L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0xaa00000000L), 0x0L)
            ), 0xaa00000008L),
            new Scene("growth-zero-append-before-release", 0x1100000000L, 0x7ff000000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x110000000cL, 0x0L), 0x0L),
                new Step(Op.R32, List.of(0x1100000008L, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R32, List.of(0x33049f64f0L, 0x3fc00000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000008L, 0xab00000000L), 0x0L),
                new Step(Op.ALLOC, List.of(0xab00000000L, 0x8800000000L, 0x8L, 0x8L), 0xbb00000000L),
                new Step(Op.R32, List.of(0x110000000cL, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x7ff000000000L, 0xaa00000000L), 0x0L),
                new Step(Op.W64, List.of(0xbb00000000L, 0xaa00000000L), 0x0L),
                new Step(Op.R32, List.of(0x110000000cL, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0x0L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000010L, 0xac00000000L), 0x0L),
                new Step(Op.FREE, List.of(0xac00000000L, 0x8800000000L, 0x0L, 0x8L), 0x0L),
                new Step(Op.W32, List.of(0x1100000008L, 0x1L), 0x0L),
                new Step(Op.W64, List.of(0x1100000000L, 0xbb00000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x1L), 0x0L)
            ), 0xbb00000000L),
            new Scene("growth-positive-append-before-copy", 0x1100000000L, 0x7ff000000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x110000000cL, 0x2L), 0x0L),
                new Step(Op.R32, List.of(0x1100000008L, 0x2L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R32, List.of(0x33049f64f0L, 0x3fc00000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000008L, 0xab00000000L), 0x0L),
                new Step(Op.ALLOC, List.of(0xab00000000L, 0x8800000000L, 0x18L, 0x8L), 0xbb00000000L),
                new Step(Op.R32, List.of(0x110000000cL, 0x2L), 0x0L),
                new Step(Op.R64, List.of(0x7ff000000000L, 0xaa00000000L), 0x0L),
                new Step(Op.W64, List.of(0xbb00000010L, 0xaa00000000L), 0x0L),
                new Step(Op.R32, List.of(0x110000000cL, 0x2L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0xcc00000000L), 0x0L),
                new Step(Op.COPY, List.of(0xbb00000000L, 0xcc00000000L, 0x10L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0xcc00000000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000010L, 0xac00000000L), 0x0L),
                new Step(Op.FREE, List.of(0xac00000000L, 0x8800000000L, 0xcc00000000L, 0x8L), 0x0L),
                new Step(Op.W32, List.of(0x1100000008L, 0x3L), 0x0L),
                new Step(Op.W64, List.of(0x1100000000L, 0xbb00000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x3L), 0x0L)
            ), 0xbb00000010L),
            new Scene("controlled-NaN-CVTTMIN-unsigned-size-signed-return", 0x1100000000L, 0x7ff000000000L, 0x3300000000L, List.of(
                new Step(Op.R32, List.of(0x110000000cL, 0x80000000L), 0x0L),
                new Step(Op.R32, List.of(0x1100000008L, 0x80000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R32, List.of(0x33049f64f0L, 0x7fc00000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000008L, 0xab00000000L), 0x0L),
                new Step(Op.ALLOC, List.of(0xab00000000L, 0x8800000000L, 0x400000008L, 0x8L), 0xbb00000000L),
                new Step(Op.R32, List.of(0x110000000cL, 0xffffffffL), 0x0L),
                new Step(Op.R64, List.of(0x7ff000000000L, 0xaa00000000L), 0x0L),
                new Step(Op.W64, List.of(0xbafffffff8L, 0xaa00000000L), 0x0L),
                new Step(Op.R32, List.of(0x110000000cL, 0xffffffffL), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0xcc00000000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000010L, 0xac00000000L), 0x0L),
                new Step(Op.FREE, List.of(0xac00000000L, 0x8800000000L, 0xcc00000000L, 0x8L), 0x0L),
                new Step(Op.W32, List.of(0x1100000008L, 0x80000001L), 0x0L),
                new Step(Op.W64, List.of(0x1100000000L, 0xbb00000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x80000001L), 0x0L)
            ), 0xb700000000L)
        );
    }
}
