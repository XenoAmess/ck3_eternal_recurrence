package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.GrowthCopyData391.Op;
import static org.xar.ck3.control.g2.m2.nativecode.GrowthCopyData391.Step;
import static org.xar.ck3.control.g2.m2.nativecode.GrowthCopyData391.Scene;

public final class GrowthCopyCases391 {
    private GrowthCopyCases391() { }

    public static List<Scene> scenes() {
        return List.of(new Scene(
            "one-to-three-known-copy16-and-reverse-chain",
            0x8100000000001000L,
            3,
            0x3300000000L,
            true,
            List.of(
                new Step(Op.R8, List.of(0x8100000000001040L, 0x0000000000000000L), 0L),
                new Step(Op.R32, List.of(0x8100000000001024L, 0x0000000000000001L), 0L),
                new Step(Op.R32, List.of(0x8100000000001024L, 0x0000000000000001L), 0L),
                new Step(Op.R32, List.of(0x8100000000001020L, 0x0000000000000001L), 0L),
                new Step(Op.R64, List.of(0x8100000000001028L, 0x8200000000002000L), 0L),
                new Step(Op.R64, List.of(0x8200000000002000L, 0x8300000000003000L), 0L),
                new Step(Op.R64, List.of(0x8300000000003008L, 0x8400000000004000L), 0L),
                new Step(Op.ALLOC, List.of(0x8400000000004000L, 0x8200000000002000L, 0x0000000000000030L, 0x0000000000000008L), 0x8500000000005000L),
                new Step(Op.R32, List.of(0x8100000000001024L, 0x0000000000000001L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8600000000006000L), 0L),
                new Step(Op.R128, List.of(0x8600000000006000L, 0x1122334455667788L, 0x89ABCDEF01234567L), 0L),
                new Step(Op.R128, List.of(0x8600000000006000L, 0x1122334455667788L, 0x89ABCDEF01234567L), 0L),
                new Step(Op.W128, List.of(0x8500000000005000L, 0x1122334455667788L, 0x89ABCDEF01234567L), 0L),
                new Step(Op.W128, List.of(0x8500000000005000L, 0x1122334455667788L, 0x89ABCDEF01234567L), 0L),
                new Step(Op.R32, List.of(0x8100000000001024L, 0x0000000000000001L), 0L),
                new Step(Op.R64, List.of(0x8100000000001028L, 0x8700000000007000L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8A0000000000A000L), 0L),
                new Step(Op.R64, List.of(0x8700000000007000L, 0x8800000000008000L), 0L),
                new Step(Op.R64, List.of(0x8800000000008010L, 0x8900000000009000L), 0L),
                new Step(Op.FREE, List.of(0x8900000000009000L, 0x8700000000007000L, 0x8A0000000000A000L, 0x0000000000000008L), 0L),
                new Step(Op.W64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W32, List.of(0x8100000000001024L, 0x0000000000000001L), 0L),
                new Step(Op.W32, List.of(0x8100000000001020L, 0x0000000000000003L), 0L),
                new Step(Op.R32, List.of(0x8100000000001024L, 0x0000000000000001L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.SET, List.of(0x8500000000005010L, 0x0000000000000000L, 0x0000000000000020L), 0L),
                new Step(Op.W32, List.of(0x8100000000001024L, 0x0000000000000003L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W32, List.of(0x8500000000005024L, 0x0000000000FFFFFFL), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W64, List.of(0x8500000000005028L, 0x0000000000000000L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W32, List.of(0x8500000000005020L, 0x0000000000FFFFFFL), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W32, List.of(0x8500000000005014L, 0x0000000000FFFFFFL), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W64, List.of(0x8500000000005018L, 0x0000000000000000L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W32, List.of(0x8500000000005024L, 0x0000000000000001L), 0L),
                new Step(Op.R64, List.of(0x8100000000001018L, 0x8500000000005000L), 0L),
                new Step(Op.W32, List.of(0x8500000000005010L, 0x0000000000000002L), 0L),
                new Step(Op.R32, List.of(0x8100000000001038L, 0x0000000000FFFFFFL), 0L),
                new Step(Op.W32, List.of(0x8100000000001038L, 0x0000000000000001L), 0L)
            )
        ));
    }
}