package org.xar.ck3.research.m3;

import java.util.List;

/** Literal source-derived arithmetic/observation witnesses; not target execution. */
public final class StringHashBook187 {
    private StringHashBook187() { }

    public enum Kind { READ_BYTE, READ_DWORD, WRITE_DWORD }
    public record Step(Kind kind, long address, long bits) { }
    public record Scenario(String id, long data, int lengthBits, long sourceEntryRsp,
            List<Step> expectedSteps, int expectedEax) { }

    private static Step rb(long address, int value) {
        return new Step(Kind.READ_BYTE, address, value);
    }
    private static Step rd(long address, int value) {
        return new Step(Kind.READ_DWORD, address, Integer.toUnsignedLong(value));
    }
    private static Step wd(long address, int value) {
        return new Step(Kind.WRITE_DWORD, address, Integer.toUnsignedLong(value));
    }

    public static List<Scenario> cases() {
        return List.of(
            new Scenario("zero_length", 0x1000L, 0, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0),
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0)
                ), 0x00000000),
            new Scenario("one_byte_a", 0x1000L, 1, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0),
                    rb(0x1000L, 0x61),
                    wd(0x8008L, 0), wd(0x8018L, 0x61000001),
                    rd(0x8018L, 0x61000001), rd(0x8008L, 0)
                ), 0x3C2569B2),
            new Scenario("three_bytes_abc", 0x1000L, 3, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0),
                    rb(0x1000L, 0x61), rb(0x1001L, 0x62), rb(0x1002L, 0x63),
                    wd(0x8008L, 0), wd(0x8018L, 0x63626103),
                    rd(0x8018L, 0x63626103), rd(0x8008L, 0)
                ), 0xB3DD93FA),
            new Scenario("one_dword_04030201", 0x1000L, 4, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0),
                    rd(0x1000L, 0x04030201),
                    wd(0x8008L, 0x4EB26727), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0x4EB26727)
                ), 0x3E349DA5),
            new Scenario("one_dword_then_byte5", 0x1000L, 5, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0),
                    rd(0x1000L, 0x04030201), rb(0x1004L, 5),
                    wd(0x8008L, 0x4EB26727), wd(0x8018L, 0x05000001),
                    rd(0x8018L, 0x05000001), rd(0x8008L, 0x4EB26727)
                ), 0xA291B9C8),
            new Scenario("unsigned_wrapped_bulk_end_skips_input", 0xFFFFFFFFFFFFFFFCL, 8, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0),
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0), rd(0x8008L, 0)
                ), 0x4939650B),
            new Scenario("synthetic_pending_count3_prefix_completes_word", 0x1000L, 1, 0x8000L,
                List.of(
                    wd(0x8008L, 0), wd(0x8018L, 0),
                    rd(0x8018L, 0x03020103), rd(0x8008L, 0),
                    rb(0x1000L, 4),
                    wd(0x8008L, 0x4EB26727), wd(0x8018L, 0xF93BDA00),
                    rd(0x8018L, 0xF93BDA00), rd(0x8008L, 0x4EB26727)
                ), 0x36670B16)
        );
    }
}
