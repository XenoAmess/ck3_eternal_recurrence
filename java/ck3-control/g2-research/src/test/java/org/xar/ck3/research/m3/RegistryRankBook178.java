package org.xar.ck3.research.m3;

import java.util.List;

/** Literal expectations derived from original source, never from target execution. */
public final class RegistryRankBook178 {
    private RegistryRankBook178() { }

    public record Bytes(int at22, int at21, int at20) { }
    public record Case(String id, long begin, List<Bytes> entries, long expectedSelected) { }

    public static List<Case> cases() {
        return List.of(
                new Case("empty", 0x1000L, List.of(), 0L),
                new Case("zero_flags", 0x2000L, List.of(new Bytes(0, 0, 0)), 0x2000L),
                new Case("at22_zero", 0x3000L,
                        List.of(new Bytes(255, 1, 0), new Bytes(0, 1, 0), new Bytes(17, 1, 0)),
                        0x3028L),
                new Case("at21_zero", 0x4000L,
                        List.of(new Bytes(9, 255, 0), new Bytes(9, 0, 0), new Bytes(9, 1, 0)),
                        0x4028L),
                new Case("at20_exact_two", 0x5000L,
                        List.of(new Bytes(9, 1, 3), new Bytes(9, 1, 2), new Bytes(9, 1, 255)),
                        0x5028L),
                new Case("first_max_tie", 0x6000L,
                        List.of(new Bytes(0, 0, 2), new Bytes(0, 0, 2), new Bytes(0, 0, 1)),
                        0x6000L),
                new Case("strict_improvements", 0x7000L,
                        List.of(new Bytes(255, 1, 2), new Bytes(0, 1, 2),
                                new Bytes(255, 0, 2), new Bytes(0, 0, 2)),
                        0x7078L),
                new Case("wrap_past_zero_tie", 0xffffffffffffffe0L,
                        List.of(new Bytes(255, 1, 1), new Bytes(0, 0, 0), new Bytes(0, 0, 3)),
                        0x8L));
    }
}
