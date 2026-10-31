package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import static org.xar.ck3.control.g2.m2.nativecode.SlotGrowthComposedFixture247.*;

public final class SlotGrowthComposedCases247 {
    private static final long T = 0x8100000000001000L;
    private static final long ALLOCATOR = 0x8200000000002000L, VTABLE = 0x8300000000003000L;
    private static final long ALLOCATE = 0x8400000000004000L, NEW = 0x8500000000005000L;
    private static final long OLD = 0x8600000000006000L, ALLOCATOR2 = 0x8700000000007000L;
    private static final long VTABLE2 = 0x8800000000008000L, RELEASE = 0x8900000000009000L;
    private static final long OLD2 = 0x8A0000000000A000L;
    private SlotGrowthComposedCases247() { }
    private static Step m(Kind kind, long address, long value) { return new Step(kind, address, value, 0, 0, 0); }
    public static List<Scene> scenes() {
        return List.of(new Scene("one-to-three-complete-reserve-copy-and-reverse-chain", T, 3, true, List.of(
            m(Kind.R8, T + 0x40, 0),
            m(Kind.R32, T + 0x24, 1),
            m(Kind.R32, T + 0x24, 1),
            m(Kind.R32, T + 0x20, 1),
            m(Kind.R64, T + 0x28, ALLOCATOR),
            m(Kind.R64, ALLOCATOR, VTABLE),
            m(Kind.R64, VTABLE + 8, ALLOCATE),
            new Step(Kind.ALLOC, ALLOCATE, NEW, ALLOCATOR, 48, 8),
            m(Kind.R32, T + 0x24, 1),
            m(Kind.R64, T + 0x18, OLD),
            new Step(Kind.COPY, 0, 0, NEW, OLD, 16),
            m(Kind.R32, T + 0x24, 1),
            m(Kind.R64, T + 0x28, ALLOCATOR2),
            m(Kind.R64, T + 0x18, OLD2),
            m(Kind.R64, ALLOCATOR2, VTABLE2),
            m(Kind.R64, VTABLE2 + 0x10, RELEASE),
            new Step(Kind.RELEASE, RELEASE, 0, ALLOCATOR2, OLD2, 8),
            m(Kind.W64, T + 0x18, NEW),
            m(Kind.W32, T + 0x24, 1),
            m(Kind.W32, T + 0x20, 3),
            m(Kind.R32, T + 0x24, 1),
            m(Kind.R64, T + 0x18, NEW),
            new Step(Kind.SET, 0, 0, NEW + 0x10, 0, 32),
            m(Kind.W32, T + 0x24, 3),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W32, NEW + 0x24, 0xFFFFFF),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W64, NEW + 0x28, 0),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W32, NEW + 0x20, 0xFFFFFF),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W32, NEW + 0x14, 0xFFFFFF),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W64, NEW + 0x18, 0),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W32, NEW + 0x24, 1),
            m(Kind.R64, T + 0x18, NEW),
            m(Kind.W32, NEW + 0x10, 2),
            m(Kind.R32, T + 0x38, 0xFFFFFF),
            m(Kind.W32, T + 0x38, 1)
        )));
    }
}
