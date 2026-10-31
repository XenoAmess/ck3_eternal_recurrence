package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.TableReserveFixture223.*;

public final class TableReserveCases223 {
    private TableReserveCases223() { }

    public static List<Scene> scenes() {
        return List.of(
            new Scene("signed-negative-desired-skip", 0xF000000000001000L, -1, List.of(
                new Step(Kind.R32, 0xF000000000001008L, 0, 0, 0, 0))),
            new Scene("negative-count-and-unsigned-allocation-size", 0xE000000000002000L, -1, List.of(
                new Step(Kind.R32, 0xE000000000002008L, 0x80000000L, 0, 0, 0),
                new Step(Kind.R64, 0xE000000000002010L, 0x1111000000000100L, 0, 0, 0),
                new Step(Kind.R64, 0x1111000000000100L, 0x2222000000000200L, 0, 0, 0),
                new Step(Kind.R64, 0x2222000000000208L, 0x3333000000000300L, 0, 0, 0),
                new Step(Kind.ALLOC, 0x3333000000000300L, 0x4444000000000400L,
                        0x1111000000000100L, 0x7FFFFFFF8L, 8),
                new Step(Kind.R32, 0xE00000000000200CL, 0xFFFFFFFFL, 0, 0, 0),
                new Step(Kind.R64, 0xE000000000002010L, 0x5555000000000500L, 0, 0, 0),
                new Step(Kind.R64, 0xE000000000002000L, 0x6666000000000600L, 0, 0, 0),
                new Step(Kind.R64, 0x5555000000000500L, 0x7777000000000700L, 0, 0, 0),
                new Step(Kind.R64, 0x7777000000000710L, 0x8888000000000800L, 0, 0, 0),
                new Step(Kind.RELEASE, 0x8888000000000800L, 0,
                        0x5555000000000500L, 0x6666000000000600L, 8),
                new Step(Kind.W64, 0xE000000000002000L, 0x4444000000000400L, 0, 0, 0),
                new Step(Kind.W32, 0xE00000000000200CL, 0xFFFFFFFFL, 0, 0, 0),
                new Step(Kind.W32, 0xE000000000002008L, 0xFFFFFFFFL, 0, 0, 0))),
            new Scene("two-moves-fresh-count-array-and-allocator", 0xD000000000003000L, 3, List.of(
                new Step(Kind.R32, 0xD000000000003008L, 1, 0, 0, 0),
                new Step(Kind.R64, 0xD000000000003010L, 0xA111000000000100L, 0, 0, 0),
                new Step(Kind.R64, 0xA111000000000100L, 0xA222000000000200L, 0, 0, 0),
                new Step(Kind.R64, 0xA222000000000208L, 0xA333000000000300L, 0, 0, 0),
                new Step(Kind.ALLOC, 0xA333000000000300L, 0xA444000000000400L,
                        0xA111000000000100L, 24, 8),
                new Step(Kind.R32, 0xD00000000000300CL, 2, 0, 0, 0),
                new Step(Kind.R64, 0xD000000000003000L, 0xA555000000000500L, 0, 0, 0),
                new Step(Kind.R64, 0xA555000000000500L, 0xF111000000000111L, 0, 0, 0),
                new Step(Kind.W64, 0xA555000000000500L, 0, 0, 0, 0),
                new Step(Kind.W64, 0xA444000000000400L, 0xF111000000000111L, 0, 0, 0),
                new Step(Kind.R64, 0xA555000000000508L, 0xF222000000000222L, 0, 0, 0),
                new Step(Kind.W64, 0xA555000000000508L, 0, 0, 0, 0),
                new Step(Kind.W64, 0xA444000000000408L, 0xF222000000000222L, 0, 0, 0),
                new Step(Kind.R32, 0xD00000000000300CL, 1, 0, 0, 0),
                new Step(Kind.R64, 0xD000000000003000L, 0xA666000000000600L, 0, 0, 0),
                new Step(Kind.R64, 0xA666000000000600L, 0xF333000000000333L, 0, 0, 0),
                new Step(Kind.FREE, 0, 0, 0xF333000000000333L, 0x172000, 0),
                new Step(Kind.R64, 0xD000000000003010L, 0xB111000000000100L, 0, 0, 0),
                new Step(Kind.R64, 0xD000000000003000L, 0xB222000000000200L, 0, 0, 0),
                new Step(Kind.R64, 0xB111000000000100L, 0xB333000000000300L, 0, 0, 0),
                new Step(Kind.R64, 0xB333000000000310L, 0xB444000000000400L, 0, 0, 0),
                new Step(Kind.RELEASE, 0xB444000000000400L, 0,
                        0xB111000000000100L, 0xB222000000000200L, 8),
                new Step(Kind.W64, 0xD000000000003000L, 0xA444000000000400L, 0, 0, 0),
                new Step(Kind.W32, 0xD00000000000300CL, 1, 0, 0, 0),
                new Step(Kind.W32, 0xD000000000003008L, 3, 0, 0, 0)))
        );
    }
}
