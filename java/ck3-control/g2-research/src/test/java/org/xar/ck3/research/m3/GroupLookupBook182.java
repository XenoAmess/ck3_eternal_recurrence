package org.xar.ck3.research.m3;

import java.util.List;

/** Six source-derived observation scripts; never executes the target to obtain expectations. */
public final class GroupLookupBook182 {
    private GroupLookupBook182() { }

    public enum Kind { READ_BYTE, READ_DWORD, READ_POINTER, XADD32, PAUSE }
    public record Step(Kind kind, long address, int delta, long returned) { }
    public record Scenario(String id, long moduleBase, long receiver, int hash32,
            List<Step> expectedSteps, long expectedReturned) { }

    private static Step rb(long address, int value) {
        return new Step(Kind.READ_BYTE, address, 0, value);
    }
    private static Step rd(long address, int value) {
        return new Step(Kind.READ_DWORD, address, 0, Integer.toUnsignedLong(value));
    }
    private static Step rp(long address, long value) {
        return new Step(Kind.READ_POINTER, address, 0, value);
    }
    private static Step xa(long address, int delta, int old) {
        return new Step(Kind.XADD32, address, delta, Integer.toUnsignedLong(old));
    }
    private static Step pa() {
        return new Step(Kind.PAUSE, 0L, 0, 0L);
    }

    public static List<Scenario> cases() {
        return List.of(
            new Scenario("bypass_direct_match", 0x10000000L, 0x20000000L, 0x12345678,
                List.of(
                    rb(0x20000EE0L, 1),
                    rd(0x2000018CL, 0),
                    rp(0x20000180L, 0x30000000L),
                    rb(0x30000004L, 1),
                    rd(0x30000008L, 0x12345678),
                    rb(0x30000004L, 1),
                    rp(0x30000010L, 0xABC001L)
                ), 0xABC001L),
            new Scenario("bypass_collision_then_match", 0x10000000L, 0x20000000L, 1,
                List.of(
                    rb(0x20000EE0L, 255),
                    rd(0x2000018CL, 3),
                    rp(0x20000180L, 0x30000000L),
                    rb(0x3000001CL, 1),
                    rd(0x30000020L, 2),
                    rb(0x30000034L, 2),
                    rd(0x30000038L, 1),
                    rb(0x30000034L, 2),
                    rp(0x30000040L, 0xABC002L)
                ), 0xABC002L),
            new Scenario("bypass_initial_failure_global_pointer", 0x10000000L, 0x20000000L, 2,
                List.of(
                    rb(0x20000EE0L, 1),
                    rd(0x2000018CL, 3),
                    rp(0x20000180L, 0x30000000L),
                    rb(0x30000034L, 0),
                    rb(0x20000190L, 1),
                    rb(0x3000007CL, 255),
                    rp(0x15D37D78L, 0xABC003L)
                ), 0xABC003L),
            new Scenario("negative_hash_and_mask_later_failure", 0x10000000L, 0x20000000L, -2,
                List.of(
                    rb(0x20000EE0L, 1),
                    rd(0x2000018CL, -1),
                    rp(0x20000180L, 0x30000000L),
                    rb(0x2FFFFFD4L, 1),
                    rd(0x2FFFFFD8L, -1),
                    rb(0x2FFFFFECL, 1),
                    rb(0x20000190L, 0),
                    rb(0x30000004L, 0),
                    rp(0x30000010L, 0xABC004L)
                ), 0xABC004L),
            new Scenario("shared_immediate_wrapping_xadd", 0x10000000L, 0x20000000L, 9,
                List.of(
                    rb(0x20000EE0L, 0),
                    xa(0x20000EA0L, 2, -2),
                    rd(0x2000018CL, 0),
                    rp(0x20000180L, 0x30000000L),
                    rb(0x30000004L, 1),
                    rd(0x30000008L, 9),
                    rb(0x30000004L, 255),
                    rp(0x15D37D78L, 0xABC005L),
                    xa(0x20000EA0L, -2, 0)
                ), 0xABC005L),
            new Scenario("shared_poll_pause_and_reacquire_race", 0x10000000L, 0x20000000L, 7,
                List.of(
                    rb(0x20000EE0L, 0),
                    xa(0x20000EA0L, 2, 1),
                    xa(0x20000EA0L, -2, 3),
                    rd(0x20000EA0L, 1),
                    pa(),
                    rd(0x20000EA0L, 0),
                    xa(0x20000EA0L, 2, 1),
                    xa(0x20000EA0L, -2, 3),
                    rd(0x20000EA0L, 0),
                    xa(0x20000EA0L, 2, 0),
                    rd(0x2000018CL, 0),
                    rp(0x20000180L, 0x30000000L),
                    rb(0x30000004L, 1),
                    rd(0x30000008L, 7),
                    rb(0x30000004L, 1),
                    rp(0x30000010L, 0xABC006L),
                    xa(0x20000EA0L, -2, 2)
                ), 0xABC006L)
        );
    }
}
