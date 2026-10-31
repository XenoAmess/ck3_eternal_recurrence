package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.QueueKnownCopyData375.*;

public final class KnownQueueCopyCases375 {
    private KnownQueueCopyCases375() { }
    public static List<Scene> scenes() {
        return List.of(
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
                new Step(Op.R128, List.of(0xcc00000000L, 0x1122334455667788L, 0x0123456789abcdefL), 0x0L),
                new Step(Op.R128, List.of(0xcc00000000L, 0x1122334455667788L, 0x0123456789abcdefL), 0x0L),
                new Step(Op.W128, List.of(0xbb00000000L, 0x1122334455667788L, 0x0123456789abcdefL), 0x0L),
                new Step(Op.W128, List.of(0xbb00000000L, 0x1122334455667788L, 0x0123456789abcdefL), 0x0L),
                new Step(Op.R64, List.of(0x1100000010L, 0x8800000000L), 0x0L),
                new Step(Op.R64, List.of(0x1100000000L, 0xcc00000000L), 0x0L),
                new Step(Op.R64, List.of(0x8800000000L, 0x9900000000L), 0x0L),
                new Step(Op.R64, List.of(0x9900000010L, 0xac00000000L), 0x0L),
                new Step(Op.FREE, List.of(0xac00000000L, 0x8800000000L, 0xcc00000000L, 0x8L), 0x0L),
                new Step(Op.W32, List.of(0x1100000008L, 0x3L), 0x0L),
                new Step(Op.W64, List.of(0x1100000000L, 0xbb00000000L), 0x0L),
                new Step(Op.W32, List.of(0x110000000cL, 0x3L), 0x0L)
            ), 0xbb00000010L)
        );
    }
}