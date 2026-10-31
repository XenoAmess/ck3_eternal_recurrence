package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.SlotArrayReserveFixture244.*;

public final class SlotArrayReserveCases244 {
    private SlotArrayReserveCases244() { }
    public static List<Scene> scenes() {
        return List.of(
            new Scene("earlySkipNegativeRequested", 0x1000000000000000L, 0xffffffff, List.of(
                new Step(Kind.R32, 0x1000000000000008L, 0x0L, 0x0L, 0x0L, 0x0L))),
            new Scene("negativeCountAllocNoCopy", 0x2000000000000000L, 0xffffffff, List.of(
                new Step(Kind.R32, 0x2000000000000008L, 0x80000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x2000000000000010L, 0x3000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x3000000000000000L, 0x4000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x4000000000000008L, 0x5000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.ALLOC, 0x5000000000000000L, 0x6000000000000000L, 0x3000000000000000L, 0xffffffff0L, 0x8L),
                new Step(Kind.R32, 0x200000000000000cL, 0xffffffffL, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x2000000000000010L, 0x3100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x2000000000000000L, 0x7100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x3100000000000000L, 0x4100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x4100000000000010L, 0x8100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.RELEASE, 0x8100000000000000L, 0x0L, 0x3100000000000000L, 0x7100000000000000L, 0x8L),
                new Step(Kind.W64, 0x2000000000000000L, 0x6000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.W32, 0x200000000000000cL, 0xffffffffL, 0x0L, 0x0L, 0x0L),
                new Step(Kind.W32, 0x2000000000000008L, 0xffffffffL, 0x0L, 0x0L, 0x0L))),
            new Scene("positiveCountCopyFreshRelease", 0x9000000000000000L, 0x10, List.of(
                new Step(Kind.R32, 0x9000000000000008L, 0x0L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x9000000000000010L, 0xa000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0xa000000000000000L, 0xb000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0xb000000000000008L, 0xc000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.ALLOC, 0xc000000000000000L, 0xd000000000000000L, 0xa000000000000000L, 0x100L, 0x8L),
                new Step(Kind.R32, 0x900000000000000cL, 0x2L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x9000000000000000L, 0xe000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.COPY, 0x0L, 0x0L, 0xd000000000000000L, 0xe000000000000000L, 0x20L),
                new Step(Kind.R32, 0x900000000000000cL, 0x1L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x9000000000000010L, 0xa100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0x9000000000000000L, 0xe100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0xa100000000000000L, 0xb100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.R64, 0xb100000000000010L, 0xf100000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.RELEASE, 0xf100000000000000L, 0x0L, 0xa100000000000000L, 0xe100000000000000L, 0x8L),
                new Step(Kind.W64, 0x9000000000000000L, 0xd000000000000000L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.W32, 0x900000000000000cL, 0x1L, 0x0L, 0x0L, 0x0L),
                new Step(Kind.W32, 0x9000000000000008L, 0x10L, 0x0L, 0x0L, 0x0L)))
        );
    }
}
