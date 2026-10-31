package org.xar.ck3.research.m3;

import java.util.List;

/** Literal finite source observations; expected values never come from target execution. */
public final class GroupNameEqualBook185 {
    private GroupNameEqualBook185() { }

    public enum Kind { READ_WORD, WRITE_WORD, READ_VECTOR128, READ_BYTE }
    public record Step(Kind kind, long address, long low, long high) { }
    public record Scenario(String id, long moduleBase, long left, long right, long sourceEntryRsp,
            List<Step> expectedSteps, int expectedAl) { }

    private static Step w(long address, int value) {
        return new Step(Kind.READ_WORD, address, value, 0L);
    }
    private static Step s(long address, int value) {
        return new Step(Kind.WRITE_WORD, address, value, 0L);
    }
    private static Step v(long address, long low, long high) {
        return new Step(Kind.READ_VECTOR128, address, low, high);
    }
    private static Step b(long address, int value) {
        return new Step(Kind.READ_BYTE, address, value, 0L);
    }

    public static List<Scenario> cases() {
        return List.of(
            new Scenario("scalar_equal_through_nul_right_word_selected",
                0x10000000L, 0x10001L, 0x20002L, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 65535),
                    s(0x8008L, 2), s(0x8010L, 1),
                    w(0x8008L, 2), w(0x8010L, 1),
                    w(0x15CB0A58L, 1), w(0x8008L, 2),
                    b(0x10001L, 65), b(0x20002L, 65),
                    b(0x10002L, 0), b(0x20003L, 0)
                ), 1),
            new Scenario("scalar_mismatch_left_word_selected",
                0x10000000L, 0x10003L, 0x20001L, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 65535),
                    s(0x8008L, 1), s(0x8010L, 3),
                    w(0x8008L, 1), w(0x8010L, 3),
                    w(0x15CB0A58L, 2), w(0x8010L, 3),
                    b(0x10003L, 128), b(0x20001L, 127)
                ), 0),
            new Scenario("vector_difference_after_first_left_zero_ignored",
                0x10000000L, 0x10000L, 0x20000L, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 0),
                    s(0x8008L, 0), s(0x8010L, 0),
                    w(0x8008L, 0), w(0x8010L, 0),
                    w(0x15CB0A58L, 0), w(0x8010L, 0),
                    v(0x10000L, 0x4444444400434241L, 0x4444444444444444L),
                    v(0x20000L, 0x4444449900434241L, 0x4444444444444444L)
                ), 1),
            new Scenario("vector_mismatch_before_first_left_zero",
                0x10000000L, 0x10000L, 0x20000L, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 0),
                    s(0x8008L, 0), s(0x8010L, 0),
                    w(0x8008L, 0), w(0x8010L, 0),
                    w(0x15CB0A58L, 0), w(0x8010L, 0),
                    v(0x10000L, 0x4444444400434241L, 0x4444444444444444L),
                    v(0x20000L, 0x4444444400994241L, 0x4444444444444444L)
                ), 0),
            new Scenario("vector_without_zero_mismatch_in_high_half",
                0x10000000L, 0x10000L, 0x20000L, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 0),
                    s(0x8008L, 0), s(0x8010L, 0),
                    w(0x8008L, 0), w(0x8010L, 0),
                    w(0x15CB0A58L, 0), w(0x8010L, 0),
                    v(0x10000L, 0x0101010101010101L, 0x0101010101010101L),
                    v(0x20000L, 0x0101010101010101L, 0x0101010101010201L)
                ), 0),
            new Scenario("vector_counter_wrap_then_second_vector_terminates",
                0x10000000L, 0x1FFFAL, 0x2FFFAL, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 65535),
                    s(0x8008L, 65530), s(0x8010L, 65530),
                    w(0x8008L, 65530), w(0x8010L, 65530),
                    w(0x15CB0A58L, 65535), w(0x8010L, 65530),
                    v(0x1FFFAL, 0x0101010101010101L, 0x0101010101010101L),
                    v(0x2FFFAL, 0x0101010101010101L, 0x0101010101010101L),
                    v(0x2000AL, 0L, 0x0101010101010101L),
                    v(0x3000AL, 0L, 0x0101010101010101L)
                ), 1),
            new Scenario("vector_bound_exit_scalar_at_advanced_addresses",
                0x10000000L, 0x10000L, 0x20000L, 0x8000L,
                List.of(
                    w(0x15CAFCBCL, 0),
                    s(0x8008L, 0), s(0x8010L, 0),
                    w(0x8008L, 0), w(0x8010L, 0),
                    w(0x15CB0A58L, 0), w(0x8010L, 0),
                    v(0x10000L, 0x0101010101010101L, 0x0101010101010101L),
                    v(0x20000L, 0x0101010101010101L, 0x0101010101010101L),
                    b(0x10010L, 65), b(0x20010L, 65),
                    b(0x10011L, 0), b(0x20011L, 0)
                ), 1)
        );
    }
}
