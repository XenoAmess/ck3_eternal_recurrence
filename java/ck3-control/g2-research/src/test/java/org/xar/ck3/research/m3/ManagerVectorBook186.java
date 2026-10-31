package org.xar.ck3.research.m3;

import java.util.List;

/** Literal supplied observations derived from held416B; no target execution. */
public final class ManagerVectorBook186 {
    private ManagerVectorBook186() { }

    public enum Kind { READ_BYTE, READ_DWORD, READ_POINTER, WRITE_BYTE, WRITE_DWORD,
        WRITE_QWORD, INCREMENT_DWORD, OBJECT08, GROWTH_CVTT32, ALLOCATOR08, OBJECT00, ALLOCATOR10 }
    public record Step(Kind kind, long address, long a, long b, long c, long result) { }
    public record Scenario(String id, long moduleBase, long manager, long output, List<Step> expectedSteps) { }

    private static Step rb(long address, int value) {
        return new Step(Kind.READ_BYTE, address, 0, 0, 0, value);
    }
    private static Step rd(long address, int value) {
        return new Step(Kind.READ_DWORD, address, 0, 0, 0, Integer.toUnsignedLong(value));
    }
    private static Step rp(long address, long value) {
        return new Step(Kind.READ_POINTER, address, 0, 0, 0, value);
    }
    private static Step wb(long address, int value) {
        return new Step(Kind.WRITE_BYTE, address, value, 0, 0, 0);
    }
    private static Step wd(long address, int value) {
        return new Step(Kind.WRITE_DWORD, address, Integer.toUnsignedLong(value), 0, 0, 0);
    }
    private static Step wq(long address, long value) {
        return new Step(Kind.WRITE_QWORD, address, value, 0, 0, 0);
    }
    private static Step inc(long address) {
        return new Step(Kind.INCREMENT_DWORD, address, 0, 0, 0, 0);
    }
    private static Step o8(long code, long receiver, long result) {
        return new Step(Kind.OBJECT08, code, receiver, 0, 0, result);
    }
    private static Step growth(int capacityBits, int multiplierBits, int result) {
        return new Step(Kind.GROWTH_CVTT32, 0, Integer.toUnsignedLong(capacityBits),
                Integer.toUnsignedLong(multiplierBits), 0, Integer.toUnsignedLong(result));
    }
    private static Step a8(long code, long allocator, long bytes, long result) {
        return new Step(Kind.ALLOCATOR08, code, allocator, bytes, 8, result);
    }
    private static Step o0(long code, long receiver) {
        return new Step(Kind.OBJECT00, code, receiver, 1, 0, 0);
    }
    private static Step a10(long code, long allocator, long block) {
        return new Step(Kind.ALLOCATOR10, code, allocator, block, 8, 0);
    }

    public static List<Scenario> cases() {
        return List.of(
            new Scenario("scan_empty_row_reaches_nonzero_end", 0x10000000L, 0x1000L, 0x2000L,
                List.of(
                    rp(0x1030L, 0x3000L),
                    rb(0x3004L, 0), rb(0x301CL, 255),
                    rb(0x1040L, 0), rd(0x103CL, 0)
                )),
            new Scenario("ordinary_append_with_increment_and_fresh_data", 0x10000000L, 0x1000L, 0x2000L,
                List.of(
                    rp(0x1030L, 0x3000L), rb(0x3004L, 1),
                    rb(0x1040L, 0), rd(0x103CL, 0),
                    rd(0x149F64F0L, 0x3FC00000),
                    rp(0x3010L, 0x4000L), rp(0x4000L, 0x4100L), rp(0x4108L, 0x4200L),
                    o8(0x4200L, 0x4000L, 0x5000L),
                    rd(0x200CL, 0), rd(0x2008L, 2),
                    rp(0x2000L, 0x6000L), wq(0x6000L, 0x5000L), inc(0x200CL),
                    rd(0x200CL, 1), rp(0x2000L, 0x6000L),
                    rp(0x6000L, 0x5000L), rd(0x3008L, 0x11223344),
                    wd(0x5008L, 0x11223344), wb(0x500CL, 0), rb(0x301CL, 255)
                )),
            new Scenario("growth_zero_old_count_no_move_or_cleanup_loop", 0x10000000L, 0x1000L, 0x2000L,
                List.of(
                    rp(0x1030L, 0x3000L), rb(0x3004L, 1),
                    rb(0x1040L, 0), rd(0x103CL, 0),
                    rd(0x149F64F0L, 0x3FC00000),
                    rp(0x3010L, 0x4000L), rp(0x4000L, 0x4100L), rp(0x4108L, 0x4200L),
                    o8(0x4200L, 0x4000L, 0x5000L),
                    rd(0x200CL, 0), rd(0x2008L, 0), growth(0, 0x3FC00000, 0),
                    rp(0x2010L, 0x7000L), rp(0x7000L, 0x7100L), rp(0x7108L, 0x7200L),
                    a8(0x7200L, 0x7000L, 8L, 0x8000L),
                    rd(0x200CL, 0), wq(0x8000L, 0x5000L), rd(0x200CL, 0),
                    rp(0x2010L, 0x7000L), rp(0x2000L, 0L),
                    rp(0x7000L, 0x7100L), rp(0x7110L, 0x7300L),
                    a10(0x7300L, 0x7000L, 0L),
                    wq(0x2000L, 0x8000L), wd(0x200CL, 1), wd(0x2008L, 1),
                    rp(0x8000L, 0x5000L), rd(0x3008L, 0x11223344),
                    wd(0x5008L, 0x11223344), wb(0x500CL, 0), rb(0x301CL, 255)
                )),
            new Scenario("growth_move_zero_fresh_cleanup_and_captured_publication", 0x10000000L, 0x1000L, 0x2000L,
                List.of(
                    rp(0x1030L, 0x3000L), rb(0x3004L, 1),
                    rb(0x1040L, 0), rd(0x103CL, 0),
                    rd(0x149F64F0L, 0x7FC00000),
                    rp(0x3010L, 0x4000L), rp(0x4000L, 0x4100L), rp(0x4108L, 0x4200L),
                    o8(0x4200L, 0x4000L, 0x5000L),
                    rd(0x200CL, 1), rd(0x2008L, 1), growth(1, 0x7FC00000, 0x80000000),
                    rp(0x2010L, 0x7000L), rp(0x7000L, 0x7100L), rp(0x7108L, 0x7200L),
                    a8(0x7200L, 0x7000L, 16L, 0x8000L),
                    rd(0x200CL, 1), wq(0x8008L, 0x5000L), rd(0x200CL, 1),
                    rp(0x2000L, 0x6000L), rp(0x6000L, 0x9000L),
                    wq(0x6000L, 0L), wq(0x8000L, 0x9000L),
                    rd(0x200CL, 1), rp(0x2000L, 0x6100L), rp(0x6100L, 0x9000L),
                    rp(0x9000L, 0x9100L), rp(0x9100L, 0x9200L), o0(0x9200L, 0x9000L),
                    rp(0x2010L, 0x7010L), rp(0x2000L, 0x6200L),
                    rp(0x7010L, 0x7118L), rp(0x7128L, 0x7308L),
                    a10(0x7308L, 0x7010L, 0x6200L),
                    wq(0x2000L, 0x8000L), wd(0x200CL, 2), wd(0x2008L, 2),
                    rp(0x8008L, 0x5000L), rd(0x3008L, 0x55667788),
                    wd(0x5008L, 0x55667788), wb(0x500CL, 0), rb(0x301CL, 255)
                ))
        );
    }
}
